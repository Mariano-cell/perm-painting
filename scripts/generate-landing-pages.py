#!/usr/bin/env python3
"""
Genera las 24 landing pages SEO (8 servicios x 3 zonas).

Estrategia nueva (jun 2026, marketing Ramón): una página estática por
combinación servicio×zona, URL plana tipo /roof-painting-byron-bay.

Fuente del molde: template-landing.html (placeholders {{...}}).
Salida: <slug>.html en la raíz del proyecto (24 archivos).

Correr desde la raíz cada vez que se modifique el template o los datos:

    python3 scripts/generate-landing-pages.py

Las páginas generadas NO se editan a mano: se pisan al regenerar.

PENDIENTES DEL CLIENTE (marcados con [PENDIENTE] / contenido provisorio):
- FAQ (3 por página): preguntas/respuestas inventadas, a revisar.
- meta descriptions de los 3 índices de zona: redactadas internamente
  (AREA_META_DESCS); Ramón no mandó esas 3, reemplazar si las manda.
"""

import html as html_lib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template-landing.html"
DOMAIN = "https://permapainting.com.au"

# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------

# Orden fijo de los 8 servicios. photo_dir = carpeta en assets/photos,
# prefix = prefijo de archivo (la galería usa <prefix>_001..004).
SERVICES = [
    {"name": "House Painters",          "photo_dir": "residential",       "prefix": "residential"},
    {"name": "Interior Painting",       "photo_dir": "interior",          "prefix": "interior"},
    {"name": "Exterior Painting",       "photo_dir": "exterior",          "prefix": "exterior"},
    {"name": "Roof Painting",           "photo_dir": "roof",              "prefix": "roof"},
    {"name": "Limewash Painting",       "photo_dir": "limewash",          "prefix": "limewash"},
    {"name": "Deck Painting",           "photo_dir": "decks",             "prefix": "decks"},
    {"name": "Kitchen Cabinet Painting","photo_dir": "kitchen-cabinets",  "prefix": "kc"},
    {"name": "Commercial Painters",     "photo_dir": "commercial",        "prefix": "commercial"},
]

ZONES = ["Byron Bay", "Ballina", "Mullumbimby"]

# Localidades cercanas por zona (sección "Service area", pills).
NEARBY = {
    "Byron Bay":   ["Suffolk Park", "Brunswick Heads", "Bangalow", "Lennox Head"],
    "Ballina":     ["East Ballina", "South Ballina", "Lennox Head", "Wardell"],
    "Mullumbimby": ["Brunswick Heads", "Ocean Shores", "Federal", "Myocum"],
}

