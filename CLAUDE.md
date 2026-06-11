# Perma Painting — notas del proyecto

Sitio estático (HTML/CSS/JS vanilla) deployado en Netlify. Sin build step ni frameworks. Respetar esta arquitectura: no introducir frameworks, bundlers ni reestructuras grandes.

## SEO local (estrategia en curso)

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
