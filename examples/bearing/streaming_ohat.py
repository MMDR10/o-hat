#!/usr/bin/env python3
"""
XJTU-SY Streaming Envelope Ô-HAT — NAS 低碳排版本
=================================================
策略：逐 CSV 讀取 → 就地 Hilbert envelope → 抽 mean energy → del raw → 下一個
491 個 CSV → 491 點精純特徵序列 → Ô-HAT 毫秒級跑完
RAM 佔用：< 50MB（單一 CSV 1.3MB + envelope buffer）
"""

import os, sys, csv, argparse, json
import numpy as np
from scipy.signal import hilbert
from pathlib import Path

sys.path.insert(0, "/app/working/workspaces/tygtDc")
from o_hat.o_hat import measure, classify

FS = 25600
CSV_SAMPLES = 32768
HIGH_PASS_CUTOFF = 3000  # Hz


def extract_envelope_energy(csv_path):
    """
    Read ONE CSV → highpass + Hilbert envelope → mean energy (scalar).
    Returns: (horizontal_mean, vertical_mean, combined_mean)
    """
    data = np.loadtxt(csv_path, delimiter=",", skiprows=1, dtype=np.float32)
    h_raw = data[:, 0].astype(np.float64)
    v_raw = data[:, 1].astype(np.float64)

    def envelope(signal):
        # FFT highpass
        N = len(signal)
        freqs = np.fft.rfftfreq(N, d=1/FS)
        fft = np.fft.rfft(signal)
        cutoff_idx = int(HIGH_PASS_CUTOFF * N / FS)
        if cutoff_idx > 0:
            fft[:cutoff_idx] = 0
        filtered = np.fft.irfft(fft, n=N)
        # Hilbert envelope
        analytic = hilbert(filtered)
        env = np.abs(analytic)
        return float(np.mean(env))

    h_mean = envelope(h_raw)
    v_mean = envelope(v_raw)
    combined = np.sqrt(h_mean**2 + v_mean**2)

    del data, h_raw, v_raw
    return h_mean, v_mean, combined


