# Ô (O-Hat) Cross-Domain Classification Spectrum v2.0

**A substrate-independent structural measurement framework validated across 12+ domains.**

---

## Abstract

Ô is a three-number operator (curl, helicity, balance) that measures structural properties of any time series — regardless of what the numbers represent. It classifies dynamical systems into a spectrum determined by baseline background activity density, not outbreak intensity. After cross-domain validation across climate, epidemiology, seismology, space weather, meteorology, AI safety, and finance, we present the v2.0 classification spectrum with seven system types, the balance dual-role hypothesis, and a 3-6-9 catastrophe-theoretic foundation.

---

## 1. The Three Metrics

| Metric | Formula | What It Captures | Physical Meaning |
|--------|---------|-----------------|------------------|
| **curl** | Σ(Δx) | Signed gradient sum | Directional acceleration — is the system moving toward or away from equilibrium? |
| **helicity** | Σ(|Δx|) | Absolute gradient sum | Total structural complexity / variation in the outbreak window |
| **balance** | |skew_outbreak| / |skew_baseline| | Skewness ratio | Distance from equilibrium — how different is the outbreak from normal? |

**Key insight:** All three are substrate-independent. They work because skewness and gradients exist in any ordered sequence, regardless of domain semantics.

---

## 2. The Seven System Types (v2.0)

### 2.1 Primary Spectrum (Balance-Ratio Based)

| Balance Ratio | System Type | Characteristics | Verified Examples |
|:------------:|:------------|:----------------|:------------------|
| **> 20×** | **SUPER-PULSE** | Near-perfect Gaussian baseline + moderate outbreak. Requires extreme baseline purity. | 1989 Quebec geomagnetic storm (40.3×, baseline |skew|=0.018) |
| **5–15×** | **PULSE** | Sparse baseline (mostly zero/minimal events) → large contrast with burst | Earthquakes M5+ (9.2×) |
| **1.5–4×** | **CONTINUOUS FLOW** | Baseline has regular activity → moderate but significant contrast with outbreak | ENSO (2.2×), COVID-19 (2.5×), Typhoon storm intensity (2.6×) |
| **< 1.5×** | **REGIME SATURATION** | System too strongly forced by external periodic driver → outbreak is more regular than baseline | Typhoon seasons (0.4×), some river flood regimes |

### 2.2 Secondary Types (Structure-Based, H_v3 Sensitive)

These types require the expanded H_v3 metric (helicity of the outbreak window) in addition to balance ratio.

| Type | Signature | Mechanism | Verified Examples |
|:-----|:----------|:----------|:------------------|
| **VOLATILITY SHIFT (R_v)** | Balance < 1, helicity ↑ | Variance changes without mean shift | S&P 500 crash regimes |
| **COLLAPSE (Type X)** | H_v3 ↓ (structure destruction) | System loses internal organization during event | Geomagnetic storms (2003 Halloween Storm: H_v3=0.42× of baseline), microservice cascading failures |
| **PERTURBATION** | H_v3 ↑ (structure emergence) | Event introduces NEW structure not present in baseline | ICS cyberattacks (H_v3 increases), LLM jailbreak prompts, adversarial attacks |

### 2.3 Type X vs Perturbation — The Critical Distinction

The same balance ratio can mask two opposite dynamics:

```
Type X:       baseline structured → event chaotic    (H_v3 ↓)
Perturbation: baseline simple → event complex         (H_v3 ↑)
```

This distinction emerges naturally from the 3-6-9 cusp catastrophe framework (see §4).

---

## 3. Scale-Dependent Transitions

Some systems exhibit **different types at different scales** — Ô detects this as a feature, not a bug.

| System | Micro Scale | Macro Scale | Mechanism |
|--------|:----------:|:----------:|:----------|
| **Typhoons** | CONTINUOUS FLOW (2.6×, individual storm intensity) | REGIME SATURATION (0.4×, seasonal cycle) | External seasonal forcing dominates macro scale |
| **LLM Attention** | PERTURBATION (jailbreak prompts) | CONTINUOUS FLOW (normal use) | Attention pattern shift is local, not global |

