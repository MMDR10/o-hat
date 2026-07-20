#!/usr/bin/env python3
"""
Synthetic Iberian Blackout Reconstruction for Ô Validation
===========================================================
Reconstructs the April 28, 2025 Iberian blackout frequency timeline
from ENTSO-E / NREL / Gridradar documented parameters, then applies
the Ô classifier to test dynamic instability detection.

Timeline (CEST = UTC+2):
  12:03-12:07  First oscillation: 0.6 Hz dominant, ~25 mHz amplitude
  12:19-12:22  Second oscillation: 0.6 Hz dominant, ~43 mHz amplitude
  12:32:57.2   G-1 trip: 355 MW loss → Δf = -26 mHz
  12:33:16.5   G-2 trip: 47.7 mHz drop in 100 ms
  12:33:18     G-3 trip
  12:33:19.62  Loss of synchronism with CESA
  12:33:23.96  HVDC Baixas-Santa Llogaia trip → total separation
  12:33:25     Frequency collapse below 48 Hz

Parameters from NREL report:
  - RoCoF within 1 Hz/s until 12:33:20.56
  - Cumulative generation loss: ~15 GW
  - Frequency nadir: ~48.0 Hz before separation
  - Oscillation: 0.6 Hz inter-area, 0.2 Hz local
"""

import numpy as np
import json
import sys
import time

# Import classifier
sys.path.insert(0, '/app/working/workspaces/tygtDc/output/grid')
from o_classifier import (
    time_series_to_trajectory,
    compute_o_metrics,
    classify_segment,
    classify_stream,
)

SAMPLING_RATE = 1  # Hz


def generate_iberian_blackout(duration_s: int = 2100) -> np.ndarray:
    """
    Generate synthetic Iberian blackout frequency timeseries.

    Covers 12:00 to 12:35 CEST (2100 seconds).
    Returns frequency deviation from 50 Hz, in mHz. Positive = above 50 Hz.
    """
    np.random.seed(28)  # April 28
    t = np.arange(duration_s, dtype=np.float64) * (1.0 / SAMPLING_RATE)
    f = np.zeros(duration_s, dtype=np.float64)

    # ── Phase 0: Normal operation (12:00-12:02) ──
    # Baseline noise: σ ≈ 10 mHz for Iberian grid
    mask0 = t < 120
    f[mask0] = np.random.randn(np.sum(mask0)) * 10.0

    # ── Phase 1: First oscillation (12:03-12:07, t=180-420) ──
    # 0.6 Hz oscillation, ~25 mHz amplitude
    mask1 = (t >= 180) & (t < 420)
    t1 = t[mask1] - 180
    f_osc1 = 25.0 * np.sin(2 * np.pi * 0.6 * t1) * np.exp(-(t1 - 120) ** 2 / (120 ** 2))
    f[mask1] = np.random.randn(np.sum(mask1)) * 8.0 + f_osc1

    # ── Phase 2: Between oscillations, elevated noise ──
    mask2 = (t >= 420) & (t < 1140)
    f[mask2] = np.random.randn(np.sum(mask2)) * 12.0

    # ── Phase 3: Second oscillation (12:19-12:22, t=1140-1320) ──
    # 0.6 Hz, ~43 mHz amplitude — stronger
    mask3 = (t >= 1140) & (t < 1320)
    t3 = t[mask3] - 1140
    f_osc3 = 43.0 * np.sin(2 * np.pi * 0.6 * t3) * np.exp(-(t3 - 90) ** 2 / (90 ** 2))
    f[mask3] = np.random.randn(np.sum(mask3)) * 10.0 + f_osc3

    # ── Phase 4: Post-oscillation, unstable (12:22-12:32:57) ──
    # Voltage rising, distributed gen tripping, frequency drifting
    mask4 = (t >= 1320) & (t < 1977)
    t4 = t[mask4] - 1320
    drift = -5.0 * np.sin(2 * np.pi * 0.08 * t4)  # slow drift
    f[mask4] = np.random.randn(np.sum(mask4)) * 15.0 + drift

    # ── Phase 5: G-1 trip (12:32:57.2, t=1977.2) ──
    # 355 MW loss → Δf ≈ -26 mHz in 200 ms
    # RoCoF = 0.13 Hz/s
    idx_g1 = int(1977 * SAMPLING_RATE)
    # Ramp down over 5 seconds
    for i in range(5):
        if idx_g1 + i < duration_s:
            f[idx_g1 + i] = f[idx_g1 + i] - (26.0 / 5) * (i + 1)

    # ── Phase 6: Between G-1 and G-2 (1977-1993), frequency recovering? No — still falling ──
    mask6 = (t >= 1982) & (t < 1993)
    f[mask6] = np.random.randn(np.sum(mask6)) * 12.0 - 26.0

    # ── Phase 7: G-2 trip (12:33:16.5, t=1996.5) ──
    # 47.7 mHz in 100 ms; RoCoF ~0.48 Hz/s
    # Then G-3 at 12:33:18
    idx_g2 = int(1996 * SAMPLING_RATE)
    for i in range(3):
        if idx_g2 + i < duration_s:
            f[idx_g2 + i] = f[idx_g2 + i] - (47.7 / 3) * (i + 1)

    idx_g3 = int(1998 * SAMPLING_RATE)
    for i in range(2):
        if idx_g3 + i < duration_s:
            f[idx_g3 + i] = f[idx_g3 + i] - (25.0 / 2) * (i + 1)

    # ── Phase 8: Cascade collapse (12:33:18 → 12:33:25) ──
    # Cumulative loss ~15 GW → frequency collapse
    mask8a = (t >= 1998) & (t < 2005)
    # Rapid descent: ~1000 mHz over 7 seconds, slightly curved
    t8 = t[mask8a] - 1998
    collapse = -1000.0 * (t8 / 7) ** 1.3
    f[mask8a] = collapse

    # Loss of synchronism 12:33:19.62, frequency continues to fall
    mask8b = (t >= 2005) & (t < 2025)
    f[mask8b] = -1000.0 + np.random.randn(np.sum(mask8b)) * 50.0

    # ── Phase 9: Post-separation (12:33:25 → 12:35) ──
    # Iberian island collapses below 48 Hz; Continental Europe recovers to 50 Hz
    # We model Iberian-side collapse
    mask9 = (t >= 2025) & (t < duration_s)
    t9 = t[mask9] - 2025
    # Deep descent into blackout
    f[mask9] = -1000.0 - 500.0 * (1 - np.exp(-t9 / 15)) + np.random.randn(np.sum(mask9)) * 30.0

    return f


