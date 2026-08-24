(() => {
    const filters = document.querySelectorAll(".services-projects__filter-link[data-category]");
    const grid = document.querySelector("#services-grid");

    if (!filters.length || !grid) return;

    const galleries = {
        interior: [
            { src: "assets/photos/interior/interior_001.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_002.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_003.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_004.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_005.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_006.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_007.webp", alt: "Interior project" },
            { src: "assets/photos/interior/interior_008.webp", alt: "Interior project" },

        ],
        exterior: [
            { src: "assets/photos/exterior/exterior_001.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_002.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_003.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_004.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_005.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_006.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_007.webp", alt: "Exterior project" },
            { src: "assets/photos/exterior/exterior_008.webp", alt: "Exterior project" },

        ],
        residential: [
            { src: "assets/photos/residential/residential_001.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_002.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_003.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_004.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_005.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_006.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_007.webp", alt: "Residential project" },
            { src: "assets/photos/residential/residential_008.webp", alt: "Residential project" },

        ],
        commercial: [
            { src: "assets/photos/commercial/commercial_001.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_002.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_003.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_004.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_005.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_006.webp", alt: "Commercial project" },
            { src: "assets/photos/commercial/commercial_007.webp", alt: "Commercial project" },

        ],
        roof: [
            { src: "assets/photos/roof/roof_001.jpg", alt: "Restoration project" },
            { src: "assets/photos/roof/roof_002.jpg", alt: "Restoration project" },
            { src: "assets/photos/roof/roof_003.jpg", alt: "Restoration project" },
            { src: "assets/photos/roof/roof_004.jpg", alt: "Restoration project" },
            { src: "assets/photos/roof/roof_005.jpg", alt: "Restoration project" },
            { src: "assets/photos/roof/roof_006.jpg", alt: "Restoration project" },

        ],
        limewash: [
            { src: "assets/photos/limewash/limewash_001.jpg", alt: "Limewash project" },
            { src: "assets/photos/limewash/limewash_002.jpg", alt: "Limewash project" },
            { src: "assets/photos/limewash/limewash_003.jpg", alt: "Limewash project" },
            { src: "assets/photos/limewash/limewash_004.jpg", alt: "Limewash project" },
            { src: "assets/photos/limewash/limewash_005.jpg", alt: "Limewash project" },
            { src: "assets/photos/limewash/limewash_006.jpg", alt: "Limewash project" },

        ],
        decks: [
            { src: "assets/photos/decks/decks_001.jpg", alt: "Decks project" },
            { src: "assets/photos/decks/decks_002.jpg", alt: "Decks project" },
            { src: "assets/photos/decks/decks_003.jpg", alt: "Decks project" },
            { src: "assets/photos/decks/decks_004.jpg", alt: "Decks project" },
            { src: "assets/photos/decks/decks_005.jpg", alt: "Decks project" },

        ],
        "kitchen-cabinets": [
            { src: "assets/photos/kitchen-cabinets/kc_001.jpg", alt: "Cabinetry project" },
            { src: "assets/photos/kitchen-cabinets/kc_002.jpg", alt: "Cabinetry project" },
            { src: "assets/photos/kitchen-cabinets/kc_003.jpg", alt: "Cabinetry project" },
            { src: "assets/photos/kitchen-cabinets/kc_004.jpg", alt: "Cabinetry project" },
            { src: "assets/photos/kitchen-cabinets/kc_005.jpg", alt: "Cabinetry project" },
            { src: "assets/photos/kitchen-cabinets/kc_006.jpg", alt: "Cabinetry project" },

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
    const GALLERY_PLACEHOLDER_WIDTH = 900;
    const GALLERY_PLACEHOLDER_HEIGHT = 1200;
    const EMPTY_IMAGE =
        "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

    let galleryImageObserver = null;

    const toWebpSrc = (src) => src.replace(/\.(jpe?g|png)$/i, ".webp");

    const disconnectGalleryImageObserver = () => {
        if (galleryImageObserver) {
            galleryImageObserver.disconnect();
            galleryImageObserver = null;
        }
    };

    const hydrateDeferredPicture = (picture) => {
        const source = picture.querySelector("source[data-srcset]");
        const img = picture.querySelector("img[data-src]");

        if (source) {
            source.srcset = source.dataset.srcset || "";
            source.removeAttribute("data-srcset");
        }

        if (img) {
            img.src = img.dataset.src || "";
            img.removeAttribute("data-src");
        }

        picture.removeAttribute("data-deferred");
    };

    const observeDeferredPictures = () => {
        const deferredPictures = Array.from(
            grid.querySelectorAll('.services-projects__picture[data-deferred="true"]')
        );

        if (!deferredPictures.length) return;

        if (!("IntersectionObserver" in window)) {
            deferredPictures.forEach(hydrateDeferredPicture);
            return;
        }

        galleryImageObserver = new IntersectionObserver(
            (entries, observer) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    hydrateDeferredPicture(entry.target);
                    observer.unobserve(entry.target);
                });
            },
            { threshold: 0.01, rootMargin: "0px 0px 10% 0px" }
        );

        deferredPictures.forEach((picture) => galleryImageObserver.observe(picture));
    };

    const renderGallery = (category) => {
        const items = galleries[category] || [];
        disconnectGalleryImageObserver();
        grid.innerHTML = "";

        items.forEach((item, index) => {
            const figure = document.createElement("figure");
            figure.className = "services-projects__card";

            const picture = document.createElement("picture");
            picture.className = "services-projects__picture";

            const source = document.createElement("source");
            source.type = "image/webp";

            const img = document.createElement("img");
            img.className = "services-projects__img";
            img.alt = item.alt || "";
            img.decoding = "async";
            img.width = GALLERY_PLACEHOLDER_WIDTH;
            img.height = GALLERY_PLACEHOLDER_HEIGHT;

            if (index < 2) {
                source.srcset = toWebpSrc(item.src);
                img.src = item.src;
            } else {
                picture.dataset.deferred = "true";
                source.dataset.srcset = toWebpSrc(item.src);
                img.dataset.src = item.src;
                img.src = EMPTY_IMAGE;
                img.loading = "lazy";
            }

            picture.appendChild(source);
            picture.appendChild(img);
            figure.appendChild(picture);
            grid.appendChild(figure);
        });

        // caption dinámico (mismo estilo, solo cambia la categoría)
        const caption = document.createElement("p");
        caption.className = "services-projects__caption";

        const label = CATEGORY_LABELS[category] || category;
        caption.textContent = `${label} - ${CAPTION_SUFFIX}`;

        grid.appendChild(caption);
        observeDeferredPictures();

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







// =======================================
// SERVICES FILTERS TOGGLE (tablet/mobile)
// =======================================
(() => {
    const nav = document.querySelector(".services-projects__filters");
    if (!nav) return;

    const btn = nav.querySelector(".services-projects__filters-toggle");
    const list = nav.querySelector(".services-projects__filters-list");
    if (!btn || !list) return;

    const mq = window.matchMedia("(max-width: 1024px)");
    const isOpen = () => nav.classList.contains("is-open");

    const open = () => {
        nav.classList.add("is-open");
        btn.setAttribute("aria-expanded", "true");
    };

    const close = () => {
        nav.classList.remove("is-open");
        btn.setAttribute("aria-expanded", "false");
    };

    const toggle = () => (isOpen() ? close() : open());

    // click en el botón
    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggle();
    });

    // click afuera => cerrar (solo si estamos en tablet/mobile)
    document.addEventListener("click", (e) => {
        if (!mq.matches) return;
        if (!isOpen()) return;
        if (!nav.contains(e.target)) close();
    });

    // ESC => cerrar
    document.addEventListener("keydown", (e) => {
        if (!mq.matches) return;
        if (e.key === "Escape" && isOpen()) close();
    });

    // si tocás un filtro, cerramos el panel (tablet/mobile)
    nav.addEventListener("click", (e) => {
        if (!mq.matches) return;
        const filterBtn = e.target.closest(".services-projects__filter-link");
        if (filterBtn) close();
    });

    // al pasar a desktop, aseguramos estado limpio (sin colapsar)
    const sync = () => {
        if (!mq.matches) {
            close();
            btn.setAttribute("aria-expanded", "false");
        }
    };

    sync();
    mq.addEventListener?.("change", sync);
    window.addEventListener("resize", sync, { passive: true });
})();
