// Mode hors-ligne : quand aucune clé API Claude n'est configurée (ou en cas de panne),
// Jarvis comprend quand même les commandes courantes grâce à ces règles.
import { runTool } from "./tools.js";

const n = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
const num = (s) => Number(String(s).replace(",", "."));

async function call(name, input) {
  const r = await runTool(name, input);
  return JSON.parse(r.content.startsWith("{") ? r.content : JSON.stringify({ error: r.content }));
}

export async function offlineReply(text) {
  const t = n(text);
  const actions = [];
  let m;

  if (/^(bonjour|salut|hello|hey|coucou)/.test(t)) return { text: "Bonjour. Tous les systèmes sont opérationnels. Que puis-je faire pour vous ?", actions };

  if (/\b(quelle heure|l'heure|heure est)/.test(t)) {
    const r = await call("get_datetime", {});
    return { text: `Il est ${r.local.split(" ").slice(-1)[0]}.`, actions };
  }
  if (/\b(quel jour|date)\b/.test(t)) {
    const r = await call("get_datetime", {});
    return { text: `Nous sommes le ${r.local.split(" à ")[0]}.`, actions };
  }
  if ((m = t.match(/meteo(?: a| de| pour| sur)? ([a-z' -]+)/))) {
    const r = await call("get_weather", { city: m[1].trim() });
    if (r.error) return { text: r.error, actions };
    return { text: `À ${r.lieu} : ${r.actuel.conditions}, ${r.actuel.temperature_c} °C (ressenti ${r.actuel.ressenti_c} °C), vent ${r.actuel.vent_kmh} km/h.`, actions };
  }
  if ((m = t.match(/^(?:calcule|combien font|combien fait|calcul)\s+(.+)$/))) {
    const expr = m[1].replace(/\bfois\b/g, "*").replace(/\bplus\b/g, "+").replace(/\bmoins\b/g, "-").replace(/divise par/g, "/").replace(/\?/g, "");
    const r = await call("calculate", { expression: expr });
    return { text: r.error ? `Je n'arrive pas à calculer cela : ${r.error}` : `Le résultat est ${r.result}.`, actions };
  }
  if ((m = text.match(/^\s*(?:note|prends note|nouvelle note)\s*:?\s*(.+)$/i))) {
    await call("notes", { action: "add", text: m[1] });
    return { text: "Note enregistrée.", actions };
  }
  if ((m = text.match(/^\s*(?:ajoute(?:r)? (?:la )?tache|nouvelle tache|ajoute(?:r)? (?:la )?tâche|nouvelle tâche|todo)\s*:?\s*(.+)$/i))) {
    await call("todos", { action: "add", text: m[1] });
    return { text: `Tâche ajoutée : ${m[1]}.`, actions };
  }
  if (/\b(mes taches|liste des taches|todo list|mes todos)\b/.test(t)) {
    const r = await call("todos", { action: "list" });
    return { text: r.todos.length ? `Vous avez ${r.todos.length} tâche(s) : ${r.todos.map((x) => x.text).join(" ; ")}.` : "Aucune tâche en attente.", actions };
  }
  if ((m = t.match(/rappel(?:le)?(?:-| )?moi dans (\d+(?:[.,]\d+)?) ?(minutes?|min|heures?|h|secondes?|s)\b(?: de | d'| que | :)?\s*(.*)/))) {
    const unit = m[2][0];
    const minutes = num(m[1]) * (unit === "h" ? 60 : unit === "s" ? 1 / 60 : 1);
    const r = await call("reminders", { action: "add", text: m[3] || "Rappel", in_minutes: minutes });
    return { text: r.error ?? `Entendu, je vous le rappellerai à ${r.local.split(" ").slice(-1)[0]}.`, actions };
  }
  if ((m = t.match(/(?:minuteur|timer|chrono)(?: de)? (\d+(?:[.,]\d+)?) ?(minutes?|min|secondes?|s|heures?|h)/))) {
    const unit = m[2][0];
    const secs = num(m[1]) * (unit === "h" ? 3600 : unit === "m" ? 60 : 1);
    actions.push({ action: "timer", value: String(Math.round(secs)) });
    return { text: `Minuteur lancé pour ${m[1]} ${m[2]}.`, actions };
  }
  if ((m = t.match(/(?:mets|joue|lance|cherche sur youtube)\s+(.+?)(?: sur youtube)?$/)) && /youtube|musique|joue|mets/.test(t)) {
    actions.push({ action: "youtube", value: m[1].replace(/ sur youtube$/, "") });
    return { text: `J'ouvre YouTube pour « ${m[1]} ».`, actions };
  }
  if ((m = t.match(/^ouvre\s+(.+)$/))) {
    const site = m[1].replace(/\s+/g, "");
    actions.push({ action: "open_url", value: site.includes(".") ? site : `${site}.com` });
    return { text: `J'ouvre ${m[1]}.`, actions };
  }
  if ((m = t.match(/^(?:recherche|cherche|google)\s+(.+)$/))) {
    actions.push({ action: "google", value: m[1] });
    return { text: `Je lance la recherche « ${m[1]} ».`, actions };
  }
  // Stock : "ajoute 10 sacs de riz au stock", "vends 3 riz", "rapport de stock", "stock bas"
  if ((m = t.match(/(?:ajoute|recu|reception(?:ne)?|entree de)\s+(\d+(?:[.,]\d+)?)\s+(?:\w+ de |\w+ d')?(.+?)(?: au stock| en stock| dans le stock)$/))) {
    const r = await call("stock_move", { product: m[2], type: "in", quantity: num(m[1]), reason: "réception" });
    if (r.error && /introuvable/.test(r.error)) {
      const c = await call("stock_add_product", { name: m[2], quantity: num(m[1]) });
      return { text: c.error ?? `Nouveau produit « ${m[2]} » créé avec ${m[1]} unité(s).`, actions };
    }
    return { text: r.error ?? `${r.product} : stock porté à ${r.new_quantity}.`, actions };
  }
  if ((m = t.match(/(?:vends|vendu|sortie de|retire)\s+(\d+(?:[.,]\d+)?)\s+(?:\w+ de |\w+ d')?(.+?)(?: du stock)?$/))) {
    const r = await call("stock_move", { product: m[2], type: "out", quantity: num(m[1]), reason: "vente" });
    return { text: r.error ?? `${r.product} : il reste ${r.new_quantity}.${r.low_stock_alert ? " Attention, stock bas." : ""}`, actions };
  }
  if (/stock bas|rupture|alerte(s)? stock/.test(t)) {
    const r = await call("stock_list", { low_only: true });
    return { text: r.count ? `Produits en stock bas : ${r.products.map((p) => `${p.name} (${p.quantity})`).join(", ")}.` : "Aucun produit en stock bas.", actions };
  }
  if (/rapport|bilan|etat du stock|inventaire|stock/.test(t)) {
    const r = await call("stock_report", {});
    return { text: `Inventaire : ${r.products} produit(s), ${r.total_units} unités, valeur ${r.stock_value_sale}. ${r.low_stock.length} alerte(s) de stock bas.`, actions };
  }
  if (/etat (du )?systeme|diagnostic|status/.test(t)) {
    const r = await call("system_status", {});
    return { text: `Système ${r.platform}, ${r.cpus} cœurs, mémoire utilisée ${r.memory_used_pct} %, en ligne depuis ${r.uptime_h} h.`, actions };
  }

  return {
    text:
      "Mode hors-ligne : je n'ai pas accès à mon intelligence complète (clé API Claude absente). " +
      "Je comprends : l'heure, la date, « météo à … », « calcule … », « note : … », « ajoute tâche … », « rappelle-moi dans 10 minutes de … », " +
      "« minuteur 5 minutes », « ouvre … », « joue … sur YouTube », « ajoute 10 riz au stock », « vends 2 riz », « rapport de stock ».",
    actions,
  };
}