def process_bearing(data_dir, bearing_path, verbose=True, use_channel="combined"):
    """Stream through all CSVs, build lightweight energy time series."""
    full_path = Path(data_dir) / bearing_path
    csv_files = sorted(full_path.glob("*.csv"))
    n = len(csv_files)

    if n == 0:
        return None, 0

    series = np.zeros(n, dtype=np.float64)

    for i, cf in enumerate(csv_files):
        h, v, c = extract_envelope_energy(str(cf))
        if use_channel == "horizontal":
            series[i] = h
        elif use_channel == "vertical":
            series[i] = v
        else:
            series[i] = c

        if verbose and (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{n} CSVs processed ({(i+1)/n*100:.0f}%)", flush=True)

    return series, n


def main():
    p = argparse.ArgumentParser(description="XJTU-SY Streaming Envelope O-HAT (NAS低碳版)")
    p.add_argument("--data-dir", default="/tmp/xjtu_sy/XJTU-SY_Bearing_Datasets")
    p.add_argument("--bearing", default="37.5Hz11kN/Bearing2_1")
    p.add_argument("--channel", default="combined", choices=["horizontal", "vertical", "combined"])
    p.add_argument("--window", type=int, default=10, help="O-HAT window size in points (default: 10)")
    p.add_argument("--baseline", type=int, default=50, help="Baseline size in points (default: 50)")
    p.add_argument("--json-out", help="Save full metrics to JSON")
    p.add_argument("--csv-out", help="Save energy series to CSV")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    import time
    t0 = time.time()

    # ── Streaming extraction ──
    if not args.quiet:
        print(f"📂 Streaming {args.bearing} ...", flush=True)

    series, n_csvs = process_bearing(args.data_dir, args.bearing, verbose=not args.quiet, use_channel=args.channel)

    if series is None:
        print("❌ No CSVs found!", file=sys.stderr)
        sys.exit(1)

    extract_time = time.time() - t0

    if not args.quiet:
        print(f"✅ {n_csvs} CSVs → {len(series)} energy points ({extract_time:.1f}s)")
        print(f"   RAM: ~{n_csvs * 8 / 1024:.1f} KB for time series (vs old method: ~{n_csvs * CSV_SAMPLES * 4 / 1024 / 1024:.0f} MB)")
        print(f"   Energy range: {series.min():.4f} – {series.max():.4f}")
        print(f"   Energy mean:  {series.mean():.4f}")

    # ── Normalize (important: raw envelope values vary by bearing) ──
    series_norm = (series - series.mean()) / (series.std() + 1e-10)

    # ── O-HAT sliding window ──
    if not args.quiet:
        print(f"\n🔬 O-HAT sliding window (window={args.window}, baseline={args.baseline}) ...", flush=True)

    N = len(series)
    stride = max(1, args.window // 5)
    n_wins = (N - args.window) // stride + 1

    results = []
    for i in range(n_wins):
        start = i * stride
        end = start + args.window
        chunk = series_norm[start:end]

        r = measure(chunk, window=args.window, baseline_len=min(args.baseline, args.window))
        r["window_start"] = start
        r["window_end"] = end
        r["time_min"] = start * 1.28 / 60  # each CSV = 1.28s
        results.append(r)

    ohat_time = time.time() - t0 - extract_time

    # ── Analysis ──
    balance_series = [r["balance_ratio"] for r in results]
    types_series = [r["system_type"] for r in results]
    type_counts = {}
    for t in types_series:
        type_counts[t] = type_counts.get(t, 0) + 1

    # Find transitions
    transitions = []
    for i in range(1, len(results)):
        if results[i-1]["system_type"] != results[i]["system_type"]:
            transitions.append({
                "point": i, "time_min": round(results[i]["time_min"], 1),
                "from": results[i-1]["system_type"],
                "to": results[i]["system_type"],
                "balance_before": results[i-1]["balance_ratio"],
                "balance_after": results[i]["balance_ratio"],
            })

    # ── Output ──
    if not args.quiet:
        print()
        print("=" * 70)
        print("  XJTU-SY STREAMING ENVELOPE Ô-HAT — NAS 低碳排報告")
        print("=" * 70)
        print(f"  Bearing        : {args.bearing}")
        print(f"  CSVs streamed  : {n_csvs} (1.28s each)")
        print(f"  Total duration : {n_csvs * 1.28 / 60:.1f} min")
        print(f"  Channel        : {args.channel}")
        print(f"  Extract time   : {extract_time:.1f}s")
        print(f"  Ô-HAT time     : {ohat_time:.3f}s")
        print(f"  RAM footprint  : < 50MB")
        print(f"  ---")
        print(f"  Energy range   : {series.min():.4f} – {series.max():.4f}")
        print(f"  Balance range  : {min(balance_series):.2f}× – {max(balance_series):.2f}×")
        print(f"  Mean balance   : {np.mean(balance_series):.2f}×")
        print(f"  ---")
        print(f"  Type distribution ({n_wins} windows):")
        for t in ["REGIME SATURATION / NOISE", "CONTINUOUS FLOW", "PULSE", "SUPER-PULSE"]:
            if t in type_counts:
                pct = type_counts[t] / n_wins * 100
                bar = "█" * int(pct / 2)
                print(f"    {t:30s}: {type_counts[t]:4d} ({pct:5.1f}%) {bar}")

        print(f"  ---")
        print(f"  Phase transitions: {len(transitions)}")
        if len(transitions) <= 20:
            for t in transitions:
                arrow = f"{t['from']} → {t['to']}"
                print(f"    @ point {t['point']:3d} ({t['time_min']:5.1f}min): {arrow:45s} balance {t['balance_before']:.1f}→{t['balance_after']:.1f}")
        else:
            for t in transitions[:10]:
                arrow = f"{t['from']} → {t['to']}"
                print(f"    @ point {t['point']:3d} ({t['time_min']:5.1f}min): {arrow:45s} balance {t['balance_before']:.1f}→{t['balance_after']:.1f}")
            print(f"    ... and {len(transitions)-10} more")

        # Trend analysis
        first_half = np.mean(balance_series[:n_wins//2])
        last_quarter = np.mean(balance_series[3*n_wins//4:])
        trend = "↑ RISING" if last_quarter > first_half * 1.2 else "↓ FALLING" if last_quarter < first_half * 0.8 else "→ STABLE"
        print(f"  ---")
        print(f"  Trend (first half → last quarter): {first_half:.2f}× → {last_quarter:.2f}×  [{trend}]")

        # Degradation verdict
        if max(balance_series) > 10:
            print(f"\n  🔥 判決：強烈退化信號 — Balance 突破 10×，系統接近結構性崩潰！")
        elif max(balance_series) > 5:
            print(f"\n  ⚡ 判決：明顯退化 — Balance 進入 PULSE 區間，系統正在經歷相變")
        elif max(balance_series) > 2:
            print(f"\n  📊 判決：溫和退化 — Balance 進入 CONTINUOUS FLOW，需觀察趨勢")
        else:
            print(f"\n  🟢 判決：無明顯退化 — 軸承在記錄期間內可能未達故障階段")
        print("=" * 70)

    # ── JSON output ──
    if args.json_out:
        output = {
            "bearing": args.bearing, "channel": args.channel,
            "n_csvs": n_csvs, "duration_min": round(n_csvs * 1.28 / 60, 1),
            "extract_sec": round(extract_time, 1), "ohat_sec": round(ohat_time, 3),
            "energy_min": round(float(series.min()), 6),
            "energy_max": round(float(series.max()), 6),
            "energy_mean": round(float(series.mean()), 6),
            "balance_min": round(float(min(balance_series)), 2),
            "balance_max": round(float(max(balance_series)), 2),
            "balance_mean": round(float(np.mean(balance_series)), 2),
            "n_windows": n_wins, "window_points": args.window,
            "type_distribution": type_counts,
            "transitions": [{
                "point": t["point"], "time_min": t["time_min"],
                "from": t["from"], "to": t["to"],
                "balance_before": round(t["balance_before"], 2),
                "balance_after": round(t["balance_after"], 2),
            } for t in transitions],
            "sliding_windows": [{
                "t": int(r["window_start"]), "time_min": round(r["time_min"], 1),
                "balance": round(float(r["balance_ratio"]), 2),
                "curl": round(float(r["curl"]), 2),
                "helicity": round(float(r["helicity"]), 2),
                "type": str(r["system_type"]),
            } for r in results],
        }
        with open(args.json_out, "w") as f:
            json.dump(output, f, indent=2)
        if not args.quiet:
            print(f"\n  💾 JSON: {args.json_out}")

    # ── CSV output ──
    if args.csv_out:
        with open(args.csv_out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["point", "time_min", "energy", "energy_norm", "balance", "curl", "helicity", "type"])
            for i, r in enumerate(results):
                writer.writerow([
                    int(r["window_start"]), round(r["time_min"], 1),
                    round(float(series[int(r["window_start"]):int(r["window_end"])].mean()), 6),
                    round(float(series_norm[int(r["window_start"]):int(r["window_end"])].mean()), 4),
                    round(float(r["balance_ratio"]), 2),
                    round(float(r["curl"]), 2),
                    round(float(r["helicity"]), 2),
                    str(r["system_type"]),
                ])
        if not args.quiet:
            print(f"  💾 CSV:  {args.csv_out}")


if __name__ == "__main__":
    main()
