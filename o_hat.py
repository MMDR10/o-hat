#!/usr/bin/env python3
"""
O-Hat: Cross-Domain Structural Measurement Operator

Measures three substrate-independent structural properties of any time series:
  curl     — directional rate of change (signed gradient sum)
  helicity — total variation / structural complexity (absolute gradient sum)
  balance  — distance from equilibrium (skewness ratio: outbreak / baseline)

Usage:
  python o_hat.py data.csv                    # auto-detect outbreak window
  python o_hat.py data.csv --window 24        # specify window size
  python o_hat.py data.csv --baseline 240     # specify baseline length
  python o_hat.py data.csv --quiet            # numerical output only
  python o_hat.py data.csv --plot             # generate classification chart

Input CSV: one numeric column (header optional). Time-ordered rows.
"""

import argparse
import sys
import numpy as np
from scipy import stats


def load_csv(path):
    """Load a single-column CSV, skipping header if non-numeric."""
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]
    values = []
    for line in lines:
        try:
            values.append(float(line.split(",")[0]))
        except ValueError:
            continue  # skip header
    return np.array(values)


def classify(balance_ratio):
    """Classify system type from balance ratio."""
    if balance_ratio > 20:
        return "SUPER-PULSE"
    elif balance_ratio > 5:
        return "PULSE"
    elif balance_ratio > 1.5:
        return "CONTINUOUS FLOW"
    else:
        return "REGIME SATURATION / NOISE"


