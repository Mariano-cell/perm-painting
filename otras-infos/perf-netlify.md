# Performance post render-blocking

Medicion local tomada el 2 de julio de 2026 sobre `http://127.0.0.1:4173` con Lighthouse CLI en modo mobile (categoria `performance`).

## Referencia externa

- PageSpeed Insights mobile (lab) reportado antes de estos cambios: `56`.
- Esa referencia corresponde al deploy y es la que vale para el cierre final.

## Resultados locales despues de esta pasada

| Pagina | Performance local | Delta vs 56 | LCP | TBT | Speed Index |
|---|---:|---:|---:|---:|---:|
| `/index.html` | 74 | +18 | 9.4 s | 140 ms | 2.0 s |
| `/our-services.html` | 96 | +40 | 2.6 s | 110 ms | 1.1 s |

## Cambios incluidos en esta corrida

- GTM se difiere fuera del render inicial y sigue cargando con el contenedor `GTM-NPJJRLZB`.
- Google Fonts pasa a cargar con patron no bloqueante (`media="print"` + `onload` + `noscript`).
- Las fotos de contenido below-the-fold mantienen `loading="lazy"` y suman `decoding="async"` donde faltaba.
- Los scripts al final del `body` ahora usan `defer`.

## Nota importante

- Estos numeros sirven solo como control local de tendencia.
- La validacion final hay que hacerla con un nuevo deploy en Netlify y una corrida fresca de PageSpeed Insights mobile sobre la URL publica.
