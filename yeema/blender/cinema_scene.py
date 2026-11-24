# yeema — film-quality jungle for the "cinema 3D photos" opening.
# Builds one Cycles scene (scanned Poly Haven plants + yeema's own Blender plants), renders 5 shots
# along the trail, then re-renders each shot as a depth map for the browser parallax effect.
import sys, os, math, random, bpy
from mathutils import Vector
S, OUT, RES, SAMPLES, SHOTS = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
D3 = '/home/user/moriba-stock-manager/yeema/assets/3d'
PH = S + '/ph'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rng = random.Random(42)
W, H = map(int, RES.split('x'))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .04; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4; sc.cycles.volume_max_steps = 256
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'

# ---------------- asset library as collection instances ----------------
LIB = {}
OWN = {'leaf': (0.10, 0.24, 0.07), 'leaf_light': (0.20, 0.36, 0.08), 'leaf_dark': (0.04, 0.13, 0.05), 'stem': (0.22, 0.32, 0.12),
       'bark': (0.42, 0.34, 0.27), 'moss': (0.12, 0.22, 0.05), 'leaf_hib': (0.05, 0.16, 0.04), 'petal_red': (0.85, 0.03, 0.06),
       'petal_gold': (0.95, 0.65, 0.08), 'leaf_orc': (0.07, 0.2, 0.06), 'petal_pink': (0.92, 0.45, 0.7), 'petal_white': (0.95, 0.92, 0.95),
       'petal_lip': (0.75, 0.1, 0.35), 'leaf_grass': (0.16, 0.26, 0.06)}
