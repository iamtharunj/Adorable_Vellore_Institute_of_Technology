"""Download the open-access papers this project relies on into research/papers/ and write a manifest.

Only publisher, arXiv, PubMed Central (via Europe PMC) and official-proceedings links are used.
Nothing behind a paywall or login is fetched; a failed download is recorded, not worked around.
PDFs are not committed (redistribution terms differ per paper); this script reproduces them.
"""
import hashlib
from pathlib import Path

import requests

OUT = Path(__file__).parent / "papers"
ARXIV, EPMC = "https://arxiv.org/pdf/{}", "PMC:{}"  # PMC ids are resolved to the publisher's own open-access PDF
PAPERS = [  # (file name, title, url)
    ("nasem_2023_digital_twins_highlights.pdf", "NASEM (2023) Foundational Research Gaps and Future Directions for Digital Twins: highlights", "https://nap.nationalacademies.org/resource/26894/RH-digital-twins.pdf"),
    ("tudor_2025_digital_twin_review.pdf", "Tudor et al. (2025) npj Digit Med: scoping review of 149 health digital twins vs the NASEM definition", EPMC.format("PMC12484800")),
    ("shamanna_2024_twin_rct_india.pdf", "Shamanna et al. (2024) JACC Adv: digital-twin RCT in Indian T2D", EPMC.format("PMC11450914")),
    ("gutierrez_2025_cgmacros.pdf", "CGMacros data descriptor (2025) Sci Data", "https://www.nature.com/articles/s41597-025-05851-7.pdf"),
    ("zhao_2023_shanghai_t1dm_t2dm.pdf", "Zhao et al. (2023) Sci Data: ShanghaiT1DM and ShanghaiT2DM", EPMC.format("PMC9849330")),
    ("brugger_2025_shanghai_xgboost.pdf", "Brugger et al. (2025) Sci Rep: dysglycaemia prediction on ShanghaiT2DM", EPMC.format("PMC12271334")),
    ("gupta_2025_cgm_indian_t2d.pdf", "Gupta (2025) Cureus: first-sensor CGM metrics in 649 Indian T2D patients", EPMC.format("PMC12066881")),
    ("buffey_2022_light_walking_meta.pdf", "Buffey et al. (2022) Sports Med: light walking breaks and postprandial glucose", EPMC.format("PMC9325803")),
    ("reyna_2020_physionet_sepsis_challenge.pdf", "Reyna et al. (2020) Crit Care Med: PhysioNet/CinC Challenge 2019", EPMC.format("PMC6964870")),
    ("physionet2019_voting_analysis.pdf", "Reyna et al. (2020) Voting of predictive models: analysis of the PhysioNet Challenge 2019 (arXiv 2012.11013)", ARXIV.format("2012.11013")),
    ("kdh_2020_bglp_proceedings.pdf", "KDH@ECAI 2020 proceedings incl. the BGLP Challenge papers", "https://folk.idi.ntnu.no/kerstinb/kdh/KDH_ECAI_2020_Proceedings.pdf"),
    ("zeevi_2015_personalized_nutrition.pdf", "Zeevi et al. (2015) Cell: personalised nutrition by prediction of glycaemic responses", "https://www.wisdom.weizmann.ac.il/~eran/zeevi_cell_2015.pdf"),
    ("glucobench_iclr2024.pdf", "Sergazinov et al. (2024) ICLR: GlucoBench", "https://proceedings.iclr.cc/paper_files/paper/2024/file/4c12e97f2e05304a451e18c9c945036f-Paper-Conference.pdf"),
    ("gibbs_candes_2021_adaptive_conformal.pdf", "Gibbs & Candes (2021) NeurIPS: adaptive conformal inference under distribution shift (arXiv 2106.00170)", ARXIV.format("2106.00170")),
    ("romano_2019_conformalized_quantile_regression.pdf", "Romano et al. (2019) NeurIPS: conformalized quantile regression (arXiv 1905.03222)", ARXIV.format("1905.03222")),
    ("physioseq2seq_2026.pdf", "Tran et al. (2026) PhysioSeq2Seq hybrid ODE + LSTM (arXiv 2605.16860)", ARXIV.format("2605.16860")),
    ("glytwin_2025.pdf", "Arefeen et al. (2025) GlyTwin counterfactual twin (arXiv 2504.09846)", ARXIV.format("2504.09846")),
    ("zhang_2026_chronos_cgm.pdf", "Zhang et al. (2026) foundation-model CGM forecasting benchmark (arXiv 2609.11872)", ARXIV.format("2609.11872")),
    ("kondratyeva_2026_cgmacros.pdf", "Kondratyeva et al. (2026) meal response on CGMacros (arXiv 2609.24453)", ARXIV.format("2609.24453")),
    ("glucose_ml_2025.pdf", "Glucose-ML (2025): catalogue of public CGM datasets (arXiv 2507.14077)", ARXIV.format("2507.14077")),
    ("brist1d_2025.pdf", "BrisT1D dataset (2025) (arXiv 2507.17757)", ARXIV.format("2507.17757")),
    ("raindrop_2022.pdf", "Zhang et al. (2022) ICLR: Raindrop, irregular multivariate time series (arXiv 2110.05357)", ARXIV.format("2110.05357")),
    ("wang_fox_2023_interpretable_cgm.pdf", "Wang & Fox (2023) ML4H: mechanistic meal-response representations", "https://proceedings.mlr.press/v225/wang23a/wang23a.pdf"),
    ("hupa_ucm_2024.pdf", "Hidalgo et al. (2024) Data in Brief: HUPA-UCM diabetes dataset", EPMC.format("PMC11214197")),
    ("ai_readi_protocol_2025.pdf", "AI-READI consortium (2025) BMJ Open: protocol", EPMC.format("PMC11800295")),
]


