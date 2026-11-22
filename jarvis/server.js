// J.A.R.V.I.S. — serveur : API de chat en streaming (SSE) propulsée par Claude,
// outils locaux (stock, notes, tâches, rappels...), et interface web.
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";
import { TOOL_DEFS, runTool, popDueReminders, dashboard, TZ } from "./tools.js";
import { offlineReply } from "./offline.js";
import { load } from "./store.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3000);
const MODEL = process.env.JARVIS_MODEL || "claude-opus-5-5";
const EFFORT = process.env.JARVIS_EFFORT || "low"; // low = réponses rapides, idéal à la voix
const USER_NAME = process.env.JARVIS_USER_NAME || "Monsieur";
const MAX_TOOL_ROUNDS = 12;

const hasCredentials = Boolean(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN);
const client = hasCredentials ? new Anthropic() : null;

// Outils envoyés à Claude : outils locaux + recherche web côté serveur Anthropic.
const TOOLS = [
  ...TOOL_DEFS.map((d) => ({ ...d, eager_input_streaming: true })),
  { type: "web_search_20260209", name: "web_search", max_uses: 5 },
];

const SYSTEM_PROMPT = `Tu es J.A.R.V.I.S., l'assistant personnel de ${USER_NAME}, inspiré du majordome IA élégant et un brin pince-sans-rire.
Tu parles français par défaut (ou la langue de l'utilisateur), tu vouvoies l'utilisateur et l'appelles "${USER_NAME}" de temps en temps, sans excès.

Tes réponses sont souvent lues à voix haute : sois concis (1 à 4 phrases pour une demande simple), naturel, sans tableaux ni listes longues sauf si on te demande un détail écrit. Pas de markdown lourd ; du gras ou une courte liste au besoin seulement.

Tes capacités, via tes outils :
- Gestion de stock complète (produits, entrées/sorties, alertes de stock bas, rapports, valeur du stock). C'est une fonction centrale : sois rigoureux sur les quantités, confirme chaque mouvement avec la nouvelle quantité et signale les stocks bas.
- Notes, liste de tâches, rappels programmés, mémoire à long terme sur l'utilisateur.
- Météo, date/heure, calculs exacts (utilise toujours l'outil calculate pour les chiffres), conversions d'unités et de devises, Wikipédia, recherche web pour l'actualité et tout ce qui est récent.
- Actions dans le navigateur : ouvrir un site, YouTube, Google, Maps, minuteur, thème.
- État du serveur.

Règles :
- Utilise les outils plutôt que d'inventer ; si une info manque (ex. quantité d'un mouvement de stock), demande-la brièvement.
- Ne supprime un produit, une note ou une tâche que sur demande explicite.
- Quand l'utilisateur partage une préférence durable ("retiens que..."), enregistre-la avec l'outil memory.
- Pour les rappels relatifs ("dans 10 minutes"), utilise in_minutes ; pour une heure précise, construis une date ISO avec le bon fuseau (${TZ}).
- Après une recherche web, résume l'essentiel en une ou deux phrases.`;

// Conversations en mémoire, une par identifiant de session navigateur.
const sessions = new Map();
const MAX_MESSAGES = 160;

function memoryBlock() {
  const facts = load("memory").facts;
  return facts.length
    ? `Ce que tu sais de l'utilisateur (mémoire long terme) :\n${facts.map((f) => `- [${f.id}] ${f.fact}`).join("\n")}`
    : "Mémoire long terme : vide pour l'instant.";
}

function contextLine() {
  const now = new Date().toLocaleString("fr-FR", { timeZone: TZ, dateStyle: "full", timeStyle: "short" });
  return `[Contexte : ${now}, fuseau ${TZ}]`;
}

const app = express();
app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(here, "public")));

app.get("/api/status", (_req, res) => {
  res.json({ online: hasCredentials, model: hasCredentials ? MODEL : null, user: USER_NAME, timezone: TZ });
});

app.get("/api/dashboard", (_req, res) => res.json(dashboard()));
app.get("/api/reminders/due", (_req, res) => res.json(popDueReminders()));
app.get("/api/stock", async (_req, res) => {
  const r = await runTool("stock_list", {});
  res.json(JSON.parse(r.content));
});

app.get("/api/weather", async (req, res) => {
  const r = await runTool("get_weather", { city: String(req.query.city || "Conakry").slice(0, 80) });
  res.json(JSON.parse(r.content.startsWith("{") ? r.content : JSON.stringify({ error: r.content })));
});

app.post("/api/reset", (req, res) => {
  sessions.delete(String(req.body?.session || ""));
  res.json({ ok: true });
});

