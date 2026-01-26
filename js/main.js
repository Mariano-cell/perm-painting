

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

const body = document.body;
const backdrop = document.querySelector(".nav-backdrop");

function closeNav() {
  body.classList.remove("is-nav-open");
}

backdrop.addEventListener("click", closeNav);

const track = document.querySelector(".why-perma__reasons-track");

if (track) {
  // Duplicamos el contenido 1 vez: ahora el track tiene 14 items (7 + 7).
  // La animación va hasta -50% para “caer” justo al inicio del segundo bloque.
  track.innerHTML += track.innerHTML;
}










(() => {
  const filters = document.querySelectorAll(".services-projects__filter-link[data-category]");
  const grid = document.querySelector("#services-grid");

  if (!filters.length || !grid) return;

  const galleries = {
    interior: [
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
      { src: "assets/photos/our services/interior.JPG", alt: "Interior project" },
    ],
    exterior: [
      { src: "assets/photos/our services/exterior.JPG", alt: "Exterior project" },
      { src: "assets/photos/IMG_1522.JPG", alt: "Exterior project detail" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Exterior project (prep)" },
      { src: "assets/photos/our services/deck.JPG", alt: "Exterior project (deck)" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Exterior project (limewash)" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Exterior project (commercial)" },
      { src: "assets/photos/our services/residential.JPG", alt: "Exterior project (residential)" },
    ],
    residential: [
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
      { src: "assets/photos/our services/residential.JPG", alt: "Residential project" },
    ],
    commercial: [
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
      { src: "assets/photos/our services/commercial.JPG", alt: "Commercial project" },
    ],
    restoration: [
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
      { src: "assets/photos/our services/restoration.JPG", alt: "Restoration project" },
    ],
    limewash: [
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
      { src: "assets/photos/our services/limewash-01.JPG", alt: "Limewash project" },
    ],
    decks: [
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
      { src: "assets/photos/our services/deck.JPG", alt: "Decks project" },
    ],
    cabinetry: [
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
      { src: "assets/photos/our services/cabinetry.JPG", alt: "Cabinetry project" },
    ],
  };

  const renderGallery = (category) => {
    const items = galleries[category] || [];
    grid.innerHTML = "";

    items.forEach((item) => {
      const figure = document.createElement("figure");
      figure.className = "services-projects__card";

      const img = document.createElement("img");
      img.className = "services-projects__img";
      img.src = item.src;
      img.alt = item.alt || "";

      figure.appendChild(img);
      grid.appendChild(figure);
    });

    // caption, si lo querés fijo como en el mock:
    const caption = document.createElement("p");
    caption.className = "services-projects__caption";
    caption.textContent = "Exterior - Byron Bay, NSW.";
    grid.appendChild(caption);
  };

  const setActive = (btn) => {
    filters.forEach((b) => {
      b.classList.toggle("is-active", b === btn);
      b.setAttribute("aria-selected", b === btn ? "true" : "false");
    });
  };

  filters.forEach((btn) => {
    btn.addEventListener("click", () => {
      const category = btn.dataset.category;
      setActive(btn);
      renderGallery(category);
    });
  });

  // init (usa el que venga activo en el HTML)
  const initiallyActive = document.querySelector(".services-projects__filter-link.is-active") || filters[0];
  setActive(initiallyActive);
  renderGallery(initiallyActive.dataset.category);
})();



async function loadReviews() {
  const container = document.getElementById('reviews-container');
  try {
    const response = await fetch('/.netlify/functions/get-reviews');
    const reviews = await response.json();

    container.innerHTML = reviews.map(rev => `
          <div class="review-card">
              <strong>${rev.author_name}</strong>
              <p>${"★".repeat(rev.rating)}</p>
              <p>${rev.text}</p>
          </div>
      `).join('');
  } catch (error) {
    container.innerHTML = '<p>No se pudieron cargar las reseñas.</p>';
  }
}

document.addEventListener('DOMContentLoaded', loadReviews);