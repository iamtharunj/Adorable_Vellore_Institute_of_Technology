"""Clinician dashboard: replay a patient's record and watch their twin update, forecast and answer
what-ifs. Run with `streamlit run app.py`. Works out of the box on the synthetic cohort; the real
cohorts appear once `python -m twin.data` has downloaded them."""
import gzip
import json
import pickle

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from twin import core
from twin.data import PROC, ROOT, load
from twin.hybrid import HORIZONS
from twin.report import C, fan

INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
COHORTS = {"Synthetic patients (simulated, India-style meals)": "synthetic", "CGMacros (real, de-identified, USA)": "cgmacros",
           "ShanghaiT2DM (real, de-identified, China; no wearable)": "shanghai",
           **{f"India, {r.title()} (simulated; regional plates and ICMR-INDIAB population)": f"india_{r}"
              for r in ("north", "south", "east", "west", "central", "northeast")}}  # generated on first open (about 45 s), then cached
st.set_page_config(page_title="PrandialTwin", layout="wide")


@st.cache_resource
def models():
    with gzip.open(ROOT / "results" / "models.pkl.gz", "rb") as f:
        m = pickle.load(f)
    fold = PROC / "fold_models.pkl.gz"  # present after `python -m twin.evaluate`: lets real patients be replayed held-out
    if fold.exists():
        with gzip.open(fold, "rb") as f:
            m["folds"] = pickle.load(f)
    return m


@st.cache_resource
def cohort(name):
    return {p["id"]: p for p in load(name)}


@st.cache_resource
def chronos2(name):
    """Fine-tuned Chronos-2 forecasts cached by `python -m twin.chronos_baseline` (held-out, every 15 min), keyed by (id, i)."""
    f = PROC / {"cgmacros": "chronos.pkl", "shanghai": "chronos_ext.pkl"}.get(name, "-")
    return pd.read_pickle(f).set_index(["id", "i"])[[f"c2ft{h}" for h in HORIZONS]] if f.exists() else None


@st.cache_resource
def run_twin(name, pid):
    """Assimilate the whole record once; the replay clock then only reveals it step by step."""
    p, m = cohort(name)[pid], models()
    held_out = next((f for f in m.get("folds", {}).values() if pid in f["test"]), None)
    mod = held_out or m["matched" if p["dt"] == 15 else "all"]
    S, L, _ = core.assimilate(p, *core.prior(mod["pop"], p["static"]), mod["pop"]["slow"])
    hours = np.arange(0, len(p["g"]), 60 // p["dt"])
    rise = np.array([core.standard_meal_rise(L[j], p["static"]["weight_kg"], mod["pop"]["slow"]) for j in hours])
    return p, mod, S, L, hours, rise, held_out is not None


def layout(fig, h, ytitle):
    fig.update_layout(height=h, margin=dict(l=60, r=20, t=50, b=50), plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb", font=dict(color=INK, size=12),
                      legend=dict(orientation="h", y=1.0, yanchor="bottom", x=0), hovermode="x unified")
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=ytitle, automargin=True)
    return fig


def band(fig, t, lo, hi, color, alpha, name=None):
    rgba = f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},{alpha})"
    fig.add_trace(go.Scatter(x=np.r_[t, t[::-1]], y=np.r_[hi, lo[::-1]], fill="toself", fillcolor=rgba, line=dict(width=0), hoverinfo="skip",
                             name=name, showlegend=name is not None))


def from_url(key, default, lo, hi):
    """A slider default taken from the URL when it is a sensible number."""
    v = st.query_params.get(key, "")
    return int(np.clip(int(v), lo, hi)) if v.isdigit() else default


def clock(p, i):
    return f"Day {i * p['dt'] // 1440 + 1}, {int(p['tod'][i]):02d}:{int(p['tod'][i] % 1 * 60):02d}"


