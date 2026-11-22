import bpy, math, bmesh
from mathutils import Vector

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def setup_render(res=(960, 1200), samples=64, bg=(0.91, 0.87, 0.82), world_strength=0.6, transparent=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    sc.cycles.max_bounces = 12
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 12
    sc.cycles.glossy_bounces = 6
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast' if False else 'None'
    w = bpy.data.worlds.new("W"); sc.world = w
    w.use_nodes = True
    nt = w.node_tree; bgn = nt.nodes.get("Background")
    bgn.inputs[0].default_value = (*bg, 1); bgn.inputs[1].default_value = world_strength
    return sc

def mat(name, base=(0.8,0.8,0.8), metallic=0.0, rough=0.4, trans=0.0, ior=1.45, coat=0.0, sss=0.0, emission=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Transmission Weight"].default_value = trans
    p.inputs["IOR"].default_value = ior
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Alpha"].default_value = alpha
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
    return m

def tex_mat(name, img_path, rough=0.55, coat=0.0):
    m = mat(name, rough=rough, coat=coat)
    nt = m.node_tree; p = nt.nodes.get("Principled BSDF")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(img_path)
    nt.links.new(t.outputs[0], p.inputs["Base Color"])
    return m

def lathe(name, profile, steps=96, thickness=0.0, subsurf=2, material=None, smooth=True):
    """profile: list of (r, z) from bottom-axis to top. Revolve around Z."""
    me = bpy.data.meshes.new(name)
    verts = [(r, 0, z) for r, z in profile]
    edges = [(i, i+1) for i in range(len(verts)-1)]
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    sc = ob.modifiers.new("screw", 'SCREW'); sc.steps = steps; sc.render_steps = steps
    sc.use_merge_vertices = True; sc.merge_threshold = 0.0005; sc.use_normal_calculate = True
    sc.use_smooth_shade = smooth
    if thickness:
        so = ob.modifiers.new("solid", 'SOLIDIFY'); so.thickness = thickness; so.offset = -1; so.use_even_offset = True
    if subsurf:
        ss = ob.modifiers.new("sub", 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
    if material: me.materials.append(material)
    return ob

def label_cyl(name, r, h, z, material, verts=128):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, end_fill_type='NOTHING', location=(0,0,z))
    ob = bpy.context.active_object; ob.name = name
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(material)
    # rotate so that u=0.5 (label front) faces -Y (camera)
    ob.rotation_euler.z = math.radians(0)
    bpy.ops.object.transform_apply(rotation=True)
    return ob

def area(name, loc, target=(0,0,1), energy=500, size=2, color=(1,1,1), shape='RECTANGLE', sx=None, sy=None, shadow=True):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color
    l.use_shadow = shadow
    l.shape = shape; l.size = sx or size; 
    if shape == 'RECTANGLE': l.size_y = sy or size
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

def camera(loc, target, lens=70):
    c = bpy.data.cameras.new("Cam"); c.lens = lens
    ob = bpy.data.objects.new("Cam", c); bpy.context.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return ob

def shadow_floor(size=30):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0,0,0))
    f = bpy.context.active_object; f.name = "Floor"; f.is_shadow_catcher = True
    return f

def empty(name, loc=(0,0,0)):
    e = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(e); e.location = loc
    return e

def parent(child, par):
    child.parent = par

def key(ob, path, frame, value, index=-1):
    if index >= 0:
        getattr(ob, path)[index] = value
    else:
        setattr(ob, path, value)
    ob.keyframe_insert(data_path=path, index=index, frame=frame)

# ---------- Products ----------
def oil_bottle(S, mats):
    root = empty("OilBottle")
    glass = lathe("Glass", [(0,0.0),(0.44,0.0),(0.49,0.02),(0.5,0.08),(0.5,1.22),(0.48,1.34),(0.40,1.45),(0.26,1.52),(0.19,1.56),(0.18,1.62),(0.18,1.70)],
                  thickness=0.035, material=mats['amber'])
    liquid = lathe("Liquid", [(0,0.04),(0.44,0.04),(0.46,0.09),(0.462,1.0),(0,1.0)], subsurf=1, material=mats['oil'])
    lab = label_cyl("Label", 0.506, 0.72, 0.62, tex_mat("LabelOil", S+"/tex/label_oil.png", rough=0.6))
    for o in (glass, liquid, lab): parent(o, root)
    dropper = empty("Dropper", (0,0,0)); parent(dropper, root)
    collar = lathe("Collar", [(0,1.58),(0.215,1.58),(0.225,1.6),(0.225,1.86),(0.21,1.88),(0.16,1.88),(0,1.88)], subsurf=1, material=mats['gold'])
    ridges = []
    bulb = lathe("Bulb", [(0,1.86),(0.15,1.86),(0.155,1.95),(0.15,2.12),(0.13,2.25),(0.09,2.32),(0,2.34)], material=mats['rubber'])
    pip = lathe("Pipette", [(0,0.22),(0.012,0.22),(0.03,0.30),(0.05,0.42),(0.05,1.6),(0,1.6)], subsurf=1, material=mats['clear'])
    pipoil = lathe("PipOil", [(0,0.23),(0.008,0.23),(0.022,0.30),(0.04,0.42),(0.04,0.95),(0,0.95)], subsurf=1, material=mats['oil'])
    for o in (collar, bulb, pip, pipoil): parent(o, dropper)
    return root, dropper

