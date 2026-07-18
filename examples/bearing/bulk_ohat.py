#!/usr/bin/env python3
"""
XJTU-SY Bearing Run-to-Failure: Envelope Ô-HAT Analysis
=======================================================
Follows the successful CWRU Envelope pattern:
  1. Load all CSVs per bearing (Horizontal + Vertical vibration)
  2. Apply Hilbert envelope (abs(hilbert(signal)) → amplitude modulation)
  3. Concatenate into single run-to-failure time series
  4. Run sliding-window Ô-HAT to detect degradation phase transitions
  5. Classify: CONTINUOUS_FLOW → PULSE → COLLAPSE

24-07-18: Initial XJTU-SY integration for Bearing1_1 (quick test) + Bearing2_1 (longest).
Target: NAS deployment with resource monitoring.
"""

import os, sys, csv, argparse, json, time
import numpy as np
from scipy.signal import hilbert
from scipy import stats
from pathlib import Path

# Import local O-HAT
sys.path.insert(0, "/app/working/workspaces/tygtDc")
from o_hat.o_hat import measure, classify

# ── Constants ──
FS = 25600  # Hz
CSV_SAMPLES = 32768  # per file
CSV_DURATION = CSV_SAMPLES / FS  # 1.28s
HIGH_PASS_CUTOFF = 3000  # Hz (CWRU pattern: 3kHz highpass for bearing faults)
DECIMATE_FACTOR = 16  # 25.6kHz → 1.6kHz envelope (enough for bearing degradation)