# Intros únicos por (servicio, zona). Provistos por el cliente/marketing.
INTROS = {
    ("House Painters", "Byron Bay"): "Full interior and exterior repaints for homes in Byron Bay, minutes from the beach and Cape Byron Lighthouse. One team handles the whole job — prep, painting and clean-up — with low-toxicity products and a clear schedule you can rely on from quote to finish.",
    ("Interior Painting", "Byron Bay"): "Interior painting for Byron Bay homes, from original beach cottages to newer builds. We work room by room with low-VOC paints and a dustless system that contains dust and airborne particles, protecting your furniture, floors and family while we work. The job stays clean and tidy so you're not living in a construction site longer than you need to.",
    ("Exterior Painting", "Byron Bay"): "Exterior painting built to handle Byron Bay's salt air, sun and humidity — and to hold up to the wear of a market where short-stay rental presentation can make or break a booking. Durable coatings, clean lines and finishes that photograph well.",
    ("Roof Painting", "Byron Bay"): "Roof painting and restoration for homes from the Byron Bay town centre out to the hinterland fringes. We clean, repair and recoat tile and metal roofs with heat-reflective finishes that hold up through summer and the wet season alike.",
    ("Limewash Painting", "Byron Bay"): "Limewash painting for Byron Bay homes, minutes from the beach and Cape Byron Lighthouse. The breathable, textured mineral finish suits the coastal cottage look many homeowners here are after, without trapping moisture in brick or render.",
    ("Deck Painting", "Byron Bay"): "Deck painting and staining for Byron Bay properties, from beach cottages to newer builds further out. Coastal humidity and sun take a toll on exposed timber — we use finishes built to handle both and keep your deck looking the part.",
    ("Kitchen Cabinet Painting", "Byron Bay"): "Kitchen cabinet painting for Byron Bay homes and short-stay rentals where presentation counts. A durable, high-end enamel finish gives tired cabinets a new look for a fraction of the cost of a full kitchen replacement.",
    ("Commercial Painters", "Byron Bay"): "Commercial painting for businesses across Byron Bay, from the town centre out to the hinterland fringes. We schedule around your trading hours — cafes, retail and offices — so the job gets done with minimal disruption to your business.",

    ("House Painters", "Ballina"): "Full interior and exterior house painting for homes in Ballina, from the town centre out along the Richmond River toward Ballina Island. One team, one quote, and a clear timeline from the first coat to the final clean-up.",
    ("Interior Painting", "Ballina"): "Interior painting for Ballina homes, where coastal humidity and salt air make a durable finish worth getting right. We use low-VOC paints and a dustless system that controls dust and airborne particles, working room by room and protecting your furniture and floors throughout the job.",
    ("Exterior Painting", "Ballina"): "Exterior painting for Ballina's mix of older brick-and-weatherboard homes and newer estates. We choose coatings to suit the surface and the coastal climate, so the finish holds up well beyond the first year.",
    ("Roof Painting", "Ballina"): "Roof painting and restoration in Ballina, using heat-resistant coatings that hold their finish through Northern Rivers summers. A properly coated roof also helps protect against weather damage over time.",
    ("Limewash Painting", "Ballina"): "Limewash painting in Ballina for a natural, breathable wall finish with genuine texture and depth. It's a specialist application, well suited to character homes and feature walls alike.",
    ("Deck Painting", "Ballina"): "Deck painting and staining in Ballina, built to handle Northern Rivers weather across every season. The right coating keeps timber decks looking sharp without constant upkeep.",
    ("Kitchen Cabinet Painting", "Ballina"): "Kitchen cabinet painting for Ballina homes, in older brick-and-weatherboard properties and newer estates alike. A durable enamel finish modernises tired cabinets at a fraction of the cost of a full kitchen renovation.",
    ("Commercial Painters", "Ballina"): "Commercial painting for Ballina businesses, from the town centre to the airport corridor. We work around your trading hours so cafes, offices and retail spaces stay open while the job gets done.",

    ("House Painters", "Mullumbimby"): "Full interior and exterior house painting for homes across Mullumbimby, from heritage Queenslanders in town to hinterland acreages. One team handles prep, painting and clean-up, with a clear schedule from quote to final coat.",
    ("Interior Painting", "Mullumbimby"): "Interior painting for Mullumbimby homes, in a town known for its arts community and organic farms. We use low-VOC paints and a dustless system to keep dust and airborne particles under control, working room by room so daily life isn't disrupted longer than it needs to be.",
    ("Exterior Painting", "Mullumbimby"): "Exterior painting built to handle the humidity that rolls off the Mullumbimby hinterland. We choose coatings suited to timber, weatherboard and render so the finish holds up through the wet season, not just the first summer.",
    ("Roof Painting", "Mullumbimby"): "Roof painting and restoration for properties across the older part of Mullumbimby and the surrounding rural blocks. We clean, repair and recoat with heat-reflective finishes built for hinterland sun and heavy rain.",
    ("Limewash Painting", "Mullumbimby"): "Limewash painting for Mullumbimby's heritage Queenslanders and hinterland acreages. The breathable, textured mineral finish suits older brick and render particularly well, and fits the relaxed character of homes in this area.",
    ("Deck Painting", "Mullumbimby"): "Deck painting and staining for Mullumbimby properties, where the arts-and-acreage lifestyle often means more time spent outdoors. We help pick the right finish for your timber and keep it protected against hinterland humidity.",
    ("Kitchen Cabinet Painting", "Mullumbimby"): "Kitchen cabinet painting in Mullumbimby — a fresh look for tired cabinets without the cost or downtime of a full renovation. We prep and finish cabinetry to a durable, high-end standard built for everyday use.",
    ("Commercial Painters", "Mullumbimby"): "Commercial painting for Mullumbimby shops, offices and local businesses, scheduled to minimise disruption to trading hours. Professional finishes with timelines you can rely on.",
}

