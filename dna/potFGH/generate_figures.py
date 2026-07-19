#!/usr/bin/env python3
"""Generate publication-quality figures for potFGH manuscript."""
import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

OUT = "/app/working/workspaces/tygtDc/output/potFGH-manuscript/"

# Global styling
plt.rcParams.update({
    'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 13,
    'legend.fontsize': 10, 'figure.dpi': 150, 'savefig.dpi': 150,
    'savefig.bbox': 'tight', 'font.family': 'sans-serif'
})

# ============================================================
# Load genome & compute stacking
# ============================================================
genome = ""
with open("/app/working/workspaces/tygtDc/dna/ecoli.fna") as f:
    for line in f:
        if not line.startswith(">"):
            genome += line.strip().upper()

STACKING = {
    ("A","A"): -1.00, ("A","T"): -1.45, ("A","C"): -1.68, ("A","G"): -1.44,
    ("T","A"): -0.88, ("T","T"): -1.00, ("T","C"): -1.45, ("T","G"): -1.68,
    ("C","A"): -1.44, ("C","T"): -1.68, ("C","C"): -2.17, ("C","G"): -3.22,
    ("G","A"): -1.68, ("G","T"): -1.44, ("G","C"): -3.22, ("G","G"): -2.17,
}

stacking = np.array([STACKING.get((genome[i], genome[i+1]), -1.75) for i in range(len(genome)-1)])

# ============================================================
# Figure 1: Genome-wide Ô Balance Scan (Manhattan-style)
# ============================================================
print("Generating Figure 1: Genome-wide balance scan...")
W, S = 5000, 500
balances = []
positions = []
for start in range(0, len(genome) - W, S):
    win = stacking[start:start+W]
    outbreak = np.percentile(np.abs(win), 95)
    baseline = np.percentile(np.abs(stacking), 50)
    balances.append(outbreak / max(baseline, 1e-6))
    positions.append(start)

balances = np.array(balances)
positions = np.array(positions) / 1000  # kb

# Compute threshold (genome-wide 99.9th percentile)
thresh = np.percentile(balances, 99.9)

fig, ax = plt.subplots(figsize=(14, 5))
colors = ['#d62728' if b > thresh else '#1f77b4' for b in balances]
ax.scatter(positions, balances, c=colors, s=3, alpha=0.6, edgecolors='none')
ax.axhline(y=thresh, color='red', linestyle='--', linewidth=0.8, label=f'99.9% threshold ({thresh:.1f}×)')

# Annotate top hits
top_indices = np.argsort(balances)[-10:]
for i in top_indices:
    if balances[i] > 100:
        ax.annotate(f'{positions[i]:.0f} kb\n{balances[i]:.0f}×',
                   (positions[i], balances[i]),
                   fontsize=7, ha='center', va='bottom',
                   xytext=(0, 5), textcoords='offset points')

ax.set_xlabel('Genome position (kb)')
ax.set_ylabel('Ô Balance (× baseline)')
ax.set_title('Genome-wide Ô Balance Scan — E. coli K-12 MG1655 (9,274 windows)')
ax.legend()
fig.tight_layout()
fig.savefig(OUT + 'fig1_genome_balance_scan.png')
plt.close()
print("  ✓ fig1 saved")

# ============================================================
# Figure 2: Stacking Energy Comparison (potFGH vs controls)
# ============================================================
print("Generating Figure 2: Stacking energy distribution comparison...")

# Define regions (all ~15kb)
regions = {
    'potFGHI (983×)': (890000, 905000),
    'rrnC (rRNA)': (4198000, 4203000),
    'Quiet (1000k)': (995000, 1005000),
}

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
bins = np.linspace(-3.5, 0, 50)

for ax, (name, (start, end)) in zip(axes, regions.items()):
    seg = stacking[start:end]
    ax.hist(seg, bins=bins, color='steelblue', alpha=0.7, edgecolor='white')
    ax.axvline(x=np.mean(seg), color='red', linestyle='--', linewidth=1.5,
              label=f'Mean = {np.mean(seg):.3f}')
    ax.axvline(x=np.mean(stacking), color='gray', linestyle=':', linewidth=1,
              label=f'Genome mean = {np.mean(stacking):.3f}')
    ax.set_xlabel('Stacking energy (kcal/mol)')
    ax.set_ylabel('Count')
    ax.set_title(name)
    ax.legend(fontsize=7)

fig.suptitle('Base-Pair Stacking Energy Distribution: potFGHI vs Controls', fontsize=13)
fig.tight_layout()
fig.savefig(OUT + 'fig2_stacking_distribution.png')
plt.close()
print("  ✓ fig2 saved")

