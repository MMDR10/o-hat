#!/usr/bin/env python3
"""
O-Hat DNA Analysis — E. coli K-12 MG1655
Convert A/C/G/T to numerical values, sliding-window O-Hat scan,
detect structural anomalies in genome sequence.
"""
import sys, os, json
import numpy as np
from pathlib import Path

# Add o_hat to path
sys.path.insert(0, "/app/working/workspaces/tygtDc")
from o_hat.o_hat import measure as o_hat

# ============================================================
# Step 1: Load genome
# ============================================================
def load_fasta(path):
    """Load FASTA, return single concatenated sequence (uppercase, no gaps)."""
    seq = []
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                continue
            seq.append(line.strip().upper())
    return "".join(seq)

print("Loading genome...")
genome = load_fasta("/app/working/workspaces/tygtDc/dna/ecoli.fna")
print(f"  Genome length: {len(genome):,} bp")

# ============================================================
# Step 2: Base → numerical encoding
# ============================================================
# Multiple encoding schemes for cross-validation
ENCODINGS = {
    "stacking_energy": {"A": 1.0, "T": 1.0, "C": 2.5, "G": 3.0},  # G/C stack stronger
    "hydrogen_bonds": {"A": 2.0, "T": 2.0, "C": 3.0, "G": 3.0},     # AT=2, GC=3 bonds
    "purine_pyrimidine": {"A": 1.0, "G": 1.0, "C": -1.0, "T": -1.0}, # purine=+1, pyrimidine=-1
    "molecular_weight": {"A": 135.13, "T": 126.11, "C": 111.10, "G": 151.13},
    "gc_binary": {"A": 0, "T": 0, "C": 1, "G": 1},
}

def encode_sequence(seq, scheme):
    """Convert nucleotide string to numerical array."""
    mapping = ENCODINGS[scheme]
    result = np.zeros(len(seq))
    for i, base in enumerate(seq):
        result[i] = mapping.get(base, 0.0)  # N/other → 0
    return result

# ============================================================
# Step 3: Sliding-window O-Hat scan
# ============================================================
WINDOW_SIZE = 5000      # 5kb windows — enough for statistical stability
STEP_SIZE = 1000        # 1kb step — fine-grained scan
# For 4.6M bp genome: ~4,600 windows

def sliding_o_hat(data, window, step):
    """Sliding window O-Hat scan. Returns list of dicts with O-Hat metrics."""
    results = []
    n = len(data)
    for start in range(0, n - window + 1, step):
        chunk = data[start:start + window]
        try:
            r = o_hat(chunk)
            results.append({
                "pos": start,
                "end": start + window,
                "curl": float(r["curl"]),
                "helicity": float(r["helicity"]),
                "balance_ratio": float(r["balance_ratio"]),
                "system_type": r["system_type"],
                "extreme_index": int(r["extreme_index"]),
            })
        except Exception as e:
            results.append({
                "pos": start, "end": start + window,
                "curl": None, "helicity": None, "balance_ratio": None,
                "system_type": None, "error": str(e)
            })
    return results

# ============================================================
# Step 4: Run all encodings
# ============================================================
all_results = {}
for scheme_name in ENCODINGS:
    print(f"\nEncoding: {scheme_name}")
    data = encode_sequence(genome, scheme_name)
    results = sliding_o_hat(data, WINDOW_SIZE, STEP_SIZE)
    all_results[scheme_name] = results
    
    # Quick stats
    valid = [r for r in results if r["curl"] is not None]
    if valid:
        curls = [r["curl"] for r in valid]
        helicities = [r["helicity"] for r in valid]
        balances = [r["balance_ratio"] for r in valid]
        types = [r["system_type"] for r in valid]
        print(f"  Windows: {len(valid)} valid / {len(results)} total")
        print(f"  Curl:     {np.mean(curls):.4f} ± {np.std(curls):.4f}")
        print(f"  Helicity: {np.mean(helicities):.1f} ± {np.std(helicities):.1f}")
        print(f"  Balance:  {np.mean(balances):.2f} ± {np.std(balances):.2f}")
        
        # Type distribution
        from collections import Counter
        type_counts = Counter(types)
        print(f"  Types: {dict(type_counts)}")
        
        # Top anomalies
        bal_top = sorted(valid, key=lambda r: abs(r["balance_ratio"]), reverse=True)[:5]
        curl_top = sorted(valid, key=lambda r: abs(r["curl"]), reverse=True)[:5]
        print(f"  Top balance anomalies:")
        for r in bal_top:
            print(f"    pos={r['pos']:,}-{r['end']:,}  balance={r['balance_ratio']:.2f}  type={r['system_type']}")
        print(f"  Top curl anomalies:")
        for r in curl_top:
            print(f"    pos={r['pos']:,}-{r['end']:,}  curl={r['curl']:.4f}  type={r['system_type']}")

# ============================================================
# Step 5: Save results
# ============================================================
output_path = "/app/working/workspaces/tygtDc/dna/ecoli_o_hat_results.json"
with open(output_path, "w") as f:
    json.dump({
        "genome": "E. coli K-12 MG1655 (NC_000913.3)",
        "length_bp": len(genome),
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "encodings": list(ENCODINGS.keys()),
        "results": all_results,
    }, f, indent=2)
print(f"\nSaved: {output_path}")
