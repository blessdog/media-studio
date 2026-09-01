"""Geometry for assembling the A2AR-D2R heterotetramer from real protomers.

PRIOR ART: coordinate parsing, cartoon geometry and membrane orientation are
NOT done here. Structures come pre-oriented from OPM (Orientations of Proteins
in Membranes) -- bilayer normal along +Z, hydrophobic slab centred at z=0 --
so nothing in this file guesses which way is "up". Molecular Nodes builds the
geometry. This module only answers one question OPM cannot: where does each
protomer sit relative to its neighbours.

THE MODEL BEING BUILT (Ferre et al. 2018, Front. Pharmacol. 9:243):
    A2A(ext) --TM6/TM6-- A2A(int) --TM4/TM5-- D2(int) --TM6/TM6-- D2(ext)
Linear arrangement; two internal interacting protomers flanked by two external
non-interacting ones; G proteins engage the EXTERNAL protomers only.

There is no experimental structure of this tetramer. The interfaces were mapped
with TM-interfering peptides, not crystallography. What IS experimental is each
protomer, its membrane orientation, and the TM helix residue ranges -- so the
assembly below is an honest composition of measured parts under a published
model, and every placement number it uses is printed rather than hidden.
"""
import numpy as np

# UniProt transmembrane annotations, fetched 2026-09-01.
# P29274 adenosine receptor A2a / P14416 D(2) dopamine receptor.
TM = {
    "A2A": {1: (8, 32), 2: (43, 66), 3: (78, 100), 4: (121, 143),
            5: (174, 198), 6: (235, 258), 7: (267, 290)},
    "D2":  {1: (38, 60), 2: (71, 93), 3: (109, 130), 4: (152, 172),
            5: (189, 213), 6: (374, 395), 7: (410, 431)},
}

# Scaffolds present in the deposited structures that are absent from a real
# striatal neuron. Hiding these is a correctness requirement, not a style choice.
BRIL_RESIDUES = list(range(1001, 1107))   # 5MZP: cytochrome b562 fusion in ICL3
SCFV16_CHAIN = "E"                        # 6VMS: stabilising antibody fragment

MEMBRANE_HALF_THICKNESS = 15.7            # A, from the OPM DUM planes of BOTH files
ANGSTROM = 0.01                           # Molecular Nodes world scale: 1 BU = 100 A


def _xy_centroid(positions, mask):
    return positions[mask][:, :2].mean(axis=0)


def face_directions(positions, res_ids, receptor):
    """Unit XY vectors from the TM bundle axis toward the TM6 and TM4/5 faces.

    These are the two interfaces the model names. Returned in the protomer's
    own frame, before any placement rotation is applied.
    """
    tm = TM[receptor]
    core = np.zeros(len(res_ids), dtype=bool)
    for lo, hi in tm.values():
        core |= (res_ids >= lo) & (res_ids <= hi)
    axis = _xy_centroid(positions, core)

    def face(helices):
        m = np.zeros(len(res_ids), dtype=bool)
        for h in helices:
            lo, hi = tm[h]
            m |= (res_ids >= lo) & (res_ids <= hi)
        v = _xy_centroid(positions, m) - axis
        return v / np.linalg.norm(v)

    return {"axis": axis, "tm6": face([6]), "tm45": face([4, 5])}


def _angle(v):
    return float(np.arctan2(v[1], v[0]))


def solve_placement(faces, primary, target_dir):
    """Rotation about Z (radians) that points `primary` face at `target_dir`.

    Returns (theta, residual_deg) where residual_deg reports how far the OTHER
    named face ends up from ITS ideal direction. One rotation about Z cannot
    satisfy two interface constraints exactly; the residual is the honest cost
    of the linear arrangement and is printed rather than swallowed.
    """
    theta = _angle(target_dir) - _angle(faces[primary])
    other = "tm45" if primary == "tm6" else "tm6"
    ideal = -np.asarray(target_dir)          # opposite side of the protomer
    got = _rot2(faces[other], theta)
    cos = float(np.clip(np.dot(got, ideal), -1, 1))
    return theta, float(np.degrees(np.arccos(cos)))


