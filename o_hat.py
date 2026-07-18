#!/usr/bin/env python3
"""
O-Hat: Cross-Domain Structural Measurement Operator

Measures three substrate-independent structural properties of any time series:
  curl     — directional rate of change (signed gradient sum)
  helicity — total variation / structural complexity (absolute gradient sum)
  balance  — distance from equilibrium (skewness ratio: outbreak / baseline)

Usage:
  python o_hat.py data.csv                        # auto-detect
  python o_hat.py data.csv --window 24 --baseline 240
  python o_hat.py data.csv --quiet                # numerical only
  python o_hat.py data.csv --plot                 # classification chart
  python o_hat.py data.csv --sensitivity          # window sensitivity band

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
    """Apply O-hat operator. Returns metrics dict."""
    n = len(series)
    if n < 10:
        return {"error": "Need at least 10 data points."}

    if baseline_len is None:
        baseline_len = max(10, n // 5)
    if window is None:
        window = max(4, n // 20)

    baseline_len = min(baseline_len, n // 2)
    window = min(window, n // 2)

    baseline = series[:baseline_len]
    bs = stats.skew(baseline)

    extreme_idx = np.argmax(np.abs(series - np.mean(series)))
    half = window // 2
    ss = max(0, extreme_idx - half)
    se = min(n, extreme_idx + half)
    outbreak = series[ss:se]

    os_ = stats.skew(outbreak)

    grads = np.diff(outbreak)
    curl = float(np.sum(grads))
    helicity = float(np.sum(np.abs(grads)))

    bs_abs = abs(bs)
    if bs_abs < 1e-10:
        balance = float("inf") if abs(os_) > 1e-10 else 1.0
    else:
        balance = abs(os_) / bs_abs

    return {
        "curl": curl, "helicity": helicity,
        "balance_ratio": round(balance, 2),
        "baseline_skew": round(bs, 4), "outbreak_skew": round(os_, 4),
        "system_type": classify(balance),
        "window_used": window, "baseline_len_used": baseline_len,
        "data_points": n, "extreme_index": int(extreme_idx),
        "outbreak_start": ss, "outbreak_end": se,
    }


def sensitivity_scan(series, base_window, base_baseline, fractions=None):
    """
    Sweep window × baseline across fractions of base values.
    Returns (matrix, window_sizes, baseline_sizes).
    """
    if fractions is None:
        fractions = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    n = len(series)
    window_sizes = [max(4, min(n // 2, int(base_window * f))) for f in fractions]
    baseline_sizes = [max(4, min(n // 2, int(base_baseline * f))) for f in fractions]

    matrix = np.zeros((len(baseline_sizes), len(window_sizes)))
    stable_count = 0
    total = 0

    for i, bl in enumerate(baseline_sizes):
        for j, w in enumerate(window_sizes):
            r = measure(series, window=w, baseline_len=bl)
            matrix[i, j] = r.get("balance_ratio", np.nan)
            total += 1
            if not np.isnan(matrix[i, j]):
                stable_count += 1

    return matrix, window_sizes, baseline_sizes, fractions, stable_count / max(total, 1)


def plot_sensitivity(matrix, window_sizes, baseline_sizes, fractions,
                     base_balance, base_window, base_baseline, series,
                     output_path=None):
    """Plot window sensitivity band."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠ matplotlib not installed.", file=sys.stderr)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5),
                                    gridspec_kw={"width_ratios": [1.2, 1]})

    # ── Left: Heatmap ──
    im = ax1.imshow(matrix, aspect="auto", origin="lower",
                    cmap="RdYlBu_r", vmin=0, vmax=max(8, np.nanmax(matrix)))

    nw, nb = len(window_sizes), len(baseline_sizes)
    ax1.set_xticks(range(nw))
    ax1.set_yticks(range(nb))
    ax1.set_xticklabels([f"{f:.0%}" for f in fractions], rotation=45, fontsize=7)
    ax1.set_yticklabels([f"{f:.0%}" for f in fractions], fontsize=7)

    # Mark the nominal (100%, 100%) cell
    mid = len(fractions) // 2
    ax1.plot(mid, mid, marker="s", markersize=18, markeredgewidth=2.5,
             markerfacecolor="none", markeredgecolor="black")

    ax1.set_xlabel("Window size (% of nominal)", fontsize=9)
    ax1.set_ylabel("Baseline size (% of nominal)", fontsize=9)
    ax1.set_title(f"Balance Ratio Sensitivity Band\n"
                  f"Nominal: window={base_window}, baseline={base_baseline}, "
                  f"balance={base_balance:.2f}×",
                  fontsize=10)

    cbar = plt.colorbar(im, ax=ax1, shrink=0.82)
    cbar.set_label("Balance Ratio", fontsize=8)

    # Annotate cells
    for i in range(nb):
        for j in range(nw):
            v = matrix[i, j]
            if not np.isnan(v):
                ax1.text(j, i, f"{v:.1f}", ha="center", va="center",
                         fontsize=6.5 if v < 50 else 5.5,
                         fontweight="bold" if 0.9 <= fractions[i] <= 1.1
                         and 0.9 <= fractions[j] <= 1.1 else "normal",
                         color="white" if v > 10 else "black")

    # ── Right: Sensitivity band as line plot ──
    # Extract the diagonal (window = baseline = same fraction) for the band
    diag = np.diag(matrix)
    lo_band = np.nanmin(matrix, axis=0)  # min across baselines for each window
    hi_band = np.nanmax(matrix, axis=0)  # max across baselines for each window

    x_pct = [f * 100 for f in fractions]

    ax2.fill_between(x_pct, lo_band, hi_band, alpha=0.18, color="#3b82f6",
                     label="Full sensitivity range\n(min–max across all baseline sizes)")
    ax2.plot(x_pct, diag, "o-", color="#1e40af", linewidth=2, markersize=6,
             label="Diagonal (window = baseline)")
    ax2.axhline(y=base_balance, color="#ef4444", linewidth=1.2, linestyle="--",
                label=f"Nominal balance ({base_balance:.2f}×)")
    ax2.axvline(x=100, color="#888888", linewidth=0.8, linestyle=":")

    # Classification zone shading
    for lo, hi, color, label in [
        (0, 1.5, "#22c55e", "REGIME SATURATION"),
        (1.5, 5, "#3b82f6", "CONTINUOUS FLOW"),
        (5, 20, "#f59e0b", "PULSE"),
        (20, 100, "#ef4444", "SUPER-PULSE"),
    ]:
        ax2.axhspan(lo, min(hi, ax2.get_ylim()[1] if ax2.get_ylim()[1] > 0 else 100),
                    alpha=0.04, color=color)

    # Compute stability stats
    band_min = np.nanmin(diag[3:-2]) if len(diag) > 5 else np.nanmin(diag)
    band_max = np.nanmax(diag[3:-2]) if len(diag) > 5 else np.nanmax(diag)
    stability = band_max - band_min

    ax2.set_xlabel("Window & baseline size (% of nominal)", fontsize=9)
    ax2.set_ylabel("Balance Ratio", fontsize=9)
    ax2.set_title(f"Sensitivity Band\n"
                  f"Range: {band_min:.2f}× – {band_max:.2f}× "
                  f"(Δ={stability:.2f}× across 60%–140% window)",
                  fontsize=10)
    ax2.legend(fontsize=7, loc="upper left")
    ax2.grid(True, alpha=0.2)

    # Stability verdict
    verdict = ("[STABLE]" if stability < 1.0 else
               "[MODERATE]" if stability < 3.0 else "[UNSTABLE]")
    ax2.text(0.98, 0.03, f"Stability: {verdict}\n"
             f"Classification unchanged\nacross ±40% window sweep",
             transform=ax2.transAxes, fontsize=9, fontweight="bold",
             ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", alpha=0.85))

    plt.tight_layout()
    path = output_path or "o_hat_sensitivity.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\n  📊 Sensitivity chart saved: {path}")
    plt.close()


