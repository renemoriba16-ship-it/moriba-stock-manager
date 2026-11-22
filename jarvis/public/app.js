// J.A.R.V.I.S. — interface : voix (reconnaissance + synthèse), streaming, HUD.
"use strict";

const $ = (s) => document.querySelector(s);
const store = {
  get(k, d) { try { const v = localStorage.getItem("jarvis." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("jarvis." + k, JSON.stringify(v)); } catch { /* stockage indisponible */ } },
};

const session = store.get("session", null) || (Date.now().toString(36) + Math.random().toString(36).slice(2));
store.set("session", session);

const els = {
  log: $("#log"), form: $("#form"), input: $("#input"), mic: $("#micBtn"), reactor: $("#reactor"),
  state: $("#stateLabel"), statusDot: $("#statusDot"), statusText: $("#statusText"),
  wake: $("#wakeToggle"), tts: $("#ttsToggle"),
};
els.tts.checked = store.get("tts", true);
els.wake.checked = false;

// ---------------- État visuel ----------------
const STATE_LABELS = { idle: "En veille", listening: "À l'écoute", thinking: "Analyse", speaking: "Réponse", wake: "Dites « Jarvis »" };
let uiState = "idle";
function setState(s) {
  uiState = s;
  els.reactor.className = "reactor " + (s === "wake" ? "idle" : s);
  els.state.textContent = STATE_LABELS[s] || s;
}

// ---------------- Thème ----------------
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  store.set("theme", t);
}
applyTheme(store.get("theme", "dark"));
$("#themeBtn").onclick = () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

// ---------------- Horloge ----------------
function tick() {
  const d = new Date();
  $("#clock").textContent = d.toLocaleTimeString("fr-FR");
  $("#date").textContent = d.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}
tick(); setInterval(tick, 1000);

// ---------------- Météo ----------------
let city = store.get("city", "Conakry");
async function loadWeather() {
  try {
    const w = await (await fetch("/api/weather?city=" + encodeURIComponent(city))).json();
    if (w.error) { $("#weather").textContent = /introuvable/.test(w.error) ? w.error : "Météo indisponible pour le moment"; return; }
    $("#weather").innerHTML = `
      <div>${esc(w.lieu)}</div>
      <div class="temp">${Math.round(w.actuel.temperature_c)}°C</div>
      <div>${esc(w.actuel.conditions)} · vent ${Math.round(w.actuel.vent_kmh)} km/h · ${w.actuel.humidite_pct}%</div>
      <div class="days">${w.previsions.map((p) => `<div>${new Date(p.date).toLocaleDateString("fr-FR", { weekday: "short" })}<br>${Math.round(p.min_c)}° / ${Math.round(p.max_c)}°<br><small>${p.pluie_pct ?? 0}% pluie</small></div>`).join("")}</div>`;
  } catch {
    $("#weather").textContent = "Météo indisponible";
  }
}
$("#cityBtn").onclick = () => {
  const c = prompt("Ville pour la météo :", city);
  if (c) { city = c; store.set("city", c); loadWeather(); }
};
loadWeather(); setInterval(loadWeather, 15 * 60 * 1000);

// ---------------- Tableau de bord ----------------
const fmt = (n) => Number(n).toLocaleString("fr-FR");
async function loadDashboard() {
  try {
    const d = await (await fetch("/api/dashboard")).json();
    $("#stProducts").textContent = fmt(d.stock.products);
    $("#stUnits").textContent = fmt(d.stock.units);
    $("#stValue").textContent = fmt(Math.round(d.stock.value));
    $("#lowStock").innerHTML = d.stock.low.length
      ? d.stock.low.map((p) => `<li>⚠ ${esc(p.name)} — ${p.quantity}</li>`).join("")
      : "";
    $("#todos").innerHTML = d.todos.length
      ? d.todos.map((t) => `<li class="prio-${t.priority}">${esc(t.text)}${t.due ? `<small>${new Date(t.due).toLocaleString("fr-FR")}</small>` : ""}</li>`).join("")
      : `<li class="muted">Rien à faire</li>`;
    $("#reminders").innerHTML = d.reminders.length
      ? d.reminders.map((r) => `<li>${esc(r.text)}<small>${new Date(r.at).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })}</small></li>`).join("")
      : `<li class="muted">Aucun rappel</li>`;
  } catch { /* serveur indisponible */ }
}
loadDashboard(); setInterval(loadDashboard, 60 * 1000);