# CTA final por servicio (texto del párrafo). Genérico pero específico al servicio.
CTA_TEXTS = {
    "House Painters": "Tell us about your home and we'll get back to you with a clear, no-obligation quote.",
    "Interior Painting": "Tell us about your space and we'll get back to you with a clear, no-obligation quote.",
    "Exterior Painting": "Tell us about your home's exterior and we'll get back to you with a clear, no-obligation quote.",
    "Roof Painting": "Tell us about your roof and we'll get back to you with a clear, no-obligation quote.",
    "Limewash Painting": "Tell us about your walls and we'll get back to you with a clear, no-obligation quote.",
    "Deck Painting": "Tell us about your deck and we'll get back to you with a clear, no-obligation quote.",
    "Kitchen Cabinet Painting": "Tell us about your kitchen and we'll get back to you with a clear, no-obligation quote.",
    "Commercial Painters": "Tell us about your premises and we'll get back to you with a clear, no-obligation quote.",
}

# FAQ PROVISORIO por servicio (3 Q/A). Inventado — el cliente debe revisar.
# {zone} se reemplaza con la zona de cada página.
FAQS = {
    "House Painters": [
        ("How long does a full house repaint take in {zone}?", "It depends on the size of the home and how much prep is needed, but most full repaints in {zone} take one to two weeks. We'll give you a clear timeline with your quote so you know what to expect."),
        ("Do you paint both inside and outside?", "Yes. We handle full interior and exterior repaints with one team, so prep, painting and clean-up are all coordinated and you only deal with one point of contact."),
        ("What kind of paint do you use?", "We work with low-toxicity, durable products chosen to suit your surfaces and the {zone} climate, prioritising longevity over quick fixes."),
    ],
    "Interior Painting": [
        ("Will my furniture and floors be protected?", "Yes. We mask and cover furniture and floors before we start, and our dustless system keeps dust and airborne particles contained while we work, room by room."),
        ("Do I need to move out during the job?", "Usually not. We work room by room so you can keep living in your {zone} home, and we keep the space clean and tidy throughout."),
        ("Are your paints low-odour?", "We use low-VOC paints, which are lower in odour and emissions than standard paints — better for your family while we work and after we leave."),
    ],
    "Exterior Painting": [
        ("How long will an exterior paint job last in {zone}?", "With proper prep and the right coatings for the coastal climate, a quality exterior repaint in {zone} can last many years. We choose products to suit your surface and the conditions."),
        ("Do you do the prep work too?", "Yes. Surface preparation is the most important part of a lasting finish — we clean, repair and prime before painting, and it's all included in your quote."),
        ("Can you work around the weather?", "We plan exterior jobs around the forecast and the wet season, so coats go on in the right conditions and the finish holds up."),
    ],
    "Roof Painting": [
        ("How long does a roof painting job take in {zone}?", "Most residential roofs take two to four days, depending on size, the condition of the surface and the weather. We clean and repair first, then apply the coats — and we'll give you a clear timeline with your quote so you know what to expect from start to finish."),
        ("Can you paint both tile and metal roofs?", "Yes. We work on both tile and Colorbond/metal roofs, using a coating system suited to each surface. For the conditions around {zone} we use heat-reflective, weather-resistant finishes that hold up through summer heat and the wet season."),
        ("Is a roof inspection included before you start?", "Every job starts with an inspection. We check for broken tiles, rust, leaks and any surface issues, then include the necessary repairs in your quote — so there are no surprises once the work begins."),
    ],
    "Limewash Painting": [
        ("What is limewash and why choose it?", "Limewash is a breathable mineral finish with natural texture and depth. It lets brick and render breathe instead of trapping moisture, and gives the soft, characterful look many {zone} homes are after."),
        ("Can limewash go over any surface?", "It's best suited to porous surfaces like brick and render. We assess your walls first and let you know whether limewash is the right choice for your {zone} home."),
        ("Is limewash durable?", "Applied correctly, limewash is long-lasting and ages gracefully. It's a specialist application, and we have the experience to get it right."),
    ],
    "Deck Painting": [
        ("Should I paint, stain or oil my deck?", "It depends on the timber and the look you want. We help you pick the right finish for your {zone} deck and the conditions it faces, so it stays protected and looks the part."),
        ("How do you handle weathered timber?", "We clean, sand and prep weathered boards before any coating goes on — proper prep is what makes the finish last against humidity and sun."),
        ("How often will the deck need recoating?", "It varies with exposure and the finish used, but the right coating keeps a {zone} deck looking sharp for years without constant upkeep."),
    ],
    "Kitchen Cabinet Painting": [
        ("Is cabinet painting cheaper than a new kitchen?", "Yes — painting your existing cabinetry gives a fresh, modern look for a fraction of the cost of a full kitchen replacement, with far less downtime."),
        ("How durable is the finish?", "We prep and finish cabinets to a durable, high-end enamel standard built to stand up to everyday use in your {zone} kitchen."),
        ("How long does it take?", "Most kitchens take several days, depending on the number of doors and drawers. We'll give you a clear timeline with your quote."),
    ],
    "Commercial Painters": [
        ("Can you work outside our trading hours?", "Yes. We schedule commercial jobs around your trading hours in {zone} — including early mornings, evenings or quieter days — so your business keeps running while the work gets done."),
        ("Do you handle larger commercial sites?", "Yes. We take on cafes, retail, offices and larger premises, with timelines and finishes you can rely on."),
        ("Will the work disrupt our customers?", "We plan the job to minimise disruption, keeping work areas tidy and contained so your space stays presentable while we're there."),
    ],
}

