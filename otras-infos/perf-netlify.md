# Performance post render-blocking

Medicion local tomada el 2 de julio de 2026 sobre `http://127.0.0.1:8000` con Lighthouse CLI en modo mobile.

## Referencia externa

- PageSpeed Insights mobile (lab) reportado antes de estos cambios: `56`.
- Esa referencia corresponde al deploy y es la que vale para el cierre final.

## Resultados locales despues de esta pasada

| Pagina | Performance local | Delta vs 56 | LCP | TBT | Speed Index |
|---|---:|---:|---:|---:|---:|
| `/index.html` | 83 | +27 | 4.3 s | 180 ms | 1.6 s |
| `/our-services.html` | 97 | +41 | 2.4 s | 120 ms | 1.1 s |

## Cambios incluidos en esta corrida

- GTM se difiere fuera del render inicial y sigue cargando con el contenedor `GTM-NPJJRLZB`.
- Google Fonts pasa a cargar con patron no bloqueante (`media="print"` + `onload` + `noscript`).
- Los estilos no criticos (`footer.css` y el CSS del mapa en contacto) salen del critical path.
- Las fotos de contenido below-the-fold mantienen `loading="lazy"` y suman `decoding="async"` donde faltaba.
- Los scripts al final del `body` ahora usan `defer`.
- El hero/LCP y los logos pasan a variantes mas chicas y responsivas para bajar payload inicial.
- Los iconos decorativos y de CTA ahora tienen dimensiones explicitas y nombres accesibles consistentes.

## Nota importante

- Estos numeros sirven solo como control local de tendencia.
- La validacion final hay que hacerla con un nuevo deploy en Netlify y una corrida fresca de PageSpeed Insights mobile sobre la URL publica.
