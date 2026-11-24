# yeema — cinematic Cycles still of the clearing, built from the same Blender jungle models
import sys, math, random, bpy
from mathutils import Vector
S, D, OUT, RES, SAMPLES = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rng = random.Random(8)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .03
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 8; sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 4; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1
w, h = map(int, RES.split('x')); sc.render.resolution_x, sc.render.resolution_y = w, h
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'

def imp(name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{D}/{name}.glb")
    obs = [o for o in bpy.data.objects if o not in before]
    for o in obs: o.select_set(False)
    return [o for o in obs if o.parent is None], obs

def leaf_material(m, trans=(0.45, 0.6, 0.1), mix=.4):
    """Cinema leaves: diffuse + translucency so sunlight glows through, with subtle vein bump."""
    nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    if not p: return
    col = tuple(p.inputs["Base Color"].default_value)
    nt.nodes.clear(); o = nt.nodes.new("ShaderNodeOutputMaterial")
    pb = nt.nodes.new("ShaderNodeBsdfPrincipled"); pb.inputs["Base Color"].default_value = col; pb.inputs["Roughness"].default_value = .42
    pb.inputs["Coat Weight"].default_value = .15
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = (min(1, col[0] * 2.2 + .05), min(1, col[1] * 2.2 + .08), col[2] * 1.5, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = mix
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 40; wv.inputs["Distortion"].default_value = 3
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = .12
    nt.links.new(wv.outputs[1], bm.inputs["Height"]); nt.links.new(bm.outputs[0], pb.inputs["Normal"])
    nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])

def library(name):
    roots, obs = imp(name)
    for o in obs:
        if o.type == 'MESH':
            for m in o.data.materials:
                if m and (('leaf' in m.name or 'petal' in m.name) and not m.get('done')):
                    leaf_material(m, mix=.25 if 'petal' in m.name else .4); m['done'] = 1
    # hide the source and return a function that makes linked duplicates
    for o in obs: o.hide_render = True; o.hide_viewport = True
    def place(loc, s=1.0, rz=None):
        for o in [x for x in obs if x.type == 'MESH']:
            c = o.copy(); bpy.context.collection.objects.link(c); c.hide_render = False; c.hide_viewport = False; c.parent = None
            c.matrix_world = o.matrix_world.copy()
            c.location = Vector(loc) + c.location * s; c.scale = c.scale * s
            c.rotation_euler.z += rz if rz is not None else rng.uniform(0, 6.28)
    return place

P = {n: library(n) for n in ["tree", "palm", "banana", "monstera", "fern", "colocasia", "liana", "hibiscus", "orchid"]}