def leaf_material(m, mix=.4):
    nt = m.node_tree
    col = (*OWN.get(m.name.split('.')[0], (0.12, 0.25, 0.07)), 1)
    leafy = 'leaf' in m.name or 'petal' in m.name
    nt.nodes.clear(); o = nt.nodes.new("ShaderNodeOutputMaterial")
    pb = nt.nodes.new("ShaderNodeBsdfPrincipled"); pb.inputs["Base Color"].default_value = col; pb.inputs["Roughness"].default_value = .45; pb.inputs["Coat Weight"].default_value = .12
    ca = nt.nodes.new("ShaderNodeVertexColor"); mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    mul.inputs[6].default_value = (*col[:3], 1); nt.links.new(ca.outputs[0], mul.inputs[7])
    nt.links.new(mul.outputs[2], pb.inputs["Base Color"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = (min(1, col[0] * 2.2 + .05), min(1, col[1] * 2.2 + .08), col[2] * 1.5, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = mix
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 40; wv.inputs["Distortion"].default_value = 3
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = .12
    nt.links.new(wv.outputs[1], bm.inputs["Height"]); nt.links.new(bm.outputs[0], pb.inputs["Normal"])
    nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    if not leafy:   # bark, stems, moss: opaque, rougher, no translucency
        mx.inputs[0].default_value = 0; pb.inputs["Roughness"].default_value = .85; pb.inputs["Coat Weight"].default_value = 0; bm.inputs["Strength"].default_value = .35

def make_lib(key, path, keep=None, scale=1.0, own=False):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and (keep is None or o.name in keep)]
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        o.matrix_world = o.matrix_world.copy(); o.parent = None
        bpy.context.view_layer.objects.active = o
    for o in bpy.context.scene.objects: o.select_set(o in meshes)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for o in meshes for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    coll = bpy.data.collections.new("SRC_" + key)
    for o in meshes:
        for v in o.data.vertices: v.co = (v.co - off) * scale
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
        if own:
            for m in o.data.materials:
                if m and m.name.split('.')[0] in OWN and not m.get('done'):
                    leaf_material(m, mix=.25 if 'petal' in m.name else .4); m['done'] = 1
    LIB[key] = coll
    return coll

def put(key, loc, s=1.0, rz=None, rx=0.0, ry=0.0):
    e = bpy.data.objects.new(key, None); e.instance_type = 'COLLECTION'; e.instance_collection = LIB[key]
    e.location = loc; e.scale = (s, s, s); e.rotation_euler = (rx, ry, rz if rz is not None else rng.uniform(0, 6.28))
    sc.collection.objects.link(e); return e

for k in ['tree', 'palm', 'banana', 'monstera', 'colocasia', 'liana', 'hibiscus', 'orchid', 'fern', 'groundcover', 'butterfly']:
    make_lib(k, f"{D3}/{k}.glb", own=True)
PHL = [('anth_a', 'anthurium_botany_01', ['anthurium_botany_01_a']), ('anth_c', 'anthurium_botany_01', ['anthurium_botany_01_c']),
       ('cal_a', 'calathea_orbifolia_01', ['calathea_orbifolia_01_a']), ('cal_b', 'calathea_orbifolia_01', ['calathea_orbifolia_01_b']),
       ('fern_b', 'fern_02', ['fern_02_b']), ('fern_c', 'fern_02', ['fern_02_c']),
       ('pach_d', 'pachira_aquatica_01', ['pachira_aquatica_01_bark_d', 'pachira_aquatica_01_leaves_d']),
       ('pach_c', 'pachira_aquatica_01', ['pachira_aquatica_01_bark_c', 'pachira_aquatica_01_leaves_c']),
       ('rock_a', 'rock_moss_set_02', ['rock_moss_set_02_rock11']), ('rock_b', 'rock_moss_set_02', ['rock_moss_set_02_rock13']),
       ('rock_c', 'rock_moss_set_02', ['rock_moss_set_02_rock10']), ('stump', 'tree_stump_01', None), ('trunk', 'dead_tree_trunk', None)]
for key, asset, keep in PHL:
    make_lib(key, f"{PH}/{asset}/{asset}_1k.gltf", keep=keep)

# ---------------- ground: photographed forest floor ----------------
bpy.ops.mesh.primitive_plane_add(size=140, location=(0, -20, 0)); g = bpy.context.active_object
sub = g.modifiers.new("s", 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 6
dm = g.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("gn", 'CLOUDS'); tx.noise_scale = 3; dm.texture = tx; dm.strength = .35
gm = bpy.data.materials.new("Floor"); gm.use_nodes = True; nt = gm.node_tree; p = nt.nodes.get("Principled BSDF")
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (46, 46, 46)
nt.links.new(tc.outputs["UV"], mp.inputs[0])
def img(path, non_color=False):
    n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(path)
    if non_color: n.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(mp.outputs[0], n.inputs[0]); return n
dif = img(f"{PH}/tex/forest_leaves_02_diff.jpg"); nor = img(f"{PH}/tex/forest_leaves_02_nor.jpg", True); rou = img(f"{PH}/tex/forest_leaves_02_rough.jpg", True)
hue = nt.nodes.new("ShaderNodeHueSaturation"); hue.inputs["Hue"].default_value = .54; hue.inputs["Saturation"].default_value = .75; hue.inputs["Value"].default_value = .55
nt.links.new(dif.outputs[0], hue.inputs["Color"]); nt.links.new(hue.outputs[0], p.inputs["Base Color"]); nt.links.new(rou.outputs[0], p.inputs["Roughness"])
nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.2; nt.links.new(nor.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], p.inputs["Normal"])
g.data.materials.append(gm)

# ---------------- jungle layout along a winding trail ----------------
trail_x = lambda y: .8 * math.sin(y * .12)
CLEAR = Vector((0, -46, 0))
def scatter(key, n, dmin, dmax, s, y0=10, y1=-60, z=0.0, clear_r=3.4, tilt=.05):
    k = 0; guard = 0
    while k < n and guard < n * 80:
        guard += 1; y = rng.uniform(y1, y0); side = rng.choice((-1, 1)); x = trail_x(y) + side * rng.uniform(dmin, dmax)
        if (Vector((x, y, 0)) - CLEAR).length < clear_r: continue
        put(key, (x, y, z if not callable(z) else z()), rng.uniform(*s), rx=rng.uniform(-tilt, tilt), ry=rng.uniform(-tilt, tilt)); k += 1
scatter('tree', 26, 4.5, 16, (.9, 1.3), clear_r=7)
scatter('palm', 30, 2.6, 13, (.8, 1.15), tilt=.1)
scatter('banana', 40, 2.1, 10, (.9, 1.4))
scatter('pach_d', 18, 2.2, 11, (2.4, 3.4)); scatter('pach_c', 18, 2.2, 11, (2.6, 3.6))
scatter('monstera', 36, 1.6, 9, (.9, 1.6)); scatter('colocasia', 30, 1.4, 9, (.9, 1.5))
scatter('anth_a', 40, 1.0, 9, (2.4, 3.4)); scatter('anth_c', 30, 1.0, 9, (2.4, 3.4))
scatter('cal_a', 40, .9, 9, (2.2, 3.2)); scatter('cal_b', 34, .9, 9, (2.2, 3.2))
scatter('fern_b', 70, .7, 10, (1.6, 2.6)); scatter('fern_c', 60, .7, 10, (1.6, 2.6)); scatter('fern', 50, .8, 10, (.8, 1.4))
scatter('hibiscus', 26, 1.3, 8, (.9, 1.4)); scatter('orchid', 34, .9, 7, (1.3, 1.9))
scatter('groundcover', 260, .6, 12, (.9, 1.7), tilt=.12)
scatter('rock_a', 10, 1.8, 10, (.6, 1.3), tilt=.15); scatter('rock_b', 8, 1.8, 10, (.6, 1.2), tilt=.15)
scatter('stump', 6, 2.0, 9, (1.0, 1.5)); scatter('trunk', 8, 2.0, 9, (1.2, 1.8))
scatter('liana', 50, 1.0, 8, (.9, 1.2), z=lambda: rng.uniform(8, 12), tilt=0)
for i in range(70):   # canopy: giant fronds high above, they break the sun into rays
    y = rng.uniform(-62, 12); put('fern', (trail_x(y) + rng.uniform(-14, 14), y, rng.uniform(12, 17)), rng.uniform(6, 9), rx=rng.uniform(-.15, .15), ry=rng.uniform(-.15, .15))
# a ring of scanned plants around the clearing
for i in range(18):
    a = i / 18 * 6.28
    if abs(math.sin(a) - 1) < .3: continue
    r = rng.uniform(2.6, 4.4); put(rng.choice(['anth_a', 'cal_a', 'fern_b', 'cal_b', 'anth_c']), (CLEAR.x + math.cos(a) * r, CLEAR.y + math.sin(a) * r, 0), rng.uniform(2.4, 3.2))

for i in range(16):   # dense foliage right behind the bottle, it melts into bokeh
    put(rng.choice(['anth_a', 'cal_a', 'cal_b', 'fern_b', 'anth_c', 'monstera']), (CLEAR.x + rng.uniform(-1.6, 1.6), CLEAR.y + rng.uniform(.9, 2.6), 0), rng.uniform(2.2, 3.2))
# ---------------- hero: real-size bottle on a mossy scanned rock in the clearing ----------------
put('rock_c', (CLEAR.x, CLEAR.y, -.05), .32, rz=.3)['hero'] = 1
bpy.context.view_layer.update()
inst = [o for o in sc.objects if o.instance_collection == LIB['rock_c']][0]
pts = [inst.matrix_world @ Vector(v.co) for o2 in LIB['rock_c'].objects for v in o2.data.vertices]
near = [p.z for p in pts if (p.x - CLEAR.x) ** 2 + (p.y - CLEAR.y) ** 2 < .12 ** 2] or [p.z for p in pts if (p.x - CLEAR.x) ** 2 + (p.y - CLEAR.y) ** 2 < .3 ** 2]
rock_top = max(near)
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{D3}/bottle.glb")
broots = [o for o in bpy.data.objects if o not in before and o.parent is None]
for o in broots:
    o.scale = (.062, .062, .062); o.location = (CLEAR.x, CLEAR.y, rock_top - .006); o.rotation_euler.z = math.radians(-8)
bpy.context.view_layer.update()
bm_ = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
cx = sum((o.matrix_world @ Vector(c)).x for o in bm_ for c in o.bound_box) / (8 * len(bm_)); cy = sum((o.matrix_world @ Vector(c)).y for o in bm_ for c in o.bound_box) / (8 * len(bm_))
for o in broots: o.location.x += CLEAR.x - cx; o.location.y += CLEAR.y - cy   # re-centre after turning the label to camera
for o in [o for o in bpy.data.objects if o not in before and o.type == 'MESH']:
    for m in o.data.materials:
        p = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
        if p and p.inputs["Transmission Weight"].default_value > .5: p.inputs["Roughness"].default_value = .02

# butterflies resting on flowers + one perched macaw
# hero plants for the close-up: a scanned anthurium in front of calatheas and ferns
for e in [put('anth_a', (-1.3, -17.4, 0), 1.9, rz=2.2), put('cal_a', (-2.3, -18.9, 0), 2.6), put('fern_b', (-.3, -19.3, 0), 2.2), put('anth_c', (-2.8, -17.6, 0), 2.2)]: e['hero'] = 1
for o in LIB['butterfly'].objects:
    for m in o.data.materials:
        if m and m.name.startswith('wing'):
            p = m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value = (0.02, 0.18, 0.95, 1); p.inputs["Metallic"].default_value = .4
            p.inputs["Emission Color"].default_value = (0.02, 0.15, 0.8, 1); p.inputs["Emission Strength"].default_value = .4

# ---------------- light: forest HDRI + sun through the canopy + volumetric haze ----------------
wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True; wn = wd.node_tree
env = wn.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(f"{PH}/hdri/forest_grove_2k.hdr")
bg = wn.nodes.get("Background"); bg.inputs[1].default_value = .55; wn.links.new(env.outputs[0], bg.inputs[0])
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 6.0; sun.color = (1.0, .86, .64); sun.angle = math.radians(1.2)
so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(38), math.radians(8), math.radians(170))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -22, 7)); vol = bpy.context.active_object; vol.name = "Haze"; vol.scale = (60, 90, 14)
vm = bpy.data.materials.new("Haze"); vm.use_nodes = True; vnt = vm.node_tree; vnt.nodes.remove(vnt.nodes.get("Principled BSDF"))
pv = vnt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = .028; pv.inputs["Anisotropy"].default_value = .62; pv.inputs["Color"].default_value = (.85, .95, .8, 1)
vnt.links.new(pv.outputs[0], vnt.nodes.get("Material Output").inputs["Volume"]); vol.data.materials.append(vm)
kl = bpy.data.lights.new("Key", 'AREA'); kl.energy = 14; kl.size = .6; kl.color = (1, .9, .78)
ko = bpy.data.objects.new("Key", kl); sc.collection.objects.link(ko); ko.location = (CLEAR.x - .6, CLEAR.y - .9, .75)
ko.rotation_euler = (Vector((CLEAR.x, CLEAR.y, .15)) - ko.location).to_track_quat('-Z', 'Y').to_euler()

