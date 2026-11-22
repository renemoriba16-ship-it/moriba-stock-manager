import sys, math, bpy
S = sys.argv[1]; sys.path.insert(0, S + "/blend")
from lib import *
out = S + "/render/products/"

def scene_base(res, bg=(0.80,0.72,0.62)):
    reset(); sc = setup_render(res=res, samples=96, bg=bg, world_strength=0.7)
    shadow_floor(); studio(); return sc, materials()

# individual stills
for name in ["oil", "shampoo", "mask"]:
    sc, M = scene_base((900, 1125))
    if name == "oil":
        r, d = oil_bottle(S, M); camera((0,-7.6,1.6), (0,0,1.17), lens=60)
    elif name == "shampoo":
        r = shampoo_bottle(S, M); camera((0,-8.6,1.8), (0,0,1.33), lens=60)
    else:
        r, lid = mask_jar(S, M); camera((0,-7.0,2.4), (0,0,0.55), lens=60)
    r.rotation_euler.z = math.radians(-14)
    sc.render.filepath = out + name + ".png"; bpy.ops.render.render(write_still=True)

# group shot
sc, M = scene_base((1800, 1100))
o, d = oil_bottle(S, M); o.location = (0.15, 0.2, 0); o.rotation_euler.z = math.radians(-8)
s = shampoo_bottle(S, M); s.location = (-1.25, 0.9, 0); s.rotation_euler.z = math.radians(10)
j, lid = mask_jar(S, M); j.location = (1.55, 0.5, 0); j.rotation_euler.z = math.radians(-25)
camera((0, -9.5, 2.6), (0.1, 0.4, 1.05), lens=55)
sc.render.filepath = out + "group.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S + "/blend/yeema_products.blend")
