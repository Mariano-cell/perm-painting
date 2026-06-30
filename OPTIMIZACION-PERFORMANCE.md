# Estrategia de optimización de performance — Perma Painting

**Foco:** velocidad de carga (Core Web Vitals).
**Alcance:** conservador. Sin frameworks, sin bundlers, sin reestructuras. Respeta `CLAUDE.md`.
**Ejecuta:** Codex (tiene acceso a todos los archivos del proyecto).
**Verifica:** Mariano, paso por paso. Cada paso es una unidad atómica con su propio check.

---

## Resumen del diagnóstico (qué encontramos)

| # | Problema | Impacto | Esfuerzo |
|---|----------|---------|----------|
| A | `fotos-nuevas/` (370 MB) y `otras-infos/` (31 MB) se deployan a Netlify pero NO se usan en el sitio | Deploy lento, repo gigante | Bajo |
| B | Imágenes JPEG sin optimizar: portadas de 884 px pesan 700–950 KB; ninguna en WebP | LCP alto, mucho transfer | Medio |
| C | Hero sin `fetchpriority`/preload; falta `width`/`height` en casi todos los `<img>` | LCP + layout shift (CLS) | Bajo |
| D | Fuentes Google: Montserrat + Inconsolata con TODO el rango de pesos variables (100–900 + itálicas) | Transfer grande, render-blocking | Bajo |
| E | `css/style.css` referencia `assets/photos/IMG_1522.JPG` que NO existe → request 404 | Request fallida en todas las páginas | Trivial |
| F | 28 `.DS_Store` trackeados en git pese al `.gitignore` | Ruido, archivos basura en deploy | Trivial |
| G | `netlify.toml` sin headers de cache para assets estáticos | Cache subóptima en visitas repetidas | Bajo |
| H | `loading="lazy"` inconsistente: solo 8 de 34 `<img>` en `index.html` | Imágenes below-the-fold compiten con el render inicial | Bajo |

**Lo que ya está bien (no tocar):** `loading="lazy"` en la mayoría de páginas, MapLibre se carga diferido y falla en silencio, `preconnect` a Google Fonts ya presente, versionado de assets con `?v=2`.

---

## Principios para Codex

1. **No romper la arquitectura.** Sitio estático vanilla. Nada de npm/webpack/vite en el sitio. Scripts Python sueltos para tareas one-off están OK (ya hay precedente en `scripts/`).
2. **Las 24 landings + 3 índices + 30 `contact/<slug>` se GENERAN, no se editan a mano.** Si un cambio las afecta, se toca el **template** o el **script generador** y se **regenera**. Editar el HTML generado a mano se pierde al regenerar.
   - Landings/índices: `template-landing.html`, `template-area-index.html`, `scripts/generate-landing-pages.py`
   - Contact slugs: `contact.html` (fuente) + `scripts/generate-location-pages.py`
   - Header en páginas no generadas: `scripts/propagate-header.py`
3. **Conservar las imágenes originales.** Al generar WebP/versiones optimizadas, NO borrar los JPG originales (sirven de fallback en `<picture>` y backup).
4. **Un paso = un commit.** Para que Mariano pueda revisar el diff y revertir si algo sale mal.
5. **Verificar visualmente.** Tras cambios de imágenes/CSS, abrir el sitio localmente y confirmar que nada se rompió.

---

## Pasos verificables

### PASO 0 — Baseline y rama de trabajo
**Hacer:**
- Crear rama `perf/optimizacion`.
- Correr Lighthouse (o PageSpeed Insights) sobre `index.html`, una landing (`roof-painting-byron-bay.html`) y `our-services.html`. Guardar los números de Performance, LCP, CLS y total transfer en un archivo `otras-infos/baseline-perf.md`.

**Verificación de Mariano:** existe `otras-infos/baseline-perf.md` con 3 mediciones. Anotá los números — los vas a comparar al final.

---

### PASO 1 — Sacar del deploy lo que no se usa (impacto grande, riesgo cero)
**Contexto:** `fotos-nuevas/` (370 MB) y `otras-infos/` (31 MB) no se referencian en ningún `.html`/`.css`/`.js`. Hoy se publican a Netlify igual.

