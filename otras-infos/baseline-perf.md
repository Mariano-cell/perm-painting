# Baseline de performance

Medición tomada el 30 de junio de 2026 sobre servidor local `http://127.0.0.1:4173` con `Lighthouse CLI 13.4.0` y Google Chrome.

## Resultados iniciales

| Página | Performance | LCP | CLS | Transfer total |
|---|---:|---:|---:|---:|
| `/index.html` | 74 | 15.7 s | 0.00 | 6,269 KiB |
| `/roof-painting-byron-bay.html` | 74 | 12.5 s | 0.00 | 3,819 KiB |
| `/our-services.html` | 73 | 21.9 s | 0.00 | 5,740 KiB |

## Notas

- Se auditó solo la categoría `performance`.
- Estas cifras sirven como baseline local para comparar contra la verificación final del paso 9.

## Resultados finales locales

Medición tomada el 1 de julio de 2026 sobre el mismo servidor local `http://127.0.0.1:4173` con `Lighthouse CLI 13.4.0` y Google Chrome.

| Página | Performance | LCP | CLS | Transfer total |
|---|---:|---:|---:|---:|
| `/index.html` | 68 | 10.2 s | 0.00 | 1,138 KiB |
| `/roof-painting-byron-bay.html` | 70 | 10.9 s | 0.00 | 1,486 KiB |
| `/our-services.html` | 70 | 9.6 s | 0.00 | 1,357 KiB |

## Comparación baseline vs final

| Página | Delta Performance | Delta LCP | Delta CLS | Delta transfer |
|---|---:|---:|---:|---:|
| `/index.html` | -6 | -5.5 s | 0.00 | -5,131 KiB |
| `/roof-painting-byron-bay.html` | -4 | -1.6 s | 0.00 | -2,333 KiB |
| `/our-services.html` | -3 | -12.3 s | 0.00 | -4,383 KiB |

## Observaciones finales

- La mejora más clara quedó en `LCP` y en el peso total transferido, sobre todo por el cambio a `WebP` y la priorización/carga diferida de imágenes.
- `CLS` se mantuvo en `0.00` en estas corridas locales.
- El score global de `Performance` bajó levemente en estas tres mediciones locales, aun con mejor `LCP`; Lighthouse puede variar entre corridas y pondera otras métricas además de las que estamos comparando acá.
- El `Paso 7` (headers de cache en `netlify.toml`) no se refleja en esta auditoría local porque `python3 -m http.server` no sirve los headers de Netlify. Ese beneficio se verá recién en deploy.
