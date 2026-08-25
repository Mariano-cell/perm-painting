# Perma Painting — notas del proyecto

Sitio estático (HTML/CSS/JS vanilla) deployado en Netlify. Sin build step ni frameworks. Respetar esta arquitectura: no introducir frameworks, bundlers ni reestructuras grandes.

## Estado actual (24 ago 2026)

- Estrategia local publicada: **60 landings = 10 servicios × 6 zonas**, más 6 índices de zona.
- Servicios nuevos: **Epoxy Floors** y **Lead Paint Removal & Restoration**.
- Zonas activas en navegación y sitemap: Byron Bay, Ballina, Mullumbimby, Kingscliff, Tweed Heads y Lismore.
- El contenido definitivo de Ramón del 20/8 está cargado en `scripts/generate-landing-pages.py` para las 30 páginas de las zonas nuevas y los dos servicios nuevos en las seis zonas.
- `DEVOLUCION-RAMON.md` centraliza fotos, cifras y validaciones pendientes. Los assets de epoxy, lead paint, Kingscliff y el hero comercial son placeholders reutilizados del sitio hasta recibir material real.
- La migración incompleta a WebP ya no deja fallbacks rotos: el generador usa el WebP como `img src` cuando el JPG equivalente no existe.

## Demo scroll (grabación de videos para portfolio)

Existe `js/demo-scroll.js`, "desconectado" a propósito (ninguna página lo carga; NO borrarlo). Si Mariano quiere grabar un screencast del sitio, preguntarle si quiere activarlo y seguir **`MANUAL-DEMO-SCROLL.md`** (cómo conectar los botones, velocidades, gotchas de scroll-behavior/lazy images, netlify dev para ver las reviews en local, y cómo desconectar antes de deployar). Nunca deployar con los botones conectados.

## Blog (ago 2026)

Pedido de Ramón. Es un link más del nav, entre OUR SERVICES y AREAS OF SERVICE.

**URLs:** `/blog/` (índice) y `/blog/<slug>` (artículos). Viven en la carpeta `blog/`,
así que **usan rutas ABSOLUTAS** (`/css/...`, `/assets/...`), a diferencia de las
páginas de la raíz. Ojo con esto si se edita algo a mano.

**Estructura de archivos:**
- `scripts/generate-blog-pages.py` — el generador. **Los datos de los artículos viven acá**
  (lista `ARTICLES`) igual que los intros/FAQs de las landings. El docstring de arriba
  explica paso a paso cómo cargar una nota nueva.
- `template-blog-index.html` / `template-blog-article.html` — los moldes.
- `css/blog.css` — estilos propios. Las páginas del blog cargan
  `style.css + landing.css + blog.css + footer.css`: **landing.css se reusa a propósito**
  (`.landing__inner`, `.landing-area__label`, `.landing-cta`) para no duplicar reglas. El
  breadcrumb compartido vive en `style.css`, porque también lo usan las páginas core.
- `js/blog.js` — filtro por categoría, en el cliente. Las tarjetas están todas en el HTML
  (bien para SEO) y solo se esconden las que no matchean. Soporta `/blog/#exterior`.

**El índice y los artículos se generan, NO se editan a mano** (se pisan al regenerar):
```
python3 scripts/generate-blog-pages.py
python3 scripts/generate-sitemap.py
```

**Fotos:** por ahora se reusan las de `assets/photos/` según la categoría. Se referencian
en `.webp` directo (sin `<picture>` + fallback `.jpg`) porque en varias carpetas los `.jpg`
ya no existen — ver el punto de abajo.

**PROVISORIO:** los 7 artículos cargados son texto de relleno escrito internamente para ver
la sección funcionando; Ramón manda los reales. Cada uno tiene `"placeholder": True`, que
pinta un cartelito arriba del cuerpo. Al cargar el texto definitivo, **borrar ese flag**.

**Categorías** (`CATEGORIES` en el generador): Exterior, Interior, Epoxy floors, Lead paint.
Son las del mockup de Ramón y no equivalen uno a uno a los 10 servicios del sitio. Si se agrega una categoría, sumarle su color en `css/blog.css`
(`.blog-tag--<slug>`).

**Pendiente:** el footer NO tiene link al blog (sus 3 links siguen siendo ABOUT US /
OUR SERVICES / CONTACT). Como el footer se edita a mano archivo por archivo, se dejó afuera.

### Cambios colaterales al sumar el blog

