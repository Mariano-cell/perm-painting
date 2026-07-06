# Prompt 1 para Codex — Lighthouse contra el deploy real de Netlify

Copiá y pegá esto en Codex.

---

Sos un asistente trabajando en **Perma Painting** (sitio estático en Netlify). Las mediciones de performance que tenemos hasta ahora se hicieron con un servidor local (`python -m http.server` / `http.server` local), que **no** sirve los headers de cache de Netlify ni usa su CDN/compresión, así que los tiempos están inflados y no son comparables con producción. Quiero mediciones reales contra el deploy de Netlify.

**Objetivo:** correr Lighthouse contra la URL pública de Netlify y documentar los resultados de forma comparable con el baseline local.

**Tareas:**

1. **Confirmá la URL de producción.** Es la que sirve Netlify (dominio real `https://www.permapainting.com.au` según `CLAUDE.md`, o la URL `*.netlify.app` si el dominio custom todavía no apunta). Si tenés dudas de cuál usar, **preguntame** antes de medir. Asegurate de que el último deploy incluya los cambios de la rama `perf/optimizacion` (si esa rama todavía no se deployó, avisame — quizás convenga un deploy preview de Netlify de esa rama y medir contra esa URL).

2. **Corré Lighthouse CLI** sobre las mismas 3 páginas del baseline, en la URL de producción:
   - `/` (home)
   - `/roof-painting-byron-bay`
   - `/our-services`

   Para cada una, corré **mobile y desktop por separado** (Netlify + CDN dan números muy distintos a local, y mobile es lo que más pesa en el ranking de Google). Usá algo como:
   ```
   lighthouse <URL> --only-categories=performance --form-factor=mobile --screenEmulation.mobile --output=json --output=html --output-path=./otras-infos/lh-<pagina>-mobile
   lighthouse <URL> --only-categories=performance --preset=desktop --output=json --output=html --output-path=./otras-infos/lh-<pagina>-desktop
   ```
   Corré cada página **2–3 veces** y quedate con la mediana (Lighthouse varía bastante entre corridas; una sola medición no es confiable).

3. **Verificá los headers de cache en producción** (esto es lo que no se veía en local). Para un asset de `/assets/`, `/css/` y `/js/`, confirmá que la respuesta trae `Cache-Control: public, max-age=31536000, immutable`. Podés usar `curl -I <url-del-asset>`. Anotá si están o no.

4. **Verificá que se sirve WebP** en producción: en las 3 páginas, confirmá que las imágenes clave se descargan como `.webp` (no `.jpg`) en un navegador moderno. Reportá si alguna imagen importante sigue cargando en JPG.

5. **Documentá todo en `otras-infos/perf-netlify.md`** con una tabla comparativa:

   | Página | Form factor | Performance | LCP | CLS | Transfer | Cache OK | WebP OK |

   Y una sección de comparación **local (baseline) vs Netlify (real)**, más 3–5 observaciones. Dejá claro qué números son los que deberíamos usar de referencia de acá en adelante (los de Netlify).

6. **Commit** en la rama `perf/optimizacion`: `Medición de performance contra deploy de Netlify`. Guardá también los `.html` de Lighthouse en `otras-infos/` por si quiero abrirlos.

**No cambies código del sitio en este prompt.** Es solo medición y documentación. Si de las mediciones surge algo para arreglar, listámelo al final como recomendaciones, sin tocarlo todavía.