# ---------------------------------------------------------------- sidebar: who and when
available = {k: v for k, v in COHORTS.items() if v == "synthetic" or v.startswith("india_") or (PROC / f"{v}.pkl").exists()}
st.sidebar.title("PrandialTwin")
st.sidebar.caption("Research prototype. Not a medical device; not for treatment decisions.")
q = st.query_params  # ?cohort=cgmacros&patient=CGM-012&i=936 reopens one exact moment (used for the demo)
names = list(available)
name = available[st.sidebar.selectbox("Cohort", names, index=next((n for n, k in enumerate(names) if available[k] == q.get("cohort")), 0))]
ids = list(cohort(name))
pid = st.sidebar.selectbox("Patient", ids, index=ids.index(q["patient"]) if q.get("patient") in ids else 0, format_func=lambda k: f"{k} ({cohort(name)[k]['group']})")
p, mod, S, L, hours, rise, held_out = run_twin(name, pid)
dt, g, H = p["dt"], p["g"], 180 // p["dt"]
grid = set(range(60 // dt, len(g) - H - 1, 15 // dt)) | {int(k) for k in p["meals"]["idx"] if 60 // dt <= k < len(g) - H - 1}
valid = [i for i in sorted(grid) if np.isfinite(g[i])]  # every 15 min, plus the moment of each logged meal
key = f"i_{name}_{pid}"
if key not in st.session_state:
    first = [i for i in p["meals"]["idx"] if i >= 3 * 1440 // dt and i in set(valid)]
    asked = int(q["i"]) if q.get("i", "").isdigit() and pid == q.get("patient") else -1
    st.session_state[key] = asked if asked in set(valid) else first[0] if first else valid[len(valid) // 2]
b1, b2, b3 = st.sidebar.columns(3)
step = lambda k: st.session_state.update({key: valid[int(np.clip(np.searchsorted(valid, st.session_state[key]) + k, 0, len(valid) - 1))]})
b1.button("−1 h", on_click=step, args=(-4,), width="stretch")
b2.button("+15 min", on_click=step, args=(1,), width="stretch")
nxt = [i for i in p["meals"]["idx"] if i > st.session_state[key] and i in set(valid)]
b3.button("Next meal", on_click=lambda: st.session_state.update({key: nxt[0]}) if nxt else None, width="stretch")
i = st.sidebar.select_slider("Replay clock", options=valid, key=key, format_func=lambda k: clock(p, k))
reveal = st.sidebar.toggle("Reveal what happened next", value=q.get("reveal") == "1", help="Retrospective only. The twin never sees these readings.")
st.sidebar.caption({"cgmacros": "De-identified research participant (CGMacros, PhysioNet).", "shanghai": "De-identified inpatient recording (ShanghaiT2DM)."}.get(
                       name, "Simulated record. No real person." + (f" Home state: {p['static']['state']}." if "state" in p["static"] else ""))
                   + (" Replayed held-out: this patient was never used to fit the models shown." if held_out else
                      " Population models were fitted on CGMacros." if name != "cgmacros" else " In-sample replay: run `python -m twin.evaluate` for held-out models."))

# ---------------------------------------------------------------- the virtual patient
s = p["static"]
f = fan(p, i, S, L, mod["pop"], mod["M"])
thr = mod["M"]["alert_thr"]["hybrid"]
st.subheader(f"{pid} · {clock(p, i)}")
c = st.columns([1.3, 1, 1, 1, 1])
homa = s.get("fpg", np.nan) * s.get("insulin", np.nan) / 405
c[0].markdown(f"**Record (static)**  \n{s.get('age', '?'):.0f} y, {s.get('sex', '?')}, BMI {s.get('bmi', np.nan):.1f}  \n"
              f"HbA1c **{s.get('hba1c', np.nan):.1f}%** · fasting glucose **{s.get('fpg', np.nan):.0f}** mg/dL  \n"
              f"Fasting insulin {s.get('insulin', np.nan):.1f} µU/mL · HOMA-IR {homa:.1f}  \n"
              + (f"Therapy: {s['agents']}" if "agents" in s else f"Therapy: {s['medications']}" if "medications" in s else f"Group: {p['group']}"))
gb_now, gb_sd = np.exp(L[i, :, 0]).mean(), np.exp(L[i, :, 0]).std()
j = np.searchsorted(hours, i, side="right") - 1
pk_now, pk0 = gb_now + rise[j].mean(), np.exp(L[0, :, 0]).mean() + rise[0].mean()
trait = rise[: max(j - 24, 1)].mean() if j > 30 else np.nan  # everything before the last 24 h
today = rise[max(j - 24, 0): j + 1].mean()
c[1].metric("Basal glucose (twin)", f"{gb_now:.0f} mg/dL")
c[1].caption(f"±{gb_sd:.0f} mg/dL. Lab fasting glucose: {s.get('fpg', np.nan):.0f}")
c[2].metric("Standard-meal peak", f"{pk_now:.0f} mg/dL")
c[2].caption(f"Expected peak after 50 g carbohydrate. {pk_now - pk0:+.0f} mg/dL since the lab-based start")
c[3].metric("Carb response today", "learning" if np.isnan(trait) else f"{(today / trait - 1) * 100:+.0f}%")
c[3].caption("Own baseline needs more than a day of data" if np.isnan(trait) else "Versus this patient's own baseline (rise per standard meal, last 24 h vs before)")
c[4].metric("Twin uncertainty", f"{(rise[j].std() / max(rise[0].std(), 1e-9) - 1) * 100:+.0f}%")
c[4].caption(f"Versus day 1, after {np.isfinite(g[: i + 1]).sum():,} readings and {(p['meals']['idx'] <= i).sum()} meals")

# the whole record so far: where we are and what the patient has been through
tl = go.Figure()
tl.add_hrect(y0=70, y1=180, fillcolor=GRID, opacity=0.35, line_width=0)
tl.add_trace(go.Scatter(x=np.arange(i + 1) * dt / 1440 + 1, y=g[: i + 1], mode="lines", line=dict(color=INK, width=1), name="CGM (target range shaded)"))
mm = p["meals"][p["meals"]["idx"] <= i]
tl.add_trace(go.Scatter(x=mm["idx"] * dt / 1440 + 1, y=np.full(len(mm), 55), mode="markers", marker=dict(symbol="line-ns-open", size=9, color=C["lgbm"]),
                        name="Logged meal", text=[f"{k}: {c_:.0f} g carbohydrate" for k, c_ in zip(mm["kind"], mm["carbs"])], hoverinfo="text"))
st.plotly_chart(layout(tl, 200, "mg/dL").update_xaxes(range=[1, len(g) * dt / 1440 + 1], dtick=1, tickprefix="Day ").update_layout(hovermode="closest"),
                width="stretch", theme=None)

left, right = st.columns([1.6, 1])
with left:
    st.markdown(f"**Forecast** · P(glucose above 180 mg/dL for 15+ min within 2 h) = **{f['p_alert']:.0%}** "
                + ("· already above 180" if g[i] > 180 else f"· {'ALERT' if f['p_alert'] >= thr else 'no alert'} (alert threshold {thr:.0%})"))
    fig, a = go.Figure(), max(i - 6 * 60 // dt, 0)
    t_past = (np.arange(a, i + 1) - i) * dt
    band(fig, f["t"], f["pct"][0], f["pct"][4], C["hybrid"], 0.10, "90% of twin trajectories")
    band(fig, f["t"], f["pct"][1], f["pct"][3], C["hybrid"], 0.18)
    fig.add_trace(go.Scatter(x=t_past, y=g[a:i + 1], mode="lines", line=dict(color=INK, width=2), name="CGM"))
    fig.add_trace(go.Scatter(x=f["t"], y=f["pct"][2], mode="lines", line=dict(color=C["hybrid"], width=2), name="Twin forecast (median)"))
    hy = f["hybrid"]
    fig.add_trace(go.Scatter(x=list(hy), y=[v[0] for v in hy.values()], mode="markers", marker=dict(color=INK, size=9, line=dict(color="#fcfcfb", width=2)),
                             error_y=dict(type="data", symmetric=False, array=[v[2] - v[0] for v in hy.values()], arrayminus=[v[0] - v[1] for v in hy.values()],
                                          color=INK, thickness=1.2), name="Hybrid forecast, 90% band"))
    c2 = chronos2(name)
    if c2 is not None and (pid, i) in c2.index:  # the reported forecast: hybrid and fine-tuned Chronos-2 averaged, as in RESULTS section 10
        ens = {h: (hy[h][0] + c2.loc[(pid, i), f"c2ft{h}"]) / 2 for h in HORIZONS}
        fig.add_trace(go.Scatter(x=list(ens), y=list(ens.values()), mode="markers", marker=dict(color=C["ens"], size=11, symbol="diamond", line=dict(color="#fcfcfb", width=2)),
                                 name="Twin + Chronos-2 average (reported forecast; no band yet)"))
    elif c2 is not None:
        st.caption("Twin + Chronos-2 average: cached on the 15-min grid only, not at this logged meal. Step +15 min to see it.")
    if reveal:
        fig.add_trace(go.Scatter(x=f["t"], y=g[i + 1:i + 1 + H], mode="markers", marker=dict(color=MUTED, size=5), name="What happened next"))
    for _, m in p["meals"][(p["meals"]["idx"] >= a) & (p["meals"]["idx"] <= i)].iterrows():
        fig.add_annotation(x=(m["idx"] - i) * dt, y=0, yref="paper", text=f"meal {m['carbs']:.0f} g", showarrow=True, arrowhead=0, ay=-22, font=dict(size=11, color=INK))
    fig.add_hline(y=180, line=dict(color=MUTED, width=1), annotation_text="180 mg/dL", annotation_position="top left")
    fig.add_vline(x=0, line=dict(color=MUTED, width=1))
    st.plotly_chart(layout(fig, 380, "Glucose (mg/dL)").update_xaxes(title="Minutes from now"), width="stretch", theme=None)

with right:
    st.markdown("**Why this forecast** · what each driver adds to the expected 3-h peak")
    peak = lambda rec, St: float(core.rollout(rec, [i], St, L, H, mod["pop"]["slow"]).max(-1).mean())
    S0 = S.copy()
    S0[i, :, 3] = 0
    drivers = {"Carbohydrate on board": f["peak"] - peak(dict(p, meals=p["meals"].iloc[:0]), S),
               "Unexplained drift right now": f["peak"] - peak(p, S0),
               "Recent activity": f["peak"] - peak(dict(p, mets=np.full(len(g), 1.2)), S)}
    fig = go.Figure(go.Bar(x=list(drivers.values()), y=[f"{k}  {v:+.0f}" for k, v in drivers.items()], orientation="h", marker_color=C["hybrid"], width=0.45))
    fig.add_vline(x=0, line=dict(color=MUTED, width=1))
    st.plotly_chart(layout(fig, 210, "").update_xaxes(title="mg/dL added to the expected peak").update_layout(hovermode="closest", showlegend=False, margin=dict(l=215)), width="stretch", theme=None)
    st.caption(f"Expected peak {f['peak']:.0f} mg/dL from {g[i]:.0f} now. Each bar is the same forecast re-run with that driver removed, so bars need not add up.")
    st.markdown("**The twin is learning** · basal glucose estimate since day 1")
    hh = hours[: j + 1]
    gm, gs = np.exp(L[hh, :, 0]).mean(1), np.exp(L[hh, :, 0]).std(1)
    fig = go.Figure()
    band(fig, hh * dt / 1440, gm - 1.64 * gs, gm + 1.64 * gs, C["hybrid"], 0.15)
    fig.add_trace(go.Scatter(x=hh * dt / 1440, y=gm, mode="lines", line=dict(color=C["hybrid"], width=2), name="Twin"))
    if np.isfinite(s.get("fpg", np.nan)):
        fig.add_hline(y=s["fpg"], line=dict(color=MUTED, width=1), annotation_text="lab fasting glucose", annotation_position="bottom right")
    st.plotly_chart(layout(fig, 200, "mg/dL").update_xaxes(title="Days of data").update_layout(showlegend=False), width="stretch", theme=None)

# ---------------------------------------------------------------- what-if
st.markdown("### What if?")
meal_now = p["meals"][p["meals"]["idx"] == i]
w = st.columns([1, 1, 1, 1.4])
if len(meal_now):
    portion = w[0].slider(f"Portion of this meal ({meal_now['carbs'].iloc[0]:.0f} g carbohydrate logged)", 0, 150, from_url("portion", 100, 0, 150) // 10 * 10, 10, format="%d%%") / 100
    add = None
else:
    portion = 1.0
    grams = w[0].slider("Eat now: carbohydrate (g)", 0, 120, 0, 5)
    add = (grams, grams * 0.25, grams * 0.2, grams * 0.08) if grams else None
walk = w[1].slider("Walk after the meal (min)", 0, 45, from_url("walk", 0, 0, 45) // 5 * 5, 5)
start = w[2].slider("Walk starts after (min)", 0, 60, 15, 5)
base = fan(p, i, S, L, mod["pop"], mod["M"], record=core.scenario(p, i))
what = fan(p, i, S, L, mod["pop"], mod["M"], record=core.scenario(p, i, carb_scale=portion, add_meal=add, walk_min=walk, walk_start=start))
changed = portion != 1.0 or add is not None or walk > 0
w[3].metric("Expected 3-h peak", f"{what['peak']:.0f} mg/dL", f"{what['peak'] - base['peak']:+.0f} mg/dL vs as planned" if changed else None, delta_color="inverse")
w[3].metric("Twin's P(15+ min above 180 within 3 h)", f"{what['p_twin_raw']:.0%}",
            f"{(what['p_twin_raw'] - base['p_twin_raw']) * 100:+.0f} points" if changed else None, delta_color="inverse")
fig = go.Figure()
band(fig, base["t"], base["pct"][1], base["pct"][3], MUTED, 0.15)
band(fig, what["t"], what["pct"][1], what["pct"][3], C["twin"], 0.18)
fig.add_trace(go.Scatter(x=base["t"], y=base["pct"][2], mode="lines", line=dict(color=MUTED, width=2), name="As planned"))
fig.add_trace(go.Scatter(x=what["t"], y=what["pct"][2], mode="lines", line=dict(color=C["twin"], width=2), name="What-if"))
fig.add_hline(y=180, line=dict(color=MUTED, width=1))
st.plotly_chart(layout(fig, 300, "Glucose (mg/dL)").update_xaxes(title="Minutes from now"), width="stretch", theme=None)
metrics = json.loads((ROOT / "results" / "metrics.json").read_text())
if len(meal_now):  # the twin tries every action on its own state and suggests the least effort that keeps the risk under 30%
    k, pr = core.recommend(p, i, S, L, mod["pop"]["slow"])
    eat, walk_k = core.ACTIONS[k]
    change = " and ".join(x for x in (f"eat {eat:.0%} of this meal" if eat < 1 else "", f"walk {walk_k} min from 15 min after it" if walk_k else "") if x)
    st.markdown("**Suggested change** · " + (f"none needed: the twin puts the chance of a spike at {pr[0]:.0%} as planned." if k == 0 else
                f"{change}: the twin's chance of a spike goes from {pr[0]:.0%} to {pr[k]:.0%}." + ("" if pr[k] < 0.3 else " No single change tried gets it under 30%; this is the safest.")))
    rec = metrics.get("recommendations")
    if rec:
        st.caption(f"Tested on {rec['patients']} synthetic patients where every action's true outcome is known: choosing this way cut meals with a true spike from "
                   f"{rec['policies']['nothing']['excursions'][0]:.0%} to {rec['policies']['twin']['excursions'][0]:.0%} (an oracle reached "
                   f"{rec['policies']['oracle']['excursions'][0]:.0%}). Simulated patients, not a trial. Options tried: portion 100/75/50%, walk 0/15/30 min.")
wi = metrics["whatif"]
st.caption(f"Track record on real data (CGMacros, held-out patients): the twin got the direction right in {wi['carbs']['twin']['sign_agreement'][0]:.0%} of "
           f"{wi['carbs']['pairs']} matched meal pairs that differed in carbohydrate, and in {wi['activity']['twin']['sign_agreement'][0]:.0%} of {wi['activity']['pairs']} "
           f"pairs that differed in post-meal activity. Observed effect of an active hour after a meal: {wi['activity']['observed_mean_diff'][0]:.0f} mg/dL; the twin attributes "
           f"{wi['activity']['twin_attributed_effect'][0]:.0f} mg/dL. What-if probabilities are the twin's own estimate, not the calibrated alert probability. "
           "Lifestyle scenarios only: no medication or insulin advice.")

with st.expander("How well does this work? Evidence and limits"):
    A, E = metrics["accuracy"], metrics["external"]["modality_matched_full"]
    X = metrics.get("external_all_models", {})
    both = (f"- With fine-tuned Chronos-2 averaged in (the diamonds on the forecast, real patients only, from cached held-out forecasts): **{A['60']['ens'][0]:.1f}** at home, "
            f"**{X['60']['ens'][0]:.1f}** abroad. Chronos-2 alone: {A['60']['c2ft'][0]:.1f} and {X['60']['c2ft'][0]:.1f}.\n") if "ens" in A["60"] and "ens" in X.get("60", {}) else ""
    st.markdown(f"- Unseen CGMacros patients, 60-min RMSE: hybrid **{A['60']['hybrid'][0]:.1f}**, population LightGBM {A['60']['lgbm'][0]:.1f}, persistence {A['60']['pers'][0]:.1f} mg/dL.\n"
                f"- Unseen country and device (ShanghaiT2DM), 60-min RMSE: hybrid **{E['60']['hybrid'][0]:.1f}**, LightGBM {E['60']['lgbm'][0]:.1f}, persistence {E['60']['pers'][0]:.1f} mg/dL.\n"
                + both +
                f"- 90% bands adapted per patient cover {metrics['uncertainty']['60']['hybrid_aci']['coverage']:.0%} of outcomes; worst patient {metrics['uncertainty']['60']['hybrid_aci']['patient_min']:.0%}.\n"
                "- Not validated on Indian patients, not prospectively tested, no insulin or drug model. Full tables: `results/RESULTS.md`.")
    for name_ in ("accuracy", "calibration", "whatif_validation"):
        st.image(str(ROOT / "results" / "figures" / f"{name_}.png"))