- **`css/style.css`**: se agregó el delay `:nth-child(5)` de la cascada de entrada del nav
  (antes eran 4 items, ahora 5).
- **`scripts/propagate-header.py`**: `REL_PAGES` es un glob de todo `.html` de la raíz que
  tenga `<nav class="site-nav">`, así cubre las 60 landings, los 6 índices y las páginas core.
- **Generador de landings reparado (ago 2026):** si un JPG fue retirado durante la migración,
  `available_fallback()` usa el WebP equivalente tanto para medir como para el `img src`.

## SEO local — CAMBIO DE ESTRATEGIA (jun 2026)

**El cliente contrató a un marketing (Ramón) que reemplaza la estrategia anterior.** La estrategia actual es **60 landing pages = 10 servicios × 6 zonas**, con URLs planas tipo `/roof-painting-byron-bay`, generadas con un template/script único, intro, FAQ, schema y meta propios. "OUR SERVICES" y "AREAS OF SERVICE" son dropdowns globales. Esta estrategia **reemplaza** el sistema `/contact/<slug>` descrito abajo.

**SISTEMA VIEJO `/contact/<slug>` — NOINDEX (ago 2026):** Ramón detectó en Search Console que las 30 páginas estaban indexadas y le generaban a Google contenido duplicado a nivel dominio, compitiendo con las landings de servicio. Solución aplicada: `<meta name="robots" content="noindex, follow">` en las 30, inyectado por `scripts/generate-location-pages.py` (NO a mano). Las páginas siguen online y el formulario funciona igual: solo salen del índice. `follow` es a propósito, para no cortar el linking interno hacia las landings. `contact.html` NO lleva noindex.

**Ojo si se retoma:** NO bloquear `/contact/` en `robots.txt` — si Google no puede crawlear, no ve el noindex y las URLs quedan indexadas igual. La desindexación tarda semanas; se puede acelerar pidiendo "Validar corrección" en Search Console.

**PENDIENTE — qué hacer definitivamente con el sistema viejo:** el noindex es la solución mínima, no la final. Cuando se retome, decidir: borrarlo (script + 30 páginas + lógica de intercept en `main.js`) o redirigir con 301 cada `/contact/<zona>` a la página de esa zona en el servicio principal (ej. `/contact/ballina` → `/house-painters-ballina`). No dejarlo huérfano indefinidamente.

### IMPLEMENTADO (jun–ago 2026) — estrategia de 60 landings

**Estructura de archivos:**
- `template-landing.html` — molde de las 60 landings, con placeholders `{{...}}`. Se edita como HTML normal; para cambiar el diseño de TODAS las landings se toca este archivo y se regenera.
- `template-area-index.html` — molde de los 3 índices originales; las zonas nuevas usan la cáscara y parciales indicados más abajo.
- `scripts/generate-landing-pages.py` — genera las 60 landings + los 6 índices. Contiene los datos de servicios, zonas, intros, localidades cercanas, FAQ, CTA, crosslinks y schema.
- `scripts/generate-sitemap.py` — genera `sitemap.xml` + `robots.txt`.
- `scripts/propagate-header.py` — propaga el header nuevo (con dropdowns) a las páginas que NO genera el script (index, about-us, our-services, contact.html y las 30 `contact/<slug>`).
- `css/landing.css` — estilos propios de las landings/índices (las páginas viejas NO lo cargan; por eso varias reglas de home.css están copiadas acá: `.os-reveal`, `.why-perma`, `.hero__right--photo`, testimonials).
- `css/style.css` — contiene el componente global `.landing-breadcrumb`. Todas las páginas
  públicas salvo la home lo renderizan; `contact.html` es la fuente para las 30 páginas
  locales, cuyo generador suma la localidad como último nivel.
- CSS de los dropdowns del header: en `css/style.css` (lo cargan todas las páginas). JS del toggle mobile: en `js/main.js`.

**Las 60 landings + 6 índices se generan, NO se editan a mano** (se pisan al regenerar). Correr tras cambiar template o datos:
```
python3 scripts/generate-landing-pages.py
python3 scripts/generate-sitemap.py
```

**Header con dropdowns:** OUR SERVICES (10 servicios → su página en Byron Bay, la zona principal) y AREAS OF SERVICE (6 zonas → su índice). Desktop abre por hover; mobile por tap en `.site-nav__caret`. Está en todas las páginas, con rutas relativas en raíz y absolutas en `contact/` y `blog/`. La cascada `fadeDropIn` tiene 5 items de nivel superior; sumar servicios o zonas dentro de los dropdowns no requiere nuevos `:nth-child`.