# ---------------- the five shots ----------------
cam = bpy.data.cameras.new("Cam"); cam.dof.use_dof = True
co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
SHOT = {
    1: dict(loc=(trail_x(9) + .2, 9, 1.65), tgt=(trail_x(-4), -4, 2.4), lens=26, f=8, focus=None),        # entering the jungle
    2: dict(loc=(trail_x(-11) + .3, -11, .9), tgt=(1.5, -22, 5.5), lens=22, f=8, focus=None),            # looking up into the canopy and the light
    3: dict(loc=(-.45, -14.9, 1.15), tgt=(-1.3, -17.4, .7), lens=85, f=2.2, focus=(-1.3, -17.4, .7)),  # scanned anthurium close-up
    4: dict(loc=(trail_x(-33), -33, 1.55), tgt=(CLEAR.x, CLEAR.y, .7), lens=35, f=5.6, focus=None),     # light falls on the clearing
    5: dict(loc=(CLEAR.x + .12, CLEAR.y - 1.25, rock_top + .16), tgt=(CLEAR.x, CLEAR.y, rock_top + .07), lens=85, f=2.4, focus=(CLEAR.x, CLEAR.y, rock_top + .07)),  # the bottle
}
def clear_view(i, r=.75, length=1.8):
    """Remove scattered plants that would sit right against the lens."""
    d = SHOT[i]; a = Vector(d['loc']); b = Vector(d['tgt']); dv = (b - a).normalized()
    for o in list(sc.objects):
        if o.instance_type != 'COLLECTION' or o.get('hero') or o.location.z > 6: continue
        t = max(0.0, min(length, (o.location - a).dot(dv))); c = a + dv * t
        if math.hypot(o.location.x - c.x, o.location.y - c.y) < r: bpy.data.objects.remove(o, do_unlink=True)
