"""Data ingestion: official downloads, tidy 5-minute patient records, patient-level splits.

Run `python -m twin.data` to download every dataset from its official source and build
`data/processed/*.pkl`. Raw files are never committed (see research/DATASETS.md for licences).
"""
import hashlib
import io
import json
import pickle
import re
import struct
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
CGMACROS_ZIP = "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip"
SHANGHAI_ZIP = "https://ndownloader.figshare.com/files/42966622"
SHANGHAI_MD5 = "4bfb61cfa506b48155fd9e841ee48e21"  # published by figshare
STEP = 5  # minutes per grid step
NUTRIENTS = ["carbs", "protein", "fat", "fiber"]


# ---------------------------------------------------------------- downloads
class _HttpRange(io.RawIOBase):
    """Seekable read-only view of a remote file, so zipfile can read one member without the rest."""

    def __init__(self, url):
        self.url, self.pos, self.s = url, 0, requests.Session()
        self.size = int(self.s.head(url, allow_redirects=True, timeout=60).headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(b), self.size) - 1
        d = self.s.get(self.url, headers={"Range": f"bytes={self.pos}-{end}"}, timeout=120).content
        b[: len(d)] = d
        self.pos += len(d)
        return len(d)


def _zip_member(url, info):
    """Fetch and inflate one zip member with a single ranged GET; CRC-checked."""
    a = info.header_offset
    r = requests.get(url, headers={"Range": f"bytes={a}-{a + 30 + 4096 + info.compress_size}"}, timeout=300).content
    n, m = struct.unpack("<HH", r[26:30])
    raw = r[30 + n + m : 30 + n + m + info.compress_size]
    data = zlib.decompress(raw, -15) if info.compress_type == zipfile.ZIP_DEFLATED else raw
    if zlib.crc32(data) != info.CRC:
        raise IOError(f"CRC mismatch for {info.filename}")
    return data