def measure(series, window=None, baseline_len=None):
    """
    Apply O-hat operator to a time series.

    Returns dict with:
      curl, helicity, balance_ratio, baseline_skew, outbreak_skew,
      system_type, window_used, baseline_len_used
    """
    n = len(series)
    if n < 10:
        return {"error": "Need at least 10 data points."}

    # Auto-parameters
    if baseline_len is None:
        baseline_len = max(10, n // 5)
    if window is None:
        window = max(4, n // 20)

    baseline_len = min(baseline_len, n // 2)
    window = min(window, n // 2)

    # Baseline: first portion
    baseline = series[:baseline_len]
    bs = stats.skew(baseline)

    # Outbreak: window around global extremum
    extreme_idx = np.argmax(np.abs(series - np.mean(series)))
    half = window // 2
    ss = max(0, extreme_idx - half)
    se = min(n, extreme_idx + half)
    outbreak = series[ss:se]

    os_ = stats.skew(outbreak)

    # Curl & Helicity
    grads = np.diff(outbreak)
    curl = float(np.sum(grads))
    helicity = float(np.sum(np.abs(grads)))

    # Balance ratio
    bs_abs = abs(bs)
    if bs_abs < 1e-10:
        balance = float("inf") if abs(os_) > 1e-10 else 1.0
    else:
        balance = abs(os_) / bs_abs

    return {
        "curl": curl,
        "helicity": helicity,
        "balance_ratio": round(balance, 2),
        "baseline_skew": round(bs, 4),
        "outbreak_skew": round(os_, 4),
        "system_type": classify(balance),
        "window_used": window,
        "baseline_len_used": baseline_len,
        "data_points": n,
        "extreme_index": int(extreme_idx),
        "outbreak_start": ss,
        "outbreak_end": se,
    }


def plot_result(series, result, output_path=None):
    """Generate a classification chart. Requires matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠ matplotlib not installed. Install with: pip install matplotlib", file=sys.stderr)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                    gridspec_kw={"width_ratios": [1.5, 1]})

    # ── Left: Time series with baseline + outbreak windows ──
    n = len(series)
    bl = result["baseline_len_used"]
    ss, se_ = result["outbreak_start"], result["outbreak_end"]

    ax1.plot(range(n), series, color="#374151", linewidth=0.7, alpha=0.8, label="Data")
    ax1.axvspan(0, bl, alpha=0.12, color="#3b82f6", label="Baseline")
    ax1.axvspan(ss, se_, alpha=0.18, color="#ef4444", label="Outbreak window")
    ax1.axvline(x=result["extreme_index"], color="#dc2626", linewidth=1.5,
                linestyle="--", label="Extreme point")

    ax1.set_xlabel("Time index")
    ax1.set_ylabel("Value")
    ax1.set_title(f"Time Series Structure\ncurl={result['curl']:.2f}  "
                  f"helicity={result['helicity']:.2f}  balance={result['balance_ratio']:.2f}×",
                  fontsize=10)
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(True, alpha=0.2)

    # ── Right: Balance ratio classification spectrum ──
    categories = [
        ("REGIME\nSATURATION", 0, 1.5, "#22c55e"),
        ("CONTINUOUS\nFLOW", 1.5, 5, "#3b82f6"),
        ("PULSE", 5, 20, "#f59e0b"),
        ("SUPER-PULSE", 20, 45, "#ef4444"),
    ]

    y_positions = [3, 2, 1, 0]
    for y, (label, lo, hi, color) in zip(y_positions, categories):
        ax2.barh(y, hi - lo, left=lo, height=0.6, color=color, alpha=0.3, edgecolor=color, linewidth=1)
        ax2.text((lo + hi) / 2, y, label, ha="center", va="center", fontsize=8, fontweight="bold", color=color)

    # Plot the measured balance ratio as a vertical line
    br = result["balance_ratio"]
    ax2.axvline(x=br, color="#000000", linewidth=2.5, linestyle="-")
    ax2.plot(br, -0.8, marker="v", markersize=14, color="#000000", clip_on=False)
    ax2.text(br, -1.3, f"{br:.1f}×\n{result['system_type']}", ha="center", fontsize=10,
             fontweight="bold", color="#000000")

    ax2.set_xlim(0, 45)
    ax2.set_ylim(-2, 4)
    ax2.set_yticks([])
    ax2.set_xlabel("Balance Ratio")
    ax2.set_title("Classification Spectrum", fontsize=10)
    ax2.grid(True, axis="x", alpha=0.2)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"\n  📊 Chart saved: {output_path}")
    else:
        path = "o_hat_chart.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        print(f"\n  📊 Chart saved: {path}")
    plt.close()


def main():
    p = argparse.ArgumentParser(description="O-Hat Structural Measurement Operator")
    p.add_argument("csv", help="Path to single-column CSV file")
    p.add_argument("--window", type=int, default=None, help="Outbreak window size")
    p.add_argument("--baseline", type=int, default=None, help="Baseline length")
    p.add_argument("--quiet", action="store_true", help="Numerical output only")
    p.add_argument("--plot", action="store_true", help="Generate classification chart")
    p.add_argument("--plot-output", type=str, default=None, help="Chart output path")
    args = p.parse_args()

    series = load_csv(args.csv)
    result = measure(series, args.window, args.baseline)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.quiet:
        print(f"{result['balance_ratio']} {result['system_type']} "
              f"curl={result['curl']:.1f} helicity={result['helicity']:.1f}")
    else:
        print("=" * 54)
        print("  O-HAT  STRUCTURAL  MEASUREMENT")
        print("=" * 54)
        print(f"  Data points  : {result['data_points']}")
        print(f"  Baseline     : {result['baseline_len_used']} points")
        print(f"  Window       : {result['window_used']} points")
        print(f"  Extreme at   : index {result['extreme_index']}")
        print(f"  ---")
        print(f"  Curl         : {result['curl']:>12.2f}")
        print(f"  Helicity     : {result['helicity']:>12.2f}")
        print(f"  Baseline skew: {result['baseline_skew']:>12.4f}")
        print(f"  Outbreak skew: {result['outbreak_skew']:>12.4f}")
        print(f"  ---")
        print(f"  BALANCE RATIO: {result['balance_ratio']:>10.2f}x")
        print(f"  SYSTEM TYPE  : {result['system_type']:>14}")
        print("=" * 54)

        print("\n  Reference spectrum:")
        print("    SUPER-PULSE        > 20x   (e.g. 1989 Quebec Storm)")
        print("    PULSE             5-15x   (e.g. Earthquakes)")
        print("    CONTINUOUS FLOW   1.5-4x  (e.g. ENSO, COVID)")
        print("    REGIME SATURATION  < 1.5x  (e.g. Seasonal forcing)")

    if args.plot:
        plot_result(series, result, args.plot_output)


if __name__ == "__main__":
    main()
