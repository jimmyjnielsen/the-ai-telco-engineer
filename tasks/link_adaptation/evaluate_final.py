#!/usr/bin/env python3
"""Standalone evaluation script for link adaptation solutions.

Evaluates solution.py against held-out evaluation trajectories and produces
per-trajectory metrics (SNR, SE, BLER) for publication-quality plots.

Usage:
    python evaluate_final.py <path/to/solution.py> [options]

Options:
    --split {training,evaluation}   Which trajectory set to use (default: evaluation)
    --output-dir DIR                Output directory for CSV and plots (default: eval_results)
    --seed INT                      Random seed (default: 42)
    --workers INT                   Parallel workers (default: 10)
    --no-olla                       Skip OLLA baseline

Paper baselines (bps/Hz):
    OLLA:        3.4196
    GPT-5.4:     3.5370
    GPT-OSS 120B: 3.3976
"""

import argparse
import csv
import importlib.util
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

# ── locate and enter eval directory (utils.py uses relative data/ paths) ────
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR / "eval"
_ORIG_CWD = Path.cwd()  # capture before chdir so we can resolve relative solution paths
os.chdir(EVAL_DIR)
sys.path.insert(0, str(EVAL_DIR))

# ── imports from eval infrastructure ────────────────────────────────────────
from utils import BLER_SIGMOID_PARAMS, MCS_TO_SE, get_bler, bler_2_mcs  # noqa: E402
from eval import (  # noqa: E402  (triggers training pkl load as side effect — acceptable)
    run_la,
    LinkAdaptation,
    BLER_TARGET,
    NACK_REPORT_BATCH_SIZE,
    SINR_BOUNDS_LIN,
)

BLER_TARGET_TOLERANCE = 0.1
N_MCS = len(MCS_TO_SE)


# ── trajectory loading ───────────────────────────────────────────────────────

def load_trajectories(split: str) -> np.ndarray:
    """Load and normalise SINR gain trajectories (same normalisation as eval.py)."""
    fname = f"data/trajectories_{split}.pkl"
    with open(fname, "rb") as f:
        _traj, gains = pickle.load(f)
    gains = np.array(gains, dtype=float)
    # Normalise to [0,1] then scale to SINR bounds (linear)
    gains = gains / np.max(gains, axis=-1, keepdims=True)
    gains = gains * (SINR_BOUNDS_LIN[1] - SINR_BOUNDS_LIN[0]) + SINR_BOUNDS_LIN[0]
    return gains


# ── module loading ───────────────────────────────────────────────────────────

def load_mcs_selection(source_file: str):
    """Return the mcs_selection callable from a Python source file."""
    module_name = Path(source_file).stem
    spec = importlib.util.spec_from_file_location(module_name, source_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {source_file}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod, "mcs_selection", None)):
        raise AttributeError(f"{source_file} must define a callable 'mcs_selection'")
    return mod.mcs_selection


# ── OLLA baseline ────────────────────────────────────────────────────────────

def make_olla_mcs_selection(step_down: float = 1.0) -> callable:
    """Step-based OLLA: adjust MCS by step_down on NACK, step_up on ACK.

    step_up / step_down == bler_target / (1 - bler_target) maintains the
    target BLER in steady state.
    """
    step_up = step_down * BLER_TARGET / (1.0 - BLER_TARGET)
    n_max = float(N_MCS - 1)
    state = {"mcs_float": n_max / 2.0, "prev_len": 0}

    def mcs_selection(is_nack_hist, mcs_ackned_hist, bler_target_arg):
        new = is_nack_hist[state["prev_len"]:]
        for nack in new:
            if nack == 1:
                state["mcs_float"] -= step_down
            else:
                state["mcs_float"] += step_up
            state["mcs_float"] = np.clip(state["mcs_float"], 0.0, n_max)
        state["prev_len"] = len(is_nack_hist)
        return int(round(state["mcs_float"]))

    return mcs_selection


