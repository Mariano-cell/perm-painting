// ============================================================
// DEMO SCROLL (temporal, solo para grabar el portfolio)
// Dos botones que recargan la página y, tras las animaciones del
// hero, hacen un scroll automático hasta el final (normal o rápido).
// Para sacarlo: borrar este archivo y sus <button> + <script> en index.html
// ============================================================

(function () {
  const FLAG = "demo-scroll-speed";     // guarda la velocidad elegida
  const HERO_ANIMATION_END = 2600;      // ms: fotos hero = 0.3s delay + 2s + margen
  const SPEED_NORMAL = 220;             // px por segundo
  const SPEED_FAST = 420;               // px por segundo

  const btnNormal = document.getElementById("demo-scroll-btn");
  const btnFast = document.getElementById("demo-scroll-btn-fast");

  // --- Modo grabación: venimos de la recarga ---
  const savedSpeed = parseFloat(sessionStorage.getItem(FLAG));
  if (savedSpeed > 0) {
    sessionStorage.removeItem(FLAG);
    if (btnNormal) btnNormal.remove(); // no se muestran a sí mismos
    if (btnFast) btnFast.remove();

    const arm = () => setTimeout(() => startAutoScroll(savedSpeed), HERO_ANIMATION_END);
    if (document.readyState === "complete") {
      arm();
    } else {
      window.addEventListener("load", arm, { once: true });
    }
    return;
  }

  // --- Modo normal: los botones disparan la recarga con su velocidad ---
  function armReload(speed) {
    sessionStorage.setItem(FLAG, String(speed));
    window.scrollTo(0, 0);
    // Pequeña espera antes de recargar, para sacar el mouse de la pantalla
    setTimeout(() => location.reload(), 500);
  }

  if (btnNormal) btnNormal.addEventListener("click", () => armReload(SPEED_NORMAL));
  if (btnFast) btnFast.addEventListener("click", () => armReload(SPEED_FAST));

  function startAutoScroll(speed) {
    // El html tiene scroll-behavior:smooth (style.css); con scrollTo por frame
    // se pelean las animaciones y el scroll no avanza. Lo apagamos durante la demo.
    document.documentElement.style.scrollBehavior = "auto";

    let lastTime = null;
    let y = window.scrollY;

    function step(time) {
      if (lastTime === null) lastTime = time;
      const delta = (time - lastTime) / 1000; // segundos desde el frame anterior
      lastTime = time;

      // maxY se recalcula en cada frame: las imágenes lazy y las reviews
      // agrandan la página mientras scrolleamos, y con un valor fijo
      // el scroll quedaba corto.
      const maxY = document.documentElement.scrollHeight - window.innerHeight;

      y = Math.min(y + speed * delta, maxY);
      window.scrollTo(0, y);

      if (y < maxY) {
        requestAnimationFrame(step);
      } else {
        window.scrollTo(0, document.documentElement.scrollHeight); // asegurar el final exacto
        document.documentElement.style.scrollBehavior = ""; // restaurar
      }
    }

    requestAnimationFrame(step);
  }
})();
