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

## Environnement savane

- `assets/plants/palm_a`, `palm_b` — deux cocotiers animés (48 images chacun, boucle de vent) lus dans un canvas : la vitesse du vent suit les mouvements de la souris, un clic secoue le palmier et fait tomber des folioles.
- `assets/plants/baobab.webp`, `aloe.webp`, `grass.webp` — baobabs à l'horizon, aloe et herbe de savane au premier plan.
- `assets/plants/shadow.webp` — ombre de palmes qui ondule sur la boutique et le rituel.
- Généré par `blender/plants.py <dossier> palm,baobab,aloe,grass,shadow`.