**Índices por zona:** los tres originales conservan su modelo simple; Kingscliff usa el modelo `quote` y Tweed Heads/Lismore el modelo `local`. Todos enlazan los 10 servicios.

**sitemap.xml:** incluye 60 landings, 6 índices, core y blog (78 URLs con los 7 artículos actuales). NO incluye las 30 `/contact/<slug>` viejas.

**PENDIENTES DEL CLIENTE (marcados en el código como provisorios/placeholder):**
- ~~24 meta descriptions~~ → HECHO (jul 2026): cargadas en `META_DESCS` del generador con los textos de Ramón. Las 3 de los índices de zona las redactamos internamente (`AREA_META_DESCS`); si Ramón manda las suyas, reemplazar ahí.
- ~~FAQs (3 por servicio, inventadas)~~ → HECHO (ago 2026): cargadas las de Ramón (PDF "Nuevas FAQ 27_7") en `FAQS` dentro de `generate-landing-pages.py`. **Cambió la estructura del dict:** antes estaba indexado por servicio (las 3 zonas compartían preguntas, con placeholder `{zone}`); ahora la llave es `(servicio, zona)` — mismo patrón que `META_DESCS` — porque las FAQs son únicas por página. Son 74 Q/A: 3 por página salvo interior y exterior de Ballina, que tienen 4 (así las mandó Ramón; el HTML y el CSS soportan N items sin tocar nada). El mismo dict alimenta el HTML visible y el schema FAQPage, así que editar ahí los mantiene en sync.
- Fotos: por ahora las primeras 4 de cada carpeta de servicio; mismas 3 fotos por servicio en las 3 zonas (alt text cambia la zona).

### ZONAS NUEVAS (ago 2026) — cáscara + un hero por modelo

Ramón pidió sumar localidades y **manda un modelo de página distinto por zona**. Decisión de Mariano (ago 2026): **Byron Bay / Ballina / Mullumbimby quedan como están**; los modelos nuevos son solo para las zonas nuevas.

Para no repetir el `<head>` (GTM, fuentes, CSS) una vez por modelo, las zonas nuevas usan **una cáscara común + un parcial de hero**:

```
template-area-shell.html          cáscara: head, header, breadcrumb,
                                  grilla de 10 servicios, otras zonas, footer
  ├── template-area-hero-quote.html   modelo "quote"  → Kingscliff
  └── template-area-hero-local.html   modelo "local"  → Tweed Heads, Lismore
```

| modelo | zonas | qué tiene el hero |
|---|---|---|
| `quote` | Kingscliff | texto + pills + 3 trust badges + **formulario sticky** + foto de la zona |
| `local` | Tweed Heads, Lismore | texto + pills + **badge de trabajos** + bloque **"Local knowledge"** + **FAQ de la zona** |

`template-area-index.html` (las 3 zonas viejas) **no se tocó**: sigue siendo un archivo completo aparte.

**Para sumar un modelo nuevo:** un `template-area-hero-<modelo>.html` más, su entrada en `AREA_HERO_TEMPLATES` y su rama en `generate_new_area_indexes()`. La cáscara no se toca.

**OJO con los `{{...}}` en los comentarios de los templates:** el reemplazo es un `str.replace()` global, así que si un comentario menciona un placeholder también se reemplaza. Ya pasó una vez (el hero terminaba inyectado dentro de un comentario). El generador aborta si queda algún `{{` sin resolver.

**Las landings de servicio son idénticas** en todas las zonas (mismo `template-landing.html`, misma función `render_landing()`); lo único que cambia es de qué lista sale la zona.

**Por qué `NEW_ZONES` está separado de `ZONES`:** mantiene separados los modelos y evita cambiar automáticamente los crosslinks de las 30 landings de las zonas originales. Las seis zonas ya están publicadas en navegación y sitemap sin unificar ambas listas. La cascada `fadeDropIn` corresponde a los 5 items de nivel superior del nav.

**Funciones del generador (`scripts/generate-landing-pages.py`):**
- `render_landing()` — arma una landing de servicio (la usan las viejas y las nuevas).
- `generate_new_zone_landings()` — las 10 landings de cada zona nueva.
- `generate_new_area_indexes()` — el índice de cada zona nueva (elige el hero por `model`).

