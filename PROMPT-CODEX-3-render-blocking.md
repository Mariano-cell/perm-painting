# Prompt 3 para Codex — Reducir render-blocking y carga inicial (subir el score de PageSpeed mobile)

Copiá y pegá esto en Codex.

---

Sos un asistente trabajando en **Perma Painting** (sitio estático vanilla en Netlify). Alcance **conservador**: sin frameworks, sin bundlers, sin reestructuras. Respetá `CLAUDE.md`. Trabajá en la rama `perf/optimizacion`, un commit por cambio.

**Contexto:** PageSpeed Insights mobile dio Rendimiento 56 (lab). Las imágenes ya están optimizadas (WebP + lazy + dimensiones). Lo que ahora frena el score es **render-blocking y JS de terceros en la carga inicial**, no las imágenes. Este prompt ataca eso. Aplicá los cambios que correspondan **también en los templates y scripts generadores** (`template-landing.html`, `template-area-index.html`, `contact.html`, y los `scripts/generate-*.py` / `propagate-header.py`) y **regenerá** las páginas, para que no queden desincronizadas. No edites a mano las 24 landings, los 3 índices ni las 30 `contact/<slug>`.

## Tareas (en orden de impacto)

### 1. Google Tag Manager fuera del critical path
Hoy el snippet de GTM está inline en el `<head>` y se ejecuta durante la carga inicial, bloqueando el hilo principal (es lo que más pena el score mobile).
- **Mové la inicialización de GTM para que dispare después de que la página cargue**, no en el `<head>` durante el render. La forma conservadora: envolver el snippet para que se ejecute en el evento `load` de la ventana (o tras un pequeño `setTimeout`/`requestIdleCallback`), en vez de ejecutarse sincrónicamente al parsear el `<head>`.
- **No borres GTM ni cambies el ID de contenedor** (`GTM-NPJJRLZB`). Solo cambiás *cuándo* se dispara. El tracking debe seguir funcionando.
- Aplicalo en TODAS las páginas (está en el `<head>` de todas) vía template + scripts + regenerar.
- **Verificá** que GTM siga cargando (en DevTools → Network aparece `gtm.js` después del load, no bloqueando el render).

### 2. Google Fonts sin bloquear el render
El `<link>` a `fonts.googleapis.com/css2` es render-blocking (frena el primer pintado hasta descargar el CSS de fuentes).
- Cargá la hoja de fuentes de forma **no bloqueante** con el patrón estándar: `<link rel="stylesheet" ... media="print" onload="this.media='all'">` más un `<noscript>` de fallback con el `<link>` normal.
- Mantené los `preconnect` que ya están (ayudan) y el `&display=swap`.
- No cambies qué pesos se piden (ya están acotados a `Montserrat:400..500` e `Inconsolata:200..700`).
- Aplicalo en todas las páginas vía template + scripts + regenerar.
- **Verificá** que las tipografías se sigan viendo igual y que no haya un flash raro de texto sin estilo notorio.

### 3. Lazy-load en las pocas fotos below-the-fold que quedaron sin él
En `index.html` la mayoría ya tiene lazy. Repasá y agregá `loading="lazy"` (y `decoding="async"` si no lo tienen) SOLO a las **fotos de contenido que están debajo del fold** y todavía no lo tengan — por ejemplo las portadas de servicios de la sección "our services" que estén sin lazy (`portada_residential.jpg`, `portada_commercial.jpg`, etc.).
- **NO toques**: la imagen LCP del hero (`landing_005`, tiene `fetchpriority="high"` — dejala como está, sin lazy), ni los `.svg`/`.png` de íconos y logos (son livianos, lazy-arlos no aporta y puede dar saltos).
- Revisá también las otras páginas core (`our-services.html`, `about-us.html`, las landings vía template) por fotos de contenido below-the-fold sin lazy.
- **Verificá**: al cargar el home, en Network solo se descargan las imágenes visibles; el resto al hacer scroll.

### 4. (Opcional, si es trivial y de bajo riesgo) `defer` en los scripts
Los `<script src=...>` están al final del `<body>` (bien), pero podés agregarles `defer` para que no compitan con el parseo final. Si al agregarlo algo se rompe (orden de ejecución de `main.js` vs `our-services.js`/`area-map.js`), revertí y dejalo como pendiente. No es prioritario.

## Reglas
- Un commit por tarea, mensaje claro en español.
- Tras cada cambio, verificá localmente que el sitio se ve y funciona igual (menú, hero slideshow, galería, formulario de contacto, mapa en byron-bay).
- Al terminar, corré Lighthouse local sobre `index.html` y `our-services.html` y anotá el nuevo score de Rendimiento vs el 56 anterior en `otras-infos/perf-netlify.md` (o donde venís documentando). Aclarando que la medición que vale es la de PageSpeed contra el deploy.
- Commits sugeridos:
  - `perf: diferir carga de GTM fuera del render inicial`
  - `perf: cargar Google Fonts sin bloquear el render`
  - `perf: lazy-load en fotos below-the-fold restantes`
  - (opcional) `perf: defer en scripts`

Al terminar, dejame un resumen de qué cambiaste y el antes/después del score, y recordame que tengo que pushear y volver a medir en PageSpeed.
