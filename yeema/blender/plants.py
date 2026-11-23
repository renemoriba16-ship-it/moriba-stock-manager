# Procedural African plants for yeema: coconut palms (sway loops), baobab, aloe, savanna grass, frond shadow
import sys, os, math, random, bpy
from mathutils import Vector, Quaternion
S = sys.argv[1]; WHAT = sys.argv[2].split(",")
sys.path.insert(0, S + "/blend")
from lib import reset, setup_render, mat, area, camera, empty, key
OUT = S + "/render/plants/"; os.makedirs(OUT, exist_ok=True)

def leaf_mat(name, col, trans_col, mix=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = 0.55
    t = nt.nodes.new("ShaderNodeBsdfTranslucent"); t.inputs["Color"].default_value = (*trans_col, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = mix
    nt.links.new(p.outputs[0], mx.inputs[1]); nt.links.new(t.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    return m

def bark_mat(name, col, scale=(1, 1, 18), bump=0.6):
    m = mat(name, base=col, rough=0.85); nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = scale
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 8
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = bump
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], nz.inputs[0]); nt.links.new(nz.outputs[0], bm.inputs["Height"])
    nt.links.new(bm.outputs[0], p.inputs["Normal"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (col[0]*.55, col[1]*.55, col[2]*.55, 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(nz.outputs[0], ramp.inputs[0]); nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    return m

def tube(name, pts, radii, sides=12, flat=1.0, material=None, origin=Vector((0,0,0)), smooth=True, cap=True):
    verts, faces = [], []
    n_pts = len(pts); n = None
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = (pts[min(i+1, n_pts-1)] - pts[max(i-1, 0)]).normalized()
        if n is None:
            up = Vector((0,0,1)) if abs(t.z) < 0.95 else Vector((1,0,0))
            n = t.cross(up).normalized()
        else:  # parallel transport: no twisting along the tube
            n = (n - t*n.dot(t)).normalized()
        b = t.cross(n).normalized()
        for k in range(sides):
            a = 2*math.pi*k/sides
            verts.append(tuple(p - origin + r*(math.cos(a)*n + flat*math.sin(a)*b)))
    for i in range(n_pts-1):
        for k in range(sides):
            a, b2 = i*sides + k, i*sides + (k+1) % sides
            faces.append((a, b2, b2+sides, a+sides))
    if cap:
        verts.append(tuple(pts[-1] - origin)); c = len(verts)-1
        for k in range(sides): faces.append(((n_pts-1)*sides + k, (n_pts-1)*sides + (k+1) % sides, c))
        verts.append(tuple(pts[0] - origin)); c0 = len(verts)-1
        for k in range(sides): faces.append((k, c0, (k+1) % sides))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if smooth: me.shade_smooth()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.location = origin
    if material: me.materials.append(material)
    return ob

# ---------------- PALM ----------------
def frond_mesh(name, C, az, el, L, droop, rng, material):
    verts, faces = [], []
    dirh = Vector((math.cos(az), math.sin(az), 0))
    side = Vector((-math.sin(az), math.cos(az), 0))
    def spine(s):
        return C + dirh*(s*L*math.cos(el)) + Vector((0,0, s*L*math.sin(el) - droop*(s**2)*L))
    steps = 44
    for i in range(1, steps):
        s = i/steps; p = spine(s); p2 = spine(min(1, s + 1/steps))
        sd = (p2 - p).normalized()
        l = (0.75*math.sin(math.pi*min(1, s*1.08))**0.8 + 0.06) * L/2.6 * rng.uniform(0.85, 1.1)
        for sg in (-1, 1):
            if rng.random() < 0.06: continue  # a few missing leaflets look natural
            d = (side*sg*0.78 + sd*0.42 + Vector((0,0,-0.48 - 0.25*s))).normalized()
            w = 0.07*L/2.6
            tip = p + d*l
            mid = p + d*l*0.5 + Vector((0,0,0.03))
            base_i = len(verts)
            verts += [tuple(p - C), tuple(p + sd*w - C), tuple(mid + sd*w*0.6 - C), tuple(mid - C), tuple(tip - C)]
            faces += [(base_i, base_i+1, base_i+2, base_i+3), (base_i+3, base_i+2, base_i+4)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.location = C
    me.materials.append(material)
    # rachis (stem)
    pts = [spine(i/20) for i in range(21)]
    st = tube(name + "_stem", pts, [0.035*(1 - i/22) + 0.006 for i in range(21)], sides=6, material=material, origin=C)
    st.parent = ob; st.location = (0,0,0)
    return ob

def palm(seed, height=6.0, lean=1.3, n_fronds=18):
    rng = random.Random(seed)
    root = empty(f"Palm{seed}")
    trunk_m = bark_mat("Trunk", (0.27, 0.21, 0.16), scale=(1,1,26), bump=1.2)
    pts, radii = [], []
    for i in range(41):
        z = i/40*height
        x = lean*(z/height)**1.8; y = 0.25*lean*math.sin(z/height*math.pi)
        pts.append(Vector((x, y, z))); radii.append(0.24 - 0.08*(z/height) + 0.012*math.sin(z*9) + (0.08*(1 - z/height*4) if z < height/4 else 0))
    tr = tube("Trunk", pts, radii, sides=16, material=trunk_m); tr.parent = root
    C = pts[-1] + Vector((0,0,0.05))
    greens = [leaf_mat(f"Leaf{i}", c, t) for i, (c, t) in enumerate([
        ((0.07, 0.16, 0.035), (0.35, 0.55, 0.08)), ((0.10, 0.19, 0.04), (0.45, 0.6, 0.1)),
        ((0.13, 0.18, 0.045), (0.55, 0.55, 0.12)), ((0.22, 0.2, 0.07), (0.6, 0.45, 0.1))])]
    fronds = []
    for i in range(n_fronds):
        az = i*2*math.pi/n_fronds + rng.uniform(-.2, .2)
        old = rng.random()
        el = math.radians(rng.uniform(10, 55) - 30*old)
        L = rng.uniform(2.6, 3.3)
        f = frond_mesh(f"Frond{i}", C, az, el, L, droop=rng.uniform(0.55, 0.9) + 0.4*old, rng=rng, material=greens[min(3, int(old*3.2))])
        f.parent = root; fronds.append((f, az, rng.random()*6.28, rng.uniform(0.8, 1.2)))
    # coconuts
    nut = mat("Coconut", base=(0.32, 0.2, 0.08), rough=0.6)
    for k in range(5):
        a = k*2*math.pi/5 + rng.uniform(-.3, .3)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=C + Vector((0.2*math.cos(a), 0.2*math.sin(a), -0.28 - rng.uniform(0, .12))))
        c = bpy.context.active_object; c.scale = (1, 1, 1.15); bpy.ops.object.shade_smooth(); c.data.materials.append(nut); c.parent = root
    return root, fronds, C

def animate_palm(root, fronds, N, wind=math.radians(-20), amp=math.radians(7)):
    for f in range(1, N+1):
        t = (f-1)/N*2*math.pi
        for (ob, az, ph, k) in fronds:
            axis = Vector((-math.sin(az), math.cos(az), 0))
            ang = amp*k*math.sin(t + ph) + math.radians(4)*math.cos(az - wind)*math.sin(t)
            yaw = math.radians(3)*k*math.sin(2*t + ph)
            q = Quaternion(Vector((0,0,1)), yaw) @ Quaternion(axis, ang)
            ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = q; ob.keyframe_insert("rotation_quaternion", frame=f)
        root.rotation_euler = (math.radians(1.2)*math.sin(t), math.radians(0.8)*math.sin(t + 1), 0); root.keyframe_insert("rotation_euler", frame=f)

def sun_setup(res, samples=24):
    sc = setup_render(res=res, samples=samples, bg=(0.85, 0.62, 0.42), world_strength=0.9)
    s = bpy.data.lights.new("Sun", 'SUN'); s.energy = 4.0; s.color = (1.0, 0.78, 0.55); s.angle = math.radians(3)
    so = bpy.data.objects.new("Sun", s); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(62), 0, math.radians(-125))
    area("Back", (2, 8, 6), (0, 0, 4), energy=1500, size=6, color=(1.0, 0.7, 0.4))
    return sc

if "palm" in WHAT:
    for seed, lean, name in [(3, 1.4, "palm_a"), (11, -1.0, "palm_b")]:
        reset(); sc = sun_setup((860, 1120), samples=20)
        root, fronds, C = palm(seed, lean=lean)
        N = 48; sc.frame_start, sc.frame_end = 1, N
        animate_palm(root, fronds, N)
        cam = camera((C.x*0.55, -13.0, 3.4), (C.x*0.55, 0, 4.0), lens=44)
        sc.render.filepath = OUT + name + "/f_"
        bpy.ops.render.render(animation=True)
        bpy.ops.wm.save_as_mainfile(filepath=S + f"/blend/yeema_{name}.blend")

if "palmtest" in WHAT:
    reset(); sc = sun_setup((720, 1120), samples=16)
    root, fronds, C = palm(3, lean=1.4)
    animate_palm(root, fronds, 48)
    camera((C.x*0.55, -13.0, 3.4), (C.x*0.55, 0, 4.0), lens=44)
    sc.frame_set(1); sc.render.filepath = OUT + "palmtest.png"; bpy.ops.render.render(write_still=True)

# ---------------- BAOBAB ----------------
def branch(name, start, direction, length, r0, depth, rng, m, leaf_m, objs):
    pts, radii = [], []; p = Vector(start); d = Vector(direction).normalized()
    for i in range(9):
        pts.append(p.copy()); radii.append(r0*(1 - 0.6*i/8))
        d = (d + Vector((rng.uniform(-.25,.25), rng.uniform(-.25,.25), rng.uniform(-.05,.2)))).normalized()
        p = p + d*length/8
    objs.append(tube(name, pts, radii, sides=10, material=m))
    if depth > 0:
        for k in range(rng.choice([2, 3])):
            nd = (d + Vector((rng.uniform(-.9,.9), rng.uniform(-.9,.9), rng.uniform(0.1,.6)))).normalized()
            branch(name + f"_{k}", pts[-1], nd, length*0.55, radii[-1]*0.9, depth-1, rng, m, leaf_m, objs)
    else:
        for k in range(rng.randint(2, 4)):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.18, 0.32), location=pts[-1] + Vector((rng.uniform(-.25,.25), rng.uniform(-.25,.25), rng.uniform(0,.2))))
            l = bpy.context.active_object; l.scale = (1.3, 1.3, 0.6); l.data.materials.append(leaf_m)
            dm = l.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("lv", 'CLOUDS'); tx.noise_scale = 0.12; dm.texture = tx; dm.strength = 0.25
            objs.append(l)

if "baobab" in WHAT:
    reset(); sc = sun_setup((1400, 1050), samples=48)
    rng = random.Random(5)
    bark = bark_mat("Bark", (0.46, 0.38, 0.33), scale=(2, 2, 0.6), bump=0.5)
    leaf_m = leaf_mat("BLeaf", (0.12, 0.2, 0.05), (0.4, 0.5, 0.1))
    prof = [(1.35, 0), (1.25, 0.25), (1.15, 1.0), (1.05, 2.0), (0.95, 3.0), (0.8, 3.6), (0.55, 4.0), (0.0, 4.15)]
    pts = [Vector((0, 0, z)) for r, z in prof]
    tr = tube("BTrunk", pts, [r for r, z in prof], sides=40, material=bark)
    sub = tr.modifiers.new("s", 'SUBSURF'); sub.levels = sub.render_levels = 2
    dm = tr.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("bark", 'CLOUDS'); tx.noise_scale = 0.5; dm.texture = tx; dm.strength = 0.18
    objs = []
    for k in range(7):
        a = k*2*math.pi/7 + rng.uniform(-.3, .3)
        st = Vector((0.45*math.cos(a), 0.45*math.sin(a), 3.75))
        branch(f"Br{k}", st, (math.cos(a)*0.9, math.sin(a)*0.9, 0.55), rng.uniform(1.6, 2.3), 0.26, 2, rng, bark, leaf_m, objs)
    camera((0, -16, 2.6), (0, 0, 3.0), lens=50)
    sc.render.filepath = OUT + "baobab.png"; bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=S + "/blend/yeema_baobab.blend")

