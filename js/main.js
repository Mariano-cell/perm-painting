

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

if (backdrop) backdrop.addEventListener("click", closeNav);

// =======================================
// NAV DROPDOWNS (mobile tap toggle)
// Desktop usa :hover (CSS). En mobile no hay hover, así que
// la flechita (.site-nav__caret) abre/cierra el dropdown.
// =======================================
(() => {
  const carets = document.querySelectorAll(".site-nav__caret");
  if (!carets.length) return;

  const mq = window.matchMedia("(max-width: 768px)");

  carets.forEach((caret) => {
    caret.addEventListener("click", (e) => {
      // Solo interceptamos en mobile; en desktop la flecha no se muestra.
      if (!mq.matches) return;
      e.preventDefault();
      e.stopPropagation();

      const item = caret.closest(".site-nav__item--has-dropdown");
      if (!item) return;

      // cerrar los otros dropdowns abiertos
      document
        .querySelectorAll(".site-nav__item--has-dropdown.is-open")
        .forEach((el) => {
          if (el !== item) el.classList.remove("is-open");
        });

      item.classList.toggle("is-open");
    });
  });

  // al cerrar el menú o pasar a desktop, resetear los dropdowns
  const resetDropdowns = () => {
    document
      .querySelectorAll(".site-nav__item--has-dropdown.is-open")
      .forEach((el) => el.classList.remove("is-open"));
  };

  window.addEventListener("resize", () => {
    if (!mq.matches) resetDropdowns();
  }, { passive: true });
})();

const track = document.querySelector(".why-perma__reasons-track");

if (track) {
  // Duplicamos el contenido 1 vez: ahora el track tiene 14 items (7 + 7).
  // La animación va hasta -50% para “caer” justo al inicio del segundo bloque.
  track.innerHTML += track.innerHTML;
}









