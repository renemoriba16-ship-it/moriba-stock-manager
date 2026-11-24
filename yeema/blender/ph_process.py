# Prepare free Poly Haven (CC0) scanned plants for the real-time jungle: pick variants, decimate, shrink textures, ground, export GLB
import sys, os, bpy
from mathutils import Vector
SRC, OUT = sys.argv[1], sys.argv[2]
JOBS = [  # (asset, objects to keep, output name, triangle budget per object)
    ('anthurium_botany_01', ['anthurium_botany_01_a'], 'ph_anthurium_a', {'*': 4500}),
    ('anthurium_botany_01', ['anthurium_botany_01_c'], 'ph_anthurium_c', {'*': 3500}),
    ('calathea_orbifolia_01', ['calathea_orbifolia_01_a'], 'ph_calathea_a', {'*': 4000}),
    ('calathea_orbifolia_01', ['calathea_orbifolia_01_b'], 'ph_calathea_b', {'*': 3500}),
    ('fern_02', ['fern_02_b'], 'ph_fern_b', {'*': 2400}),
    ('fern_02', ['fern_02_c'], 'ph_fern_c', {'*': 2300}),
    ('pachira_aquatica_01', ['pachira_aquatica_01_bark_d', 'pachira_aquatica_01_leaves_d'], 'ph_pachira_d', {'pachira_aquatica_01_bark_d': 1800, 'pachira_aquatica_01_leaves_d': 7000}),
    ('pachira_aquatica_01', ['pachira_aquatica_01_bark_c', 'pachira_aquatica_01_leaves_c'], 'ph_pachira_c', {'pachira_aquatica_01_bark_c': 1500, 'pachira_aquatica_01_leaves_c': 5500}),
    ('rock_moss_set_02', ['rock_moss_set_02_rock11'], 'ph_rock_a', {'*': 3000}),
    ('rock_moss_set_02', ['rock_moss_set_02_rock13'], 'ph_rock_b', {'*': 3000}),
    ('tree_stump_01', ['tree_stump_01'], 'ph_stump', {'*': 4000}),
    ('dead_tree_trunk', ['dead_tree_trunk'], 'ph_deadtrunk', {'*': 5000}),
]
tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
for asset, keep, out, budget in JOBS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f"{SRC}/{asset}/{asset}_1k.gltf")
    for o in list(bpy.context.scene.objects):
        if o.type == 'MESH' and o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects: o.select_set(o.type == 'MESH')
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    before = sum(tris(o) for o in obs)
    for o in obs:
        b = budget.get(o.name, budget.get('*'))
        if tris(o) > b:
            d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = b / tris(o); d.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="dec")
    for o in bpy.context.scene.objects: o.select_set(o.type == 'MESH')
    if len(obs) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for v in ob.data.vertices: v.co -= off
    for img in bpy.data.images:
        if img.size[0] > 512: img.scale(512, 512)
    ob.name = out
    bpy.ops.export_scene.gltf(filepath=f"{OUT}/{out}.glb", export_format='GLB', export_apply=True, export_image_format='WEBP', export_image_quality=80, export_cameras=False, export_lights=False)
    print("PH", out, before, "->", tris(ob), "tris", round(os.path.getsize(f"{OUT}/{out}.glb") / 1e6, 2), "MB", "dims", [round(x, 2) for x in (mx - mn)], [m.name for m in ob.data.materials])
