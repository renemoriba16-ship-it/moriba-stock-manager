// Évaluateur d'expressions mathématiques sûr (pas d'eval).
// Supporte + - * / % ^, parenthèses, constantes (pi, e) et fonctions usuelles.

const FUNCS = {
  sqrt: Math.sqrt, abs: Math.abs, round: Math.round, floor: Math.floor, ceil: Math.ceil,
  sin: Math.sin, cos: Math.cos, tan: Math.tan, asin: Math.asin, acos: Math.acos, atan: Math.atan,
  ln: Math.log, log: Math.log10, log2: Math.log2, exp: Math.exp,
};
const CONSTS = { pi: Math.PI, e: Math.E };

function tokenize(src) {
  const s = src.replace(/,/g, ".").replace(/×/g, "*").replace(/÷/g, "/").toLowerCase();
  const tokens = [];
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (/\s/.test(c)) { i++; continue; }
    if (/[0-9.]/.test(c)) {
      let j = i;
      while (j < s.length && /[0-9.]/.test(s[j])) j++;
      if (s[j] === "e" && /[0-9+-]/.test(s[j + 1] ?? "")) {
        j++;
        if (/[+-]/.test(s[j])) j++;
        while (j < s.length && /[0-9]/.test(s[j])) j++;
      }
      const n = Number(s.slice(i, j));
      if (Number.isNaN(n)) throw new Error(`Nombre invalide: ${s.slice(i, j)}`);
      tokens.push({ t: "num", v: n });
      i = j;
    } else if (/[a-z]/.test(c)) {
      let j = i;
      while (j < s.length && /[a-z0-9]/.test(s[j])) j++;
      tokens.push({ t: "id", v: s.slice(i, j) });
      i = j;
    } else if ("+-*/%^()".includes(c)) {
      tokens.push({ t: "op", v: c });
      i++;
    } else {
      throw new Error(`Caractère inattendu: ${c}`);
    }
  }
  return tokens;
}

export function evaluate(expr) {
  const tokens = tokenize(String(expr));
  let pos = 0;
  const peek = () => tokens[pos];
  const eat = (v) => {
    const tk = tokens[pos];
    if (!tk || tk.v !== v) throw new Error(`Attendu "${v}"`);
    pos++;
  };

  // expr := term (('+'|'-') term)*
  function parseExpr() {
    let v = parseTerm();
    while (peek()?.t === "op" && (peek().v === "+" || peek().v === "-")) {
      const op = tokens[pos++].v;
      const r = parseTerm();
      v = op === "+" ? v + r : v - r;
    }
    return v;
  }
  // term := unary (('*'|'/'|'%') unary)*
  function parseTerm() {
    let v = parseUnary();
    while (peek()?.t === "op" && "*/%".includes(peek().v)) {
      const op = tokens[pos++].v;
      const r = parseUnary();
      if (op === "*") v *= r;
      else if (op === "/") {
        if (r === 0) throw new Error("Division par zéro");
        v /= r;
      } else v %= r;
    }
    return v;
  }
  // unary := ('-'|'+') unary | power
  function parseUnary() {
    if (peek()?.t === "op" && (peek().v === "-" || peek().v === "+")) {
      const op = tokens[pos++].v;
      const v = parseUnary();
      return op === "-" ? -v : v;
    }
    return parsePower();
  }
  // power := primary ('^' unary)?   (associatif à droite)
  function parsePower() {
    const base = parsePrimary();
    if (peek()?.t === "op" && peek().v === "^") {
      pos++;
      return Math.pow(base, parseUnary());
    }
    return base;
  }
  function parsePrimary() {
    const tk = tokens[pos++];
    if (!tk) throw new Error("Expression incomplète");
    if (tk.t === "num") return tk.v;
    if (tk.t === "id") {
      if (tk.v in CONSTS) return CONSTS[tk.v];
      if (tk.v in FUNCS) {
        eat("(");
        const arg = parseExpr();
        eat(")");
        return FUNCS[tk.v](arg);
      }
      throw new Error(`Inconnu: ${tk.v}`);
    }
    if (tk.v === "(") {
      const v = parseExpr();
      eat(")");
      return v;
    }
    throw new Error(`Symbole inattendu: ${tk.v}`);
  }

  const result = parseExpr();
  if (pos !== tokens.length) throw new Error("Expression mal formée");
  if (!Number.isFinite(result)) throw new Error("Résultat non fini");
  return Math.round(result * 1e12) / 1e12;
}
