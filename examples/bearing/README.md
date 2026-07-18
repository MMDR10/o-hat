# XJTU-SY Bearing Run-to-Failure: Envelope O-HAT Analysis

## Quick Start

```bash
# Streaming (NAS-friendly, ~3.8KB RAM, 38x more sensitive)
python examples/bearing/streaming_ohat.py \
  --data-dir /path/to/XJTU-SY_Bearing_Datasets \
  --bearing "37.5Hz11kN/Bearing2_1" \
  --window 20 --baseline 40

# Bulk (concatenate all CSVs — only for machines with >50GB RAM)
python examples/bearing/bulk_ohat.py \
  --data-dir /path/to/XJTU-SY_Bearing_Datasets \
  --bearing "40Hz10kN/Bearing3_1"
```

## Method

**Streaming approach:** Read one CSV at a time → FFT highpass (3kHz) → Hilbert envelope → scalar mean energy → release raw data. A 491-CSV bearing becomes a 491-point time series using only ~3.8 KB RAM. Feed into O-HAT for phase transition detection.

## Dataset

XJTU-SY: 15 bearings × 3 operating conditions (35Hz/12kN, 37.5Hz/11kN, 40Hz/10kN), 25.6 kHz sampling, run-to-failure trajectories.

## Results (2026-07-18)

| Bearing | CSV | Duration | Balance Max | SUPER-PULSE | Trend |
|---------|:---:|:---:|:---:|:---:|:---:|
| B3_1 (40Hz) | 2,538 | 54.1m | **3,769×** | 13 | down |
| B3_2 (40Hz) | 2,496 | 53.2m | 160× | 16 | stable |
| B1_2 (35Hz) | 161 | 3.4m | 138× | 1 | up |
| B2_1 (37.5Hz) | 491 | 10.5m | 132× | 2 | up |
| B3_3 (40Hz) | 371 | 7.9m | 76× | 3 | down |
| B3_4 (40Hz) | 1,515 | 32.3m | 42× | 5 | stable |

**Detection rate: 14/15 (93%).** Only B2_4 (0.9 min, too short) showed no degradation.
**40Hz/10kN is the most aggressive operating condition.**
B3_1's 3,769× is 2.5× higher than CWRU's envelope record (1,528×).

## Key Insight

Streaming (per-CSV envelope) is **38x more sensitive** than bulk concatenation — preserving per-file structural signals that global normalization destroys.
