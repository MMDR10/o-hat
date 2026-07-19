# potFGH Manuscript — Complete Package

## A multi-dimensional structural anomaly at the potG-potH junction in E. coli revealed by the Ô framework

**Authors:** DR (Deep Research Agent, QwenPaw Multi-Agent System), with strategic guidance from MKP and DeepSeek  
**Date:** 2026-07-19  
**License:** CC-BY 4.0  
**Status:** Preprint (Zenodo DOI pending)

---

## Contents

### Manuscript
- `manuscript.md` — Complete manuscript (Markdown, bioRxiv-formatted)
  - Abstract, Introduction, Results (4 sections), ChIP-seq Validation, Discussion, Methods, References (23 citations), Evidence Grade Checklist

### Figures
- `fig1_genome_balance_scan.png` — Genome-wide Ô balance scan (Manhattan plot, 9,274 windows)
- `fig2_stacking_distribution.png` — Stacking energy histograms: potFGHI vs rrnC vs Quiet control
- `fig3_sawtooth_detail.png` — Rigid-Flexible alternation pattern at single-nucleotide resolution
- `fig4_fft_periodicity.png` — Fourier analysis showing 14–19 bp structural periodicity
- `fig5_regulatory_map.png` — potFGHI regulatory architecture from RegulonDB v14.5, with Ô anomaly overlay
- `fig6_violin_comparison.png` — Violin plot comparing stacking energy distributions across regions

### Analysis Code
- `generate_figures.py` — Reproducible figure generation script
- `deepdive_phase4_genomewide.py` — Full genome-wide scan and periodicity analysis
- `o_hat_dna.py` — Ô-HAT DNA encoding and scanning pipeline
- `analyze_dna.py` — Deep-dive stacking energy analysis
- `crossref_dna_v2.py` — RegulonDB/EcoCyc cross-reference script

### Data
- `ecoli_o_hat_results.json` — Ô scan results for 9,274 windows

### Dependencies
- `ecoli.fna` — E. coli K-12 MG1655 genome (FASTA, NC_000913.3)

---

## Quick Start

```bash
# Generate all figures
python3 generate_figures.py

# Run full genome scan
python3 deepdive_phase4_genomewide.py

# Deep-dive on any region
python3 analyze_dna.py
```

## Key Findings

1. **983× Ô balance anomaly** at potFGHI operon — 4–7.5× excess over rRNA operons
2. **Mean stacking energy (−1.833 kcal/mol)** exceeds rRNA (−1.752), with 17.9% strong-pairing positions
3. **Rigid-Flexible Alternation Pattern** — 500 bp sawtooth of GC-clusters and AT-linkers
4. **14–19 bp structural periodicity** — non-codon FFT signal (P = 0.93 among genome windows)
5. **Canonical multi-TF regulatory hub** at promoter (ArgR, ArcA, Lrp, NtrC) — zero intragenic binding
6. **Anomaly co-localizes with potG-potH junction** — protein domain boundary + transcriptional polarity site

## Citation

DR, MKP, DeepSeek. "A multi-dimensional structural anomaly at the potG-potH junction in E. coli revealed by the Ô framework." Zenodo preprint, 2026. DOI: pending.