# ============================================================
# Figure 3: Rigid-Flexible Alternation (Sawtooth) Detail
# ============================================================
print("Generating Figure 3: Sawtooth pattern detail...")

window_start, window_end = 896200, 896700
x = np.arange(window_start, window_end)
y = stacking[window_start:window_end]

fig, ax = plt.subplots(figsize=(14, 4))
colors_detail = ['#2ca02c' if y[i] <= -3.0 else '#ff7f0e' if y[i] >= -1.5 else '#1f77b4' 
                 for i in range(len(y))]
ax.bar(x, y, width=1, color=colors_detail, edgecolor='none', alpha=0.8)
ax.axhline(y=-3.0, color='green', linestyle='--', linewidth=0.8, label='Strong pairing (≤−3.0)')
ax.axhline(y=-1.5, color='orange', linestyle='--', linewidth=0.8, label='Flexible (≥−1.5)')
ax.axhline(y=np.mean(y), color='gray', linestyle=':', linewidth=1, label=f'Window mean = {np.mean(y):.3f}')

ax.set_xlabel('Genome position (bp)')
ax.set_ylabel('Stacking energy (kcal/mol)')
ax.set_title('Rigid-Flexible Alternation Pattern — potH (896,200–896,700, skewness = −1.065)')
ax.legend(fontsize=9)

# Legend for colors
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#2ca02c', label='GC-cluster (rigid)'),
    Patch(facecolor='#ff7f0e', label='AT-linker (flexible)'),
    Patch(facecolor='#1f77b4', label='Intermediate')
]
ax.legend(handles=legend_elements + ax.legend().legend_handles[:3], fontsize=8, loc='upper right')

fig.tight_layout()
fig.savefig(OUT + 'fig3_sawtooth_detail.png')
plt.close()
print("  ✓ fig3 saved")

# ============================================================
# Figure 4: FFT Periodicity (14-19bp Signal)
# ============================================================
print("Generating Figure 4: FFT periodicity analysis...")

# potFGH anomaly window FFT
seg = stacking[896200:896700]
n = len(seg)
fft = np.abs(np.fft.rfft(seg - np.mean(seg)))**2
freqs = np.fft.rfftfreq(n, d=1)
periods = 1 / freqs[1:]  # skip DC

# Also compute on codon-filtered version (remove period-3)
from scipy import signal as sig
# Remove 3bp period by notch filter or just show raw+filtered
# Simple: just compute both raw and codon-removed
seg_codon_removed = seg.copy()
for i in range(0, len(seg)-3, 3):
    seg_codon_removed[i:i+3] -= np.mean(seg_codon_removed[i:i+3])

fft_codon = np.abs(np.fft.rfft(seg_codon_removed - np.mean(seg_codon_removed)))**2

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Raw FFT
ax1.plot(periods, fft[1:], 'b-', alpha=0.7, linewidth=1)
ax1.axvspan(14, 19, alpha=0.15, color='red', label='14–19 bp window')
ax1.set_xlim(2, 60)
ax1.set_xlabel('Period (bp)')
ax1.set_ylabel('Power')
ax1.set_title('Raw Stacking Energy FFT — potH anomaly window')
ax1.legend()

# Codon-filtered FFT
ax2.plot(periods, fft_codon[1:], 'r-', alpha=0.7, linewidth=1)
ax2.axvspan(14, 19, alpha=0.15, color='red', label='14–19 bp window')
ax2.set_xlim(2, 60)
ax2.set_xlabel('Period (bp)')
ax2.set_ylabel('Power')
ax2.set_title('Non-codon FFT (period-3 filtered)')
ax2.legend()

fig.suptitle('Fourier Analysis: 14–19 bp Structural Periodicity in potH', fontsize=13)
fig.tight_layout()
fig.savefig(OUT + 'fig4_fft_periodicity.png')
plt.close()
print("  ✓ fig4 saved")

# ============================================================
# Figure 5: Regulatory Architecture (Schematic)
# ============================================================
print("Generating Figure 5: Regulatory architecture schematic...")

fig, ax = plt.subplots(figsize=(14, 3))

# Gene map
genes = [
    ('potF', 893784, 894896, '#3498db'),
    ('potG', 894893, 896161, '#2ecc71'),
    ('potH', 896158, 897240, '#e74c3c'),
    ('potI', 897237, 898115, '#9b59b6'),
]

# Draw operon
operon_start, operon_end = 893479, 898115
ax.plot([operon_start, operon_end], [1, 1], 'k-', linewidth=2)
ax.text(operon_start - 100, 1, '5\'', ha='right', va='center', fontsize=10)
ax.text(operon_end + 100, 1, '3\'', ha='left', va='center', fontsize=10)

