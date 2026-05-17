#!/usr/bin/env python3
"""
Exploratory plot: running-max training metric per generation across all
completed link adaptation runs. Not part of the paper figures — used to
visualise the convergence behaviour and late-generation improvements
that motivate the consolidation argument.

Output: paper/figures/explore-running-max.{pdf,png}
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "lines.linewidth": 1.7,
    "lines.markersize": 5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
})

REPO = Path("/home/jjn/repos/the-ai-telco-engineer")
FIG_DIR = REPO / "paper" / "figures"

OLLA = 3.4196
GPT_OSS_120B = 3.3976
GPT_5_4 = 3.5370

# (label, task_dir, color, marker, linestyle)
runs = [
    ("LA-F1  (Opus → Gemma4)",       "link_adaptation_f1", "tab:blue",   "^", "-"),
    ("LA-G0  (Opus → Qwen3)",        "link_adaptation_g0", "tab:cyan",   "v", "-"),
    ("LA-F0  (Sonnet → Gemma4)",     "link_adaptation_f0", "tab:orange", "s", "-"),
    ("LA-A0  (Gemma4 → Gemma4)",     "link_adaptation_a0", "tab:gray",   "o", "-"),
    ("LA-A1  (Gemma4 → Gemma4 + v1)","link_adaptation_a1", "0.55",       "o", "--"),
    ("LA-C0  (Nemotron → Gemma4)",   "link_adaptation",    "tab:green",  "D", "-"),
    ("LA-C1  (Nemotron → Gemma4+v1)","link_adaptation_c1", "tab:olive",  "D", "--"),
    ("LA-B0  (Qwen3 → Qwen3)",       "link_adaptation_b0", "tab:red",    "x", "-"),
]


def running_max(task_dir):
    data = json.load(open(REPO / "tasks" / task_dir / "workspaces" / "leaderboard.json"))
    cands = [c for cl in data["clusters"].values() for c in cl]
    by_gen = {}
    for c in cands:
        by_gen.setdefault(c["generation"], []).append(c)
    gens = sorted(by_gen)
    if not gens:
        return np.array([]), np.array([])
    total = max(gens) + 1
    out = np.full(total, np.nan)
    running = float("-inf")
    for g in range(total):
        succ = [c["metric"] for c in by_gen.get(g, []) if c.get("success")]
        if succ:
            running = max(running, max(succ))
        if running > float("-inf"):
            out[g] = running
    return np.arange(total), out


fig, ax = plt.subplots(figsize=(7.2, 4.5))

for label, task_dir, color, marker, ls in runs:
    gens, best = running_max(task_dir)
    ax.plot(gens, best, marker=marker, color=color, linestyle=ls, label=label, alpha=0.95)
    # mark final-best generation with a larger star
    if len(best) > 0:
        # find first index reaching the global max
        final = np.nanmax(best)
        idx = next(i for i, v in enumerate(best) if np.isclose(v, final))
        ax.plot(gens[idx], best[idx], marker="*", markersize=14,
                markerfacecolor=color, markeredgecolor="black",
                markeredgewidth=0.7, linestyle="None", zorder=5)

# Reference lines
for y, lbl, ls in [(OLLA, "OLLA  (3.42)", "--"),
                   (GPT_OSS_120B, "GPT-OSS 120B  (3.40)", ":"),
                   (GPT_5_4, "GPT-5.4  (3.54)", "-.")]:
    ax.axhline(y, color="black", linewidth=0.7, linestyle=ls, alpha=0.6)
    ax.annotate(lbl, xy=(1.0, y), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points",
                fontsize=8, color="black", alpha=0.8, va="center", ha="left")

ax.set_xlabel("Generation")
ax.set_ylabel("Running-max best training SE  (bps/Hz)")
ax.set_title("Running-max best score per generation, all configurations\n"
             "(★ marks the generation in which each run's all-time best was first achieved)",
             fontsize=10, pad=8)
ax.set_xlim(-0.5, 20.5)
ax.set_xticks(range(0, 21, 2))
ax.set_ylim(0.4, 3.65)
ax.grid(True, alpha=0.25)
ax.legend(loc="lower right", framealpha=0.95, frameon=True,
          fancybox=False, edgecolor="black", ncol=2, fontsize=8)

fig.subplots_adjust(left=0.10, right=0.82, top=0.91, bottom=0.10)
fig.savefig(FIG_DIR / "explore-running-max.pdf")
fig.savefig(FIG_DIR / "explore-running-max.png")
print(f"Wrote {FIG_DIR}/explore-running-max.{{pdf,png}}")
