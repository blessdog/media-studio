"""Probe scene: the A2A adenosine receptor with caffeine in the pocket.

PRIOR ART: structure loading, ribbon/cartoon geometry, atom instancing and
per-element colouring are ALL done by Molecular Nodes (Brady Johnston,
bl_ext.blender_org.molecularnodes, v4.5.x, MDAnalysis/biotite backed). Nothing
here parses a coordinate file or builds molecular geometry by hand -- this
script only stages, lights and moves a camera. See
docs/MOLECULAR-LANE-RESEARCH-2026-09-01.md for the tools rejected and why
(ChimeraX->glTF: frozen geometry; CHARMM-GUI: precision the audience never
cashes in).

Structure is PINNED in blender/assets/pdb/5mzp.cif (2.1 A, X-ray), not fetched,
so the render is reproducible offline and does not depend on RCSB uptime.

WHY THE bRIL SELECTION: 5MZP entity 1 is "Adenosine receptor A2a, Soluble
cytochrome b562, Adenosine receptor A2a" -- a thermostabilising fusion spliced
into intracellular loop 3, numbered residues 1001-1106. It is a crystallography
scaffold and is NOT present in a striatal neuron. Rendering it would put a
protein domain on screen that does not exist in the viewer's brain.

Run via studio/blender.py (headless, --factory-startup + --addons).
"""
import math
import sys

import bpy
import bl_ext.blender_org.molecularnodes as mn

frames_pattern, frames, fps, width, height = \
    sys.argv[sys.argv.index("--") + 1:][:5]
frames, fps, width, height = int(frames), int(fps), int(width), int(height)

ROOT = "/Users/SSDrive/projects/mediaStudio/media-studio"
BRIL = list(range(1001, 1107))

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene

mol = mn.Molecule.load(f"{ROOT}/blender/assets/pdb/5mzp.cif")

# the receptor itself: seven transmembrane helices, bRIL fusion excluded
mol.add_style(
    mn.StyleCartoon(quality=3, peptide_thickness=0.7, peptide_width=2.4),
    selection=mn.MoleculeSelector().is_peptide().not_res_id(BRIL),
    color="common",
)
# caffeine, in the orthosteric pocket -- the whole point of this structure
mol.add_style(
    mn.StyleBallAndStick(),
    selection=mn.MoleculeSelector().res_name("CFF"),
)
obj = mol.object
bpy.context.view_layer.update()

# --- staging ---------------------------------------------------------------
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (.02, .02, .03, 1)

key = bpy.data.lights.new("key", "AREA"); key.energy = 400; key.size = 4
ko = bpy.data.objects.new("key", key); scene.collection.objects.link(ko)
ko.location = (3, -4, 4); ko.rotation_euler = (0.7, 0.2, 0.6)

rim = bpy.data.lights.new("rim", "AREA"); rim.energy = 250; rim.size = 3
rim.color = (0.5, 0.7, 1.0)
ro = bpy.data.objects.new("rim", rim); scene.collection.objects.link(ro)
ro.location = (-4, 3, 2); ro.rotation_euler = (1.2, 0, -2.2)

bpy.ops.object.empty_add(location=tuple(obj.location))
pivot = bpy.context.object
bpy.ops.object.camera_add(location=(2.2, 0, 0.3))
cam = bpy.context.object
cam.parent = pivot
cam.data.lens = 70
cam.constraints.new("TRACK_TO").target = obj
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