**Hacer:** agregar a `netlify.toml` la exclusión de esas carpetas del publish, O moverlas fuera de la carpeta publicada. La forma conservadora con Netlify es ignorarlas en el deploy sin borrarlas del repo. Opción recomendada: agregar un `.gitignore`-style con Netlify ignore, o (más simple y explícito) mover `fotos-nuevas/` y `otras-infos/` a una carpeta hermana fuera del root publicado NO es posible si `publish = "."`. Por lo tanto:
- Mantener `publish = "."` pero **borrar del repo** `fotos-nuevas/` y `otras-infos/` (son material de trabajo, no del sitio), tras confirmar con Mariano que tiene backup local.
- **ALTERNATIVA sin borrar:** mover ambas carpetas a una subcarpeta `_no-deploy/` y configurar Netlify para ignorarla. (Netlify no excluye fácil por glob en publish="."; lo más limpio es no tenerlas en el repo.)

**⚠️ Decisión de Mariano requerida:** ¿borrar `fotos-nuevas/` y `otras-infos/` del repo (tenés backup) o preferís otra estrategia? Codex debe PREGUNTAR antes de borrar.

**Verificación:** tras el cambio, el tamaño del repo publicado baja de ~400 MB a ~70 MB. `git ls-files | grep -E "fotos-nuevas|otras-infos"` no devuelve nada (si se eligió borrar).

---

### PASO 2 — Limpiar `.DS_Store` trackeados
**Hacer:** `git rm --cached` de los 28 `.DS_Store` trackeados (ya están en `.gitignore`, solo falta destrackearlos). No se borran del disco de Mariano, solo del repo.

**Verificación:** `git ls-files | grep -c DS_Store` devuelve `0`.

---

### PASO 3 — Arreglar la imagen rota en CSS (trivial, alta prioridad)
**Contexto:** `css/style.css:135` hace `background-image: url("../assets/photos/IMG_1522.JPG")` y ese archivo NO existe → 404 en TODAS las páginas que cargan `style.css` (o sea, todas).

**Hacer:** identificar qué elemento usa esa regla. Reemplazar por una imagen existente equivalente o eliminar la regla si el fondo ya no se necesita. **Preguntar a Mariano** qué imagen iba ahí si no es obvio por el contexto.

**Verificación:** en DevTools → Network, recargar cualquier página, no aparece ningún 404 de `IMG_1522.JPG`. El diseño de la sección afectada sigue correcto.

---

### PASO 4 — Adelgazar las fuentes de Google
**Contexto:** hoy se piden Montserrat e Inconsolata con el rango variable completo (`100..900` + itálicas). Eso descarga muchísimo más de lo que el sitio usa.

**Hacer:**
- Auditar qué `font-weight` se usan realmente en los CSS (`grep -rhoE "font-weight:[^;]*" css/`).
- Reducir la URL de Google Fonts a solo los pesos usados (ej. `Montserrat:wght@400;600;700` en vez del rango completo). Si Inconsolata se usa poco, considerar limitarla igual.
- Agregar `&display=swap` ya está presente — mantener.
- Aplicar el mismo cambio en TODAS las páginas. Como el `<head>` se repite, verificar si conviene un reemplazo masivo (sed) o si los templates/scripts generadores también deben actualizarse para que las páginas generadas hereden el cambio. **Importante:** actualizar `template-landing.html`, `template-area-index.html`, `contact.html` y los scripts, no solo el HTML ya generado.

**Verificación:** el sitio se ve igual (mismas tipografías visibles). En Network, la descarga de fuentes baja. Comparar peso del CSS de fuentes antes/después.

---

### PASO 5 — Optimizar imágenes a WebP con `<picture>` (el cambio de mayor impacto)
**Contexto:** las portadas/hero son el grueso del transfer. 884 px = 700–950 KB es compresión floja. WebP suele bajar 60–80% sin pérdida visible.

**Hacer:**
1. Escribir un script Python one-off en `scripts/optimize-images.py` (usa Pillow) que, para cada imagen usada en el sitio:
   - genere una versión `.webp` (calidad ~80) junto al original, sin borrar el `.jpg`.
   - opcionalmente recomprima el JPG a calidad ~80 si está claramente sobredimensionado en peso.
   - NO procese `fotos-nuevas/` ni `otras-infos/`.
2. Cambiar los `<img>` clave (hero + portadas de `our-services`, lo above-the-fold y lo más pesado) a `<picture>` con fuente WebP y fallback JPG:
   ```html
   <picture>
     <source srcset="assets/.../portada_interior.webp" type="image/webp">
     <img src="assets/.../portada_interior.jpg" alt="..." width="884" height="1174" loading="lazy">
   </picture>
   ```