async function loadReviews() {
  const container = document.getElementById("reviews-container");
  if (!container) return;

  try {
    const response = await fetch("/.netlify/functions/get-reviews");
    const reviews = await response.json();

    if (!reviews || reviews.length === 0) {
      container.innerHTML =
        '<p class="hero__insight">No reviews available at the moment.</p>';
      return;
    }

    container.innerHTML = reviews
      .slice(0, 4)
      .map((rev, i) => {
        const safeText = (rev.text || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const safeAuthor = (rev.author_name || "")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;");

        const id = `review-text-${i}`;

        return `
          <div class="review-card">
              <span class="review-card__author">${safeAuthor}</span>
              <div class="review-card__rating">${"★".repeat(rev.rating || 0)}</div>

              <div class="review-card__text-wrap">
                <p class="review-card__text" id="${id}">"${safeText}"</p>

                <button
                  class="review-card__toggle"
                  type="button"
                  aria-expanded="false"
                  aria-controls="${id}"
                  aria-label="Show full review"
                  hidden
                >+</button>
              </div>
          </div>
        `;
      })
      .join("");

    // Mostrar el botón SOLO si el texto supera el line-clamp
    const cards = container.querySelectorAll(".review-card");

    const needsExpandByClone = (textEl) => {
      // altura clamped (como se ve en pantalla)
      const clampedH = textEl.getBoundingClientRect().height;

      // clon para medir el texto completo, mismo ancho
      const clone = textEl.cloneNode(true);

      // sacarlo del layout visual pero que mida bien
      clone.style.position = "absolute";
      clone.style.visibility = "hidden";
      clone.style.pointerEvents = "none";
      clone.style.height = "auto";
      clone.style.maxHeight = "none";

      // IMPORTANTÍSIMO: anular clamp en el clon
      clone.style.display = "block";
      clone.style.overflow = "visible";
      clone.style.webkitLineClamp = "unset";
      clone.style.webkitBoxOrient = "initial";

      // mismo ancho que el original (para mismo wrap)
      clone.style.width = `${textEl.getBoundingClientRect().width}px`;

      document.body.appendChild(clone);
      const fullH = clone.getBoundingClientRect().height;
      clone.remove();

      return fullH > clampedH + 1;
    };

    cards.forEach((card) => {
      const text = card.querySelector(".review-card__text");
      const btn = card.querySelector(".review-card__toggle");
      if (!text || !btn) return;

      // estado inicial
      card.classList.remove("is-expanded");
      btn.setAttribute("aria-expanded", "false");
      btn.textContent = "+";
      btn.hidden = true;

      // medir (clon)
      const needsExpand = needsExpandByClone(text);
      btn.hidden = !needsExpand;

      // click toggle
      btn.addEventListener("click", () => {
        const isExpanded = card.classList.toggle("is-expanded");
        btn.setAttribute("aria-expanded", String(isExpanded));
        btn.textContent = isExpanded ? "−" : "+";
        btn.setAttribute("aria-label", isExpanded ? "Collapse review" : "Show full review");

        // Animación suave usando max-height en px
        if (isExpanded) {
          // 1) arrancar desde el alto actual (colapsado)
          const from = text.getBoundingClientRect().height;

          // 2) medir alto completo
          text.style.maxHeight = `${from}px`;
          // forzar reflow
          text.offsetHeight;

          // 3) setear destino: alto completo (scrollHeight)
          const to = text.scrollHeight;
          text.style.maxHeight = `${to}px`;
          text.addEventListener(
            "transitionend",
            () => {
              // cuando terminó de abrir, liberamos el max-height
              if (card.classList.contains("is-expanded")) {
                text.style.maxHeight = "none";
              }
            },
            { once: true }
          );
        } else {
          // cierre: ir desde alto actual (expandido) a alto colapsado
          const from = text.getBoundingClientRect().height;
          text.style.maxHeight = `${from}px`;
          text.offsetHeight;

          // tu alto colapsado fijo (ajustalo a tu look)
          const collapsed = getComputedStyle(text).getPropertyValue("--collapsed-h").trim();
          text.style.maxHeight = collapsed;

        }
      });

    });


  } catch (error) {
    container.innerHTML = "<p>Something went wrong loading reviews.</p>";
  }
}

document.addEventListener("DOMContentLoaded", loadReviews);


// =======================================
// PAGE TRANSITIONS (salida con blur)
// =======================================
(() => {
  const LEAVE_MS = 300; // debe coincidir con la transition de .page-leave en style.css

  document.addEventListener("click", (e) => {
    // Respetar accesibilidad: sin animación si el user pidió reduced motion
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const link = e.target.closest("a[href]");
    if (!link) return;

    // Si otro handler ya canceló la navegación (ej: dropdown de locations), no tocar
    if (e.defaultPrevented) return;

    // Solo click izquierdo simple, misma pestaña, mismo dominio, sin download
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    if (link.target && link.target !== "_self") return;
    if (link.origin !== location.origin) return;
    if (link.hasAttribute("download")) return;

    // Anchors dentro de la misma página (#seccion): scroll normal, sin animación
    if (link.pathname === location.pathname && link.hash) return;

    e.preventDefault();
    document.body.classList.add("page-leave");
    setTimeout(() => {
      location.href = link.href;
    }, LEAVE_MS);
  });

  // Si la página vuelve desde el bfcache (botón atrás), limpiar el estado de salida
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) document.body.classList.remove("page-leave");
  });
})();

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

  // --- SEO local: helpers ---
  const slugify = (name) =>
    name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

  // Actualiza h2, <title>, meta description y canonical para una localidad
  const applyLocation = (value) => {
    triggerText.textContent = value;

    const titleEl = document.querySelector(".contact-form__title");
    if (titleEl) {
      titleEl.innerHTML = `Tell us about<br>your project in ${value}!`;
    }

    document.title = `Painters in ${value} | Perma P.`;

    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        "content",
        `Professional painting services in ${value}, NSW. Get a free quote from Perma Painting, your local Northern Rivers painters.`
      );
    }

    const canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      canonical.setAttribute(
        "href",
        `${location.origin}/contact/${slugify(value)}`
      );
    }
  };

  // Al cargar /contact/<slug> (página estática generada): el h2, <title>,
  // meta y canonical ya vienen en el HTML — solo reflejamos la localidad
  // en el trigger del dropdown. NO usar applyLocation acá: pisaría los
  // textos únicos de cada página generada.
  const slugMatch = location.pathname.match(/^\/contact\/([a-z0-9-]+)\/?$/);
  if (slugMatch) {
    const btn = optionBtns.find(
      (b) => slugify(b.dataset.location || b.textContent.trim()) === slugMatch[1]
    );
    if (btn) triggerText.textContent = btn.dataset.location || btn.textContent.trim();
  }

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
    btn.addEventListener("click", (e) => {
      // El href existe para que Google indexe /contact/<slug>;
      // acá interceptamos para no recargar y no perder datos del form.
      e.preventDefault();

      const value = btn.dataset.location || btn.textContent.trim();

      // 1) actualizar URL sin recargar
      const href = btn.getAttribute("href") || `/contact/${slugify(value)}`;
      history.pushState({ location: value }, "", href);

      // 2) h2 + <title> + meta + canonical
      applyLocation(value);
      close();

      // 3) scroll al principio de la página
      window.scrollTo({ top: 0, behavior: "smooth" });

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


// =======================================
// SCROLL REVEAL (calmo: fade + leve subida)
// Revela los elementos .reveal una sola vez al entrar al viewport.
// =======================================
(() => {
  const items = document.querySelectorAll(".reveal, .os-reveal");
  if (!items.length) return;

  // Fallback: sin IntersectionObserver o con reduced-motion, mostrar todo.
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const reveal = (el) => el.classList.add("is-visible");

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          reveal(entry.target);
          obs.unobserve(entry.target); // una sola vez
        }
      });
    },
    // threshold 0 = dispara apenas el borde del elemento cruza la zona.
    // El rootMargin negativo abajo retrasa ese cruce hasta que la imagen
    // sube un poco en pantalla, dando a cada fila su propio punto de
    // entrada sin exigir un % de área (que las imágenes altas no cumplen).
    { threshold: 0, rootMargin: "0px 0px -12% 0px" }
  );

  items.forEach((el) => observer.observe(el));

  // Red de seguridad: revela cualquier elemento que ya esté dentro del
  // viewport pero que el observer no haya marcado (p. ej. imágenes altas
  // que no disparan). Corre al cargar y en cada scroll, así ninguna fila
  // queda atrapada invisible, pero las de más abajo conservan su entrada.
  const isInViewport = (el) => {
    const r = el.getBoundingClientRect();
    const vh = window.innerHeight || document.documentElement.clientHeight;
    return r.top < vh * 0.92 && r.bottom > 0; // un poco dentro, no pegado al borde
  };

  const safetyCheck = () => {
    items.forEach((el) => {
      if (!el.classList.contains("is-visible") && isInViewport(el)) reveal(el);
    });
  };

  window.addEventListener("scroll", safetyCheck, { passive: true });
  window.addEventListener("load", () => setTimeout(safetyCheck, 300));
})();

