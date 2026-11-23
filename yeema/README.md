# yeema — site motion

Site vitrine pour la marque de soins capillaires **yeema** (cheveux bouclés, frisés, crépus).

- `index.html` — page unique (three.js, GSAP + ScrollTrigger, Lenis via CDN).
- `assets/3d/` — modèles 3D Blender de la jungle et du flacon (scène temps réel de l'ouverture).
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

## Jungle 3D (ouverture du site)

L'ouverture est une scène 3D temps réel (three.js 0.160, chargé depuis jsDelivr) :
le défilement fait avancer la caméra sur un sentier à travers la jungle jusqu'à une clairière
où le flacon est posé sur un rocher moussu. La souris permet de regarder autour, et les feuilles
s'écartent autour du pointeur ; le vent s'intensifie quand on bouge.

- `assets/3d/*.glb` — modèles exportés de Blender : palmier, bananier, monstera, fougère, colocasia,
  arbre géant à contreforts, liane, rocher moussu et flacon d'huile.
- Générés par `blender/jungle.py <dossier_scripts> <dossier_sortie>`.
- Le vent et l'écartement des feuilles sont calculés dans le vertex shader (instanciation GPU).
