/* ============================================================
   MAPA DE ZONA (areas-of-service) — Perma Painting
   ------------------------------------------------------------
   Mapa que se acerca a Byron Bay y marca el punto, sin sombrear
   áreas. Basemap CARTO dark-matter recoloreado a grises por JS.
   Animación "fly to" en 3 etapas (mundo -> región -> Byron Bay)
   disparada al entrar en viewport. Respeta prefers-reduced-motion.
   Al terminar: marker con pulso + label, y se habilita interacción.

   GeoJSON embebido NO se usa (sin fetch): funciona también con
   file:// al abrir el HTML directo, sin servidor.
   Se auto-inicializa SOLO si encuentra [data-area-map].
   ============================================================ */
const AreaMap = {
  MAPLIBRE_CSS: 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css',
  MAPLIBRE_JS:  'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js',
  STYLE_URL:    'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',

  CANVAS_ID: 'area-map-canvas',

  /* Etapas del vuelo: mundo -> región -> Byron Bay. [lng, lat] + zoom.
     Última etapa con zoom más bajo: se ve "desde un poco más lejos"
     para que entre el círculo de alcance completo. */
  STAGES: [
    { center: [134, -26],        zoom: 3,    hold: 700 },  // Australia
    { center: [153.4, -28.7],    zoom: 8,    speed: 0.8 }, // Northern Rivers (vuelo lento)
    { center: [153.5550, -28.6650], zoom: 8.9, speed: 0.6 }, // Byron + alrededores (vuelo lento)
  ],
  MOBILE_BREAKPOINT: 768,
  MOBILE_FINAL_ZOOM_OFFSET: -0.35,

  /* Punto a marcar (Byron Bay). Sin label: termina solo con el punto. */
  MARKER: [153.6020, -28.6470], // Byron Bay [lng, lat]

  /* Círculo de "área de alcance" que se dibuja al final.
     Centro y radio (km) elegidos para envolver Byron Bay y las
     localidades cercanas. No es un radio real/verificado. */
  REACH: { center: [153.5550, -28.6650], radiusKm: 25.5 },

  /* Paleta de grises del basemap. */
  PALETTE: {
    gray100: '#F6F6F6', gray200: '#DADADA', gray300: '#9D9D9C',
    gray400: '#575756', gray500: '#3C3C3B', black: '#1D1D1B',
  },
  WATER_COLOR: 'gray200',

  map: null,
  container: null,
  marker: null,
  sequencePlayed: false,

  init() {
    this.container = document.querySelector('[data-area-map]');
    if (!this.container) return;
    // Lazy-load: bajar MapLibre cuando el contenedor está a ~2 viewports.
    const loadObserver = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        loadObserver.disconnect();
        this.loadMapLibre();
      }
    }, { rootMargin: '0px 0px 200% 0px' });
    loadObserver.observe(this.container);
  },

  loadMapLibre() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = this.MAPLIBRE_CSS;
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = this.MAPLIBRE_JS;
    script.onload = () => this.onLibraryLoaded();
    script.onerror = () => {}; // falla en silencio: queda el gradiente
    document.head.appendChild(script);
  },

  onLibraryLoaded() {
    const stages = this.getStages();
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const start = reduced ? stages[stages.length - 1] : stages[0];

    this.map = new maplibregl.Map({
      container: this.CANVAS_ID,
      style: this.STYLE_URL,
      center: start.center,
      zoom: start.zoom,
      interactive: false,
      attributionControl: false,
    });

    this.map.on('load', () => {
      this.applyGrayscale();

      if (reduced) {
        const last = stages[stages.length - 1];
        this.map.jumpTo({ center: last.center, zoom: last.zoom });
        this.showMarker();
        this.showReach();
        this.enableInteraction();
        return;
      }
      const animObserver = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !this.sequencePlayed) {
          this.sequencePlayed = true;
          animObserver.disconnect();
          this.runSequence(stages);
        }
      }, { threshold: 0.3 });
      animObserver.observe(this.container);
    });
  },

  isMobileViewport() {
    return window.matchMedia(`(max-width: ${this.MOBILE_BREAKPOINT}px)`).matches;
  },

  getStages() {
    const stages = this.STAGES.map((stage) => ({ ...stage }));
    if (!this.isMobileViewport()) return stages;
    const lastStage = stages[stages.length - 1];
    if (lastStage) lastStage.zoom += this.MOBILE_FINAL_ZOOM_OFFSET;
    return stages;
  },

  /* Recolorea el basemap a escala de grises. */
  applyGrayscale() {
    const p = this.PALETTE;
    const water = this.WATER_COLOR ? p[this.WATER_COLOR] : p.gray100;
    const set = (id, prop, val) => { try { this.map.setPaintProperty(id, prop, val); } catch (_) {} };
    const hide = (id) => { try { this.map.setLayoutProperty(id, 'visibility', 'none'); } catch (_) {} };
    const layers = this.map.getStyle()?.layers || [];
    layers.forEach((layer) => {
      const id = (layer.id || '').toLowerCase();
      const srcLayer = (layer['source-layer'] || '').toLowerCase();

      // Ocultar por completo cualquier capa de límites administrativos
      // (estados/condados/países/suburbs) — las "figuras de tramos rectos".
      // Se filtra por id Y por source-layer 'boundary' para no dejar ninguna.
      if (/boundary|admin|border/.test(id) || srcLayer === 'boundary' || srcLayer === 'admin') {
        hide(layer.id);
        return;
      }
      if (layer.type === 'background') { set(layer.id, 'background-color', p.gray300); return; }
      if (layer.type === 'fill') {
        let fill = p.gray300;
        if (/water|ocean|sea|lake|river/.test(id)) fill = water;
        else if (id.includes('building')) fill = p.gray400;
        else if (/park|landuse|landcover|wood/.test(id)) fill = p.gray300;
        else if (id.includes('land')) fill = p.gray400;
        set(layer.id, 'fill-color', fill);
        set(layer.id, 'fill-outline-color', p.gray500);
        return;
      }
      if (layer.type === 'line') {
        // (las boundaries ya se ocultaron arriba; acá solo carreteras y demás)
        set(layer.id, 'line-color', p.gray500);
        set(layer.id, 'line-width', ['interpolate', ['linear'], ['zoom'], 0, 0.4, 10, 0.6, 14, 1.0, 18, 1.4]);
        return;
      }
      if (layer.type === 'symbol') {
        set(layer.id, 'text-color', p.black);
        set(layer.id, 'text-halo-color', p.gray200);
        set(layer.id, 'icon-color', p.gray500);
        set(layer.id, 'icon-halo-color', p.gray200);
        return;
      }
      if (layer.type === 'circle') {
        set(layer.id, 'circle-color', p.gray500);
        set(layer.id, 'circle-stroke-color', p.gray200);
        return;
      }
      if (layer.type === 'fill-extrusion') {
        set(layer.id, 'fill-extrusion-color', p.gray400);
      }
    });
  },

  runSequence(stages = this.getStages()) {
    let current = 0;
    const next = () => {
      current++;
      if (current >= stages.length) {
        // Fin: marcar el punto y, como última acción, el círculo de alcance.
        this.showMarker();
        this.showReach();
        this.enableInteraction();
        return;
      }
      const s = stages[current];
      this.map.flyTo({ center: s.center, zoom: s.zoom, speed: s.speed, essential: true });
      this.map.once('moveend', next);
    };
    setTimeout(next, stages[0].hold || 0);
  },

  /* Punto en Byron Bay (sin label). */
  showMarker() {
    if (this.marker) this.marker.remove();
    const el = document.createElement('div');
    el.className = 'area-map-marker';
    el.innerHTML = '<div class="area-map-marker__dot"></div><div class="area-map-marker__ring"></div>';
    this.marker = new maplibregl.Marker({ element: el }).setLngLat(this.MARKER).addTo(this.map);
    requestAnimationFrame(() => el.classList.add('area-map-marker--entering'));
  },

  /* Genera un polígono circular (radio en km) alrededor de un centro [lng,lat]. */
  circlePolygon(center, radiusKm, points = 64) {
    const [lng, lat] = center;
    const kmPerDegLat = 110.574;
    const kmPerDegLng = 111.320 * Math.cos(lat * Math.PI / 180);
    const coords = [];
    for (let i = 0; i <= points; i++) {
      const a = (i / points) * 2 * Math.PI;
      coords.push([
        lng + (radiusKm / kmPerDegLng) * Math.cos(a),
        lat + (radiusKm / kmPerDegLat) * Math.sin(a),
      ]);
    }
    return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [coords] } };
  },

  /* Dibuja el círculo de área de alcance con un fade de entrada. */
  showReach() {
    if (this.map.getSource('reach')) return;
    const c = '#3c5b49'; // verde primario de la marca
    this.map.addSource('reach', {
      type: 'geojson',
      data: this.circlePolygon(this.REACH.center, this.REACH.radiusKm),
    });
    this.map.addLayer({
      id: 'reach-fill',
      type: 'fill',
      source: 'reach',
      paint: { 'fill-color': c, 'fill-opacity': 0, 'fill-opacity-transition': { duration: 700 } },
    }, this.firstSymbolLayerId());
    this.map.addLayer({
      id: 'reach-line',
      type: 'line',
      source: 'reach',
      paint: {
        'line-color': c, 'line-width': 2,
        'line-opacity': 0, 'line-opacity-transition': { duration: 700 },
      },
    }, this.firstSymbolLayerId());
    // fade-in en el siguiente frame
    requestAnimationFrame(() => {
      this.map.setPaintProperty('reach-fill', 'fill-opacity', 0.12);
      this.map.setPaintProperty('reach-line', 'line-opacity', 0.9);
    });
  },

  /* Inserta el círculo debajo de las etiquetas (para que el texto se lea encima). */
  firstSymbolLayerId() {
    const layers = this.map.getStyle()?.layers || [];
    const sym = layers.find((l) => l.type === 'symbol');
    return sym ? sym.id : undefined;
  },

  enableInteraction() {
    this.map.scrollZoom.enable();
    this.map.dragPan.enable();
    this.map.touchZoomRotate.enable();
    this.map.doubleClickZoom.enable();
    this.map.keyboard.enable();
    this.addZoomControls();
  },

  addZoomControls() {
    if (this.container.querySelector('.area-map__controls')) return;
    const wrap = document.createElement('div');
    wrap.className = 'area-map__controls';
    const mkBtn = (label, aria, fn) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'area-map__btn';
      b.setAttribute('aria-label', aria);
      b.textContent = label;
      b.addEventListener('click', fn);
      return b;
    };
    wrap.appendChild(mkBtn('+', 'Zoom in', () => this.map.zoomIn()));
    wrap.appendChild(mkBtn('−', 'Zoom out', () => this.map.zoomOut()));
    this.container.appendChild(wrap);
  },
};

document.addEventListener('DOMContentLoaded', () => AreaMap.init());
