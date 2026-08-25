#!/usr/bin/env node

/**
 * Downloads a deliberately small subset of the official NSW Suburb layer and
 * packages it as a classic browser script. The locality data therefore loads
 * directly from file://; the MapLibre library and grey basemap still use their
 * external CDNs at preview time.
 *
 * Source: NSW Spatial Services — NSW Administrative Boundaries / Suburb.
 * Geometry is generalised to roughly 45 m for an interface-sized map. This is
 * cartographic reference data, not a legal definition of business coverage.
 */

import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUTPUT = resolve(HERE, "assets/service-areas-data.js");
const SOURCE = "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme_multiCRS/FeatureServer/2";

const regions = [
  {
    id: "tweed-border",
    name: "Tweed & border",
    range: "NSW–QLD border",
    color: "#b96f4d",
    localities: [
      { name: "Tweed Heads", official: "TWEED HEADS" },
      { name: "Tweed Heads South", official: "TWEED HEADS SOUTH" },
      { name: "Banora Point", official: "BANORA POINT" },
      { name: "Terranora", official: "TERRANORA" },
      { name: "Bilambil", official: "BILAMBIL" },
    ],
  },
  {
    id: "kingscliff-coast",
    name: "Kingscliff coast",
    range: "Tweed Coast",
    color: "#cc9d54",
    localities: [
      { name: "Kingscliff", official: "KINGSCLIFF" },
      { name: "Casuarina", official: "CASUARINA" },
      { name: "Salt Village", official: "CASUARINA", kind: "alias", note: "Local precinct within Casuarina" },
      { name: "Cudgen", official: "CUDGEN" },
      { name: "Chinderah", official: "CHINDERAH" },
      { name: "Pottsville", official: "POTTSVILLE" },
    ],
  },
  {
    id: "mullumbimby-north-byron",
    name: "Mullumbimby & North Byron",
    range: "Coast & hinterland",
    color: "#769f91",
    localities: [
      { name: "Mullumbimby", official: "MULLUMBIMBY" },
      { name: "Brunswick Heads", official: "BRUNSWICK HEADS" },
      { name: "Ocean Shores", official: "OCEAN SHORES" },
      { name: "South Golden Beach", official: "SOUTH GOLDEN BEACH" },
      { name: "New Brighton", official: "NEW BRIGHTON" },
      { name: "Billinudgel", official: "BILLINUDGEL" },
      { name: "Myocum", official: "MYOCUM" },
      { name: "Tyagarah", official: "TYAGARAH" },
      { name: "Federal", official: "FEDERAL" },
      { name: "The Pocket", official: "THE POCKET" },
    ],
  },
  {
    id: "byron-bay-hinterland",
    name: "Byron Bay & hinterland",
    range: "Home base",
    color: "#3c5b49",
    localities: [
      { name: "Byron Bay", official: "BYRON BAY" },
      { name: "Suffolk Park", official: "SUFFOLK PARK" },
      { name: "Ewingsdale", official: "EWINGSDALE" },
      { name: "Sunrise, Byron Bay", official: "BYRON BAY", kind: "alias", note: "Local precinct within Byron Bay" },
      { name: "Belongil", official: "BYRON BAY", kind: "alias", note: "Local precinct within Byron Bay" },
      { name: "Broken Head", official: "BROKEN HEAD" },
      { name: "Bangalow", official: "BANGALOW" },
      { name: "Coorabell", official: "COORABELL" },
      { name: "Skinners Shoot", official: "SKINNERS SHOOT" },
    ],
  },
  {
    id: "ballina-richmond-coast",
    name: "Ballina & Richmond coast",
    range: "Coast & river plain",
    color: "#5d91a0",
    localities: [
      { name: "Ballina", official: "BALLINA" },
      { name: "East Ballina", official: "EAST BALLINA" },
      { name: "South Ballina", official: "SOUTH BALLINA" },
      { name: "Lennox Head", official: "LENNOX HEAD" },
      { name: "Wardell", official: "WARDELL" },
      { name: "Alstonville", official: "ALSTONVILLE" },
      { name: "Newrybar", official: "NEWRYBAR" },
      { name: "Tintenbar", official: "TINTENBAR" },
      { name: "Cumbalum", official: "CUMBALUM" },
      { name: "Skennars Head", official: "SKENNARS HEAD", note: "Official spelling; replaces “Skinners Head”" },
    ],
  },
  {
    id: "lismore",
    name: "Lismore",
    range: "Richmond hinterland",
    color: "#8b708c",
    localities: [
      { name: "Lismore", official: "LISMORE" },
      { name: "Goonellabah", official: "GOONELLABAH" },
      { name: "East Lismore", official: "EAST LISMORE" },
      { name: "North Lismore", official: "NORTH LISMORE" },
      { name: "South Lismore", official: "SOUTH LISMORE" },
    ],
  },
];

