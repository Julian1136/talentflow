/**
 * TalentFlow — tema localStorage, CSRF en fetch, formularios con envío.
 */
(function () {
  const root = document.documentElement;
  const body = document.body;
  const LS_THEME = "tf_theme_mode";
  const LS_PRESET = "tf_theme_preset";
  const LEGACY_THEME = "tf-theme";

  function setMode(mode) {
    const dark = mode === "dark";
    if (dark) {
      root.setAttribute("data-theme", "dark");
      body.classList.add("dark");
    } else {
      root.removeAttribute("data-theme");
      body.classList.remove("dark");
    }
    localStorage.setItem(LS_THEME, dark ? "dark" : "light");
    paint();
  }

  function setPreset(preset) {
    if (preset === "vibrante") root.setAttribute("data-preset", "vibrante");
    else root.removeAttribute("data-preset");
    localStorage.setItem(LS_PRESET, preset);
    paint();
  }

  function paint() {
    const mode = localStorage.getItem(LS_THEME) || "light";
    const preset = localStorage.getItem(LS_PRESET) || "base";
    document.getElementById("chipDark")?.classList.toggle("active", mode === "dark");
    document.getElementById("chipPresetBase")?.classList.toggle("active", mode === "light" && preset === "base");
    document.getElementById("chipPresetVibrante")?.classList.toggle("active", preset === "vibrante");
  }

  document.getElementById("chipDark")?.addEventListener("click", () => {
    const current = localStorage.getItem(LS_THEME) || "light";
    setMode(current === "dark" ? "light" : "dark");
  });
  document.getElementById("chipPresetBase")?.addEventListener("click", () => {
    setMode("light");
    setPreset("base");
  });
  document.getElementById("chipPresetVibrante")?.addEventListener("click", () => setPreset("vibrante"));

  let initial = localStorage.getItem(LS_THEME);
  if (!initial) {
    const leg = localStorage.getItem(LEGACY_THEME);
    if (leg) {
      initial = leg === "dark" ? "dark" : "light";
      localStorage.removeItem(LEGACY_THEME);
    }
  }
  setMode(initial || "light");
  setPreset(localStorage.getItem(LS_PRESET) || "base");
})();

(function () {
  const meta = document.querySelector('meta[name="csrf-token"]');
  const token = meta?.getAttribute("content");
  if (token && window.fetch) {
    const orig = window.fetch;
    window.fetch = function (input, init) {
      init = init || {};
      const m = String(init.method || "GET").toUpperCase();
      if (m !== "GET" && m !== "HEAD" && m !== "OPTIONS") {
        const h = new Headers(init.headers || {});
        if (!h.has("X-CSRFToken")) h.set("X-CSRFToken", token);
        init.headers = h;
      }
      return orig.call(this, input, init);
    };
  }

  function armarFormularios() {
    if (!token) return;
    document.querySelectorAll('form[method="post"],form[method="POST"]').forEach((f) => {
      if (f.querySelector('input[name="csrf_token"]')) return;
      const i = document.createElement("input");
      i.type = "hidden";
      i.name = "csrf_token";
      i.value = token;
      f.prepend(i);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    armarFormularios();
    document.querySelectorAll("form[data-loading-on-submit]").forEach((form) => {
      form.addEventListener("submit", () => {
        form.classList.add("form-submitting");
      });
    });
  });
})();

(function () {
  const body = document.body;
  const marcaVista = body?.dataset?.tfMarcaVista;
  const marcaTodas = body?.dataset?.tfMarcaTodas;
  if (!marcaVista) return;

  const btn = document.getElementById("notifToggle");
  const drop = document.getElementById("notifDrop");
  if (!btn || !drop) return;

  const KEY_SEEN_COUNT = "tf_notif_last_count";
  const currentCount = Number(body.dataset.tfNotifCount || "0");
  const prevCount = Number(localStorage.getItem(KEY_SEEN_COUNT) || "0");
  if (currentCount > 0 && currentCount > prevCount) btn.classList.add("has-new");
  localStorage.setItem(KEY_SEEN_COUNT, String(currentCount));

  btn.addEventListener("click", () => drop.classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (!drop.contains(e.target) && !btn.contains(e.target)) drop.classList.remove("open");
  });

  drop.querySelectorAll(".notif-seen-btn").forEach((b) => {
    b.addEventListener("click", async (e) => {
      e.preventDefault();
      const key = b.dataset.key || "";
      if (!key) return;
      try {
        const form = new URLSearchParams();
        form.set("notif_key", key);
        const r = await fetch(marcaVista, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: form.toString(),
        });
        const d = await r.json();
        if (d.ok) {
          b.closest(".notif-item")?.remove();
          const badge = document.querySelector(".notif-badge");
          if (badge) {
            const n = Number(badge.textContent || "0") - 1;
            if (n > 0) badge.textContent = String(n);
            else badge.remove();
          }
        }
      } catch (_) {}
    });
  });

  const btnAll = document.getElementById("btnNotifAllSeen");
  btnAll?.addEventListener("click", async () => {
    const rows = [...drop.querySelectorAll(".notif-seen-btn")];
    const keys = rows.map((x) => x.dataset.key).filter(Boolean);
    if (!keys.length || !marcaTodas) return;
    try {
      const form = new URLSearchParams();
      keys.forEach((k) => form.append("notif_keys[]", k));
      const r = await fetch(marcaTodas, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      const d = await r.json();
      if (d.ok) {
        rows.forEach((x) => x.closest(".notif-item")?.remove());
        document.querySelector(".notif-badge")?.remove();
        btn.classList.remove("has-new");
        btnAll.remove();
      }
    } catch (_) {}
  });
})();
