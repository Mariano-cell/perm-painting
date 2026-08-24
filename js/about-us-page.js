window.addEventListener("load", () => {
  document.body.classList.add("is-loaded");
});

/* =========================================================
   GALERIA ABOUT-US — rotacion de fotos con mascara vertical
   ---------------------------------------------------------
   La "mascara invisible" es un clip-path inset() aplicado al
   contenedor de cada foto (.about-page__img-container):

     1) sube tapando la foto actual   (bottom 0% -> 100%)
     2) con la foto ya tapada, se cambia la imagen
     3) baja destapando la nueva      (bottom 100% -> 0%)

   Regla de oro: la foto que entra tiene que estar DESCARGADA Y
   DECODIFICADA antes de que la mascara se mueva. Si no, la mascara
   destapa un hueco vacio — y destapar un hueco vacio no se ve, asi
   que el efecto se percibe como un corte seco.

   MASK_MS tiene que coincidir con la duracion de la transition
   definida en css/about-us.css.
   ========================================================= */
(() => {
  "use strict";

  const BASE = "assets/photos/about-us-photos/";

  /* Catalogo de fotos. Las llaves 1..6 son las "fotos" de las instancias.
     Para cambiar una: dejar el archivo en la carpeta y actualizar webp/src/alt. */
  const PHOTOS = {
    1: { webp: BASE + "team_008.webp", src: BASE + "team_008.jpeg", alt: "Perma Painting team on site" },
    2: { webp: BASE + "team_007.webp", src: BASE + "team_007.jpg",  alt: "Painter preparing a surface" },
    3: { webp: BASE + "team_001.webp", src: BASE + "team_001.jpg",  alt: "Perma Painting crew at work" },
    4: { webp: BASE + "team_002.webp", src: BASE + "team_002.jpg",  alt: "Freshly painted home exterior" },
    5: { webp: BASE + "team_009.webp", src: BASE + "team_009.jpg",  alt: "Perma Painting painter finishing timber cabinetry" },
    6: { webp: BASE + "team_010.webp", src: BASE + "team_010.jpg",  alt: "Perma Painting painter rolling a red feature wall" }
  };

  /* Cada fila es una "instancia": que foto va en cada una de las 4 columnas.
     De una fila a la siguiente cambian 2 columnas, alternando (1 y 3) / (2 y 4).
     Se puede editar libremente: el script detecta solo cuales cambian.

     Ya no hay restriccion de que foto puede ir en que columna: cada columna
     toma el ratio real de su foto, asi que nunca se recorta nada. */
  const FRAMES = [
    [1, 2, 3, 4],
    [5, 2, 6, 4],
    [5, 3, 6, 1],
    [2, 3, 4, 1],
    [2, 5, 4, 6],
    [3, 5, 1, 6],
    [3, 2, 1, 4]
  ];

  const MASK_MS    = 620;   // duracion de la mascara (igual que el CSS)
  const STAGGER_MS = 250;   // desfase entre las dos columnas que cambian
  const HOLD_MS    = 4200;  // cuanto queda quieta cada instancia

  const viewport = document.querySelector('[data-gallery="about-2up"]');
  if (!viewport) return;

  const figures = Array.from(viewport.querySelectorAll("figure"));
  if (figures.length !== FRAMES[0].length) return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const wait      = (ms) => new Promise((r) => setTimeout(r, ms));
  /* dos rAF = garantia de que el navegador ya pinto un fotograma */
  const nextPaint = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));

  /* Elegimos formato UNA sola vez y descargamos solo ese archivo.
     (Antes se precargaban webp + jpg de las 6: 4.4 MB para mostrar 760 KB.) */
  const supportsWebp = (() => {
    try {
      const c = document.createElement("canvas");
      return c.toDataURL("image/webp").indexOf("data:image/webp") === 0;
    } catch (e) { return false; }
  })();

  const urlOf = (photo) => (supportsWebp && photo.webp) ? photo.webp : photo.src;

  /* El <picture> con su <source> ya no hace falta: elegimos el formato aca.
     Dejarlo puesto haria que el <source> pisara cada cambio de src. */
  figures.forEach((figure, i) => {
    figure.querySelectorAll("source").forEach((s) => s.remove());
    const img = figure.querySelector("img");
    const photo = PHOTOS[FRAMES[0][i]];
    img.src = urlOf(photo);          // misma URL que ya venia del <source>: no re-descarga
    img.alt = photo.alt;
  });

  /* Cache de imagenes ya decodificadas. Guardar la promesa mantiene viva la
     referencia, asi el recolector de basura no descarta la precarga. */
  const cache = new Map();

  function preload(photo) {
    const url = urlOf(photo);
    if (!cache.has(url)) {
      const im = new Image();
      im.src = url;
      const p = (im.decode ? im.decode() : Promise.resolve())
        .catch(() => {})
        .then(() => { loadedImages.set(url, im); return im; });
      cache.set(url, p);
    }
    return cache.get(url);
  }

  /* Las imagenes ya precargadas quedan tambien en un mapa sincronico,
     para poder leer sus medidas sin volver a esperar una promesa. */
  const loadedImages = new Map();
  const cacheSync = (photo) => loadedImages.get(urlOf(photo));

  /* La columna adopta el ratio exacto de su foto: por eso no se recorta nada.
     Como la <figure> tiene altura fija, cambiarlo no mueve el resto de la pagina. */
  function fitToPhoto(box, im) {
    if (im && im.naturalWidth && im.naturalHeight) {
      box.style.aspectRatio = im.naturalWidth + " / " + im.naturalHeight;
    }
  }

  async function swapSlot(index, photo) {
    const figure = figures[index];
    const box    = figure.querySelector(".about-page__img-container");
    const img    = figure.querySelector("img");
    if (!box || !img) return;

    // 0) la foto que entra tiene que estar lista ANTES de mover la mascara
    const ready = await preload(photo);

    // 1) la mascara sube y tapa la foto actual
    box.classList.add("is-masked");
    await wait(MASK_MS);

    // 2) foto tapada: se cambia la imagen y la columna toma su ratio.
    //    Con la mascara cerrada el cambio de alto es invisible.
    img.src = ready.src;
    img.alt = photo.alt;
    if (ready.naturalWidth) {
      img.width  = ready.naturalWidth;
      img.height = ready.naturalHeight;
    }
    fitToPhoto(box, ready);
    if (img.decode) { try { await img.decode(); } catch (e) {} }
    await nextPaint();

    // 3) la mascara baja y descubre la nueva de arriba hacia abajo
    box.classList.remove("is-masked");
    await wait(MASK_MS);
  }

  /* La rotacion solo corre en la grilla de 4 columnas. En 2 o 1 columna
     cada figure sigue el alto de su foto, asi que rotar moveria todo lo que
     esta debajo en pleno scroll (mal CLS, y en un telefono se nota mucho). */
  const wideLayout = window.matchMedia("(min-width: 769px)");

  let frame        = 0;
  let onScreen     = false;
  let isWide       = wideLayout.matches;
  let photosReady  = false;
  let busy         = false;
  let timer        = null;

  function schedule() {
    clearTimeout(timer);
    if (!onScreen || !isWide || !photosReady || busy) return;
    timer = setTimeout(run, HOLD_MS);
  }

  async function run() {
    if (!onScreen || !isWide || busy) return;
    busy = true;

    const current = FRAMES[frame];
    const next    = FRAMES[(frame + 1) % FRAMES.length];
    const changed = current
      .map((photoId, i) => (photoId !== next[i] ? i : -1))
      .filter((i) => i !== -1);

    /* Si una columna recibe justo la foto que otra esta soltando, el desfase
       las dejaria un instante con la misma imagen: en ese caso van juntas. */
    const swapsPhoto = changed.some((i) =>
      changed.some((j) => j !== i && next[i] === current[j])
    );
    const stagger = swapsPhoto ? 0 : STAGGER_MS;

    await Promise.all(
      changed.map(async (slotIndex, order) => {
        await wait(order * stagger);
        await swapSlot(slotIndex, PHOTOS[next[slotIndex]]);
      })
    );

    frame = (frame + 1) % FRAMES.length;
    busy  = false;
    schedule();
  }

  /* No arrancamos hasta tener las 6 fotos descargadas y decodificadas.
     Recien ahi conocemos las medidas reales y podemos fijar la altura de
     la fila (la foto mas alta) y el ratio inicial de cada columna.
     En mobile no se llama nunca: seria bajar dos fotos que no se usan. */
  let preloadStarted = false;

  function ensurePreload() {
    if (preloadStarted || !isWide) return;
    preloadStarted = true;

    Promise.all(Object.keys(PHOTOS).map((k) => preload(PHOTOS[k]))).then((loaded) => {
      const ratio = (im) => im.naturalWidth / im.naturalHeight;
      const tallest = loaded
        .filter((im) => im && im.naturalWidth && im.naturalHeight)
        .reduce((a, b) => (!a || ratio(b) < ratio(a) ? b : a), null);

      if (tallest) {
        viewport.style.setProperty(
          "--gallery-tallest",
          tallest.naturalWidth + " / " + tallest.naturalHeight
        );
      }

      figures.forEach((figure, i) => {
        const box = figure.querySelector(".about-page__img-container");
        if (box) fitToPhoto(box, cacheSync(PHOTOS[FRAMES[0][i]]));
      });

      photosReady = true;
      schedule();
    });
  }

  function setOnScreen(value) {
    onScreen = value;
    if (value) { ensurePreload(); schedule(); } else clearTimeout(timer);
  }

  wideLayout.addEventListener("change", (e) => {
    isWide = e.matches;
    if (isWide) { ensurePreload(); schedule(); } else clearTimeout(timer);
  });

  if ("IntersectionObserver" in window) {
    new IntersectionObserver((entries) => {
      entries.forEach((e) => setOnScreen(e.isIntersecting));
    }, { threshold: 0.25 }).observe(viewport);
  } else {
    setOnScreen(true);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) setOnScreen(false);
    else setOnScreen(viewport.getBoundingClientRect().top < window.innerHeight);
  });
})();