def download(force=False):
    """Download CGMacros CSVs (6.6 MB of a 657 MB archive; meal photos are skipped) and ShanghaiT2DM."""
    log = {}
    out = RAW / "cgmacros"
    if force or not (out / "CGMacros" / "bio.csv").exists():
        zf = zipfile.ZipFile(io.BufferedReader(_HttpRange(CGMACROS_ZIP), 1 << 18))
        infos = [i for i in zf.infolist() if i.filename.endswith(".csv")]
        with ThreadPoolExecutor(8) as ex:
            for info, data in zip(infos, ex.map(lambda i: _zip_member(CGMACROS_ZIP, i), infos)):
                p = out / info.filename
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
    out = RAW / "shanghai"
    z = out / "diabetes_datasets.zip"
    if force or not z.exists():
        out.mkdir(parents=True, exist_ok=True)
        z.write_bytes(requests.get(SHANGHAI_ZIP, timeout=300).content)
    if hashlib.md5(z.read_bytes()).hexdigest() != SHANGHAI_MD5:
        raise IOError("ShanghaiT2DM archive does not match the md5 published by figshare")
    if not (out / "Shanghai_T2DM").exists():
        with zipfile.ZipFile(z) as zf:
            zf.extractall(out, [n for n in zf.namelist() if not n.startswith("__MACOSX") and ".DS_Store" not in n])
    for name, url in [("cgmacros", CGMACROS_ZIP), ("shanghai", SHANGHAI_ZIP)]:
        files = sorted(p for p in (RAW / name).rglob("*") if p.is_file() and p.name != "SOURCES.json")
        log[name] = {"url": url, "n_files": len(files), "bytes": sum(p.stat().st_size for p in files),
                     "sha256": {p.relative_to(RAW / name).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (RAW / "SOURCES.json").write_text(json.dumps(log, indent=1))
    return log


# ---------------------------------------------------------------- patient records
# A patient is a dict: id, cohort, group, dt (min), static (dict of EHR fields), and arrays on a
# regular grid: g (CGM mg/dL, NaN = missing), tod (hour of day), mets (NaN = watch not worn), hr,
# plus `meals` (DataFrame: idx, kind, carbs, protein, fat, fiber). Grid index i covers minutes
# [i*dt, (i+1)*dt); everything stored at i is known at the END of that interval.

def _group(hba1c):
    return "healthy" if hba1c < 5.7 else "prediabetes" if hba1c < 6.5 else "T2D"  # ADA HbA1c cut-offs


def _grid(ts, start, dt):
    return ((ts - start).dt.total_seconds() // (60 * dt)).astype(int).to_numpy()


def _meals(idx, kind, macros):
    m = pd.DataFrame({"idx": idx, "kind": kind, **macros}).fillna({n: 0.0 for n in NUTRIENTS})
    agg = {"kind": "first", **{n: "sum" for n in NUTRIENTS}}
    return m.groupby("idx", as_index=False).agg(agg).sort_values("idx").reset_index(drop=True)


def load_cgmacros():
    base = RAW / "cgmacros" / "CGMacros"
    bio = pd.read_csv(base / "bio.csv")
    bio.columns = [c.strip() for c in bio.columns]
    out = []
    for _, b in bio.iterrows():
        sid = int(b["subject"])
        d = pd.read_csv(base / f"CGMacros-{sid:03d}" / f"CGMacros-{sid:03d}.csv", parse_dates=["Timestamp"])
        d.columns = [c.strip() for c in d.columns]
        d = d.sort_values("Timestamp").drop_duplicates("Timestamp")
        i = _grid(d["Timestamp"], d["Timestamp"].iloc[0], STEP)
        T = i.max() + 1
        # Dexcom is stored interpolated to 1 min; keep only native (integer) readings so that no
        # value on our grid was computed from a later sample.
        dex = d["Dexcom GL"].where(d["Dexcom GL"] == d["Dexcom GL"].round())
        g = np.full(T, np.nan)
        s = pd.Series(dex.to_numpy(), index=i).dropna()
        g[s.index[~s.index.duplicated(keep="last")]] = s[~s.index.duplicated(keep="last")]
        # Fitbit activity as METs: native METs x10, or calories / resting calories (the same quantity:
        # calories == METs/10 * BMR per minute in every file that has both).
        if "METs" in d:
            mets = d["METs"] / 10.0
        else:
            cal = d["Calories (Activity)"]
            mets = cal / cal[cal > 0].min()
        mean = lambda v: pd.Series(v.to_numpy(), index=i).groupby(level=0).mean().reindex(range(T)).to_numpy()
        ml = d[d["Meal Type"].notna() & d["Carbs"].notna()]
        static = {
            "age": float(b["Age"]), "sex": b["Gender"], "bmi": float(b["BMI"]),
            "weight_kg": float(b["Body weight"]) * 0.4536, "hba1c": float(b["A1c PDL (Lab)"]),
            "fpg": float(b["Fasting GLU - PDL (Lab)"]), "insulin": float(b["Insulin"]),
            "tg": float(b["Triglycerides"]), "hdl": float(b["HDL"]), "ethnicity": b["Self-identify"].strip(),
        }
        start = d["Timestamp"].iloc[0]
        out.append({
            "id": f"CGM-{sid:03d}", "cohort": "cgmacros", "group": _group(static["hba1c"]), "dt": STEP,
            "static": static, "g": g, "hr": mean(d["HR"]), "mets": mean(mets),
            "tod": (start.hour + start.minute / 60 + (np.arange(T) + 1) * STEP / 60) % 24,
            "meals": _meals(i[d.index.get_indexer(ml.index)], ml["Meal Type"].str.lower().str.replace(r"[^a-z]", "", regex=True).str.rstrip("s").to_numpy(),
                            {n: ml[n.capitalize()].to_numpy(float) for n in NUTRIENTS}),
        })
    return out


# Carbohydrate, protein, fat, fibre per gram of food as served. Approximate values from standard
# food-composition tables; first matching keyword wins, so specific dishes come before staples.
# ponytail: keyword table, not a nutrition database. The twin's per-patient carb-yield parameter
# absorbs a systematic scale error; swap in a real food-composition API if meal-level accuracy matters.
_FOOD = [
    (r"dumpling|wonton|bun|baozi|pancake|cake|biscuit|cracker|cookie|pastry|pie|pizza", (0.30, 0.08, 0.08, 0.01)),
    (r"steamed bread|mantou|bread|toast", (0.47, 0.08, 0.02, 0.02)),
    (r"porridge|congee|gruel|soup|broth", (0.10, 0.01, 0.00, 0.00)),
    (r"noodle|pasta|vermicelli|spaghetti", (0.25, 0.04, 0.01, 0.01)),
    (r"rice|coarse grain|grain|oat|corn|millet|cereal", (0.26, 0.03, 0.00, 0.01)),
    (r"potato|yam|taro|pumpkin|lotus root|chestnut", (0.15, 0.02, 0.00, 0.02)),
    (r"apple|pear|orange|banana|grape|peach|kiwi|melon|fruit|pomelo|mango|cherry|strawberr|date|juice|cola|sugar|honey|candy", (0.13, 0.00, 0.00, 0.02)),
    (r"milk|yogurt|yoghurt|soy", (0.05, 0.03, 0.03, 0.00)),
    (r"tofu|bean", (0.05, 0.08, 0.04, 0.02)),
    (r"egg", (0.01, 0.13, 0.10, 0.00)),
    (r"pork|beef|mutton|lamb|chicken|duck|fish|shrimp|meat|liver|rib|ham|sausage|crab|squid|cuttlefish|goose|prawn", (0.01, 0.20, 0.10, 0.00)),
    (r"", (0.04, 0.02, 0.00, 0.02)),  # default: vegetables
]


def meal_macros(text):
    """Estimate grams of each nutrient from a free-text meal like 'Rice 100 g\\nBeef 15 g'."""
    tot = np.zeros(4)
    for line in str(text).lower().split("\n"):
        w = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|ml)\b", line)
        if w:
            tot += float(w.group(1)) * np.array(next(v for k, v in _FOOD if re.search(k, line)))
    return tot


def load_shanghai():
    base = RAW / "shanghai"
    summ = pd.read_excel(base / "Shanghai_T2DM_Summary.xlsx").set_index("Patient Number")
    out, dt = [], 15
    for f in sorted((base / "Shanghai_T2DM").glob("*.xls*")):
        b, d = summ.loc[f.stem], pd.read_excel(f)
        d = d.rename(columns={c: "CGM" if str(c).startswith("CGM") else str(c).strip() for c in d.columns})  # header spelling varies by file
        d["Date"] = pd.to_datetime(d["Date"])
        d = d.dropna(subset=["Date"]).sort_values("Date")
        i = _grid(d["Date"], d["Date"].iloc[0], dt)
        T = i.max() + 1
        g = np.full(T, np.nan)
        g[i] = pd.to_numeric(d["CGM"], errors="coerce")
        ml = d[d["Dietary intake"].notna() & (d["Dietary intake"].astype(str).str.strip() != "data not available")]
        mac = np.array([meal_macros(t) for t in ml["Dietary intake"]]).reshape(-1, 4)
        keep = mac[:, 0] > 0
        num = lambda c: pd.to_numeric(b[c], errors="coerce")
        static = {
            "age": float(b["Age (years)"]), "sex": "F" if b["Gender (Female=1, Male=2)"] == 1 else "M",
            "bmi": float(b["BMI (kg/m2)"]), "weight_kg": float(b["Weight (kg)"]),
            "hba1c": 0.0915 * num("HbA1c (mmol/mol)") + 2.15,  # IFCC mmol/mol -> NGSP %
            "fpg": num("Fasting Plasma Glucose (mg/dl)"), "insulin": num("Fasting Insulin (pmol/L)") / 6.0,  # pmol/L -> uU/mL
            "tg": num("Triglyceride (mmol/L)") * 88.57, "hdl": num("High-Density Lipoprotein Cholesterol (mmol/L)") * 38.67,
            "agents": str(b["Hypoglycemic Agents"]), "duration_y": num("Duration of diabetes (years)"),
        }
        start = d["Date"].iloc[0]
        out.append({
            "id": f"SH-{f.stem}", "cohort": "shanghai", "group": "T2D", "dt": dt, "static": static, "g": g,
            "hr": np.full(T, np.nan), "mets": np.full(T, np.nan),
            "tod": (start.hour + start.minute / 60 + (np.arange(T) + 1) * dt / 60) % 24,
            "meals": _meals(i[d.index.get_indexer(ml.index)][keep], "meal", {n: mac[keep, k] for k, n in enumerate(NUTRIENTS)}),
        })
    return out


def load(cohort="cgmacros"):
    """Cached patient records for a cohort ('cgmacros', 'shanghai', 'synthetic' or 'india_<region>', see twin.india)."""
    p = PROC / f"{cohort}.pkl"
    if not p.exists():
        PROC.mkdir(parents=True, exist_ok=True)
        if cohort == "synthetic" or cohort.startswith("india_"):
            from .synth import generate
            recs = generate(region=cohort[6:] if cohort.startswith("india_") else None)
        else:
            recs = {"cgmacros": load_cgmacros, "shanghai": load_shanghai}[cohort]()
        p.write_bytes(pickle.dumps(recs))
    return pickle.loads(p.read_bytes())


def folds(patients, k=5, seed=0):
    """Patient-level folds, stratified by glycaemic group. Returns a list of test-index arrays."""
    rng = np.random.default_rng(seed)
    out = [[] for _ in range(k)]
    j = 0
    for grp in sorted({p["group"] for p in patients}):
        for i in rng.permutation([i for i, p in enumerate(patients) if p["group"] == grp]):
            out[j % k].append(i)
            j += 1
    return [np.array(sorted(f)) for f in out]


def summary(patients):
    return pd.DataFrame([{
        "id": p["id"], "group": p["group"], "days": len(p["g"]) * p["dt"] / 1440, "cgm_cov": np.isfinite(p["g"]).mean(),
        "wear_cov": np.isfinite(p["mets"]).mean(), "meals": len(p["meals"]), "mean_g": np.nanmean(p["g"]),
        "tar180": np.nanmean(p["g"] > 180), **{k: p["static"][k] for k in ("age", "bmi", "hba1c", "fpg", "insulin")},
    } for p in patients])


if __name__ == "__main__":
    info = download()
    print({k: (v["n_files"], v["bytes"]) for k, v in info.items()})
    for c in ("cgmacros", "shanghai"):
        (PROC / f"{c}.pkl").unlink(missing_ok=True)
        s = summary(load(c))
        print(c, len(s), "patients;", s["group"].value_counts().to_dict(), "; meals", s["meals"].sum())
        print(s.drop(columns=["id", "group"]).describe().loc[["mean", "min", "max"]].round(2).to_string())
