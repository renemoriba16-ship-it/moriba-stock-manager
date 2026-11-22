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
  instagram: "https://instagram.com/ruskov",
  price: 180000,            // prix unique de tous les maillots (en GNF)
};

/* ---------------------------------------------------------
   CATALOGUE
   pattern : "plain" | "stripes" | "hoops" | "sash" | "halves" | "chevron"
   colors  : [couleur principale, couleur secondaire, couleur du texte]
   category: "club" | "selection"
   stock   : nombre d'unités disponibles (0 = rupture)
   photo     : (optionnel) photo de face, ex : "images/p01.jpg"
   photoBack : (optionnel) photo de dos,  ex : "images/p01-dos.jpg"
               → sans photo, le maillot est dessiné automatiquement avec les couleurs
   (le prix est le même pour tous : voir "price" plus haut)
   --------------------------------------------------------- */
window.PRODUCTS = [
  { id: "p01", name: "Maillot Domicile Royal",    category: "club",      season: "25/26", pattern: "stripes", colors: ["#0b1f6b", "#d11f2f", "#ffffff"], stock: 12, badge: "Best-seller" },
  { id: "p02", name: "Maillot Extérieur Ivoire",  category: "club",      season: "25/26", pattern: "plain",   colors: ["#f4efe3", "#1b1b1b", "#1b1b1b"], stock: 8 },
  { id: "p03", name: "Maillot Third Néon",        category: "club",      season: "25/26", pattern: "chevron", colors: ["#111111", "#c6ff00", "#c6ff00"], stock: 5, badge: "Nouveau" },
  { id: "p04", name: "Sélection Lions Verts",     category: "selection", season: "2026",  pattern: "sash",    colors: ["#0f8a3c", "#ffd200", "#ffffff"], stock: 15, badge: "Coupe 2026" },
  { id: "p05", name: "Sélection Éléphants",       category: "selection", season: "2026",  pattern: "halves",  colors: ["#ff7a00", "#ffffff", "#0f5132"], stock: 10 },
  { id: "p06", name: "Sélection Aigles",          category: "selection", season: "2026",  pattern: "hoops",   colors: ["#d11f2f", "#ffd200", "#ffffff"], stock: 0 },
  { id: "p10", name: "Maillot Gardien Magma",     category: "club",      season: "25/26", pattern: "chevron", colors: ["#ff3d00", "#2b0a00", "#ffffff"], stock: 7 },
  { id: "p11", name: "Sélection Étoile Noire",    category: "selection", season: "2026",  pattern: "sash",    colors: ["#111111", "#c8a24a", "#c8a24a"], stock: 9 },
];

window.PRODUCTS.forEach((p) => { if (p.price === undefined) p.price = window.SHOP.price; });
