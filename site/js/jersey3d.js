/* =========================================================
   MAILLOT 3D DE L'ACCUEIL
   - modèle : site/models/maillot.glb (blender/maillot.py)
   - textures : photos de tes maillots (blender/textures.py) -> site/models/tex/
   - le maillot flotte, suit la souris, se tourne au doigt, montre le dos
     au défilement et passe d'un maillot du catalogue à l'autre
   - si la 3D n'est pas possible, le carrousel photo reste affiché
   ========================================================= */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const host = document.querySelector(".hero-visual");
const JERSEYS = (window.PRODUCTS || []).filter((p) => p.tex3d && p.status !== "bientot");

function webglOK() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch (_) { return false; }
}

function shadowTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 256;
  const g = c.getContext("2d");
  const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grd.addColorStop(0, "rgba(0,0,0,.6)"); grd.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = grd; g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}

async function start() {
  if (!host || !JERSEYS.length || !webglOK()) return;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping; // couleurs fidèles aux photos
  renderer.toneMappingExposure = 1.0;
  const canvas = renderer.domElement;
  canvas.className = "jersey-3d";
  canvas.setAttribute("role", "img");

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 50);
  camera.position.set(0, 0.05, 6.4);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x30303a, 1.6));
  const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(2.5, 3, 5); scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(-4, 1, 3); scene.add(fill);
  const rimA = new THREE.DirectionalLight(0xc6ff00, 1.4); rimA.position.set(-5, 2, -4); scene.add(rimA);
  const rimB = new THREE.DirectionalLight(0x6a5bff, 1.6); rimB.position.set(5, -1, -4); scene.add(rimB);

  /* ---------- textures (chargées au fur et à mesure) ---------- */
  const loader = new THREE.TextureLoader();
  const cache = new Map();
  const maxAniso = renderer.capabilities.getMaxAnisotropy();
  function getTexture(p) {
    if (!cache.has(p.id)) {
      cache.set(p.id, loader.loadAsync(p.tex3d).then((t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.flipY = false; // UV glTF
        t.anisotropy = maxAniso;
        return t;
      }));
    }
    return cache.get(p.id);
  }

  let index = 0;
  const [gltf, firstTex] = await Promise.all([new GLTFLoader().loadAsync("models/maillot.glb"), getTexture(JERSEYS[0])]);
  let mesh = null;
  gltf.scene.traverse((o) => { if (o.isMesh && !mesh) mesh = o; });
  if (!mesh) return;
  mesh.geometry.computeVertexNormals();
  const material = new THREE.MeshPhysicalMaterial({
    map: firstTex, roughness: 0.72, metalness: 0, sheen: 0.35, sheenRoughness: 0.6, sheenColor: new THREE.Color(0xffffff), side: THREE.DoubleSide,
  });
  mesh.material = material;
  if (JERSEYS[1]) getTexture(JERSEYS[1]);

  const pivot = new THREE.Group();
  pivot.add(gltf.scene);
  scene.add(pivot);

  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(2.0, 0.6), new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -1.3;
  scene.add(shadow);

  host.appendChild(canvas);
  document.documentElement.classList.add("three-ready");

  /* ---------- nom du maillot + bouton ---------- */
  const labelName = host.querySelector(".jersey-label-name");
  const labelBtn = host.querySelector(".jersey-label-btn");
  function showLabel() {
    const p = JERSEYS[index];
    canvas.setAttribute("aria-label", `${p.name} en 3D`);
    if (!labelName) return;
    labelName.classList.add("swap");
    setTimeout(() => { labelName.textContent = p.name; labelName.classList.remove("swap"); }, 250);
  }
  showLabel();
  if (labelBtn) labelBtn.addEventListener("click", () => window.openProduct && window.openProduct(JERSEYS[index].id));

  function resize() {
    const r = host.getBoundingClientRect();
    const w = Math.max(1, r.width), h = Math.max(1, r.height);
    renderer.setSize(w, h, false);
    canvas.style.width = w + "px"; canvas.style.height = h + "px";
    camera.aspect = w / h;
    camera.position.z = w / h < 0.9 ? 7.2 : 6.4;
    camera.updateProjectionMatrix();
  }
  resize();
  addEventListener("resize", resize);

  /* ---------- interactions ---------- */
  let mouseX = 0, mouseY = 0, tiltX = 0, tiltY = 0;
  addEventListener("pointermove", (e) => {
    mouseX = e.clientX / innerWidth - 0.5;
    mouseY = e.clientY / innerHeight - 0.5;
  }, { passive: true });

  let dragging = false, lastX = 0, dragVel = 0, dragRot = 0, lastInteract = 0;
  canvas.style.touchAction = "pan-y";
  const hint = host.querySelector(".drag-hint");
  canvas.addEventListener("pointerdown", (e) => {
    dragging = true; lastX = e.clientX; lastInteract = performance.now();
    canvas.setPointerCapture(e.pointerId);
    if (hint) hint.classList.add("gone");
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX; lastX = e.clientX;
    dragRot += dx * 0.012; dragVel = dx * 0.012; lastInteract = performance.now();
  });
  const endDrag = () => { dragging = false; };
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);

  /* ---------- passage au maillot suivant (vrille) ---------- */
  let spin = null;
  function next(step = 1) {
    if (spin || JERSEYS.length < 2) return;
    const target = (index + step + JERSEYS.length) % JERSEYS.length;
    spin = { t0: performance.now(), dur: 1200, swapped: false, target, tex: null };
    const s = spin;
    getTexture(JERSEYS[target]).then((t) => { s.tex = t; });
    getTexture(JERSEYS[(target + 1) % JERSEYS.length]); // précharge le suivant
  }
  canvas.addEventListener("dblclick", () => next(1));
  let visible = true;
  const timer = setInterval(() => {
    if (visible && !dragging && performance.now() - lastInteract > 4000) next(1);
  }, 4500);

  /* ---------- boucle ---------- */
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); }, { threshold: 0 }).observe(host);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) loop(); });

  const clock = new THREE.Clock();
  let running = false;
  function loop() {
    if (running) return;
    running = true;
    requestAnimationFrame(tick);
  }
  function tick() {
    if (!visible || document.hidden) { running = false; return; }
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    if (!dragging) { dragRot += dragVel; dragVel *= 0.94; dragRot *= 0.985; } // revient doucement de face
    const sway = reduce ? 0 : Math.sin(t * 0.45) * 0.55;

    // défilement : le maillot se retourne et montre le dos
    const hr = host.getBoundingClientRect();
    const startAt = Math.max(0, hr.top + scrollY - innerHeight * 0.2);
    const p = Math.min(1, Math.max(0, (scrollY - startAt) / (hr.height * 0.4)));

    let spinRot = 0, spinScale = 1;
    if (spin) {
      let k = Math.min(1, (performance.now() - spin.t0) / spin.dur);
      if (k >= 0.45 && !spin.swapped && !spin.tex) { spin.t0 += dt * 1000; k = 0.45; } // attend la texture
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      spinRot = e * Math.PI * 2;
      spinScale = 1 - Math.sin(k * Math.PI) * 0.1;
      if (!spin.swapped && k >= 0.45 && spin.tex) {
        spin.swapped = true;
        material.map = spin.tex; material.needsUpdate = true;
        index = spin.target;
        showLabel();
      }
      if (k >= 1) spin = null;
    }

    tiltX += (mouseY * 0.3 - tiltX) * 0.06;
    tiltY += (mouseX * 0.5 - tiltY) * 0.06;

    pivot.rotation.y = sway + p * Math.PI + dragRot + spinRot + tiltY;
    pivot.rotation.x = tiltX + Math.sin(t * 0.8) * 0.035;
    pivot.rotation.z = Math.sin(t * 0.6) * 0.03;
    const bob = reduce ? 0 : Math.sin(t * 1.2) * 0.07;
    pivot.position.y = bob;
    pivot.scale.setScalar(spinScale);
    shadow.scale.setScalar(1 - bob * 1.5);

    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  loop();
  addEventListener("pagehide", () => clearInterval(timer));
}

start().catch((err) => console.warn("3D indisponible :", err));
