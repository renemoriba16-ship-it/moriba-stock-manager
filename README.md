# Moriba Stock Manager

Bienvenue dans le projet Moriba Stock Manager!

## Description

Ce projet est une application de gestion de stock.

## Installation

Pour installer ce projet, clonez le dépôt et installez les dépendances.

```bash
git clone https://github.com/renemoriba16-ship-it/moriba-stock-manager.git
cd moriba-stock-manager
```

## Utilisation

Utilisez les commandes disponibles pour gérer votre stock.

## Contribuer

Les contributions sont les bienvenues! N'hésitez pas à soumettre des pull requests.

## Licence

Ce projet est sous licence MIT.

## 🛍️ Site boutique « Motion » (dossier `site/`)

Site vitrine animé pour la vente de maillots, 100 % statique (HTML/CSS/JS, aucune installation).

**Lancer :** ouvre `site/index.html` dans ton navigateur, ou héberge le dossier `site/` (Netlify, GitHub Pages…).

**Fonctionnalités**
- Hero animé : titre qui monte, maillot 3D qui suit la souris et change de modèle, compteurs, marquee
- Catalogue avec filtres (Clubs / Sélections), recherche et tri ; les maillots se retournent au survol
- Prix unique : tous les maillots à 180 000 GNF
- Fiche produit : choix de taille et quantité
- Panier animé (sauvegardé dans le navigateur), gestion du stock
- Livraison selon le lieu du client, prix confirmé sur WhatsApp
- Commande envoyée directement sur **WhatsApp** avec le récapitulatif complet
- Responsive mobile, respecte « réduire les animations »

**Maillot 3D (Blender + three.js)**
- `blender/textures.py` détoure les photos des maillots (fond blanc), calcule leur silhouette moyenne
  (`blender/silhouette.json`) et crée les textures 3D (face + dos) dans `site/models/tex/`.
- `blender/maillot.py` construit le modèle 3D dans Blender avec cette silhouette et l'exporte dans `site/models/maillot.glb`.
- Pour tout régénérer : `pip install bpy numpy opencv-python-headless pillow`, puis
  `python blender/textures.py` et `python blender/maillot.py`.
- Ajouter un maillot à la 3D : photo sur fond blanc dans `site/images/`, une ligne dans `JERSEYS` (textures.py),
  relancer les deux scripts, et ajouter `tex3d: "models/tex/<id>.webp"` au produit dans `config.js`.
- Le site l'affiche en direct avec three.js (`site/js/jersey3d.js`, bibliothèque copiée dans `site/vendor/three/`) :
  il flotte, suit la souris, se fait tourner au doigt, passe d'un maillot du catalogue à l'autre (avec un bouton pour ouvrir sa fiche) et montre le dos quand on défile.
- La 3D ne fonctionne qu'en ligne (ou via un petit serveur local, ex. `python3 -m http.server` dans `site/`) ;
  en ouvrant `index.html` directement, le carrousel photo s'affiche à la place.

**Personnaliser :** tout se règle dans `site/js/config.js` — nom de la boutique, numéro WhatsApp, e-mail, Instagram, devise, prix unique des maillots, et la liste des maillots (nom, couleurs, motif, stock).
