"""
« L'HEURE DORÉE » : court-métrage automobile de 3 minutes, 100 % gratuit.

Technique : HDRI backplate (panoramas photo réels Poly Haven, CC0) + voitures 3D
(Khronos CarConcept, base CC0) posées sur un shadow catcher, rendu Cycles.
Chaque plan est rendu par un processus Blender séparé (reprise facile).

Usage :
  python film.py -- --list
  python film.py -- --shot C02 [--test] [--frames 1,50,100]
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FPS = 24
CAR_GLB = os.path.join(ASSETS, "CarConcept.glb")
WHEEL_R = 0.385

# =====================================================================
#  LIEUX : panorama + géométrie de la route (mesurée par projection au sol)
#  road(s, lane) -> (x, y) : s = abscisse le long de la route (m), lane = décalage latéral
# =====================================================================
def coast_road(s, lane):
    return (s, lane - COAST_K * s * s)

COAST_K = float(arg("--coastk", 0.0018))
DES_KN = float(arg("--deskn", 0.21))
DES_KP = float(arg("--deskp", 0.0016))
CAN_K = float(arg("--cank", 0.03))
YSTOP = float(arg("--ystop", -9))
DES_A = math.radians(3.6)
def desert_road(s, lane):
    bx, by = 0.0, 1.5
    dx, dy = math.cos(DES_A), math.sin(DES_A)
    bend = (-DES_KN * s * s / (abs(s) + 15)) if s < 0 else DES_KP * s * s
    return (bx + s * dx - lane * dy, by + s * dy + lane * dx + bend)

TRK_A = math.radians(-7.3)
def track_road(s, lane):
    bx, by = 0.0, 0.85
    dx, dy = math.cos(TRK_A), math.sin(TRK_A)
    return (bx + s * dx - lane * dy, by + s * dy + lane * dx)

def canyon_road(s, lane):
    return (lane + (CAN_K * s * s if s < 0 else 0.0), s)

LOCS = {
    "coast":   dict(hdri="victoria_sunset_4k.hdr", h=1.7, sun=(0.60, 3.5, 3.0), road=coast_road),
    "desert":  dict(hdri="goegap_road_4k.hdr", h=1.7, sun=(0.60, 5.0, 3.0), road=desert_road),
    "track":   dict(hdri="zwartkops_straight_sunset_4k.hdr", h=1.7, sun=(0.60, 1.5, 3.0), road=track_road),
    "canyon":  dict(hdri="camdeboo_road_4k.hdr", h=1.7, sun=(0.60, 3.0, 3.0), road=canyon_road),
}

# voies
CN, CF = -2.3, -5.0            # côte : voie proche / voie opposée
DA, DB = 0.3, -2.0             # désert : voie principale / voie de dépassement (loin de la caméra seulement)
TA, TB, TC = 2.6, -2.8, 5.2    # circuit (la caméra est sur la piste, entre TA et TB)
YL = 2.2                       # piste de montagne

def car(name, lane, s0, s1=None, motion="lin", **kw):
    d = dict(car=name, lane=lane, s0=s0, s1=s0 if s1 is None else s1, motion=motion)
    d.update(kw); return d

def pan(target, lens=35, fstop=2.8):
    return dict(type="pan", target=target, lens=lens, fstop=fstop)

def fixed(yaw, pitch=1.0, lens=50, focus=None, fstop=4.0, hold=False):
    return dict(type="fixed", yaw=yaw, pitch=pitch, lens=lens, focus=focus, fstop=fstop, hold=hold)

S = lambda sec: int(round(sec * FPS))

# =====================================================================
#  SCÉNARIO : les plans
# =====================================================================
SHOTS = [
    # ---------------- ACTE 1 : LA CÔTE --------------------------------
    dict(name="C01", loc="coast", dur=6, cam=fixed(-20, 1.0, 35, hold=True), cars=[]),
    dict(name="C02", loc="coast", dur=5, cam=fixed(188, 1.0, 135, focus="red"),
         cars=[car("red", CN, -150, -30)]),
    dict(name="C03", loc="coast", dur=4, cam=pan("red", 40),
         cars=[car("red", CN, -50, 46)]),
    dict(name="C04", loc="coast", dur=5, cam=fixed(-15, 2.0, 28, focus="red"),
         cars=[car("red", CN, 5, 120)]),
    dict(name="C05", loc="coast", dur=5, cam=fixed(188, 1.0, 135, focus="black"),
         cars=[car("black", CN, -175, -45)]),
    dict(name="C06", loc="coast", dur=4, cam=pan("black", 35),
         cars=[car("black", CN, -60, 60)]),
    dict(name="C07", loc="coast", dur=5, cam=fixed(-10, 1.0, 50, focus="pearl"),
         cars=[car("pearl", CF, 150, 20)]),
    dict(name="C08", loc="coast", dur=6, cam=pan("black", 35),
         cars=[car("red", CN, -80, 70), car("black", CN, -96, 64)]),
    dict(name="C09", loc="coast", dur=6, cam=pan("black", 135),
         cars=[car("red", CN, 30, 120), car("black", CF, 22, 118)]),
    dict(name="C10", loc="coast", dur=5, cam=pan("red", 35),
         cars=[car("red", CN, -60, 65), car("pearl", CF, 60, -60)]),
    # ---------------- ACTE 2 : LE DÉSERT ------------------------------
    dict(name="D01", loc="desert", dur=5, cam=fixed(-30, 2.0, 28, hold=True), cars=[]),
    dict(name="D02", loc="desert", dur=5, cam=fixed(191, 1.0, 135, focus="red"),
         cars=[car("red", DA, -150, -30), car("black", DA, -165, -42)]),
    dict(name="D03", loc="desert", dur=4, cam=pan("red", 24),
         cars=[car("red", DA, -40, 60), car("black", DA, -52, 46)]),
    dict(name="D04", loc="desert", dur=5, cam=fixed(0, 2.0, 24, focus="black"),
         cars=[car("red", DA, 10, 110), car("black", DB, 14, 140)]),
    dict(name="D05", loc="desert", dur=5, cam=fixed(189, 1.0, 135, focus="pearl"),
         cars=[car("pearl", DA, -200, -60)]),
    dict(name="D06", loc="desert", dur=5, cam=pan("pearl", 28),
         cars=[car("black", DA, -48, 64), car("red", DA, -62, 50), car("pearl", DA, -80, 44)]),
    dict(name="D07", loc="desert", dur=5, cam=fixed(184, 2.5, 24, focus="red"),
         cars=[car("red", DA, -110, 25), car("black", DA, -126, 10)]),
    dict(name="D08", loc="desert", dur=6, cam=fixed(8, 1.0, 85, focus="red"),
         cars=[car("red", DA, 20, 130), car("black", DB, 16, 138), car("pearl", DA, 8, 120)]),
    # ---------------- ACTE 3 : LE CIRCUIT -----------------------------
    dict(name="T01", loc="track", dur=6, cam=fixed(-10, 1.0, 28, hold=True), cars=[]),
    dict(name="T02", loc="track", dur=7, cam=fixed(172, 1.5, 50, focus="red"),
         cars=[car("red", TA, -28, motion=("launch", S(3), 9.0)),
               car("black", TB, -30, motion=("launch", S(3), 9.2)),
               car("pearl", TC, -36, motion=("launch", S(3.2), 8.5))]),
    dict(name="T03", loc="track", dur=4, cam=pan("red", 28),
         cars=[car("red", TA, -90, 90), car("black", TB, -95, 85), car("pearl", TC, -110, 60)]),
    dict(name="T04", loc="track", dur=5, cam=fixed(-8, 0.6, 200, focus="red"),
         cars=[car("red", TA, 30, 250), car("black", TB, 26, 248), car("pearl", TC, 10, 215)]),
    dict(name="T05", loc="track", dur=5, cam=fixed(172, 0.8, 135, focus="black"),
         cars=[car("black", TB, -260, -60), car("red", TA, -272, -62)]),
    dict(name="T06", loc="track", dur=5, cam=pan("red", 35),
         cars=[car("red", TA, -70, 90), car("black", TB, -60, 80)]),
    dict(name="T09", loc="track", dur=5, cam=fixed(172, 1.0, 85, focus="pearl"),
         cars=[car("pearl", TC, -170, -20), car("black", TB, -180, -25)]),
    dict(name="T07", loc="track", dur=5, cam=fixed(-8, 1.0, 35, focus="red"),
         cars=[car("red", TA, 0, 200), car("black", TB, -20, 160)]),
    dict(name="T08", loc="track", dur=6, cam=fixed(-8, 0.5, 135, focus="red"),
         cars=[car("red", TA, 150, 230, "out"), car("black", TB, 135, 212, "out")]),
    dict(name="T10", loc="track", dur=5, cam=fixed(-30, 2.0, 50, focus="red", hold=True),
         cars=[car("red", TA, 14, motion="stop", heading=-1), car("black", TB, 20, motion="stop", heading=-1)]),
    # ---------------- ACTE 4 : LE DERNIER RAYON -----------------------
    dict(name="Y01", loc="canyon", dur=6, cam=fixed(-50, 2.0, 35, hold=True), cars=[]),
    dict(name="Y02", loc="canyon", dur=4, cam=pan("red", 35),
         cars=[car("red", YL, 18, -4)]),
    dict(name="Y03", loc="canyon", dur=6, cam=fixed(-70, 1.5, 50, focus="red"),
         cars=[car("red", YL, -1, YSTOP, "out")]),
    dict(name="Y04", loc="canyon", dur=8, cam=fixed(-62, 2.5, 50, focus="red", hold=True),
         cars=[car("red", YL, YSTOP, motion="stop", heading=-1)]),
    dict(name="Y05", loc="canyon", dur=8, cam=fixed(-75, 4.0, 85, focus="red", hold=True),
         cars=[car("red", YL, YSTOP, motion="stop", heading=-1)]),
]
SHOT_BY_NAME = {s["name"]: s for s in SHOTS}

if "--list" in argv:
    tot = 0
    for s in SHOTS:
        tot += s["dur"]; print(f'{s["name"]} {s["loc"]:8s} {s["dur"]:3d}s  hold={s["cam"].get("hold", False)}  t={tot}s')
    print("TOTAL", tot, "s"); sys.exit(0)

# =====================================================================
#  CONSTRUCTION D'UN PLAN
# =====================================================================
shot = SHOT_BY_NAME[arg("--shot")]
loc = LOCS[shot["loc"]]
TEST = "--test" in argv
NF = S(shot["dur"])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS; scene.frame_start, scene.frame_end = 1, NF

# ---- monde
world = bpy.data.worlds.new("HDRI"); scene.world = world
nt = world.node_tree; N = nt.nodes
env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(ASSETS, loc["hdri"]))
nt.links.new(env.outputs["Color"], N["Background"].inputs["Color"])
if loc["sun"]:
    u, el, energy = loc["sun"]
    az = 2 * math.pi * (u - 0.5); el = math.radians(el)
    d = Vector((math.cos(az) * math.cos(el), -math.sin(az) * math.cos(el), math.sin(el)))
    sl = bpy.data.lights.new("Sun", "SUN"); sl.energy = energy; sl.color = (1.0, 0.72, 0.45); sl.angle = math.radians(0.6)
    so = bpy.data.objects.new("Sun", sl); scene.collection.objects.link(so)
    so.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

# ---- sol
bpy.ops.mesh.primitive_plane_add(size=1200)
ground = bpy.context.active_object; ground.is_shadow_catcher = True
gm = bpy.data.materials.new("Ground"); gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.06, 0.06, 0.06, 1); gb.inputs["Roughness"].default_value = 0.55
ground.data.materials.append(gm)

# ---- voitures
PAINT = {"red": "Carmine", "black": "Graphite", "pearl": "Pearl"}
plate = bpy.data.materials.new("PlateBlank")
plate.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.78, 1)

def emission_input(m):
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED": return n.inputs["Emission Strength"]
        if n.type == "EMISSION": return n.inputs["Strength"]

def import_car(cname):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=CAR_GLB)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(cname, None); scene.collection.objects.link(root)
    body = bpy.data.objects.new(cname + "_Body", None); scene.collection.objects.link(body); body.parent = root
    model = bpy.data.objects.new(cname + "_Model", None); scene.collection.objects.link(model); model.parent = body
    model.rotation_euler.z = math.radians(90)          # avant du modèle (-Y) -> +X
    brake = None
    for o in new:
        if o.parent is None: o.parent = model
        for sl_ in o.material_slots:
            if not sl_.material: continue
            mn = sl_.material.name
            if mn.startswith("Paint ") or mn.startswith("Interior 3"):
                base = mn.split(".")[0].rsplit(" ", 1)[0]
                tgt = bpy.data.materials.get(f"{base} {PAINT[cname]}")
                if tgt: sl_.material = tgt
            elif mn.startswith("License"):
                sl_.material = plate
            elif mn.startswith("Brakelight"):
                if brake is None:
                    brake = sl_.material.copy(); brake.name = cname + "_Brake"
                sl_.material = brake
    wheels = [o for o in new if o.type == "EMPTY" and o.name.split(".")[0] in ("WheelFrontL", "WheelFrontR", "WheelRearL", "WheelRearR")]
    tgt = bpy.data.objects.new(cname + "_Target", None); scene.collection.objects.link(tgt)
    tgt.parent = body; tgt.location = (0, 0, 0.65)
    return root, body, wheels, brake, tgt

def s_of(c, f):
    """position le long de la route à l'image f (1..NF)."""
    t = (f - 1) / max(1, NF - 1); m = c["motion"]
    s0, s1 = c["s0"], c["s1"]
    if m == "stop": return s0
    if m == "lin": return s0 + (s1 - s0) * t
    if m == "out": return s0 + (s1 - s0) * (1 - (1 - t) ** 2)
    if m == "in":  return s0 + (s1 - s0) * t * t
    if m[0] == "launch":
        _, f0, acc = m; dt = max(0.0, (f - f0) / FPS)
        return s0 + 0.5 * acc * dt * dt
    raise ValueError(m)

