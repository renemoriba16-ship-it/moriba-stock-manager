import sys, math, bpy
S = sys.argv[1]; mode = sys.argv[2]  # test | anim
sys.path.insert(0, S + "/blend")
import importlib, lib; importlib.reload(lib)
from lib import *

reset()
BG = (0.80, 0.72, 0.62)  # linear-ish world tint; site bg sampled later
sc = setup_render(res=(960, 1200), samples=32 if mode=="anim" else 32, bg=BG, world_strength=0.7)
M = materials()
root, dropper = oil_bottle(S, M)
shadow_floor()
studio()
cam = camera((0, -7.2, 1.9), (0, 0, 1.45), lens=58)

# Drop of oil falling from the pipette tip
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.055, location=(0,0,0))
drop = bpy.context.active_object; drop.name = "Drop"; bpy.ops.object.shade_smooth()
drop.data.materials.append(M['oil'])

N = 120
sc.frame_start, sc.frame_end = 1, N
# bottle rotation
key(root, "rotation_euler", 1, 0.0, index=2)
key(root, "rotation_euler", N, math.radians(-360), index=2)
# dropper: unscrew (spin + small rise), then lift out
key(dropper, "rotation_euler", 1, 0.0, index=2); key(dropper, "location", 1, 0.0, index=2)
key(dropper, "rotation_euler", 30, 0.0, index=2); key(dropper, "location", 30, 0.0, index=2)
key(dropper, "rotation_euler", 62, math.radians(540), index=2); key(dropper, "location", 62, 0.14, index=2)
key(dropper, "location", 100, 1.75, index=2)
key(dropper, "location", N, 1.82, index=2)
key(dropper, "rotation_euler", 70, 0.0, index=0); key(dropper, "rotation_euler", 108, math.radians(-6), index=0)
key(dropper, "rotation_euler", N, math.radians(-6), index=0)
# camera gentle pull-back & rise to frame lifted dropper
key(cam, "location", 1, -7.2, index=1); key(cam, "location", 1, 1.9, index=2)
key(cam, "location", 60, -7.2, index=1); key(cam, "location", 60, 1.9, index=2)
key(cam, "location", 110, -9.0, index=1); key(cam, "location", 110, 2.5, index=2)
key(cam, "location", N, -9.0, index=1); key(cam, "location", N, 2.5, index=2)
# drop: hidden inside, grows at tip (world) then falls
drop.scale = (0,0,0); drop.keyframe_insert("scale", frame=1); drop.keyframe_insert("scale", frame=100)
drop.location = (0, 0, 0.22+1.75-0.04); drop.keyframe_insert("location", frame=100)
drop.scale = (1,1,1.15); drop.keyframe_insert("scale", frame=108)
drop.location = (0, 0.02, 0.22+1.78-0.07); drop.keyframe_insert("location", frame=108)
drop.scale = (0.9,0.9,1.35); drop.keyframe_insert("scale", frame=N)
drop.location = (0, 0.03, 1.72); drop.keyframe_insert("location", frame=N)

# camera tracks the bottle center via constraint-free re-aim: re-aim each key manually
tgt = empty("Tgt", (0,0,1.45))
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
key(tgt, "location", 60, 1.45, index=2); key(tgt, "location", 110, 2.0, index=2)

out = S + "/render/hero/"
if mode == 'test':
    import time
    for f in [int(x) for x in sys.argv[3].split(',')]:
        sc.frame_set(f); sc.render.filepath = out + f"test_{f:03d}.png"
        t = time.time(); bpy.ops.render.render(write_still=True); print("frame", f, "time", round(time.time()-t,1))
else:
    a, b = int(sys.argv[3]), int(sys.argv[4])
    sc.frame_start, sc.frame_end = a, b
    sc.render.filepath = out + "f_"
    bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=S + "/blend/yeema_hero.blend")
