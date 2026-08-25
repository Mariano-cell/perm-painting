# Plan: hub `/service-areas` + reforma del header (ago 2026)

> **ESTADO: implementado (25 ago 2026).** Los 9 pasos están hechos y la arquitectura
> quedó documentada en `CLAUDE.md`. Este archivo se conserva porque guarda el *porqué*
> de las decisiones (el análisis del plan de Codex y el trade-off del header), que en
> `CLAUDE.md` no entra. Se puede borrar cuando ya no sirva como referencia.
>
> **Falta:** validar el copy con Ramón (anotado en `DEVOLUCION-RAMON.md`) y commitear.

---

## 1. Por qué se hace esto

Ramón sumó "AREAS OF SERVICE" como dropdown de nivel superior en el header. Eso convirtió
al header en un mapa de landings: dos dropdowns (10 servicios + 6 zonas) compitiendo con
las acciones principales del sitio.

La propuesta (originada en una consulta a Codex, revisada acá) es:

- Crear una página hub `/service-areas` que centralice la navegación geográfica.
- Bajar el dropdown de 6 zonas a un **navlink simple** que apunta a ese hub.
- Sumar una sección "Where We Work" en la home, que hoy **no linkea ninguna zona**
  fuera del nav (verificado con grep sobre `index.html`).

---

## 2. Objetivos de SEO vigentes (NO romper)

Estos son los que gobiernan el proyecto. Están dispersos en `CLAUDE.md`,
`DEVOLUCION-RAMON.md` y comentarios del código; acá van juntos.

### 2.1 La estrategia de Ramón

- **60 landings = 10 servicios × 6 zonas**, más **6 índices de zona**.
- URLs **planas**: `/roof-painting-byron-bay`, `/ballina`. Sin carpetas.
- Zonas activas: Byron Bay, Ballina, Mullumbimby, Kingscliff, Tweed Heads, Lismore.
- Sitio **estático** (HTML/CSS/JS vanilla) en Netlify. Sin frameworks, sin build step.

### 2.2 El principio rector: EVITAR CANIBALIZACIÓN

Es la decisión que se repite en todo el proyecto. Cuatro precedentes concretos:

1. Las 30 páginas viejas `/contact/<localidad>` fueron a `noindex, follow` porque Search
   Console mostró que le hacían contenido duplicado a nivel dominio y competían con las
   landings de servicio.
2. `generate-sitemap.py` **excluye a propósito** esas 30 URLs.
3. Los índices de zona **no tienen contenido propio**. Comentario literal en
   `template-area-index.html`: *"solo título + links a los servicios. Sin contenido propio
   (para no canibalizar las landings)"*.
4. El `<title>` de Lismore se cambió de "House Painters Lismore" a **"Painters Lismore"**
   justamente porque chocaba con `house-painters-lismore.html`.

**Consecuencia directa para el hub:** `/service-areas` **NO** debe intentar posicionar
para "painters Ballina" ni ninguna keyword local. Se posiciona como página general de
cobertura y su función es distribuir autoridad hacia las 6 zonas.

### 2.3 Reglas duras del proyecto

- **Nada se edita a mano.** Las 60 landings, los 6 índices, el blog y las 30
  `contact/<slug>` se **generan**. Se editan el template y el script, y se regenera.
  Editar el HTML a mano se pierde en la próxima corrida.
- **No se inventan datos.** `jobs_badge` está en `None` en Tweed Heads y Lismore porque no
  se conoce el número real. Los testimonios de los croquis no se publicaron por no ser
  verificables. Mismo criterio para cualquier cifra o afirmación comercial nueva.
- **Dominio canónico: `https://permapainting.com.au`** (apex, SIN www). `DOMAIN` está
  definido en los 3 scripts generadores y deben mantenerse consistentes.
- **`ZONES` y `NEW_ZONES` van separadas a propósito.** Unificarlas regeneraría los
  crosslinks de las 30 landings de las zonas originales (`crosslinks_zones_html()` itera
  solo sobre `ZONES`). Para el hub se usa una lista derivada aparte.
- **El footer no tiene script propagador**: se edita a mano archivo por archivo. Por eso
  se evita tocarlo en este trabajo.

---

## 3. Decisiones tomadas (Mariano, 25 ago 2026)

| Tema | Decisión |
|---|---|
| **Copia de trabajo** | `~/Desktop/Programación/PERMA/perma-painting` (la que tiene `.git`). La de `~/Desktop/perma-painting` es un duplicado sin git; va a quedar desactualizada. |
| **Header** | `SERVICE AREAS` como **navlink simple** apuntando a `/service-areas`. Se elimina el dropdown de 6 zonas. **NO** se sigue a Codex, que lo bajaba a un link secundario dentro del dropdown de Our Services. |
| **`prototypes/service-areas-atlas`** | Queda **afuera**. Es un prototipo aislado de Mariano (mapa de suburbios con datos de NSW Spatial Services). Quizás se integre más adelante, pero hoy no "es" esta página. El hub v1 va sin mapa. |

