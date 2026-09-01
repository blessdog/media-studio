"""The A2AR-D2R heterotetramer, pre-coupled to Gs/olf and Gi, in a membrane.

Beat 3-5 of the caffeine explainer: four real receptor protomers, placed by
measured interface geometry (blender/lib_complex.py), sitting in the OPM
bilayer both source structures agree on (z = +/-15.7 A).

PRIOR ART: Molecular Nodes builds every piece of molecular geometry here.
OPM supplies membrane orientation. UniProt supplies TM helix ranges. This file
stages, colours and moves a camera -- nothing else.

SCAFFOLDS HIDDEN, because they are not in a striatal neuron:
  5MZP residues 1001-1106  bRIL (cytochrome b562) fusion in ICL3
  6VMS chain E             scFv16 stabilising antibody fragment

Run via studio/blender.py (headless, --factory-startup + --addons).
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np
import bl_ext.blender_org.molecularnodes as mn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_complex as lc

frames_pattern, frames, fps, width, height = \
    sys.argv[sys.argv.index("--") + 1:][:5]
frames, fps, width, height = int(frames), int(fps), int(width), int(height)

ASSETS = str(Path(__file__).resolve().parent / "assets" / "pdb")
A = lc.ANGSTROM

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene


def mat(name, rgb, rough=0.45, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


M_A2A = mat("a2a", (0.95, 0.35, 0.15))       # adenosine side: warm
M_D2 = mat("d2", (0.20, 0.55, 0.95))         # dopamine side: cool
M_GS = mat("gs", (1.00, 0.75, 0.25))         # Gs/olf
M_GI = mat("gi", (0.45, 0.85, 0.75))         # Gi
M_LIG = mat("lig", (1.0, 0.95, 0.6), rough=0.2)

# --- the four protomers ----------------------------------------------------
for p in lc.solve(ASSETS):
    mol = mn.Molecule.load(f"{ASSETS}/{p['file']}", name=p["name"])
    sel = mn.MoleculeSelector()
    if p["receptor"] == "A2A":
        sel = sel.is_peptide().not_res_id(lc.BRIL_RESIDUES)
        material = M_A2A
    else:
        sel = sel.chain_id("R")
        material = M_D2
    mol.add_style(mn.StyleCartoon(quality=3, peptide_thickness=0.65,
                                  peptide_width=2.3),
                  selection=sel, material=material)

    # G proteins engage the EXTERNAL protomers only (Ferre et al. 2018)
    if p["name"] == "D2_ext":
        mol.add_style(mn.StyleCartoon(quality=2, peptide_thickness=0.55),
                      selection=mn.MoleculeSelector().chain_id(["A", "B", "C"]),
                      material=M_GI)
    if p["receptor"] == "A2A":
        mol.add_style(mn.StyleBallAndStick(),
                      selection=mn.MoleculeSelector().res_name("CFF"),
                      material=M_LIG)

    o = mol.object
    o.rotation_euler = (0.0, 0.0, p["theta"])
    o.location = tuple(v * A for v in p["location_A"])

bpy.context.view_layer.update()

# --- the bilayer both structures agree on ----------------------------------
memb = mat("memb", (0.30, 0.34, 0.48), rough=0.9, alpha=0.055)
for z in (+lc.MEMBRANE_HALF_THICKNESS, -lc.MEMBRANE_HALF_THICKNESS):
    bpy.ops.mesh.primitive_plane_add(size=1.7, location=(0, 0, z * A))
    bpy.context.object.data.materials.append(memb)

# --- staging ---------------------------------------------------------------
scene.world = bpy.data.worlds.new("w")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = \
    (0.015, 0.017, 0.025, 1)

for nm, loc, rot, energy, col, size in (
        ("key", (2.5, -3.0, 2.2), (0.85, 0.1, 0.7), 700, (1, .96, .9), 5),
        ("rim", (-3.0, 2.4, 1.4), (1.15, 0, -2.25), 450, (.5, .7, 1.0), 4),
        ("fill", (0, 0, -3.0), (math.pi, 0, 0), 200, (.6, .6, .8), 6)):
    li = bpy.data.lights.new(nm, "AREA")
    li.energy, li.color, li.size = energy, col, size
    ob = bpy.data.objects.new(nm, li)
    scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler = loc, rot

bpy.ops.object.empty_add(location=(0, 0, 0))
pivot = bpy.context.object
bpy.ops.object.camera_add(location=(2.95, 0, 0.85))
cam = bpy.context.object
cam.parent = pivot
cam.data.lens = 52
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
