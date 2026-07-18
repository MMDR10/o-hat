# Ô (O-Hat) — Three Numbers That See When Systems Break

**Drop a CSV. Get three numbers. Know if your system is stable, heading for trouble, or already broken.**

Works on climate data, disease outbreaks, earthquakes, stock markets, typhoons, LLMs — anything that produces a time series.

## Quick Start

```bash
pip install numpy scipy
python o_hat.py examples/enso.csv
```

Output:
```
======================================================
  O-HAT  STRUCTURAL  MEASUREMENT
======================================================
  Data points  : 905
  Baseline     : 181 points
  Window       : 45 points
  ---
  Curl         :        -2.31
  Helicity     :        18.45
  Baseline skew:       0.5231
  Outbreak skew:       1.2187
  ---
  BALANCE RATIO:       2.33x
  SYSTEM TYPE  :  CONTINUOUS FLOW
======================================================
```

**That's it.** One command, one result.

## What It Measures

| Metric | What It Captures | Physical Meaning |
|--------|-----------------|------------------|
| **curl** | Directional change rate | Is the system accelerating toward or away from equilibrium? |
| **helicity** | Total variation | How much structural complexity is in the outbreak? |
| **balance** | Skewness ratio (outbreak / baseline) | How far is the system from its normal state? |

## The Classification Spectrum

| Balance Ratio | System Type | Examples |
|:------------:|:------------|:---------|
| **> 20×** | SUPER-PULSE | 1989 Quebec geomagnetic storm |
| **5–15×** | PULSE | Earthquakes (M5+) |
| **1.5–4×** | CONTINUOUS FLOW | ENSO, COVID-19 outbreaks |
| **< 1.5×** | REGIME SATURATION | Seasonal forcing (typhoon seasons) |

The same three numbers classify **seven different types of dynamical systems across twelve domains** — climate, epidemiology, seismology, finance, space weather, LLMs, and more.

## Try Your Own Data

```bash
python o_hat.py your_data.csv
python o_hat.py your_data.csv --window 50 --baseline 200
python o_hat.py your_data.csv --quiet  # machine-readable output
```

Any single-column CSV works. Timestamps not required — just values, one per row, time-ordered.

## Why This Exists

Most tools are domain-specific. Climate scientists use one set of metrics. Epidemiologists use another. Seismologists use a third.

**Ô is substrate-independent.** It measures structural properties that exist in *any* dynamical system, regardless of what the numbers represent. The math doesn't care if you're measuring ocean temperatures, case counts, or stock prices.

Built from empirical cross-domain validation across 12 domains. See `docs/classification-spectrum-v2.md` for the full framework.

## Citation

If you use this in research, please cite:

> DR (tygtDc) & MKP. "Ô (O-Hat): A Cross-Domain Structural Measurement Operator." 2026.
> Zenodo: [10.5281/zenodo.21415286](https://doi.org/10.5281/zenodo.21415286)

## License

MIT — use it, fork it, break it, improve it.