const slugify = (value) => value
  .toLowerCase()
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9]+/g, "-")
  .replace(/(^-|-$)/g, "");

const officialNames = [...new Set(
  regions.flatMap((region) => region.localities.map((locality) => locality.official)),
)];

const query = new URL(`${SOURCE}/query`);
query.search = new URLSearchParams({
  where: `suburbname IN (${officialNames.map((name) => `'${name.replaceAll("'", "''")}'`).join(",")})`,
  outFields: "suburbname,postcode,lastupdate",
  returnGeometry: "true",
  outSR: "4326",
  geometryPrecision: "5",
  maxAllowableOffset: "0.0004",
  orderByFields: "suburbname",
  f: "geojson",
}).toString();

const response = await fetch(query, { headers: { accept: "application/geo+json, application/json" } });
if (!response.ok) {
  throw new Error(`NSW Spatial Services request failed: ${response.status} ${response.statusText}`);
}

const geojson = await response.json();
if (geojson.error) throw new Error(JSON.stringify(geojson.error));

const returned = new Set(geojson.features.map((feature) => feature.properties.suburbname));
const missing = officialNames.filter((name) => !returned.has(name));
if (missing.length) throw new Error(`Missing official localities: ${missing.join(", ")}`);

const officialToRegion = new Map();
for (const region of regions) {
  for (const locality of region.localities) {
    if (!officialToRegion.has(locality.official)) officialToRegion.set(locality.official, region.id);
    locality.id = slugify(`${region.id}-${locality.name}`);
    locality.officialId = slugify(locality.official);
  }
}

for (const feature of geojson.features) {
  const officialName = feature.properties.suburbname;
  feature.properties = {
    id: slugify(officialName),
    name: officialName.toLowerCase().replace(/(^|\s)\S/g, (char) => char.toUpperCase()),
    officialName,
    postcode: feature.properties.postcode,
    regionId: officialToRegion.get(officialName),
  };
}

const payload = {
  meta: {
    title: "Perma Painting service areas atlas",
    macroRegion: "Northern Rivers, NSW",
    sourceName: "NSW Spatial Services — NSW Administrative Boundaries, Suburb layer",
    sourceUrl: SOURCE,
    sourcePageUrl: "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme_multiCRS/FeatureServer/2",
    retrievedAt: new Date().toISOString(),
    displayLocalityCount: regions.reduce((sum, region) => sum + region.localities.length, 0),
    officialBoundaryCount: officialNames.length,
    regionCount: regions.length,
    disclaimer: "Service clusters are a Perma Painting presentation layer. Locality shapes are official reference boundaries and do not imply guaranteed service availability at every address.",
  },
  regions,
  geojson,
};

const banner = `/* Generated by build-data.mjs from NSW Spatial Services. Do not hand-edit. */\n`;
const output = `${banner}window.PERMA_SERVICE_AREAS = ${JSON.stringify(payload)};\n`;

await mkdir(dirname(OUTPUT), { recursive: true });
await writeFile(OUTPUT, output, "utf8");
console.log(`Wrote ${OUTPUT}`);
console.log(`${officialNames.length} official boundaries / ${payload.meta.displayLocalityCount} display names / ${regions.length} service clusters`);