**Implication:** Ô is a meta-metric that reveals scale-dependent structure. The "correct" classification depends on the scale you care about.

---

## 4. Theoretical Foundation: 3-6-9 Cusp Catastrophe

### 4.1 Σ(t) Formulation

The framework maps to a three-variable state vector:

```
Σ(t) = (x, ẋ, V)
```

Where:
- **x** = system state (curl maps to this)
- **ẋ** = rate of change (helicity maps to this)
- **V** = potential energy / stress (balance maps to this)

### 4.2 Cusp Catastrophe Geometry

The cusp catastrophe surface has three behavioral modes:
- **9** (stable equilibrium) — system on lower sheet
- **6** (bifurcation zone) — system approaching fold curve
- **3** (catastrophe jump) — system crosses fold, jumps to upper sheet

### 4.3 Directional Reversal (9 → 3 → 6)

A key prediction: after a catastrophe jump (State 3), the system does NOT return along the same path. It must traverse back (State 6) before restabilizing (State 9). This directionality is visible in the curl sign reversal between Type X and Perturbation events.

---

## 5. The Balance Dual-Role Hypothesis

Balance ratio serves two diagnostic functions simultaneously:

| Role | What It Measures | Example |
|:-----|:-----------------|:--------|
| **Outbreak Detector** | How different is the outbreak from baseline? | Brazil COVID: high outbreak skew → high balance |
| **Containment Dynamics** | Does the system return to equilibrium between events? | UK COVID: poor containment → elevated baseline skew → LOW balance despite severe outbreak |

**This was discovered during Brazil vs UK COVID-19 comparison** — two countries with similarly severe outbreaks showed different balance ratios because UK's poor containment elevated the baseline, making the outbreak appear "less unusual" structurally.

---

## 6. The Curl × Helicity 2×2 Matrix

Crossing curl (directional) with helicity (magnitude) yields four behavioral quadrants:

| | Low Helicity | High Helicity |
|:--|:------------|:--------------|
| **Positive Curl** | Gentle drift away from equilibrium | Accelerating structural divergence |
| **Negative Curl** | Gentle return toward equilibrium | Accelerating structural collapse |

This matrix was independently identified by DeepSeek's analysis of the Ô framework and confirmed by reanalysis of LLM attention-layer data.

---

## 7. Complete Domain Coverage

| # | Domain | System Type | Balance Ratio | Key Finding | Confidence |
|:--|:-------|:-----------|:-------------|:------------|:----------|
| 1 | **ENSO (climate)** | CONTINUOUS FLOW | ~2.2× | 92% of El Niño events detected; baseline activity from regular ENSO cycle | ✅ Verified |
| 2 | **COVID-19 (epidemiology)** | CONTINUOUS FLOW | ~2.5× (Brazil), varies by country | Balance reveals containment quality, not just outbreak severity | ✅ Verified |
| 3 | **Earthquakes M5+ (seismology)** | PULSE | 9.2× | Sparse inter-event baseline creates high contrast; window-size sensitive | ✅ Verified |
| 4 | **1989 Quebec Storm (space weather)** | SUPER-PULSE | 40.3× | Baseline |skew|=0.018 — near-perfect Gaussian drives extreme ratio | ✅ Verified |
| 5 | **2003 Halloween Storm (space weather)** | COLLAPSE (Type X) | N/A | H_v3=0.42× — structure destruction during event | ✅ Verified |
| 6 | **Typhoons — storm scale (meteorology)** | CONTINUOUS FLOW | 2.6× | Individual storm intensity follows same pattern as ENSO/COVID | ✅ Verified |
| 7 | **Typhoons — seasonal scale (meteorology)** | REGIME SATURATION | 0.4× | Seasonal forcing overwhelms anomaly signal at macro scale | ✅ Verified |
| 8 | **LLM Hidden States (AI safety)** | Mixed | Varies | Type X for geomagnetic-storm analogy; Perturbation for jailbreaks | ✅ Verified |
| 9 | **LLM Attention Layers (AI safety)** | Mixed | Varies | Curl best discriminator for JB vs LM; seq length is dominant confound | ✅ Verified |
| 10 | **ICS Cyberattacks (security)** | PERTURBATION | Varies | H_v3 ↑ — attack introduces structure not present in baseline | ✅ Verified |
| 11 | **S&P 500 (finance)** | VOLATILITY SHIFT | < 1 | Variance change without mean shift; balance < 1, helicity ↑ | ⚠️ Preliminary |
| 12 | **Microservice Failures (systems)** | COLLAPSE (Type X) | Varies | Cascading failure destroys internal structure | ⚠️ Preliminary |