def resolve(url):
    """PubMed Central blocks scripted PDF downloads, so look the DOI up (Europe PMC API) and use the
    publisher's open-access PDF where the URL pattern is public. Returns (pdf url or None, page for a human)."""
    if not url.startswith("PMC:"):
        return url, url
    page = f"https://pmc.ncbi.nlm.nih.gov/articles/{url[4:]}/"
    try:
        hit = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", timeout=60,
                           params={"query": f"PMCID:{url[4:]}", "format": "json"}).json()["resultList"]["result"][0]
        doi = hit.get("doi", "")
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None, page
    if doi.startswith("10.1038/"):
        return f"https://www.nature.com/articles/{doi[8:]}.pdf", page
    if doi.startswith("10.1007/"):
        return f"https://link.springer.com/content/pdf/{doi}.pdf", page
    return None, page


def main():
    OUT.mkdir(exist_ok=True)
    rows = ["| File | Paper | Source | Status | SHA-256 (first 16) |", "|---|---|---|---|---|"]
    for name, title, url in PAPERS:
        p = OUT / name
        status = "already present"
        url, page = resolve(url)
        if not p.exists() and url is None:
            status = "NOT DOWNLOADED (no scriptable open-access PDF): open the source link in a browser and save the PDF"
        elif not p.exists():
            try:
                r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0 (research download; contact via repository)"})
                if r.ok and r.content[:4] == b"%PDF":
                    p.write_bytes(r.content)
                    status = "downloaded"
                else:
                    status = f"NOT DOWNLOADED (HTTP {r.status_code}, not a PDF): open the source link in a browser"
            except requests.RequestException as e:
                status = f"NOT DOWNLOADED ({type(e).__name__}): open the source link in a browser"
        digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else ""
        rows.append(f"| `{name}` | {title} | {url or page} | {status} | `{digest}` |")
        print(status[:40], name, flush=True)
    (OUT / "MANIFEST.md").write_text("# Downloaded papers\n\nWritten by `research/fetch_papers.py`. PDFs stay local (git-ignored).\n\n" + "\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
