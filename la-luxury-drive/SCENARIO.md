# « Golden Hour Boulevard » : scénario

**Lieu :** un boulevard de Los Angeles bordé de palmiers, 4 voies, boutiques en stucco pastel et enseignes néon, collines en arrière-plan.
**Moment :** l'heure dorée, avec le soleil à 6° au-dessus de l'horizon, une lumière orange rasante et un ciel bleu-rose.
**Durée :** 5 secondes (120 images à 24 i/s), soit 4 plans.

## Casting automobile (designs génériques, aucune marque)

| Nom dans la scène | Type | Couleur | Rôle |
|---|---|---|---|
| Hero_Rosso | Supercar à aileron | Rouge métallisé | Voiture héros, voie de gauche |
| GT_Noir | Grand tourisme | Noir | Suit le héros, voie de droite |
| Cabrio_Bleu | Cabriolet, sièges cuir | Bleu nuit | Devant, voie de droite |
| SUV_Blanc | SUV de luxe | Blanc nacré | Ferme le convoi |
| Super_Giallo | Supercar | Jaune | Sens inverse |
| GT_Vert | Grand tourisme | Vert anglais | Sens inverse |
| SUV_Noir | SUV de luxe | Noir | Sens inverse |

## Découpage

| # | Images | Caméra | Description |
|---|---|---|---|
| 1 | 1 à 30 | `CAM_01_Establishing`, 24 mm, fixe | Depuis le trottoir, à hauteur d'homme. La perspective du boulevard s'étend avec ses palmiers et ses vitrines, et le convoi arrive au loin, phares allumés. |
| 2 | 31 à 60 | `CAM_02_Tracking`, 35 mm, travelling | Caméra basse accrochée à la supercar rouge, en 3/4 avant. Les palmiers défilent avec du flou de mouvement et les reflets du ciel glissent sur la carrosserie. |
| 3 | 61 à 90 | `CAM_03_Rear`, 50 mm, travelling | 3/4 arrière, avec la bande de feux rouges et l'aileron. Le cabriolet bleu est visible dans la voie voisine et la double ligne jaune file vers l'horizon. |
| 4 | 91 à 120 | `CAM_04_Drone`, 28 mm, montée | Plan drone qui s'élève au-dessus du boulevard. On voit tout le convoi et la circulation en sens inverse entre les palmes. |

Le changement de caméra se fait grâce aux **marqueurs de la timeline** liés aux caméras.

## Pistes pour aller plus loin
- **Musique / son :** une piste synthwave à environ 100 BPM, avec le son du moteur V12 en montée sur le plan 2.
- **Modèles réalistes :** remplacer les voitures procédurales par des modèles importés (Sketchfab, BlenderKit). Il suffit de les parenter aux empties `Hero_Rosso`, etc., et l'animation est conservée.
- **Ciel HDRI :** remplacer le nœud Sky par une HDRI de coucher de soleil (Poly Haven).
- **Post-production :** étalonnage teal/orange, grain et léger halo des feux dans DaVinci Resolve ou le Compositor de Blender.