def main():
    print("Generating synthetic Iberian blackout (35 min, 1 Hz)...")
    t0 = time.time()
    freq = generate_iberian_blackout(2100)
    print(f"Generated {len(freq):,} samples in {time.time()-t0:.1f}s")

    # ── Run Ô classifier on 2-minute segments for fine-grained detection ──
    print("\n=== Ô Classification (120s segments) ===")
    results = classify_stream(
        freq,
        window=60,
        stride=30,
        segment_duration=120,  # 2-minute segments for high resolution
        H_threshold=10.0,
        H_v3_threshold=1.5,
        freq_std_threshold=22.0,
    )

    # ── Identify key phases ──
    key_phases = {
        "NORMAL": (0, 120),
        "OSCILLATION_1": (180, 420),
        "BETWEEN_OSCILLATIONS": (420, 1140),
        "OSCILLATION_2": (1140, 1320),
        "PRE_TRIP_UNSTABLE": (1320, 1977),
        "G1_TRIP": (1977, 1993),
        "G2_G3_TRIP": (1993, 2005),
        "COLLAPSE": (2005, 2100),
    }

    phase_results = {}
    for phase_name, (start, end) in key_phases.items():
        phase_segments = [r for r in results if r["start_s"] < end and r["end_s"] > start]
        if phase_segments:
            labels = [r["label"] for r in phase_segments]
            h_vals = [r["H"] for r in phase_segments]
            hv3_vals = [r["H_v3"] for r in phase_segments]
            fstds = [r["freq_std"] for r in phase_segments]
            phase_results[phase_name] = {
                "n_segments": len(phase_segments),
                "label_counts": {lab: labels.count(lab) for lab in set(labels)},
                "H_mean": float(np.mean(h_vals)),
                "H_v3_mean": float(np.mean(hv3_vals)),
                "freq_std_mean": float(np.mean(fstds)),
            }

    # ── Full classification summary ──
    from collections import Counter
    all_labels = Counter(r["label"] for r in results)

    output = {
        "description": "Synthetic Iberian Blackout (April 28, 2025) Ô Analysis",
        "parameters": {
            "duration_s": 2100,
            "sampling_rate_hz": SAMPLING_RATE,
            "H_threshold": 10.0,
            "H_v3_threshold_rad": 1.5,
            "freq_std_threshold_mHz": 22.0,
            "segment_duration_s": 60,
        },
        "overall_distribution": dict(all_labels),
        "phase_analysis": phase_results,
    }

    print("\n=== Full Analysis ===")
    print(json.dumps(output, indent=2, default=str))

    # ── Key verdict ──
    print("\n" + "=" * 60)
    print("KEY VERDICT")
    print("=" * 60)

    # Did Ô detect the oscillations as DYNAMIC_INSTABILITY?
    osc1 = phase_results.get("OSCILLATION_1", {})
    osc2 = phase_results.get("OSCILLATION_2", {})
    col = phase_results.get("COLLAPSE", {})

    for name, phase in [("Oscillation 1", osc1), ("Oscillation 2", osc2), ("Collapse", col)]:
        if phase:
            counts = phase.get("label_counts", {})
            H = phase.get("H_mean", 0)
            Hv3 = phase.get("H_v3_mean", 0)
            dim = counts.get("DYNAMIC_INSTABILITY", 0)
            total = phase.get("n_segments", 1)
            print(f"  {name}: H={H:.1f}, H_v3={Hv3:.2f} rad → "
                  f"DYNAMIC_INSTABILITY in {dim}/{total} segments ({100*dim/total:.0f}%)")

    # ── Direct pre-oscillation metrics ──
    print("\n=== Direct Ô on Pure Oscillation (120s window) ===")
    # Pure 0.6 Hz, 43 mHz amplitude oscillation
    t_pure = np.arange(120 * SAMPLING_RATE, dtype=np.float64) / SAMPLING_RATE
    pure_osc = 43.0 * np.sin(2 * np.pi * 0.6 * t_pure) + np.random.randn(len(t_pure)) * 5.0
    traj_pure, _ = time_series_to_trajectory(pure_osc, 60, 30)
    m_pure = compute_o_metrics(traj_pure)
    r_pure = classify_segment(m_pure, pure_osc)
    print(f"  Pure 0.6Hz oscillation: H={m_pure['H']:.1f}, H_v3={m_pure['H_v3']:.2f} rad")
    print(f"  Label: {r_pure.label} (confidence: {r_pure.confidence})")
    print(f"  Reasoning: {r_pure.reasoning}")

    return output


if __name__ == "__main__":
    main()