### Por qué el navlink simple y no la propuesta de Codex

Codex afirmaba que su plan "conserva el valor SEO de la estructura". **No es exacto.**
Hoy los 6 índices de zona reciben un link desde cada una de las ~100 páginas del sitio.
Con su versión pasarían a recibir uno solo (desde el hub) más el de la home: ganaría el
hub, pero las zonas bajarían un nivel de profundidad.

El navlink simple mantiene un link sitewide de nivel superior hacia el hub, elimina el
dropdown (que era la queja real) y **no obliga a tocar los `:nth-child` de `fadeDropIn`
en `css/style.css`**, que están tuneados para 5 items de nav. La versión de Codex los
dejaba en 4. Codex no menciona este punto.

---

## 4. Correcciones al plan de Codex (además del header)

1. **Breadcrumb de las 6 zonas → sí se toca.** Codex decía "no tocar las 6 páginas de
   área", pero entonces el hub se declara nivel padre y ninguna zona apunta hacia arriba.
   Se cambia a `Home → Service Areas → <Zona>` en `template-area-shell.html` y
   `template-area-index.html`. Son templates: se regenera y listo. Suma 6 links entrantes
   al hub y deja la jerarquía coherente.
   **OJO:** el breadcrumb de las 60 landings **NO se toca**. Es `Home → Servicio → Zona`
   y eso es deliberado: el servicio es la keyword.
2. **El copy nuevo es provisorio.** H1, meta description y las 6 descripciones de zona son
   texto indexable nuevo sobre una estructura que diseñó Ramón. Se redactan desde material
   que ya existe (las listas `NEARBY` / `nearby` del generador) y se anotan como
   pendientes de validación en `DEVOLUCION-RAMON.md`, igual que se hizo con los intros y
   las FAQs.
3. **Punto a favor de Codex que conviene registrar:** hoy el link de nivel superior
   "AREAS OF SERVICE" apunta a `byron-bay.html`, que es arbitrario. El hub lo arregla.

---

## 5. Checklist de ejecución

- [x] **1.** `template-service-areas.html` — template nuevo del hub.
- [x] **2.** `generate_service_areas_page()` en `scripts/generate-landing-pages.py`, con
      una lista derivada propia (tipo `SERVICE_AREA_ORDER`) que **no** toca
      `ZONES` / `NEW_ZONES`.
- [x] **3.** Generar `/service-areas` y revisarlo.
- [x] **4.** Breadcrumb de las 6 zonas → `Home → Service Areas → <Zona>` y regenerar.
- [x] **5.** Sección "Where We Work" en la home (entre `our-services` y `why-perma`).
- [x] **6.** Header: `SERVICE AREAS` navlink simple + `propagate-header.py`.
      Revisar rutas relativas (raíz) vs absolutas (`/blog/`, `/contact/`).
- [x] **7.** `generate-sitemap.py`: sumar `/service-areas`.
- [x] **8.** Verificar desktop, mobile, teclado y rutas.
- [x] **9.** Actualizar `CLAUDE.md` + `DEVOLUCION-RAMON.md`.

### Comandos de regeneración

```
python3 scripts/generate-landing-pages.py
python3 scripts/generate-blog-pages.py
python3 scripts/propagate-header.py
python3 scripts/generate-sitemap.py     # correr DESPUÉS de generate-blog-pages.py
python3 scripts/validate-generated-site.py
```

---

## 6. Gotchas conocidos

- **`str.replace()` global en los templates:** si un comentario del template menciona un
  `{{PLACEHOLDER}}`, también se reemplaza. Ya pasó una vez (el hero terminó inyectado
  dentro de un comentario). El generador aborta si queda algún `{{` sin resolver.
- **Rutas:** las páginas de la raíz usan rutas **relativas**; `/blog/` y `/contact/` usan
  **absolutas**. `propagate-header.py` arma las dos variantes con un `prefix`.
- **`css/style.css`** tiene los `:nth-child(1..5)` de la cascada `fadeDropIn` del nav.
  Con el navlink simple siguen siendo 5 items: no se tocan.
- **El working tree de git estaba sucio** antes de empezar este trabajo (blog, landings,
  `css/landing.css` modificados sin commitear). Ese ruido es previo.
- **`header` y `footer` de los índices de zona** se extraen de `template-landing.html`
  con `_extract()`, para tener una sola fuente de verdad. El hub debe hacer lo mismo.
