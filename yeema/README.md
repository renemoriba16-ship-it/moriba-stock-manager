# yeema — site motion

Site vitrine pour la marque de soins capillaires **yeema** (cheveux bouclés, frisés, crépus).

- `index.html` — page unique (GSAP + ScrollTrigger + Lenis via CDN).
- `assets/hero/` — 120 images rendues dans Blender, lues au scroll (flacon qui tourne, pipette qui se dévisse, goutte d'huile).
- `assets/products/` — rendus Blender des trois produits et photo de groupe.
- `assets/oil-loop.mp4` — boucle d'huile dorée (métaballes Blender) pour la section ingrédients.
- `blender/` — scripts Python Blender (`bpy` 5.1) qui génèrent toutes les scènes et étiquettes.

## Lancer en local

```bash
cd yeema && python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

## Régénérer les animations

```bash
pip install bpy==5.1.2
python3 blender/labels.py <dossier>        # étiquettes (polices Fraunces + Inter dans <dossier>/fonts)
python3 blender/hero.py <dossier> anim 1 120
python3 blender/products.py <dossier>
python3 blender/blob.py <dossier>
```
