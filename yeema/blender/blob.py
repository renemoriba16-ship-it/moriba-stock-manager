import sys, math, bpy, random
S = sys.argv[1]; sys.path.insert(0, S + "/blend")
from lib import *
reset()
sc = setup_render(res=(1000, 1000), samples=32, bg=(0.022, 0.014, 0.010), world_strength=1.0, transparent=False)
M = materials()
oil = mat("OilBlob", base=(0.95, 0.58, 0.14), rough=0.04, trans=0.85, ior=1.47, coat=0.6)
gold = M['gold']
mb = bpy.data.metaballs.new("Oil"); mb.resolution = 0.06; mb.render_resolution = 0.025; mb.threshold = 0.6
ob = bpy.data.objects.new("OilBlob", mb); bpy.context.collection.objects.link(ob); mb.materials.append(oil)
N = 96; random.seed(7)
els = []
for i in range(9):
    e = mb.elements.new(); e.radius = random.uniform(0.55, 1.0)
    els.append((e, random.uniform(0.6, 1.6), random.uniform(0.5, 1.4), random.random()*6.28, random.choice([1,2]), random.choice([1,2,3])))
sc.frame_start, sc.frame_end = 1, N
for f in range(1, N+1):
    t = (f-1)/N * 2*math.pi
    for (e, ax, az, ph, k1, k2) in els:
        e.co = (ax*math.cos(k1*t+ph), 0.4*math.sin(k2*t+ph)*ax, az*math.sin(k1*t+ph*1.3)*0.9)
        e.keyframe_insert("co", frame=f)
# gold flecks
golds = []
for i in range(7):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(0.05,0.12), segments=32, ring_count=16)
    g = bpy.context.active_object; bpy.ops.object.shade_smooth(); g.data.materials.append(gold)
    r0, ph, h = random.uniform(1.9, 2.6), random.random()*6.28, random.uniform(-1.3,1.3)
    for f in range(1, N+1, 4):
        t = (f-1)/N*2*math.pi
        g.location = (r0*math.cos(t+ph), r0*0.5*math.sin(t+ph), h + 0.25*math.sin(2*t+ph)); g.keyframe_insert("location", frame=f)
    f = N+1; t = 2*math.pi; g.location = (r0*math.cos(t+ph), r0*0.5*math.sin(t+ph), h + 0.25*math.sin(2*t+ph)); g.keyframe_insert("location", frame=f)
area("Back", (0, 5, 2), (0,0,0), energy=2500, size=4, color=(1.0, 0.75, 0.45))
area("Key", (-4, -4, 3), (0,0,0), energy=900, size=3, color=(1.0, 0.92, 0.82))
area("Rim", (4, -1, -2), (0,0,0), energy=600, size=2, color=(1.0, 0.6, 0.3))
camera((0, -9, 0), (0,0,0), lens=55)
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
sc.render.filepath = S + "/render/blob/b_"
bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=S + "/blend/yeema_oil_loop.blend")