def load_bearing_csv(data_dir, bearing_path):
    """Load all CSVs for one bearing, return (horizontal_signal, vertical_signal)."""
    full_path = Path(data_dir) / bearing_path
    csv_files = sorted(full_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSVs found in {full_path}")

    h_signals, v_signals = [], []
    for cf in csv_files:
        data = np.loadtxt(cf, delimiter=",", skiprows=1, dtype=np.float32)
        h_signals.append(data[:, 0])  # Horizontal
        v_signals.append(data[:, 1])  # Vertical

    return np.concatenate(h_signals), np.concatenate(v_signals), len(csv_files)


def compute_envelope(signal, highpass_cutoff=None, decimate=None):
    """Apply Hilbert envelope: |H(signal)| — amplitude modulation.
    Optional: highpass filter + decimation for efficiency.
    Returns envelope_signal."""
    # Simple highpass via FFT
    if highpass_cutoff and highpass_cutoff > 0:
        N = len(signal)
        freqs = np.fft.rfftfreq(N, d=1/FS)
        fft = np.fft.rfft(signal)
        cutoff_idx = int(highpass_cutoff * N / FS)
        if cutoff_idx > 0:
            fft[:cutoff_idx] = 0  # zero out below cutoff
        signal = np.fft.irfft(fft, n=N)

    # Hilbert envelope
    analytic = hilbert(signal)
    envelope = np.abs(analytic)

    # Decimate for efficiency
    if decimate and decimate > 1:
        envelope = envelope[::decimate]

    return envelope


def sliding_ohat(envelope, window_samples, stride, baseline_samples):
    """
    Sliding-window Ô-HAT: sweep across envelope signal.
    Returns list of dicts per window.
    """
    N = len(envelope)
    results = []
    n_windows = (N - window_samples) // stride + 1

    for i in range(n_windows):
        start = i * stride
        end = start + window_samples
        chunk = envelope[start:end]

        r = measure(chunk, window=window_samples, baseline_len=baseline_samples)
        r["window_start"] = start
        r["window_end"] = end
        r["time_sec"] = start / (FS / DECIMATE_FACTOR)
        results.append(r)

    return results


def find_transitions(results, threshold=3.0):
    """Find phase boundaries where balance_ratio crosses threshold.
    Returns list of (index, from_type, to_type)."""
    transitions = []
    for i in range(1, len(results)):
        prev_type = results[i-1]["system_type"]
        curr_type = results[i]["system_type"]
        if prev_type != curr_type:
            transitions.append({
                "window_index": i,
                "time_sec": results[i]["time_sec"],
                "from_type": prev_type,
                "to_type": curr_type,
                "balance_before": results[i-1]["balance_ratio"],
                "balance_after": results[i]["balance_ratio"],
            })
    return transitions


def main():
    parser = argparse.ArgumentParser(description="XJTU-SY Envelope O-HAT Analysis")
    parser.add_argument("--data-dir", default="/tmp/xjtu_sy/XJTU-SY_Bearing_Datasets")
    parser.add_argument("--bearing", default="35Hz12kN/Bearing1_1",
                       help="e.g. '35Hz12kN/Bearing1_1' or '37.5Hz11kN/Bearing2_1'")
    parser.add_argument("--window-sec", type=float, default=10.0,
                       help="Sliding window size in seconds (default: 10)")
    parser.add_argument("--stride-sec", type=float, default=2.0,
                       help="Stride in seconds (default: 2)")
    parser.add_argument("--baseline-sec", type=float, default=5.0,
                       help="Baseline in seconds for skew estimation (default: 5)")
    parser.add_argument("--channel", default="both", choices=["horizontal", "vertical", "both"])
    parser.add_argument("--json-out", help="Save results as JSON")
    parser.add_argument("--csv-out", help="Save sliding window results as CSV")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    # Decimate effective FS
    fs_eff = FS / DECIMATE_FACTOR

    window_samples = int(args.window_sec * fs_eff)
    stride_samples = int(args.stride_sec * fs_eff)
    baseline_samples = int(args.baseline_sec * fs_eff)

    t0 = time.time()

    # ── Load ──
    if not args.quiet:
        print(f"📂 Loading {args.bearing}...", end=" ", flush=True)
    h_signal, v_signal, n_csvs = load_bearing_csv(args.data_dir, args.bearing)
    duration_min = len(h_signal) / FS / 60
    if not args.quiet:
        print(f"{n_csvs} CSVs, {len(h_signal):,} samples, {duration_min:.1f} min @ {FS}Hz")

    # ── Envelope ──
    if not args.quiet:
        print(f"📡 Computing envelope (Hilbert, {HIGH_PASS_CUTOFF/1000:.0f}kHz highpass, {DECIMATE_FACTOR}× decimate)...", end=" ", flush=True)

    if args.channel == "horizontal":
        env = compute_envelope(h_signal, HIGH_PASS_CUTOFF, DECIMATE_FACTOR)
    elif args.channel == "vertical":
        env = compute_envelope(v_signal, HIGH_PASS_CUTOFF, DECIMATE_FACTOR)
    else:
        env_h = compute_envelope(h_signal, HIGH_PASS_CUTOFF, DECIMATE_FACTOR)
        env_v = compute_envelope(v_signal, HIGH_PASS_CUTOFF, DECIMATE_FACTOR)
        env = np.sqrt(env_h**2 + env_v**2)  # combined magnitude

    if not args.quiet:
        print(f"→ {len(env):,} samples @ {fs_eff}Hz ({len(env)/fs_eff:.0f}s)")

    # ── Sliding O-HAT ──
    n_wins = (len(env) - window_samples) // stride_samples + 1
    if not args.quiet:
        print(f"🔬 Sliding Ô-HAT: {n_wins} windows (window={args.window_sec}s, stride={args.stride_sec}s, baseline={args.baseline_sec}s)")

    results = sliding_ohat(env, window_samples, stride_samples, baseline_samples)
    transitions = find_transitions(results)
    # Cast all np types to Python native for JSON
    for t in transitions:
        for k in t:
            if hasattr(t[k], 'item'):
                t[k] = t[k].item()

    elapsed = time.time() - t0

    # ── Output ──
    balance_series = [r["balance_ratio"] for r in results]
    types_series = [r["system_type"] for r in results]

    if not args.quiet:
        print()
        print("=" * 70)
        print("  XJTU-SY ENVELOPE Ô-HAT ANALYSIS")
        print("=" * 70)
        print(f"  Bearing       : {args.bearing}")
        print(f"  Duration      : {duration_min:.1f} min")
        print(f"  Channel       : {args.channel}")
        print(f"  Envelope      : {HIGH_PASS_CUTOFF/1000:.0f}kHz HP + {DECIMATE_FACTOR}× decimate")
        print(f"  Ô-HAT windows : {n_wins} × {args.window_sec}s")
        print(f"  Processing    : {elapsed:.1f}s")
        print(f"  ---")
        print(f"  Balance range : {min(balance_series):.2f}× – {max(balance_series):.2f}×")
        print(f"  Mean balance  : {np.mean(balance_series):.2f}×")
        print(f"  Median balance: {np.median(balance_series):.2f}×")

        type_counts = {}
        for t in types_series:
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"  Type distribution:")
        for t in ["REGIME SATURATION / NOISE", "CONTINUOUS FLOW", "PULSE", "SUPER-PULSE"]:
            if t in type_counts:
                pct = type_counts[t] / len(types_series) * 100
                print(f"    {t:30s}: {type_counts[t]:4d} ({pct:5.1f}%)")

        print(f"  ---")
        print(f"  Phase transitions detected: {len(transitions)}")
        for t in transitions:
            print(f"    @ {t['time_sec']:.0f}s: {t['from_type']} → {t['to_type']} "
                  f"(balance {t['balance_before']:.1f}→{t['balance_after']:.1f})")
        print("=" * 70)

        # Degradation curve assessment
        if len(transitions) == 0:
            if type_counts.get("CONTINUOUS FLOW", 0) / max(len(types_series), 1) > 0.7:
                print("\n  📊 Assessment: NO DEGRADATION DETECTED — bearing remained in CONTINUOUS FLOW")
                print("     This bearing may not have failed within recorded window.")
            else:
                print(f"\n  📊 Assessment: {max(type_counts, key=type_counts.get)} dominant — check window sensitivity")
        elif len(transitions) >= 2:
            print("\n  📊 Assessment: MULTI-PHASE DEGRADATION detected")
            sequences = [t["to_type"] for t in transitions]
            if "PULSE" in sequences:
                print("     CONTINUOUS_FLOW → PULSE → ? pattern confirmed ✓")

    # ── JSON output ──
    if args.json_out:
        import json
        output = {
            "bearing": args.bearing,
            "config": {
                "fs": FS, "highpass_hz": HIGH_PASS_CUTOFF, "decimate": DECIMATE_FACTOR,
                "window_sec": args.window_sec, "stride_sec": args.stride_sec,
                "baseline_sec": args.baseline_sec, "channel": args.channel,
            },
            "summary": {
                "n_csvs": n_csvs, "duration_min": round(duration_min, 1),
                "processing_sec": round(elapsed, 1),
                "balance_min": round(float(min(balance_series)), 2),
                "balance_max": round(float(max(balance_series)), 2),
                "balance_mean": round(float(np.mean(balance_series)), 2),
                "transitions": len(transitions),
            },
            "transitions": transitions,
            "sliding_windows": [
                {"t": float(r["time_sec"]), "balance": float(r["balance_ratio"]),
                 "curl": float(r["curl"]), "helicity": float(r["helicity"]),
                 "type": str(r["system_type"]),
                 "baseline_skew": float(r["baseline_skew"]), "outbreak_skew": float(r["outbreak_skew"])}
                for r in results
            ],
        }
        with open(args.json_out, "w") as f:
            json.dump(output, f, indent=2)
        if not args.quiet:
            print(f"\n  💾 JSON saved: {args.json_out}")

    # ── CSV output ──
    if args.csv_out:
        with open(args.csv_out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_sec", "balance_ratio", "curl", "helicity",
                            "system_type", "baseline_skew", "outbreak_skew"])
            for r in results:
                writer.writerow([
                    round(r["time_sec"], 1), r["balance_ratio"],
                    round(r["curl"], 2), round(r["helicity"], 2),
                    r["system_type"], r["baseline_skew"], r["outbreak_skew"]
                ])
        if not args.quiet:
            print(f"  💾 CSV saved: {args.csv_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
