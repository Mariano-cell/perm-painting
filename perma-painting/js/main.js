

// ==============================
// HEADER SCROLL STATES
// ==============================
const header = document.querySelector(".site-header");

if (header) {
  const SCROLL_TRIGGER = 20;   // efecto 1: color/blur
  const COMPACT_TRIGGER = 90;  // efecto 2: shrink

  const updateHeaderState = () => {
    const y = window.scrollY || document.documentElement.scrollTop;
    header.classList.toggle("is-scrolled", y > SCROLL_TRIGGER);
    header.classList.toggle("is-compact", y > COMPACT_TRIGGER);
  };

  updateHeaderState();
  window.addEventListener("scroll", updateHeaderState, { passive: true });
}

// =======================================
// MOBILE OVERLAY NAV (full-screen overlay)
// =======================================
(() => {
  const toggleBtn = document.querySelector(".site-header__toggle");
  const nav = document.querySelector("#site-nav");
  if (!toggleBtn || !nav) return;

  const panel = nav.querySelector(".site-nav__panel");
  const closeBtn = nav.querySelector(".site-nav__close");
  const navLinks = nav.querySelectorAll("a");

  const OPEN_LABEL = "Close menu";
  const CLOSED_LABEL = "Open menu";

  const isOpen = () => document.body.classList.contains("is-nav-open");

  const setToggleA11y = (open) => {
    toggleBtn.setAttribute("aria-expanded", open ? "true" : "false");
    toggleBtn.setAttribute("aria-label", open ? OPEN_LABEL : CLOSED_LABEL);
  };

  const focusFirstInsideNav = () => {
    // Prioridad: botón close, luego primer link, luego el panel (si fuera focusable)
    if (closeBtn) return closeBtn.focus();
    const firstLink = nav.querySelector("a");
    if (firstLink) return firstLink.focus();
  };

  const openNav = () => {
    // Guardamos el foco previo para devolverlo al cerrar
    nav.dataset.prevFocus = document.activeElement ? document.activeElement.className || "toggle" : "toggle";

    document.body.classList.add("is-nav-open");
    setToggleA11y(true);

    // Esperamos un tick para que el overlay sea "visible" antes de enfocar
    requestAnimationFrame(focusFirstInsideNav);
  };

  const closeNav = () => {
    document.body.classList.remove("is-nav-open");
    setToggleA11y(false);

    // Devolver foco al toggle (patrón modal básico)
    requestAnimationFrame(() => toggleBtn.focus());
  };

  // Estado inicial coherente (por si recarga con clase puesta por error)
  setToggleA11y(isOpen());

  // Toggle botón hamburguesa
  toggleBtn.addEventListener("click", () => {
    isOpen() ? closeNav() : openNav();
  });

  // Botón cerrar
  if (closeBtn) closeBtn.addEventListener("click", closeNav);

  // Click fuera del panel: cerrar
  nav.addEventListener("click", (e) => {
    if (!isOpen()) return;

    if (panel) {
      if (!panel.contains(e.target)) closeNav();
    } else {
      if (e.target === nav) closeNav();
    }
  });

  // ESC para cerrar
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen()) closeNav();
  });

  // Click en un link: cerrar
  navLinks.forEach((a) => a.addEventListener("click", () => {
    if (isOpen()) closeNav();
  }));

  // Si pasamos a desktop con el menú abierto, cerramos
  window.addEventListener(
    "resize",
    () => {
      if (window.innerWidth > 768 && isOpen()) closeNav();
    },
    { passive: true }
  );
})();