# ── per-trajectory simulation ────────────────────────────────────────────────

def _simulate(scenario_idx: int, sinr_hist: np.ndarray,
              mcs_selection_func, seed: int, algorithm: str) -> dict:
    """Run one trajectory simulation and return per-trajectory metrics."""
    try:
        la = LinkAdaptation(BLER_TARGET, mcs_selection_func=mcs_selection_func)
        is_nack_hist, rate_hist, _, _, _ = run_la(
            la, sinr_hist, BLER_SIGMOID_PARAMS,
            nack_report_batch_size=NACK_REPORT_BATCH_SIZE,
            mcs_to_se=MCS_TO_SE, seed=seed,
        )
        bler = float(np.mean(is_nack_hist))
        se = float(np.mean(rate_hist))
        success = bler < BLER_TARGET * (1.0 + BLER_TARGET_TOLERANCE)
        snr_db = float(10.0 * np.log10(np.mean(sinr_hist)))
        return {
            "trajectory_idx": scenario_idx,
            "mean_snr_db": snr_db,
            "se": se,
            "bler": bler,
            "success": success,
            "algorithm": algorithm,
            "error": None,
        }
    except Exception as exc:
        import traceback
        return {
            "trajectory_idx": scenario_idx,
            "mean_snr_db": float("nan"),
            "se": float("nan"),
            "bler": float("nan"),
            "success": False,
            "algorithm": algorithm,
            "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        }


def _simulate_worker(args):
    scenario_idx, sinr_hist, source_file, seed, algorithm = args
    mcs_fn = load_mcs_selection(source_file)
    return _simulate(scenario_idx, sinr_hist, mcs_fn, seed, algorithm)


def _simulate_olla_worker(args):
    scenario_idx, sinr_hist, seed = args
    mcs_fn = make_olla_mcs_selection()
    return _simulate(scenario_idx, sinr_hist, mcs_fn, seed, "OLLA")


# ── parallel evaluation ──────────────────────────────────────────────────────

def evaluate_all(gains: np.ndarray, source_file: str,
                 seed: int, workers: int, label: str) -> list[dict]:
    tasks = [(i, gains[i], source_file, seed + i, label) for i in range(len(gains))]
    results = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_simulate_worker, t): t[0] for t in tasks}
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: r["trajectory_idx"])
    return results


def evaluate_olla(gains: np.ndarray, seed: int, workers: int) -> list[dict]:
    tasks = [(i, gains[i], seed + i) for i in range(len(gains))]
    results = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_simulate_olla_worker, t): t[0] for t in tasks}
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: r["trajectory_idx"])
    return results


# ── CSV output ───────────────────────────────────────────────────────────────

def save_csv(records: list[dict], path: Path):
    fields = ["trajectory_idx", "mean_snr_db", "se", "bler", "success", "algorithm"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"Saved CSV: {path}")


# ── printing summary ─────────────────────────────────────────────────────────

def print_summary(records: list[dict], label: str):
    good = [r for r in records if r["error"] is None]
    errors = [r for r in records if r["error"] is not None]
    if errors:
        print(f"\n  {len(errors)} simulation error(s) — check CSV for details")
    if not good:
        print(f"\n[{label}] All simulations failed.")
        return
    se_vals = np.array([r["se"] for r in good])
    bler_vals = np.array([r["bler"] for r in good])
    success_vals = np.array([r["success"] for r in good])
    print(f"\n[{label}]")
    print(f"  Trajectories:  {len(good)}/{len(records)}")
    print(f"  Mean SE:       {np.mean(se_vals):.4f} bps/Hz")
    print(f"  Success rate:  {np.mean(success_vals)*100:.1f}%  (BLER < {BLER_TARGET*(1+BLER_TARGET_TOLERANCE):.2f})")
    print(f"  BLER  min/med/max: {np.min(bler_vals):.3f} / {np.median(bler_vals):.3f} / {np.max(bler_vals):.3f}")

    # Paper reference baselines
    if label not in ("OLLA",):
        print("\n  Paper baselines (bps/Hz):")
        print(f"    OLLA:         3.4196")
        print(f"    GPT-OSS 120B: 3.3976")
        print(f"    GPT-5.4:      3.5370")


