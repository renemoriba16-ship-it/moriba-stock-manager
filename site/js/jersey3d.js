/* =========================================================
   MAILLOT 3D (modèle Blender : site/models/maillot.glb)
   - texture dessinée en direct : couleurs, motifs, nom, numéro
   - tourne au défilement, suit la souris, change de couleurs
   - si la 3D n'est pas possible, le carrousel photo reste affiché
   ========================================================= */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const host = document.querySelector(".hero-visual");
const SHOP = window.SHOP || { name: "SENSEY'S JERSEYS", backName: "SENSEY" };

/* Coloris (décoratifs) : fond, couleur secondaire, texte, motif */
const COLORWAYS = [
  { base: "#1b2a8f", alt: "#2f45c9", ink: "#ffffff", trim: "#ffffff", pattern: "diagonal" },
  { base: "#f5d90a", alt: "#0b6b4a", ink: "#0b6b4a", trim: "#0b6b4a", pattern: "plain" },
  { base: "#a50044", alt: "#004d98", ink: "#f5c518", trim: "#0b1640", pattern: "stripes" },
  { base: "#111111", alt: "#c6ff00", ink: "#c6ff00", trim: "#c6ff00", pattern: "chevron" },
  { base: "#c8102e", alt: "#a50d26", ink: "#ffffff", trim: "#1e8f8f", pattern: "waves" },
  { base: "#f2f2f2", alt: "#1b2240", ink: "#1b2240", trim: "#c8102e", pattern: "sash" },
];

function webglOK() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch (_) { return false; }
}

/* ---------- Texture du maillot (gauche = face, droite = dos) ---------- */
function paintTexture(ctx, cw) {
  const W = 2048, H = 1024, HW = 1024;
  ctx.save();
  ctx.fillStyle = cw.base;
  ctx.fillRect(0, 0, W, H);

  // motif sur les deux moitiés
  ctx.fillStyle = cw.alt;
  ctx.strokeStyle = cw.alt;
  for (let side = 0; side < 2; side++) {
    const ox = side * HW;
    ctx.save();
    ctx.beginPath(); ctx.rect(ox, 0, HW, H); ctx.clip();
    switch (cw.pattern) {
      case "stripes":
        for (let x = 0; x < HW; x += 128) ctx.fillRect(ox + x + 64, 0, 64, H);
        break;
      case "diagonal":
        ctx.lineWidth = 14;
        for (let i = -H; i < HW + H; i += 44) { ctx.beginPath(); ctx.moveTo(ox + i, H); ctx.lineTo(ox + i + H * 0.7, 0); ctx.stroke(); }
        break;
      case "chevron":
        ctx.beginPath();
        ctx.moveTo(ox, 380); ctx.lineTo(ox + HW / 2, 560); ctx.lineTo(ox + HW, 380);
        ctx.lineTo(ox + HW, 470); ctx.lineTo(ox + HW / 2, 650); ctx.lineTo(ox, 470); ctx.closePath(); ctx.fill();
        break;
      case "waves":
        ctx.lineWidth = 6; ctx.globalAlpha = 0.7;
        for (let y = 140; y < H; y += 46) {
          ctx.beginPath();
          for (let x = 0; x <= HW; x += 16) ctx.lineTo(ox + x, y + Math.sin(x / 60) * 10);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
        break;
      case "sash":
        ctx.beginPath();
        ctx.moveTo(ox + (side ? HW * 0.75 : HW * 0.15), 0); ctx.lineTo(ox + (side ? HW * 0.95 : HW * 0.35), 0);
        ctx.lineTo(ox + (side ? HW * 0.25 : HW * 0.85), H); ctx.lineTo(ox + (side ? HW * 0.05 : HW * 0.65), H);
        ctx.closePath(); ctx.fill();
        break;
    }
    // col
    ctx.strokeStyle = cw.trim; ctx.lineWidth = 34;
    ctx.beginPath(); ctx.ellipse(ox + HW / 2, -6, 132, 118, 0, 0, Math.PI); ctx.stroke();
    // bouts de manches
    ctx.fillStyle = cw.trim;
    ctx.fillRect(ox, 0, 34, H); ctx.fillRect(ox + HW - 34, 0, 34, H);
    // bas
    ctx.fillRect(ox, H - 26, HW, 26);
    ctx.restore();
    ctx.fillStyle = cw.alt; ctx.strokeStyle = cw.alt;
  }

  ctx.fillStyle = cw.ink;
  ctx.strokeStyle = cw.ink;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const font = (px) => `${px}px Anton, Impact, "Arial Narrow", sans-serif`;

  // face : écusson (côté cœur), petit logo, nom de la boutique, numéro
  ctx.lineWidth = 9;
  ctx.beginPath(); ctx.arc(690, 330, 52, 0, Math.PI * 2); ctx.stroke();
  ctx.font = font(56); ctx.fillText("S", 690, 334);
  ctx.beginPath(); ctx.moveTo(300, 345); ctx.lineTo(330, 300); ctx.lineTo(360, 345); ctx.stroke();
  // nom de la boutique sur deux lignes si besoin (ex. « SENSEY'S » / « JERSEYS »)
  const words = SHOP.name.toUpperCase().split(/\s+/);
  if (words.length > 1) {
    ctx.font = font(118); ctx.fillText(words[0], HW / 2, 500, 430);
    ctx.font = font(64); ctx.fillText(words.slice(1).join(" "), HW / 2, 590, 430);
  } else {
    ctx.font = font(118); ctx.fillText(words[0], HW / 2, 520, 430);
  }
  ctx.font = font(64); ctx.fillText("10", HW / 2, 720);

  // dos : nom + grand numéro
  const back = (SHOP.backName || SHOP.name).toUpperCase();
  ctx.font = font(96); ctx.fillText(back, HW + HW / 2, 240, 560);
  ctx.font = font(400);
  ctx.lineWidth = 10; ctx.strokeStyle = cw.base;
  ctx.strokeText("10", HW + HW / 2, 560);
  ctx.fillText("10", HW + HW / 2, 560);
  ctx.restore();
}

/* ---------- Ombre douce sous le maillot ---------- */
function shadowTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 256;
  const g = c.getContext("2d");
  const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grd.addColorStop(0, "rgba(0,0,0,.55)"); grd.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = grd; g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}