// ---------------- Inventaire ----------------
let inventory = [];
function renderInventory() {
  const q = $("#invSearch").value.toLowerCase();
  const rows = inventory.filter((p) => [p.name, p.category, p.sku].join(" ").toLowerCase().includes(q));
  $("#invBody").innerHTML = rows.length
    ? rows.map((p) => `<tr class="${p.low ? "low" : ""}"><td>${esc(p.name)}</td><td>${esc(p.category)}</td><td>${esc(p.sku || "—")}</td><td>${fmt(p.quantity)} ${esc(p.unit)}</td><td>${fmt(p.price)}</td><td>${p.min_stock}</td></tr>`).join("")
    : `<tr><td colspan="6" class="muted">Aucun produit. Dites par exemple : « Ajoute 50 sacs de riz à 250 000 l'unité ».</td></tr>`;
}
$("#inventoryBtn").onclick = async () => {
  inventory = (await (await fetch("/api/stock")).json()).products;
  renderInventory();
  $("#inventory").showModal();
};
$("#invSearch").oninput = renderInventory;
$("#invClose").onclick = () => $("#inventory").close();

// ---------------- Journal ----------------
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function renderMd(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
}
function addMsg(kind, text = "") {
  const div = document.createElement("div");
  div.className = "msg " + kind;
  if (kind === "jarvis") div.innerHTML = `<div class="tools"></div><div class="body"></div>`;
  else div.textContent = text;
  els.log.appendChild(div);
  els.log.scrollTop = els.log.scrollHeight;
  return div;
}
function greet(online) {
  const h = new Date().getHours();
  const salut = h < 5 ? "Bonsoir" : h < 18 ? "Bonjour" : "Bonsoir";
  const m = addMsg("jarvis");
  m.querySelector(".body").textContent = online
    ? `${salut}. Tous les systèmes sont en ligne. Je gère votre stock, vos tâches, vos rappels, la météo, les calculs et la recherche web. Que puis-je faire pour vous ?`
    : `${salut}. Je fonctionne en mode hors-ligne : ajoutez une clé ANTHROPIC_API_KEY sur le serveur pour activer mon intelligence complète. Les commandes de base restent disponibles.`;
}

// ---------------- Synthèse vocale ----------------
const synth = window.speechSynthesis;
let voice = null;
function pickVoice() {
  const voices = synth ? synth.getVoices() : [];
  const fr = voices.filter((v) => v.lang && v.lang.toLowerCase().startsWith("fr"));
  voice = fr.find((v) => /google|microsoft|thomas|henri|paul|daniel/i.test(v.name)) || fr[0] || null;
}
if (synth) { pickVoice(); synth.onvoiceschanged = pickVoice; }

