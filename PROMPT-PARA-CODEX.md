# Prompt para Codex

Copiá y pegá esto en Codex. Está pensado para ejecutarse paso a paso, con pausa para revisión humana entre pasos.

---

Sos un asistente trabajando en **Perma Painting**, un sitio estático (HTML/CSS/JS vanilla) deployado en Netlify, sin build step ni frameworks. Tu tarea es **optimizar la performance de carga** (Core Web Vitals) con un alcance **conservador**: NO introduzcas frameworks, bundlers ni reestructuras. Respetá `CLAUDE.md`.

Hay un documento `OPTIMIZACION-PERFORMANCE.md` en la raíz con la estrategia completa en pasos. Seguilo en orden. Reglas obligatorias:

**Arquitectura (no romper):**
- Sitio estático vanilla. Nada de npm/webpack/vite en el sitio. Scripts Python sueltos para tareas one-off están permitidos (ya hay precedente en `scripts/`).
- Las 24 landing pages, los 3 índices de zona y las 30 páginas `contact/<slug>` se **GENERAN con scripts, no se editan a mano**. Si un cambio las afecta, modificá el **template** o el **script generador** y **regenerá**:
  - Landings/índices: `template-landing.html`, `template-area-index.html`, `scripts/generate-landing-pages.py` → `python3 scripts/generate-landing-pages.py`
  - Contact slugs: `contact.html` + `scripts/generate-location-pages.py` → `python3 scripts/generate-location-pages.py`
  - Header de páginas no generadas: `scripts/propagate-header.py`
  - Tras tocar URLs: `python3 scripts/generate-sitemap.py`
- NO borres las imágenes originales `.jpg` (sirven de fallback en `<picture>` y de backup).

**Flujo de trabajo:**
- Trabajá en la rama `perf/optimizacion`.
- **Un paso = un commit.** Mensaje claro en español. Mariano revisa el diff entre pasos.
- Antes de cualquier acción destructiva (borrar carpetas/archivos), **PARÁ y preguntá**.
- Tras cambios de imágenes o CSS, verificá visualmente abriendo el sitio localmente y revisando que no haya 404 ni regresiones.

**Pasos (resumen — el detalle está en `OPTIMIZACION-PERFORMANCE.md`):**

0. **Baseline:** creá la rama. Corré Lighthouse sobre `index.html`, `roof-painting-byron-bay.html` y `our-services.html`. Guardá los números (Performance, LCP, CLS, transfer total) en `otras-infos/baseline-perf.md`.

1. **Quitar del deploy lo que no se usa:** `fotos-nuevas/` (370 MB) y `otras-infos/` (31 MB) NO se referencian en ningún `.html`/`.css`/`.js`, pero se publican igual. **PREGUNTÁ a Mariano** si tiene backup local antes de borrarlas del repo. No las borres sin confirmación.

2. **Limpiar `.DS_Store`:** hay 28 `.DS_Store` trackeados en git pese al `.gitignore`. Destrackealos con `git rm --cached` (no los borres del disco). Verificá: `git ls-files | grep -c DS_Store` → `0`.

3. **Arreglar imagen rota:** `css/style.css:135` referencia `../assets/photos/IMG_1522.JPG` que NO existe (404 en todas las páginas). Identificá el elemento, reemplazá por una imagen existente o quitá la regla. Si no es obvio cuál iba, **preguntá a Mariano**.

4. **Adelgazar fuentes Google:** hoy se pide Montserrat + Inconsolata con el rango variable completo (`100..900` + itálicas). Auditá qué `font-weight` se usan realmente (`grep -rhoE "font-weight:[^;]*" css/`) y reducí la URL de Google Fonts a solo esos pesos. Aplicalo en TODAS las páginas **y en los templates/scripts generadores** (`template-landing.html`, `template-area-index.html`, `contact.html`, y donde corresponda) y regenerá. Mantené `&display=swap`.

5. **WebP con `<picture>` (mayor impacto):** escribí `scripts/optimize-images.py` (Pillow) que genere `.webp` (calidad ~80) junto a cada imagen usada en el sitio, sin borrar los `.jpg`, y sin tocar `fotos-nuevas/` ni `otras-infos/`. Convertí los `<img>` clave (hero + portadas de `our-services` + lo más pesado) a `<picture>` con `<source type="image/webp">` y fallback `<img>`. Para las landings/índices, modificá `template-landing.html` + `scripts/generate-landing-pages.py` para que emitan `<picture>` y **regenerá** (no edites las páginas a mano).

6. **Dimensiones + prioridad + lazy consistente:** agregá `width`/`height` reales a los `<img>` para reducir CLS (el CSS ya escala con `max-width`, no rompe responsive). Poné `fetchpriority="high"` en la imagen LCP del hero de `index.html` y `loading="lazy"` en todas las imágenes below-the-fold que no lo tengan. La imagen above-the-fold NO debe llevar `lazy`. Para páginas generadas: template + script + regenerar.

7. **Cache headers en Netlify:** agregá a `netlify.toml` `Cache-Control: max-age=31536000, immutable` para `/assets/*`, `/css/*`, `/js/*` (ya usan `?v=` para cache busting). HTML con cache corta / `must-revalidate`.

8. **(Opcional, posponer)** consolidar los 15 selectores CSS duplicados entre `home.css` y `landing.css`. NO lo hagas salvo que Mariano lo pida — riesgo de regresión visual, sin beneficio de performance.

9. **Verificación final:** volvé a correr Lighthouse sobre las 3 páginas del Paso 0, compará contra `baseline-perf.md`, recorré el sitio (home, landing, our-services, contact, about-us) confirmando que no hay 404 ni regresiones, y documentá el antes/después. Recién ahí Mariano hace el merge.

**Importante:** después de cada paso, hacé el commit, dejá un resumen de 2–3 líneas de qué cambiaste y cómo verificarlo, y **esperá visto bueno antes de seguir** al próximo paso.
