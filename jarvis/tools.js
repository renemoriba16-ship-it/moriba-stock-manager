// Outils locaux que Jarvis peut appeler (via Claude) : stock, notes, tâches,
// rappels, mémoire, météo, calcul, conversions, devises, Wikipédia, heure.
import os from "node:os";
import { load, update, newId } from "./store.js";
import { evaluate } from "./calc.js";

const TZ = process.env.JARVIS_TIMEZONE || Intl.DateTimeFormat().resolvedOptions().timeZone;
const LOW_STOCK_DEFAULT = 5;

// ---------- utilitaires ----------
const norm = (s) =>
  String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

function findProduct(data, query) {
  const q = norm(query);
  return (
    data.products.find((p) => p.id === query || norm(p.sku) === q) ||
    data.products.find((p) => norm(p.name) === q) ||
    data.products.find((p) => norm(p.name).includes(q))
  );
}

async function fetchJson(url) {
  const res = await fetch(url, { headers: { "User-Agent": "jarvis-assistant/1.0" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} sur ${new URL(url).host}`);
  return res.json();
}

const WEATHER_CODES = {
  0: "ciel dégagé", 1: "plutôt dégagé", 2: "partiellement nuageux", 3: "couvert",
  45: "brouillard", 48: "brouillard givrant", 51: "bruine légère", 53: "bruine", 55: "bruine dense",
  61: "pluie faible", 63: "pluie", 65: "forte pluie", 71: "neige faible", 73: "neige", 75: "forte neige",
  80: "averses", 81: "averses", 82: "violentes averses", 95: "orage", 96: "orage avec grêle", 99: "orage violent",
};

const UNITS = {
  // longueur (m)
  mm: ["len", 0.001], cm: ["len", 0.01], m: ["len", 1], km: ["len", 1000],
  in: ["len", 0.0254], ft: ["len", 0.3048], yd: ["len", 0.9144], mi: ["len", 1609.344],
  // masse (kg)
  mg: ["mass", 1e-6], g: ["mass", 0.001], kg: ["mass", 1], t: ["mass", 1000],
  oz: ["mass", 0.0283495], lb: ["mass", 0.453592],
  // volume (L)
  ml: ["vol", 0.001], cl: ["vol", 0.01], l: ["vol", 1], gal: ["vol", 3.78541],
  // vitesse (m/s)
  "m/s": ["speed", 1], "km/h": ["speed", 1 / 3.6], mph: ["speed", 0.44704], kn: ["speed", 0.514444],
  // données (octets)
  b: ["data", 1], kb: ["data", 1e3], mb: ["data", 1e6], gb: ["data", 1e9], tb: ["data", 1e12],
  // temps (s)
  s: ["time", 1], min: ["time", 60], h: ["time", 3600], j: ["time", 86400], day: ["time", 86400],
};

function convertTemp(v, from, to) {
  const toC = { c: (x) => x, f: (x) => (x - 32) * (5 / 9), k: (x) => x - 273.15 };
  const fromC = { c: (x) => x, f: (x) => x * (9 / 5) + 32, k: (x) => x + 273.15 };
  return fromC[to](toC[from](v));
}

// ---------- définitions des outils ----------
const S = (properties, required = []) => ({ type: "object", properties, required });
const str = (description) => ({ type: "string", description });
const num = (description) => ({ type: "number", description });

export const TOOL_DEFS = [
  {
    name: "get_datetime",
    description: "Donne la date et l'heure actuelles (fuseau de l'utilisateur ou un fuseau IANA précisé).",
    input_schema: S({ timezone: str("Fuseau IANA optionnel, ex. Europe/Paris, Africa/Conakry") }),
  },
  {
    name: "get_weather",
    description: "Météo actuelle et prévisions sur 3 jours pour une ville.",
    input_schema: S({ city: str("Nom de la ville, ex. Conakry, Paris") }, ["city"]),
  },
  {
    name: "calculate",
    description: "Calcule une expression mathématique exacte (+ - * / % ^, sqrt, sin, log, ln, pi...). À utiliser pour tout calcul chiffré.",
    input_schema: S({ expression: str("Expression, ex. (12.5*4)^2 / sqrt(16)") }, ["expression"]),
  },
  {
    name: "convert_units",
    description: "Convertit une valeur entre unités (longueur, masse, volume, vitesse, données, temps, température c/f/k).",
    input_schema: S({ value: num("Valeur"), from: str("Unité source, ex. km, lb, c"), to: str("Unité cible") }, ["value", "from", "to"]),
  },
  {
    name: "convert_currency",
    description: "Convertit un montant entre devises avec le taux du jour (codes ISO : EUR, USD, GBP, XOF, GNF...).",
    input_schema: S({ amount: num("Montant"), from: str("Devise source"), to: str("Devise cible") }, ["amount", "from", "to"]),
  },
  {
    name: "wikipedia_summary",
    description: "Résumé encyclopédique d'un sujet depuis Wikipédia.",
    input_schema: S({ topic: str("Sujet"), lang: str("Langue Wikipédia, défaut fr") }, ["topic"]),
  },
  {
    name: "system_status",
    description: "État du serveur qui héberge Jarvis : CPU, mémoire, uptime, plateforme.",
    input_schema: S({}),
  },
  // --- Gestion de stock ---
  {
    name: "stock_list",
    description: "Liste les produits en stock, avec filtre texte optionnel et option 'seulement stock bas'.",
    input_schema: S({ search: str("Filtre sur le nom/catégorie/SKU"), low_only: { type: "boolean", description: "Uniquement les produits sous leur seuil d'alerte" } }),
  },
  {
    name: "stock_add_product",
    description: "Crée un nouveau produit dans l'inventaire.",
    input_schema: S({
      name: str("Nom du produit"),
      quantity: num("Quantité initiale"),
      price: num("Prix unitaire de vente"),
      cost: num("Coût d'achat unitaire (optionnel)"),
      category: str("Catégorie"),
      sku: str("Référence/SKU (optionnel)"),
      min_stock: num("Seuil d'alerte stock bas (défaut 5)"),
      unit: str("Unité, ex. pièce, kg, carton"),
    }, ["name", "quantity"]),
  },
  {
    name: "stock_move",
    description: "Enregistre une entrée (réception) ou une sortie (vente/perte) de stock pour un produit existant.",
    input_schema: S({
      product: str("Nom, SKU ou id du produit"),
      type: { type: "string", enum: ["in", "out"], description: "in = entrée, out = sortie" },
      quantity: num("Quantité (positive)"),
      reason: str("Motif : vente, réception fournisseur, casse..."),
    }, ["product", "type", "quantity"]),
  },
  {
    name: "stock_update_product",
    description: "Modifie les attributs d'un produit (prix, coût, seuil, catégorie, nom, SKU, unité).",
    input_schema: S({
      product: str("Nom, SKU ou id du produit"),
      name: str("Nouveau nom"), price: num("Nouveau prix"), cost: num("Nouveau coût"),
      min_stock: num("Nouveau seuil"), category: str("Nouvelle catégorie"), sku: str("Nouveau SKU"), unit: str("Nouvelle unité"),
    }, ["product"]),
  },
  {
    name: "stock_delete_product",
    description: "Supprime définitivement un produit. Ne l'utiliser que si l'utilisateur l'a demandé explicitement.",
    input_schema: S({ product: str("Nom, SKU ou id du produit") }, ["product"]),
  },
  {
    name: "stock_report",
    description: "Rapport global : valeur du stock, nombre d'articles, alertes stock bas, derniers mouvements, ventes récentes.",
    input_schema: S({ days: num("Période en jours pour les mouvements (défaut 7)") }),
  },
  // --- Productivité ---
  {
    name: "notes",
    description: "Gère les notes : ajouter, lister, chercher, supprimer.",
    input_schema: S({
      action: { type: "string", enum: ["add", "list", "search", "delete"] },
      text: str("Contenu (add) ou terme de recherche (search)"),
      id: str("Id de la note (delete)"),
    }, ["action"]),
  },
  {
    name: "todos",
    description: "Gère la liste de tâches : ajouter, lister, terminer, supprimer.",
    input_schema: S({
      action: { type: "string", enum: ["add", "list", "done", "delete"] },
      text: str("Intitulé (add)"),
      id: str("Id de la tâche (done/delete)"),
      priority: { type: "string", enum: ["basse", "normale", "haute"] },
      due: str("Échéance ISO 8601 optionnelle"),
    }, ["action"]),
  },
  {
    name: "reminders",
    description: "Programme, liste ou annule des rappels. Jarvis alertera l'utilisateur (voix + notification) à l'heure dite.",
    input_schema: S({
      action: { type: "string", enum: ["add", "list", "cancel"] },
      text: str("Message du rappel (add)"),
      in_minutes: num("Dans combien de minutes (add, alternatif à 'at')"),
      at: str("Date/heure ISO 8601 avec fuseau (add, alternatif à 'in_minutes')"),
      id: str("Id du rappel (cancel)"),
    }, ["action"]),
  },
  {
    name: "memory",
    description: "Mémoire à long terme sur l'utilisateur (préférences, informations utiles). Sauvegarder seulement ce que l'utilisateur veut qu'on retienne.",
    input_schema: S({
      action: { type: "string", enum: ["remember", "recall", "forget"] },
      fact: str("Fait à retenir (remember)"),
      id: str("Id du fait (forget)"),
    }, ["action"]),
  },
  // --- Actions côté navigateur ---
  {
    name: "browser_action",
    description: "Déclenche une action dans le navigateur de l'utilisateur : ouvrir un site, lancer une recherche YouTube/Google/Maps, démarrer un minuteur, changer de thème.",
    input_schema: S({
      action: { type: "string", enum: ["open_url", "youtube", "google", "maps", "timer", "theme"] },
      value: str("URL, requête, durée en secondes (timer) ou 'dark'/'light' (theme)"),
      label: str("Libellé du minuteur (optionnel)"),
    }, ["action", "value"]),
  },
];

// Validation légère des entrées (requis + types) avant exécution.
function validate(def, input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return "entrée invalide";
  for (const key of def.input_schema.required ?? []) {
    if (input[key] === undefined || input[key] === null || input[key] === "") return `champ requis manquant : ${key}`;
  }
  for (const [key, val] of Object.entries(input)) {
    const spec = def.input_schema.properties[key];
    if (!spec) continue;
    if (spec.type === "number" && typeof val !== "number") return `${key} doit être un nombre`;
    if (spec.type === "string" && typeof val !== "string") return `${key} doit être du texte`;
    if (spec.type === "boolean" && typeof val !== "boolean") return `${key} doit être un booléen`;
    if (spec.enum && !spec.enum.includes(val)) return `${key} doit valoir ${spec.enum.join("|")}`;
  }
  return null;
}

// ---------- implémentations ----------
const HANDLERS = {
  get_datetime({ timezone }) {
    const tz = timezone || TZ;
    const now = new Date();
    return {
      timezone: tz,
      iso: now.toISOString(),
      local: now.toLocaleString("fr-FR", { timeZone: tz, dateStyle: "full", timeStyle: "medium" }),
    };
  },

  async get_weather({ city }) {
    const geo = await fetchJson(
      `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=fr`,
    );
    const place = geo.results?.[0];
    if (!place) return { error: `Ville introuvable : ${city}` };
    const w = await fetchJson(
      `https://api.open-meteo.com/v1/forecast?latitude=${place.latitude}&longitude=${place.longitude}` +
        `&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code` +
        `&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&forecast_days=3&timezone=auto`,
    );
    return {
      lieu: `${place.name}${place.admin1 ? ", " + place.admin1 : ""}, ${place.country}`,
      actuel: {
        temperature_c: w.current.temperature_2m,
        ressenti_c: w.current.apparent_temperature,
        humidite_pct: w.current.relative_humidity_2m,
        vent_kmh: w.current.wind_speed_10m,
        conditions: WEATHER_CODES[w.current.weather_code] ?? `code ${w.current.weather_code}`,
      },
      previsions: w.daily.time.map((d, i) => ({
        date: d,
        min_c: w.daily.temperature_2m_min[i],
        max_c: w.daily.temperature_2m_max[i],
        pluie_pct: w.daily.precipitation_probability_max[i],
        conditions: WEATHER_CODES[w.daily.weather_code[i]] ?? "",
      })),
    };
  },

  calculate({ expression }) {
    return { expression, result: evaluate(expression) };
  },

  convert_units({ value, from, to }) {
    const f = norm(from).replace(/°/g, ""), t = norm(to).replace(/°/g, "");
    const temps = { c: "c", celsius: "c", f: "f", fahrenheit: "f", k: "k", kelvin: "k" };
    if (temps[f] && temps[t]) {
      return { value, from, to, result: Math.round(convertTemp(value, temps[f], temps[t]) * 1000) / 1000 };
    }
    const a = UNITS[f], b = UNITS[t];
    if (!a || !b) return { error: `Unité inconnue (${!a ? from : to}). Connues : ${Object.keys(UNITS).join(", ")}, c, f, k` };
    if (a[0] !== b[0]) return { error: `Unités incompatibles : ${from} → ${to}` };
    return { value, from, to, result: Math.round(((value * a[1]) / b[1]) * 1e6) / 1e6 };
  },

  async convert_currency({ amount, from, to }) {
    const src = from.toUpperCase(), dst = to.toUpperCase();
    const data = await fetchJson(`https://open.er-api.com/v6/latest/${encodeURIComponent(src)}`);
    if (data.result !== "success") return { error: `Devise inconnue : ${src}` };
    const rate = data.rates?.[dst];
    if (!rate) return { error: `Devise inconnue : ${dst}` };
    return { amount, from: src, to: dst, rate, result: Math.round(amount * rate * 100) / 100, date: data.time_last_update_utc };
  },

  async wikipedia_summary({ topic, lang = "fr" }) {
    const l = /^[a-z]{2,3}$/.test(lang) ? lang : "fr";
    const search = await fetchJson(
      `https://${l}.wikipedia.org/w/api.php?action=opensearch&format=json&limit=1&search=${encodeURIComponent(topic)}`,
    );
    const title = search?.[1]?.[0];
    if (!title) return { error: `Aucun article trouvé pour « ${topic} »` };
    const s = await fetchJson(`https://${l}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`);
    return { title: s.title, summary: s.extract, url: s.content_urls?.desktop?.page };
  },

  system_status() {
    const [l1, l5, l15] = os.loadavg();
    return {
      platform: `${os.type()} ${os.release()} (${os.arch()})`,
      cpus: os.cpus().length,
      load: { "1min": l1.toFixed(2), "5min": l5.toFixed(2), "15min": l15.toFixed(2) },
      memory_used_pct: Math.round((1 - os.freemem() / os.totalmem()) * 100),
      memory_total_gb: +(os.totalmem() / 1e9).toFixed(1),
      uptime_h: +(os.uptime() / 3600).toFixed(1),
      node: process.version,
    };
  },

  // --- Stock ---
  stock_list({ search, low_only }) {
    const data = load("stock");
    let items = data.products;
    if (search) {
      const q = norm(search);
      items = items.filter((p) => [p.name, p.category, p.sku].some((v) => norm(v).includes(q)));
    }
    if (low_only) items = items.filter((p) => p.quantity <= p.min_stock);
    return {
      count: items.length,
      products: items.map((p) => ({
        id: p.id, name: p.name, sku: p.sku, category: p.category, quantity: p.quantity, unit: p.unit,
        price: p.price, min_stock: p.min_stock, low: p.quantity <= p.min_stock,
      })),
    };
  },

  stock_add_product(input) {
    return update("stock", (data) => {
      if (findProduct(data, input.name) && norm(findProduct(data, input.name).name) === norm(input.name)) {
        return { error: `Le produit « ${input.name} » existe déjà. Utilise stock_move pour ajuster sa quantité.` };
      }
      if (input.quantity < 0) return { error: "La quantité initiale ne peut pas être négative." };
      const p = {
        id: newId(),
        name: input.name.trim(),
        sku: input.sku ?? "",
        category: input.category ?? "Général",
        quantity: input.quantity,
        unit: input.unit ?? "pièce",
        price: input.price ?? 0,
        cost: input.cost ?? 0,
        min_stock: input.min_stock ?? LOW_STOCK_DEFAULT,
        created_at: new Date().toISOString(),
      };
      data.products.push(p);
      data.movements.push({ id: newId(), product_id: p.id, product: p.name, type: "in", quantity: p.quantity, reason: "stock initial", at: p.created_at });
      return { ok: true, product: p };
    });
  },

  stock_move({ product, type, quantity, reason }) {
    if (!(quantity > 0)) return { error: "La quantité doit être strictement positive." };
    return update("stock", (data) => {
      const p = findProduct(data, product);
      if (!p) return { error: `Produit introuvable : ${product}` };
      if (type === "out" && quantity > p.quantity) {
        return { error: `Stock insuffisant pour ${p.name} : ${p.quantity} ${p.unit} disponible(s).` };
      }
      p.quantity += type === "in" ? quantity : -quantity;
      data.movements.push({ id: newId(), product_id: p.id, product: p.name, type, quantity, reason: reason ?? (type === "in" ? "entrée" : "sortie"), at: new Date().toISOString(), unit_price: p.price });
      return { ok: true, product: p.name, new_quantity: p.quantity, unit: p.unit, low_stock_alert: p.quantity <= p.min_stock };
    });
  },

  stock_update_product({ product, ...changes }) {
    return update("stock", (data) => {
      const p = findProduct(data, product);
      if (!p) return { error: `Produit introuvable : ${product}` };
      for (const k of ["name", "price", "cost", "min_stock", "category", "sku", "unit"]) {
        if (changes[k] !== undefined) p[k] = changes[k];
      }
      return { ok: true, product: p };
    });
  },

  stock_delete_product({ product }) {
    return update("stock", (data) => {
      const p = findProduct(data, product);
      if (!p) return { error: `Produit introuvable : ${product}` };
      data.products = data.products.filter((x) => x.id !== p.id);
      return { ok: true, deleted: p.name };
    });
  },

  stock_report({ days = 7 }) {
    const data = load("stock");
    const since = Date.now() - days * 86400000;
    const recent = data.movements.filter((m) => Date.parse(m.at) >= since);
    const sales = recent.filter((m) => m.type === "out");
    return {
      products: data.products.length,
      total_units: data.products.reduce((s, p) => s + p.quantity, 0),
      stock_value_sale: Math.round(data.products.reduce((s, p) => s + p.quantity * p.price, 0) * 100) / 100,
      stock_value_cost: Math.round(data.products.reduce((s, p) => s + p.quantity * (p.cost || 0), 0) * 100) / 100,
      low_stock: data.products.filter((p) => p.quantity <= p.min_stock).map((p) => ({ name: p.name, quantity: p.quantity, min: p.min_stock })),
      period_days: days,
      movements_in_period: recent.length,
      units_out_in_period: sales.reduce((s, m) => s + m.quantity, 0),
      revenue_estimate: Math.round(sales.reduce((s, m) => s + m.quantity * (m.unit_price || 0), 0) * 100) / 100,
      last_movements: data.movements.slice(-10).reverse(),
    };
  },

  // --- Productivité ---
  notes({ action, text, id }) {
    return update("notes", (data) => {
      if (action === "add") {
        if (!text) return { error: "Texte requis" };
        const n = { id: newId(), text, at: new Date().toISOString() };
        data.notes.push(n);
        return { ok: true, note: n };
      }
      if (action === "list") return { notes: data.notes.slice(-30) };
      if (action === "search") {
        const q = norm(text);
        return { notes: data.notes.filter((n) => norm(n.text).includes(q)) };
      }
      if (action === "delete") {
        const before = data.notes.length;
        data.notes = data.notes.filter((n) => n.id !== id);
        return before === data.notes.length ? { error: `Note introuvable : ${id}` } : { ok: true };
      }
    });
  },

  todos({ action, text, id, priority, due }) {
    return update("todos", (data) => {
      if (action === "add") {
        if (!text) return { error: "Intitulé requis" };
        const t = { id: newId(), text, priority: priority ?? "normale", due: due ?? null, done: false, at: new Date().toISOString() };
        data.todos.push(t);
        return { ok: true, todo: t };
      }
      if (action === "list") return { todos: data.todos.filter((t) => !t.done), done_count: data.todos.filter((t) => t.done).length };
      const t = data.todos.find((x) => x.id === id) || data.todos.find((x) => id && norm(x.text).includes(norm(id)));
      if (!t) return { error: `Tâche introuvable : ${id}` };
      if (action === "done") { t.done = true; t.done_at = new Date().toISOString(); return { ok: true, todo: t }; }
      if (action === "delete") { data.todos = data.todos.filter((x) => x.id !== t.id); return { ok: true }; }
    });
  },

  reminders({ action, text, in_minutes, at, id }) {
    return update("reminders", (data) => {
      if (action === "add") {
        if (!text) return { error: "Message requis" };
        let when;
        if (typeof in_minutes === "number") when = Date.now() + in_minutes * 60000;
        else if (at) when = Date.parse(at);
        if (!when || Number.isNaN(when)) return { error: "Préciser in_minutes ou une date 'at' ISO valide" };
        if (when < Date.now() - 60000) return { error: "Cette heure est déjà passée" };
        const r = { id: newId(), text, at: new Date(when).toISOString(), fired: false };
        data.reminders.push(r);
        return { ok: true, reminder: r, local: new Date(when).toLocaleString("fr-FR", { timeZone: TZ }) };
      }
      if (action === "list") return { reminders: data.reminders.filter((r) => !r.fired) };
      if (action === "cancel") {
        const before = data.reminders.length;
        data.reminders = data.reminders.filter((r) => r.id !== id);
        return before === data.reminders.length ? { error: `Rappel introuvable : ${id}` } : { ok: true };
      }
    });
  },

  memory({ action, fact, id }) {
    return update("memory", (data) => {
      if (action === "remember") {
        if (!fact) return { error: "Fait requis" };
        const f = { id: newId(), fact, at: new Date().toISOString() };
        data.facts.push(f);
        return { ok: true, fact: f };
      }
      if (action === "recall") return { facts: data.facts };
      if (action === "forget") {
        const before = data.facts.length;
        data.facts = data.facts.filter((f) => f.id !== id);
        return before === data.facts.length ? { error: `Fait introuvable : ${id}` } : { ok: true };
      }
    });
  },

  // Exécuté côté navigateur : le serveur renvoie juste l'ordre, le client l'applique.
  browser_action(input) {
    return { ok: true, dispatched_to_browser: input };
  },
};