async function start() {
  if (!host || !webglOK()) return;
  if (document.fonts && document.fonts.load) {
    try { await document.fonts.load('120px "Anton"'); } catch (_) {}
  }

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const canvas = renderer.domElement;
  canvas.className = "jersey-3d";
  canvas.setAttribute("aria-label", "Maillot en 3D");
  canvas.setAttribute("role", "img");

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  camera.position.set(0, 0.1, 6.4);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x1a1a2e, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(3, 4, 5); scene.add(key);
  const rimA = new THREE.DirectionalLight(0xc6ff00, 2.2); rimA.position.set(-5, 2, -3); scene.add(rimA);
  const rimB = new THREE.DirectionalLight(0x5b4bff, 2.6); rimB.position.set(5, -1, -4); scene.add(rimB);

  // texture
  const texCanvas = document.createElement("canvas");
  texCanvas.width = 2048; texCanvas.height = 1024;
  const tctx = texCanvas.getContext("2d");
  let cwIndex = 0;
  paintTexture(tctx, COLORWAYS[0]);
  const tex = new THREE.CanvasTexture(texCanvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = false; // UV glTF
  tex.anisotropy = renderer.capabilities.getMaxAnisotropy();

  const material = new THREE.MeshPhysicalMaterial({
    map: tex, roughness: 0.62, metalness: 0, sheen: 0.6, sheenRoughness: 0.5, sheenColor: new THREE.Color(0xffffff), side: THREE.DoubleSide,
  });

  const gltf = await new GLTFLoader().loadAsync("models/maillot.glb");
  let mesh = null;
  gltf.scene.traverse((o) => { if (o.isMesh && !mesh) mesh = o; });
  if (!mesh) return;
  mesh.material = material;
  mesh.geometry.computeVertexNormals();

  const pivot = new THREE.Group();
  pivot.add(gltf.scene);
  scene.add(pivot);

  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.7), new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -1.35;
  scene.add(shadow);

  host.appendChild(canvas);
  document.documentElement.classList.add("three-ready");

  function resize() {
    const r = host.getBoundingClientRect();
    const w = Math.max(1, r.width), h = Math.max(1, r.height);
    renderer.setSize(w, h, false);
    canvas.style.width = w + "px"; canvas.style.height = h + "px";
    camera.aspect = w / h;
    camera.position.z = w / h < 0.9 ? 7.4 : 6.4;
    camera.updateProjectionMatrix();
  }
  resize();
  addEventListener("resize", resize);

  /* ---------- Interactions ---------- */
  let mouseX = 0, mouseY = 0, tiltX = 0, tiltY = 0;
  addEventListener("pointermove", (e) => {
    mouseX = e.clientX / innerWidth - 0.5;
    mouseY = e.clientY / innerHeight - 0.5;
  }, { passive: true });

  // glisser pour faire tourner (souris ou doigt)
  let dragging = false, lastX = 0, dragVel = 0, dragRot = 0;
  canvas.style.touchAction = "pan-y";
  canvas.addEventListener("pointerdown", (e) => { dragging = true; lastX = e.clientX; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX; lastX = e.clientX;
    dragRot += dx * 0.012; dragVel = dx * 0.012;
  });
  const hint = host.querySelector(".drag-hint");
  canvas.addEventListener("pointerdown", () => hint && hint.classList.add("gone"), { once: true });
  const endDrag = () => { dragging = false; };
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);

  /* ---------- Changement de coloris avec une vrille ---------- */
  let spin = null; // { t0, dur, swapped }
  function nextColorway() {
    if (spin) return;
    spin = { t0: performance.now(), dur: 1100, swapped: false };
  }
  canvas.addEventListener("dblclick", nextColorway);
  const swapTimer = setInterval(() => { if (visible && !dragging) nextColorway(); }, 5000);

  /* ---------- Boucle ---------- */
  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); }, { threshold: 0 }).observe(host);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) loop(); });

  const clock = new THREE.Clock();
  let auto = 0, running = false;

  function loop() {
    if (running) return;
    running = true;
    requestAnimationFrame(tick);
  }
  function tick() {
    if (!visible || document.hidden) { running = false; return; }
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    // rotation : automatique + défilement + glisser (avec inertie)
    if (!dragging) { dragRot += dragVel; dragVel *= 0.94; }
    // balancement doux : on voit surtout la face (la vrille montre le dos à chaque changement)
    if (!reduce) auto = Math.sin(t * 0.45) * 0.75;
    // progression : 0 en haut de page, 1 quand le maillot a défilé de 40 % de sa hauteur
    const hr = host.getBoundingClientRect();
    const absTop = hr.top + scrollY;
    const startAt = Math.max(0, absTop - innerHeight * 0.2);
    const p = Math.min(1, Math.max(0, (scrollY - startAt) / (hr.height * 0.4)));
    const scrollRot = p * Math.PI;                                // montre le dos en descendant

    let spinRot = 0, spinScale = 1;
    if (spin) {
      const k = Math.min(1, (performance.now() - spin.t0) / spin.dur);
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      spinRot = e * Math.PI * 2;
      spinScale = 1 - Math.sin(k * Math.PI) * 0.12;
      if (!spin.swapped && k >= 0.45) {
        spin.swapped = true;
        cwIndex = (cwIndex + 1) % COLORWAYS.length;
        paintTexture(tctx, COLORWAYS[cwIndex]);
        tex.needsUpdate = true;
      }
      if (k >= 1) spin = null;
    }

    tiltX += (mouseY * 0.35 - tiltX) * 0.06;
    tiltY += (mouseX * 0.6 - tiltY) * 0.06;

    pivot.rotation.y = auto + scrollRot + dragRot + spinRot + tiltY;
    pivot.rotation.x = tiltX + Math.sin(t * 0.8) * 0.04;
    pivot.rotation.z = Math.sin(t * 0.6) * 0.04;
    const bob = reduce ? 0 : Math.sin(t * 1.2) * 0.08;
    pivot.position.y = bob;
    pivot.scale.setScalar(spinScale * (1 - p * 0.08));
    shadow.scale.setScalar(1 - bob * 1.5);

    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  loop();

  addEventListener("pagehide", () => clearInterval(swapTimer));
}

start().catch((err) => console.warn("3D indisponible :", err));
