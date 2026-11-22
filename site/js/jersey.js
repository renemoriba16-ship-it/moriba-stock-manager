/* Génère un maillot en SVG (face ou dos) à partir des données produit */
(function () {
  let uid = 0;
  const BODY = "M62 12 L38 20 L4 48 L24 86 L44 76 L44 214 Q100 222 156 214 L156 76 L176 86 L196 48 L162 20 L138 12 Q100 40 62 12 Z";

  function pattern(p, c1, c2) {
    switch (p.pattern) {
      case "stripes":
        return Array.from({ length: 7 }, (_, i) => i % 2 ? `<rect x="${i * 29}" y="0" width="29" height="230" fill="${c2}"/>` : "").join("");
      case "hoops":
        return Array.from({ length: 8 }, (_, i) => i % 2 ? `<rect x="0" y="${i * 28}" width="200" height="28" fill="${c2}"/>` : "").join("");
      case "sash":
        return `<polygon points="30,0 75,0 200,170 200,230 170,230" fill="${c2}"/>`;
      case "halves":
        return `<rect x="100" y="0" width="100" height="230" fill="${c2}"/>`;
      case "chevron":
        return `<polygon points="0,60 100,120 200,60 200,92 100,152 0,92" fill="${c2}"/>`;
      default:
        return `<rect x="0" y="180" width="200" height="8" fill="${c2}" opacity=".9"/>`;
    }
  }

  window.jerseySVG = function (p, opts = {}) {
    const id = "j" + ++uid;
    const [c1, c2, c3] = p.colors;
    const side = opts.side || "front";
    const name = (opts.name || "").toUpperCase().slice(0, 12);
    const num = opts.number === undefined || opts.number === "" ? "" : String(opts.number).slice(0, 2);
    const collar = side === "front"
      ? `<path d="M62 12 Q100 40 138 12 Q100 52 62 12Z" fill="${c2}"/>`
      : `<path d="M66 13 Q100 26 134 13" stroke="${c2}" stroke-width="6" fill="none"/>`;
    let print = "";
    if (side === "front") {
      print = `
        <circle cx="128" cy="70" r="11" fill="none" stroke="${c3}" stroke-width="2.5"/>
        <path d="M122 70 l4 4 l8 -9" stroke="${c3}" stroke-width="2.5" fill="none"/>
        <text x="72" y="76" font-family="Anton, Impact, sans-serif" font-size="13" fill="${c3}" text-anchor="middle">${p.season || ""}</text>
        <text x="100" y="128" font-family="Anton, Impact, sans-serif" font-size="22" letter-spacing="3" fill="${c3}" text-anchor="middle" opacity=".95">${window.SHOP ? window.SHOP.name : ""}</text>
        ${num ? `<text x="100" y="168" font-family="Anton, Impact, sans-serif" font-size="26" fill="${c3}" text-anchor="middle">${num}</text>` : ""}`;
    } else {
      print = `
        ${name ? `<text x="100" y="72" font-family="Anton, Impact, sans-serif" font-size="${name.length > 8 ? 17 : 21}" letter-spacing="2" fill="${c3}" text-anchor="middle">${escapeXML(name)}</text>` : ""}
        ${num ? `<text x="100" y="168" font-family="Anton, Impact, sans-serif" font-size="88" fill="${c3}" text-anchor="middle" stroke="${c1}" stroke-width="1.5">${num}</text>` : ""}`;
    }
    return `
<svg class="jersey-svg" viewBox="0 0 200 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escapeXML(p.name)}">
  <defs>
    <clipPath id="${id}c"><path d="${BODY}"/></clipPath>
    <linearGradient id="${id}s" x1="0" x2="1">
      <stop offset="0" stop-color="#000" stop-opacity=".22"/>
      <stop offset=".25" stop-color="#fff" stop-opacity=".10"/>
      <stop offset=".55" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity=".28"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#${id}c)">
    <rect width="200" height="230" fill="${c1}"/>
    ${pattern(p, c1, c2)}
    <path d="M4 48 L24 86 L44 76 L38 20Z M196 48 L176 86 L156 76 L162 20Z" fill="${c2}" opacity=".35"/>
    ${collar}
    ${print}
    <rect width="200" height="230" fill="url(#${id}s)"/>
  </g>
  <path d="${BODY}" fill="none" stroke="rgba(0,0,0,.25)" stroke-width="1.5"/>
</svg>`;
  };

  function escapeXML(s) {
    return String(s).replace(/[<>&"']/g, (ch) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&#39;" }[ch]));
  }
  window.escapeXML = escapeXML;
})();
