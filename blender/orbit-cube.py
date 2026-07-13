"""Fixture scene: camera orbits a lit cube — proves the deterministic
camera lane. Args after `--`: frames_pattern frames fps width height,
where frames_pattern is a filepath prefix for a PNG sequence (Blender 5
removed built-in video encoding — the harness muxes with ffmpeg).

Run via studio/blender.py (headless, --factory-startup)."""
import math
import sys

import bpy

frames_pattern, frames, fps, width, height = \
    sys.argv[sys.argv.index("--") + 1:][:5]
frames, fps, width, height = int(frames), int(fps), int(width), int(height)

# clean, deterministic scene
bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.object
mat = bpy.data.materials.new("cube-mat")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = \
    (0.8, 0.3, 0.1, 1.0)
cube.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

bpy.ops.object.light_add(type="SUN", location=(4, -4, 8))
bpy.context.object.data.energy = 3.0

# camera rides an empty that rotates a full turn — the deterministic move.
# Track To keeps the subject framed no matter the orbit (the reusable idiom).
bpy.ops.object.empty_add(location=(0, 0, 1))
pivot = bpy.context.object
bpy.ops.object.camera_add(location=(7, 0, 4))
cam = bpy.context.object
cam.parent = pivot
track = cam.constraints.new("TRACK_TO")
track.target = cube
scene.camera = cam

# linear interpolation via preference default — Blender 5.x layered actions
# removed Action.fcurves, so set the default BEFORE inserting keys
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
scene.render.filepath = frames_pattern  # -> <pattern>0001.png ...

bpy.ops.render.render(animation=True)
