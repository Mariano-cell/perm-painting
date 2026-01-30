

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

  const CATEGORY_LABELS = {
    interior: "Interior",
    exterior: "Exterior",
    residential: "Residential",
    commercial: "Commercial",
    restoration: "Restoration",
    limewash: "Limewash",
    decks: "Decks",
    cabinetry: "Cabinetry",
  };

  const CAPTION_SUFFIX = "Byron Bay, NSW.";


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

    // caption dinámico (mismo estilo, solo cambia la categoría)
    const caption = document.createElement("p");
    caption.className = "services-projects__caption";

    const label = CATEGORY_LABELS[category] || category;
    caption.textContent = `${label} - ${CAPTION_SUFFIX}`;

    grid.appendChild(caption);

    // Disparar animación de entrada (stagger)
    const cards = Array.from(grid.querySelectorAll(".services-projects__card"));

    // si el usuario prefiere reducir motion, no animamos
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      cards.forEach((c) => c.classList.add("is-in"));
      return;
    }

    // Importante: 2 RAF para asegurar que el "estado inicial" (opacity 0) se aplique
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        cards.forEach((card, i) => {
          setTimeout(() => card.classList.add("is-in"), i * 60); // 60ms stagger
        });
      });
    });


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

      history.replaceState(null, "", `#${encodeURIComponent(category)}`);
    });
  });


  // init: si viene hash (ej: our-services.html#decks), lo usamos
  const hash = (window.location.hash || "")
    .replace("#", "")
    .trim()
    .toLowerCase();

  const fromHash =
    hash &&
    Array.from(filters).find((b) => (b.dataset.category || "").toLowerCase() === hash);

  const initiallyActive =
    fromHash ||
    document.querySelector(".services-projects__filter-link.is-active") ||
    filters[0];

  setActive(initiallyActive);
  renderGallery(initiallyActive.dataset.category);

  // ==============================
  // Auto-scroll a la galería (solo si venís desde Home)
  // our-services.html?view=projects#interior
  // ==============================
  const params = new URLSearchParams(window.location.search);
  const shouldScrollToProjects = params.get("view") === "projects";

  if (shouldScrollToProjects) {
    const target = document.querySelector(".services-projects") || document.querySelector("#services-grid");
    if (target) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      // Esperamos a que el DOM tenga el contenido renderizado + layout listo
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const headerEl = document.querySelector(".site-header");
          const headerH = headerEl ? headerEl.getBoundingClientRect().height : 0;

          const y = window.scrollY + target.getBoundingClientRect().top - headerH + 60;

          window.scrollTo({
            top: Math.max(0, y),
            behavior: reduced ? "auto" : "smooth",
          });

          // opcional: limpiar el param para que si el usuario recarga, no vuelva a scrollear
          // (si querés esto, descomentá)
          // history.replaceState(null, "", window.location.pathname + window.location.hash);
        });
      });
    }
  }


})();



async function loadReviews() {
  const container = document.getElementById('reviews-container');
  try {
    const response = await fetch('/.netlify/functions/get-reviews');
    const reviews = await response.json();

    if (!reviews || reviews.length === 0) {
      container.innerHTML = '<p class="hero__insight">No reviews available at the moment.</p>';
      return;
    }

    container.innerHTML = reviews.map(rev => `
          <div class="review-card">
              <span class="review-card__author">${rev.author_name}</span>
              <div class="review-card__rating">${"★".repeat(rev.rating)}</div>
              <p class="review-card__text">"${rev.text}"</p>
          </div>
      `).join('');
  } catch (error) {
    container.innerHTML = '<p>Something went wrong loading reviews.</p>';
  }
}

document.addEventListener('DOMContentLoaded', loadReviews);

// =======================================
// LOCATIONS dropdown (search + select)
// =======================================
(() => {
  const root = document.querySelector("[data-locations]");
  if (!root) return;

  const trigger = root.querySelector(".locations__trigger");
  const triggerText = root.querySelector(".locations__trigger-text");
  const panel = root.querySelector(".locations__panel");
  const searchInput = root.querySelector(".locations__search-input");
  const optionBtns = Array.from(root.querySelectorAll(".locations__option-btn"));

  if (!trigger || !triggerText || !panel || !searchInput || optionBtns.length === 0) return;

  const isOpen = () => !panel.hasAttribute("hidden");

  const open = () => {
    panel.removeAttribute("hidden");
    trigger.setAttribute("aria-expanded", "true");

    // foco al search para que el usuario tipeé directo
    requestAnimationFrame(() => searchInput.focus());
  };

  const close = () => {
    panel.setAttribute("hidden", "");
    trigger.setAttribute("aria-expanded", "false");

    // limpiar filtro cuando cerrás (opcional; si no lo querés, borrá estas 2 líneas)
    searchInput.value = "";
    optionBtns.forEach((b) => (b.closest(".locations__option").style.display = ""));
  };

  const toggle = () => (isOpen() ? close() : open());

  const filter = (query) => {
    const q = query.trim().toLowerCase();
    optionBtns.forEach((btn) => {
      const label = (btn.dataset.location || btn.textContent).trim().toLowerCase();
      const show = label.includes(q);
      btn.closest(".locations__option").style.display = show ? "" : "none";
    });
  };

  // 1) abrir/cerrar con el trigger
  trigger.addEventListener("click", toggle);

  // 2) filtrar mientras tipeás
  searchInput.addEventListener("input", (e) => {
    filter(e.target.value);
  });

  // 3) seleccionar opción
  optionBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const value = btn.dataset.location || btn.textContent.trim();

      // 1) set dropdown text
      triggerText.textContent = value;
      close();

      // 2) update contact form title
      const titleEl = document.querySelector(".contact-form__title");
      if (titleEl) {
        // mantenemos el <br> como en tu diseño
        titleEl.innerHTML = `Tell us about<br>your project in ${value}!`;
      }

      // 3) scroll to form (con offset por header fijo)
      const formSection = document.querySelector(".contact-form");
      if (formSection) {
        const headerEl = document.querySelector(".site-header");
        const headerH = headerEl ? headerEl.getBoundingClientRect().height : 0;

        const y =
          window.scrollY + formSection.getBoundingClientRect().top - headerH - 16; // 16px “aire”

        window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
      }

      // 4) foco (mejor UX / a11y)
      requestAnimationFrame(() => trigger.focus());
    });
  });


  // 4) click afuera => cerrar
  document.addEventListener("click", (e) => {
    if (!isOpen()) return;
    if (!root.contains(e.target)) close();
  });

  // 5) ESC => cerrar
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen()) {
      e.preventDefault();
      close();
      requestAnimationFrame(() => trigger.focus());
    }
  });

  // 6) si estás en mobile (panel position: static) igual funciona,
  // pero evitamos que quede abierto al cambiar a desktop/tablet si querés:
  window.addEventListener(
    "resize",
    () => {
      if (!isOpen()) return;
      // si querés cerrarlo siempre al resize:
      close();
    },
    { passive: true }
  );
})();
