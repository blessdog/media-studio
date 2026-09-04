"""Membrane-protein geometry. General algorithms, no molecule knows its name.

REUSABLE LAYER. Everything here works on any membrane protein and any pair of
structures; nothing in this file mentions a receptor, a ligand or a story. The
subject-specific tables -- which helices, which residues, which arrangement --
live with the job that needs them (see jobs/<job>/complex.py for the caffeine
explainer's spec).

PRIOR ART: coordinate parsing and molecular geometry are Molecular Nodes' job;
membrane orientation is OPM's. This module exists only for what neither
supplies: relative placement of protomers by their interface faces, and a
membrane normal for structures OPM has no entry for.

Split out of blender/lib_complex.py on 2026-09-02, when the caffeine job moved
into jobs/caffeine/ -- the file was doing two things and a second molecular
video would have had to copy half of it.
"""
import numpy as np

ANGSTROM = 0.01        # Molecular Nodes world scale: 1 Blender unit = 100 A


# --- reading coordinates ---------------------------------------------------

def read_ca(path, chain=None):
    """CA atoms from a PDB file -> (positions Nx3 in Angstroms, res_ids N).

    Deliberately a short fixed-column reader rather than a dependency: this runs
    OUTSIDE Blender so placement can be checked without launching it, and
    CA-only backbone geometry is all the interface math needs.
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


def read_hetatm(path, resname):
    """All atoms of one ligand -> (positions Nx3, element symbols)."""
    pos, el = [], []
    for line in open(path):
        if line.startswith("HETATM") and line[17:20].strip() == resname:
            pos.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            el.append(line[76:78].strip() or line[12:16].strip()[0])
    return np.asarray(pos), el


def residue_mask(res_ids, ranges):
    m = np.zeros(len(res_ids), dtype=bool)
    for lo, hi in ranges:
        m |= (res_ids >= lo) & (res_ids <= hi)
    return m


# --- interface faces: where does this protomer present a given helix? ------

def _xy_centroid(positions, mask):
    return positions[mask][:, :2].mean(axis=0)


def face_directions(positions, res_ids, tm_ranges, faces):
    """Unit XY vectors from the TM bundle axis toward each named face.

    `tm_ranges` maps helix number -> (lo, hi). `faces` maps a face name -> the
    list of helix numbers forming it, e.g. {"tm6": [6], "tm45": [4, 5]}.
    Returned in the protomer's own frame, before any placement rotation.
    """
    core = residue_mask(res_ids, tm_ranges.values())
    axis = _xy_centroid(positions, core)
    out = {"axis": axis}
    for name, helices in faces.items():
        v = _xy_centroid(positions,
                         residue_mask(res_ids, [tm_ranges[h] for h in helices])) - axis
        out[name] = v / np.linalg.norm(v)
    return out


def angle(v):
    return float(np.arctan2(v[1], v[0]))


def rot2(v, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def rot2_many(v, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.column_stack([c * v[:, 0] - s * v[:, 1],
                            s * v[:, 0] + c * v[:, 1]])


def location_for(faces, theta, target_xy):
    """Object translation putting the rotated TM-bundle axis at target_xy."""
    a = rot2(faces["axis"], theta)
    return float(target_xy[0] - a[0]), float(target_xy[1] - a[1]), 0.0


# --- orienting a structure that OPM does not carry -------------------------
#
# Each TM helix's axis is its first principal component; the membrane normal is
# the leading eigenvector of the scatter matrix of those axes, which is
# sign-invariant and so does not care that consecutive helices run in opposite
# directions. The sign is then fixed by the one piece of topology that is never
# ambiguous: the cytoplasmic domains are cytoplasmic, so the normal points away.

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
    n = np.linalg.eigh(axes.T @ axes)[1][:, -1]
    n /= np.linalg.norm(n)
    tm = residue_mask(res_ids, tm_ranges.values())
    cyto = residue_mask(res_ids, cyto_ranges)
    if cyto.sum() and np.dot(n, positions[cyto].mean(0) - positions[tm].mean(0)) > 0:
        n = -n
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


def orient_report(pdb_path, tm_ranges, cyto_ranges, half_thickness, chain=None):
    """Orient a structure to the membrane and MEASURE how well it worked.

    Returns the transform plus the fraction of TM alpha-carbons landing inside
    the bilayer slab. A correctly oriented membrane protein puts nearly all of
    them there; well under ~0.85 means the normal is wrong and the result must
    not be rendered. The caller is expected to check it.
    """
    pos, rid = read_ca(pdb_path, chain=chain)
    n, n_helices = membrane_normal(pos, rid, tm_ranges, cyto_ranges)
    R = rotation_to_z(n)
    rot = pos @ R.T
    tm = residue_mask(rid, tm_ranges.values())
    dz = -rot[tm][:, 2].mean()
    inside = np.abs(rot[tm][:, 2] + dz) <= half_thickness
    return {"R": R, "dz": float(dz), "normal": n, "n_helices": n_helices,
            "tm_in_slab": float(inside.mean()), "n_tm_ca": int(tm.sum())}


# --- putting a ligand from one structure into another structure's pocket ---

def superpose(mobile_path, target_path, tm_ranges, mobile_chain=None,
              target_chain=None):
    """Kabsch superposition on shared TM alpha-carbons.

    Standard algorithm (Kabsch 1976) -- not reimplemented out of NIH, but
    because pulling in a structural-bioinformatics dependency to rotate one
    small ligand is a worse trade than the SVD itself.

    Returns the transform plus the RMSD, which is the check: two structures of
    the same receptor should land well under 2 A, and above that the residue
    correspondence is wrong and the placement must not be used.
    """
    mp, mr = read_ca(mobile_path, chain=mobile_chain)
    tp, tr = read_ca(target_path, chain=target_chain)
    tm = set()
    for lo, hi in tm_ranges.values():
        tm |= set(range(lo, hi + 1))
    shared = sorted(tm & set(mr.tolist()) & set(tr.tolist()))
    mi = {r: i for i, r in enumerate(mr.tolist())}
    ti = {r: i for i, r in enumerate(tr.tolist())}
    P = mp[[mi[r] for r in shared]]
    Q = tp[[ti[r] for r in shared]]
    pc, qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    rmsd = float(np.sqrt((((P - pc) @ R.T - (Q - qc)) ** 2).sum(1).mean()))
    return {"R": R, "t": qc - R @ pc, "rmsd": rmsd, "n_shared": len(shared)}
