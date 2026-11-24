# yeema — procedural jungle plant library, exported as GLB for the real-time three.js scene
import sys, os, math, random, bpy
from mathutils import Vector
S = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, S + "/blend")
import lib

def M(name, col, rough=0.6, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metallic
    m.use_backface_culling = False
    return m

class Geo:
    def __init__(self): self.v, self.f, self.mi, self.uv = [], [], [], []
    def face(self, idx, m): self.f.append(idx); self.mi.append(m)
    def tube(self, pts, radii, sides=8, flat=1.0, m=0, cap=True):
        n = None; start = len(self.v)
        for i, (p, r) in enumerate(zip(pts, radii)):
            t = (pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]).normalized()
            if n is None:
                up = Vector((0,0,1)) if abs(t.z) < 0.95 else Vector((1,0,0)); n = t.cross(up).normalized()
            else: n = (n - t*n.dot(t)).normalized()
            b = t.cross(n).normalized()
            for k in range(sides):
                a = 2*math.pi*k/sides; self.v.append(p + r*(math.cos(a)*n + flat*math.sin(a)*b)); self.uv.append((k/sides, i/max(1, len(pts)-1)))
        for i in range(len(pts)-1):
            for k in range(sides):
                a = start + i*sides + k; b2 = start + i*sides + (k+1) % sides
                self.face((a, b2, b2+sides, a+sides), m)
        if cap:
            self.v.append(pts[-1]); self.uv.append((.5, 1.)); c = len(self.v)-1; last = start + (len(pts)-1)*sides
            for k in range(sides): self.face((last+k, last+(k+1) % sides, c), m)
    def blade(self, base, direction, length, width, droop, fold=0.12, segs=14, cols=6, profile=None, m=0, drop=None, twist=0.0):
        """A leaf blade along a drooping midrib. drop(i,j)->True removes a face (tears, slits, holes)."""
        d = Vector(direction).normalized(); h = Vector((d.x, d.y, 0))
        side = (Vector((-d.y, d.x, 0)) if h.length > 1e-3 else Vector((1,0,0))).normalized()
        prof = profile or (lambda s: math.sin(math.pi*s)**0.7)
        start = len(self.v); rows = segs + 1
        for i in range(rows):
            s = i/segs
            c = base + d*(s*length) + Vector((0,0,-droop*length*s*s))
            w = width*prof(s)
            sd = side*math.cos(twist*s) + Vector((0,0,1))*math.sin(twist*s)
            for j in range(cols+1):
                u = j/cols*2 - 1
                self.v.append(c + sd*(u*w) + Vector((0,0,fold*w*abs(u)))); self.uv.append((j/cols, s))
        for i in range(segs):
            for j in range(cols):
                if drop and drop(i, j): continue
                a = start + i*(cols+1) + j
                self.face((a, a+1, a+cols+2, a+cols+1), m)
    def frond(self, C, az, el, L, droop, rng, m_leaf, m_stem, steps=30, leaf_len=0.72, w=0.06):
        dirh = Vector((math.cos(az), math.sin(az), 0)); side = Vector((-math.sin(az), math.cos(az), 0))
        sp = lambda s: C + dirh*(s*L*math.cos(el)) + Vector((0,0, s*L*math.sin(el) - droop*(s**2)*L))
        for i in range(1, steps):
            s = i/steps; p = sp(s); sd = (sp(min(1, s+1/steps)) - p).normalized()
            l = (leaf_len*math.sin(math.pi*min(1, s*1.08))**0.8 + 0.05)*L/2.6*rng.uniform(.85, 1.1)
            for sg in (-1, 1):
                if rng.random() < 0.05: continue
                dd = (side*sg*0.8 + sd*0.4 + Vector((0,0,-0.45 - 0.25*s))).normalized()
                ww = w*L/2.6; tip = p + dd*l; mid = p + dd*l*.5 + Vector((0,0,.02))
                b0 = len(self.v); self.v += [p, p+sd*ww, mid+sd*ww*.6, mid, tip]; self.uv += [(.5, 0), (.62, .04), (.62, .5), (.5, .5), (.5, 1)]
                self.face((b0, b0+1, b0+2, b0+3), m_leaf); self.face((b0+3, b0+2, b0+4), m_leaf)
        self.tube([sp(i/12) for i in range(13)], [0.03*(1-i/14)+.006 for i in range(13)], sides=5, m=m_stem)
    def build(self, name, mats, ao=True, tint=None):
        me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in self.v], [], self.f); me.update()
        for m in mats: me.materials.append(m)
        for poly, mi in zip(me.polygons, self.mi): poly.material_index = mi
        me.shade_smooth()
        uv = self.uv + [(.5, .5)] * (len(self.v) - len(self.uv))
        layer = me.uv_layers.new(name="UVMap")
        for loop in me.loops: layer.data[loop.index].uv = uv[loop.vertex_index]
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
        if ao: bake_ao(ob, tint)
        return ob

