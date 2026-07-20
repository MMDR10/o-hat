#!/usr/bin/env python3
"""
Ô Grid Frequency Anomaly Classifier
====================================
Automated classification of power grid frequency segments into:
  - NORMAL              : typical stochastic volatility
  - DYNAMIC_INSTABILITY : high helicity + elevated freq_std
  - STATIC_BIAS         : low helicity + elevated freq_std (DC offset)
  - QUIESCENT           : low helicity + low freq_std

Based on H × H_v3 diagnostic quadrant from:
  DR (2026). Ô Helicity Framework Case Study: Power Grid Frequency Anomaly
  Classification. Zenodo. doi:10.5281/zenodo.21448537

Usage:
  python o_classifier.py --input data.csv --window 100 --stride 50
  python o_classifier.py --help

Dependencies: numpy, scipy
"""

import argparse
import csv
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, asdict
from typing import List, Tuple

import numpy as np


# ─────────────────────────────────────────────────────────────────────
# Core Ô computation
# ─────────────────────────────────────────────────────────────────────

def compute_o_metrics(trajectory: np.ndarray) -> dict:
    """
    Compute Ô helicity metrics from a trajectory matrix.

    Args:
        trajectory: (L, d) array; L = layers/windows, d = features per window.
    """
    L, d = trajectory.shape
    if L < 2:
        raise ValueError(f"Trajectory must have at least 2 layers, got {L}")

    X = trajectory - trajectory.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    pc1 = U[:, 0] * S[0]
    pc2 = U[:, 1] * S[1] if d >= 2 else np.zeros(L)

    per_layer_H = np.zeros(L - 1)
    for l in range(L - 1):
        dx = pc1[l + 1] - pc1[l]
        dy = pc2[l + 1] - pc2[l]
        forward = abs(dx)
        rotation = abs(dy)
        per_layer_H[l] = rotation / max(forward, 1e-12)

    H_mean = float(np.mean(per_layer_H))
    H_skew = float(
        ((per_layer_H - H_mean) ** 3).mean()
        / max(per_layer_H.std() ** 3, 1e-12)
    )

    centroid = np.array([pc1.mean(), pc2.mean()])
    angles = np.array(
        [np.arctan2(pc2[l] - centroid[1], pc1[l] - centroid[0]) for l in range(L)]
    )
    H_v3 = float(np.sum(np.abs(np.diff(np.unwrap(angles)))))

    return {
        "H": H_mean,
        "H_v3": H_v3,
        "H_median": float(np.median(per_layer_H)),
        "H_p95": float(np.percentile(per_layer_H, 95)),
        "H_max": float(np.max(per_layer_H)),
        "H_skew": H_skew,
        "H_lt1_pct": float(np.mean(per_layer_H < 1.0) * 100),
        "H_gt3_pct": float(np.mean(per_layer_H > 3.0) * 100),
        "n_layers": L,
    }


# ─────────────────────────────────────────────────────────────────────
# Time series → trajectory
# ─────────────────────────────────────────────────────────────────────

def time_series_to_trajectory(
    freq: np.ndarray, window: int = 100, stride: int = 50
) -> Tuple[np.ndarray, np.ndarray]:
    """Convert 1D frequency to trajectory via sliding windows (5 features each)."""
    n_windows = (len(freq) - window) // stride + 1
    trajectory = np.zeros((n_windows, 5))
    centers = np.zeros(n_windows, dtype=int)

    for i in range(n_windows):
        s = i * stride
        chunk = freq[s : s + window]
        n = len(chunk)
        mu = np.mean(chunk)
        sigma = np.std(chunk)

        trajectory[i, 0] = mu
        trajectory[i, 1] = sigma
        trajectory[i, 2] = float(
            np.sum(((chunk - mu) / max(sigma, 1e-12)) ** 3) / n
        )
        trajectory[i, 3] = float(
            np.sum(((chunk - mu) / max(sigma, 1e-12)) ** 4) / n - 3
        )
        trajectory[i, 4] = np.max(chunk) - np.min(chunk)
        centers[i] = s + window // 2

    return trajectory, centers


# ─────────────────────────────────────────────────────────────────────
# Classification
# ─────────────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    label: str
    confidence: str
    H: float
    H_v3: float
    freq_std: float
    freq_range: float
    reasoning: str