3. **Las imágenes de las landings/índices se inyectan vía script generador** → modificar `template-landing.html` y `scripts/generate-landing-pages.py` para que emitan `<picture>`, y **regenerar**. No editar las 24 landings a mano.

**Verificación:** las imágenes se ven idénticas. En Network, los assets de imagen pesan mucho menos. El LCP de `index.html` baja respecto al baseline del Paso 0.

---

### PASO 6 — `width`/`height` explícitos + `fetchpriority` en el hero + lazy consistente
**Contexto:** casi ningún `<img>` tiene `width`/`height` → causa layout shift (CLS). El hero no se prioriza. Lazy-load inconsistente.

**Hacer:**
- Agregar `width` y `height` (los reales en px, los tenemos en el diagnóstico) a los `<img>` para reservar espacio y reducir CLS. El CSS ya escala con `max-width`, así que los atributos no rompen el responsive.
- Agregar `fetchpriority="high"` a la imagen LCP del hero en `index.html` (la primera visible) y `loading="lazy"` a TODAS las imágenes below-the-fold que aún no lo tengan.
- **La imagen above-the-fold NUNCA debe llevar `loading="lazy"`** (retrasaría el LCP). Revisar que el hero no lo tenga.
- Para las páginas generadas: aplicar en template + script + regenerar.

**Verificación:** CLS baja respecto al baseline. La imagen del hero carga primero. Ninguna imagen above-the-fold tiene `lazy`.

---

### PASO 7 — Headers de cache en Netlify
**Contexto:** `netlify.toml` no define cache para assets estáticos.

**Hacer:** agregar a `netlify.toml` headers `Cache-Control` de larga duración (`max-age=31536000, immutable`) para `/assets/*`, `/css/*`, `/js/*` (los CSS/JS ya usan `?v=` para bustear cache). HTML con cache corta o `must-revalidate`.

**Verificación:** tras deploy, en Network los assets responden con el header `Cache-Control` correcto. En segunda visita cargan desde cache.

---

### PASO 8 — (Opcional, mantenibilidad) consolidar CSS duplicado
**Contexto:** 15 selectores están duplicados entre `home.css` y `landing.css` (copiados a propósito porque las landings no cargan `home.css`). No es un problema de performance directo, pero es deuda.

**Hacer:** SOLO si Mariano lo pide. Mover las reglas compartidas (`.why-perma*`, `.os-reveal`, `.hero__right--photo*`) a un archivo común que ambas carguen, o dejar como está. **Riesgo de regresión visual** → no es prioridad para performance. Recomendación: **posponer**.

**Verificación:** N/A (opcional).

---

### PASO 9 — Verificación final (obligatorio)
**Hacer:**
- Volver a correr Lighthouse sobre las mismas 3 páginas del Paso 0.
- Comparar contra `baseline-perf.md`: Performance, LCP, CLS, total transfer.
- Recorrer el sitio (home, una landing, our-services, contact, about-us) confirmando que nada se rompió visualmente y que no hay 404 en consola.
- Documentar el antes/después en `otras-infos/baseline-perf.md`.

**Verificación de Mariano:** los números mejoraron, el sitio se ve igual o mejor, sin errores en consola. Recién ahí, merge de `perf/optimizacion` a la rama principal.

---

## Orden recomendado y dependencias

```
Paso 0 (baseline)
  ├─ Paso 1 (no-deploy)      ┐
  ├─ Paso 2 (.DS_Store)      │ independientes, rápidos, riesgo bajo
  ├─ Paso 3 (img rota)       │ → hacer primero, commits chicos
  ├─ Paso 4 (fuentes)        ┘
  ├─ Paso 5 (WebP)           → mayor impacto, requiere regenerar páginas
  ├─ Paso 6 (dims/priority)  → puede ir junto al 5
  └─ Paso 7 (cache headers)
Paso 8 (CSS) — opcional, posponer
Paso 9 (verificación final) — al final, siempre
```

## Qué NO hacer (límites del alcance conservador)
- No introducir frameworks, bundlers ni npm en el sitio.
- No reestructurar carpetas ni rutas.
- No tocar la lógica SEO (las 24 landings, schema, sitemap, `/contact/<slug>`) salvo lo necesario para emitir `<picture>`/atributos desde los templates.
- No editar a mano páginas generadas: tocar template/script + regenerar.
- No borrar imágenes originales JPG.
