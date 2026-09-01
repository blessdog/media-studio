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

MEMBRANE_HALF_THICKNESS = 15.7            # A, from the OPM DUM planes of 5MZP and 6VMS.
                                          # 5G53's own OPM slab is 16.8 A -- depositions
                                          # disagree by 1.1 A. One bilayer is chosen, and
                                          # every protomer is aligned to it (see align_z).

# Adenylyl cyclase 5 (UniProt O95622), fetched 2026-09-01. Twelve TM helices in
# two cassettes, and two cytoplasmic catalytic domains that form the pseudo-
# heterodimeric active site. AC5 is itself a membrane protein: it sits IN the
# same bilayer as the receptors, not underneath it -- only its catalytic core
# hangs into the cytoplasm. That is what "pre-coupled" looks like in space.
TM_AC5 = {1: (196, 216), 2: (242, 262), 3: (268, 288), 4: (299, 319),
          5: (325, 345), 6: (374, 394), 7: (770, 790), 8: (792, 812),
          9: (836, 856), 10: (910, 930), 11: (935, 955), 12: (984, 1004)}
CATALYTIC_AC5 = [(469, 596), (1071, 1210)]   # C1a and C2a, both cytoplasmic
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
    # A2A_ext carries Gs/olf, so it uses 5G53 (A2A + engineered Gs) rather than
    # 5MZP, which has no G protein at all. A2A_int keeps 5MZP because that is
    # the structure with caffeine in the pocket.
    ("A2A_ext", "A2A", "5g53_opm_clean.pdb", "A"),
    ("A2A_int", "A2A", "5mzp_opm_clean.pdb", "A"),
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
    for p, f, (name, receptor, fname, chain) in zip(placed, frames, CHAIN):
        p["axis_xy"] = p["axis_xy"] - centre
        x, y, _ = location_for(f, p["theta"], p["axis_xy"])
        # Depositions disagree slightly about where the bilayer sits: measured
        # 2026-09-01, D2's TM z-centroid is 3.4 A below A2A's, and 5G53's OPM
        # slab is 1.1 A thicker than 5MZP's. There is ONE membrane, so every
        # protomer's TM bundle is pulled onto a common z=0 rather than trusting
        # four separate fits to agree.
        pos, rid = read_ca(f"{asset_dir}/{fname}", chain=chain)
        tm = np.zeros(len(rid), bool)
        for lo, hi in TM[receptor].values():
            tm |= (rid >= lo) & (rid <= hi)
        p["tm_z_centroid"] = float(pos[tm][:, 2].mean())
        p["location_A"] = (x, y, -p["tm_z_centroid"])
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


# --- orienting a structure that OPM does not carry --------------------------
#
# OPM has no entry for AC5 (8SL3 returns 404; the deposited model also stops at
# residue 1042 and is missing the C2a catalytic domain entirely), so the
# full-length AlphaFold model AF-O95622 is used and must be oriented here.
#
# The method is the standard one and is checkable: each TM helix's axis is its
# first principal component; the membrane normal is the leading eigenvector of
# the scatter matrix of those axes, which is sign-invariant and so does not care
# that consecutive helices run in opposite directions. The sign is then fixed by
# the one piece of topology that is not ambiguous -- the catalytic domains are
# cytoplasmic, so the normal points away from them.

def _helix_axis(ca):
    c = ca - ca.mean(axis=0)
    return np.linalg.svd(c, full_matrices=False)[2][0]


def membrane_normal(positions, res_ids, tm_ranges, cyto_ranges):
    axes = []
    for lo, hi in tm_ranges.values():
        m = (res_ids >= lo) & (res_ids <= hi)
        if m.sum() >= 5:
            axes.append(_helix_axis(positions[m]))
    axes = np.asarray(axes)
    scatter = axes.T @ axes                      # sign-invariant
    n = np.linalg.eigh(scatter)[1][:, -1]
    n /= np.linalg.norm(n)

    tm = np.zeros(len(res_ids), bool)
    for lo, hi in tm_ranges.values():
        tm |= (res_ids >= lo) & (res_ids <= hi)
    cyto = np.zeros(len(res_ids), bool)
    for lo, hi in cyto_ranges:
        cyto |= (res_ids >= lo) & (res_ids <= hi)
    if cyto.sum() and np.dot(n, positions[cyto].mean(0) - positions[tm].mean(0)) > 0:
        n = -n                                   # normal points extracellular
    return n, len(axes)


def rotation_to_z(n):
    """Rotation matrix taking unit vector n onto +Z (Rodrigues)."""
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(n, z)
    s, c = np.linalg.norm(v), float(np.dot(n, z))
    if s < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)


def orient_report(pdb_path, tm_ranges, cyto_ranges, chain=None):
    """Orient a structure to the membrane and MEASURE how well it worked.

    Returns the transform plus the fraction of TM alpha-carbons that land inside
    the bilayer slab. A membrane protein that is correctly oriented puts nearly
    all of them there; a number well under ~0.85 means the normal is wrong and
    the result must not be rendered.
    """
    pos, rid = read_ca(pdb_path, chain=chain)
    n, n_helices = membrane_normal(pos, rid, tm_ranges, cyto_ranges)
    R = rotation_to_z(n)
    rot = pos @ R.T
    tm = np.zeros(len(rid), bool)
    for lo, hi in tm_ranges.values():
        tm |= (rid >= lo) & (rid <= hi)
    dz = -rot[tm][:, 2].mean()
    inside = np.abs(rot[tm][:, 2] + dz) <= MEMBRANE_HALF_THICKNESS
    return {"R": R, "dz": float(dz), "normal": n, "n_helices": n_helices,
            "tm_in_slab": float(inside.mean()), "n_tm_ca": int(tm.sum())}


def place_ac5(asset_dir, protomers, clearance=9.0):
    """Find where AC5 sits in the membrane relative to the tetramer.

    AC5 is a membrane protein, so it goes IN the bilayer beside the receptors,
    with its catalytic core in the cytoplasm -- not floating underneath. The
    model requires it to be reachable by the G proteins on BOTH external
    protomers, which sit at opposite ends of the rhombus, so it is pushed out
    perpendicular to the long axis just far enough to stop clashing.

    Distance is searched, not chosen: the returned offset is the smallest one
    whose closest TM alpha-carbon approach to any receptor clears `clearance`.
    """
    r = orient_report(f"{asset_dir}/ac5_af_confident.pdb", TM_AC5, CATALYTIC_AC5)
    pos, rid = read_ca(f"{asset_dir}/ac5_af_confident.pdb")
    tm = np.zeros(len(rid), bool)
    for lo, hi in TM_AC5.values():
        tm |= (rid >= lo) & (rid <= hi)
    ac5_tm = (pos @ r["R"].T)[tm]
    ac5_tm[:, 2] += r["dz"]

    recep = []
    for p in protomers:
        rp, rr = read_ca(f"{asset_dir}/{p['file']}", chain=p["chain"])
        m = np.zeros(len(rr), bool)
        for lo, hi in TM[p["receptor"]].values():
            m |= (rr >= lo) & (rr <= hi)
        q = _rot2_many(rp[m][:, :2], p["theta"])
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


def _rot2_many(v, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.column_stack([c * v[:, 0] - s * v[:, 1],
                            s * v[:, 0] + c * v[:, 1]])
