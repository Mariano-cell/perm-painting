# Prompt 2 para Codex — Terminar la optimización de la galería de our-services

Copiá y pegá esto en Codex.

---

Sos un asistente trabajando en **Perma Painting** (sitio estático vanilla en Netlify). Alcance **conservador**: sin frameworks, sin bundlers, sin reestructuras. Respetá `CLAUDE.md`. Trabajá en la rama `perf/optimizacion`, un commit por cambio.

**Contexto:** la optimización de imágenes ya está casi completa. La galería de `our-services.html` YA sirve WebP con `<picture>` (el JS `js/our-services.js` genera un `<picture>` con `<source type="image/webp">` y fallback `<img>` — eso está bien, NO lo rehagas). Lo que falta es que esos `<img>` que crea el JS **no reservan espacio ni difieren la carga**, y hay un par de detalles finos. Esto sube el CLS y hace que se descarguen imágenes que todavía no se ven.

**Tareas (en `js/our-services.js`, en la función `renderGallery`, donde se crea el `img`):**

1. **`loading="lazy"`** en cada `<img>` de la galería, EXCEPTO las primeras 1–2 imágenes de la categoría inicial (esas son las visibles al cargar; si todas van lazy, la primera categoría tarda de más). Criterio simple y seguro: las primeras 2 imágenes del render sin lazy, el resto con `loading="lazy"`.

2. **`decoding="async"`** en todos los `<img>` de la galería (decodificación fuera del hilo principal, mejora la fluidez).

3. **`width` y `height` explícitos** en cada `<img>` para reservar espacio y bajar el CLS. Las fotos de la galería son verticales/cuadradas según carpeta; para no medir una por una, definí en el objeto de cada item (o como constante por categoría) las dimensiones reales, o usá un `width`/`height` representativo que respete el aspect-ratio con el que se muestran en el grid. Si el CSS ya fija el tamaño de `.services-projects__img` con `aspect-ratio`/`object-fit`, alcanza con poner `width`/`height` coherentes con ese ratio. Verificá en `css/our-services.css` cómo se dimensiona `.services-projects__img` antes de elegir los valores, para no romper el layout.

4. **No rompas la animación de entrada** (`is-in`, el stagger con `requestAnimationFrame`) ni el soporte de `prefers-reduced-motion` que ya existe.

**Verificación (hacela vos y dejámela documentada):**
- Abrí `our-services.html` local, cambiá entre categorías (Interior, Exterior, etc.) y confirmá que las fotos se ven, la animación funciona y no hay saltos de layout.
- En DevTools → Network, filtrando imágenes: al cargar la página, solo se descargan las primeras imágenes; el resto recién al hacer scroll. Todas en `.webp` en navegador moderno.
- En DevTools → elementos, confirmá que los `<img>` generados tienen `loading`, `decoding`, `width` y `height`.
- Corré Lighthouse local sobre `our-services.html` y confirmá que el CLS sigue en 0 y que no empeoró el LCP.

**Extra (opcional, solo si es rápido y de bajo riesgo):**
- Revisá si el hero de `index.html` (slideshow en `js/main.js`) y las imágenes below-the-fold del resto de páginas tienen `decoding="async"`. Si falta y es trivial agregarlo sin tocar la lógica, hacelo en un commit aparte. Si implica algo más que agregar el atributo, NO lo toques y listámelo como pendiente.

**Commits sugeridos:**
- `our-services: lazy-load, decoding async y dimensiones en galería`
- (opcional) `imgs: decoding async en hero y below-the-fold`

Al terminar, dejame un resumen de qué cambió y el antes/después de CLS y transfer de `our-services.html`.
