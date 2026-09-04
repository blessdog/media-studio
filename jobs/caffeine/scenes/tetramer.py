"""The A2AR-D2R heterotetramer pre-coupled to adenylyl cyclase 5, in a membrane.

Beats 3-5 and 7 of the caffeine explainer, in one scene:
  - four real receptor protomers, placed by measured interface geometry
  - Gs/olf on the external A2A, Gi on the external D2 (Ferre et al. 2018:
    G proteins engage the EXTERNAL protomers only)
  - AC5 sitting IN the same bilayer with its catalytic core in the cytoplasm,
    already there before any signal arrives -- that is what "pre-coupled" means
  - caffeine in the A2A orthosteric pocket

PRIOR ART: Molecular Nodes builds all molecular geometry. OPM supplies membrane
orientation for the receptors. UniProt supplies TM helix ranges. blender/
jobs/caffeine/complex.py answers only what those cannot: relative placement, and the
membrane normal for AC5 (which OPM has no entry for).

SCAFFOLDS HIDDEN, because they are not in a striatal neuron:
  5MZP residues 1001-1106  bRIL (cytochrome b562) fusion in ICL3
  6VMS chain E             scFv16 stabilising antibody fragment

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


M_A2A = mat("a2a", (0.95, 0.33, 0.13))          # adenosine side: warm
M_D2 = mat("d2", (0.16, 0.52, 0.95))            # dopamine side: cool
M_GS = mat("gs", (1.00, 0.72, 0.20))            # Gs/olf -- raises cAMP
M_GI = mat("gi", (0.30, 0.85, 0.70))            # Gi -- lowers it
M_AC5 = mat("ac5", (0.72, 0.40, 0.90))          # the cyclase they converge on
M_CFF = mat("cff", (1.0, 0.93, 0.45), rough=0.15, emit=2.5)   # caffeine

# --- the four protomers ----------------------------------------------------
protomers = cx.solve(ASSETS)
for p in protomers:
    mol = mn.Molecule.load(f"{ASSETS}/{p['file']}", name=p["name"])
    if p["receptor"] == "A2A":
        sel = mn.MoleculeSelector().chain_id(p["chain"]).not_res_id(cx.BRIL_RESIDUES)
        material = M_A2A
    else:
        sel = mn.MoleculeSelector().chain_id(p["chain"])
        material = M_D2
    mol.add_style(mn.StyleCartoon(quality=3, peptide_thickness=0.65,
                                  peptide_width=2.3),
                  selection=sel, material=material)

    # G proteins engage the EXTERNAL protomers only
    if p["name"] == "A2A_ext":                  # 5G53 chain C: engineered Gs
        mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.55),
                      selection=mn.MoleculeSelector().chain_id("C"),
                      material=M_GS)
    if p["name"] == "D2_ext":                   # 6VMS chains A/B/C: Gai/Gb/Gg
        mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.55),
                      selection=mn.MoleculeSelector().chain_id(["A", "B", "C"]),
                      material=M_GI)
    # caffeine lives in 5MZP only -- the internal A2A carries the pocket beat
    if p["name"] == "A2A_int":
        mol.add_style(mn.StyleBallAndStick(),
                      selection=mn.MoleculeSelector().res_name("CFF"),
                      material=M_CFF)

    o = mol.object
    o.rotation_euler = (0.0, 0.0, p["theta"])
    o.location = tuple(v * A for v in p["location_A"])

# --- AC5, in the same membrane, already there ------------------------------
ac5 = cx.place_ac5(ASSETS, protomers)
print(f"AC5 placed {ac5['distance_A']:.0f} A off-axis; closest approach "
      f"{ac5['closest_approach_A']:.1f} A; TM in slab {ac5['tm_in_slab']*100:.0f}%")
mol = mn.Molecule.load(f"{ASSETS}/ac5_af.pdb", name="AC5")
mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.6),
              selection=mn.MoleculeSelector().is_peptide(), material=M_AC5)
o = mol.object
o.rotation_mode = "QUATERNION"
o.rotation_quaternion = Matrix(ac5["R"].tolist()).to_quaternion()
o.location = (ac5["offset_xy"][0] * A, ac5["offset_xy"][1] * A, ac5["dz"] * A)

bpy.context.view_layer.update()

# --- the bilayer -----------------------------------------------------------
# Wide enough that its edges leave frame: a membrane reads as a plane, and a
# plane you can see the corners of reads as a floating card.
memb = mat("memb", (0.28, 0.32, 0.46), rough=0.9, alpha=0.045)
for z in (+cx.MEMBRANE_HALF_THICKNESS, -cx.MEMBRANE_HALF_THICKNESS):
    bpy.ops.mesh.primitive_plane_add(size=9.0, location=(0, 0, z * A))
    bpy.context.object.data.materials.append(memb)

# --- frame everything that is actually in the shot -------------------------
mols = [o for o in scene.objects if o.type == "MESH" and "Plane" not in o.name]
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in mols:
    ev = o.evaluated_get(dg)
    if ev.data and len(ev.data.vertices):
        pts += [o.matrix_world @ v.co for v in ev.data.vertices]
xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
radius = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) / 2
print(f"scene radius {radius / A:.0f} A, centre {[round(c / A) for c in centre]} A")

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
# Fit the bounding sphere to the SHORT (vertical) axis of a 16:9 frame.
# Blender's default sensor is 36mm on the long side, so the vertical half-height
# is 36*(h/w)/2. Distance for a sphere of radius r to subtend the half-angle
# theta is r/sin(theta) -- derived, not dialled in. MARGIN is the only chosen
# number here and it is the breathing room around the subject.
MARGIN = 1.18
sensor_v = 36.0 * height / width
theta_v = math.atan(sensor_v / (2.0 * LENS))
dist = radius / math.sin(theta_v) * MARGIN
print(f"camera: radius {radius / A:.0f} A, vfov {math.degrees(theta_v)*2:.1f} deg, "
      f"distance {dist / A:.0f} A")
bpy.ops.object.camera_add(location=(centre[0] + dist, centre[1], centre[2] + radius * 0.38))
cam = bpy.context.object
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
cam.data.lens = LENS
cam.constraints.new("TRACK_TO").target = pivot
scene.camera = cam

bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.tau)
pivot.keyframe_insert("rotation_euler", frame=frames)

scene.frame_start, scene.frame_end = 1, frames
scene.render.fps = fps
scene.render.resolution_x, scene.render.resolution_y = width, height
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = frames_pattern

bpy.ops.render.render(animation=True)