const speechQueue = [];
let speaking = false;
function cleanForSpeech(t) {
  return t.replace(/\*\*|__|`|#+\s/g, "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/https?:\/\/\S+/g, "le lien affiché").replace(/[•▪-]\s/g, "").trim();
}
function speak(text) {
  if (!els.tts.checked || !synth) return;
  const clean = cleanForSpeech(text);
  if (!clean) return;
  speechQueue.push(clean);
  if (!speaking) nextUtterance();
}
function nextUtterance() {
  const text = speechQueue.shift();
  if (!text) {
    speaking = false;
    if (uiState === "speaking") setState(els.wake.checked ? "wake" : "idle");
    resumeWakeAfterSpeech();
    return;
  }
  speaking = true;
  pauseWakeForSpeech();
  setState("speaking");
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "fr-FR"; u.rate = 1.05; u.pitch = 0.9;
  if (voice) u.voice = voice;
  u.onend = u.onerror = nextUtterance;
  synth.speak(u);
}
function stopSpeaking() {
  speechQueue.length = 0;
  if (synth) synth.cancel();
  speaking = false;
}
els.tts.onchange = () => { store.set("tts", els.tts.checked); if (!els.tts.checked) stopSpeaking(); };

// ---------------- Chat (streaming SSE) ----------------
let busy = false;
async function ask(text) {
  text = text.trim();
  if (!text || busy) return;
  busy = true;
  stopSpeaking();
  $("#suggestions").style.display = "none";
  addMsg("user", text);
  const msg = addMsg("jarvis");
  const body = msg.querySelector(".body");
  const tools = msg.querySelector(".tools");
  body.classList.add("typing");
  setState("thinking");

  let full = "", spokenUpTo = 0;
  const flushSpeech = (final) => {
    // Parle phrase par phrase dès qu'une phrase est complète : latence minimale.
    const pending = full.slice(spokenUpTo);
    const re = final ? /[\s\S]+$/ : /^[\s\S]*?[.!?…:](\s|$)|^[\s\S]*?\n/;
    let m;
    let rest = pending;
    while ((m = rest.match(re)) && m[0].trim()) {
      speak(m[0]);
      spokenUpTo += m[0].length;
      rest = full.slice(spokenUpTo);
      if (final) break;
    }
  };

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, session }),
    });
    if (!res.ok || !res.body) throw new Error("HTTP " + res.status);
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const raw = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const ev = /^event: (.+)$/m.exec(raw)?.[1];
        const dataLine = /^data: (.*)$/m.exec(raw)?.[1];
        if (!ev || !dataLine) continue;
        const data = JSON.parse(dataLine);
        if (ev === "text") {
          full += data.delta;
          body.innerHTML = renderMd(full);
          flushSpeech(false);
        } else if (ev === "tool") {
          const chip = document.createElement("span");
          chip.className = "tool-chip";
          chip.textContent = TOOL_LABELS[data.name] || data.name;
          tools.appendChild(chip);
        } else if (ev === "browser_action") {
          browserAction(data);
        } else if (ev === "refresh") {
          loadDashboard();
        } else if (ev === "notice") {
          addMsg("notice", data.message);
        } else if (ev === "error") {
          addMsg("error", data.message);
          speak(data.message);
        }
        els.log.scrollTop = els.log.scrollHeight;
      }
    }
  } catch (err) {
    addMsg("error", "Connexion au serveur impossible : " + err.message);
  }
  body.classList.remove("typing");
  if (!full.trim()) msg.remove();
  flushSpeech(true);
  if (!speaking) setState(els.wake.checked ? "wake" : "idle");
  busy = false;
}

const TOOL_LABELS = {
  get_datetime: "horloge", get_weather: "météo", calculate: "calcul", convert_units: "conversion",
  convert_currency: "devises", wikipedia_summary: "wikipédia", system_status: "système", web_search: "recherche web",
  stock_list: "stock", stock_add_product: "nouveau produit", stock_move: "mouvement stock", stock_update_product: "maj produit",
  stock_delete_product: "suppression produit", stock_report: "rapport stock", notes: "notes", todos: "tâches",
  reminders: "rappels", memory: "mémoire", browser_action: "action",
};

els.form.onsubmit = (e) => {
  e.preventDefault();
  const t = els.input.value;
  els.input.value = "";
  ask(t);
};
$("#suggestions").onclick = (e) => { if (e.target.tagName === "BUTTON") ask(e.target.textContent); };
$("#resetBtn").onclick = async () => {
  await fetch("/api/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session }) });
  els.log.innerHTML = "";
  stopSpeaking();
  addMsg("notice", "Nouvelle conversation. La mémoire long terme est conservée.");
};

// ---------------- Actions navigateur ----------------
function browserAction({ action, value, label }) {
  const open = (url) => window.open(url, "_blank", "noopener");
  switch (action) {
    case "open_url": open(/^https?:\/\//.test(value) ? value : "https://" + value); break;
    case "youtube": open("https://www.youtube.com/results?search_query=" + encodeURIComponent(value)); break;
    case "google": open("https://www.google.com/search?q=" + encodeURIComponent(value)); break;
    case "maps": open("https://www.google.com/maps/search/" + encodeURIComponent(value)); break;
    case "timer": startTimer(Number(value), label); break;
    case "theme": applyTheme(value === "light" ? "light" : "dark"); break;
  }
}

// ---------------- Minuteurs ----------------
const timers = [];
function startTimer(seconds, label) {
  if (!(seconds > 0)) return;
  timers.push({ id: Math.random(), end: Date.now() + seconds * 1000, label: label || `Minuteur ${Math.round(seconds / 60) || 1} min` });
  renderTimers();
}
function renderTimers() {
  const now = Date.now();
  for (const t of [...timers]) {
    if (t.end <= now) {
      timers.splice(timers.indexOf(t), 1);
      alertUser(`${t.label} terminé.`);
    }
  }
  $("#timers").innerHTML = timers.length
    ? timers.map((t) => {
        const s = Math.max(0, Math.round((t.end - now) / 1000));
        return `<li>${esc(t.label)}<small>${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}</small></li>`;
      }).join("")
    : `<li class="muted">Aucun minuteur</li>`;
}
setInterval(renderTimers, 1000);

// ---------------- Rappels & alertes ----------------
function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [880, 1320].forEach((f, i) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = f; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0.15, ctx.currentTime + i * 0.18);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.18 + 0.16);
      o.start(ctx.currentTime + i * 0.18); o.stop(ctx.currentTime + i * 0.18 + 0.17);
    });
  } catch { /* audio indisponible */ }
}
function alertUser(text) {
  beep();
  addMsg("notice", "🔔 " + text);
  speak(text);
  if ("Notification" in window && Notification.permission === "granted") new Notification("J.A.R.V.I.S.", { body: text });
}
async function pollReminders() {
  try {
    const due = await (await fetch("/api/reminders/due")).json();
    for (const r of due) alertUser("Rappel : " + r.text);
    if (due.length) loadDashboard();
  } catch { /* hors ligne */ }
}
setInterval(pollReminders, 15000);
document.addEventListener("click", () => {
  if ("Notification" in window && Notification.permission === "default") Notification.requestPermission();
}, { once: true });

// ---------------- Reconnaissance vocale ----------------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null, recMode = null; // "command" | "wake"
let wakePausedForSpeech = false;

function makeRecognizer(mode) {
  const r = new SR();
  r.lang = "fr-FR";
  r.interimResults = true;
  r.continuous = mode === "wake";
  r.maxAlternatives = 1;
  return r;
}

function listenCommand() {
  if (!SR) { addMsg("error", "La reconnaissance vocale n'est pas prise en charge par ce navigateur (utilisez Chrome ou Edge)."); return; }
  stopRecognition();
  stopSpeaking();
  recMode = "command";
  rec = makeRecognizer("command");
  let finalText = "";
  rec.onstart = () => { setState("listening"); els.mic.classList.add("active"); startMicViz(); };
  rec.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
      else interim += e.results[i][0].transcript;
    }
    els.input.value = finalText + interim;
  };
  rec.onerror = (e) => { if (e.error !== "no-speech" && e.error !== "aborted") addMsg("error", "Micro : " + e.error); };
  rec.onend = () => {
    els.mic.classList.remove("active");
    stopMicViz();
    rec = null; recMode = null;
    els.input.value = "";
    if (finalText.trim()) ask(finalText);
    else setState(els.wake.checked ? "wake" : "idle");
    if (els.wake.checked) setTimeout(startWake, 400);
  };
  rec.start();
}

function startWake() {
  if (!SR || !els.wake.checked || rec || speaking || busy) return;
  recMode = "wake";
  rec = makeRecognizer("wake");
  rec.onstart = () => { if (!busy && !speaking) setState("wake"); };
  rec.onresult = (e) => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (!e.results[i].isFinal) continue;
      const said = e.results[i][0].transcript.trim();
      const m = said.match(/\b(jarvis|jarvi|jarvice|djarvis)\b[\s,.!?]*(.*)$/i);
      if (!m) continue;
      const command = m[2].trim();
      stopRecognition();
      if (command.length > 2) ask(command);
      else { beep(); listenCommand(); }
      return;
    }
  };
  rec.onerror = (e) => {
    if (e.error === "not-allowed") { els.wake.checked = false; addMsg("error", "Accès au micro refusé."); }
  };
  rec.onend = () => {
    rec = null; recMode = null;
    if (els.wake.checked && !wakePausedForSpeech) setTimeout(startWake, 300);
  };
  try { rec.start(); } catch { rec = null; }
}

function stopRecognition() {
  if (rec) { const r = rec; rec = null; recMode = null; r.onend = null; try { r.abort(); } catch { /* déjà arrêté */ } }
  els.mic.classList.remove("active");
  stopMicViz();
}
function pauseWakeForSpeech() {
  // Évite que Jarvis s'entende lui-même parler.
  if (recMode === "wake") { wakePausedForSpeech = true; stopRecognition(); }
}
function resumeWakeAfterSpeech() {
  wakePausedForSpeech = false;
  if (els.wake.checked) setTimeout(startWake, 300);
}

els.wake.onchange = () => {
  if (els.wake.checked) { if (!SR) { els.wake.checked = false; addMsg("error", "Reconnaissance vocale indisponible dans ce navigateur."); return; } startWake(); }
  else { stopRecognition(); setState("idle"); }
};
const toggleListen = () => (recMode === "command" ? stopRecognition() || setState("idle") : listenCommand());
els.mic.onclick = toggleListen;
els.reactor.onclick = toggleListen;
// Espace maintenu (hors champ texte) = push-to-talk
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat && document.activeElement !== els.input && !$("#inventory").open) { e.preventDefault(); if (recMode !== "command") listenCommand(); }
  if (e.key === "Escape") { stopSpeaking(); stopRecognition(); setState("idle"); }
});
document.addEventListener("keyup", (e) => {
  if (e.code === "Space" && recMode === "command" && document.activeElement !== els.input) rec && rec.stop();
});

// ---------------- Visualiseur audio ----------------
const canvas = $("#viz"), ctx2d = canvas.getContext("2d");
let analyser = null, micStream = null, audioCtx = null;
async function startMicViz() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 128;
    audioCtx.createMediaStreamSource(micStream).connect(analyser);
  } catch { analyser = null; }
}
function stopMicViz() {
  if (micStream) micStream.getTracks().forEach((t) => t.stop());
  if (audioCtx) audioCtx.close().catch(() => {});
  micStream = audioCtx = analyser = null;
}
const bins = new Uint8Array(64);
function draw(t) {
  const W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;
  ctx2d.clearRect(0, 0, W, H);
  const color = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#00d8ff";
  const N = 64, R = 100;
  if (analyser) analyser.getByteFrequencyData(bins);
  ctx2d.strokeStyle = color;
  ctx2d.lineWidth = 2;
  ctx2d.shadowColor = color;
  ctx2d.shadowBlur = 8;
  for (let i = 0; i < N; i++) {
    let amp;
    if (analyser) amp = bins[i % bins.length] / 255;
    else if (uiState === "speaking") amp = 0.25 + 0.35 * Math.abs(Math.sin(t / 120 + i * 0.7)) * Math.abs(Math.sin(t / 300 + i));
    else if (uiState === "thinking") amp = 0.15 + 0.15 * Math.sin(t / 150 + i * 0.4);
    else amp = 0.04 + 0.03 * Math.sin(t / 700 + i * 0.5);
    const a = (i / N) * Math.PI * 2;
    const len = 6 + amp * 40;
    ctx2d.globalAlpha = 0.35 + amp * 0.65;
    ctx2d.beginPath();
    ctx2d.moveTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R);
    ctx2d.lineTo(cx + Math.cos(a) * (R + len), cy + Math.sin(a) * (R + len));
    ctx2d.stroke();
  }
  ctx2d.globalAlpha = 1;
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);

// ---------------- Démarrage ----------------
(async () => {
  try {
    const s = await (await fetch("/api/status")).json();
    els.statusDot.classList.toggle("on", s.online);
    els.statusText.textContent = s.online ? `En ligne · ${s.model}` : "Mode hors-ligne";
    greet(s.online);
  } catch {
    els.statusText.textContent = "Serveur injoignable";
  }
  setState("idle");
})();
