# Service Areas Atlas — isolated prototype

This directory contains the framework-free source and isolated preview for the Perma Painting service-area atlas. The same data and JavaScript are loaded by `service-areas.html`, the home page and About Us; `index.html` remains the standalone preview.

## Geographic criterion

- **Northern Rivers** is treated as the macro-region.
- The six named areas in the website navigation are represented as **editorial service clusters**, not as invented administrative polygons.
- Every coloured map shape is an official NSW suburb/locality boundary.
- Local names that are not official bounded localities remain visible as aliases:
  - Salt Village → Casuarina
  - Sunrise, Byron Bay → Byron Bay
  - Belongil → Byron Bay
- `Skinners Head` was normalised to the official locality spelling `Skennars Head`. `Skinners Shoot` is a different official locality and remains unchanged.

The current dataset has 45 display names, 42 distinct official boundaries, and 6 service clusters.

The directory uses an accordion: only the six service zones are visible initially. Opening a zone reveals its localities; searching also opens the matching zone automatically.

The isolated page deliberately contains only the grey map and a compact searchable zone directory floating inside its bottom-right corner. Every zone and locality uses the same Perma green (`#3c5b49`) when active.

## Files

- `index.html` — minimal standalone component markup: search, zone directory and map.
- `service-areas-atlas.css` — all prototype/component styles.
- `service-areas-atlas.js` — MapLibre setup, Australia-to-Northern-Rivers journey, geographic layers, hover/focus, search and filtering.
- `assets/service-areas-data.js` — generated locality data; works from `file://` without `fetch`.
- `build-data.mjs` — rebuilds the data file from NSW Spatial Services.

## Preview

Open `index.html` directly, or serve the repository root and visit:

```text
/prototypes/service-areas-atlas/
```

The locality geometry is local. An internet connection is still required for MapLibre, the CARTO basemap and the web fonts, matching the dependency model of the original map component.

## Data source

NSW Spatial Services, **NSW Administrative Boundaries Theme / Suburb layer**. Geometry is requested in WGS84 and simplified to approximately 45 metres for an interface-sized reference map. The shapes are reference data; they do not promise service at every address.

To refresh the generated data:

```sh
node prototypes/service-areas-atlas/build-data.mjs
```