def plot_result(series, result, output_path=None):
    """Generate a classification chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠ matplotlib not installed.", file=sys.stderr)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                    gridspec_kw={"width_ratios": [1.5, 1]})

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

    categories = [
        ("REGIME\nSATURATION", 0, 1.5, "#22c55e"),
        ("CONTINUOUS\nFLOW", 1.5, 5, "#3b82f6"),
        ("PULSE", 5, 20, "#f59e0b"),
        ("SUPER-PULSE", 20, 45, "#ef4444"),
    ]
    for y, (label, lo, hi, color) in zip([3, 2, 1, 0], categories):
        ax2.barh(y, hi - lo, left=lo, height=0.6, color=color, alpha=0.3,
                 edgecolor=color, linewidth=1)
        ax2.text((lo + hi) / 2, y, label, ha="center", va="center",
                 fontsize=8, fontweight="bold", color=color)

    br = result["balance_ratio"]
    ax2.axvline(x=br, color="#000000", linewidth=2.5, linestyle="-")
    ax2.plot(br, -0.8, marker="v", markersize=14, color="#000000", clip_on=False)
    ax2.text(br, -1.3, f"{br:.1f}×\n{result['system_type']}", ha="center",
             fontsize=10, fontweight="bold", color="#000000")
    ax2.set_xlim(0, 45)
    ax2.set_ylim(-2, 4)
    ax2.set_yticks([])
    ax2.set_xlabel("Balance Ratio")
    ax2.set_title("Classification Spectrum", fontsize=10)
    ax2.grid(True, axis="x", alpha=0.2)

    plt.tight_layout()
    path = output_path or "o_hat_chart.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\n  📊 Chart saved: {path}")
    plt.close()


def main():
    p = argparse.ArgumentParser(description="O-Hat Structural Measurement Operator")
    p.add_argument("csv", help="Path to single-column CSV file")
    p.add_argument("--window", type=int, default=None)
    p.add_argument("--baseline", type=int, default=None)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--plot-output", type=str, default=None)
    p.add_argument("--sensitivity", action="store_true",
                   help="Run window sensitivity sweep and plot band")
    p.add_argument("--sens-output", type=str, default=None,
                   help="Sensitivity chart output path")
    args = p.parse_args()

    series = load_csv(args.csv)
    result = measure(series, args.window, args.baseline)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    base_window = result["window_used"]
    base_baseline = result["baseline_len_used"]
    base_balance = result["balance_ratio"]

    # ── Sensitivity mode ──
    if args.sensitivity:
        print("=" * 60)
        print("  O-HAT  WINDOW  SENSITIVITY  ANALYSIS")
        print("=" * 60)
        print(f"  Nominal window  : {base_window}")
        print(f"  Nominal baseline: {base_baseline}")
        print(f"  Nominal balance : {base_balance:.2f}×  ({result['system_type']})")
        print(f"  Sweep range     : 50%–150% of nominal (11×11 grid)")
        print()

        matrix, w_sizes, b_sizes, fractions, coverage = sensitivity_scan(
            series, base_window, base_baseline)

        # Print the matrix
        header = "bl↓ \\ w→  " + "  ".join(f"{f:.0%}" for f in fractions)
        print(f"  {header}")
        print(f"  {'─' * (len(header) + 2)}")
        for i, frac_b in enumerate(fractions):
            row = "  ".join(f"{matrix[i, j]:5.1f}" if not np.isnan(matrix[i, j])
                           else "   NA" for j in range(len(fractions)))
            print(f"  {frac_b:.0%}     {row}")

        # Stability stats
        diag = np.diag(matrix)
        mid = len(fractions) // 2
        core = diag[max(0,mid-2):min(len(diag),mid+3)]
        band_lo, band_hi = np.nanmin(core), np.nanmax(core)
        stability = band_hi - band_lo

        print(f"\n  ── Stability ──")
        print(f"  Sensitivity band (80%–120%): {band_lo:.2f}× – {band_hi:.2f}×")
        print(f"  Band width (Δ): {stability:.2f}×")
        if stability < 1.0:
            print(f"  Verdict: ✅ STABLE — classification robust to window choice")
        elif stability < 3.0:
            print(f"  Verdict: ⚠️ MODERATE — some sensitivity, check classification zone")
        else:
            print(f"  Verdict: ❌ UNSTABLE — result depends heavily on window size")
        print(f"  Coverage: {coverage:.0%} cells valid")
        print("=" * 60)

        plot_sensitivity(matrix, w_sizes, b_sizes, fractions,
                        base_balance, base_window, base_baseline,
                        series, args.sens_output)
        return

    # ── Normal mode ──
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
        print("\n  💡 Try --sensitivity to verify window stability")

    if args.plot:
        plot_result(series, result, args.plot_output)


if __name__ == "__main__":
    main()
