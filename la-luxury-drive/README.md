# LA Luxury Drive (Blender)

Scène 100 % procédurale : un boulevard de Los Angeles à l'heure dorée, avec des voitures de luxe.

- `SCENARIO.md` : le scénario et le découpage plan par plan
- `build_scene.py` : le script qui génère toute la scène (route, palmiers, bâtiments, voitures, caméras, animation)
- `la_luxury_drive.blend` : le fichier à ouvrir directement dans Blender 5.x
- `renders/` : les images HD des 4 plans et la vidéo `la_luxury_drive.mp4`

## Régénérer

```bash
blender -b -P build_scene.py -- --stills          # 4 images 1280x720
blender -b -P build_scene.py -- --anim            # animation 120 images -> renders/frames/
ffmpeg -framerate 24 -i renders/frames/f_%04d.png -pix_fmt yuv420p renders/la_luxury_drive.mp4
```
Options : `--preview` (24 samples), `--test` (640x360, rapide).