def _rot2(v, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def location_for(faces, theta, target_xy):
    """Object translation putting the rotated TM-bundle axis at target_xy."""
    a = _rot2(faces["axis"], theta)
    return float(target_xy[0] - a[0]), float(target_xy[1] - a[1]), 0.0


def read_ca(path, chain=None):
    """CA atoms from a PDB file -> (positions Nx3 in Angstroms, res_ids N).

    Deliberately a 12-line fixed-column reader rather than a dependency: this
    runs OUTSIDE Blender so the placement can be checked without launching it,
    and CA-only backbone geometry is all the interface math needs.
    """
    pos, rid = [], []
    for line in open(path):
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        if chain is not None and line[21] != chain:
            continue
        pos.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        rid.append(int(line[22:26]))
    return np.asarray(pos), np.asarray(rid)


# The tetramer as a CHAIN of interfaces, not as a straight line.
#
# Measured 2026-09-01 from 5MZP and 6VMS: on both receptors the TM6 face and
# the TM4/TM5 face sit ~94-96 degrees apart around the bundle axis, NOT 180.
# So a protomer that bonds via TM6 on one side and TM4/TM5 on the other MUST
# turn a corner. The "linear arrangement" of Ferre et al. Fig 3B is a schematic
# convenience; the real coordinates make a strictly collinear tetramer
# geometrically unavailable. We walk the interface chain and let the measured
# face angles decide the shape, which comes out as a zigzag / rhombus.
SPACING = 38.0   # A, centre-to-centre. CHOSEN (class A GPCR bundle diameter),
                 # not measured -- the interfaces give direction, not distance.

CHAIN = [
    ("A2A_ext", "A2A", "5mzp_opm_clean.pdb", None),
    ("A2A_int", "A2A", "5mzp_opm_clean.pdb", None),
    ("D2_int",  "D2",  "6vms_opm_clean.pdb", "R"),
    ("D2_ext",  "D2",  "6vms_opm_clean.pdb", "R"),
]
# interface between consecutive protomers in CHAIN
INTERFACES = ["tm6", "tm45", "tm6"]


def solve(asset_dir):
    """Walk the interface chain. Each protomer is rotated so the face naming
    its bond points at the partner it bonds to; the next bond direction then
    falls out of that protomer's own measured geometry."""
    frames = []
    for name, receptor, fname, chain in CHAIN:
        pos, rid = read_ca(f"{asset_dir}/{fname}", chain=chain)
        frames.append(face_directions(pos, rid, receptor))

    placed, cursor, heading = [], np.zeros(2), np.array([1.0, 0.0])
    for i, (name, receptor, fname, chain) in enumerate(CHAIN):
        if i == 0:
            theta = _angle(heading) - _angle(frames[i][INTERFACES[0]])
        else:
            # rotate so the incoming face points back the way we came
            theta = _angle(-heading) - _angle(frames[i][INTERFACES[i - 1]])
        placed.append({"name": name, "receptor": receptor, "file": fname,
                       "chain": chain, "theta": float(theta),
                       "axis_xy": cursor.copy()})
        if i < len(INTERFACES):
            heading = _rot2(frames[i][INTERFACES[i]], theta)
            cursor = cursor + heading * SPACING

    centre = np.mean([p["axis_xy"] for p in placed], axis=0)
    for p, f in zip(placed, frames):
        p["axis_xy"] = p["axis_xy"] - centre
        loc = location_for(f, p["theta"], p["axis_xy"])
        p["location_A"] = loc
    return placed


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "assets/pdb"
    ps = solve(d)
    print(f"{'protomer':10} {'rotZ':>8}  {'bundle axis x,y (A)':>22}")
    for p in ps:
        x, y = p["axis_xy"]
        print(f"{p['name']:10} {np.degrees(p['theta']):7.1f}d  {x:10.1f},{y:10.1f}")
    print("\nneighbour spacing check (A):")
    for a, b in zip(ps, ps[1:]):
        print(f"  {a['name']:9} -> {b['name']:9} "
              f"{np.linalg.norm(a['axis_xy'] - b['axis_xy']):6.1f}")
    span = max(np.linalg.norm(a["axis_xy"] - b["axis_xy"])
               for a in ps for b in ps)
    print(f"\ntetramer longest span: {span:.1f} A")
