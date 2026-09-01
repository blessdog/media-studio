#!/usr/bin/env python3
"""Strip OPM's DUM pseudo-atoms so biotite (via Molecular Nodes) can read the file.

OPM appends rows of DUM "atoms" marking the two hydrophobic boundary planes.
They are not chemistry and biotite rejects the file because of them
('' cannot be parsed into a number). Their ONLY payload is the membrane
half-thickness, which is already recorded as a measured constant in
blender/lib_complex.py (MEMBRANE_HALF_THICKNESS = 15.7 A, identical in both
5MZP and 6VMS). Nothing is lost by dropping them here.

    python3 prep-opm.py            # rewrites *_opm.pdb -> *_opm_clean.pdb
"""
import pathlib
import re

for src in sorted(pathlib.Path(".").glob("*_opm.pdb")):
    dst = src.with_name(src.stem + "_clean.pdb")
    kept = dropped = 0
    planes = set()
    with open(dst, "w") as out:
        for line in open(src):
            if line[:6] in ("ATOM  ", "HETATM"):
                if line[17:20].strip() == "DUM":
                    dropped += 1
                    planes.add(round(float(line[46:54]), 1))
                    continue
                kept += 1
                out.write(line)
            elif line[:3] in ("TER", "END"):
                out.write(line)
    print(f"{src.name} -> {dst.name}: kept {kept}, dropped {dropped} DUM "
          f"(planes z = {sorted(planes)})")
