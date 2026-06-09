#!/usr/bin/env python3
"""Build publication-ready figures from the A/B evaluation.

Produces two PNG figures (300 dpi) for the paper:
  - fig_metrics.png   : grouped bars, Baseline vs Detector on the 4 quality metrics
  - fig_latency.png   : mean + P95 latency comparison (log scale)

Numbers are taken from eval/evaluate.py on ab_results_reasoning.xlsx
(N=100 claims, FEVER+LIAR) and the latency sidecar (N=15).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

# --- Data (from eval/evaluate.py, ab_results_reasoning.xlsx) ---
METRICS = ["Accuracy", "Precision\n(macro)", "Recall\n(macro)", "F1-score\n(macro)"]
BASELINE = [0.360, 0.806, 0.348, 0.485]
DETECTOR = [0.450, 0.818, 0.437, 0.569]

LAT_LABELS = ["Mean", "P95"]
LAT_BASE = [1.70, 1.88]
LAT_DET = [10.54, 12.97]

C_BASE = "#9aa7b4"   # muted grey-blue (baseline)
C_DET = "#2e6fb0"    # blue (detector)


def fig_metrics(path="eval/fig_metrics.png"):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = range(len(METRICS))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], BASELINE, w, label="Базовая LLM (baseline)",
                color=C_BASE, edgecolor="white")
    b2 = ax.bar([i + w / 2 for i in x], DETECTOR, w, label="Мультиагентный детектор",
                color=C_DET, edgecolor="white")
    for bars in (b1, b2):
        for r in bars:
            ax.annotate(f"{r.get_height():.3f}", (r.get_x() + r.get_width() / 2, r.get_height()),
                        ha="center", va="bottom", fontsize=8.5, xytext=(0, 1),
                        textcoords="offset points")
    ax.set_xticks(list(x))
    ax.set_xticklabels(METRICS, fontsize=9.5)
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.set_ylabel("Значение метрики")
    ax.set_title("Сравнение качества классификации (выборка FEVER+LIAR, N=100)",
                 fontsize=11, pad=10)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    print("saved", path)


def fig_latency(path="eval/fig_latency.png"):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    x = range(len(LAT_LABELS))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], LAT_BASE, w, label="Базовая LLM",
                color=C_BASE, edgecolor="white")
    b2 = ax.bar([i + w / 2 for i in x], LAT_DET, w, label="Детектор",
                color=C_DET, edgecolor="white")
    for bars in (b1, b2):
        for r in bars:
            ax.annotate(f"{r.get_height():.2f}s", (r.get_x() + r.get_width() / 2, r.get_height()),
                        ha="center", va="bottom", fontsize=8.5, xytext=(0, 1),
                        textcoords="offset points")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Среднее", "P95"], fontsize=10)
    ax.set_ylabel("Время обработки одного утверждения, с")
    ax.set_title("Задержка обработки (latency)", fontsize=11, pad=10)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 15)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    print("saved", path)


if __name__ == "__main__":
    fig_metrics()
    fig_latency()
