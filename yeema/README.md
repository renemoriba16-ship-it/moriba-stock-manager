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
- Qualité d'image : occlusion ambiante précalculée dans Blender (couleurs de sommets), textures procédurales
  de feuilles, d'écorce et de litière avec normal maps, translucidité des feuilles à contre-jour, ombres
  portées avec canopée, rayons de soleil (diffusion en espace écran), ciel lumineux derrière la canopée,
  brume au sol, rendu AgX, feuilles cirées (clear coat) aux teintes variées, bloom, étalonnage, vignettage et grain.
  La qualité s'adapte à l'appareil (`?q=low|mid|high` pour la forcer).
- Fluidité : végétation découpée en tranches de 15 m (seules celles à l'écran et hors de la brume sont
  dessinées), ombres recalculées seulement quand on avance, résolution dynamique, shaders précompilés
  pendant le chargement, modèles allégés (~1,5 M triangles par image au lieu de 7,6 M).
- Faune et fleurs (`blender/jungle_life.py`) : hibiscus, orchidées, papillons qui fuient le pointeur,
  aras perchés qui s'envolent quand on approche ou qu'on clique dessus.
- Son d'ambiance synthétisé en Web Audio (vent dans les feuilles, insectes, chants d'oiseaux, cris d'aras),
  activé par le bouton « Son de la jungle » (aucun fichier audio).
