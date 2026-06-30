# Perma Painting — notas del proyecto

Sitio estático (HTML/CSS/JS vanilla) deployado en Netlify. Sin build step ni frameworks. Respetar esta arquitectura: no introducir frameworks, bundlers ni reestructuras grandes.

## SEO local — CAMBIO DE ESTRATEGIA (jun 2026)

**El cliente contrató a un marketing (Ramón) que reemplaza la estrategia anterior.** La nueva estrategia es **24 landing pages = 8 servicios × 3 zonas** (Byron Bay, Ballina, Mullumbimby), URLs planas tipo `/roof-painting-byron-bay`, generadas con un template/script único, cada una con intro única, schema markup (LocalBusiness + Service + FAQPage), FAQ, crosslinks a las otras 23, y meta title/description propios. Más: "OUR SERVICES" pasa a dropdown por servicio y se agrega "AREAS OF SERVICE" como dropdown por zona. Esta estrategia **reemplaza** el sistema `/contact/<slug>` descrito abajo.

**PENDIENTE — sistema viejo `/contact/<slug>`:** se deja SIN TOCAR por ahora (no se borra, no se redirige). Cuando se retome, decidir: borrarlo (script + 30 páginas + lógica de intercept en `main.js`) o redirigir con 301 cada `/contact/<zona>` a la página de esa zona en el servicio principal (ej. `/contact/ballina` → `/house-painters-ballina`). No dejarlo huérfano indefinidamente.

### IMPLEMENTADO (jun 2026) — estrategia nueva de 24 landings

**Estructura de archivos:**
- `template-landing.html` — molde de las 24 landings, con placeholders `{{...}}`. Se edita como HTML normal; para cambiar el diseño de TODAS las landings se toca este archivo y se regenera.
- `template-area-index.html` — molde de los 3 índices por zona.
- `scripts/generate-landing-pages.py` — genera las 24 landings + los 3 índices de zona. Contiene TODOS los datos: servicios (con su carpeta de fotos), zonas, los 24 intros, localidades cercanas por zona, FAQs (PROVISORIAS, inventadas), CTA por servicio, crosslinks automáticos y schema (BreadcrumbList + FAQPage).
- `scripts/generate-sitemap.py` — genera `sitemap.xml` + `robots.txt`.
- `scripts/propagate-header.py` — propaga el header nuevo (con dropdowns) a las páginas que NO genera el script (index, about-us, our-services, contact.html y las 30 `contact/<slug>`).
- `css/landing.css` — estilos propios de las landings/índices (las páginas viejas NO lo cargan; por eso varias reglas de home.css están copiadas acá: `.os-reveal`, `.why-perma`, `.hero__right--photo`, testimonials).
- CSS de los dropdowns del header: en `css/style.css` (lo cargan todas las páginas). JS del toggle mobile: en `js/main.js`.

**Las 24 landings + 3 índices se generan, NO se editan a mano** (se pisan al regenerar). Correr tras cambiar template o datos:
```
python3 scripts/generate-landing-pages.py
python3 scripts/generate-sitemap.py
```

**Header con dropdowns:** OUR SERVICES (8 servicios → su página en Byron Bay, la zona principal) y AREAS OF SERVICE (3 zonas → su índice). Desktop abre por hover (CSS, con un "puente" `padding-top` para no perder el hover en el hueco); mobile por tap en `.site-nav__caret` (JS). Ambos labels siguen siendo links a su página. Está en TODAS las páginas, en 2 variantes de rutas: relativa (raíz) y absoluta (contact.html + las 30 `contact/<slug>`, que viven en subcarpeta). La animación de entrada de los navlinks (`fadeDropIn`) tiene delays para 4 items; si se agrega/quita un link, ajustar los `:nth-child` en `style.css`.

**Índices por zona** (`byron-bay.html`, `ballina.html`, `mullumbimby.html`): SOLO título + links a los 8 servicios de esa zona. Sin contenido propio, a propósito, para no canibalizar las landings.

**sitemap.xml:** incluye SOLO lo nuevo + core (24 landings + 3 índices + home/about-us/our-services/contact = 31 URLs). NO incluye las 30 `/contact/<slug>` viejas, para no competir por las mismas keywords (canibalización). Las viejas no se rompen, solo no se "empujan".

**PENDIENTES DEL CLIENTE (marcados en el código como provisorios/placeholder):**
- 24 meta descriptions → placeholder `[META DESCRIPTION PENDIENTE — ...]`.
- FAQs (3 por servicio) → inventadas, en `FAQS` dentro de `generate-landing-pages.py`. Revisar/reemplazar; alimentan también el schema FAQPage.
- Fotos: por ahora las primeras 4 de cada carpeta de servicio; mismas 3 fotos por servicio en las 3 zonas (alt text cambia la zona).

---

## SEO local (estrategia ANTERIOR — descartada, ver arriba)

Implementado (jun 2026): una página estática por localidad en `contact/<slug>.html` (30 páginas), generadas con `scripts/generate-location-pages.py` a partir de `contact.html` (fuente de verdad). Cada página tiene `<title>`, meta description, canonical y h2 propios. Para reducir la uniformidad entre páginas, el generador rota variantes de texto (listas `*_VARIANTS` en el script) para title, meta, h2, el label del textarea y el título de la sección locations (este último menciona la localidad, salvo en las que contienen "Byron Bay", que usan la variante neutra para no quedar redundantes); la elección es determinística por slug (hash md5), así regenerar no cambia los textos. `main.js` NO pisa el h2/title al cargar `/contact/<slug>` (solo setea el trigger del dropdown) — ojo con reintroducir eso. Netlify sirve `/contact/<slug>` sin extensión automáticamente; slugs inexistentes dan 404 (intencional). Los 30 botones del dropdown de locations en `contact.html` son anchors `<a href="/contact/<slug>">`. `js/main.js` intercepta el click con `pushState` (no recarga, no se pierden datos del form) y `applyLocation()` actualiza h2/title/meta/canonical en el cliente.

**IMPORTANTE — regenerar las páginas:** si se modifica `contact.html` (form, footer, dropdown, lo que sea) o se agrega/quita una localidad, correr:

```
python3 scripts/generate-location-pages.py
```

Las páginas en `contact/` NO se editan a mano: se pisan al regenerar.

### Pendiente — cuando se retome la optimización SEO, hacer (o al menos analizar):

1. **`sitemap.xml`** con las 30 URLs `/contact/<slug>` para acelerar la indexación (y referenciarlo en `robots.txt`, que tampoco existe).
2. **Linkear las localidades de `about-us.html`**: hoy son `<li>` sin links; deberían apuntar a las mismas URLs `/contact/<slug>` para sumar linking interno.
3. **Párrafo único por localidad**: hoy las 30 páginas solo difieren en title/meta/h2 — diferenciación mínima, riesgo de que Google las trate como duplicadas ("doorway pages"). El upgrade: agregar contenido único por localidad (testimonios de esa zona, trabajos hechos ahí, texto específico). Eso las convierte en landing pages legítimas a ojos de Google. Implementación sugerida: un JSON/dict de contenido por slug que el script generador inyecte.

### Otras notas

- El dominio asumido en canonicals es `https://www.permapainting.com.au` (definido en `DOMAIN` dentro de `scripts/generate-location-pages.py`) — verificar que sea el dominio real en producción.
- La slugificación vive duplicada: en `slugify()` de `main.js` y en `slugify()` del script generador. Deben mantenerse idénticas (minúsculas, no-alfanuméricos → `-`).
