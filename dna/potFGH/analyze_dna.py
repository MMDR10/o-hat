#!/usr/bin/env python3
"""Detailed analysis of E. coli O-Hat results."""
import json, numpy as np
from collections import Counter

with open("/app/working/workspaces/tygtDc/dna/ecoli_o_hat_results.json") as f:
    data = json.load(f)

se = data["results"]["stacking_energy"]
valid = [r for r in se if r["curl"] is not None]
total = len(valid)

print("=" * 60)
print("E. coli K-12 MG1655 — O-HAT Structural Analysis")
print("=" * 60)

# Type distribution
types = Counter(r["system_type"] for r in valid)
print(f"\nClassification Spectrum ({total:,} windows of 5kb):")
for t in ["SUPER-PULSE", "PULSE", "CONTINUOUS FLOW", "REGIME SATURATION / NOISE"]:
    count = types.get(t, 0)
    pct = count / total * 100
    bar = "#" * int(pct)
    print(f"  {t:32s}: {count:5d} ({pct:5.1f}%) {bar}")

# Helicity by type
print(f"\nHelicity by Type:")
for t in ["SUPER-PULSE", "PULSE", "CONTINUOUS FLOW", "REGIME SATURATION / NOISE"]:
    h_vals = [r["helicity"] for r in valid if r["system_type"] == t]
    if h_vals:
        print(f"  {t:32s}: mean={np.mean(h_vals):.1f}  std={np.std(h_vals):.1f}")

# Balance ratio by type
print(f"\nBalance Ratio by Type:")
for t in ["SUPER-PULSE", "PULSE", "CONTINUOUS FLOW", "REGIME SATURATION / NOISE"]:
    b_vals = [r["balance_ratio"] for r in valid if r["system_type"] == t]
    if b_vals:
        print(f"  {t:32s}: mean={np.mean(b_vals):.1f}  std={np.std(b_vals):.1f}  max={np.max(b_vals):.1f}")

# Top 20 SUPER-PULSE regions
sp = sorted([r for r in valid if r["system_type"] == "SUPER-PULSE"],
            key=lambda r: r["balance_ratio"], reverse=True)
print(f"\nTop 20 SUPER-PULSE Regions:")
print(f"  {'Position (kb)':>16s}  {'Balance':>10s}  {'Helicity':>8s}")
for r in sp[:20]:
    print(f"  {r['pos']/1000:7.1f} - {r['end']/1000:7.1f}  {r['balance_ratio']:10.1f}  {r['helicity']:8.1f}")

# Anomaly hotspots (100kb bins)
print(f"\nSUPER-PULSE hotspots (100kb bins):")
bin_size = 100000
n_bins = 4641652 // bin_size + 1
hotspots = []
for i in range(n_bins):
    start = i * bin_size
    end = start + bin_size
    bin_windows = [r for r in valid if start <= r["pos"] < end]
    if bin_windows:
        sp_count = sum(1 for r in bin_windows if r["system_type"] == "SUPER-PULSE")
        if sp_count >= 2:  # at least 2 SP windows in 100kb
            hotspots.append((start, sp_count, len(bin_windows)))

hotspots.sort(key=lambda x: x[1], reverse=True)
for pos, sp, total_w in hotspots[:10]:
    print(f"  {pos/1000:6.0f}-{pos/1000+100:6.0f}kb: {sp}x SUPER-PULSE / {total_w} windows")
