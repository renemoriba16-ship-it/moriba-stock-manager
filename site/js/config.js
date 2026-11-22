/* =========================================================
   CONFIGURATION DE LA BOUTIQUE — modifie ce fichier librement
   ========================================================= */
window.SHOP = {
  name: "SENSEY’S JERSEYS",
  backName: "SENSEY",       // nom affiché au dos des maillots d'exemple
  tagline: "Maillots de foot — Clubs & Sélections",
  currency: "GNF",          // ex : "GNF", "€", "FCFA"
  currencyAfter: true,      // true => "35 €", false => "€35"
  whatsapp: "224626759433",  // numéro WhatsApp au format international, sans + ni espaces
  email: "renemoriba16@gmail.com",
  instagram: "https://instagram.com/rene_moriba",
  showPrices: false,        // false = aucun prix affiché (prix donné sur WhatsApp) ; true = prix visibles
  price: 180000,            // prix unique de tous les maillots (en GNF), utilisé si showPrices: true
};

/* ---------------------------------------------------------
   CATALOGUE
   name      : nom affiché
   category  : "club" | "selection"
   photo     : photo de face (dans le dossier images/)
   photoBack : (optionnel) photo de dos — le maillot se retourne au survol
   fit       : "cover" pour les photos sur fond gris / photos portées
   status    : "commande" (par défaut) | "stock" | "bientot"
               - commande : vendu sur commande, quantité libre
               - stock    : en stock, préciser stock: 5 (0 = rupture)
               - bientot  : visible mais pas encore commandable
   colors    : couleurs du maillot (lueur autour de la photo)
   tex3d     : (optionnel) texture du maillot 3D de l'accueil, créée par blender/textures.py
   Le prix est le même pour tous : voir "price" plus haut.
   --------------------------------------------------------- */
window.PRODUCTS = [
  // ---- Sélections ----
  { id: "fra-dom", tex3d: "models/tex/fra-dom.webp", name: "France Domicile",       category: "selection", photo: "images/france-domicile.webp",      colors: ["#1b2a8f", "#ffffff"] },
  { id: "fra-ext", tex3d: "models/tex/fra-ext.webp", name: "France Extérieur",      category: "selection", photo: "images/france-exterieur.webp",     colors: ["#bfe6d6", "#c0392b"] },
  { id: "bra-dom", name: "Brésil Domicile",       category: "selection", photo: "images/bresil-domicile.webp",    photoBack: "images/bresil-domicile-dos.webp",    fit: "cover", colors: ["#f5d90a", "#0b6b4a"] },
  { id: "bra-ext", name: "Brésil Extérieur",      category: "selection", photo: "images/bresil-exterieur.webp",   photoBack: "images/bresil-exterieur-dos.webp",   fit: "cover", colors: ["#1b3aa8", "#0b1640"] },
  { id: "por-dom", name: "Portugal Domicile",     category: "selection", photo: "images/portugal-domicile.webp",  photoBack: "images/portugal-domicile-dos.webp",  fit: "cover", colors: ["#c8102e", "#1e8f8f"] },
  { id: "por-ext", name: "Portugal Extérieur",    category: "selection", photo: "images/portugal-exterieur.webp", photoBack: "images/portugal-exterieur-dos.webp", fit: "cover", colors: ["#3fc1b5", "#ffffff"] },
  { id: "ang-dom", tex3d: "models/tex/ang-dom.webp", name: "Angleterre Domicile",   category: "selection", photo: "images/angleterre-domicile.webp",  colors: ["#f2f2f2", "#1b2240"] },
  { id: "ang-ext", tex3d: "models/tex/ang-ext.webp", name: "Angleterre Extérieur",  category: "selection", photo: "images/angleterre-exterieur.webp", colors: ["#e3202b", "#1b2240"] },
  { id: "bel-dom", tex3d: "models/tex/bel-dom.webp", name: "Belgique Domicile",     category: "selection", photo: "images/belgique-domicile.webp",    colors: ["#d10f0f", "#f2c200"] },
  // ---- Clubs ----
  { id: "psg-dom", tex3d: "models/tex/psg-dom.webp", name: "PSG Domicile",              category: "club", photo: "images/psg-domicile.webp",               colors: ["#1f4fd1", "#e3202b"] },
  { id: "psg-ext", name: "PSG Extérieur",             category: "club", photo: "images/psg-exterieur.webp", fit: "cover", colors: ["#f2f2f2", "#c8102e"] },
  { id: "bar-dom", tex3d: "models/tex/bar-dom.webp", name: "FC Barcelone Domicile",     category: "club", photo: "images/barcelone-domicile.webp",         colors: ["#a50044", "#004d98"] },
  { id: "rma-3rd", tex3d: "models/tex/rma-3rd.webp", name: "Real Madrid Third",         category: "club", photo: "images/real-madrid-third.webp",          colors: ["#1f4a45", "#e8dfc8"] },
  { id: "mun-dom", tex3d: "models/tex/mun-dom.webp", name: "Manchester United Domicile", category: "club", photo: "images/manchester-united-domicile.webp", colors: ["#c70101", "#ffffff"] },
  { id: "che-dom", tex3d: "models/tex/che-dom.webp", name: "Chelsea Domicile",          category: "club", photo: "images/chelsea-domicile.webp",           colors: ["#1438b8", "#e9b51e"] },
  { id: "bay-dom", tex3d: "models/tex/bay-dom.webp", name: "Bayern Munich Domicile",    category: "club", photo: "images/bayern-domicile.webp",            colors: ["#dc052d", "#ffffff"] },
  { id: "juv-3rd", name: "Juventus Third",            category: "club", photo: "images/juventus-third.webp", fit: "cover", status: "bientot", colors: ["#f4a6c6", "#111111"] },
];

window.PRODUCTS.forEach((p) => {
  if (p.price === undefined) p.price = window.SHOP.price;
  if (!p.status) p.status = "commande";
  if (!p.pattern) p.pattern = "plain";
  if (p.colors.length < 3) p.colors = [p.colors[0], p.colors[1], p.colors[1]];
});