# Meta descriptions por (servicio, zona). Provistas por marketing (Ramón, jul 2026).
META_DESCS = {
    ("House Painters", "Byron Bay"): "Byron Bay house painters with a clean, professional finish. Low-tox products, clear timelines, no surprises. Free quote today.",
    ("Interior Painting", "Byron Bay"): "Interior painting in Byron Bay done with minimal mess and disruption. Durable, low-toxicity finishes. Request a free quote.",
    ("Exterior Painting", "Byron Bay"): "Coastal-grade exterior painting for Byron Bay homes — coatings built to handle salt air and humidity. Get a free quote.",
    ("Roof Painting", "Byron Bay"): "Heat-resistant roof painting and restoration in Byron Bay. Lower indoor temps, longer-lasting finish. Free quote today.",
    ("Limewash Painting", "Byron Bay"): "Limewash painting in Byron Bay for a natural, breathable, textured look — increasingly popular on Byron homes. Request a quote.",
    ("Deck Painting", "Byron Bay"): "Outdoor deck painting and staining in Byron Bay, built to handle sun, salt and rain. Get a free quote today.",
    ("Kitchen Cabinet Painting", "Byron Bay"): "Refresh your kitchen in Byron Bay without a full renovation. Cabinet painting with a lasting finish. Free quote today.",
    ("Commercial Painters", "Byron Bay"): "Commercial painters in Byron Bay for shops, offices and hospitality fit-outs. Minimal disruption, clear timelines. Request a quote.",

    ("House Painters", "Ballina"): "Looking for reliable house painters in Ballina? Quality finishes, low-tox products and a schedule you can count on. Free quote.",
    ("Interior Painting", "Ballina"): "Interior painting in Ballina with clean processes and durable, low-toxicity finishes. Get a free quote today.",
    ("Exterior Painting", "Ballina"): "Exterior painting in Ballina with coatings built for the Northern Rivers climate. Request a free quote.",
    ("Roof Painting", "Ballina"): "Roof painting and restoration in Ballina. Durable, heat-resistant coatings that hold up over time. Free quote today.",
    ("Limewash Painting", "Ballina"): "Specialist limewash painting in Ballina — a natural, breathable finish with real texture and depth. Request a free quote.",
    ("Deck Painting", "Ballina"): "Deck painting and staining in Ballina, finished to handle Northern Rivers weather year-round without early wear or fading. Get a free quote today.",
    ("Kitchen Cabinet Painting", "Ballina"): "Transform your Ballina kitchen with professional cabinet painting, no full renovation needed and minimal downtime involved. Request a free quote today.",
    ("Commercial Painters", "Ballina"): "Professional commercial painters in Ballina for offices, retail and hospitality spaces, with reliable timelines you can plan around. Get a free quote.",

    ("House Painters", "Mullumbimby"): "House painters in Mullumbimby offering high-quality finishes and a clear, reliable timeline from first quote to final coat. Request a free quote.",
    ("Interior Painting", "Mullumbimby"): "Expert interior painting in Mullumbimby using low-toxicity products and a clean, tidy process room by room of your home. Request a free quote today.",
    ("Exterior Painting", "Mullumbimby"): "Exterior painters in Mullumbimby using coatings designed to handle the Northern Rivers climate and hinterland humidity year-round. Get a free quote.",
    ("Roof Painting", "Mullumbimby"): "Roof painting and restoration in Mullumbimby with durable, heat-resistant coatings built for local weather conditions. Request a free quote today.",
    ("Limewash Painting", "Mullumbimby"): "Limewash painting in Mullumbimby for a distinctive, natural and breathable finish that suits the area's character homes well. Get a free quote today.",
    ("Deck Painting", "Mullumbimby"): "Weather-resistant deck painting and staining for Mullumbimby homes, built to handle humidity and seasonal rain year-round. Request a free quote today.",
    ("Kitchen Cabinet Painting", "Mullumbimby"): "Kitchen cabinet painting in Mullumbimby for a fresh look without a full renovation or weeks of downtime involved. Get a free quote today.",
    ("Commercial Painters", "Mullumbimby"): "Commercial painters in Mullumbimby for shops, offices and local businesses, with professional finishes and clear timelines throughout the job.",
}

