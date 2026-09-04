"""The mechanism, animated: assembly, the allosteric hit, and caffeine blocking it.

Beats 3-8 of the caffeine explainer in one 10s take. The two things a static
orbit could not say:

  1. WHAT IT IS. The four protomers arrive one at a time so they can be counted,
     and AC5 is on screen BEFORE any of them -- "pre-coupled" means the cyclase
     was already there, not that it turns up when called.
  2. WHAT IT DOES. Adenosine binds the A2A pocket; the effect crosses the
     TM4/TM5 heteromeric interface to D2 and the dopamine response drops. Then
     caffeine takes the same pocket, the signal never departs, and the dopamine
     response stays up. Caffeine is not adding drive -- it is stopping a
     subtraction.

MEASURED, not staged: adenosine (2YDO) and caffeine (5MZP) are placed by Kabsch
superposition onto this A2A protomer, RMSD 1.62 A over 168 shared TM CAs, and
their centroids land 1.8 A apart. The competition for one site is a measurement
from two independent structures, not an animator's assertion.

SCHEMATIC, and marked as such by being a plain sphere rather than a molecule:
the dopamine marker at D2. No dopamine-bound D2 structure exists to borrow from
(6VMS carries no ligand), so it is anchored to Asp114 -- the conserved TM3
aspartate that binds the ligand amine -- and never pretends to be coordinates.

Run via tools/forge-blender.py (headless, --factory-startup + --addons).
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix
import bl_ext.blender_org.molecularnodes as mn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "blender"))
import complex as cx
import lib_membrane as mb

frames_pattern, frames, fps, width, height = \
    sys.argv[sys.argv.index("--") + 1:][:5]
frames, fps, width, height = int(frames), int(fps), int(width), int(height)

ASSETS = cx.STRUCTURES
A = cx.ANGSTROM

# --- beat sheet, in frames at the requested fps ----------------------------
def F(sec):
    return max(1, int(round(sec * fps)))

T_AC5_ALONE = F(1.0)      # the cyclase is already there
T_ARRIVE = F(1.0)         # per protomer
T_SETTLE = F(0.6)
T_ADEN = F(1.4)           # adenosine descends
T_CROSS = F(1.2)          # the allosteric hit crosses the interface
T_CAFF = F(1.6)           # caffeine takes the pocket
T_HOLD = F(1.8)

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene


def mat(name, rgb, rough=0.45, alpha=1.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


M_A2A = mat("a2a", (0.95, 0.33, 0.13))
M_D2 = mat("d2", (0.16, 0.52, 0.95))
M_GS = mat("gs", (1.00, 0.72, 0.20))
M_GI = mat("gi", (0.30, 0.85, 0.70))
M_AC5 = mat("ac5", (0.72, 0.40, 0.90))
M_ADEN = mat("aden", (0.55, 1.00, 0.55), rough=0.15, emit=4.0)
M_CFF = mat("cff", (1.00, 0.90, 0.30), rough=0.15, emit=5.0)
M_PULSE = mat("pulse", (1.00, 0.45, 0.15), rough=0.1, emit=9.0)
M_DOPA = mat("dopa", (0.45, 0.80, 1.00), rough=0.15, emit=6.0)


def world(p, local):
    """Protomer-local Angstroms -> world Blender units."""
    c, s = math.cos(p["theta"]), math.sin(p["theta"])
    x = c * local[0] - s * local[1] + p["location_A"][0]
    y = s * local[0] + c * local[1] + p["location_A"][1]
    z = local[2] + p["location_A"][2]
    return (x * A, y * A, z * A)


def key_loc(obj, frame, loc):
    obj.location = loc
    obj.keyframe_insert("location", frame=frame)


def key_emit(m, frame, value):
    inp = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    inp.default_value = value
    inp.keyframe_insert("default_value", frame=frame)


def key_scale(obj, frame, s):
    obj.scale = (s, s, s)
    obj.keyframe_insert("scale", frame=frame)


def blob(name, loc, radius, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc,
                                         segments=24, ring_count=12)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o


LIGAND_RADIUS = 3.4   # A. NOT van der Waals -- legibility, chosen.


def ligand(name, positions, material, radius=LIGAND_RADIUS):
    """One sphere per heavy atom, parented to an empty that can be animated."""
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.object
    root.name = name
    centre = positions.mean(0)
    for i, q in enumerate(positions):
        o = blob(f"{name}-{i}", tuple((q - centre) * A * 1.0), radius * A, material)
        o.parent = root
    return root


protomers = cx.solve(ASSETS)
by_name = {p["name"]: p for p in protomers}

# --- AC5 first: it is already there ----------------------------------------
ac5 = cx.place_ac5(ASSETS, protomers)
m = mn.Molecule.load(f"{ASSETS}/ac5_af_confident.pdb", name="AC5")
m.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.6),
            selection=mn.MoleculeSelector().is_peptide(), material=M_AC5)
o = m.object
o.rotation_mode = "QUATERNION"
o.rotation_quaternion = Matrix(ac5["R"].tolist()).to_quaternion()
o.location = (ac5["offset_xy"][0] * A, ac5["offset_xy"][1] * A, ac5["dz"] * A)

# --- the four protomers, arriving one at a time ----------------------------
ORDER = ["A2A_ext", "A2A_int", "D2_int", "D2_ext"]
arrive_end = {}
for i, name in enumerate(ORDER):
    p = by_name[name]
    mol = mn.Molecule.load(f"{ASSETS}/{p['file']}", name=name)
    if p["receptor"] == "A2A":
        sel = mn.MoleculeSelector().chain_id(p["chain"]).not_res_id(cx.BRIL_RESIDUES)
        material = M_A2A
    else:
        sel = mn.MoleculeSelector().chain_id(p["chain"])
        material = M_D2
    mol.add_style(mn.StyleCartoon(quality=3, peptide_thickness=0.65,
                                  peptide_width=2.3),
                  selection=sel, material=material)
    if name == "A2A_ext":
        mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.55),
                      selection=mn.MoleculeSelector().chain_id("C"), material=M_GS)
    if name == "D2_ext":
        mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.55),
                      selection=mn.MoleculeSelector().chain_id(["A", "B", "C"]),
                      material=M_GI)

    obj = mol.object
    obj.rotation_euler = (0.0, 0.0, p["theta"])
    home = tuple(v * A for v in p["location_A"])
    # slides in along its own outward radial direction, in the membrane plane
    r = np.array(p["axis_xy"], dtype=float)
    r = r / (np.linalg.norm(r) or 1.0)
    away = (home[0] + r[0] * 240 * A, home[1] + r[1] * 240 * A, home[2])
    start = T_AC5_ALONE + i * T_ARRIVE
    key_loc(obj, 1, away)
    key_loc(obj, start, away)
    key_loc(obj, start + T_ARRIVE, home)
    arrive_end[name] = start + T_ARRIVE

assembled = max(arrive_end.values()) + T_SETTLE

# --- ligands, placed by superposition --------------------------------------
a2a_int = by_name["A2A_int"]
sup = mb.superpose(f"{ASSETS}/2ydo_opm_clean.pdb", f"{ASSETS}/{a2a_int['file']}",
                   cx.TM["A2A"], mobile_chain="A", target_chain=a2a_int["chain"])
print(f"2YDO->5MZP RMSD {sup['rmsd']:.2f} A over {sup['n_shared']} CAs")
adn_local = mb.read_hetatm(f"{ASSETS}/2ydo_opm_clean.pdb", "ADN")[0] @ sup["R"].T + sup["t"]
cff_local = mb.read_hetatm(f"{ASSETS}/{a2a_int['file']}", "CFF")[0]
gap = np.linalg.norm(adn_local.mean(0) - cff_local.mean(0))
print(f"adenosine/caffeine centroid separation {gap:.1f} A -- same pocket")

pocket = world(a2a_int, adn_local.mean(0))
above = (pocket[0], pocket[1], pocket[2] + 42 * A)

adn = ligand("adenosine", adn_local, M_ADEN)
cff = ligand("caffeine", cff_local, M_CFF)

# dopamine marker: schematic, anchored to D2 Asp114 (conserved TM3 aspartate)
d2_int = by_name["D2_int"]
pos, rid = mb.read_ca(f"{ASSETS}/{d2_int['file']}", chain=d2_int["chain"])
asp114 = pos[np.argmin(np.abs(rid - 114))]
dopa_at = world(d2_int, asp114)
dopa = blob("dopamine-response", dopa_at, 5.0 * A, M_DOPA)

# the allosteric hit, crossing the TM4/TM5 interface
mid = tuple((a + b) / 2 for a, b in zip(pocket, dopa_at))
pulse = blob("allosteric-hit", pocket, 3.2 * A, M_PULSE)

# --- choreography ----------------------------------------------------------
t = assembled
key_loc(adn, 1, above); key_loc(adn, t, above)
key_loc(cff, 1, above); key_loc(cff, t, above)
key_emit(M_PULSE, 1, 0.0); key_emit(M_PULSE, t, 0.0)
key_emit(M_DOPA, 1, 6.0); key_emit(M_DOPA, t, 6.0)
key_loc(pulse, 1, pocket); key_loc(pulse, t, pocket)
# Both markers are anchored to coordinates the assembled complex defines, so
# before assembly they would hang in empty space asserting a site that is not
# there yet. Scaled to nothing until the protomers arrive.
key_scale(dopa, 1, 0.001); key_scale(dopa, t - F(0.25), 0.001)
key_scale(dopa, t, 1.0)
key_scale(pulse, 1, 0.001); key_scale(pulse, t, 0.001)

# adenosine lands
t2 = t + T_ADEN
key_loc(adn, t2, pocket)

# the hit crosses the interface; the dopamine response falls
t3 = t2 + T_CROSS
key_emit(M_PULSE, t2, 0.0)
key_emit(M_PULSE, t2 + F(0.15), 9.0)
key_scale(pulse, t2, 0.001)
key_scale(pulse, t2 + F(0.15), 1.0)
key_scale(pulse, t3, 1.0)
key_scale(pulse, t3 + F(0.12), 0.001)
key_loc(pulse, t2, pocket)
key_loc(pulse, t2 + T_CROSS // 2, mid)
key_loc(pulse, t3, dopa_at)
key_emit(M_PULSE, t3, 0.0)
key_emit(M_DOPA, t2 + T_CROSS // 2, 6.0)
key_emit(M_DOPA, t3, 0.8)          # reduced affinity AND intrinsic efficacy
key_scale(dopa, t2 + T_CROSS // 2, 1.0)
key_scale(dopa, t3, 0.45)

# caffeine takes the pocket; adenosine is turned away
t4 = t3 + T_CAFF
key_loc(adn, t3, pocket)
key_loc(adn, t4, above)
key_loc(cff, t3, above)
key_loc(cff, t4, pocket)
# no hit departs, so the dopamine response comes back
key_emit(M_DOPA, t4, 0.8)
key_scale(dopa, t4, 0.45)
t5 = t4 + T_HOLD
key_emit(M_DOPA, t5, 6.0)
key_scale(dopa, t5, 1.0)
key_emit(M_PULSE, t5, 0.0)

total = max(t5 + F(0.4), frames)
print(f"beat sheet: assembled@{assembled} adenosine@{t2} crossed@{t3} "
      f"caffeine@{t4} restored@{t5} of {total} frames")

# --- membrane, framing, light ----------------------------------------------
memb = mat("memb", (0.28, 0.32, 0.46), rough=0.9, alpha=0.03)
for z in (+cx.MEMBRANE_HALF_THICKNESS, -cx.MEMBRANE_HALF_THICKNESS):
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, z * A))
    bpy.context.object.data.materials.append(memb)

bpy.context.scene.frame_set(total)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
STRUCTURAL = set(ORDER) | {"AC5"}
pts = []
for o in scene.objects:
    if o.type != "MESH" or o.name.split(".")[0] not in STRUCTURAL:
        continue
    ev = o.evaluated_get(dg)
    if ev.data and len(ev.data.vertices):
        pts += [o.matrix_world @ v.co for v in ev.data.vertices]
if not pts:
    raise RuntimeError("framing found no structural geometry -- check names: "
                       + ", ".join(sorted(o.name for o in scene.objects)))
xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
radius = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) / 2
print(f"framing on {len(pts)} verts of {len(STRUCTURAL)} structures: "
      f"extent {(max(xs)-min(xs))/A:.0f} x {(max(ys)-min(ys))/A:.0f} x "
      f"{(max(zs)-min(zs))/A:.0f} A, radius {radius/A:.0f} A")

scene.world = bpy.data.worlds.new("w")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = \
    (0.013, 0.015, 0.023, 1)
for nm, loc, rot, energy, col, size in (
        ("key", (3.0, -3.6, 2.8), (0.85, 0.1, 0.7), 1400, (1, .96, .9), 6),
        ("rim", (-3.6, 2.9, 1.8), (1.15, 0, -2.25), 900, (.5, .7, 1.0), 5),
        ("fill", (0, 0, -3.6), (math.pi, 0, 0), 380, (.6, .6, .85), 7)):
    li = bpy.data.lights.new(nm, "AREA")
    li.energy, li.color, li.size = energy, col, size
    ob = bpy.data.objects.new(nm, li)
    scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot

bpy.ops.object.empty_add(location=centre)
pivot = bpy.context.object
LENS = 50.0
sensor_v = 36.0 * height / width
dist = radius / math.sin(math.atan(sensor_v / (2.0 * LENS))) * 1.18
bpy.ops.object.camera_add(
    location=(centre[0] + dist, centre[1], centre[2] + radius * 0.38))
cam = bpy.context.object
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
cam.data.lens = LENS
cam.constraints.new("TRACK_TO").target = pivot
scene.camera = cam

WIDE = cam.location.copy()
CLOSE = WIDE * 0.62
for frame, where in ((1, WIDE), (assembled, WIDE), (t2, CLOSE), (t4, CLOSE),
                     (t5, WIDE)):
    cam.location = where
    cam.keyframe_insert("location", frame=frame)

bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
pivot.rotation_euler = (0, 0, -0.35)
pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, 0.95)
pivot.keyframe_insert("rotation_euler", frame=total)

scene.frame_start, scene.frame_end = 1, total
scene.render.fps = fps
scene.render.resolution_x, scene.render.resolution_y = width, height
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = frames_pattern
bpy.ops.render.render(animation=True)