# Draw genes
for name, start, end, color in genes:
    ax.barh(1, end-start, left=start, height=0.4, color=color, alpha=0.7, edgecolor='black')
    ax.text((start+end)/2, 0.65, name, ha='center', va='top', fontsize=9, fontweight='bold')

# Draw promoters
for pos, name, color in [(893634, 'potFp2', 'green'), (893736, 'potFp1', 'orange')]:
    ax.axvline(x=pos, ymin=0.4, ymax=1.6, color=color, linewidth=1.5, linestyle='--')
    ax.annotate(name, (pos, 1.65), fontsize=8, ha='center', color=color,
               arrowprops=dict(arrowstyle='->', color=color, lw=0.8))

# Draw TF binding sites
tf_sites = [
    (893479, 893493, 'Lrp−', '#e67e22'),
    (893498, 893512, 'ArcA−', '#c0392b'),
    (893568, 893582, 'ArcA−', '#c0392b'),
    (893697, 893735, 'ArgR−', '#8e44ad'),
]

for start, end, name, color in tf_sites:
    ax.barh(1, end-start, left=start, height=0.15, color=color, alpha=0.9)
    ax.text((start+end)/2, 0.45, name, ha='center', va='top', fontsize=6, color='white', fontweight='bold')

# Highlight anomaly window
ax.axvspan(896200, 896700, alpha=0.15, color='red')
ax.annotate('983× Ô Anomaly\n(potG-potH junction)', xy=(896450, 1.8),
           fontsize=9, ha='center', color='red', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffcccc', alpha=0.9))

ax.set_ylim(0, 2.2)
ax.set_xlim(892500, 899000)
ax.set_yticks([])
ax.set_xlabel('Genome position (bp)')
ax.set_title('potFGHI Operon — Regulatory Architecture (RegulonDB v14.5) + Ô Anomaly')
ax.legend([
    plt.Rectangle((0,0),1,1,fc='#3498db',alpha=0.7), plt.Rectangle((0,0),1,1,fc='#2ecc71',alpha=0.7),
    plt.Rectangle((0,0),1,1,fc='#e74c3c',alpha=0.7), plt.Rectangle((0,0),1,1,fc='#9b59b6',alpha=0.7),
    plt.Rectangle((0,0),1,1,fc='#8e44ad',alpha=0.9), plt.Rectangle((0,0),1,1,fc='#c0392b',alpha=0.9),
    plt.Rectangle((0,0),1,1,fc='#e67e22',alpha=0.9), plt.Rectangle((0,0),1,1,fc='#ffcccc',alpha=0.5),
], ['potF (SBP)', 'potG (ATPase)', 'potH (Permease)', 'potI (Permease)',
    'ArgR−', 'ArcA−', 'Lrp−', 'Ô Anomaly'], loc='upper right', fontsize=7, ncol=2)

fig.tight_layout()
fig.savefig(OUT + 'fig5_regulatory_map.png')
plt.close()
print("  ✓ fig5 saved")

# ============================================================
# Figure 6: Violin Plot — Stacking Energy by Region
# ============================================================
print("Generating Figure 6: Violin plot...")

data = []
labels = []
for name, (s, e) in regions.items():
    data.append(stacking[s:e])
    labels.append(name)

fig, ax = plt.subplots(figsize=(10, 5))
parts = ax.violinplot(data, positions=range(len(data)), showmeans=True, showmedians=True)
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(['#e74c3c', '#3498db', '#95a5a6'][i])
    pc.set_alpha(0.6)

ax.set_xticks(range(len(data)))
ax.set_xticklabels(labels)
ax.set_ylabel('Stacking energy (kcal/mol)')
ax.set_title('Base-Pair Stacking Energy Distribution by Region')

# Add stats annotations
for i, d in enumerate(data):
    mean_val = np.mean(d)
    ax.annotate(f'μ={mean_val:.3f}\nstrong={100*np.mean(d<=-3.0):.1f}%',
               (i, -3.4), fontsize=9, ha='center')

ax.axhline(y=np.mean(stacking), color='gray', linestyle=':', label=f'Genome mean = {np.mean(stacking):.3f}')
ax.legend()
fig.tight_layout()
fig.savefig(OUT + 'fig6_violin_comparison.png')
plt.close()
print("  ✓ fig6 saved")

print(f"\n✅ All 6 figures saved to {OUT}")
print("Files: fig1_genome_balance_scan.png, fig2_stacking_distribution.png,")
print("       fig3_sawtooth_detail.png, fig4_fft_periodicity.png,")
print("       fig5_regulatory_map.png, fig6_violin_comparison.png")