# ---------------- ALOE + GRASS ----------------
def aloe(rng, loc=Vector((0,0,0)), n=17, scale=1.0, material=None):
    obs = []
    for i in range(n):
        az = i*2.399 + rng.uniform(-.1, .1)  # golden-angle rosette
        inner = 1 - i/n
        el = math.radians(35 + 45*inner + rng.uniform(-6, 6))
        L = scale*(0.7 + 0.65*(1 - inner*0.6))*rng.uniform(0.9, 1.1)
        pts, radii = [], []
        for s in [j/14 for j in range(15)]:
            d = Vector((math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)))
            p = loc + d*s*L + Vector((0, 0, -0.35*L*s*s*(1 - inner)))
            pts.append(p); radii.append(scale*0.11*(1 - s)**0.9 + 0.004)
        obs.append(tube(f"Aloe{i}", pts, radii, sides=10, flat=0.32, material=material))
    return obs

def aloe_mat():
    m = mat("AloeM", base=(0.2, 0.32, 0.24), rough=0.45, sss=0.15); nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    v = nt.nodes.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = 60
    r = nt.nodes.new("ShaderNodeValToRGB"); r.color_ramp.elements[0].position = 0.08; r.color_ramp.elements[0].color = (0.75, 0.8, 0.7, 1)
    r.color_ramp.elements[1].position = 0.12; r.color_ramp.elements[1].color = (0.18, 0.3, 0.22, 1)
    nt.links.new(v.outputs["Distance"], r.inputs[0]); nt.links.new(r.outputs[0], p.inputs["Base Color"])
    return m