# ── plotting ─────────────────────────────────────────────────────────────────

def make_plots(all_records: list[dict], output_dir: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — skipping plots")
        return

    # Group by algorithm
    algos = sorted(set(r["algorithm"] for r in all_records))
    palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color = {a: palette[i % len(palette)] for i, a in enumerate(algos)}

    snr_bins = np.linspace(0, 20, 11)  # 2 dB bins
    bin_centers = 0.5 * (snr_bins[:-1] + snr_bins[1:])

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for algo in algos:
        recs = [r for r in all_records if r["algorithm"] == algo
                and r["error"] is None]
        if not recs:
            continue
        snr = np.array([r["mean_snr_db"] for r in recs])
        se = np.array([r["se"] for r in recs])
        bler = np.array([r["bler"] for r in recs])
        c = color[algo]

        # SNR vs SE scatter + binned mean
        ax = axes[0]
        ax.scatter(snr, se, alpha=0.35, s=20, color=c)
        bin_se = [se[(snr >= snr_bins[i]) & (snr < snr_bins[i+1])]
                  for i in range(len(snr_bins)-1)]
        bin_means = [np.mean(b) if len(b) else np.nan for b in bin_se]
        ax.plot(bin_centers, bin_means, "o-", color=c, linewidth=2, label=algo)

        # SNR vs BLER scatter + binned mean
        ax = axes[1]
        ax.scatter(snr, bler, alpha=0.35, s=20, color=c)
        bin_bler = [bler[(snr >= snr_bins[i]) & (snr < snr_bins[i+1])]
                    for i in range(len(snr_bins)-1)]
        bin_means_b = [np.mean(b) if len(b) else np.nan for b in bin_bler]
        ax.plot(bin_centers, bin_means_b, "o-", color=c, linewidth=2, label=algo)

        # SE CDF
        ax = axes[2]
        se_sorted = np.sort(se)
        cdf = np.arange(1, len(se_sorted)+1) / len(se_sorted)
        ax.step(se_sorted, cdf, where="post", color=c, linewidth=2, label=algo)

    # BLER target line
    axes[1].axhline(BLER_TARGET * (1 + BLER_TARGET_TOLERANCE),
                    color="red", linestyle="--", linewidth=1, label="BLER limit")

    axes[0].set_xlabel("Mean SNR (dB)")
    axes[0].set_ylabel("Spectral Efficiency (bps/Hz)")
    axes[0].set_title("SNR vs Spectral Efficiency")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    axes[1].set_xlabel("Mean SNR (dB)")
    axes[1].set_ylabel("Long-term BLER")
    axes[1].set_title("SNR vs BLER")
    axes[1].set_yscale("log")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3, which="both")

    axes[2].set_xlabel("Spectral Efficiency (bps/Hz)")
    axes[2].set_ylabel("CDF")
    axes[2].set_title("SE CDF")
    axes[2].legend(fontsize=8)
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    plot_path = output_dir / "evaluation_plots.pdf"
    fig.savefig(plot_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved plot: {plot_path}")

    # Also save PNG for quick viewing
    fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
    # Re-draw (reuse the same logic above via the saved PDF)
    # Instead, reload the PDF approach is complex; just save both formats in one go
    # Re-draw:
    for algo in algos:
        recs = [r for r in all_records if r["algorithm"] == algo
                and r["error"] is None]
        if not recs:
            continue
        snr = np.array([r["mean_snr_db"] for r in recs])
        se = np.array([r["se"] for r in recs])
        bler = np.array([r["bler"] for r in recs])
        c = color[algo]
        axes2[0].scatter(snr, se, alpha=0.35, s=20, color=c)
        bin_se = [se[(snr >= snr_bins[i]) & (snr < snr_bins[i+1])]
                  for i in range(len(snr_bins)-1)]
        bin_means = [np.mean(b) if len(b) else np.nan for b in bin_se]
        axes2[0].plot(bin_centers, bin_means, "o-", color=c, linewidth=2, label=algo)
        axes2[1].scatter(snr, bler, alpha=0.35, s=20, color=c)
        bin_bler = [bler[(snr >= snr_bins[i]) & (snr < snr_bins[i+1])]
                    for i in range(len(snr_bins)-1)]
        bin_means_b = [np.mean(b) if len(b) else np.nan for b in bin_bler]
        axes2[1].plot(bin_centers, bin_means_b, "o-", color=c, linewidth=2, label=algo)
        se_sorted = np.sort(se)
        cdf = np.arange(1, len(se_sorted)+1) / len(se_sorted)
        axes2[2].step(se_sorted, cdf, where="post", color=c, linewidth=2, label=algo)

    axes2[1].axhline(BLER_TARGET * (1 + BLER_TARGET_TOLERANCE),
                     color="red", linestyle="--", linewidth=1, label="BLER limit")
    for ax, xlabel, ylabel, title in zip(
        axes2,
        ["Mean SNR (dB)", "Mean SNR (dB)", "Spectral Efficiency (bps/Hz)"],
        ["Spectral Efficiency (bps/Hz)", "Long-term BLER", "CDF"],
        ["SNR vs Spectral Efficiency", "SNR vs BLER", "SE CDF"],
    ):
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    axes2[1].set_yscale("log")
    axes2[1].grid(True, alpha=0.3, which="both")
    fig2.tight_layout()
    png_path = output_dir / "evaluation_plots.png"
    fig2.savefig(png_path, bbox_inches="tight", dpi=150)
    plt.close(fig2)
    print(f"Saved plot: {png_path}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("solution", help="Path to solution.py (must define mcs_selection)")
    parser.add_argument("--split", choices=["training", "evaluation"],
                        default="evaluation",
                        help="Trajectory set to evaluate against (default: evaluation)")
    parser.add_argument("--output-dir", default="eval_results",
                        help="Output directory for CSV and plots (default: eval_results)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--no-olla", action="store_true",
                        help="Skip OLLA baseline computation")
    parser.add_argument("--label", default=None,
                        help="Algorithm label for plots/CSV (default: solution filename stem)")
    args = parser.parse_args()

    solution_path = (_ORIG_CWD / args.solution).resolve()
    if not solution_path.exists():
        print(f"Error: {solution_path} does not exist", file=sys.stderr)
        sys.exit(1)

    label = args.label or solution_path.stem
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.split} trajectories...")
    gains = load_trajectories(args.split)
    print(f"  {len(gains)} trajectories x {gains.shape[1]} slots")

    print(f"\nEvaluating {label} ({solution_path.name}) ...")
    agent_records = evaluate_all(gains, str(solution_path),
                                 args.seed, args.workers, label)
    print_summary(agent_records, label)

    all_records = agent_records[:]

    if not args.no_olla:
        print(f"\nEvaluating OLLA baseline ...")
        olla_records = evaluate_olla(gains, args.seed, args.workers)
        print_summary(olla_records, "OLLA")
        all_records += olla_records

    csv_path = output_dir / f"results_{args.split}.csv"
    save_csv(all_records, csv_path)

    make_plots(all_records, output_dir)

    # Print errors if any
    errors = [r for r in all_records if r.get("error")]
    if errors:
        print(f"\n{len(errors)} error(s) encountered:")
        for r in errors[:5]:
            print(f"  traj {r['trajectory_idx']} ({r['algorithm']}): "
                  f"{r['error'].splitlines()[0]}")


if __name__ == "__main__":
    main()