# Meta descriptions de los 3 índices de zona (redactadas internamente, jul 2026;
# Ramón no mandó estas 3 — reemplazar acá si las manda).
AREA_META_DESCS = {
    "Byron Bay": "Professional painting services in Byron Bay — house, interior, exterior, roof, limewash, deck, kitchen cabinets and commercial. Free quote today.",
    "Ballina": "Painting services in Ballina — from full house repaints to roofs, decks and commercial spaces. Low-tox products, clear timelines. Request a free quote.",
    "Mullumbimby": "Painters in Mullumbimby for every job — interiors, exteriors, roofs, limewash, decks and more. Quality finishes, reliable timelines. Get a free quote.",
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Debe coincidir con slugify() de js/main.js."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def page_slug(service: str, zone: str) -> str:
    """house-painters-byron-bay, roof-painting-ballina, etc."""
    return f"{slugify(service)}-{slugify(zone)}"


def webp_src(src: str) -> str:
    return re.sub(r"\.(jpe?g|png)$", ".webp", src, flags=re.IGNORECASE)


@lru_cache(maxsize=None)
def image_dimensions(src: str) -> tuple[int, int]:
    # macOS: sips. Fallback (Linux/otros): Pillow, si está instalado.
    try:
        output = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(ROOT / src)],
            text=True,
        )
    except FileNotFoundError:
        from PIL import Image

        with Image.open(ROOT / src) as im:
            return im.size
    values: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return int(values["pixelWidth"]), int(values["pixelHeight"])


def gallery_html(service: dict, zone: str) -> str:
    """4 figuras con fotos del servicio. Alt text incluye la zona."""
    prefix = service["prefix"]
    pdir = service["photo_dir"]
    sl = service["name"].lower()
    # alt variados por foto, todos con la zona
    alts = [
        f"{sl} in {zone}",
        f"{sl} project in {zone}",
        f"{sl} work in {zone}",
        f"professional {sl} in {zone}",
    ]
    delays = ["0s", "0.12s", "0.24s", "0.36s"]
    rows = []
    for i in range(4):
        n = f"{i+1:03d}"
        src = f"assets/photos/{pdir}/{prefix}_{n}.jpg"
        width, height = image_dimensions(src)
        rows.append(
            f'                <figure class="landing-gallery__card os-reveal" style="--reveal-delay: {delays[i]}">\n'
            f'                    <picture class="landing-gallery__picture">\n'
            f'                        <source srcset="{webp_src(src)}" type="image/webp">\n'
            f'                        <img src="{src}" alt="{alts[i]}"\n'
            f'                            class="landing-gallery__img" width="{width}" height="{height}" loading="lazy" decoding="async">\n'
            f'                    </picture>\n'
            f'                </figure>'
        )
    return "\n\n".join(rows)


def pills_html(zone: str) -> str:
    rows = [f'                    <li class="landing-area__pill">{loc}</li>' for loc in NEARBY[zone]]
    return "\n".join(rows)


def faq_html(service: str, zone: str) -> str:
    """details/summary nativo. {zone} reemplazado en las plantillas."""
    items = []
    for q, a in FAQS[service]:
        q = q.format(zone=zone)
        a = a.format(zone=zone)
        items.append(
            f'                    <details class="landing-faq__item">\n'
            f'                        <summary class="landing-faq__question">{q}</summary>\n'
            f'                        <div class="landing-faq__answer">\n'
            f'                            <p>{a}</p>\n'
            f'                        </div>\n'
            f'                    </details>'
        )
    return "\n\n".join(items)


