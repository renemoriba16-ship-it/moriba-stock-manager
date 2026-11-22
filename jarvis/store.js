// Stockage JSON minimaliste sur disque (data/*.json), écritures atomiques.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = process.env.JARVIS_DATA_DIR || path.join(here, "data");
fs.mkdirSync(DATA_DIR, { recursive: true });

const DEFAULTS = {
  stock: { products: [], movements: [] },
  notes: { notes: [] },
  todos: { todos: [] },
  reminders: { reminders: [] },
  memory: { facts: [] },
};

export function load(name) {
  const file = path.join(DATA_DIR, `${name}.json`);
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return structuredClone(DEFAULTS[name] ?? {});
  }
}

export function save(name, data) {
  const file = path.join(DATA_DIR, `${name}.json`);
  const tmp = `${file}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, file);
}

export function update(name, fn) {
  const data = load(name);
  const result = fn(data);
  save(name, data);
  return result;
}

export const newId = () =>
  Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