for i in (1, 3, 4, 5): clear_view(i)
def aim(i):
    d = SHOT[i]; co.location = d['loc']; cam.lens = d['lens']; cam.dof.aperture_fstop = d['f']
    co.rotation_euler = (Vector(d['tgt']) - Vector(d['loc'])).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.focus_distance = (Vector(d['focus'] or d['tgt']) - Vector(d['loc'])).length if d['focus'] else 30
shots = [int(x) for x in SHOTS.split(',')]
for i in shots:
    aim(i); sc.render.filepath = f"{OUT}/shot{i}.png"; bpy.ops.render.render(write_still=True); print("RENDERED", i, flush=True)

# ---------------- depth maps (same cameras): every surface emits 1/(1+0.22·distance), cut-outs kept ----------------
vol.hide_render = True; bg.inputs[1].default_value = 0; sun.energy = 0
sc.cycles.samples = 6; sc.cycles.use_denoising = False; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = W // 2, H // 2
for m in bpy.data.materials:
    if not m.use_nodes or m.name == 'Haze': continue
    nt = m.node_tree; out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not out: continue
    alpha = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for l in nt.links:
                if l.to_node == n and l.to_socket.name == 'Alpha': alpha = l.from_socket
    cd = nt.nodes.new("ShaderNodeCameraData"); k = nt.nodes.new("ShaderNodeMath"); k.operation = 'MULTIPLY'; k.inputs[1].default_value = .22
    a1 = nt.nodes.new("ShaderNodeMath"); a1.operation = 'ADD'; a1.inputs[1].default_value = 1
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'DIVIDE'; inv.inputs[0].default_value = 1
    nt.links.new(cd.outputs['View Distance'], k.inputs[0]); nt.links.new(k.outputs[0], a1.inputs[0]); nt.links.new(a1.outputs[0], inv.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(inv.outputs[0], em.inputs['Strength']); em.inputs['Color'].default_value = (1, 1, 1, 1)
    shader = em.outputs[0]
    if alpha is not None:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(alpha, mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); shader = mx.outputs[0]
    for l in list(nt.links):
        if l.to_node == out: nt.links.remove(l)
    nt.links.new(shader, out.inputs['Surface'])
for i in shots:
    aim(i); cam.dof.use_dof = False; sc.render.filepath = f"{OUT}/shot{i}_depth.png"; bpy.ops.render.render(write_still=True); cam.dof.use_dof = True
    print("DEPTH", i, flush=True)
print("CINEMA DONE")
