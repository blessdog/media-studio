"""The A2AR-D2R heterotetramer / AC5 complex: this job's structural spec.

JOB LAYER. Everything here is specific to the caffeine explainer -- which
receptors, which helices, which arrangement, which crystallography scaffolds to
hide. The general algorithms it calls live in blender/lib_membrane.py and know
nothing about any of this.

THE MODEL BEING BUILT (Ferre et al. 2018, Front. Pharmacol. 9:243):
    A2A(ext) --TM6/TM6-- A2A(int) --TM4/TM5-- D2(int) --TM6/TM6-- D2(ext)
Two internal interacting protomers flanked by two external non-interacting
ones; G proteins engage the EXTERNAL protomers only; the whole thing is
pre-coupled to adenylyl cyclase 5.

There is NO experimental structure of this tetramer. The interfaces were mapped
with TM-interfering peptides, not crystallography. What IS experimental is each
protomer, its membrane orientation and its TM helix ranges -- so this is an
honest composition of measured parts under a published model, and every number
it uses is printed rather than hidden.

    python3 jobs/caffeine/complex.py        # solve and print the geometry
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "blender"))
import lib_membrane as mb                                        # noqa: E402

ANGSTROM = mb.ANGSTROM
STRUCTURES = str(Path(__file__).resolve().parent / "structures")

# UniProt transmembrane annotations, fetched 2026-09-01.
# P29274 adenosine receptor A2a / P14416 D(2) dopamine receptor.
TM = {
    "A2A": {1: (8, 32), 2: (43, 66), 3: (78, 100), 4: (121, 143),
            5: (174, 198), 6: (235, 258), 7: (267, 290)},
    "D2":  {1: (38, 60), 2: (71, 93), 3: (109, 130), 4: (152, 172),
            5: (189, 213), 6: (374, 395), 7: (410, 431)},
}
FACES = {"tm6": [6], "tm45": [4, 5]}

# Adenylyl cyclase 5 (UniProt O95622). Twelve TM helices in two cassettes, and
# two cytoplasmic catalytic domains forming the pseudo-heterodimeric active
# site. AC5 is itself a membrane protein: it sits IN the same bilayer as the
# receptors and only its catalytic core hangs into the cytoplasm. That is what
# "pre-coupled" looks like in space.
TM_AC5 = {1: (196, 216), 2: (242, 262), 3: (268, 288), 4: (299, 319),
          5: (325, 345), 6: (374, 394), 7: (770, 790), 8: (792, 812),
          9: (836, 856), 10: (910, 930), 11: (935, 955), 12: (984, 1004)}
CATALYTIC_AC5 = [(469, 596), (1071, 1210)]   # C1a and C2a, both cytoplasmic

# Present in the deposited structures, absent from a striatal neuron. Hiding
# these is a correctness requirement, not a style choice.
BRIL_RESIDUES = list(range(1001, 1107))   # 5MZP: cytochrome b562 fusion in ICL3
SCFV16_CHAIN = "E"                        # 6VMS: stabilising antibody fragment

# From the OPM DUM planes of 5MZP and 6VMS. 5G53's own slab is 16.8 A --
# depositions disagree by 1.1 A. One bilayer is chosen and every protomer is
# aligned to it (see solve).
MEMBRANE_HALF_THICKNESS = 15.7

# The tetramer as a CHAIN of interfaces, not as a straight line.
#
# Measured 2026-09-01: on both receptors the TM6 face and the TM4/TM5 face sit
# 94-96 degrees apart around the bundle axis, NOT 180. A protomer bonding via
# TM6 on one side and TM4/TM5 on the other MUST turn a corner, so the "linear
# arrangement" of Ferre et al. Fig 3B is a schematic of CONNECTIVITY and cannot
# be built from real coordinates. We walk the chain and let the measured face
# angles decide the shape; it comes out a rhombus.
SPACING = 38.0   # A centre-to-centre. CHOSEN (class A GPCR bundle diameter) --
                 # the interfaces give direction, not distance.

CHAIN = [
    # A2A_ext carries Gs/olf, so it uses 5G53 (A2A + engineered Gs) rather than
    # 5MZP, which has no G protein at all. A2A_int keeps 5MZP because that is
    # the structure with caffeine in the pocket.
    ("A2A_ext", "A2A", "5g53_opm_clean.pdb", "A"),
    ("A2A_int", "A2A", "5mzp_opm_clean.pdb", "A"),
    ("D2_int",  "D2",  "6vms_opm_clean.pdb", "R"),
    ("D2_ext",  "D2",  "6vms_opm_clean.pdb", "R"),
]
INTERFACES = ["tm6", "tm45", "tm6"]   # between consecutive protomers


def solve(asset_dir=STRUCTURES):
    """Walk the interface chain. Each protomer is rotated so the face naming
    its bond points at the partner it bonds to; the next bond direction then
    falls out of that protomer's own measured geometry."""
    frames = []
    for name, receptor, fname, chain in CHAIN:
        pos, rid = mb.read_ca(f"{asset_dir}/{fname}", chain=chain)
        frames.append(mb.face_directions(pos, rid, TM[receptor], FACES))

    placed, cursor, heading = [], np.zeros(2), np.array([1.0, 0.0])
    for i, (name, receptor, fname, chain) in enumerate(CHAIN):
        if i == 0:
            theta = mb.angle(heading) - mb.angle(frames[i][INTERFACES[0]])
        else:
            theta = mb.angle(-heading) - mb.angle(frames[i][INTERFACES[i - 1]])
        placed.append({"name": name, "receptor": receptor, "file": fname,
                       "chain": chain, "theta": float(theta),
                       "axis_xy": cursor.copy()})
        if i < len(INTERFACES):
            heading = mb.rot2(frames[i][INTERFACES[i]], theta)
            cursor = cursor + heading * SPACING

    centre = np.mean([p["axis_xy"] for p in placed], axis=0)
    for p, f, (name, receptor, fname, chain) in zip(placed, frames, CHAIN):
        p["axis_xy"] = p["axis_xy"] - centre
        x, y, _ = mb.location_for(f, p["theta"], p["axis_xy"])
        # Depositions disagree about where the bilayer sits (D2's TM z-centroid
        # is 3.4 A below A2A's). There is ONE membrane, so every protomer's TM
        # bundle is pulled onto a common z=0 rather than trusting four separate
        # fits to agree.
        pos, rid = mb.read_ca(f"{asset_dir}/{fname}", chain=chain)
        tm = mb.residue_mask(rid, TM[receptor].values())
        p["tm_z_centroid"] = float(pos[tm][:, 2].mean())
        p["location_A"] = (x, y, -p["tm_z_centroid"])
    return placed


