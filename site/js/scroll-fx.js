/* =========================================================
   ANIMATIONS AU DÉFILEMENT
   - ballons qui flottent en arrière-plan et tournent quand on défile
   - ballon qui roule au bout de la barre de progression
   - ballons qui roulent sur des lignes de terrain
   - titres qui glissent selon le défilement
   ========================================================= */
(function () {
  "use strict";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Dessin du ballon (un seul symbole réutilisé partout) ---------- */
  const pt = (r, deg) => [50 + r * Math.cos((deg * Math.PI) / 180), 50 + r * Math.sin((deg * Math.PI) / 180)];
  const poly = (cx, cy, r, rot) =>
    Array.from({ length: 5 }, (_, k) => {
      const a = ((rot + 72 * k) * Math.PI) / 180;
      return `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`;
    }).join(" ");
  let patches = `<polygon points="${poly(50, 50, 15, -90)}"/>`;
  let seams = "";
  for (let k = 0; k < 5; k++) {
    const dir = -90 + 72 * k;
    const [ox, oy] = pt(45, dir);
    patches += `<polygon points="${poly(ox, oy, 13, dir + 180)}"/>`;
    const [a1, b1] = pt(15, dir), [a2, b2] = pt(33, dir);
    seams += `<line x1="${a1}" y1="${b1}" x2="${a2}" y2="${b2}"/>`;
    const [c1, d1] = pt(36, dir + 36), [c2, d2] = pt(52, dir + 36);
    seams += `<line x1="${c1}" y1="${d1}" x2="${c2}" y2="${d2}"/>`;
  }
  const sprite = document.createElement("div");
  sprite.setAttribute("aria-hidden", "true");
  sprite.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
  sprite.innerHTML = `
  <svg xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="ballShade" cx="36%" cy="30%" r="75%">
        <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#ececf1"/><stop offset="1" stop-color="#8d8d99"/>
      </radialGradient>
      <radialGradient id="ballLight" cx="36%" cy="30%" r="70%">
        <stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".35"/>
      </radialGradient>
      <clipPath id="ballClip"><circle cx="50" cy="50" r="48"/></clipPath>
    </defs>
    <symbol id="ball" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="48" fill="url(#ballShade)"/>
      <g clip-path="url(#ballClip)">
        <g fill="#141418">${patches}</g>
        <g stroke="#141418" stroke-width="1.6" stroke-linecap="round">${seams}</g>
        <circle cx="50" cy="50" r="48" fill="url(#ballLight)"/>
      </g>
      <circle cx="50" cy="50" r="48" fill="none" stroke="rgba(0,0,0,.35)" stroke-width="1"/>
    </symbol>
  </svg>`;
  document.body.prepend(sprite);
  const ball = (cls = "") => `<svg class="ball ${cls}" viewBox="0 0 100 100"><use href="#ball"/></svg>`;
  window.ballSVG = ball;

  /* ---------- Couche de ballons flottants ---------- */
  const layer = document.createElement("div");
  layer.className = "ball-layer";
  layer.setAttribute("aria-hidden", "true");
  document.body.prepend(layer);

  const small = innerWidth < 700;
  // x en % de la largeur, y en % de la hauteur d'écran, taille en px, vitesse de parallaxe, rotation
  const defs = [
    { x: 6,  y: 30,  s: 46, v: 0.35, spin: 0.5,  blur: 0 },
    { x: 88, y: 55,  s: 70, v: 0.6,  spin: -0.35, blur: 0 },
    { x: 18, y: 95,  s: 28, v: 0.2,  spin: 0.9,  blur: 1.5 },
    { x: 74, y: 120, s: 38, v: 0.45, spin: -0.7, blur: 0 },
    { x: 45, y: 160, s: 110, v: 0.85, spin: 0.25, blur: 3 },
    { x: 94, y: 190, s: 24, v: 0.25, spin: 1,    blur: 1.5 },
    { x: 30, y: 220, s: 56, v: 0.55, spin: -0.45, blur: 0 },
  ].slice(0, small ? 4 : 7);

  const balls = defs.map((d, i) => {
    const el = document.createElement("div");
    el.className = "float-ball";
    const size = small ? Math.round(d.s * 0.7) : d.s;
    el.style.width = el.style.height = size + "px";
    el.style.left = d.x + "%";
    if (d.blur) el.style.filter = `blur(${d.blur}px)`;
    el.style.opacity = d.blur ? 0.35 : 0.9;
    el.innerHTML = `<div class="float-ball-bob" style="animation-delay:${-i * 1.3}s">${ball()}</div>`;
    layer.appendChild(el);
    return { ...d, el, size, angle: 0, inner: el.querySelector(".ball") };
  });

  /* ---------- Ballon au bout de la barre de progression ---------- */
  const pBall = document.createElement("div");
  pBall.className = "progress-ball";
  pBall.setAttribute("aria-hidden", "true");
  pBall.innerHTML = ball();
  document.body.appendChild(pBall);

  /* ---------- Lignes de terrain avec ballon qui roule ---------- */
  const tracks = [...document.querySelectorAll(".roll-track")].map((t) => {
    t.innerHTML = `<span class="roll-line"></span><span class="roll-ball">${ball()}</span>`;
    return { el: t, b: t.querySelector(".roll-ball") };
  });

  /* ---------- Bannière en parallaxe ---------- */
  const banners = [...document.querySelectorAll(".banner")].map((b) => ({ el: b, img: b.querySelector(".banner-img") }));

  /* ---------- Titres qui glissent ---------- */
  const heads = [...document.querySelectorAll(".section-head h2")];

  /* ---------- Boucle d'animation (seulement quand on défile) ---------- */
  let lastY = scrollY, ticking = false, velocity = 0;

  function frame() {
    const y = scrollY, H = innerHeight, W = innerWidth;
    const dy = y - lastY;
    lastY = y;
    velocity = velocity * 0.85 + dy * 0.15;

    // Ballons flottants : parallaxe + rotation liée à la distance parcourue + léger balancement
    balls.forEach((b) => {
      const span = H + b.size * 2;
      let top = ((b.y / 100) * H - y * b.v) % span;
      if (top < -b.size) top += span;
      const sway = Math.sin(y / 260 + b.x) * 22;
      b.angle += dy * b.spin;
      const stretch = 1 + Math.min(Math.abs(velocity) / 400, 0.12);
      b.el.style.transform = `translate3d(${sway}px, ${top - b.size}px, 0)`;
      b.inner.style.transform = `rotate(${b.angle}deg) scale(${1 / stretch}, ${stretch})`;
    });

    // Ballon de la barre de progression : roule sans glisser (angle = distance / rayon)
    const max = document.documentElement.scrollHeight - H;
    const p = max > 0 ? y / max : 0;
    const px = p * (W - 16);
    pBall.style.transform = `translate3d(${px}px, 0, 0) rotate(${(px / 8) * (180 / Math.PI)}deg)`;

    // Ballons qui roulent sur les lignes
    tracks.forEach((t) => {
      const r = t.el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > H + 100) return;
      const k = Math.min(1, Math.max(0, (H - r.top) / (H + r.height)));
      const size = t.b.offsetWidth;
      const x = k * (r.width - size);
      t.b.style.transform = `translate3d(${x}px, 0, 0) rotate(${(x / (size / 2)) * (180 / Math.PI)}deg)`;
    });

    // Bannière : l'image défile plus lentement que la page et zoome légèrement
    banners.forEach((b) => {
      const r = b.el.getBoundingClientRect();
      if (r.bottom < 0 || r.top > H) return;
      const k = (r.top + r.height / 2 - H / 2) / H;
      b.img.style.transform = `translate3d(0, ${k * -60}px, 0) scale(${1.05 + Math.abs(k) * 0.08})`;
    });

    // Titres : glissent depuis la gauche puis se figent
    heads.forEach((h, i) => {
      const r = h.getBoundingClientRect();
      if (r.bottom < 0 || r.top > H) return;
      const k = Math.min(1, Math.max(0, (H - r.top) / (H * 0.6)));
      const dir = i % 2 ? 1 : -1;
      h.style.transform = `translate3d(${(1 - k) * 80 * dir}px, 0, 0)`;
    });

    ticking = false;
    if (Math.abs(velocity) > 0.5) requestTick(); // laisse retomber la vitesse en douceur
  }
  function requestTick() {
    if (!ticking) { ticking = true; requestAnimationFrame(frame); }
  }

  if (reduce) {
    layer.remove();
    pBall.remove();
    return;
  }
  addEventListener("scroll", requestTick, { passive: true });
  addEventListener("resize", requestTick);
  frame();
})();