def crosslinks_services_html(zone: str, current_service: str) -> str:
    """Los otros 7 servicios de la misma zona."""
    rows = []
    for s in SERVICES:
        if s["name"] == current_service:
            continue
        slug = page_slug(s["name"], zone)
        rows.append(
            f'                        <li><a class="landing-links__link" href="{slug}.html">'
            f'<span>{s["name"]}</span>'
            f'<span class="landing-links__arrow" aria-hidden="true">→</span></a></li>'
        )
    return "\n".join(rows)


def crosslinks_zones_html(service: str, current_zone: str) -> str:
    """El mismo servicio en las otras 2 zonas."""
    rows = []
    for z in ZONES:
        if z == current_zone:
            continue
        slug = page_slug(service, z)
        rows.append(
            f'                        <li><a class="landing-links__link" href="{slug}.html">'
            f'<span>{service} in {z}</span>'
            f'<span class="landing-links__arrow" aria-hidden="true">→</span></a></li>'
        )
    return "\n".join(rows)


def schema_breadcrumb(service: str, zone: str, slug: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": service, "item": f"{DOMAIN}/{slug}"},
            {"@type": "ListItem", "position": 3, "name": zone},
        ],
    }
    return json.dumps(data, indent=8, ensure_ascii=False)


def schema_faq(service: str, zone: str) -> str:
    main = []
    for q, a in FAQS[service]:
        main.append({
            "@type": "Question",
            "name": q.format(zone=zone),
            "acceptedAnswer": {"@type": "Answer", "text": a.format(zone=zone)},
        })
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": main}
    return json.dumps(data, indent=8, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    count = 0

    for service in SERVICES:
        sname = service["name"]
        for zone in ZONES:
            slug = page_slug(sname, zone)
            intro = INTROS[(sname, zone)]

            page = template
            replacements = {
                "{{META_TITLE}}": f"{sname} in {zone} | Perma Painting",
                "{{META_DESCRIPTION}}": META_DESCS[(sname, zone)],
                "{{DOMAIN}}": DOMAIN,
                "{{SLUG}}": slug,
                "{{SERVICE}}": sname,
                "{{SERVICE_LOWER}}": sname.lower(),
                # "Roof Painting" -> "Roof painting" (solo 1ra letra mayúscula)
                "{{SERVICE_LOWER_CAP}}": sname[0] + sname[1:].lower(),
                "{{ZONE}}": zone,
                "{{INTRO}}": intro,
                "{{CTA_TEXT}}": CTA_TEXTS[sname],
                "{{GALLERY}}": gallery_html(service, zone),
                "{{PILLS}}": pills_html(zone),
                "{{FAQ}}": faq_html(sname, zone),
                "{{CROSSLINKS_SERVICES}}": crosslinks_services_html(zone, sname),
                "{{CROSSLINKS_ZONES}}": crosslinks_zones_html(sname, zone),
                "{{SCHEMA_BREADCRUMB}}": schema_breadcrumb(sname, zone, slug),
                "{{SCHEMA_FAQ}}": schema_faq(sname, zone),
            }
            for k, v in replacements.items():
                page = page.replace(k, v)

            (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
            count += 1
            print(f"  ✓ {slug}.html")

    print(f"\n{count} landing pages generadas en la raíz del proyecto.")
    if count != 24:
        raise SystemExit(f"ERROR: se esperaban 24 páginas, se generaron {count}")

    generate_area_indexes()


# ---------------------------------------------------------------------------
# ÍNDICES POR ZONA (AREAS OF SERVICE)
# Página simple por zona: solo título + links a los 8 servicios de esa zona.
# Sin contenido propio para no canibalizar las landings.
# El header/footer se extraen del template-landing (ya tienen el nav nuevo)
# para mantener una sola fuente de verdad.
# ---------------------------------------------------------------------------

def _extract(tag_open_marker: str, tag_close: str, html: str) -> str:
    start = html.index(tag_open_marker)
    end = html.index(tag_close, start) + len(tag_close)
    return html[start:end]


# Mapa de zonas: SOLO se inserta en el índice de Byron Bay (la zona que el
# GeoJSON destaca). Para las otras zonas, los placeholders quedan vacíos.
# Si en el futuro se quiere un mapa por zona, hacer un GeoJSON por zona y
# mapear ZONE -> bloque correspondiente.
AREA_MAP_ZONE = "Byron Bay"

AREA_MAP_HTML = """                <div class="area-index__head-media">
                    <div class="area-map" data-area-map>
                        <div class="area-map__canvas" id="area-map-canvas"></div>
                    </div>
                </div>"""

AREA_MAP_SCRIPT = '    <script src="js/area-map.js" defer></script>'


def generate_area_indexes() -> None:
    landing = TEMPLATE.read_text(encoding="utf-8")
    header = _extract('<header class="site-header"', "</header>", landing)
    footer = _extract('<footer class="site-footer"', "</footer>", landing)

    idx_template = (ROOT / "template-area-index.html").read_text(encoding="utf-8")

    for zone in ZONES:
        slug = slugify(zone)

        # links a los 8 servicios de esta zona
        rows = []
        for s in SERVICES:
            s_slug = page_slug(s["name"], zone)
            rows.append(
                f'                        <li><a class="landing-links__link" href="{s_slug}.html">'
                f'<span>{s["name"]}</span>'
                f'<span class="landing-links__arrow" aria-hidden="true">→</span></a></li>'
            )
        service_links = "\n".join(rows)

        # localidades de la zona como pills (sin link: no tienen página propia).
        # Incluye la zona principal primero, luego las cercanas.
        area_names = [zone] + NEARBY[zone]
        pill_rows = [
            f'                    <li class="landing-area__pill">{loc}</li>'
            for loc in area_names
        ]
        area_pills = "\n".join(pill_rows)

        # botones-link a las OTRAS 2 zonas principales (cada una con índice propio)
        other_rows = []
        for z in ZONES:
            if z == zone:
                continue
            z_slug = slugify(z)
            other_rows.append(
                f'                            <a class="area-index__zone-btn" href="{z_slug}.html">'
                f'<span>{z}</span>'
                f'<span class="area-index__zone-btn-arrow" aria-hidden="true">→</span></a>'
            )
        other_zone_links = "\n".join(other_rows)

        breadcrumb = json.dumps({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": zone},
            ],
        }, indent=8, ensure_ascii=False)

        # Columna derecha del head:
        # - Byron Bay -> el mapa interactivo (con su script).
        # - Otras zonas -> una imagen 4/3 (assets/photos/area-index/<slug>.jpg).
        if zone == AREA_MAP_ZONE:
            area_map_html = AREA_MAP_HTML
            area_map_script = AREA_MAP_SCRIPT
        else:
            src = f"assets/photos/area-index/{slug}.jpg"
            width, height = image_dimensions(src)
            area_map_html = (
                '                <div class="area-index__head-media">\n'
                '                    <div class="area-index__photo-container">\n'
                f'                        <picture class="area-index__photo-picture">\n'
                f'                            <source srcset="{webp_src(src)}" type="image/webp">\n'
                f'                            <img src="{src}"\n'
                f'                                alt="Painting work in {zone}" class="area-index__photo" width="{width}" height="{height}">\n'
                f'                        </picture>\n'
                '                    </div>\n'
                '                </div>'
            )
            area_map_script = ""

        page = idx_template
        page = page.replace("{{HEADER}}", header)
        page = page.replace("{{FOOTER}}", footer)
        page = page.replace("{{SERVICE_LINKS}}", service_links)
        page = page.replace("{{AREA_PILLS}}", area_pills)
        page = page.replace("{{OTHER_ZONE_LINKS}}", other_zone_links)
        page = page.replace("{{AREA_MAP}}", area_map_html)
        page = page.replace("{{AREA_MAP_SCRIPT}}", area_map_script)
        page = page.replace("{{SCHEMA_BREADCRUMB}}", breadcrumb)
        page = page.replace("{{ZONE}}", zone)
        page = page.replace("{{SLUG}}", slug)
        page = page.replace("{{DOMAIN}}", DOMAIN)
        page = page.replace("{{META_DESCRIPTION}}", AREA_META_DESCS[zone])

        (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
        print(f"  ✓ {slug}.html (índice de zona)")

    print("3 índices por zona generados.")


if __name__ == "__main__":
    main()