**Datos** (todo en `NEW_ZONE_DATA`, con `"model"` como primera clave): title, meta, headline, intro, `nearby` + lo propio del modelo (`trust`/`photo` para quote; `jobs_badge`/`local_knowledge`/`faqs` para local). Los intros/metas/FAQ definitivos entregados el 20/8 se cargan con `.update()` sobre `INTROS` / `META_DESCS` / `FAQS`.

**Formulario (modelo quote):** usa `name="contact"` (el mismo form de Netlify que ya recibe notificaciones) con campos nuevos `suburb`, `service` y `phone-or-email`, más un hidden `source` con la zona para saber de qué página vino. Si se separa en un form propio (`name="quote"`), **hay que darle de alta las notificaciones en Netlify** o se pierden los leads.

**CSS:** bloques `.area-quote__*` y `.area-local__*` al final de `css/landing.css`. Reusan `.area-index` (wrapper y título), `.landing-area__pills`, `.landing-links`, `.area-index__zone-btn` y — en el modelo local — el componente `.landing-faq` completo. Mobile: una columna; en quote el formulario va **antes** de la foto.

**PENDIENTES de las zonas nuevas:**
- **Kingscliff:** la foto `assets/photos/area-index/kingscliff.jpg` + `.webp` sigue siendo placeholder. Confirmar además la diferencia entre las cuatro pills nuevas y la FAQ que menciona Bogangar/Pottsville.
- **Tweed Heads y Lismore:** falta confirmar el número real de trabajos para `jobs_badge`; sin dato el badge no se renderiza.
- **`jobs_badge` está en `None` en las dos zonas `local`** porque no tenemos el número real de trabajos hechos ahí. Sin dato el badge no se renderiza: no se inventa la cifra. Los croquis decían 25+ (Tweed Heads) y 30+ (Lismore); cargar el número verdadero y regenerar.
- **Los testimonios de los croquis no se publicaron** ("Strata Committee Member — Tweed Heads", "Homeowner — South Lismore"): decisión de Mariano, no se publica un testimonio que no sea real. Si llegan reviews reales de esas zonas, el lugar natural es el widget de reviews que ya usan las landings, no un texto hardcodeado.
- **Title de Lismore:** el croquis decía "House Painters Lismore | Perma Painting", que chocaría con el `<title>` de `house-painters-lismore.html`. El índice usa "Painters Lismore", igual que las otras dos zonas nuevas.
- Las tres zonas nuevas ya están en el dropdown "AREAS OF SERVICE" y en `sitemap.xml`.

### Assets temporales pendientes de reemplazo

1. **`assets/photos/commercial/commercial-hero.*`** existe en JPG/WebP y evita el hero roto, pero es una copia temporal de `commercial_001`; reemplazar por la foto real cuando llegue.
2. **Migración a WebP resuelta en el generador:** los JPG retirados no se restauraron; cuando faltan, el WebP equivalente se usa como fallback real. No volver a generar HTML que apunte a JPG inexistentes.

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

### 404 de `/about.html` — arreglado (ago 2026)

Search Console reportaba un 404 en `/about.html`. Origen: el bloque `site-footer__mobile-links` (footer mobile) linkeaba a `about.html`, archivo que nunca existió — el real es `about-us.html`. Estaba en `index.html`, `our-services.html`, `contact.html` y, por herencia, en las 30 `contact/<slug>`. Arreglado en los 3 archivos fuente + regeneración de las 30. Se sumó además un 301 `/about.html` → `/about-us.html` en `netlify.toml` para backlinks externos.

**El footer NO tiene script propagador** (a diferencia del header, que usa `propagate-header.py`): se edita a mano en cada archivo. Si se toca un link del footer, revisar página por página con `grep -rn`.

### Otras notas

- El dominio canónico es `https://permapainting.com.au` (SIN www — verificado jul 2026: el sitio vive sin www y Netlify redirige www → apex con 301). `DOMAIN` está definido en los 3 scripts (`generate-landing-pages.py`, `generate-sitemap.py`, `generate-location-pages.py`); mantenerlos consistentes. Las páginas core (index, about-us, our-services, contact) tienen canonical propio hardcodeado en su HTML. Las 30 `contact/<slug>` tenían canonical con www; al regenerarlas (ago 2026, por el noindex) quedaron alineadas al apex y de paso se sincronizaron con `contact.html` en el snippet de GTM y el `width/height` del logo de NSW Fair Trading.
- La slugificación vive duplicada: en `slugify()` de `main.js` y en `slugify()` del script generador. Deben mantenerse idénticas (minúsculas, no-alfanuméricos → `-`).