def place_ac5(asset_dir, protomers, clearance=9.0):
    """Where AC5 sits in the membrane relative to the tetramer.

    It goes IN the bilayer beside the receptors, not floating underneath, and
    must be reachable by the G proteins on BOTH external protomers -- which sit
    at opposite ends of the rhombus. So it is pushed out perpendicular to the
    long axis just far enough to stop clashing. Distance is SEARCHED, not
    chosen: the smallest offset whose closest TM approach clears `clearance`.
    """
    r = mb.orient_report(f"{asset_dir}/ac5_af_confident.pdb", TM_AC5,
                         CATALYTIC_AC5, MEMBRANE_HALF_THICKNESS)
    pos, rid = mb.read_ca(f"{asset_dir}/ac5_af_confident.pdb")
    tm = mb.residue_mask(rid, TM_AC5.values())
    ac5_tm = (pos @ r["R"].T)[tm]
    ac5_tm[:, 2] += r["dz"]

    recep = []
    for p in protomers:
        rp, rr = mb.read_ca(f"{asset_dir}/{p['file']}", chain=p["chain"])
        m = mb.residue_mask(rr, TM[p["receptor"]].values())
        q = mb.rot2_many(rp[m][:, :2], p["theta"])
        recep.append(np.column_stack([q[:, 0] + p["location_A"][0],
                                      q[:, 1] + p["location_A"][1]]))
    recep = np.vstack(recep)

    long_axis = protomers[-1]["axis_xy"] - protomers[0]["axis_xy"]
    perp = np.array([-long_axis[1], long_axis[0]])
    perp /= np.linalg.norm(perp)

    for d in np.arange(20.0, 140.0, 2.0):
        c = perp * d
        gap = np.min(np.linalg.norm(
            ac5_tm[:, None, :2] + c - recep[None, :, :], axis=2))
        if gap >= clearance:
            return {**r, "offset_xy": (float(c[0]), float(c[1])),
                    "distance_A": float(d), "closest_approach_A": float(gap)}
    raise RuntimeError("no clash-free AC5 placement found out to 140 A")


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else STRUCTURES
    ps = solve(d)
    print(f"{'protomer':9} {'rotZ':>8} {'x,y,z (A)':>26} {'TM z-centroid':>14}")
    for p in ps:
        x, y, z = p["location_A"]
        print(f"{p['name']:9} {np.degrees(p['theta']):7.1f}d "
              f"{x:8.1f},{y:7.1f},{z:6.1f} {p['tm_z_centroid']:13.2f}")
    print("\nneighbour spacing (A):")
    for a, b in zip(ps, ps[1:]):
        print(f"  {a['name']:9} -> {b['name']:9} "
              f"{np.linalg.norm(a['axis_xy'] - b['axis_xy']):6.1f}")
    a = place_ac5(d, ps)
    print(f"\nAC5: offset {np.round(a['offset_xy'], 1)} A "
          f"(distance {a['distance_A']:.0f} A)")
    print(f"     closest TM approach to any receptor: {a['closest_approach_A']:.1f} A")
    print(f"     TM alpha-carbons in bilayer slab   : {a['tm_in_slab']*100:.1f}% "
          f"({a['n_helices']}/12 helices)")