def shampoo_bottle(S, mats):
    root = empty("Shampoo")
    body = lathe("Body", [(0,0),(0.40,0),(0.43,0.04),(0.43,1.75),(0.40,1.88),(0.30,1.97),(0.16,2.02),(0.15,2.12)], material=mats['frost'])
    lab = label_cyl("LabelS", 0.433, 1.3, 0.9, tex_mat("LabelSh", S+"/tex/label_shampoo.png", rough=0.6))
    cap = lathe("Pump", [(0,2.05),(0.19,2.05),(0.19,2.28),(0.17,2.30),(0,2.30)], subsurf=1, material=mats['gold'])
    stem = lathe("Stem", [(0,2.28),(0.05,2.28),(0.05,2.48),(0,2.48)], subsurf=1, material=mats['espresso'])
    head = lathe("Head", [(0,2.46),(0.13,2.46),(0.14,2.52),(0.13,2.6),(0,2.62)], subsurf=1, material=mats['espresso'])
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.035, depth=0.38, location=(0,-0.2,2.55), rotation=(math.radians(90),0,0))
    nozzle = bpy.context.active_object; nozzle.data.materials.append(mats['espresso']); bpy.ops.object.shade_smooth()
    for o in (body, lab, cap, stem, head, nozzle): parent(o, root)
    return root

def mask_jar(S, mats):
    root = empty("Jar")
    jar = lathe("JarGlass", [(0,0),(0.72,0),(0.76,0.04),(0.77,0.12),(0.77,0.72),(0.74,0.78),(0.68,0.80),(0.68,0.86)], thickness=0.04, material=mats['amber'])
    cream = lathe("Cream", [(0,0.05),(0.70,0.05),(0.72,0.1),(0.72,0.72),(0,0.74)], subsurf=1, material=mats['cream'])
    lab = label_cyl("LabelM", 0.775, 0.42, 0.42, tex_mat("LabelMk", S+"/tex/label_mask.png", rough=0.6))
    lid = lathe("Lid", [(0,0.80),(0.78,0.80),(0.80,0.83),(0.80,1.07),(0.78,1.1),(0,1.1)], subsurf=1, material=mats['gold'])
    for o in (jar, cream, lab, lid): parent(o, root)
    return root, lid

def materials():
    return {
        'amber': mat("Amber", base=(0.62, 0.28, 0.07), rough=0.03, trans=1.0, ior=1.5),
        'clear': mat("Clear", base=(0.97, 0.95, 0.92), rough=0.02, trans=1.0, ior=1.5),
        'oil': mat("Oil", base=(0.95, 0.62, 0.16), rough=0.02, trans=1.0, ior=1.47),
        'gold': mat("Gold", base=(0.95, 0.70, 0.40), metallic=1.0, rough=0.22),
        'rubber': mat("Rubber", base=(0.018, 0.012, 0.009), rough=0.45, coat=0.15),
        'espresso': mat("Espresso", base=(0.05, 0.032, 0.022), rough=0.35, coat=0.5),
        'frost': mat("Frost", base=(0.16, 0.075, 0.04), rough=0.42, coat=0.35),
        'cream': mat("CreamMat", base=(0.96, 0.84, 0.66), rough=0.45, sss=0.4),
    }

def studio(warm=True):
    area("Key", (-3.5, -3.5, 4.5), (0,0,1), energy=1100, size=5, color=(1.0, 0.93, 0.85))
    area("Rim", (3.0, 2.5, 3.0), (0,0,1.2), energy=700, sx=0.6, sy=4, color=(1.0, 0.85, 0.7), shadow=False)
    area("Fill", (4.0, -3.0, 1.5), (0,0,1), energy=220, size=4, color=(0.95, 0.95, 1.0), shadow=False)
    area("Top", (0, 0, 6), (0,0,0), energy=250, size=3)
    area("StripL", (-2.2, 1.0, 1.5), (0,0,1.2), energy=300, sx=0.3, sy=4, shadow=False)