def classify_segment(
    metrics: dict,
    freq_signal: np.ndarray,
    H_threshold: float = 10.0,
    H_v3_threshold: float = 1.5,
    freq_std_threshold: float = 22.0,
) -> ClassificationResult:
    H = metrics["H"]
    H_v3 = metrics["H_v3"]
    f_std = float(np.std(freq_signal))
    f_range = float(np.max(freq_signal) - np.min(freq_signal))

    if H < H_threshold and H_v3 < H_v3_threshold:
        if f_std > freq_std_threshold:
            return ClassificationResult(
                "STATIC_BIAS", "HIGH", H, H_v3, f_std, f_range,
                f"H={H:.1f}<{H_threshold}, H_v3={H_v3:.2f}<{H_v3_threshold}, "
                f"f_std={f_std:.1f}>{freq_std_threshold} → DC offset",
            )
        return ClassificationResult(
            "QUIESCENT", "HIGH", H, H_v3, f_std, f_range,
            f"H={H:.1f}<{H_threshold}, H_v3={H_v3:.2f}<{H_v3_threshold}, "
            f"f_std={f_std:.1f}≤{freq_std_threshold} → quiescent",
        )

    if H >= H_threshold and H_v3 >= H_v3_threshold:
        conf = "HIGH" if H > 15 and H_v3 > 2.0 else "MEDIUM"
        return ClassificationResult(
            "DYNAMIC_INSTABILITY", conf, H, H_v3, f_std, f_range,
            f"H={H:.1f}≥{H_threshold}, H_v3={H_v3:.2f}≥{H_v3_threshold} → dynamic instability",
        )

    if H >= H_threshold and H_v3 < H_v3_threshold:
        flag = f_std > freq_std_threshold
        return ClassificationResult(
            "NORMAL", "HIGH", H, H_v3, f_std, f_range,
            f"H={H:.1f}≥{H_threshold}, H_v3={H_v3:.2f}<{H_v3_threshold}"
            + (f", f_std={f_std:.1f}>{freq_std_threshold} (elevated)" if flag else ""),
        )

    return ClassificationResult(
        "UNUSUAL", "LOW", H, H_v3, f_std, f_range,
        f"H={H:.1f}<{H_threshold}, H_v3={H_v3:.2f}≥{H_v3_threshold} → unusual quadrant",
    )


# ─────────────────────────────────────────────────────────────────────
# Stream classifier
# ─────────────────────────────────────────────────────────────────────

def classify_stream(
    freq: np.ndarray,
    window: int = 100,
    stride: int = 50,
    segment_duration: int = 3600,
    H_threshold: float = 10.0,
    H_v3_threshold: float = 1.5,
    freq_std_threshold: float = 22.0,
) -> List[dict]:
    results = []
    pos = 0
    while pos < len(freq):
        end = min(pos + segment_duration, len(freq))
        segment = freq[pos:end]
        if len(segment) < window:
            break
        try:
            traj, _ = time_series_to_trajectory(segment, window, stride)
            metrics = compute_o_metrics(traj)
            r = classify_segment(metrics, segment, H_threshold, H_v3_threshold, freq_std_threshold)
        except ValueError as e:
            r = ClassificationResult("ERROR", "N/A", 0, 0, 0, 0, str(e))
        results.append({"start_s": pos, "end_s": end, "duration_s": end - pos, **asdict(r)})
        pos += segment_duration
    return results


# ─────────────────────────────────────────────────────────────────────
# I/O
# ─────────────────────────────────────────────────────────────────────

def load_frequency_csv(path: str) -> np.ndarray:
    data = []
    with open(path) as f:
        for row in csv.reader(f):
            if row:
                try:
                    data.append(float(row[0]))
                except ValueError:
                    pass
    arr = np.array(data, dtype=np.float64)
    return arr[~np.isnan(arr)]


def main():
    parser = argparse.ArgumentParser(
        description="Ô Grid Frequency Anomaly Classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python o_classifier.py --input de_freq.csv
  python o_classifier.py --input fr_freq.csv --H-threshold 6.0
  python o_classifier.py --input data.csv --json""",
    )
    parser.add_argument("--input", "-i", required=True, help="CSV of frequency values (mHz)")
    parser.add_argument("--window", "-w", type=int, default=100)
    parser.add_argument("--stride", "-s", type=int, default=50)
    parser.add_argument("--segment", type=int, default=3600, help="Segment duration in samples")
    parser.add_argument("--H-threshold", type=float, default=10.0)
    parser.add_argument("--H-v3-threshold", type=float, default=1.5)
    parser.add_argument("--freq-std-threshold", type=float, default=22.0)
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    print(f"Loading: {args.input}", file=sys.stderr)
    freq = load_frequency_csv(args.input)
    print(f"Loaded {len(freq):,} valid points", file=sys.stderr)

    t0 = time.time()
    results = classify_stream(
        freq, args.window, args.stride, args.segment,
        args.H_threshold, args.H_v3_threshold, args.freq_std_threshold,
    )
    elapsed = time.time() - t0
    print(f"Classified {len(results)} segments in {elapsed:.1f}s", file=sys.stderr)

    counts = Counter(r["label"] for r in results)
    print(f"Distribution: {dict(counts)}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"{'Start':>10s} {'End':>10s} {'Label':>22s} {'Conf':>6s} {'H':>8s} {'H_v3':>6s} {'f_std':>8s}")
        print("-" * 80)
        for r in results:
            print(f"{r['start_s']:>10d} {r['end_s']:>10d} {r['label']:>22s} "
                  f"{r['confidence']:>6s} {r['H']:>8.1f} {r['H_v3']:>6.2f} {r['freq_std']:>8.1f}")


if __name__ == "__main__":
    main()