def linear_keys(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    act = ad.action
    for layer in getattr(act, "layers", []):
        for st in layer.strips:
            for bag in st.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points: k.interpolation = "LINEAR"

CARS = {}
road = loc["road"]
for c in shot["cars"]:
    root, body, wheels, brake, tgt = import_car(c["car"])
    CARS[c["car"]] = tgt
    ss = [s_of(c, f) for f in range(1, NF + 1)]
    smin_f, smax_f = ss[0], ss[-1]
    moving = abs(smax_f - smin_f) > 0.05
    if moving:
        cu = bpy.data.curves.new(c["car"] + "_Path", "CURVE"); cu.dimensions = "3D"
        sp = cu.splines.new("POLY"); n = 120; sp.points.add(n - 1)
        for i in range(n):
            s = smin_f + (smax_f - smin_f) * i / (n - 1)
            x, y = road(s, c["lane"]); sp.points[i].co = (x, y, 0, 1)
        path = bpy.data.objects.new(c["car"] + "_Path", cu); scene.collection.objects.link(path)
        path.hide_render = True
        fp = root.constraints.new("FOLLOW_PATH"); fp.target = path
        fp.use_curve_follow = True; fp.use_fixed_location = True
        fp.forward_axis = "FORWARD_X"; fp.up_axis = "UP_Z"
        for f, s in enumerate(ss, 1):
            fp.offset_factor = (s - smin_f) / (smax_f - smin_f); fp.keyframe_insert("offset_factor", frame=f)
    else:
        x, y = road(smin_f, c["lane"]); x2, y2 = road(smin_f + 1, c["lane"])
        root.location = (x, y, 0)
        hd = c.get("heading", 1)
        root.rotation_euler.z = math.atan2(y2 - y, x2 - x) + (0 if hd > 0 else math.pi)
    # roues, assiette (tangage à l'accélération / freinage), vibrations de la route
    for f, s in enumerate(ss, 1):
        dist = abs(s - ss[0])
        for w in wheels:
            w.rotation_mode = "XYZ"
            if f == 1: w["rx0"] = w.rotation_euler.x
            w.rotation_euler.x = w["rx0"] - dist / WHEEL_R
            w.keyframe_insert("rotation_euler", index=0, frame=f)
        if 1 < f < NF:
            acc = (ss[f] - 2 * s + ss[f - 2]) * FPS * FPS * (1 if smax_f >= smin_f else -1)
        else:
            acc = 0.0
        speed = abs(ss[min(f, NF - 1)] - ss[f - 1]) * FPS
        body.rotation_euler.y = max(-0.03, min(0.03, -0.0022 * acc))
        body.location.z = 0.004 * math.sin(f * 2.3 + hash(c["car"]) % 7) * min(1.0, speed / 10)
        body.keyframe_insert("rotation_euler", index=1, frame=f)
        body.keyframe_insert("location", index=2, frame=f)
        if brake is not None:
            ei = emission_input(brake)
            if ei is not None:
                braking = acc < -1.5 or (c["motion"] == "stop") or (isinstance(c["motion"], tuple) and f < c["motion"][1])
                ei.default_value = 40.0 if braking else 6.0
                ei.keyframe_insert("default_value", frame=f)
    for o in [root, body] + wheels: linear_keys(o)

# ---- caméra
cs = shot["cam"]
cd = bpy.data.cameras.new("Cam"); cd.lens = cs["lens"]; cd.sensor_width = 36
cd.dof.use_dof = True; cd.dof.aperture_fstop = cs.get("fstop", 4.0)
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam)
cam.location = (0, 0, loc["h"]); scene.camera = cam
if cs["type"] == "pan":
    tgt = CARS[cs["target"]]
    tt = cam.constraints.new("TRACK_TO"); tt.target = tgt
    tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
    cd.dof.focus_object = tgt
