# yeema — flowers and animals for the 3D jungle (hibiscus, orchid, butterfly, macaw), exported as GLB
import sys, math, random, bpy
from mathutils import Vector
S = sys.argv[1]; OUT = sys.argv[2]
src = open(S + "/blend/jungle.py").read().split("# ---------------- palm ----------------")[0]
sys.argv = [sys.argv[0], S, OUT]; exec(src)          # reuse Geo, M, export, fresh from jungle.py

def obj_at(g, name, mats, origin):
    """Build a Geo whose vertices are expressed around `origin`, so the object pivots there (wings)."""
    g.v = [v - origin for v in g.v]; ob = g.build(name, mats); ob.location = origin; return ob

PETAL = lambda n, c: M(f"petal_{n}", c, .45)
round_prof = lambda s: math.sin(math.pi * min(1, s * 0.85 + 0.05)) ** 0.5

# ---------------- hibiscus shrub ----------------
fresh(); rng = random.Random(23); g = Geo()
LEAF_, STEM_, RED, GOLD = 0, 1, 2, 3
tips = []
for k in range(5):
    a = k * 2 * math.pi / 5 + rng.uniform(-.3, .3); h = rng.uniform(0.9, 1.5)
    pts = [Vector((math.cos(a) * h * .35 * (i / 6) ** 1.3, math.sin(a) * h * .35 * (i / 6) ** 1.3, h * i / 6)) for i in range(7)]
    g.tube(pts, [.025 - .015 * i / 6 for i in range(7)], sides=5, m=STEM_)
    tips.append((pts[-1], a))
    for i in range(2, 7):
        for j in range(3):
            az = rng.uniform(0, 6.28)
            g.blade(pts[i], Vector((math.cos(az), math.sin(az), rng.uniform(-.2, .5))), rng.uniform(.16, .24), rng.uniform(.07, .1), droop=.3, segs=3, cols=2, m=LEAF_)
for (p, a) in tips + [(t[0] + Vector((rng.uniform(-.2, .2), rng.uniform(-.2, .2), -rng.uniform(.25, .45))), t[1] + 1) for t in tips[:4]]:
    face = Vector((math.cos(a) * .7, math.sin(a) * .7, .7)).normalized()
    up = Vector((0, 0, 1)); side = face.cross(up).normalized(); up2 = side.cross(face).normalized()
    for i in range(5):
        th = i * 2 * math.pi / 5
        d = (face * .55 + side * math.cos(th) + up2 * math.sin(th)).normalized()
        g.blade(p, d, .17, .085, droop=-.15, fold=-.25, segs=4, cols=3, profile=round_prof, m=RED)
    g.tube([p, p + face * .16], [.008, .006], sides=4, m=GOLD)
export("hibiscus", [g.build("hibiscus", [M("leaf_hib", (0.05, 0.16, 0.04), .5), STEM(), PETAL("red", (0.85, 0.03, 0.06)), PETAL("gold", (0.95, 0.65, 0.08))])])

# ---------------- orchid cluster ----------------
fresh(); rng = random.Random(29); g = Geo()
for k in range(5):  # broad base leaves
    az = k * 2 * math.pi / 5 + rng.uniform(-.2, .2)
    g.blade(Vector((0, 0, .03)), Vector((math.cos(az), math.sin(az), .35)), rng.uniform(.3, .4), .09, droop=.4, fold=.2, segs=8, cols=4, m=0)
for k in range(3):  # arching flower spikes
    az = k * 2.1 + rng.uniform(-.3, .3)
    sp = lambda s, az=az: Vector((math.cos(az) * .45 * s, math.sin(az) * .45 * s, .75 * math.sin(s * 1.9)))
    g.tube([sp(i / 10) for i in range(11)], [.008] * 11, sides=4, m=1)
    colour = 2 if k != 1 else 3
    for f in range(5):
        s = .55 + f * .1; c = sp(s) - Vector((0, 0, .05))
        face = Vector((math.cos(az + 1.57), math.sin(az + 1.57), .15)).normalized()
        side = face.cross(Vector((0, 0, 1))).normalized(); up2 = side.cross(face).normalized()
        for i in range(5):
            th = i * 2 * math.pi / 5 + .3
            g.blade(c, (face * .3 + side * math.cos(th) + up2 * math.sin(th)).normalized(), .07 if i else .05, .045, droop=0, fold=-.1, segs=4, cols=3, profile=round_prof, m=colour)
        g.blade(c, (face + Vector((0, 0, -.6))).normalized(), .05, .03, droop=.2, segs=3, cols=2, m=4)  # lip