def bake_ao(ob, tint=None):
    """Bake ambient occlusion into a colour attribute: inner leaves and crevices get darker, like in a real render."""
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    if not sc.world: sc.world = bpy.data.worlds.new("AOW")
    sc.world.light_settings.distance = 0.6
    me = ob.data; ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'POINT'); me.color_attributes.active_color = ca
    me.attributes.render_color_index = me.color_attributes.active_color_index
    for o in bpy.context.view_layer.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
    for i in range(len(ca.data)):  # soften: keep crevices darker without crushing thin leaves to black
        c = ca.data[i].color; k = 0.42 + 0.58 * c[0]; ca.data[i].color = (k, k, k, 1)
    if tint:
        for i, v in enumerate(me.vertices):
            t = tint(v.co); c = ca.data[i].color
            ca.data[i].color = (c[0]*t[0], c[1]*t[1], c[2]*t[2], 1)

def export(name, objs=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in (objs or bpy.context.scene.objects): o.select_set(True)
    kw = dict(filepath=f"{OUT}/{name}.glb", export_format='GLB', use_selection=True, export_apply=True,
              export_normals=True, export_texcoords=True, export_materials='EXPORT', export_cameras=False, export_lights=False)
    try: bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE')
    except TypeError: bpy.ops.export_scene.gltf(**kw, export_colors=True)
    print("exported", name)

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

LEAF  = lambda: M("leaf", (0.10, 0.24, 0.07), 0.55)
LEAF2 = lambda: M("leaf_light", (0.20, 0.36, 0.08), 0.5)
LEAF3 = lambda: M("leaf_dark", (0.04, 0.13, 0.05), 0.5)
STEM  = lambda: M("stem", (0.22, 0.32, 0.12), 0.6)
BARK  = lambda: M("bark", (0.16, 0.12, 0.09), 0.9)
MOSS  = lambda: M("moss", (0.12, 0.22, 0.05), 0.95)

# ---------------- palm ----------------
fresh(); rng = random.Random(3); g = Geo()
H = 8.0; pts = [Vector((0.9*(i/30*H/H)**2, 0.2*math.sin(i/30*math.pi), i/30*H)) for i in range(31)]
g.tube(pts, [0.26 - 0.09*i/30 + 0.012*math.sin(i*2.3) for i in range(31)], sides=10, m=0)
C = pts[-1]
for i in range(16):
    az = i*2*math.pi/16 + rng.uniform(-.2, .2); old = rng.random()
    g.frond(C, az, math.radians(rng.uniform(15, 55) - 30*old), rng.uniform(2.8, 3.5), rng.uniform(.55, .9) + .4*old, rng, 1 + int(old > .6), 3)
export_ob = g.build("palm", [BARK(), LEAF(), LEAF2(), STEM()]); export("palm", [export_ob])

# ---------------- ground cover: low clumps of broad leaves and grass ----------------
fresh(); rng = random.Random(31); g = Geo()
for k in range(9):
    az = k*2*math.pi/9 + rng.uniform(-.3, .3)
    g.blade(Vector((0,0,.01)), Vector((math.cos(az), math.sin(az), rng.uniform(.4, 1.1))), rng.uniform(.16, .26), rng.uniform(.05, .08), droop=.6, fold=.15, segs=5, cols=2, m=0)
for k in range(26):
    az = rng.uniform(0, 6.28); r = rng.uniform(0, .08)
    base = Vector((math.cos(az)*r, math.sin(az)*r, 0))
    g.blade(base, Vector((math.cos(az)*.25, math.sin(az)*.25, 1)), rng.uniform(.18, .34), .012, droop=.25, fold=0, segs=4, cols=1, m=1, profile=lambda s: 1 - s)
export("groundcover", [g.build("groundcover", [LEAF(), M("leaf_grass", (0.16, 0.26, 0.06), .6)])])

# ---------------- fallen mossy log with a few ferns ----------------
fresh(); rng = random.Random(37); g = Geo()
L = 4.2; pts = [Vector((i/12*L - L/2, .08*math.sin(i*.9), .3 + .05*math.sin(i*1.3))) for i in range(13)]
g.tube(pts, [.33 - .06*abs(i-6)/6 for i in range(13)], sides=14, m=0)
for k in range(3):
    base = pts[3 + k*3] + Vector((0, 0, .28))
    for j in range(8):
        az = j*2*math.pi/8 + rng.uniform(-.2, .2)
        g.frond(base, az, math.radians(rng.uniform(25, 55)), rng.uniform(.4, .6), 1.0, rng, 1, 2, steps=12, leaf_len=.5, w=.08)
def log_tint(co):
    m = max(0.0, min(1.0, (co.z - .35) * 3.0))
    return (0.9 - 0.5*m, 0.8 + 0.3*m, 0.7 - 0.35*m)
export("log", [g.build("log", [M("bark", (0.42, 0.34, 0.27), 0.9), LEAF2(), STEM()], tint=log_tint)])

# ---------------- banana ----------------
fresh(); rng = random.Random(7); g = Geo()
stem_pts = [Vector((0, 0, i/8*1.7)) for i in range(9)]
g.tube(stem_pts, [0.14 - 0.03*i/8 for i in range(9)], sides=10, m=1)
for i in range(8):
    az = i*2.4 + rng.uniform(-.2, .2); el = math.radians(rng.uniform(35, 75))
    base = Vector((0, 0, 1.6 + rng.uniform(0, .25)))
    pet_end = base + Vector((math.cos(az)*.25, math.sin(az)*.25, .3))
    g.tube([base, (base+pet_end)/2 + Vector((0,0,.05)), pet_end], [.035, .03, .025], sides=5, m=1, cap=False)
    d = Vector((math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)))
    tears = {j for j in range(16) if rng.random() < .22}
    g.blade(pet_end, d, rng.uniform(1.6, 2.2), rng.uniform(.38, .48), droop=rng.uniform(.5, .9), fold=.18, segs=16, cols=6,
            profile=lambda s: (math.sin(math.pi*s)**0.35)*(1 - .25*s), m=0, drop=lambda a, b, t=tears: a in t and b in (0, 5) and a > 2)
