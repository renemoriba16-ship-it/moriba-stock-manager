"""
PCH Golden Hour : version photoréaliste.
Technique pro "HDRI backplate + shadow catcher" :
  - panorama HDR réel (Poly Haven, CC0) = arrière-plan ET éclairage physiquement exact
  - voitures 3D détaillées (Khronos CarConcept, base CC0) posées sur un shadow catcher
  - caméra sur trépied au point de prise de vue du panorama -> perspective cohérente
  - Cycles path tracing, motion blur, DOF, AgX
Usage : python build_photoreal.py -- --assets DIR [--test] [--stills] [--anim]
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = arg("--assets", os.path.join(HERE, "assets"))
TEST = "--test" in argv
HDRI = os.path.join(ASSETS, "victoria_sunset_4k.hdr")
CAR = os.path.join(ASSETS, "CarConcept.glb")

CAM_H = float(arg("--camh", 1.7))       # hauteur de prise de vue du panorama
HDRI_ROT = math.radians(float(arg("--hdrirot", 0)))
LANE_NEAR = float(arg("--lane", -2.3))  # voie proche (sens +X)
LANE_FAR = float(arg("--lanefar", -5.0)) # voie opposée (sens -X)
FPS, FRAMES = 24, 120

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES

# ---------------------------------------------------------------- monde HDRI
world = bpy.data.worlds.new("HDRI"); scene.world = world
nt = world.node_tree; N = nt.nodes
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(HDRI)
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord")
mp.inputs["Rotation"].default_value[2] = HDRI_ROT
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
nt.links.new(env.outputs["Color"], N["Background"].inputs["Color"])
N["Background"].inputs["Strength"].default_value = 1.0

# soleil (direction mesurée sur le panorama : u≈0.60, ~3.5° au-dessus de l'horizon)
az = 2 * math.pi * (float(arg("--sunu", 0.60)) - 0.5) + HDRI_ROT
el = math.radians(float(arg("--sunel", 3.5)))
sun_dir = Vector((-math.cos(az) * math.cos(el), -math.sin(az) * math.cos(el), math.sin(el)))
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = float(arg("--sun", 3.0))
sun.color = (1.0, 0.72, 0.45); sun.angle = math.radians(0.6)
so = bpy.data.objects.new("Sun", sun); scene.collection.objects.link(so)
so.rotation_euler = (-sun_dir).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- sol shadow catcher
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
ground = bpy.context.active_object; ground.name = "ShadowCatcher"
ground.is_shadow_catcher = True
gm = bpy.data.materials.new("GroundAsphalt")
gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.06, 0.06, 0.06, 1); gb.inputs["Roughness"].default_value = 0.55
ground.data.materials.append(gm)

# ---------------------------------------------------------------- voitures
PAINT = {"Carmine": "Carmine", "Graphite": "Graphite", "Pearl": "Pearl"}
plate = bpy.data.materials.new("PlateBlank")
plate.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.78, 1)

def import_car(name, paint):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=CAR)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); scene.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
        for s in o.material_slots:
            if not s.material: continue
            mn = s.material.name
            if mn.startswith("Paint ") or mn.startswith("Interior 3"):
                base = mn.split(".")[0].rsplit(" ", 1)[0]          # "Paint 1"
                tgt = bpy.data.materials.get(f"{base} {paint}")
                if tgt: s.material = tgt
            if mn.startswith("License"):
                s.material = plate
    wheels = [o for o in new if o.type == "EMPTY" and o.name.split(".")[0] in ("WheelFrontL", "WheelFrontR", "WheelRearL", "WheelRearR")]
    return root, wheels

CURVE_K = float(arg("--curve", -0.0018))   # la route du panorama tourne vers -Y côté soleil

def road_y(x, lane):
    return lane + (CURVE_K * x * x if x < 0 else 0.0)

def make_path(name, lane, x0, x1):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); n = 80
    sp.points.add(n - 1)
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        sp.points[i].co = (x, road_y(x, lane), 0, 1)
    o = bpy.data.objects.new(name, cu); scene.collection.objects.link(o)
    o.hide_render = True
    return o

def animate(root, wheels, x0, x1, lane, heading):
    """la voiture suit une courbe calée sur la route réelle du panorama."""
    path = make_path(root.name + "_Path", lane, x0, x1)
    root.rotation_euler.z = math.radians(90)       # avant du modèle (-Y) -> axe +X local, aligné sur la tangente du chemin
    fp = root.constraints.new("FOLLOW_PATH"); fp.target = path
    fp.use_curve_follow = True; fp.use_fixed_location = True
    fp.forward_axis = "FORWARD_X"; fp.up_axis = "UP_Z"
    fp.offset_factor = 0.0; fp.keyframe_insert("offset_factor", frame=1)
    fp.offset_factor = 1.0; fp.keyframe_insert("offset_factor", frame=FRAMES)
    dist = abs(x1 - x0); spin = dist / 0.385 * (1 if heading > 0 else 1)
    for w in wheels:
        w.rotation_mode = "XYZ"
        base = w.rotation_euler.copy()
        w.keyframe_insert("rotation_euler", frame=1)
        w.rotation_euler.x = base.x - spin
        w.keyframe_insert("rotation_euler", frame=FRAMES)
    for o in [root] + wheels:
        act = o.animation_data.action
        for layer in getattr(act, "layers", []):
            for st in layer.strips:
                for bag in st.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points: k.interpolation = "LINEAR"
        for fc in getattr(act, "fcurves", []):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"

T = FRAMES / FPS
hero, hw = import_car("Hero_Carmine", "Carmine")
animate(hero, hw, -70, -70 + 20 * T, LANE_NEAR, +1)            # ~80 km/h vers la caméra
second, sw = import_car("Follow_Graphite", "Graphite")
animate(second, sw, -86, -86 + 20 * T, LANE_NEAR, +1)
onc, ow = import_car("Oncoming_Pearl", "Pearl")
animate(onc, ow, 40, 40 - 20 * T, LANE_FAR, -1)

# ---------------------------------------------------------------- caméras
def make_cam(name, lens, loc):
    c = bpy.data.cameras.new(name); c.lens = lens; c.sensor_width = 36
    c.dof.use_dof = True; c.dof.aperture_fstop = 2.8
    o = bpy.data.objects.new(name, c); scene.collection.objects.link(o); o.location = loc
    return o

target = bpy.data.objects.new("HeroTarget", None); scene.collection.objects.link(target)
target.parent = hero; target.location = (0, 0, 0.7)

# plan pano : trépied, panoramique qui suit la voiture héros (pas de parallaxe -> raccord parfait)
cam_pan = make_cam("CAM_Pan", 50, (0, 0, CAM_H))
tt = cam_pan.constraints.new("TRACK_TO"); tt.target = target
tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
cam_pan.data.dof.focus_object = target

# plan fixe au ras du sol, téléobjectif, voitures sortant du soleil
cam_low = make_cam("CAM_Tele", 135, (0, 0, CAM_H))
cam_low.rotation_euler = (math.radians(89), 0, math.radians(90 + 8))
cam_low.data.dof.focus_object = target; cam_low.data.dof.aperture_fstop = 4

scene.camera = cam_pan

# ---------------------------------------------------------------- rendu
r = scene.render
r.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32 if TEST else 160
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
r.resolution_x, r.resolution_y = (960, 540) if TEST else (1920, 1080)
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = float(arg("--exposure", 0.0))
r.film_transparent = False

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "pch_golden_hour.blend"))
OUT = os.path.join(HERE, "renders")
if "--stills" in argv:
    for cam, f in ((cam_low, 30), (cam_pan, 72), (cam_pan, 96)):
        scene.camera = cam; scene.frame_set(f)
        r.filepath = os.path.join(OUT, f"{cam.name}_f{f:03d}.png")
        bpy.ops.render.render(write_still=True); print("rendered", r.filepath)
if "--anim" in argv:
    scene.camera = cam_pan
    scene.cycles.samples = int(arg("--animsamples", 24))
    r.resolution_x, r.resolution_y = 1280, 720
    r.use_overwrite = False; r.use_placeholder = True   # reprise possible après interruption
    r.filepath = os.path.join(OUT, "frames", "f_")
    bpy.ops.render.render(animation=True)
