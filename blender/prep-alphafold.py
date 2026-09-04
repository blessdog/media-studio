#!/usr/bin/env python3
"""Drop the low-confidence parts of an AlphaFold model before rendering it.

AlphaFold writes per-residue confidence (pLDDT, 0-100) into the B-factor column.
Regions below 70 are not predictions of a shape -- they are the model saying it
does not know, and they come out as long sprawling loops. Rendering them puts
confident-looking protein on screen where there is no information, which is the
same error class as rendering a crystallography scaffold.

Threshold 70 is EBI/DeepMind's own published band edge between "confident" and
"low": >=90 very high, 70-90 confident, 50-70 low, <50 very low / likely
disordered. CHOSEN from that published banding, not tuned.

    python3 prep-alphafold.py ac5_af.pdb 70
"""
import sys

src = sys.argv[1] if len(sys.argv) > 1 else "ac5_af.pdb"
cut = float(sys.argv[2]) if len(sys.argv) > 2 else 70.0
dst = src.replace(".pdb", "_confident.pdb")

keep = drop = 0
with open(dst, "w") as out:
    for line in open(src):
        if line[:6] in ("ATOM  ", "HETATM"):
            if float(line[60:66]) < cut:
                drop += 1
                continue
            keep += 1
            out.write(line)
        elif line[:3] in ("TER", "END"):
            out.write(line)
print(f"{src} -> {dst}: kept {keep} atoms, dropped {drop} below pLDDT {cut:g}")
