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
    }


def main():
    p = argparse.ArgumentParser(description="O-Hat Structural Measurement Operator")
    p.add_argument("csv", help="Path to single-column CSV file")
    p.add_argument("--window", type=int, default=None, help="Outbreak window size")
    p.add_argument("--baseline", type=int, default=None, help="Baseline length")
    p.add_argument("--quiet", action="store_true", help="Numerical output only")
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

        # Classification reference
        print("\n  Reference spectrum:")
        print("    SUPER-PULSE        > 20x   (e.g. 1989 Quebec Storm)")
        print("    PULSE             5-15x   (e.g. Earthquakes)")
        print("    CONTINUOUS FLOW   1.5-4x  (e.g. ENSO, COVID)")
        print("    REGIME SATURATION  < 1.5x  (e.g. Seasonal forcing)")


if __name__ == "__main__":
    main()