export async function runTool(name, input) {
  const def = TOOL_DEFS.find((d) => d.name === name);
  if (!def) return { isError: true, content: `Outil inconnu : ${name}` };
  const problem = validate(def, input);
  if (problem) return { isError: true, content: JSON.stringify({ INVALID_INPUT: problem }) };
  try {
    const out = await HANDLERS[name](input);
    const isError = Boolean(out && out.error);
    return { isError, content: JSON.stringify(out) };
  } catch (err) {
    return { isError: true, content: `Erreur : ${err.message}` };
  }
}

// Rappels arrivés à échéance (consommés une seule fois).
export function popDueReminders() {
  return update("reminders", (data) => {
    const now = Date.now();
    const due = data.reminders.filter((r) => !r.fired && Date.parse(r.at) <= now);
    for (const r of due) r.fired = true;
    data.reminders = data.reminders.filter((r) => !r.fired || Date.parse(r.at) > now - 86400000);
    return due;
  });
}

export function dashboard() {
  const stock = load("stock");
  const todos = load("todos").todos.filter((t) => !t.done);
  const reminders = load("reminders").reminders.filter((r) => !r.fired).sort((a, b) => a.at.localeCompare(b.at));
  return {
    stock: {
      products: stock.products.length,
      units: stock.products.reduce((s, p) => s + p.quantity, 0),
      value: Math.round(stock.products.reduce((s, p) => s + p.quantity * p.price, 0) * 100) / 100,
      low: stock.products.filter((p) => p.quantity <= p.min_stock).map((p) => ({ name: p.name, quantity: p.quantity })),
    },
    todos: todos.slice(0, 8),
    reminders: reminders.slice(0, 5),
    notes: load("notes").notes.length,
  };
}

export { TZ };