# ground: dark soil and moss with displacement
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); g = bpy.context.active_object
sub = g.modifiers.new("s", 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 6
dm = g.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("gn", 'CLOUDS'); tx.noise_scale = .6; dm.texture = tx; dm.strength = .12
gm = bpy.data.materials.new("Soil"); gm.use_nodes = True; nt = gm.node_tree; p = nt.nodes.get("Principled BSDF")
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 12
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.035, 0.03, 0.02, 1); cr.color_ramp.elements[1].color = (0.06, 0.1, 0.03, 1)
nt.links.new(nz.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = .95
g.data.materials.append(gm)

# hero: real-size bottle on a mossy rock
rr, robs = imp("rock")
def moss_rock(m, moss):
    nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60 if moss else 9; nz.inputs["Detail"].default_value = 15; nz.inputs["Roughness"].default_value = .7
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140
    cr = nt.nodes.new("ShaderNodeValToRGB")
    if moss:
        cr.color_ramp.elements[0].color = (0.01, 0.022, 0.006, 1); cr.color_ramp.elements[1].color = (0.07, 0.11, 0.02, 1)
        e = cr.color_ramp.elements.new(.5); e.color = (0.03, 0.06, 0.012, 1)
    else:
        cr.color_ramp.elements[0].color = (0.012, 0.012, 0.009, 1); cr.color_ramp.elements[1].color = (0.06, 0.055, 0.04, 1)
    nt.links.new(nz.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = .9 if moss else .5
    nt.links.new((vo.outputs["Distance"] if moss else nz.outputs[0]), bm.inputs["Height"]); nt.links.new(bm.outputs[0], p.inputs["Normal"])
    p.inputs["Roughness"].default_value = .95
    if moss: p.inputs["Sheen Weight"].default_value = 0; p.inputs["Sheen Tint"].default_value = (.5, .7, .3, 1)
for o in rr: o.scale = (.13, .13, .16); o.location = (0, 0, -.02)
for o in robs:
    if o.type == 'MESH':
        for m in o.data.materials:
            if m and not m.get('done'): moss_rock(m, 'moss' in m.name.lower()); m['done'] = 1
bpy.context.view_layer.update()
top = max((o.matrix_world @ Vector(v)).z for o in robs if o.type == 'MESH' for v in [vv.co for vv in o.data.vertices])
br, bobs = imp("bottle")
for o in br: o.scale = (.062, .062, .062); o.location = (0, 0, top - .004); o.rotation_euler.z = math.radians(-8)
for o in bobs:
    if o.type == 'MESH':
        for m in o.data.materials:
            p = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
            if p and p.inputs["Transmission Weight"].default_value > .5: p.inputs["Roughness"].default_value = .02

# jungle composition (metres): foreground ferns framing, mid ground flowers, deep background trees
for i in range(14):
    a = rng.uniform(0, 6.28); r = rng.uniform(.55, 1.6)
    if math.sin(a) < -.55 and r < 1.0: continue          # keep the lens side clear
    P["fern"]((math.cos(a) * r, math.sin(a) * r, 0), rng.uniform(.5, .9))
for (x, y) in [(-.42, -.55), (.5, -.62), (-.75, -.35)]: P["fern"]((x, y, 0), .55)   # out-of-focus foreground
for i in range(10): a = rng.uniform(0, 6.28); r = rng.uniform(.9, 2.2); P["orchid"]((math.cos(a) * r, math.sin(a) * r + .6, 0), rng.uniform(.9, 1.3))
for i in range(9): a = rng.uniform(0, 6.28); r = rng.uniform(1.4, 3); P["hibiscus"]((math.cos(a) * r, abs(math.sin(a)) * r + .8, 0), rng.uniform(.9, 1.3))
for i in range(14): x = rng.uniform(-5, 5); y = rng.uniform(1.5, 6); P["monstera" if i % 2 else "colocasia"]((x, y, 0), rng.uniform(1, 1.6))
for i in range(10): x = rng.uniform(-7, 7); y = rng.uniform(3, 9); P["banana"]((x, y, 0), rng.uniform(1, 1.4))
for i in range(8): x = rng.uniform(-9, 9); y = rng.uniform(5, 14); P["palm"]((x, y, 0), rng.uniform(.8, 1.1))
for (x, y) in [(-3.5, 6), (4.2, 8), (-7, 11), (1, 13), (8, 15)]: P["tree"]((x, y, 0), rng.uniform(.9, 1.2))
for i in range(12): x = rng.uniform(-4, 4); y = rng.uniform(1.5, 7); P["liana"]((x, y, rng.uniform(4, 7)), 1.0)

# light: warm sun breaking through the canopy + green sky bounce + volumetric haze for god rays
wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True
bg = wd.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.25, 0.36, 0.22, 1); bg.inputs[1].default_value = .5
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 5.5; sun.color = (1.0, 0.82, 0.58); sun.angle = math.radians(1.5)
so = bpy.data.objects.new("Sun", sun); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(52), math.radians(-12), math.radians(200))
kl = bpy.data.lights.new("Key", "AREA"); kl.energy = 26; kl.size = .6; kl.color = (1, .9, .78)
ko = bpy.data.objects.new("Key", kl); bpy.context.collection.objects.link(ko); ko.location = (-.6, -.7, .7)
ko.rotation_euler = (Vector((0, 0, .15)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4, 4)); vol = bpy.context.active_object; vol.scale = (30, 30, 8)
vm = bpy.data.materials.new("Haze"); vm.use_nodes = True; vnt = vm.node_tree; vnt.nodes.remove(vnt.nodes.get("Principled BSDF"))
pv = vnt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = .035; pv.inputs["Anisotropy"].default_value = .55
pv.inputs["Color"].default_value = (.85, .95, .8, 1)
vnt.links.new(pv.outputs[0], vnt.nodes.get("Material Output").inputs["Volume"]); vol.data.materials.append(vm)

# camera: 85 mm macro-ish product shot, shallow depth of field
cam = bpy.data.cameras.new("Cam"); cam.lens = 85; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.4
co = bpy.data.objects.new("Cam", cam); bpy.context.collection.objects.link(co); sc.camera = co
co.location = (.12, -1.25, .23); target = Vector((0, 0, top + .07))
co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler(); cam.dof.focus_distance = (target - co.location).length
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=S + "/blend/yeema_cinematic.blend")
print("CINE DONE")