else:
    cam.rotation_euler = (math.radians(90 - cs["pitch"]), 0, math.radians(cs["yaw"] - 90))
    if cs.get("focus"): cd.dof.focus_object = CARS[cs["focus"]]
    else: cd.dof.use_dof = False

# ---- rendu
r = scene.render
r.engine = "CYCLES"
cy = scene.cycles
cy.device = "CPU"
cy.samples = int(arg("--samples", 6))
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True
cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 3; cy.transmission_bounces = 4
cy.caustics_reflective = cy.caustics_refractive = False
r.resolution_x, r.resolution_y = (640, 360) if TEST else (960, 540)
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.use_persistent_data = True
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"

OUT = os.path.join(HERE, "renders", "test" if TEST else "shots", shot["name"])
os.makedirs(OUT, exist_ok=True)
# trajectoires (pour le mixage audio : volume / effet Doppler des moteurs)
import json
traj = {}
for c in shot["cars"]:
    traj[c["car"]] = [list(road(s_of(c, f), c["lane"])) for f in range(1, NF + 1)]
with open(os.path.join(OUT, "traj.json"), "w") as fh:
    json.dump(dict(fps=FPS, frames=NF, cam=[0, 0, loc["h"]], cars=traj), fh)
if cs.get("hold"):
    scene.frame_set(1)
    r.filepath = os.path.join(OUT, "hold.png")
    bpy.ops.render.render(write_still=True)
elif arg("--frames"):
    for f in [int(x) for x in arg("--frames").split(",")]:
        scene.frame_set(f); r.filepath = os.path.join(OUT, f"f_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    r.use_overwrite = False; r.use_placeholder = True
    r.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)
print("SHOT DONE", shot["name"])