export("banana", [g.build("banana", [LEAF2(), STEM()])])

# ---------------- monstera ----------------
fresh(); rng = random.Random(11); g = Geo()
for i in range(9):
    az = i*2.4 + rng.uniform(-.3, .3); r = rng.uniform(.5, .9)
    top = Vector((math.cos(az)*r*.5, math.sin(az)*r*.5, rng.uniform(.6, 1.1)))
    g.tube([Vector((0,0,0)), Vector((top.x*.3, top.y*.3, top.z*.6)), top], [.025, .022, .018], sides=5, m=1, cap=False)
    d = Vector((math.cos(az), math.sin(az), rng.uniform(-.1, .4)))
    holes = {(a, b) for a in range(3, 12) for b in (0, 1, 8, 9) if (a + b) % 3 == 0}
    inner = {(a, b) for a in range(4, 11) for b in (3, 6) if (a % 3 == 1) and rng.random() < .7}
    g.blade(top, d, rng.uniform(.6, .85), rng.uniform(.33, .42), droop=.55, fold=.1, segs=14, cols=10,
            profile=lambda s: (math.sin(math.pi*min(1, s*1.05 + .08))**0.5), m=0, drop=lambda a, b, h=holes, n=inner: (a, b) in h or (a, b) in n)
export("monstera", [g.build("monstera", [LEAF3(), STEM()])])

# ---------------- fern ----------------
fresh(); rng = random.Random(5); g = Geo()
for i in range(18):
    az = i*2*math.pi/18 + rng.uniform(-.15, .15)
    g.frond(Vector((0,0,.05)), az, math.radians(rng.uniform(45, 75)), rng.uniform(.9, 1.3), rng.uniform(.9, 1.2), rng, 0, 1, steps=22, leaf_len=.5, w=.08)
export("fern", [g.build("fern", [LEAF2(), STEM()])])

