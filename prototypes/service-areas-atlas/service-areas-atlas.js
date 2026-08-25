(function () {
    "use strict";

    const root = document.querySelector("[data-service-atlas]");
    const data = window.PERMA_SERVICE_AREAS;
    if (!root || !data) return;

    const STYLE_URL = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
    const AUSTRALIA_CAMERA = { center: [134, -26], zoom: 3.15, bearing: 0, pitch: 0 };
    const EAST_COAST_CAMERA = { center: [151.1, -29.4], zoom: 5.05, bearing: 0, pitch: 0 };
    const HOME_BASE = [153.602, -28.647];
    const ACTIVE_COLOR = "#3c5b49";
    const EMPTY_FILTER = ["==", ["get", "id"], "__none__"];

    const regionList = root.querySelector("[data-region-list]");
    const search = root.querySelector("[data-atlas-search]");
    const emptyState = root.querySelector("[data-empty-state]");
    const mapLoader = root.querySelector("[data-map-loader]");
    const directory = root.querySelector(".atlas-directory");

    const featureById = new Map(data.geojson.features.map((feature) => [feature.properties.id, feature]));
    const regionById = new Map(data.regions.map((region) => [region.id, region]));
    const localityButtons = [];
    const regionElements = new Map();

    let map = null;
    let mapReady = false;
    let homeMarker = null;
    let preview = null;
    let pinned = null;
    let searchQuery = "";
    let journeyRunning = false;
    let journeyToken = 0;
    let coverageCamera = null;
    const expandedRegions = new Set();

    function walkCoordinates(coordinates, visit) {
        if (typeof coordinates[0] === "number") {
            visit(coordinates);
            return;
        }
        coordinates.forEach((child) => walkCoordinates(child, visit));
    }

    function featureBounds(feature) {
        const bounds = new maplibregl.LngLatBounds();
        walkCoordinates(feature.geometry.coordinates, (coordinate) => bounds.extend(coordinate));
        return bounds;
    }

    function regionBounds(regionId) {
        const bounds = new maplibregl.LngLatBounds();
        data.geojson.features
            .filter((feature) => feature.properties.regionId === regionId)
            .forEach((feature) => walkCoordinates(feature.geometry.coordinates, (coordinate) => bounds.extend(coordinate)));
        return bounds;
    }

    function allCoverageBounds() {
        const bounds = new maplibregl.LngLatBounds();
        data.geojson.features.forEach((feature) => {
            walkCoordinates(feature.geometry.coordinates, (coordinate) => bounds.extend(coordinate));
        });
        return bounds;
    }

    function cameraPadding(compact = false) {
        const mobile = window.matchMedia("(max-width: 640px)").matches;
        if (mobile) {
            return compact
                ? { top: 46, right: 34, bottom: 260, left: 34 }
                : { top: 52, right: 34, bottom: 280, left: 34 };
        }
        return compact
            ? { top: 76, right: 380, bottom: 82, left: 76 }
            : { top: 82, right: 390, bottom: 96, left: 82 };
    }

    function initMap() {
        if (!window.maplibregl) {
            showMapError("The map library could not load. Check the internet connection and reload this prototype.");
            return;
        }

        map = new maplibregl.Map({
            container: "service-areas-map",
            style: STYLE_URL,
            center: AUSTRALIA_CAMERA.center,
            zoom: AUSTRALIA_CAMERA.zoom,
            bearing: 0,
            pitch: 0,
            interactive: true,
            attributionControl: false,
            fadeDuration: 220,
        });

        disableMapInteraction();
        map.addControl(new maplibregl.NavigationControl({ showCompass: false, visualizePitch: false }), "top-left");

        const loadTimeout = window.setTimeout(() => {
            if (!mapReady) showMapError("The grey basemap is taking too long to load. Check the internet connection and try again.");
        }, 15000);

        map.on("load", () => {
            window.clearTimeout(loadTimeout);
            applyGrayscale();
            addServiceLayers();
            bindMapEvents();
            mapReady = true;
            root.classList.add("is-map-ready");
            mapLoader.classList.add("is-hidden");

            coverageCamera = map.cameraForBounds(allCoverageBounds(), {
                padding: cameraPadding(false),
                maxZoom: 9.1,
            });

            const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            if (reducedMotion) {
                focusCoverage(0);
                finishJourney();
                return;
            }

            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    observer.disconnect();
                    runJourney();
                }
            }, { threshold: 0.25 });
            observer.observe(root.querySelector(".atlas-map-card"));
        });
    }

    function addServiceLayers() {
        map.addSource("service-localities", {
            type: "geojson",
            data: data.geojson,
        });

        const beforeId = firstSymbolLayerId();
        const color = ACTIVE_COLOR;

        map.addLayer({
            id: "service-localities-base",
            type: "fill",
            source: "service-localities",
            paint: {
                "fill-color": color,
                "fill-opacity": 0.045,
                "fill-opacity-transition": { duration: 260 },
            },
        }, beforeId);

        map.addLayer({
            id: "service-region-active",
            type: "fill",
            source: "service-localities",
            filter: EMPTY_FILTER,
            paint: {
                "fill-color": color,
                "fill-opacity": 0.24,
                "fill-opacity-transition": { duration: 280 },
            },
        }, beforeId);

        map.addLayer({
            id: "service-locality-active",
            type: "fill",
            source: "service-localities",
            filter: EMPTY_FILTER,
            paint: {
                "fill-color": color,
                "fill-opacity": 0.68,
                "fill-opacity-transition": { duration: 220 },
            },
        }, beforeId);

        map.addLayer({
            id: "service-localities-outline",
            type: "line",
            source: "service-localities",
            paint: {
                "line-color": "#575756",
                "line-width": 0.8,
                "line-opacity": 0.34,
            },
        }, beforeId);

        map.addLayer({
            id: "service-region-active-outline",
            type: "line",
            source: "service-localities",
            filter: EMPTY_FILTER,
            paint: {
                "line-color": color,
                "line-width": 2,
                "line-opacity": 0.95,
                "line-opacity-transition": { duration: 260 },
            },
        }, beforeId);

        map.addLayer({
            id: "service-locality-active-outline",
            type: "line",
            source: "service-localities",
            filter: EMPTY_FILTER,
            paint: {
                "line-color": "#f6f6f6",
                "line-width": 3,
                "line-opacity": 1,
            },
        }, beforeId);
    }

    function firstSymbolLayerId() {
        const layers = map.getStyle()?.layers || [];
        return layers.find((layer) => layer.type === "symbol")?.id;
    }

    function basemapCategory(layer) {
        const descriptor = `${layer.id || ""} ${layer["source-layer"] || ""}`.toLowerCase();

        if (/boundary|admin|border/.test(descriptor)) return "administrative-boundary";
        if (/waterway|river|stream|canal/.test(descriptor)) return "waterway";
        if (/water|ocean|sea|lake/.test(descriptor)) return "water-edge";
        if (/road|transportation|tunnel|bridge|rail|aeroway/.test(descriptor)) return "transportation";
        if (/park|landuse|landcover|wood/.test(descriptor)) return "land-detail";
        if (/building/.test(descriptor)) return "building";
        return "other";
    }

    function applyGrayscale() {
        const palette = {
            gray100: "#f6f6f6",
            gray200: "#dadada",
            gray300: "#9d9d9c",
            gray400: "#575756",
            gray500: "#3c3c3b",
            black: "#1d1d1b",
        };
        const set = (id, property, value) => {
            try { map.setPaintProperty(id, property, value); } catch (_) { /* Different basemap layer. */ }
        };
        const hide = (id) => {
            try { map.setLayoutProperty(id, "visibility", "none"); } catch (_) { /* Different basemap layer. */ }
        };

        (map.getStyle()?.layers || []).forEach((layer) => {
            const id = (layer.id || "").toLowerCase();
            const category = basemapCategory(layer);

            if (category === "administrative-boundary") {
                hide(layer.id);
                return;
            }
            if (layer.type === "background") {
                set(layer.id, "background-color", palette.gray300);
                return;
            }
            if (layer.type === "fill") {
                let fill = palette.gray300;
                if (/water|ocean|sea|lake|river/.test(id)) fill = palette.gray200;
                else if (id.includes("building")) fill = palette.gray400;
                else if (/park|landuse|landcover|wood/.test(id)) fill = palette.gray300;
                else if (id.includes("land")) fill = palette.gray400;
                set(layer.id, "fill-color", fill);
                set(layer.id, "fill-outline-color", category === "land-detail" ? fill : palette.gray500);
                return;
            }
            if (layer.type === "line") {
                set(layer.id, "line-color", palette.gray500);
                set(layer.id, "line-width", ["interpolate", ["linear"], ["zoom"], 0, 0.4, 10, 0.6, 14, 1, 18, 1.4]);
                return;
            }
            if (layer.type === "symbol") {
                set(layer.id, "text-color", palette.black);
                set(layer.id, "text-halo-color", palette.gray200);
                set(layer.id, "icon-color", palette.gray500);
                set(layer.id, "icon-halo-color", palette.gray200);
                return;
            }
            if (layer.type === "circle") {
                set(layer.id, "circle-color", palette.gray500);
                set(layer.id, "circle-stroke-color", palette.gray200);
                return;
            }
            if (layer.type === "fill-extrusion") set(layer.id, "fill-extrusion-color", palette.gray400);
        });
    }

    function disableMapInteraction() {
        if (!map) return;
        map.scrollZoom.disable();
        map.dragPan.disable();
        map.dragRotate.disable();
        map.touchZoomRotate.disable();
        map.doubleClickZoom.disable();
        map.keyboard.disable();
        map.boxZoom.disable();
    }

    function enableMapInteraction() {
        if (!map) return;
        map.scrollZoom.enable();
        map.dragPan.enable();
        map.touchZoomRotate.enable();
        map.doubleClickZoom.enable();
        map.keyboard.enable();
        map.boxZoom.enable();
    }

    function showMapError(message) {
        mapLoader.classList.add("is-hidden");
        const previous = root.querySelector(".atlas-map-error");
        if (previous) previous.remove();
        const error = document.createElement("div");
        error.className = "atlas-map-error";
        error.textContent = message;
        root.querySelector(".atlas-map-card").appendChild(error);
    }

    async function runJourney() {
        if (!mapReady) return;
        const token = ++journeyToken;
        journeyRunning = true;
        disableMapInteraction();
        clearSelectionState(true);
        map.stop();
        map.jumpTo(AUSTRALIA_CAMERA);

        await wait(1400);
        if (token !== journeyToken) return;

        if (!await flyTo(EAST_COAST_CAMERA, { speed: 0.78, curve: 1.25 }, token)) return;

        if (!await flyTo(coverageCamera, { speed: 0.68, curve: 1.35 }, token)) return;

        finishJourney();
    }

    function flyTo(camera, motion, token) {
        return new Promise((resolve) => {
            const onEnd = () => resolve(token === journeyToken);
            map.once("moveend", onEnd);
            map.flyTo({
                center: camera.center,
                zoom: camera.zoom,
                bearing: camera.bearing || 0,
                pitch: camera.pitch || 0,
                speed: motion.speed,
                curve: motion.curve,
                essential: true,
            });
        });
    }

    function finishJourney() {
        journeyRunning = false;
        showHomeMarker();
        enableMapInteraction();
        renderState();
        revealDirectory();
    }

    function revealDirectory() {
        root.classList.add("is-journey-complete");
        directory.removeAttribute("inert");
        directory.setAttribute("aria-hidden", "false");
    }

    function cancelJourney() {
        if (!journeyRunning) return;
        journeyToken += 1;
        journeyRunning = false;
        map.stop();
        enableMapInteraction();
    }

    function ensureCoverageVisible() {
        if (!mapReady) return;
        if (journeyRunning || map.getZoom() < 7) {
            cancelJourney();
            focusCoverage(600);
            showHomeMarker();
        }
    }

    function focusCoverage(duration = 850) {
        if (!mapReady || !coverageCamera) return;
        map.easeTo({
            center: coverageCamera.center,
            zoom: coverageCamera.zoom,
            bearing: 0,
            pitch: 0,
            duration,
            essential: true,
        });
    }

    function zoomToFeature(officialId) {
        if (!mapReady) return;
        const feature = featureById.get(officialId);
        if (!feature) return;
        map.fitBounds(featureBounds(feature), {
            padding: cameraPadding(true),
            maxZoom: 11.2,
            duration: 850,
            essential: true,
        });
    }

    function zoomToRegion(regionId) {
        if (!mapReady) return;
        map.fitBounds(regionBounds(regionId), {
            padding: cameraPadding(true),
            maxZoom: 10.2,
            duration: 850,
            essential: true,
        });
    }

    function showHomeMarker() {
        if (homeMarker || !mapReady) return;
        const marker = document.createElement("div");
        marker.className = "area-map-marker";
        marker.setAttribute("aria-label", "Perma Painting home base in Byron Bay");
        marker.innerHTML = '<span class="area-map-marker__dot"></span><span class="area-map-marker__ring"></span>';
        homeMarker = new maplibregl.Marker({ element: marker }).setLngLat(HOME_BASE).addTo(map);
    }

    function wait(milliseconds) {
        return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
    }

    function bindMapEvents() {
        map.on("mouseenter", "service-localities-base", () => {
            if (!journeyRunning) map.getCanvas().style.cursor = "pointer";
        });

        map.on("mousemove", "service-localities-base", (event) => {
            if (journeyRunning || !event.features?.length) return;
            const feature = event.features[0];
            const region = regionById.get(feature.properties.regionId);
            preview = {
                type: "locality",
                regionId: region.id,
                officialId: feature.properties.id,
                name: feature.properties.name,
            };
            renderState();
        });

        map.on("mouseleave", "service-localities-base", () => {
            map.getCanvas().style.cursor = "crosshair";
            preview = null;
            renderState();
        });

        map.on("click", "service-localities-base", (event) => {
            if (journeyRunning || !event.features?.length) return;
            const feature = event.features[0];
            const region = regionById.get(feature.properties.regionId);
            pinned = {
                type: "locality",
                regionId: region.id,
                officialId: feature.properties.id,
                name: feature.properties.name,
            };
            expandedRegions.clear();
            expandedRegions.add(region.id);
            syncRegionExpansion();
            preview = null;
            zoomToFeature(feature.properties.id);
            renderState();
        });
    }

    function regionSelection(regionId) {
        const region = regionById.get(regionId);
        return {
            type: "region",
            regionId,
            name: region.name,
        };
    }

    function localitySelection(region, locality, feature) {
        return {
            type: "locality",
            regionId: region.id,
            localityId: locality.id,
            officialId: locality.officialId,
            name: locality.name,
        };
    }

    function syncRegionExpansion() {
        for (const [regionId, section] of regionElements) {
            const header = section.querySelector(".atlas-region__header");
            const localities = section.querySelector(".atlas-region__localities");
            const toggle = section.querySelector(".atlas-region__toggle");
            const expanded = expandedRegions.has(regionId) && !section.hidden;
            header.setAttribute("aria-expanded", String(expanded));
            localities.classList.toggle("is-expanded", expanded);
            localities.setAttribute("aria-hidden", String(!expanded));
            localities.toggleAttribute("inert", !expanded);
            toggle.textContent = expanded ? "−" : "+";
        }
    }

    function renderDirectory() {
        let localityIndex = 0;
        for (const region of data.regions) {
            const section = document.createElement("section");
            section.className = "atlas-region";
            section.dataset.regionId = region.id;
            section.style.setProperty("--region-color", ACTIVE_COLOR);

            const header = document.createElement("button");
            header.type = "button";
            header.className = "atlas-region__header";
            header.setAttribute("aria-expanded", "false");
            header.setAttribute("aria-controls", `atlas-localities-${region.id}`);
            header.innerHTML = `
                <span class="atlas-region__name">${region.name}</span>
                <span class="atlas-region__toggle" aria-hidden="true">+</span>
            `;
            const showRegion = () => {
                ensureCoverageVisible();
                preview = regionSelection(region.id);
                renderState();
            };
            const hideRegion = () => {
                preview = null;
                renderState();
            };
            header.addEventListener("pointerenter", showRegion);
            header.addEventListener("pointerleave", hideRegion);
            header.addEventListener("focus", showRegion);
            header.addEventListener("blur", hideRegion);
            header.addEventListener("click", () => {
                ensureCoverageVisible();
                const willExpand = !expandedRegions.has(region.id);
                expandedRegions.clear();
                if (willExpand) expandedRegions.add(region.id);
                syncRegionExpansion();
                pinned = willExpand ? regionSelection(region.id) : null;
                preview = null;
                if (pinned) zoomToRegion(region.id);
                else focusCoverage();
                renderState();
            });

            const localityWrap = document.createElement("div");
            localityWrap.className = "atlas-region__localities";
            localityWrap.id = `atlas-localities-${region.id}`;
            localityWrap.setAttribute("aria-hidden", "true");
            localityWrap.setAttribute("inert", "");

            const localityInner = document.createElement("div");
            localityInner.className = "atlas-region__localities-inner";

            region.localities.forEach((locality) => {
                localityIndex += 1;
                const feature = featureById.get(locality.officialId);
                const selection = localitySelection(region, locality, feature);
                const button = document.createElement("button");
                button.type = "button";
                button.className = "atlas-locality";
                button.dataset.localityId = locality.id;
                button.dataset.officialId = locality.officialId;
                button.dataset.regionId = region.id;
                button.dataset.searchText = `${locality.name} ${locality.official} ${region.name}`.toLowerCase();
                button.setAttribute("aria-pressed", "false");
                if (locality.note) button.title = locality.note;
                button.innerHTML = `
                    <span class="atlas-locality__index">${String(localityIndex).padStart(2, "0")}</span>
                    <span class="atlas-locality__name">${locality.name}</span>
                    <span class="atlas-locality__meta">
                        ${locality.kind === "alias" ? '<span class="atlas-locality__alias">alias</span>' : ""}
                        <span class="atlas-locality__arrow" aria-hidden="true">→</span>
                    </span>
                `;
                const showLocality = () => {
                    ensureCoverageVisible();
                    preview = selection;
                    renderState();
                };
                const hideLocality = () => {
                    preview = null;
                    renderState();
                };
                button.addEventListener("pointerenter", showLocality);
                button.addEventListener("pointerleave", hideLocality);
                button.addEventListener("focus", showLocality);
                button.addEventListener("blur", hideLocality);
                button.addEventListener("click", () => {
                    ensureCoverageVisible();
                    pinned = pinned?.localityId === locality.id ? null : selection;
                    preview = null;
                    if (pinned) zoomToFeature(locality.officialId);
                    else focusCoverage();
                    renderState();
                });
                localityInner.appendChild(button);
                localityButtons.push(button);
            });

            localityWrap.appendChild(localityInner);
            section.append(header, localityWrap);
            regionList.appendChild(section);
            regionElements.set(region.id, section);
        }
    }

    function applyFilters() {
        const matchingOfficialIds = new Set();
        const visibleRegionIds = new Set();
        let visibleCount = 0;

        for (const button of localityButtons) {
            const matchesSearch = !searchQuery || button.dataset.searchText.includes(searchQuery);
            const visible = matchesSearch;
            button.hidden = !visible;
            if (visible) {
                visibleCount += 1;
                matchingOfficialIds.add(button.dataset.officialId);
                visibleRegionIds.add(button.dataset.regionId);
            }
        }

        for (const [regionId, section] of regionElements) {
            section.hidden = !localityButtons.some((button) => button.dataset.regionId === regionId && !button.hidden);
        }

        if (searchQuery) {
            expandedRegions.clear();
            visibleRegionIds.forEach((regionId) => expandedRegions.add(regionId));
        }
        syncRegionExpansion();

        if (mapReady) {
            const shouldFilterMap = Boolean(searchQuery);
            const filter = shouldFilterMap
                ? ["in", ["get", "id"], ["literal", [...matchingOfficialIds]]]
                : null;
            map.setFilter("service-localities-base", filter);
            map.setFilter("service-localities-outline", filter);
        }

        emptyState.hidden = visibleCount !== 0;
    }

    function renderState() {
        const active = preview || pinned;
        root.classList.toggle("has-map-focus", Boolean(active));

        if (mapReady) {
            map.setFilter("service-region-active", active ? ["==", ["get", "regionId"], active.regionId] : EMPTY_FILTER);
            map.setFilter("service-region-active-outline", active ? ["==", ["get", "regionId"], active.regionId] : EMPTY_FILTER);
            map.setFilter("service-locality-active", active?.type === "locality" ? ["==", ["get", "id"], active.officialId] : EMPTY_FILTER);
            map.setFilter("service-locality-active-outline", active?.type === "locality" ? ["==", ["get", "id"], active.officialId] : EMPTY_FILTER);
        }

        for (const button of localityButtons) {
            const currentByListId = active?.localityId && active.localityId === button.dataset.localityId;
            const currentByMapId = active?.type === "locality" && !active.localityId && active.officialId === button.dataset.officialId;
            const isCurrent = currentByListId || currentByMapId;
            const isPinned = pinned?.localityId === button.dataset.localityId;
            button.classList.toggle("is-current", Boolean(isCurrent));
            button.setAttribute("aria-pressed", String(Boolean(isPinned)));
        }
    }

    search.addEventListener("input", () => {
        searchQuery = search.value.trim().toLowerCase();
        pinned = null;
        expandedRegions.clear();
        ensureCoverageVisible();
        applyFilters();
        renderState();
    });

    function clearSelectionState(clearSearch = true) {
        preview = null;
        pinned = null;
        expandedRegions.clear();
        if (clearSearch) {
            searchQuery = "";
            search.value = "";
        }
        applyFilters();
        renderState();
    }

    function clearAll(returnToCoverage) {
        clearSelectionState(true);
        if (returnToCoverage) focusCoverage();
    }

    document.addEventListener("keydown", (event) => {
        if (journeyRunning) return;

        if (event.key === "/" && document.activeElement !== search && !/input|textarea|select/i.test(document.activeElement?.tagName)) {
            event.preventDefault();
            search.focus();
            return;
        }
        if (event.key === "Escape") {
            cancelJourney();
            clearAll(true);
            if (document.activeElement === search) search.blur();
        }
        if ((event.key === "ArrowDown" || event.key === "ArrowUp") && document.activeElement?.classList.contains("atlas-locality")) {
            const visibleButtons = localityButtons.filter((button) => !button.hidden);
            const index = visibleButtons.indexOf(document.activeElement);
            const offset = event.key === "ArrowDown" ? 1 : -1;
            const next = visibleButtons[(index + offset + visibleButtons.length) % visibleButtons.length];
            if (next) {
                event.preventDefault();
                next.focus();
            }
        }
    });

    renderDirectory();
    applyFilters();
    renderState();
    initMap();
})();