### Untested Domains (Priority Queue)

| Domain | Expected Type | Rationale |
|--------|:------------:|:----------|
| Volcanic eruptions | PULSE | Sparse events, similar to earthquakes |
| River floods | Scale-dependent | Like typhoons — seasonal forcing at macro, pulse at event scale |
| Stellar light curves | Unknown | Potentially novel transient structure |
| Social media virality | PULSE or SUPER-PULSE | Sparse events with massive contrast |
| LLM perplexity under attack | PERTURBATION | Attention-layer findings suggest H_v3 ↑ |

---

## 8. Known Limitations

See `docs/known-limitations.md` for detailed analysis. Key failure modes:

1. **Crime rate data** — long-term secular trends collapse baseline/outbreak distinction
2. **Random walks** — no inherent structure to measure
3. **Multi-modal distributions** — skewness assumption breaks
4. **Very short series (< 50 points)** — auto-parameterization fails
5. **Heavily smoothed data** — gradient metrics suppressed
6. **Strong external periodic forcing** — Ô detects the clock, not the anomaly

---

## 9. The Cross-Domain ~2.2× Anomaly

**Observation:** Three domains converge on balance ratios near 2.2×:
- ENSO: 2.2×
- COVID-19 (Brazil): 2.5×
- Typhoon storm intensity: 2.6×

**Hypothesis:** ~2.2× represents a universal "baseline-active outbreak" ratio — systems where the background never goes to zero but outbreaks still produce detectable structural change.

**Falsification strategy:** Find a domain with continuous baseline activity AND a balance ratio outside the 1.5–4× range.

---

## 10. References

### Primary (Zenodo, peer-accessible)

| # | Title | DOI | Date |
|:--|:------|:----|:-----|
| 1 | A Simple Way to Measure El Niño | [10.5281/zenodo.21415286](https://doi.org/10.5281/zenodo.21415286) | 2026-07-17 |
| 2 | Ô Cross-Domain Synthesis Note | [10.5281/zenodo.21416188](https://doi.org/10.5281/zenodo.21416188) | 2026-07-17 |
| 3 | COVID-19 Cross-Domain Validation | [10.5281/zenodo.21416411](https://doi.org/10.5281/zenodo.21416411) | 2026-07-17 |
| 4 | H-Detector v0.4 — Cross-Domain Structural Detection | [10.5281/zenodo.21383080](https://doi.org/10.5281/zenodo.21383080) | 2026-07-15 |

### Software

| Resource | URL |
|:---------|:----|
| Ô (O-Hat) GitHub Repository | https://github.com/MMDR10/o-hat |
| Colab Demo Notebook | Included in `examples/o_hat_demo.ipynb` |

### Theoretical Foundation (External)

- Zeeman, E.C. (1976). "Catastrophe Theory." *Scientific American*, 234(4), 65-83.
- Gilmore, R. (1981). *Catastrophe Theory for Scientists and Engineers*. Wiley.

---

## Appendix A: Evidence-Level Notation

| Label | Meaning | Criterion |
|:------|:--------|:----------|
| ✅ **Verified** | High confidence | ≥ 2 independent sources, consistent conclusions |
| ⚠️ **Preliminary** | Medium confidence | Single-source or limited verification |
| ⬜ **Untested** | No confidence | No data yet |

---

*Authored by DR (tygtDc) and MKP. Cross-domain validation conducted June–July 2026.*
*Cite as: DR & MKP. "Ô Cross-Domain Classification Spectrum v2.0." Zenodo. 2026.*
