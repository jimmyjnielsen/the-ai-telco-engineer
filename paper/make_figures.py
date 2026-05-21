#!/usr/bin/env python3
"""
Generate Figures 2 and 3 for the IEEE Wireless Communications Magazine paper
on hybrid cloud-local LLM agents for wireless algorithm discovery.

Run from connectivity1, in the ai-telco-engineer repo root. Outputs:
    paper/figures/fig2-convergence.pdf
    paper/figures/fig2-convergence.png
    paper/figures/fig3-token-economy.pdf
    paper/figures/fig3-token-economy.png

Data sources:
    Fig 2: tasks/link_adaptation_{a0,f0,f1}/workspaces/leaderboard.json
    Fig 3: hardcoded measured/estimated values from the study notes
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ─── IEEE-friendly plotting defaults ─────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "lines.linewidth": 1.5,
    "lines.markersize": 4,
    "axes.linewidth": 0.7,
    "grid.linewidth": 0.4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,   # truetype (embed)
    "ps.fonttype": 42,
})

# Paper baselines (Aït Aoudia et al., 2026)
OLLA = 3.4196
GPT_OSS_120B = 3.3976
GPT_5_4 = 3.5370

REPO = Path(__file__).resolve().parent.parent
FIG_DIR = REPO / "paper" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# Figure 2 — Convergence trajectory and success rate
# ═══════════════════════════════════════════════════════════════════════

def load_per_generation(task_dir: str):
    """Return (gens, eval_best, success_rate) arrays.

    eval_best is the held-out-set spectral efficiency of the running-best
    workspace at each generation (by training metric). Values are read from
    paper/figures/per_gen_eval_se.json, which is produced by
    /tmp/per_gen_eval.py running evaluate_final.py on each unique running-
    best workspace. The success_rate is derived directly from the leaderboard.
    """
    # success_rate from leaderboard
    lb_path = REPO / "tasks" / task_dir / "workspaces" / "leaderboard.json"
    data = json.load(open(lb_path))
    candidates = [c for cluster in data["clusters"].values() for c in cluster]
    by_gen: dict[int, list[dict]] = {}
    for c in candidates:
        by_gen.setdefault(c["generation"], []).append(c)
    max_gen = max(by_gen) if by_gen else -1

    # eval_best from per_gen_eval_se.json
    eval_json = json.load(open(REPO / "paper" / "figures" / "per_gen_eval_se.json"))
    entry = next((v for v in eval_json.values() if v["task_dir"] == task_dir), None)
    if entry is None:
        raise RuntimeError(f"No per-gen eval data for {task_dir}; re-run per_gen_eval.py")

    gens = []
    eval_best = []
    success_rate = []
    for row in entry["per_gen"]:
        g, ws, train_metric, eval_se = row
        gens.append(g)
        eval_best.append(eval_se if eval_se is not None else np.nan)
        succ_count = sum(1 for c in by_gen.get(g, []) if c.get("success"))
        total = len(by_gen.get(g, [])) or 1
        success_rate.append(succ_count / total)
    return np.array(gens), np.array(eval_best), np.array(success_rate)


def make_fig2():
    # Configurations (manager varies, agents fixed = Gemma4-26B).
    # Labels use the short Manager-Agent naming used in Table I.
    configs = [
        ("link_adaptation_a1", "G4-G4 (local Gemma4 manager)",   "tab:gray",   "o", "-"),
        ("link_adaptation_f0", "So-G4 (Sonnet 4.6 manager)",     "tab:orange", "s", "-"),
        ("link_adaptation_f1", "Op-G4 (Opus 4.7 manager)",       "tab:blue",   "^", "-"),
    ]

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(3.5, 4.2), sharex=True,
        gridspec_kw={"height_ratios": [1.4, 1.0], "hspace": 0.10},
    )

    # ── top: running-best on eval scale, zoomed to where the action is ──
    for task_dir, label, color, marker, style in configs:
        gens, best, _ = load_per_generation(task_dir)
        # plot only points within the visible range
        mask = best >= 3.15
        ax_top.plot(gens[mask], best[mask], marker=marker, color=color,
                    linestyle=style, label=label)

    # Reference lines — labels in the right-hand margin to avoid stacking
    refs = [(OLLA, "OLLA", "--"),
            (GPT_OSS_120B, "GPT-OSS 120B", ":"),
            (GPT_5_4, "GPT-5.4", "-.")]
    for y, lbl, ls in refs:
        ax_top.axhline(y, color="black", linewidth=0.6, linestyle=ls, alpha=0.55)
        ax_top.annotate(lbl, xy=(1.0, y), xycoords=("axes fraction", "data"),
                        xytext=(3, 0), textcoords="offset points",
                        fontsize=7, color="black", alpha=0.8, va="center", ha="left")

    ax_top.set_ylabel("Eval-set SE (bps/Hz)")
    ax_top.set_ylim(3.15, 3.65)
    ax_top.set_yticks([3.2, 3.3, 3.4, 3.5, 3.6])
    ax_top.grid(True, alpha=0.25)
    ax_top.legend(loc="lower right", framealpha=0.95, frameon=True,
                  fancybox=False, edgecolor="black")

    # ── bottom: success rate ─────────────────────────────────────────────
    for task_dir, label, color, marker, style in configs:
        gens, _, success = load_per_generation(task_dir)
        ax_bot.plot(gens, success * 100, marker=marker, color=color,
                    linestyle=style, alpha=0.85)

    ax_bot.set_xlabel("Generation")
    ax_bot.set_ylabel("Agent success rate (%)")
    ax_bot.set_ylim(-5, 105)
    ax_bot.set_yticks([0, 25, 50, 75, 100])
    ax_bot.grid(True, alpha=0.25)
    ax_bot.set_xticks(range(0, 20, 2))

    # Panel labels
    ax_top.text(0.02, 0.97, "(a)", transform=ax_top.transAxes,
                fontsize=9, fontweight="bold", va="top", ha="left")
    ax_bot.text(0.02, 0.97, "(b)", transform=ax_bot.transAxes,
                fontsize=9, fontweight="bold", va="top", ha="left")

    # Tight layout, leaving room for the right-margin reference labels
    fig.subplots_adjust(left=0.14, right=0.82, top=0.97, bottom=0.10)

    fig.savefig(FIG_DIR / "fig2-convergence.pdf")
    fig.savefig(FIG_DIR / "fig2-convergence.png")
    print(f"Wrote {FIG_DIR}/fig2-convergence.{{pdf,png}}")


# ═══════════════════════════════════════════════════════════════════════
# Figure 3 — Cloud token economy: hybrid vs fully-cloud
# ═══════════════════════════════════════════════════════════════════════

def make_fig3():
    # Measured (manager) and estimated (agent) token counts per 10-gen run.
    # Manager values: Anthropic console export (sum of input + output tokens).
    # Agent values for fully-cloud estimates: agent_calls × avg 4.5K input + 0.8K output.

    deployments = [
        # short label,           manager_kt,  agent_kt,  is_estimated
        ("Hybrid\nF0",            338,         0,         False),
        ("Hybrid\nF1",            538,         0,         False),
        ("Full-cloud\nF0-equiv.", 338,         2500,      True),
        ("Full-cloud\nF1-equiv.", 538,         2500,      True),
    ]

    labels = [d[0] for d in deployments]
    mgr_tokens = np.array([d[1] for d in deployments])
    agent_tokens = np.array([d[2] for d in deployments])
    total_tokens = mgr_tokens + agent_tokens

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    x = np.arange(len(deployments))
    width = 0.6

    ax.bar(x, mgr_tokens, width, color="tab:blue", edgecolor="black",
           linewidth=0.5, label="Manager (cloud, measured)")
    ax.bar(x, agent_tokens, width, bottom=mgr_tokens,
           color="tab:red", edgecolor="black", linewidth=0.5, alpha=0.7,
           hatch="//", label="Agents (cloud, estimated)")

    # Total label above each bar
    for i, tot in enumerate(total_tokens):
        ax.text(i, tot + 60,
                f"{tot/1000:.2f}M" if tot >= 1000 else f"{tot}K",
                ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("Cloud tokens per 10-gen run")
    ax.set_ylim(0, 3500)
    ax.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000])
    ax.set_yticklabels(["0", "500K", "1M", "1.5M", "2M", "2.5M", "3M"])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", framealpha=0.95, frameon=True,
              fancybox=False, edgecolor="black", fontsize=7.5)

    # Bracket / annotation showing the hybrid-vs-fully-cloud ratio
    ax.annotate(
        "", xy=(3.0, 2900), xytext=(1.0, 2900),
        arrowprops=dict(arrowstyle="<->", color="black", lw=0.8),
    )
    ax.text(2.0, 3050, r"$\approx$6–10$\times$ fewer cloud tokens",
            ha="center", va="bottom", fontsize=8)

    fig.subplots_adjust(left=0.16, right=0.97, top=0.93, bottom=0.20)
    fig.savefig(FIG_DIR / "fig3-token-economy.pdf")
    fig.savefig(FIG_DIR / "fig3-token-economy.png")
    print(f"Wrote {FIG_DIR}/fig3-token-economy.{{pdf,png}}")


# ═══════════════════════════════════════════════════════════════════════
# Figure 1 — Single-LLM vs hybrid two-LLM deployment architecture
# ═══════════════════════════════════════════════════════════════════════

def _box(ax, x, y, w, h, text, *, fc="white", ec="black", lw=1.0,
         fontsize=8, fontweight="normal", style="round,pad=0.04", zorder=2):
    from matplotlib.patches import FancyBboxPatch
    p = FancyBboxPatch(
        (x, y), w, h, boxstyle=style,
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=zorder,
    )
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=fontsize, fontweight=fontweight,
            zorder=zorder + 1)


def _arrow(ax, x0, y0, x1, y1, *, color="black", lw=1.2, style="->",
           connectionstyle="arc3,rad=0.0", zorder=3):
    from matplotlib.patches import FancyArrowPatch
    p = FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle=style, color=color, lw=lw,
        connectionstyle=connectionstyle, mutation_scale=10, zorder=zorder,
    )
    ax.add_patch(p)


def _panel_axes(ax, title):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=9, fontweight="bold", loc="left", pad=4)


def make_fig1():
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.6))

    # ── Panel (a): Single-LLM (prior work) ──────────────────────────────
    _panel_axes(axa, "(a) Single-LLM deployment")

    # Single LLM endpoint (cloud or cluster) — top, wide
    _box(axa, 1.5, 7.3, 7.0, 1.7,
         "Single LLM endpoint\n(cloud API or multi-GPU cluster)",
         fc="#dde7f5", lw=1.1, fontweight="bold")
    axa.text(8.5, 8.15, "manager\n+ agent\ncalls",
             ha="left", va="center", fontsize=6.5, color="0.35", style="italic")

    # Framework controller
    _box(axa, 3.3, 4.8, 3.4, 1.1, "Framework\ncontroller",
         fc="white", lw=1.0)

    # Arrow: LLM <-> controller
    _arrow(axa, 5.0, 7.3, 5.0, 5.95, style="<->")

    # Agent workspaces (5 small boxes)
    for i, x in enumerate([0.6, 2.4, 4.2, 6.0, 7.8]):
        _box(axa, x, 1.5, 1.6, 1.4, f"agent\nworkspace {i+1}",
             fc="#f6f0e0", fontsize=6.5, lw=0.8)
        # arrow controller -> workspace
        _arrow(axa, 5.0, 4.8, x + 0.8, 2.9, style="->", lw=0.7,
               color="0.35", connectionstyle="arc3,rad=-0.1")
        # arrow workspace -> LLM endpoint (long upward) — implicit per-turn LLM call
        _arrow(axa, x + 0.8, 2.9, x + 0.8, 7.3, style="->",
               lw=0.7, color="#c0392b", connectionstyle="arc3,rad=0.0")

    axa.text(0.6, 0.6,
             "Every agent turn (multi-turn, dense traffic) hits the same\n"
             "endpoint as the manager's sparse strategic calls.",
             ha="left", va="center", fontsize=6.5, style="italic", color="0.3")

    # ── Panel (b): Hybrid two-LLM (this work) ───────────────────────────
    _panel_axes(axb, "(b) Hybrid two-LLM deployment (this work)")

    # Cloud manager (top-left)
    _box(axb, 0.4, 7.3, 4.5, 1.7,
         "Cloud LLM\n(frontier, e.g.\\ Opus 4.7)\n— manager role",
         fc="#dde7f5", lw=1.1, fontweight="bold")
    axb.text(2.65, 6.95, "$\\sim$11 sparse calls/gen",
             ha="center", va="top", fontsize=6.5, color="0.35", style="italic")

    # Local vLLM endpoint (top-right)
    _box(axb, 5.1, 7.3, 4.5, 1.7,
         "Local vLLM (compact MoE,\ne.g.\\ Gemma4-26B)\n— agent role",
         fc="#e6f1de", lw=1.1, fontweight="bold")
    axb.text(7.35, 6.95, "$\\sim$100s dense calls/gen,\ncontinuous batching",
             ha="center", va="top", fontsize=6.5, color="0.35", style="italic")

    # Framework controller in the middle, bridging both endpoints
    _box(axb, 3.3, 4.7, 3.4, 1.1, "Framework\ncontroller",
         fc="white", lw=1.0)

    # Arrows controller <-> manager (sparse) and controller <-> vLLM (dense)
    _arrow(axb, 4.0, 5.8, 2.6, 7.3, style="<->", lw=1.0)
    _arrow(axb, 6.0, 5.8, 7.4, 7.3, style="<->", lw=1.4, color="#27632a")

    # Agent workspaces below
    for i, x in enumerate([0.6, 2.4, 4.2, 6.0, 7.8]):
        _box(axb, x, 1.5, 1.6, 1.4, f"agent\nworkspace {i+1}",
             fc="#f6f0e0", fontsize=6.5, lw=0.8)
        # controller -> workspace
        _arrow(axb, 5.0, 4.7, x + 0.8, 2.9, style="->", lw=0.7,
               color="0.35", connectionstyle="arc3,rad=-0.1")
        # workspace -> local vLLM (green, all stay local)
        _arrow(axb, x + 0.8, 2.9, 7.35, 7.3, style="->",
               lw=0.7, color="#27632a", connectionstyle="arc3,rad=0.15")

    axb.text(0.4, 0.6,
             "Agent traffic stays local; only the manager's distilled\n"
             "outputs cross the cloud boundary.",
             ha="left", va="center", fontsize=6.5, style="italic", color="0.3")

    fig.subplots_adjust(left=0.02, right=0.99, top=0.93, bottom=0.02, wspace=0.05)
    fig.savefig(FIG_DIR / "fig1-architecture.pdf")
    fig.savefig(FIG_DIR / "fig1-architecture.png")
    print(f"Wrote {FIG_DIR}/fig1-architecture.{{pdf,png}}")


# ═══════════════════════════════════════════════════════════════════════
# Figure 4 — Manager x Agent grid as 4-line running-max trajectory
# Replaces the earlier Table III. Visualises the cliff-edge of LA-B0
# (fully-local Qwen3-only) and the near-equivalence of F1 and G0 (Opus
# manager with either agent model) in one image.
# ═══════════════════════════════════════════════════════════════════════

def make_fig4():
    # Configurations matching the four-cell manager x agent grid in Table I.
    # Names match Table I's Manager-Agent short labels.
    configs = [
        # (label,    task_dir,                color,        marker, linestyle)
        ("G4-G4",    "link_adaptation_a1",    "tab:gray",   "o",    "-"),
        ("Q3-Q3",    "link_adaptation_b0",    "tab:red",    "x",    "-"),
        ("Op-G4",    "link_adaptation_f1",    "tab:blue",   "^",    "-"),
        ("Op-Q3",    "link_adaptation_g0",    "tab:cyan",   "v",    "-"),
    ]

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    for label, task_dir, color, marker, ls in configs:
        gens, best, _ = load_per_generation(task_dir)
        ax.plot(gens, best, marker=marker, color=color, linestyle=ls, label=label, alpha=0.95)
        if len(best) > 0:
            final = np.nanmax(best)
            idx = next(i for i, v in enumerate(best) if np.isclose(v, final))
            ax.plot(gens[idx], best[idx], marker="*", markersize=11,
                    markerfacecolor=color, markeredgecolor="black",
                    markeredgewidth=0.6, linestyle="None", zorder=5)

    # Reference lines — labels in the right-hand margin to avoid stacking
    for y, lbl, lstyle in [(OLLA, "OLLA", "--"),
                           (GPT_OSS_120B, "GPT-OSS 120B", ":"),
                           (GPT_5_4, "GPT-5.4", "-.")]:
        ax.axhline(y, color="black", linewidth=0.6, linestyle=lstyle, alpha=0.55)
        ax.annotate(lbl, xy=(1.0, y), xycoords=("axes fraction", "data"),
                    xytext=(3, 0), textcoords="offset points",
                    fontsize=6.5, color="black", alpha=0.8, va="center", ha="left")

    ax.set_xlabel("Generation")
    ax.set_ylabel("Eval-set SE (bps/Hz)")
    ax.set_xlim(-0.5, 20.5)
    ax.set_xticks(range(0, 21, 4))
    ax.set_ylim(0.4, 3.65)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="center right", framealpha=0.95, frameon=True,
              fancybox=False, edgecolor="black", fontsize=8, title="Mgr-Agt", title_fontsize=8)

    fig.subplots_adjust(left=0.14, right=0.78, top=0.97, bottom=0.13)
    fig.savefig(FIG_DIR / "fig4-grid.pdf")
    fig.savefig(FIG_DIR / "fig4-grid.png")
    print(f"Wrote {FIG_DIR}/fig4-grid.{{pdf,png}}")


# ═══════════════════════════════════════════════════════════════════════
# Figure 5 — Consolidation ablation: context growth (top) +
#             running-best eval SE (bottom), Op-G4 vs Op-G4*
# ═══════════════════════════════════════════════════════════════════════

def make_fig5():
    data = json.load(open(FIG_DIR / "context_growth.json"))
    f1_ctx = data["F1_with_cons"]   # [(gen, chars), ...] gens 0..9
    f2_ctx = data["F2_no_cons"]     # [(gen, chars), ...] gens 0..9

    ref_data = json.load(open(FIG_DIR / "ref_oldest_gen.json"))
    # rel_gen 0 has no refs; use gens 1-9
    ref_gens_with_data = [d for d in ref_data if d["oldest_ref"] is not None]
    rx = [d["rel_gen"] for d in ref_gens_with_data]
    ry = [d["oldest_ref"] - 4 for d in ref_gens_with_data]  # normalise: gen04 -> 0

    x_max = 9  # run 2 has 10 gens (0-9)

    fig, (ax_ctx, ax_ref) = plt.subplots(
        2, 1, figsize=(3.6, 4.8), sharex=True,
        gridspec_kw={"hspace": 0.35},
    )

    # ── top: context growth ──────────────────────────────────────────────
    g1c = [p[0] for p in f1_ctx]; t1 = [p[1] / 1000 for p in f1_ctx]
    g2c = [p[0] for p in f2_ctx]; t2 = [p[1] / 1000 for p in f2_ctx]

    ax_ctx.plot(g2c, t2, marker="s", color="tab:red",  linewidth=1.2, markersize=5, label="Op-G4*")
    ax_ctx.plot(g1c, t1, marker="o", color="tab:blue", linewidth=1.2, markersize=5, label="Op-G4")
    ax_ctx.axhline(32, color="black", linestyle="--", linewidth=0.6, alpha=0.55)
    ax_ctx.annotate("32K limit", xy=(9.2, 32), xycoords="data",
                    xytext=(0, 3), textcoords="offset points",
                    fontsize=7, ha="right", va="bottom", alpha=0.8)
    ax_ctx.set_ylabel("Manager context (K tokens)")
    ax_ctx.set_ylim(0, 36)
    ax_ctx.grid(True, alpha=0.25)
    ax_ctx.legend(loc="upper left", framealpha=0.95, frameon=True,
                  fancybox=False, edgecolor="black", fontsize=8, handletextpad=0.4)
    ax_ctx.text(0.98, 0.04, "(a)", transform=ax_ctx.transAxes,
                fontsize=9, fontweight="bold", va="bottom", ha="right")

    # ── bottom: oldest referenced workspace generation (Op-G4* only) ────
    ax_ref.step(rx, ry, where="post", color="tab:red", linewidth=1.5)
    ax_ref.scatter(rx, ry, color="tab:red", s=30, zorder=4)

    # Shade the "forgotten" region: everything older than oldest_ref
    ax_ref.axvspan(7.5, x_max + 0.5, color="tab:red", alpha=0.08,
                   label="context truncated")

    # Mark the truncation boundary
    ax_ref.axvline(7.5, color="black", linestyle="--", linewidth=0.6, alpha=0.55)
    ax_ref.annotate("truncation\nbegins", xy=(7.5, 4.2), xycoords="data",
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=6.5, ha="left", va="center", alpha=0.8)

    # Label what gen04 represents
    ax_ref.axhline(0, color="gray", linestyle=":", linewidth=0.6, alpha=0.5)
    ax_ref.annotate("gen04\n(best early soln.)", xy=(0.02, 0.12),
                    xycoords="axes fraction", fontsize=6.5, color="gray",
                    va="bottom", ha="left", alpha=0.9)

    ax_ref.set_xlabel("Generation (Op-G4*)")
    ax_ref.set_ylabel("Oldest cited workspace\n(gens before run start)")
    ax_ref.set_ylim(-0.5, x_max + 0.5)
    ax_ref.set_yticks(range(0, x_max + 1, 2))
    ax_ref.grid(True, alpha=0.25)
    ax_ref.text(0.02, 0.97, "(b)", transform=ax_ref.transAxes,
                fontsize=9, fontweight="bold", va="top")

    fig.subplots_adjust(left=0.17, right=0.97, top=0.97, bottom=0.10)
    fig.savefig(FIG_DIR / "fig5-consolidation-ablation.pdf")
    fig.savefig(FIG_DIR / "fig5-consolidation-ablation.png")
    print(f"Wrote {FIG_DIR}/fig5-consolidation-ablation.{{pdf,png}}")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    make_fig1()
    make_fig2()
    make_fig3()
    make_fig4()
    make_fig5()
