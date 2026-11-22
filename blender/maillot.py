"""
Modélisation du maillot 3D du site (Blender 5.x, exécutable sans interface).

    python blender/maillot.py            # avec le module bpy (pip install bpy)
    blender -b -P blender/maillot.py     # ou avec Blender installé

Étapes :
 1. silhouette 2D du maillot (face) -> épaisseur -> remaillage uniforme
 2. simulation de tissu avec pression : le maillot « gonfle » comme un vrai vêtement
 3. lissage, coordonnées UV (face à gauche de la texture, dos à droite)
 4. export site/models/maillot.glb (la texture est dessinée en direct par le site)
"""
import math
import os

import bpy
import bmesh
from mathutils import Vector

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "models", "maillot.glb")

# ---------------------------------------------------------------- scène vide
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- 1. silhouette
# Demi-silhouette (côté droit), du milieu du col jusqu'au milieu du bas. Unités ~ mètres.
half = [
    (0.00, 0.62),   # creux du col (devant)
    (0.10, 0.66), (0.17, 0.72), (0.21, 0.78),   # bord du col
    (0.34, 0.75), (0.48, 0.70),                 # épaule
    (0.62, 0.62), (0.78, 0.48), (0.88, 0.36),   # manche (dessus)
    (0.80, 0.28), (0.70, 0.20),                 # bout de manche
    (0.56, 0.30), (0.46, 0.36),                 # dessous de manche -> aisselle
    (0.45, 0.10), (0.45, -0.20), (0.46, -0.50), (0.47, -0.72),  # flanc
    (0.30, -0.75), (0.15, -0.76), (0.00, -0.76),                 # bas
]
outline = half + [(-x, y) for (x, y) in reversed(half[1:-1])]

# Si blender/textures.py a calculé la silhouette moyenne des photos, on l'utilise :
# chaque photo de maillot épouse alors parfaitement le modèle.
SIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silhouette.json")
if os.path.exists(SIL):
    import json
    outline = [tuple(p) for p in json.load(open(SIL))["outline"]]
    print("silhouette des photos :", len(outline), "points")

mesh = bpy.data.meshes.new("contour")
bm = bmesh.new()
verts = [bm.verts.new((x, y, 0.0)) for (x, y) in outline]
bm.faces.new(verts)
bm.to_mesh(mesh)
bm.free()
obj = bpy.data.objects.new("Maillot", mesh)
scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

def apply(mod):
    bpy.ops.object.modifier_apply(modifier=mod.name)

sol = obj.modifiers.new("epaisseur", "SOLIDIFY")
sol.thickness = 0.06
sol.offset = 0.0
apply(sol)

rem = obj.modifiers.new("remaillage", "REMESH")
rem.mode = "VOXEL"
rem.voxel_size = 0.018
apply(rem)

# ---------------------------------------------------------------- 2. volume
# On garde la silhouette exacte et on « gonfle » selon la distance au bord :
# le torse est épais, les manches plus fines, les bords arrondis comme un vrai tissu.
segs = [(Vector((*outline[i], 0)), Vector((*outline[(i + 1) % len(outline)], 0))) for i in range(len(outline))]

def dist_to_outline(x, y):
    p = Vector((x, y, 0))
    best = 1e9
    for a, b in segs:
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        best = min(best, (a + ab * t - p).length)
    return best

THICK = 0.15   # demi-épaisseur max du torse
REACH = 0.26   # distance au bord où l'épaisseur max est atteinte
for v in obj.data.vertices:
    x, y, z = v.co
    side = 1 if z >= 0 else -1
    d = dist_to_outline(x, y)
    f = min(1.0, d / REACH)
    f = math.sin(f * math.pi / 2) ** 0.8          # arrondi doux
    puff = 0.012 + THICK * f
    if side > 0:
        puff *= 1.0 + 0.15 * max(0.0, 1 - abs(y - 0.15) / 0.7)   # poitrine un peu plus bombée
    wrap = -0.22 * x * x                           # le maillot s'enroule comme sur un corps
    fold = 0.012 * math.sin(7 * y + 3 * x) * f      # légers plis du tissu
    v.co.z = side * puff + wrap + fold

# ---------------------------------------------------------------- 3. lissage + UV
sm = obj.modifiers.new("lissage", "SMOOTH")
sm.factor = 0.6
sm.iterations = 4
apply(sm)

dec = obj.modifiers.new("allegement", "DECIMATE")
dec.ratio = 0.5
apply(dec)

for p in obj.data.polygons:
    p.use_smooth = True

# Centrage + mise à l'échelle (hauteur ~ 2 unités)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
obj.location = (0, 0, 0)
dims = obj.dimensions
k = 2.0 / dims.y
obj.scale = (k, k, k)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

xs = [v.co.x for v in obj.data.vertices]
ys = [v.co.y for v in obj.data.vertices]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

uv = obj.data.uv_layers.new(name="UVMap")
for poly in obj.data.polygons:
    front = poly.center.z >= 0
    for li in poly.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        xn = (co.x - minx) / (maxx - minx)
        yn = (co.y - miny) / (maxy - miny)
        # face : moitié gauche ; dos : moitié droite, inversé pour se lire de dos
        u = xn * 0.5 if front else 0.5 + (1 - xn) * 0.5
        uv.data[li].uv = (u, yn)

# Debout : dans Blender la hauteur est sur Z (le glTF la convertit en Y, face vers +Z)
obj.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

mat = bpy.data.materials.new("Tissu")
obj.data.materials.append(mat)

# ---------------------------------------------------------------- 4. export
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT,
    export_format="GLB",
    use_selection=True,
    export_yup=True,
    export_normals=True,
    export_texcoords=True,
    export_materials="PLACEHOLDER",
    export_draco_mesh_compression_enable=False,
)
print("OK", OUT, len(obj.data.vertices), "sommets,", len(obj.data.polygons), "faces")