export("orchid", [g.build("orchid", [M("leaf_orc", (0.07, 0.2, 0.06), .4), STEM(), PETAL("pink", (0.92, 0.45, 0.7)), PETAL("white", (0.95, 0.92, 0.95)), PETAL("lip", (0.75, 0.1, 0.35))])])

# ---------------- butterfly (wings pivot on the body) ----------------
fresh(); objs = []
outline = [(0, 0), (.18, .1), (.42, .2), (.5, .14), (.44, -.02), (.32, -.1), (.36, -.24), (.24, -.34), (.1, -.26), (.02, -.1)]
for side, name in ((1, "WingR"), (-1, "WingL")):
    g = Geo()
    pts = [Vector((side * x, y, 0)) for x, y in outline]
    c = Vector((0, 0, 0)); g.v.append(c)
    for p in pts: g.v.append(p)
    n = len(pts)
    for i in range(n):
        a, b = 1 + i, 1 + (i + 1) % n
        g.face((0, a, b) if side > 0 else (0, b, a), 0)
    objs.append(g.build(name, [M("wing", (1, 1, 1), .35)]))
g = Geo(); g.tube([Vector((0, .1, 0)), Vector((0, -.06, 0)), Vector((0, -.18, 0))], [.018, .02, .01], sides=6, m=0)
objs.append(g.build("BBody", [M("bbody", (0.03, 0.03, 0.04), .6)]))
export("butterfly", objs)

# ---------------- scarlet macaw (facing +Y, wings pivot at the shoulders) ----------------
fresh(); objs = []
RED_, YEL, BLU, BEAK, WHITE = [M("macaw_red", (0.7, 0.02, 0.02), .5), M("macaw_yellow", (0.95, 0.6, 0.02), .5), M("macaw_blue", (0.02, 0.18, 0.7), .45), M("beak", (0.85, 0.8, 0.7), .4), M("face", (0.95, 0.93, 0.9), .7)]
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=.11, location=(0, 0, 0)); b = bpy.context.active_object; b.name = "MBody"; b.scale = (1, 1.9, 1.05); b.data.materials.append(RED_); bpy.ops.object.shade_smooth(); objs.append(b)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=.075, location=(0, .23, .07)); h = bpy.context.active_object; h.name = "MHead"; h.data.materials.append(RED_); bpy.ops.object.shade_smooth(); objs.append(h)
for sx in (1, -1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.035, location=(sx * .045, .26, .075)); e = bpy.context.active_object; e.scale = (.5, 1, 1); e.data.materials.append(WHITE); objs.append(e)
g = Geo(); g.tube([Vector((0, .28, .06)), Vector((0, .33, .05)), Vector((0, .345, .01)), Vector((0, .33, -.03))], [.032, .026, .016, .004], sides=8, m=0); objs.append(g.build("Beak", [BEAK]))
g = Geo()  # long tail: red feathers with blue tips
for k, dx in enumerate((-.03, 0, .03)):
    base = Vector((dx, -.18, -.02))
    g.blade(base, Vector((dx * 2, -1, -.25)), .55 - abs(dx) * 3, .045, droop=.05, segs=8, cols=2, m=0 if k == 1 else 1)
objs.append(g.build("Tail", [RED_, BLU]))
for side, name in ((1, "WingR"), (-1, "WingL")):
    g = Geo(); sh = Vector((side * .08, .05, .04))
    for k, (m_i, w0, ln) in enumerate(((0, .0, .2), (1, .17, .12), (2, .26, .2))):
        base = sh + Vector((side * w0, -.02 * k, 0))
        g.blade(base, Vector((side, -.35 - .25 * k, 0)), ln, .11 - .015 * k, droop=0, fold=.05, segs=5, cols=3, m=m_i)
    objs.append(obj_at(g, name, [RED_, YEL, BLU], sh))
export("macaw", objs)
print("LIFE DONE")