def grass_tuft(rng, loc, n=70, h=1.0, mats=None):
    verts, faces, = [], []
    for i in range(n):
        a = rng.uniform(0, 2*math.pi); rr = rng.uniform(0, 0.25)
        base = loc + Vector((rr*math.cos(a), rr*math.sin(a), 0))
        lean = Vector((math.cos(a), math.sin(a), 0))*rng.uniform(0.2, 0.7)
        hh = h*rng.uniform(0.5, 1.2); w = 0.025
        side = Vector((-math.sin(a), math.cos(a), 0))
        bi = len(verts)
        for j in range(6):
            s = j/5; p = base + lean*hh*s*s + Vector((0,0,hh*s)); ww = w*(1 - s)
            verts += [tuple(p - side*ww), tuple(p + side*ww)]
        for j in range(5): faces.append((bi+2*j, bi+2*j+1, bi+2*j+3, bi+2*j+2))
    me = bpy.data.meshes.new("Grass"); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new("Grass", me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    for poly in me.polygons: poly.material_index = (poly.index // 5) % len(mats) if rng.random() > 0.3 else 0
    return ob

if "aloe" in WHAT:
    reset(); sc = sun_setup((1000, 800), samples=48)
    rng = random.Random(9)
    aloe(rng, material=aloe_mat())
    camera((0, -6.2, 2.2), (0, 0, 0.45), lens=120)
    sc.render.filepath = OUT + "aloe.png"; bpy.ops.render.render(write_still=True)

if "grass" in WHAT:
    reset(); sc = sun_setup((2400, 520), samples=32)
    rng = random.Random(2)
    gm = [leaf_mat("G1", (0.55, 0.42, 0.2), (0.8, 0.6, 0.25), 0.3), leaf_mat("G2", (0.42, 0.36, 0.15), (0.7, 0.55, 0.2), 0.3), leaf_mat("G3", (0.2, 0.25, 0.08), (0.5, 0.6, 0.15), 0.3)]
    for k in range(40):
        grass_tuft(rng, Vector((-11.4 + k*0.585 + rng.uniform(-.25, .25), rng.uniform(-.3, .8), 0)), n=rng.randint(70, 120), h=rng.uniform(0.55, 1.5), mats=gm)
    c = camera((0, -26, 0.8), (0, 0, 0.7), lens=50); c.data.type = 'ORTHO'; c.data.ortho_scale = 23.5
    sc.render.filepath = OUT + "grass.png"; bpy.ops.render.render(write_still=True)

if "shadow" in WHAT:
    reset(); sc = setup_render(res=(1600, 1600), samples=8, bg=(1,1,1), world_strength=0)
    blk = mat("Black", base=(0,0,0), rough=1)
    rng = random.Random(4)
    for i, (az, L) in enumerate([(0.3, 3.1), (1.9, 2.8), (3.5, 3.0), (-1.2, 2.6)]):
        frond_mesh(f"F{i}", Vector((0,0,0)), az, 0.0, L, droop=0.0, rng=rng, material=blk)
    for ob in bpy.data.objects:
        if ob.type == 'MESH': ob.visible_shadow = False
    em = bpy.data.lights.new("L", 'SUN'); eo = bpy.data.objects.new("L", em); bpy.context.collection.objects.link(eo)
    c = camera((0, 0, 20), (0, 0, 0), lens=50); c.data.type = 'ORTHO'; c.data.ortho_scale = 6.8
    sc.render.filepath = OUT + "shadow.png"; bpy.ops.render.render(write_still=True)
print("PLANTS DONE", WHAT)