app.post("/api/chat", async (req, res) => {
  const text = String(req.body?.text ?? "").trim().slice(0, 8000);
  const sessionId = String(req.body?.session ?? "default").slice(0, 64);
  if (!text) return res.status(400).json({ error: "Message vide" });

  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
  });
  const send = (event, data) => res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  let closed = false;
  res.on("close", () => { closed = true; });

  // Pas de clé : mode hors-ligne à base de règles.
  if (!client) {
    const r = await offlineReply(text);
    send("text", { delta: r.text });
    for (const a of r.actions) send("browser_action", a);
    send("done", { offline: true });
    return res.end();
  }

  let messages = sessions.get(sessionId) ?? [];
  if (messages.length > MAX_MESSAGES) {
    messages = [];
    send("notice", { message: "Conversation très longue : je repars d'une mémoire de travail vierge (la mémoire long terme est conservée)." });
  }
  // Conversation en cours de construction ; on ne l'enregistre qu'en cas de tour complet.
  const working = [...messages, { role: "user", content: `${contextLine()}\n${text}` }];

  try {
    let jsonRetries = 0;
    for (let round = 0; round < MAX_TOOL_ROUNDS && !closed; round++) {
      const stream = client.beta.messages.stream({
        model: MODEL,
        max_tokens: 64000,
        betas: ["server-side-fallback-2026-07-01"],
        fallbacks: "default", // si le modèle décline, l'API relance sur le modèle de repli recommandé
        output_config: { effort: EFFORT },
        cache_control: { type: "ephemeral" },
        system: [
          { type: "text", text: SYSTEM_PROMPT },
          { type: "text", text: memoryBlock() },
        ],
        tools: TOOLS,
        messages: working,
      });

      stream.on("text", (delta) => send("text", { delta }));
      stream.on("streamEvent", (event) => {
        if (event.type === "content_block_start") {
          const b = event.content_block;
          if (b.type === "tool_use" || b.type === "server_tool_use") send("tool", { name: b.name });
        }
      });

      let message;
      try {
        message = await stream.finalMessage();
        jsonRetries = 0;
      } catch (err) {
        // Entrée d'outil illisible ou connexion coupée : on relance le tour (max 2 fois).
        if (err instanceof Anthropic.APIError || jsonRetries++ >= 2) throw err;
        continue;
      }

      if (message.stop_reason === "refusal") {
        send("text", { delta: "\n\nJe suis désolé, je ne peux pas donner suite à cette demande." });
        break;
      }
      if (message.stop_reason === "pause_turn") {
        working.push({ role: "assistant", content: message.content });
        continue;
      }

      const toolUses = message.content.filter((b) => b.type === "tool_use");
      // Un appel d'outil coupé par max_tokens ne doit jamais être exécuté ni gardé dans l'historique.
      if (message.stop_reason === "max_tokens" && toolUses.length) throw new Error("Réponse tronquée (max_tokens)");
      working.push({ role: "assistant", content: message.content });

      if (message.stop_reason !== "tool_use" || toolUses.length === 0) {
        sessions.set(sessionId, working);
        break;
      }

      // Exécute tous les outils de ce tour en parallèle, renvoie tous les résultats dans un seul message.
      const results = await Promise.all(
        toolUses.map(async (tu) => {
          const r = await runTool(tu.name, tu.input);
          if (tu.name === "browser_action" && !r.isError) send("browser_action", tu.input);
          if (/^stock_|^todos$|^reminders$|^notes$/.test(tu.name)) send("refresh", { scope: tu.name });
          return { type: "tool_result", tool_use_id: tu.id, content: r.content, ...(r.isError ? { is_error: true } : {}) };
        }),
      );
      working.push({ role: "user", content: results });
      sessions.set(sessionId, working);
    }
    send("done", {});
  } catch (err) {
    console.error("[jarvis] erreur API :", err);
    if (err instanceof Anthropic.AuthenticationError) {
      const r = await offlineReply(text);
      send("notice", { message: "Clé API invalide : bascule en mode hors-ligne." });
      send("text", { delta: r.text });
      for (const a of r.actions) send("browser_action", a);
    } else if (err instanceof Anthropic.RateLimitError) {
      send("error", { message: "Je suis momentanément saturé (limite de débit). Réessayez dans quelques secondes." });
    } else if (err instanceof Anthropic.APIConnectionError) {
      const r = await offlineReply(text);
      send("notice", { message: "Connexion à mes serveurs perdue : réponse en mode hors-ligne." });
      send("text", { delta: r.text });
      for (const a of r.actions) send("browser_action", a);
    } else {
      send("error", { message: `Incident technique : ${err.message}` });
    }
    send("done", {});
  }
  res.end();
});

app.listen(PORT, () => {
  console.log(`\n  J.A.R.V.I.S. en ligne → http://localhost:${PORT}`);
  console.log(hasCredentials ? `  Cerveau : ${MODEL} (effort ${EFFORT})` : "  Mode hors-ligne (définissez ANTHROPIC_API_KEY pour l'intelligence complète)");
});
