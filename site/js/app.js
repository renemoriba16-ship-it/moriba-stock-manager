(function () {
  "use strict";
  const S = window.SHOP;
  const P = window.PRODUCTS;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = matchMedia("(pointer: fine)").matches;
  const SIZES = ["M", "L", "XL", "XXL"];
  const CAT_LABEL = { club: "Club", selection: "Sélection" };

  const money = (n) => {
    const v = n.toLocaleString("fr-FR", { maximumFractionDigits: 2 }).replace(/\u202f|\u00a0/g, " ");
    return S.currencyAfter ? `${v} ${S.currency}` : `${S.currency}${v}`;
  };
  const byId = (id) => P.find((p) => p.id === id);
  const isOut = (p) => p.status === "bientot" || (p.status === "stock" && p.stock <= 0);
  const limitOf = (p) => (p.status === "stock" ? p.stock : 99);
  const metaOf = (p) => [CAT_LABEL[p.category], p.season].filter(Boolean).join(" • ");

  /* Photo réelle si fournie dans config.js (photo / photoBack), sinon maillot dessiné */
  const img = (src, alt, fit) => `<img class="jersey-photo${fit === "cover" ? " cover" : ""}" src="${escapeXML(src)}" alt="${escapeXML(alt)}" loading="lazy" />`;
  const hasBack = (p) => !p.photo || !!p.photoBack;
  function face(p, side = "front", opts = {}) {
    if (side === "front" && p.photo) return img(p.photo, p.name, p.fit);
    if (side === "back" && p.photoBack) return img(p.photoBack, p.name + " (dos)", p.fit);
    if (side === "back" && p.photo) return img(p.photo, p.name, p.fit);
    return jerseySVG(p, side === "back" ? { side: "back", name: S.backName || S.name, number: 10, ...opts } : opts);
  }

  /* ---------------- Static text from config ---------------- */
  $$("[data-shop-name]").forEach((el) => (el.textContent = S.name));
  $("[data-tagline]").textContent = S.tagline;
  $("#year").textContent = new Date().getFullYear();
  $("#waContact").href = `https://wa.me/${S.whatsapp}`;
  $("#mailContact").href = `mailto:${S.email}`;
  $("#igContact").href = S.instagram;
  document.title = `${S.name} — Boutique de maillots`;

  /* ---------------- Header, progress, cursor ---------------- */
  const header = $(".header");
  const progress = $(".progress");
  let lastY = 0;
  addEventListener("scroll", () => {
    const y = scrollY;
    header.classList.toggle("scrolled", y > 30);
    header.classList.toggle("hidden", y > lastY && y > 400 && !$("#nav").classList.contains("open"));
    lastY = y;
    const h = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${h > 0 ? y / h : 0})`;
  }, { passive: true });

  const burger = $("#burger"), nav = $("#nav");
  burger.addEventListener("click", () => {
    burger.classList.toggle("open");
    nav.classList.toggle("open");
  });
  $$("a", nav).forEach((a) => a.addEventListener("click", () => { burger.classList.remove("open"); nav.classList.remove("open"); }));

  const glow = $(".cursor-glow");
  if (finePointer && !reduceMotion) {
    addEventListener("pointermove", (e) => { glow.style.left = e.clientX + "px"; glow.style.top = e.clientY + "px"; }, { passive: true });
  }

  /* ---------------- Reveal on scroll ---------------- */
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
  function observeReveals(root = document) {
    $$(".reveal:not(.in)", root).forEach((el) => {
      const sibs = [...el.parentElement.children].filter((c) => c.classList.contains("reveal"));
      if (!el.style.getPropertyValue("--d") && !el.closest(".hero")) el.style.setProperty("--d", `${sibs.indexOf(el) * 0.08}s`);
      io.observe(el);
    });
  }
  observeReveals();

  /* ---------------- Counters ---------------- */
  const counterIO = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target, end = parseFloat(el.dataset.count), dec = +(el.dataset.decimals || 0);
      const t0 = performance.now(), dur = reduceMotion ? 1 : 1800;
      const tick = (t) => {
        const k = Math.min(1, (t - t0) / dur), ease = 1 - Math.pow(1 - k, 4);
        const v = dec ? (end * ease).toFixed(dec) : Math.round(end * ease).toLocaleString("fr-FR").replace(/\u202f|\u00a0/g, " ");
        el.textContent = v + (k === 1 && "plus" in el.dataset ? "+" : "");
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      counterIO.unobserve(el);
    });
  }, { threshold: 0.6 });
  $$("[data-count]").forEach((el) => counterIO.observe(el));

  /* ---------------- Magnetic buttons & tilt cards ---------------- */
  if (finePointer && !reduceMotion) {
    document.addEventListener("pointermove", (e) => {
      const m = e.target.closest(".magnetic");
      if (m) {
        const r = m.getBoundingClientRect();
        m.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.25}px, ${(e.clientY - r.top - r.height / 2) * 0.35}px)`;
      }
      const t = e.target.closest(".tilt");
      if (t) {
        const r = t.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        t.style.transform = `perspective(900px) rotateX(${(0.5 - y) * 10}deg) rotateY(${(x - 0.5) * 12}deg)`;
        t.style.setProperty("--mx", x * 100 + "%");
        t.style.setProperty("--my", y * 100 + "%");
      }
    }, { passive: true });
    document.addEventListener("pointerout", (e) => {
      const el = e.target.closest(".magnetic, .tilt");
      if (el && !el.contains(e.relatedTarget)) el.style.transform = "";
    });
  }

  /* ---------------- Hero jersey carousel + parallax ---------------- */
  const heroStage = $("#heroJersey");
  const heroPicks = P.filter((p) => !isOut(p) && p.fit !== "cover").slice(0, 6);
  if (!heroPicks.length) heroPicks.push(P[0]);
  let heroIdx = 0;
  heroStage.innerHTML = face(heroPicks[0], "front", { number: 10 });
  if (!reduceMotion) {
    setInterval(() => {
      const old = heroStage.firstElementChild;
      old.classList.add("swap-out");
      setTimeout(() => {
        heroIdx = (heroIdx + 1) % heroPicks.length;
        heroStage.innerHTML = face(heroPicks[heroIdx], "front", { number: 10 });
        heroStage.firstElementChild.classList.add("swap-in");
      }, 450);
    }, 3500);
    if (finePointer) {
      $(".hero").addEventListener("pointermove", (e) => {
        const x = e.clientX / innerWidth - 0.5, y = e.clientY / innerHeight - 0.5;
        heroStage.style.transform = `rotateY(${x * 24}deg) rotateX(${-y * 16}deg)`;
        $$(".blob").forEach((b, i) => (b.style.translate = `${x * (i + 1) * 30}px ${y * (i + 1) * 30}px`));
      });
    }
  }

  /* ---------------- Category shortcuts ---------------- */
  $$("[data-goto-search]").forEach((b) => b.addEventListener("click", () => {
    setFilter("all");
    $("#search").value = b.dataset.gotoSearch;
    state.q = b.dataset.gotoSearch.toLowerCase();
    renderProducts();
  }));
  $$("[data-goto]").forEach((b) => b.addEventListener("click", () => {
    setFilter(b.dataset.goto);
    $("#catalogue").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
  }));

  /* ---------------- Catalogue ---------------- */
  const grid = $("#products");
  const state = { filter: "all", q: "", sort: "default" };

  function renderProducts() {
    let list = P.filter((p) => (state.filter === "all" || p.category === state.filter) &&
      (p.name + " " + (p.season || "") + " " + CAT_LABEL[p.category]).toLowerCase().includes(state.q));
    if (state.sort === "price-asc") list = [...list].sort((a, b) => a.price - b.price);
    if (state.sort === "price-desc") list = [...list].sort((a, b) => b.price - a.price);
    if (state.sort === "name") list = [...list].sort((a, b) => a.name.localeCompare(b.name, "fr"));
    $("#empty").hidden = list.length > 0;
    grid.innerHTML = list.map((p, i) => {
      const out = isOut(p);
      return `
      <article class="product" style="--i:${i}" data-id="${p.id}" tabindex="0" aria-label="${escapeXML(p.name)}">
        ${p.status === "bientot" ? `<span class="badge soon">Bientôt disponible</span>` : out ? `<span class="badge out">Rupture</span>` : p.badge ? `<span class="badge">${escapeXML(p.badge)}</span>` : ""}
        <div class="product-media${p.photo ? (p.fit === "cover" ? " photo-cover" : " photo-light") : ""}" style="--glow:${p.colors[0]}55">
          <div class="flip${hasBack(p) ? "" : " no-flip"}${p.photo ? " has-photo" : ""}"><div class="flip-inner">
            <div class="flip-face front">${face(p)}</div>
            <div class="flip-face back">${face(p, "back")}</div>
          </div></div>
          ${out ? "" : `<button class="quick-add" data-quick="${p.id}" aria-label="Ajout rapide ${escapeXML(p.name)}">+</button>`}
        </div>
        <div class="product-info">
          <span class="meta">${metaOf(p)}</span>
          <h3>${escapeXML(p.name)}</h3>
          <div class="price">${money(p.price)} ${p.oldPrice ? `<s>${money(p.oldPrice)}</s>` : ""}</div>
          ${p.status === "commande" ? `<div class="on-order">Sur commande</div>` : p.status === "stock" && !out && p.stock <= 5 ? `<div class="stock-low">Plus que ${p.stock} en stock</div>` : ""}
        </div>
      </article>`;
    }).join("");
  }

  function setFilter(f) {
    state.filter = f;
    $$(".chip").forEach((c) => c.classList.toggle("active", c.dataset.filter === f));
    renderProducts();
  }
  $$(".chip").forEach((c) => c.addEventListener("click", () => setFilter(c.dataset.filter)));
  $("#search").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); renderProducts(); });
  $("#sort").addEventListener("change", (e) => { state.sort = e.target.value; renderProducts(); });

  grid.addEventListener("click", (e) => {
    const quick = e.target.closest("[data-quick]");
    if (quick) {
      e.stopPropagation();
      addToCart({ id: quick.dataset.quick, size: "M", qty: 1 }, quick.closest(".product").querySelector(".flip-face.front > *"));
      return;
    }
    const card = e.target.closest(".product");
    if (card) openModal(card.dataset.id);
  });
  grid.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.classList.contains("product")) openModal(e.target.dataset.id);
  });
  renderProducts();

  /* ---------------- Product modal ---------------- */
  const modal = $("#modal");
  const m = { id: null, size: null, qty: 1 };
  let lastFocus = null;

  function openModal(id) {
    const p = byId(id);
    if (!p) return;
    lastFocus = document.activeElement;
    Object.assign(m, { id, size: null, qty: 1 });
    $(".modal-visual").style.setProperty("--glow", p.colors[0] + "77");
    $("#mCat").textContent = metaOf(p);
    $("#mTitle").textContent = p.name;
    $("#mPrice").innerHTML = `${money(p.price)}${p.oldPrice ? `<s>${money(p.oldPrice)}</s>` : ""}`;
    const stock = $("#mStock");
    const low = p.status === "stock" && p.stock <= 5;
    stock.textContent =
      p.status === "bientot" ? "Bientôt disponible — écris-nous sur WhatsApp pour être prévenu" :
      p.status === "commande" ? "Sur commande — on te confirme le délai sur WhatsApp" :
      p.stock <= 0 ? "Rupture de stock — contacte-nous sur WhatsApp" :
      low ? `Plus que ${p.stock} en stock, fais vite !` : "En stock";
    stock.classList.toggle("low", low || p.status === "bientot");
    $("#mSizes").innerHTML = SIZES.map((s) => `<button type="button" data-size="${s}">${s}</button>`).join("");
    $("#mQty").textContent = "1";
    $("#mFlip").classList.remove("turned");
    $("#mTurn").textContent = "↻ Voir le dos";
    $("#mAdd").disabled = isOut(p);
    $("#mAdd").textContent = p.status === "bientot" ? "Bientôt disponible" : isOut(p) ? "Indisponible" : "Ajouter au panier";
    renderModalJersey();
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("locked");
    setTimeout(() => $(".modal-close").focus(), 50);
  }
  function renderModalJersey() {
    const p = byId(m.id);
    $("#mFront").innerHTML = face(p);
    $("#mBack").innerHTML = face(p, "back");
    $("#mTurn").hidden = !hasBack(p);
    $("#mFlip").classList.toggle("has-photo", !!p.photo);
  }
  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("locked");
    if (lastFocus) lastFocus.focus();
  }
  $$("[data-close]", modal).forEach((b) => b.addEventListener("click", closeModal));
  $("#mSizes").addEventListener("click", (e) => {
    const b = e.target.closest("[data-size]");
    if (!b) return;
    m.size = b.dataset.size;
    $$("#mSizes button").forEach((x) => x.classList.toggle("active", x === b));
  });
  $("#mTurn").addEventListener("click", () => {
    const f = $("#mFlip");
    f.classList.toggle("turned");
    $("#mTurn").textContent = f.classList.contains("turned") ? "↻ Voir la face" : "↻ Voir le dos";
  });
  $("#mMinus").addEventListener("click", () => { m.qty = Math.max(1, m.qty - 1); $("#mQty").textContent = m.qty; });
  $("#mPlus").addEventListener("click", () => { m.qty = Math.min(limitOf(byId(m.id)) || 1, m.qty + 1); $("#mQty").textContent = m.qty; });
  $("#mAdd").addEventListener("click", () => {
    if (!m.size) {
      toast("Choisis ta taille 👕");
      $("#mSizes").animate([{ transform: "translateX(0)" }, { transform: "translateX(-8px)" }, { transform: "translateX(8px)" }, { transform: "translateX(0)" }], { duration: 350 });
      return;
    }
    addToCart({ id: m.id, size: m.size, qty: m.qty }, $("#mFlip .flip-face.front > *"));
    closeModal();
  });

  /* ---------------- Cart ---------------- */
  const KEY = "moriba-cart";
  let cart = [];
  try { cart = JSON.parse(localStorage.getItem(KEY)) || []; } catch (_) { cart = []; }
  cart = cart.filter((it) => byId(it.id) && !isOut(byId(it.id)) && SIZES.includes(it.size)).map(({ id, size, qty }) => ({ id, size, qty }));
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(cart)); } catch (_) {} };
  const keyOf = (it) => it.id + "|" + it.size;
  const unitPrice = (it) => byId(it.id).price;

  function addToCart(item, sourceEl) {
    const p = byId(item.id);
    const k = keyOf(item);
    const existing = cart.find((c) => keyOf(c) === k);
    const inCart = cart.filter((c) => c.id === item.id).reduce((s, c) => s + c.qty, 0);
    if (isOut(p)) return;
    if (inCart + item.qty > limitOf(p)) { toast(`Quantité max atteinte (${limitOf(p)})`); return; }
    if (existing) existing.qty += item.qty; else cart.push({ ...item });
    save();
    header.classList.remove("hidden");
    flyToCart(sourceEl, () => { renderCart(); bumpCount(); });
    toast(`✓ ${p.name} (${item.size}) ajouté`);
  }

  function flyToCart(el, done) {
    const target = $("#openCart");
    if (!el || reduceMotion) { done(); return; }
    const r = el.getBoundingClientRect(), t = target.getBoundingClientRect();
    const clone = el.cloneNode(true);
    const fly = document.createElement("div");
    fly.className = "fly";
    fly.appendChild(clone);
    fly.style.left = r.left + r.width / 2 - 35 + "px";
    fly.style.top = r.top + r.height / 2 - 40 + "px";
    document.body.appendChild(fly);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      fly.style.transform = `translate(${t.left + t.width / 2 - (r.left + r.width / 2)}px, ${t.top + t.height / 2 - (r.top + r.height / 2)}px) scale(.25) rotate(360deg)`;
      fly.style.opacity = ".4";
    }));
    setTimeout(() => { fly.remove(); done(); }, 800);
  }

  function bumpCount() {
    const c = $("#cartCount");
    c.classList.remove("bump"); void c.offsetWidth; c.classList.add("bump");
  }

  const totalOf = () => cart.reduce((s, it) => s + unitPrice(it) * it.qty, 0);

  function renderCart() {
    const count = cart.reduce((s, it) => s + it.qty, 0);
    $("#cartCount").textContent = count;
    const total = totalOf();
    const list = $("#cartItems");
    if (!cart.length) {
      list.innerHTML = `<li class="cart-empty"><span>👕</span>Ton panier est vide.<br/>Va vite choisir un maillot !</li>`;
    } else {
      list.innerHTML = cart.map((it, i) => {
        const p = byId(it.id);
        return `
        <li class="cart-item" data-i="${i}" style="animation-delay:${i * 50}ms">
          <div class="cart-thumb">${face(p)}</div>
          <div>
            <h4>${escapeXML(p.name)}</h4>
            <small>Taille ${it.size} • ${money(unitPrice(it))} l'unité</small>
            <div class="qty"><button data-act="minus" aria-label="Moins">−</button><span>${it.qty}</span><button data-act="plus" aria-label="Plus">+</button></div>
          </div>
          <div><div class="line-price">${money(unitPrice(it) * it.qty)}</div><button class="rm" data-act="rm">Retirer</button></div>
        </li>`;
      }).join("");
    }
    $("#total").textContent = money(total);
    $("#checkout").disabled = !cart.length;
  }

  $("#cartItems").addEventListener("click", (e) => {
    const b = e.target.closest("[data-act]");
    if (!b) return;
    const li = b.closest(".cart-item"), i = +li.dataset.i, it = cart[i];
    const act = b.dataset.act;
    if (act === "plus") {
      const p = byId(it.id), inCart = cart.filter((c) => c.id === it.id).reduce((s, c) => s + c.qty, 0);
      if (inCart >= limitOf(p)) { toast(`Quantité max atteinte (${limitOf(p)})`); return; }
      it.qty++;
    }
    if (act === "minus") it.qty--;
    if (act === "rm" || it.qty <= 0) {
      li.classList.add("removing");
      setTimeout(() => { cart.splice(i, 1); save(); renderCart(); }, reduceMotion ? 0 : 350);
      return;
    }
    save(); renderCart();
  });

  const drawer = $("#drawer");
  const openCart = () => { drawer.classList.add("open"); drawer.setAttribute("aria-hidden", "false"); document.body.classList.add("locked"); };
  const closeCart = () => { drawer.classList.remove("open"); drawer.setAttribute("aria-hidden", "true"); document.body.classList.remove("locked"); };
  $("#openCart").addEventListener("click", openCart);
  $$("[data-close-cart]").forEach((b) => b.addEventListener("click", closeCart));
  $("#clearCart").addEventListener("click", () => { if (cart.length && confirm("Vider le panier ?")) { cart = []; save(); renderCart(); } });
  addEventListener("keydown", (e) => { if (e.key === "Escape") { closeModal(); closeCart(); } });

  try {
    $("#custName").value = localStorage.getItem("moriba-name") || "";
    $("#custCity").value = localStorage.getItem("moriba-city") || "";
  } catch (_) {}

  $("#checkout").addEventListener("click", () => {
    if (!cart.length) return;
    const name = $("#custName").value.trim(), city = $("#custCity").value.trim();
    if (!name || !city) { toast("Indique ton nom et ta ville 📦"); (!name ? $("#custName") : $("#custCity")).focus(); return; }
    try { localStorage.setItem("moriba-name", name); localStorage.setItem("moriba-city", city); } catch (_) {}
    const total = totalOf();
    const lines = cart.map((it) => {
      const p = byId(it.id);
      return `• ${it.qty} × ${p.name} (taille ${it.size}) : ${money(unitPrice(it) * it.qty)}`;
    });
    const msg = [
      `Bonjour ${S.name} 👋, je souhaite commander :`, "", ...lines, "",
      `*Total maillots : ${money(total)}*`, "",
      `Nom : ${name}`, `Lieu de livraison : ${city}`, "",
      "Merci de me confirmer le prix de la livraison 🙏",
    ].join("\n");
    window.open(`https://wa.me/${S.whatsapp}?text=${encodeURIComponent(msg)}`, "_blank", "noopener");
  });

  renderCart();

  /* ---------------- Toast ---------------- */
  let toastT;
  function toast(text) {
    const t = $("#toast");
    t.textContent = text;
    t.classList.add("show");
    clearTimeout(toastT);
    toastT = setTimeout(() => t.classList.remove("show"), 2400);
  }
})();
