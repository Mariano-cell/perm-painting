/* =========================================================
   BLOG — filtro por categoría (solo /blog)

   Filtrado en el cliente: las tarjetas ya están todas en el HTML
   (bien para SEO) y acá solo escondemos las que no corresponden.
   Nada de fetch ni de rutas nuevas.

   Soporta hash: /blog#exterior abre el blog con esa categoría ya
   filtrada, así una landing puede linkear directo a su categoría.
========================================================= */

(function () {
  "use strict";

  const filters = Array.from(document.querySelectorAll(".blog-filter"));
  if (!filters.length) return;

  const cards = Array.from(document.querySelectorAll(".blog-card"));
  const featured = document.querySelector("[data-blog-featured]");
  const empty = document.querySelector("[data-blog-empty]");

  function apply(category) {
    let visible = 0;

    cards.forEach(function (card) {
      const match = category === "all" || card.dataset.category === category;
      card.hidden = !match;
      if (match) visible++;
    });

    if (featured) {
      const match = category === "all" || featured.dataset.category === category;
      featured.hidden = !match;
      if (match) visible++;
    }

    if (empty) empty.hidden = visible > 0;

    filters.forEach(function (btn) {
      const active = btn.dataset.filter === category;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const category = btn.dataset.filter || "all";
      apply(category);

      // Deja la categoría en la URL sin recargar ni saltar el scroll.
      const url = category === "all"
        ? location.pathname + location.search
        : location.pathname + location.search + "#" + category;
      history.replaceState(null, "", url);
    });
  });

  // Categoría inicial desde el hash (si existe y es una de las nuestras).
  const fromHash = location.hash.replace("#", "");
  const known = filters.some(function (b) { return b.dataset.filter === fromHash; });
  apply(known ? fromHash : "all");
})();
