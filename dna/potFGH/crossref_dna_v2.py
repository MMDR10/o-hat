#!/usr/bin/env python3
"""Cross-reference O-Hat SUPER-PULSE regions with E. coli gene annotations — fixed parser."""
import json, re, numpy as np
from collections import Counter, defaultdict

# ============================================================
# Step 1: Parse GenBank features (fixed)
# ============================================================
def parse_genbank(path):
    with open(path) as f:
        text = f.read()
    
    m = re.search(r'FEATURES\s+Location/Qualifiers\n', text)
    if not m:
        print("ERROR: no FEATURES")
        return []
    
    start = m.end()
    m2 = re.search(r'\nORIGIN', text[start:])
    end = start + m2.start() if m2 else len(text)
    lines = text[start:end].split('\n')
    
    features = []
    current = None
    
    for line in lines:
        line = line.rstrip()
        if not line.strip():
            continue
        
        # Feature header: starts with exactly 5 spaces, then type, then location
        if line.startswith('     ') and not line.startswith('      '):
            # Save previous
            if current and current.get("start"):
                features.append(current)
            
            parts = line[5:].strip()
            # Split type from location
            type_match = re.match(r'(\S+)\s+(.+)', parts)
            if type_match:
                current = {
                    "type": type_match.group(1),
                    "location": type_match.group(2).strip(),
                    "gene": "", "product": "", "locus_tag": ""
                }
                # Parse location immediately
                nums = [int(n) for n in re.findall(r'(\d+)', current["location"])]
                if nums:
                    current["start"] = min(nums)
                    current["end"] = max(nums)
            else:
                current = None
        elif current and '/' in line:
            # Qualifier
            qual = line.strip()
            if qual.startswith('/gene='):
                current["gene"] = qual.split('=', 1)[1].strip('"')
            elif qual.startswith('/product='):
                current["product"] = qual.split('=', 1)[1].strip('"')
            elif qual.startswith('/locus_tag='):
                current["locus_tag"] = qual.split('=', 1)[1].strip('"')
    
    if current and current.get("start"):
        features.append(current)
    
    return features

print("Parsing GenBank...")
features = parse_genbank("/app/working/workspaces/tygtDc/dna/ecoli_full.gb")
print(f"  Parsed features: {len(features):,}")

# Type distribution
feat_types = Counter(f["type"] for f in features)
for t, c in feat_types.most_common(10):
    print(f"  {t}: {c:,}")

# ============================================================
# Step 2: Load O-Hat results
# ============================================================
with open("/app/working/workspaces/tygtDc/dna/ecoli_o_hat_results.json") as f:
    data = json.load(f)
se = data["results"]["stacking_energy"]
valid = [r for r in se if r["curl"] is not None]

# ============================================================
# Step 3: Cross-reference Top SUPER-PULSE
# ============================================================
sp = sorted([r for r in valid if r["system_type"] == "SUPER-PULSE"],
            key=lambda r: r["balance_ratio"], reverse=True)

print(f"\n{'='*80}")
print(f"Top 25 SUPER-PULSE Regions — Cross-Referenced with Gene Annotations")
print(f"{'='*80}")
print(f"{'Position (kb)':>16s}  {'Balance':>8s}  {'Biological Features'}")

for r in sp[:25]:
    start = r["pos"]
    end = r["end"]
    # Find overlapping features
    ov = [f for f in features if f.get("start") and f.get("end")
          and f["end"] >= start and f["start"] <= end]
    
    # Categorize
    rrnas = [f for f in ov if f["type"] == "rRNA"]
    trnas = [f for f in ov if f["type"] == "tRNA"]
    genes = [f for f in ov if f["type"] in ("gene", "CDS") and f["gene"]]
    pseudos = [f for f in ov if f["type"] == "gene" and "pseudo" in f.get("product", "").lower()]
    
    parts = []
    if rrnas:
        rnames = [f["gene"] or f["locus_tag"] for f in rrnas[:3]]
        parts.append(f"🔴 rRNA: {', '.join(rnames)}")
    if trnas:
        tnames = [f["gene"] or f["locus_tag"] for f in trnas[:3]]
        parts.append(f"🟡 tRNA: {', '.join(tnames)}")
    if pseudos:
        parts.append(f"⚪ pseudogene(s)")
    if genes:
        gnames = [f["gene"] for f in genes[:5]]
        parts.append(f"genes: {', '.join(gnames)}")
    if not parts:
        intergenic = len(ov) == 0
        parts.append("⬜ INTERGENIC" if intergenic else f"CDS ({len(ov)} unnamed)")
    
    desc = " | ".join(parts)
    kb = start / 1000
    print(f"  {kb:6.0f}-{end/1000:6.0f} kb  {r['balance_ratio']:8.1f}  {desc}")

# ============================================================
# Step 4: Hotspot feature composition
# ============================================================
print(f"\n{'='*80}")
print(f"HOTSPOT Feature Composition (100kb bins)")
print(f"{'='*80}")

bin_size = 100000
hotspots = defaultdict(list)
for r in sp:
    hotspots[r["pos"] // bin_size].append(r)

for idx in sorted(hotspots.keys(), key=lambda i: len(hotspots[i]), reverse=True)[:10]:
    sp_list = hotspots[idx]
    start = idx * bin_size
    end = start + bin_size
    
    ov = [f for f in features if f.get("start") and f.get("end")
          and f["end"] >= start and f["start"] <= end]
    
    rrnas = [f for f in ov if f["type"] == "rRNA"]
    trnas = [f for f in ov if f["type"] == "tRNA"]
    genes = [f for f in ov if f["type"] in ("gene", "CDS") and f["gene"]]
    
    balances = [r["balance_ratio"] for r in sp_list]
    
    print(f"\n  {start/1000:.0f}-{end/1000:.0f} kb: {len(sp_list)}x SUPER-PULSE (bal {min(balances):.0f}-{max(balances):.0f})")
    if rrnas:
        print(f"    rRNA: {', '.join(f['gene'] or f['locus_tag'] for f in rrnas)}")
    if trnas:
        print(f"    tRNA: {', '.join(f['gene'] or f['locus_tag'] for f in trnas[:5])}")
    if genes:
        print(f"    Notable: {', '.join(f['gene'] for f in genes[:8])}")
    
    # Also show what types are in this bin
    bin_types = Counter(f["type"] for f in ov)
    print(f"    All features: {dict(bin_types.most_common(5))}")
