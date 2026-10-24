"""Draws docs/architecture.pdf and docs/architecture.png. Run: python docs/make_architecture.py"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

INK, SECOND, MUTED, LINE, SURFACE = "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#ffffff"
BLUE, BLUE_TINT, NEUTRAL = "#2a78d6", "#e6f0fc", "#f4f4f1"
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"]})
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")


def box(x, y, w, h, title, lines, fill=NEUTRAL, edge=LINE, tcolor=INK, size=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12", facecolor=fill, edgecolor=edge, linewidth=1.2))
    ax.text(x + 0.18, y + h - 0.2, title, fontsize=size + 1.5, fontweight="bold", color=tcolor, va="top")
    ax.text(x + 0.18, y + h - 0.62, "\n".join(lines), fontsize=size, color=SECOND, va="top", linespacing=1.45)


def arrow(a, b, dashed=False, label=None, lxy=None, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=16, linewidth=1.6, color=MUTED if dashed else INK,
                                 linestyle=(0, (5, 4)) if dashed else "solid", connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
    if label:
        ax.text(*lxy, label, fontsize=9.5, color=SECOND, ha="center", va="center", backgroundcolor=SURFACE)


ax.text(0.4, 8.72, "PrandialTwin: one patient, one continuously updated physiological twin", fontsize=17, fontweight="bold", color=INK, va="center")

box(0.4, 6.35, 3.3, 1.85, "Static record (EHR)", ["Age, sex, weight, BMI", "HbA1c, fasting glucose,", "fasting insulin"])
box(0.4, 3.25, 3.3, 2.45, "Dynamic streams", ["CGM every 5 or 15 min", "Meals: carbohydrate, protein,", "fat, fibre, clock time", "Activity: METs (optional)"])
box(4.55, 6.35, 3.2, 1.85, "Labs become a prior", ["Ridge map from labs to each", "twin parameter, learned on", "training patients only"])
box(4.55, 3.25, 3.2, 2.45, "Ensemble Kalman filter", ["128 twin copies run in parallel", "Every reading corrects states", "and parameters together", "No reading: the twin coasts"])
box(8.6, 2.45, 3.3, 5.75, "The virtual patient", ["States, now", "  glucose, insulin action,", "  insulin drive, unexplained drift", "", "Parameters, this person",
                                                     "  basal glucose", "  insulin-mediated disposal", "  gut absorption rate", "  carbohydrate sensitivity", "  activity uptake",
                                                     "", "Held as an ensemble, so the", "twin knows how sure it is"], fill=BLUE_TINT, edge=BLUE)
box(12.75, 6.95, 2.9, 1.25, "Forecast", ["Twin rollout + capped LightGBM,", "averaged with Chronos-2"], size=9.8)
box(12.75, 5.45, 2.9, 1.25, "Honest uncertainty", ["Conformal 90% bands,", "re-calibrated per patient"], size=9.8)
box(12.75, 3.95, 2.9, 1.25, "Early warning", ["P(>180 mg/dL for 15+ min)", "Alert at <= 1 false per day"], size=9.8)
box(12.75, 2.45, 2.9, 1.25, "What-if and advice", ["Re-run the same state, then", "suggest the easiest safe change"], size=9.8)
box(8.6, 0.75, 7.05, 1.3, "Clinician dashboard", ["Record  |  twin state and how it has learned  |  forecast with bands  |  drivers",
                                               "What-if simulator and suggested change, each shown with its own track record"], size=9.8)
box(0.75, 0.75, 7.0, 1.85, "Learned once, from training patients only",
    ["Meal-composition and time-of-day effects, population prior, lab-to-prior map,", "residual and quantile models, conformal scores, alert threshold, fine-tuned Chronos-2.",
     "Checked by patient-level CV, matched real meal pairs, an unseen cohort, synthetic truth"], size=9.8)

arrow((3.7, 7.27), (4.55, 7.27))
arrow((7.75, 7.27), (8.6, 7.27), label="prior", lxy=(8.17, 7.52))
arrow((3.7, 4.47), (4.55, 4.47))
arrow((7.75, 4.9), (8.6, 4.9), label="update", lxy=(8.17, 5.15))
arrow((8.6, 4.05), (7.75, 4.05), label="predict", lxy=(8.17, 3.8))
for y in (7.57, 6.07, 4.57, 3.07):
    arrow((11.9, y), (12.75, y))
arrow((14.2, 2.45), (14.2, 2.05))
arrow((6.15, 2.6), (6.15, 3.25), label="frozen components", lxy=(4.75, 2.92))
# the loop that makes it a twin and not a shadow: advice changes behaviour, behaviour returns as data
ax.plot([12.1, 12.1, 0.25, 0.25], [0.75, 0.3, 0.3, 4.47], color=MUTED, linewidth=1.6, linestyle=(0, (5, 4)))
arrow((0.22, 4.47), (0.42, 4.47), dashed=True)
ax.text(6.2, 0.3, "  clinician advice changes meals and activity, which return as new data  ", fontsize=9.5, color=SECOND, ha="center", va="center",
        style="italic", backgroundcolor=SURFACE)

out = Path(__file__).parent
fig.savefig(out / "architecture.pdf", bbox_inches="tight", facecolor=SURFACE)
fig.savefig(out / "architecture.png", dpi=150, bbox_inches="tight", facecolor=SURFACE)