// ==============================
// HERO SLIDESHOW (cross-fade cada 6s, escalonado izq/der)
// ==============================
(() => {
  const INTERVAL = 6000;       // ms entre fotos
  const REVEAL_DONE = 2500;    // la animación de entrada del hero termina ~2.3s
  const STAGGER = 1000;        // la derecha rota 1s después de la izquierda

  // Respetar a quien prefiere menos movimiento: no rotar
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const left = document.querySelector(".hero__left--photo-container.hero-slideshow");
  const right = document.querySelector(".hero__right--photo-container.hero-slideshow");

  const start = (show, delay) => {
    if (!show) return;
    const slides = Array.from(show.querySelectorAll(".hero-slide"));
    if (slides.length < 2) return;

    // Activamos "is-running" cuando el reveal de entrada ya terminó: a partir de
    // acá la 1ª slide hace cross-fade por opacidad (sin saltos ni parpadeo).
    show.classList.add("is-running");

    let current = 0; // arranca en la imagen original (1ª), ya marcada .is-active

    const advance = () => {
      slides[current].classList.remove("is-active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("is-active");
    };

    // El primer avance ocurre tras INTERVAL (+ delay escalonado); luego cada INTERVAL.
    setTimeout(() => {
      advance();
      setInterval(advance, INTERVAL);
    }, INTERVAL + delay);
  };

  // Esperamos a que termine el reveal de entrada antes de armar el carrusel,
  // así "is-running" no provoca el espasmo en el primer cambio.
  setTimeout(() => {
    start(left, 0);
    start(right, STAGGER); // la derecha, 1s después
  }, REVEAL_DONE);
})();
