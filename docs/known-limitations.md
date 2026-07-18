# Known Limitations & Edge Cases

Ô is not a universal tool. It works remarkably well across many domains, but there
are clear cases where it fails or gives unreliable results. Being honest about
these limits makes the framework more trustworthy.

## ❌ Known Failure Cases

### 1. Crime Rate Data
- **Why it fails:** Crime rates often exhibit **long-term secular trends** (declining over decades) with sporadic noise. The baseline/outbreak distinction collapses — there is no clear "normal" state to compare against.
- **What happens:** Balance ratio tends to 1.0 or lower, classifying everything as REGIME SATURATION, even when there are genuine spikes.
- **Diagnosis:** If your data has a strong monotonic trend (e.g., always going down), Ô will not be informative. Detrend first.

### 2. Random Walk / Brownian Motion
- **Why it fails:** Random walks have no inherent structure — every window is statistically equivalent. The "outbreak" is just the latest fluctuation.
- **What happens:** Balance ratios near 1.0. Helicity scales with window size, not with any genuine outbreak. Results are meaningless.

### 3. Multi-modal Distributions
- **Why it fails:** Ô uses skewness, which assumes unimodal distribution. If your data has two stable states (bimodal), the skewness calculation can be misleading.
- **Example:** Stock markets alternating between bull/bear regimes.
- **Workaround:** Segment by regime first, then apply Ô to each segment.

## ⚠️ Partial / Conditional Cases

### 4. Very Short Time Series (< 50 points)
- **Issue:** Window and baseline auto-sizing breaks down. Skewness estimates are unreliable.
- **Workaround:** Manually set `--window` and `--baseline`. Interpret results with caution.

### 5. Heavily Smoothed Data
- **Issue:** If your data has already been through a moving average or low-pass filter, gradient-based metrics (curl, helicity) will be artificially suppressed.
- **Diagnosis:** Check helicity. If it's suspiciously close to zero despite visible variation, your data may be over-smoothed.

### 6. Domain with External Periodic Forcing
- **Issue:** If your system has a strong external clock (e.g., daily commute patterns, annual retail cycles), Ô will pick up the forcing, not the anomaly.
- **Found in:** Typhoon seasons (classified as REGIME SATURATION at macro scale, but CONTINUOUS FLOW at storm-level scale).
- **This is actually a feature** — it reveals scale-dependent structure. But it means you need to know what scale you care about.

## 🧪 Cases We Haven't Tested Yet

| Domain | Status | Expected Behavior |
|--------|:------:|:------------------|
| Volcanic eruptions | ⬜ Untested | May behave like earthquakes (PULSE) |
| River floods | ⬜ Untested | May show scale-dependent forcing like typhoons |
| Stellar light curves | ⬜ Untested | Unknown — potentially interesting transient structure |
| Social media virality | ⬜ Untested | May be PULSE or SUPER-PULSE |
| LLM perplexity under attack | ⬜ Untested | Shows PERTURBATION (H_v3 ↑) in attention-layer tests |

## 🔑 The Golden Rule

**Ô tells you IF something structurally unusual happened. It does NOT tell you WHY.**

If you get a high balance ratio, it means: "Look at this window — something changed." The interpretation (earthquake? market crash? sensor failure?) is still your job.

---

*Last updated: 2026-07-18. If you find a new failure case, please open an issue at https://github.com/MMDR10/o-hat*