# ---------------- colocasia (elephant ear) ----------------
fresh(); rng = random.Random(13); g = Geo()
for i in range(6):
    az = i*2.4 + rng.uniform(-.3, .3); hgt = rng.uniform(1.0, 1.6)
    top = Vector((math.cos(az)*.35, math.sin(az)*.35, hgt))
    g.tube([Vector((0,0,0)), Vector((top.x*.2, top.y*.2, hgt*.6)), top], [.04, .032, .02], sides=6, m=1, cap=False)
    d = Vector((math.cos(az)*.6, math.sin(az)*.6, -.25))
    g.blade(top + Vector((0,0,.02)) - d.normalized()*.25, d, rng.uniform(.9, 1.15), rng.uniform(.4, .5), droop=.35, fold=.16, segs=12, cols=8,
            profile=lambda s: (0.75 + .25*math.cos(s*2.2))*(1 - s)**0.6 if s > .05 else .7, m=0)
export("colocasia", [g.build("colocasia", [LEAF(), STEM()])])

# ---------------- giant rainforest tree ----------------
fresh(); rng = random.Random(17); g = Geo()
pts = [Vector((0.3*math.sin(i*.5), 0.3*math.cos(i*.4), i/24*26)) for i in range(25)]
g.tube(pts, [1.1 - .45*i/24 for i in range(25)], sides=16, m=0)
for k in range(7):  # buttress roots: flattened fins
    a = k*2*math.pi/7 + rng.uniform(-.2, .2); dr = Vector((math.cos(a), math.sin(a), 0))
    rp = [Vector((0,0,3.2)) + dr*.5, dr*1.4 + Vector((0,0,1.6)), dr*2.4 + Vector((0,0,.5)), dr*3.2 + Vector((0,0,-.1))]
    g.tube(rp, [.55, .45, .3, .12], sides=8, flat=.28, m=0)
for k in range(5):  # moss patches / epiphyte ferns along the trunk
    z = rng.uniform(4, 16); a = rng.uniform(0, 6.28)
    base = Vector((math.cos(a)*.95, math.sin(a)*.95, z))
    for j in range(7):
        az = a + rng.uniform(-1.1, 1.1)
        g.frond(base, az, math.radians(rng.uniform(10, 50)), rng.uniform(.6, .9), 1.0, rng, 1, 1, steps=14, leaf_len=.45, w=.07)
def moss_tint(co):
    m = max(0.0, min(1.0, 1.0 - co.z / 5.0)) * (0.6 + 0.4 * math.sin(co.x * 3.1 + co.y * 2.3))
    return (0.95 - 0.45 * m, 0.85 + 0.25 * m, 0.75 - 0.35 * m)
export("tree", [g.build("tree", [M("bark", (0.42, 0.34, 0.27), 0.9), MOSS()], tint=moss_tint)])

# ---------------- hanging liana ----------------
fresh(); rng = random.Random(19); g = Geo()
for v in range(3):
    ox = v*.35 - .35; L = rng.uniform(7, 10)
    pts = [Vector((ox + .25*math.sin(i*.7 + v), .2*math.cos(i*.5 + v), -i/20*L)) for i in range(21)]
    g.tube(pts, [.035]*21, sides=5, m=1, cap=False)
    for i in range(2, 20):
        if rng.random() < .65:
            p = pts[i]; az = rng.uniform(0, 6.28)
            g.blade(p, Vector((math.cos(az), math.sin(az), -.6)), .22, .09, droop=.2, segs=4, cols=2, m=0)
export("liana", [g.build("liana", [LEAF(), STEM()])])

# ---------------- mossy rock (bottle pedestal) ----------------
fresh()
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
rock = bpy.context.active_object; rock.name = "rock"; rock.scale = (1.4, 1.1, .7)
tx = bpy.data.textures.new("rk", 'CLOUDS'); tx.noise_scale = .6
dm = rock.modifiers.new("d", 'DISPLACE'); dm.texture = tx; dm.strength = .35
bpy.ops.object.modifier_apply(modifier="d"); bpy.ops.object.transform_apply(scale=True)
me = rock.data
for v in me.vertices:
    if v.co.z > .25: v.co.z = .25 + (v.co.z - .25)*.15  # flat top for the bottle
me.materials.append(M("rock", (0.18, 0.17, 0.14), .9)); me.materials.append(MOSS())
for p in me.polygons: p.material_index = 1 if p.normal.z > .55 else 0
bpy.ops.object.shade_smooth(); bake_ao(rock); export("rock", [rock])

# ---------------- yeema oil bottle (same model as the renders) ----------------
fresh()
mats = lib.materials()
root, dropper = lib.oil_bottle(S, mats)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
export("bottle", objs)
print("JUNGLE DONE")
