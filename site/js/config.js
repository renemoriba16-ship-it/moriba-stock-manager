/* =========================================================
   CONFIGURATION DE LA BOUTIQUE — modifie ce fichier librement
   ========================================================= */
window.SHOP = {
  name: "MORIBA",
  tagline: "Maillots de foot — Club, Sélections & Rétro",
  currency: "€",            // ex : "€", "FCFA", "$"
  currencyAfter: true,      // true => "35 €", false => "€35"
  whatsapp: "33600000000",  // numéro WhatsApp au format international, sans + ni espaces
  email: "contact@exemple.com",
  instagram: "https://instagram.com/",
  flocagePrice: 10,         // prix du flocage nom + numéro
  freeShippingFrom: 80,     // livraison offerte à partir de ce montant
  shippingPrice: 6,
};

/* ---------------------------------------------------------
   CATALOGUE
   pattern : "plain" | "stripes" | "hoops" | "sash" | "halves" | "chevron"
   colors  : [couleur principale, couleur secondaire, couleur du texte]
   category: "club" | "selection" | "retro"
   stock   : nombre d'unités disponibles (0 = rupture)
   --------------------------------------------------------- */
window.PRODUCTS = [
  { id: "p01", name: "Maillot Domicile Royal",    category: "club",      season: "25/26", price: 45, oldPrice: 60, pattern: "stripes", colors: ["#0b1f6b", "#d11f2f", "#ffffff"], stock: 12, badge: "Best-seller" },
  { id: "p02", name: "Maillot Extérieur Ivoire",  category: "club",      season: "25/26", price: 45, pattern: "plain",   colors: ["#f4efe3", "#1b1b1b", "#1b1b1b"], stock: 8 },
  { id: "p03", name: "Maillot Third Néon",        category: "club",      season: "25/26", price: 50, pattern: "chevron", colors: ["#111111", "#c6ff00", "#c6ff00"], stock: 5, badge: "Nouveau" },
  { id: "p04", name: "Sélection Lions Verts",     category: "selection", season: "2026",  price: 55, pattern: "sash",    colors: ["#0f8a3c", "#ffd200", "#ffffff"], stock: 15, badge: "Coupe 2026" },
  { id: "p05", name: "Sélection Éléphants",       category: "selection", season: "2026",  price: 55, pattern: "halves",  colors: ["#ff7a00", "#ffffff", "#0f5132"], stock: 10 },
  { id: "p06", name: "Sélection Aigles",          category: "selection", season: "2026",  price: 55, pattern: "hoops",   colors: ["#d11f2f", "#ffd200", "#ffffff"], stock: 0 },
  { id: "p07", name: "Rétro 1998 Bleu Nuit",      category: "retro",     season: "1998",  price: 65, pattern: "plain",   colors: ["#13235b", "#ffffff", "#ffffff"], stock: 4, badge: "Édition limitée" },
  { id: "p08", name: "Rétro 1986 Rayé",           category: "retro",     season: "1986",  price: 60, pattern: "stripes", colors: ["#ffffff", "#2a6fd6", "#111111"], stock: 6 },
  { id: "p09", name: "Rétro 2002 Cerclé",         category: "retro",     season: "2002",  price: 60, oldPrice: 75, pattern: "hoops", colors: ["#0b6b3a", "#ffffff", "#ffffff"], stock: 3 },
  { id: "p10", name: "Maillot Gardien Magma",     category: "club",      season: "25/26", price: 50, pattern: "chevron", colors: ["#ff3d00", "#2b0a00", "#ffffff"], stock: 7 },
  { id: "p11", name: "Sélection Étoile Noire",    category: "selection", season: "2026",  price: 55, pattern: "sash",    colors: ["#111111", "#c8a24a", "#c8a24a"], stock: 9 },
  { id: "p12", name: "Rétro 1994 Bordeaux",       category: "retro",     season: "1994",  price: 60, pattern: "halves",  colors: ["#6b0f2a", "#e8d9b0", "#e8d9b0"], stock: 5 },
];
