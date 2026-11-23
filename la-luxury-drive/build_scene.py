"""
LA Golden Hour – boulevard de Los Angeles avec voitures de luxe.
Scène 100 % procédurale pour Blender 5.x.

Usage :
  blender -b -P build_scene.py -- [--stills] [--anim] [--preview]
  (ou: python build_scene.py ... avec le module pip `bpy`)
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PREVIEW = "--preview" in argv
TEST = "--test" in argv

# ------------------------------------------------------------------ reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
FPS, FRAMES = 24, 120
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FRAMES

ROAD_LEN = 420.0           # route le long de l'axe X, de -210 à +210
LANE = 3.6
ROAD_W = LANE * 4 + 1.0    # 4 voies + terre-plein peint
SIDEWALK_W = 4.5

# ------------------------------------------------------------------ materials
def mat(name, color, metal=0.0, rough=0.5, emit=None, strength=0.0, coat=0.0, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Transmission Weight"].default_value = transmission
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def noise_mat(name, c1, c2, scale=30.0, rough=0.8, bump=0.3):
    m = bpy.data.materials.new(name)
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 8
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    return m

M = {
    "asphalt": noise_mat("Asphalt", (0.035, 0.035, 0.04), (0.09, 0.09, 0.095), 180, 0.72, 0.15),
    "concrete": noise_mat("Concrete", (0.45, 0.43, 0.40), (0.62, 0.60, 0.56), 40, 0.9, 0.1),
    "white": mat("LineWhite", (0.85, 0.85, 0.82), rough=0.6),
    "yellow": mat("LineYellow", (0.9, 0.62, 0.05), rough=0.6),
    "trunk": noise_mat("PalmTrunk", (0.22, 0.15, 0.09), (0.42, 0.32, 0.20), 6, 0.9, 0.6),
    "frond": mat("PalmFrond", (0.08, 0.20, 0.05), rough=0.6),
    "tire": mat("Tire", (0.015, 0.015, 0.015), rough=0.85),
    "rim": mat("Rim", (0.85, 0.85, 0.88), metal=1.0, rough=0.15),
    "rim_dark": mat("RimDark", (0.05, 0.05, 0.06), metal=1.0, rough=0.25),
    "glass": mat("Glass", (0.02, 0.025, 0.03), metal=0.3, rough=0.02, coat=1.0),
    "chrome": mat("Chrome", (0.9, 0.9, 0.9), metal=1.0, rough=0.05),
    "head": mat("HeadLight", (1, 1, 1), emit=(1.0, 0.95, 0.85), strength=25),
    "tail": mat("TailLight", (0.5, 0, 0), emit=(1.0, 0.02, 0.01), strength=18),
    "trim": mat("BlackTrim", (0.01, 0.01, 0.012), rough=0.4),
    "hill": noise_mat("Hills", (0.22, 0.18, 0.11), (0.33, 0.30, 0.17), 3, 0.95, 0.5),
    "lamp": mat("Lamp", (1, 1, 1), emit=(1.0, 0.7, 0.35), strength=30),
    "pole": mat("Pole", (0.12, 0.12, 0.13), metal=0.8, rough=0.4),
}
PAINTS = {
    "Rosso":   mat("Paint_Rosso",   (0.55, 0.01, 0.01), metal=0.6, rough=0.25, coat=1.0),
    "Noir":    mat("Paint_Noir",    (0.01, 0.01, 0.012), metal=0.7, rough=0.2, coat=1.0),
    "Blanc":   mat("Paint_Blanc",   (0.85, 0.85, 0.83), metal=0.2, rough=0.25, coat=1.0),
    "Bleu":    mat("Paint_Bleu",    (0.01, 0.06, 0.35), metal=0.8, rough=0.2, coat=1.0),
    "Giallo":  mat("Paint_Giallo",  (0.85, 0.55, 0.0), metal=0.4, rough=0.2, coat=1.0),
    "Vert":    mat("Paint_Vert",    (0.01, 0.12, 0.05), metal=0.8, rough=0.2, coat=1.0),
}

def link(obj, coll=None):
    (coll or scene.collection).objects.link(obj)
    return obj

def new_coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c

def box(name, size, loc, material, coll=None, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me), coll); o.location = loc
    me.materials.append(material)
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL"); mod.width = bevel; mod.segments = 2
    return o

# ------------------------------------------------------------------ world / lumière (golden hour)
world = bpy.data.worlds.new("LA_Sky"); scene.world = world
wn = world.node_tree.nodes; wl = world.node_tree.links
sky = wn.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING"
sky.sun_elevation = math.radians(6)
sky.sun_rotation = math.radians(200)
sky.altitude = 80; sky.aerosol_density = 3.0; sky.air_density = 1.2
sky.sun_intensity = 0.6
wl.new(sky.outputs["Color"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.35

sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 5.0
sun.color = (1.0, 0.62, 0.35); sun.angle = math.radians(1.2)
so = link(bpy.data.objects.new("Sun", sun))
so.rotation_euler = (math.radians(90 - 6), 0, math.radians(200 + 90 + 180))

# ------------------------------------------------------------------ route
C_ROAD = new_coll("Route")
box("Asphalt", (ROAD_LEN, ROAD_W, 0.2), (0, 0, -0.1), M["asphalt"], C_ROAD)
for side in (-1, 1):
    y = side * (ROAD_W / 2 + SIDEWALK_W / 2)
    box(f"Sidewalk_{side}", (ROAD_LEN, SIDEWALK_W, 0.35), (0, y, 0.025), M["concrete"], C_ROAD, bevel=0.04)
    box(f"Ground_{side}", (ROAD_LEN, 60, 0.1), (0, side * (ROAD_W / 2 + SIDEWALK_W + 30), 0.0), M["concrete"], C_ROAD)
# double ligne jaune centrale
for dy in (-0.15, 0.15):
    box(f"Yellow_{dy}", (ROAD_LEN, 0.12, 0.01), (0, dy, 0.005), M["yellow"], C_ROAD)
# pointillés blancs (instanciés via array)
for side in (-1, 1):
    d = box(f"Dash_{side}", (3.0, 0.13, 0.01), (-ROAD_LEN / 2, side * (LANE + 0.5), 0.005), M["white"], C_ROAD)
    a = d.modifiers.new("Array", "ARRAY"); a.count = int(ROAD_LEN / 12); a.relative_offset_displace = (4.0, 0, 0)
    box(f"Edge_{side}", (ROAD_LEN, 0.13, 0.01), (0, side * (ROAD_W / 2 - 0.3), 0.005), M["white"], C_ROAD)

# ------------------------------------------------------------------ palmiers
C_PALM = new_coll("Palmiers")

def make_palm_template():
    # tronc
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.28, depth=1, location=(0, 0, 0))
    trunk = bpy.context.active_object; trunk.name = "PalmTrunk_T"
    trunk.data.materials.append(M["trunk"])
    H = 16.0
    trunk.scale = (1, 1, H); trunk.location.z = H / 2
    bpy.ops.object.transform_apply(scale=True, location=True)
    bm = bmesh.new(); bm.from_mesh(trunk.data)
    vert_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1]
    bmesh.ops.subdivide_edges(bm, edges=vert_edges, cuts=20, use_grid_fill=True)
    bm.to_mesh(trunk.data); bm.free()
    # léger fléchissement et effilement
    for v in trunk.data.vertices:
        t = v.co.z / H
        k = 1.25 - 0.45 * t
        v.co.x *= k; v.co.y *= k
        v.co.x += 0.9 * t * t
    # couronne
    fronds = []
    for i in range(14):
        me = bpy.data.meshes.new("Frond")
        bm = bmesh.new()
        L, segs = 4.6, 10
        verts = []
        for s in range(segs + 1):
            u = s / segs
            w = 0.55 * math.sin(math.pi * min(1, u * 1.1)) + 0.05
            droop = -2.6 * u * u
            verts.append((bm.verts.new((u * L, -w, droop + 0.2 * w)), bm.verts.new((u * L, 0, droop + 0.05)), bm.verts.new((u * L, w, droop + 0.2 * w))))
        for s in range(segs):
            a, b = verts[s], verts[s + 1]
            bm.faces.new((a[0], b[0], b[1], a[1])); bm.faces.new((a[1], b[1], b[2], a[2]))
        bm.to_mesh(me); bm.free()
        f = bpy.data.objects.new("Frond", me); bpy.context.collection.objects.link(f)
        me.materials.append(M["frond"])
        tilt = random.uniform(-0.25, 0.35)
        f.rotation_euler = (0, tilt, i * 2 * math.pi / 14 + random.uniform(-0.1, 0.1))
        f.location = (0.9, 0, H - 0.1)
        fronds.append(f)
    bpy.ops.object.select_all(action="DESELECT")
    trunk.select_set(True)
    for f in fronds: f.select_set(True)
    bpy.context.view_layer.objects.active = trunk
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    for p in trunk.data.polygons: p.use_smooth = True
    sol = trunk.modifiers.new("Solid", "SOLIDIFY"); sol.thickness = 0.02
    return trunk

palm_tpl = make_palm_template()
palm_tpl.name = "Palm_Template"
for c in palm_tpl.users_collection: c.objects.unlink(palm_tpl)
x = -ROAD_LEN / 2 + 4
while x < ROAD_LEN / 2:
    for side in (-1, 1):
        p = bpy.data.objects.new("Palm", palm_tpl.data); C_PALM.objects.link(p)
        p.location = (x + random.uniform(-1, 1), side * (ROAD_W / 2 + 1.6), 0.2)
        s = random.uniform(0.85, 1.25)
        p.scale = (s, s, s)
        p.rotation_euler.z = random.uniform(0, 2 * math.pi)
    x += 14

# lampadaires
C_LAMP = new_coll("Lampadaires")
for i, x in enumerate(range(-200, 200, 28)):
    for side in (-1, 1):
        y = side * (ROAD_W / 2 + 0.6)
        box("Pole", (0.18, 0.18, 9), (x + 7, y, 4.5), M["pole"], C_LAMP)
        box("Arm", (0.12, 2.4, 0.12), (x + 7, y - side * 1.2, 8.9), M["pole"], C_LAMP)
        box("LampHead", (0.7, 0.35, 0.15), (x + 7, y - side * 2.3, 8.8), M["lamp"], C_LAMP)

# ------------------------------------------------------------------ bâtiments (stucco, enseignes néon génériques)
C_BLD = new_coll("Batiments")
STUCCO = [(0.85, 0.72, 0.58), (0.92, 0.85, 0.74), (0.75, 0.55, 0.45), (0.95, 0.9, 0.85), (0.62, 0.70, 0.72), (0.88, 0.65, 0.62)]
NEON = [(1, 0.1, 0.5), (0.1, 0.8, 1), (1, 0.45, 0.05), (0.6, 0.2, 1)]
stucco_mats = [mat(f"Stucco{i}", c, rough=0.85) for i, c in enumerate(STUCCO)]
neon_mats = [mat(f"Neon{i}", c, emit=c, strength=12) for i, c in enumerate(NEON)]
win_mat = mat("ShopWindow", (0.02, 0.02, 0.02), metal=0.5, rough=0.05, emit=(1, 0.7, 0.4), strength=0.25)
for side in (-1, 1):
    x = -ROAD_LEN / 2
    while x < ROAD_LEN / 2:
        w = random.uniform(10, 24); h = random.choice([5, 6, 8, 10, 14, 22])
        d = random.uniform(12, 20)
        y = side * (ROAD_W / 2 + SIDEWALK_W + 2 + d / 2)
        box("Building", (w - 0.6, d, h), (x + w / 2, y, h / 2), random.choice(stucco_mats), C_BLD)
        # vitrine
        box("Shopfront", (w - 2, 0.1, 2.8), (x + w / 2, y - side * (d / 2 + 0.05), 1.8), win_mat, C_BLD)
        # auvent
        box("Awning", (w - 1.5, 1.4, 0.12), (x + w / 2, y - side * (d / 2 + 0.7), 3.6), M["trim"], C_BLD)
        if random.random() < 0.45:
            box("NeonSign", (random.uniform(3, 6), 0.15, 0.5), (x + w / 2, y - side * (d / 2 + 0.1), min(h - 0.8, 4.6)), random.choice(neon_mats), C_BLD)
        x += w

# collines en arrière-plan
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=40, size=1, location=(0, 0, 0))
hill = bpy.context.active_object; hill.name = "Hills"
hill.scale = (1400, 300, 1); bpy.ops.object.transform_apply(scale=True)
for v in hill.data.vertices:
    v.co.z = max(0, 55 * math.sin(v.co.x / 90 + 1.3) * math.cos(v.co.x / 47) + 45 + 30 * math.sin(v.co.x / 23)) * (0.5 + 0.5 * (v.co.y + 150) / 300)
hill.location = (0, 320, -2)
hill.data.materials.append(M["hill"])
for p in hill.data.polygons: p.use_smooth = True

# ------------------------------------------------------------------ voitures de luxe (designs génériques)
C_CARS = new_coll("Voitures")

def extrude_profile(name, pts, width, material, bevel=0.06):
    """pts = profil latéral (x=longueur, z=hauteur) dans le sens antihoraire."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    L = [bm.verts.new((x, -width / 2, z)) for x, z in pts]
    R = [bm.verts.new((x, width / 2, z)) for x, z in pts]
    n = len(pts)
    bm.faces.new(L); bm.faces.new(list(reversed(R)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((L[i], L[j], R[j], R[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    if bevel:
        bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = bevel; bv.segments = 4
        bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(20)
        o.modifiers.new("WN", "WEIGHTED_NORMAL").keep_sharp = False
    for p in me.polygons: p.use_smooth = True
    return o

def taper(obj, factor):
    """resserre le haut (pavillon) pour donner du galbe."""
    zs = [v.co.z for v in obj.data.vertices]; zmin, zmax = min(zs), max(zs)
    for v in obj.data.vertices:
        t = (v.co.z - zmin) / max(1e-6, zmax - zmin)
        v.co.y *= 1 - factor * t

CAR_TYPES = {
    # body profile, cabin profile, width, wheel radius, wheel x positions
    "supercar": dict(
        body=[(-2.25, 0.2), (2.15, 0.18), (2.38, 0.3), (2.3, 0.5), (1.2, 0.72), (-1.6, 0.92), (-2.3, 0.95), (-2.35, 0.55)],
        hl=0.42, tl=0.82,
        cabin=[(-1.25, 0.88), (0.9, 0.74), (-0.05, 1.18), (-0.85, 1.17)],
        width=2.0, r=0.36, wx=(1.45, -1.35)),
    "gt": dict(
        body=[(-2.4, 0.24), (2.3, 0.22), (2.48, 0.38), (2.42, 0.64), (1.3, 0.82), (-2.0, 0.95), (-2.45, 0.9), (-2.5, 0.5)],
        hl=0.55, tl=0.8,
        cabin=[(-1.6, 0.92), (0.95, 0.82), (0.0, 1.30), (-1.05, 1.30)],
        width=1.95, r=0.37, wx=(1.55, -1.5)),
    "suv": dict(
        body=[(-2.5, 0.34), (2.45, 0.34), (2.58, 0.55), (2.55, 0.92), (1.6, 1.12), (-2.45, 1.15), (-2.55, 0.95)],
        hl=0.82, tl=0.98,
        cabin=[(-2.35, 1.1), (1.3, 1.1), (0.55, 1.85), (-2.25, 1.88)],
        width=2.05, r=0.42, wx=(1.65, -1.6)),
    "cabrio": dict(
        body=[(-2.3, 0.22), (2.2, 0.2), (2.4, 0.34), (2.35, 0.55), (1.0, 0.78), (-2.0, 0.88), (-2.35, 0.85), (-2.38, 0.5)],
        hl=0.46, tl=0.74,
        cabin=[(-0.2, 0.78), (0.6, 0.76), (0.15, 1.12), (0.05, 1.12)],  # pare-brise seul (décapotable)
        width=1.95, r=0.36, wx=(1.5, -1.45)),
}

def make_wheel(name, r, width, coll, rim_mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=width, rotation=(math.pi / 2, 0, 0))
    tire = bpy.context.active_object; tire.name = name
    tire.data.materials.append(M["tire"])
    bv = tire.modifiers.new("Bevel", "BEVEL"); bv.width = 0.06; bv.segments = 3
    for p in tire.data.polygons: p.use_smooth = True
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r * 0.68, depth=width + 0.02, rotation=(math.pi / 2, 0, 0))
    rim = bpy.context.active_object; rim.name = name + "_Rim"; rim.data.materials.append(rim_mat)
    rim.parent = tire
    # rayons
    for k in range(5):
        bpy.ops.mesh.primitive_cube_add(size=1)
        sp = bpy.context.active_object; sp.name = name + "_Spoke"
        sp.scale = (r * 1.25, width + 0.05, 0.07)
        sp.rotation_euler = (0, k * math.pi / 5, 0)
        sp.data.materials.append(M["trim"]); sp.parent = tire
    for o in [tire] + list(tire.children):
        for c in o.users_collection: c.objects.unlink(o)
        coll.objects.link(o)
    return tire

def make_car(name, kind, paint, rim_mat):
    spec = CAR_TYPES[kind]
    root = link(bpy.data.objects.new(name, None), C_CARS)
    root.empty_display_size = 2.5
    body = extrude_profile(name + "_Body", spec["body"], spec["width"], paint, 0.09)
    taper(body, 0.06)
    cabin = extrude_profile(name + "_Cabin", spec["cabin"], spec["width"] * 0.86, M["glass"], 0.05)
    taper(cabin, 0.18)
    parts = [body, cabin]
    W = spec["width"]
    fz = [z for x, z in spec["body"]]
    front_x = max(x for x, z in spec["body"]); rear_x = min(x for x, z in spec["body"])
    # phares / feux
    for s in (-1, 1):
        parts.append(box(name + "_HL", (0.08, 0.42, 0.07), (front_x - 0.02, s * W * 0.33, spec["hl"]), M["head"]))
        parts.append(box(name + "_TL", (0.06, 0.5, 0.06), (rear_x + 0.02, s * W * 0.3, spec["tl"]), M["tail"]))
    # bande de feux arrière continue
    parts.append(box(name + "_TLbar", (0.05, W * 0.55, 0.03), (rear_x + 0.02, 0, spec["tl"]), M["tail"]))
    # calandre / diffuseur
    parts.append(box(name + "_Grille", (0.05, W * 0.55, 0.16), (front_x + 0.03, 0, 0.34 if kind != "suv" else 0.6), M["trim"]))
    parts.append(box(name + "_Diffuser", (0.3, W * 0.7, 0.1), (rear_x + 0.15, 0, 0.22 if kind != "suv" else 0.4), M["trim"]))
    # rétroviseurs
    mx = spec["cabin"][1][0] - 0.1; mz = spec["cabin"][1][1] + 0.05
    for s in (-1, 1):
        parts.append(box(name + "_Mirror", (0.2, 0.18, 0.1), (mx, s * (W / 2 + 0.05), mz), paint, bevel=0.03))
    if kind == "supercar":
        parts.append(box(name + "_Wing", (0.35, W * 0.9, 0.04), (rear_x + 0.25, 0, 1.12), M["trim"]))
        for s in (-1, 1):
            parts.append(box(name + "_WingPost", (0.12, 0.04, 0.2), (rear_x + 0.25, s * W * 0.3, 1.02), M["trim"]))
    if kind == "cabrio":
        # sièges en cuir
        leather = bpy.data.materials.get("Leather") or mat("Leather", (0.35, 0.12, 0.04), rough=0.5)
        for s in (-1, 1):
            parts.append(box(name + "_Seat", (0.55, 0.55, 0.55), (-0.55, s * 0.42, 0.95), leather, bevel=0.08))
    for p in parts:
        if p.name not in C_CARS.objects:
            for c in p.users_collection: c.objects.unlink(p)
            C_CARS.objects.link(p)
        p.parent = root
    wheels = []
    for wx in spec["wx"]:
        for s in (-1, 1):
            wh = make_wheel(name + "_Wheel", spec["r"], 0.3, C_CARS, rim_mat)
            wh.location = (wx, s * (W / 2 - 0.12), spec["r"])
            wh.parent = root
            wheels.append(wh)
    # phares avant : vraies lumières (spot) pour les reflets sur l'asphalte
    for s in (-1, 1):
        ld = bpy.data.lights.new(name + "_Beam", "SPOT"); ld.energy = 300; ld.spot_size = math.radians(55)
        ld.color = (1, 0.93, 0.8)
        lo = bpy.data.objects.new(name + "_Beam", ld); C_CARS.objects.link(lo)
        lo.parent = root; lo.location = (front_x + 0.1, s * W * 0.33, 0.6)
        lo.rotation_euler = (0, math.radians(95), 0)
    return root, wheels, spec["r"]

def animate_car(root, wheels, r, x0, y, speed, heading=1):
    """déplacement linéaire + rotation des roues cohérente avec la vitesse."""
    root.rotation_euler.z = 0 if heading > 0 else math.pi
    T = FRAMES / FPS
    root.location = (x0, y, 0); root.keyframe_insert("location", frame=1)
    root.location = (x0 + heading * speed * T, y, 0); root.keyframe_insert("location", frame=FRAMES)
    spin = -(speed * T) / r
    for w in wheels:
        w.rotation_euler = (0, 0, 0); w.keyframe_insert("rotation_euler", frame=1)
        w.rotation_euler = (0, spin, 0); w.keyframe_insert("rotation_euler", frame=FRAMES)
    for o in [root] + wheels:
        ad = o.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for k in fc.keyframe_points: k.interpolation = "LINEAR"
            # Blender 5 : actions en couches
            for layer in getattr(ad.action, "layers", []):
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for k in fc.keyframe_points: k.interpolation = "LINEAR"

# voie de droite (sens +X) : y = -LANE*0.5-0.5, -LANE*1.5-0.5 ; sens inverse : y positif
L1, L2 = -(LANE * 0.5 + 0.5), -(LANE * 1.5 + 0.5)
O1, O2 = (LANE * 0.5 + 0.5), (LANE * 1.5 + 0.5)
CARS = [
    # name, type, paint, rim, x0, lane y, vitesse m/s, sens
    ("Hero_Rosso",   "supercar", "Rosso",  M["rim_dark"], -30, L1, 18.0, 1),
    ("GT_Noir",      "gt",       "Noir",   M["rim"],      -42, L2, 17.0, 1),
    ("Cabrio_Bleu",  "cabrio",   "Bleu",   M["rim"],      -8,  L2, 16.0, 1),
    ("SUV_Blanc",    "suv",      "Blanc",  M["rim_dark"], -60, L1, 18.5, 1),
    ("Super_Giallo", "supercar", "Giallo", M["rim_dark"],  90, O1, 17.0, -1),
    ("GT_Vert",      "gt",       "Vert",   M["rim"],       60, O2, 15.0, -1),
    ("SUV_Noir",     "suv",      "Noir",   M["rim"],      140, O2, 16.0, -1),
]
hero = None
for n, kind, paint, rim, x0, y, v, hd in CARS:
    root, wheels, r = make_car(n, kind, PAINTS[paint], rim)
    animate_car(root, wheels, r, x0, y, v, hd)
    if n.startswith("Hero"): hero = root

# ------------------------------------------------------------------ caméras
def cam(name, lens):
    c = bpy.data.cameras.new(name); c.lens = lens
    c.dof.use_dof = True; c.dof.aperture_fstop = 2.8
    return link(bpy.data.objects.new(name, c))

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# 1) plan large d'établissement (statique, grand-angle depuis le trottoir)
cam_wide = cam("CAM_01_Establishing", 24)
cam_wide.location = (38, -10.6, 1.5); look_at(cam_wide, (-20, -1.5, 2.6))
cam_wide.data.dof.focus_distance = 50

# 2) travelling bas sur la voiture héros (rig suiveur)
rig = link(bpy.data.objects.new("CamRig_Tracking", None))
rig.parent = hero
cam_track = cam("CAM_02_Tracking", 35)
cam_track.parent = rig
cam_track.location = (6.5, -4.2, 0.9); look_at(cam_track, (0.3, 0, 0.7))
cam_track.data.dof.focus_object = hero
cam_track.data.dof.aperture_fstop = 4

# 3) arrière 3/4 avec coucher de soleil dans l'axe
cam_rear = cam("CAM_03_Rear", 50)
cam_rear.parent = rig
cam_rear.location = (-7.5, 2.8, 1.4); look_at(cam_rear, (0.5, 0, 0.8))
cam_rear.data.dof.focus_object = hero

# 4) vue drone en surplomb
cam_drone = cam("CAM_04_Drone", 28)
cam_drone.location = (-25, -6, 14); cam_drone.keyframe_insert("location", frame=1)
cam_drone.location = (30, 0, 26); cam_drone.keyframe_insert("location", frame=FRAMES)
tc = cam_drone.constraints.new("TRACK_TO"); tc.target = hero; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_drone.data.dof.use_dof = False

# montage : marqueurs de timeline pour changer de caméra
for frame, c in [(1, cam_wide), (31, cam_track), (61, cam_rear), (91, cam_drone)]:
    m = scene.timeline_markers.new(c.name, frame=frame); m.camera = c
scene.camera = cam_wide

# ------------------------------------------------------------------ rendu
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24 if PREVIEW else 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = (640, 360) if TEST else (1280, 720)
if TEST: scene.cycles.samples = 12
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = 0.3
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.4

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "la_luxury_drive.blend"))
print("Saved .blend")

OUT = os.path.join(HERE, "renders")
if "--stills" in argv:
    shots = [(cam_wide, 20), (cam_track, 40), (cam_rear, 75), (cam_drone, 105)]
    for c, f in shots:
        scene.camera = c; scene.frame_set(f)
        scene.render.filepath = os.path.join(OUT, f"{c.name}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", c.name)
if "--anim" in argv:
    scene.cycles.samples = 16
    scene.render.resolution_x, scene.render.resolution_y = (960, 540)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(OUT, "frames", "f_")
    bpy.ops.render.render(animation=True)
