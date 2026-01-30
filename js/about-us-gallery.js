// (() => {
//     const viewport = document.querySelector('[data-gallery="taca"]');
//     if (!viewport) return;

//     // Si tu "viewport" no es el scroller, ajustá esto:
//     // - Si el scroller real es otro elemento con overflow-x, apuntalo acá.
//     const scroller = viewport;

//     const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

//     // --- Helpers ---
//     const isTypingTarget = (el) => {
//         if (!el) return false;
//         const tag = (el.tagName || "").toLowerCase();
//         return (
//             tag === "input" ||
//             tag === "textarea" ||
//             tag === "select" ||
//             el.isContentEditable
//         );
//     };

//     const isGalleryOnScreen = () => {
//         const r = viewport.getBoundingClientRect();
//         const vh = window.innerHeight || document.documentElement.clientHeight;

//         // "Visible" si el bloque cruza el viewport.
//         // (Podés endurecerlo si querés: r.top < vh*0.8 && r.bottom > vh*0.2)
//         return r.bottom > 0 && r.top < vh;
//     };

//     // Un "step" = la mitad del viewport (porque se ven 2 slides por vez)
//     let step = Math.max(1, Math.round(scroller.clientWidth / 2));

//     const recalcStep = () => {
//         step = Math.max(1, Math.round(scroller.clientWidth / 2));
//     };

//     const getIndex = () => {
//         // índice del "par" visible (0,1,2,3...) en steps
//         return Math.round(scroller.scrollLeft / step);
//     };

//     const scrollToIndex = (index, behavior = "smooth") => {
//         const target = index * step;

//         // clamp (por si no querés loop)
//         const max = scroller.scrollWidth - scroller.clientWidth;
//         const clamped = Math.max(0, Math.min(target, max));

//         scroller.scrollTo({
//             left: clamped,
//             behavior: prefersReduced ? "auto" : behavior,
//         });
//     };

//     const next = () => scrollToIndex(getIndex() + 1);
//     const prev = () => scrollToIndex(getIndex() - 1);

//     // --- Keyboard: flechas ---
//     // Nota: usamos window para que funcione aunque el usuario no "focusée" el scroller.
//     window.addEventListener("keydown", (e) => {
//         // No romper escritura en inputs
//         if (isTypingTarget(document.activeElement)) return;

//         // Solo cuando la galería está en pantalla (evita secuestrar flechas en otras secciones)
//         if (!isGalleryOnScreen()) return;

//         if (e.key === "ArrowRight") {
//             e.preventDefault();
//             next();
//         } else if (e.key === "ArrowLeft") {
//             e.preventDefault();
//             prev();
//         }
//     });

//     // --- Recalcular step si cambia el tamaño ---
//     window.addEventListener("resize", () => {
//         // preserva el índice al recalcular
//         const idx = getIndex();
//         recalcStep();
//         scrollToIndex(idx, "auto");
//     });

//     // init
//     recalcStep();
// })();
