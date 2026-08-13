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

# FAQ por (servicio, zona). Textos provistos por marketing (Ramón, jul 2026),
# PDF "Nuevas FAQ 27_7". Son ÚNICOS por página: las 3 zonas NO comparten
# preguntas ni respuestas (los datos cambian por zona a propósito: días de obra,
# años entre repintados, localidades). Alimentan el HTML visible (faq_html) y
# el schema FAQPage (schema_faq), así que editar acá los mantiene en sync.
# Casi todas tienen 3 Q/A; interior y exterior de Ballina tienen 4 (así vinieron).
# El {zone} de las plantillas viejas ya no se usa, pero .format(zone=...) sigue
# aplicándose por si se quiere volver a usar en algún texto.

FAQS = {
    # --- BYRON BAY ---
    ("House Painters", "Byron Bay"): [
        ("How long does a full house repaint take?",
         "A standard 3 bedroom home in Byron Bay usually takes 6-10 days depending on size and prep needed, longer if we're stripping old coastal salt damage first."),
        ("Do I need to move out while the work is being done?",
         "No, most Byron Bay homes stay liveable throughout. We work room by room or section by section and keep pathways and living areas clear."),
        ("What areas near Byron Bay do you service?",
         "Alongside Byron Bay itself, we regularly work in Suffolk Park, Bangalow, Brunswick Heads, Lennox Head and most of the Northern Rivers region."),
    ],
    ("Interior Painting", "Byron Bay"): [
        ("Will my furniture and floors be protected?",
         "Yes, floors, furniture and fittings are fully covered before we start, and we use a dustless sanding system to keep dust to a minimum — especially useful in Byron Bay's open-plan coastal homes."),
        ("Do I need to move out during interior painting?",
         "No. We work zone by zone, so you can keep living in the rest of the house — handy for short-stay rental turnovers too, if that applies to your property."),
        ("What products do you use for interior work?",
         "We use low-toxicity, low-odour paints, which matter in Byron Bay's tightly sealed, energy-efficient newer builds where ventilation can be limited."),
    ],
    ("Exterior Painting", "Byron Bay"): [
        ("How long does exterior paint last in Byron Bay?",
         "Given the salt air and UV exposure, we generally see 5-7 years before a repaint is needed, sometimes less on north or ocean-facing walls."),
        ("How do you prepare weathered or peeling exteriors?",
         "We wash down, scrape back any failing paint, sand and prime before applying coatings rated for coastal conditions."),
        ("Can you paint during Byron Bay's humid months?",
         "We schedule around weather and humidity, choosing dry windows and avoiding early mornings when dew is heavy."),
    ],
    ("Roof Painting", "Byron Bay"): [
        ("Does roof painting actually help with heat inside the house?",
         "Yes — a heat-reflective coating can noticeably lower indoor temperatures in Byron Bay's summer, especially in homes with lower ceiling insulation."),
        ("How often should a roof be repainted?",
         "Coastal salt exposure means most Byron Bay roofs benefit from a repaint every 8-10 years."),
        ("What does the roof prep process involve?",
         "We pressure wash, treat any rust or moss, then apply a primer before the topcoat."),
    ],
    ("Limewash Painting", "Byron Bay"): [
        ("What exactly is limewash, and how is it different to regular paint?",
         "Limewash is a mineral-based finish that soaks into the surface rather than sitting on top, giving a soft, textured, matte look popular on Byron Bay's beach-style homes."),
        ("Does limewash need any special upkeep?",
         "It weathers naturally over time, which is part of its appeal, but we can talk you through simple maintenance if you want it looking consistent."),
        ("What surfaces work best for limewash?",
         "Render, brick, drywall and some masonry surfaces take limewash particularly well — we can assess your walls during the quote."),
    ],
    ("Deck Painting", "Byron Bay"): [
        ("How long does decking oil or stain last outdoors in Byron Bay?",
         "With direct sun and salt air, most deck coatings need refreshing every 1-2 years to keep protecting the timber."),
        ("Do you repair damaged timber before painting?",
         "Yes, we check for rot, loose boards or damaged sections and repair these before any coating goes on."),
        ("What finish do you recommend for outdoor decks here?",
         "We generally recommend a UV and salt-resistant stain or paint suited to coastal exposure — we'll talk through options during the quote."),
    ],
    ("Kitchen Cabinet Painting", "Byron Bay"): [
        ("Is painting cabinets cheaper than replacing them?",
         "Yes, generally significantly cheaper than a full replacement, and a popular option for Byron Bay renovations and rental refreshes alike."),
        ("How long does a kitchen cabinet respray take?",
         "Most Byron Bay kitchens take 3-5 days, depending on the number of doors and drawers."),
        ("Can any cabinet material be painted?",
         "Most laminate, timber and MDF cabinets can be painted with the right prep — we'll confirm suitability when we see your kitchen."),
    ],
    ("Commercial Painters", "Byron Bay"): [
        ("Can you work outside normal business hours?",
         "Yes, we regularly schedule around trading hours for Byron Bay cafes, shops and accommodation providers to avoid disrupting business."),
        ("Do you work on strata or multi-tenant buildings?",
         "Yes, we manage the logistics and communication needed for shared or strata-titled commercial properties."),
        ("What types of businesses do you typically work with?",
         "Retail stores, hospitality venues and short-stay accommodation are common in Byron Bay, alongside standard office spaces."),
    ],

    # --- BALLINA ---
    ("House Painters", "Ballina"): [
        ("How long does a full house repaint take?",
         "A full interior and exterior repaint typically takes 8-12 days for an average Ballina home, depending on size and how much prep work is needed."),
        ("Will I need to vacate the property during the job?",
         "You can stay in your home during most of the job. We section off work areas and keep noise and mess to a minimum."),
        ("Do you cover areas outside Ballina itself?",
         "Yes — our Ballina crew also covers East Ballina, South Ballina, Lennox Head and Wardell."),
    ],
    ("Interior Painting", "Ballina"): [
        ("How long does interior painting take?",
         "A standard Ballina home takes around 5-10 days for interior painting, depending on the number of rooms and prep required."),
        ("How do you protect my floors and furniture?",
         "Everything is covered before we start, and our dustless sanding system keeps airborne dust down throughout the job."),
        ("Is it possible to stay home while you paint the interior?",
         "Yes — we section the work so parts of your Ballina home stay usable while we finish other rooms."),
        ("Are the paints you use safe indoors?",
         "We only use low-toxicity, low-odour paints, which is worth knowing if anyone in the household is sensitive to fumes."),
    ],
    ("Exterior Painting", "Ballina"): [
        ("How long does exterior painting take?",
         "Exterior painting for an average Ballina home takes around 7-12 days, depending on size, surface condition and weather."),
        ("How long does exterior paint typically last in Ballina?",
         "Homes further from the coastline tend to hold their exterior finish for 6-8 years, though river-facing properties may need attention sooner."),
        ("What's involved in prepping an older exterior?",
         "We start with a wash-down, address any flaking or cracked paint, then sand and prime before the final coats go on."),
        ("Does Northern Rivers humidity affect the painting schedule?",
         "Yes, we monitor humidity and rainfall and schedule exterior work for drier stretches to make sure the paint cures properly."),
    ],
    ("Roof Painting", "Ballina"): [
        ("Will roof painting reduce heat in my home?",
         "A quality reflective coating can make a real difference to indoor temperatures, particularly on north-facing roofs around Ballina."),
        ("How often does a roof need repainting in Ballina?",
         "Most Ballina roofs go 9-11 years between coats, depending on material and sun exposure."),
        ("What's involved in preparing the roof beforehand?",
         "We clean off moss and debris, repair any minor damage, then prime before applying the final coating."),
    ],
    ("Limewash Painting", "Ballina"): [
        ("What is limewash painting exactly?",
         "It's a breathable, mineral-based coating that creates texture and depth rather than a flat, uniform finish — a look that's becoming more popular on Ballina renders and brick homes."),
        ("Is limewash high-maintenance?",
         "Not really — it ages gracefully, though we can advise on refresh options if you'd prefer a consistent look long-term."),
        ("Which parts of my home suit limewash?",
         "Rendered or brick exteriors are the best candidates; we'll check your surfaces during the quote to confirm suitability."),
    ],
    ("Deck Painting", "Ballina"): [
        ("How long does deck painting last in Ballina's climate?",
         "Typically 2-3 years before a refresh is needed, but an annual recoat is recommendable."),
        ("Will you fix any damaged boards first?",
         "Yes, any rot, splitting or loose boards are repaired before we apply any coating."),
        ("What's the best finish for a Ballina deck?",
         "A weather-resistant stain or paint that handles humidity and rain well is usually the right call — we can advise based on your deck's exposure."),
    ],
    ("Kitchen Cabinet Painting", "Ballina"): [
        ("Does cabinet painting cost less than a full replacement?",
         "Yes, it's usually a fraction of the cost of new cabinetry, which makes it popular for Ballina kitchen updates."),
        ("How long does the kitchen cabinet job take?",
         "Typically 3-5 days for an average Ballina kitchen, depending on the layout and finish chosen."),
        ("Will my cabinets be suitable for painting?",
         "Most materials can be prepped and painted — we assess this during your free quote."),
    ],
    ("Commercial Painters", "Ballina"): [
        ("Can painting be scheduled outside business hours?",
         "Yes, we work with Ballina businesses to schedule around trading hours, including evenings or weekends if needed."),
        ("Do you handle strata-managed commercial properties?",
         "Yes, we're experienced coordinating with strata managers and multiple tenants on shared properties."),
        ("What kinds of commercial clients do you usually work with?",
         "Offices, retail spaces and hospitality venues around Ballina make up most of our commercial work."),
    ],

    # --- MULLUMBIMBY ---
    ("House Painters", "Mullumbimby"): [
        ("How long does a house repaint take in Mullumbimby?",
         "Older character homes and Queenslanders in Mullumbimby often take 6-9 days, as heritage weatherboard needs more careful prep than newer builds."),
        ("Can I stay in my home during the repaint?",
         "In most cases yes. We plan the job in stages so you're never without access to key living areas."),
        ("What surrounding areas do you service from Mullumbimby?",
         "We also service Brunswick Heads, Ocean Shores, Federal and Myocum from our Mullumbimby jobs."),
    ],
    ("Interior Painting", "Mullumbimby"): [
        ("Will my belongings be protected during interior painting?",
         "We cover floors, furniture and fixtures before starting, and use a dustless sanding system — particularly useful in older Mullumbimby homes with timber floors that scratch easily."),
        ("Do I need to leave the house while the interior is painted?",
         "No, most clients stay home. We work through the house in stages so daily life isn't disrupted."),
        ("What paint do you use inside heritage homes?",
         "We use low-toxicity, breathable-where-needed products suited to older weatherboard and Queenslander interiors common in Mullumbimby."),
    ],
    ("Exterior Painting", "Mullumbimby"): [
        ("How long does exterior paint last on Mullumbimby homes?",
         "Inland from the coast, exteriors typically last 7-9 years, though hinterland rain and humidity mean prep quality matters more than in drier areas."),
        ("How do you handle prep on older weatherboard exteriors?",
         "Heritage weatherboard needs careful scraping and sanding to avoid damaging the timber, followed by priming suited to older materials."),
        ("Can painting go ahead during Mullumbimby's wetter months?",
         "We work around the hinterland's rain patterns and hold off on exterior coats until surfaces are properly dry."),
    ],
    ("Roof Painting", "Mullumbimby"): [
        ("Does roof painting help with heat retention in Mullumbimby homes?",
         "Yes, especially on older tin roofs common in the hinterland, where a reflective coating can meaningfully cool the roof space."),
        ("How often should roofs be repainted around Mullumbimby?",
         "With less salt exposure inland, roofs here often go 10-12 years, though heavier rainfall means we check for rust more closely."),
        ("What does your roof prep involve?",
         "We wash the roof, treat rust spots and moss build-up from higher rainfall, then prime before the final coat."),
    ],
    ("Limewash Painting", "Mullumbimby"): [
        ("What makes limewash different from standard paint?",
         "It's a natural, breathable mineral finish rather than a plastic-based coating, which suits the character of Mullumbimby's older homes and gives a distinctive textured look."),
        ("Does limewash require special care over time?",
         "It naturally develops a soft patina, which many owners of character homes actually prefer — we can advise on options if you want a more even finish maintained."),
        ("What surfaces in my home would suit limewash?",
         "Render and masonry surfaces work best — common on many of Mullumbimby's older and heritage-style homes."),
    ],
    ("Deck Painting", "Mullumbimby"): [
        ("How often does deck coating need redoing in Mullumbimby?",
         "With higher rainfall and humidity inland, we generally recommend a refresh every 2-3 years to prevent moisture getting into the timber."),
        ("Do you address timber damage before painting the deck?",
         "Yes, we repair any rot or damaged boards first, which is especially important given the wetter hinterland climate."),
        ("What finish holds up best on Mullumbimby decks?",
         "A moisture-resistant stain designed to cope with higher humidity and rainfall works best here."),
    ],
    ("Kitchen Cabinet Painting", "Mullumbimby"): [
        ("Is cabinet painting a cheaper alternative to replacing my kitchen?",
         "Yes, it's a cost-effective way to modernise a kitchen without a full renovation, which suits many of Mullumbimby's older homes."),
        ("How long does kitchen cabinet painting take?",
         "Usually 3-5 days, sometimes longer for older cabinetry that needs extra prep."),
        ("Can older cabinets in character homes be painted?",
         "In most cases yes — older timber cabinetry common in Mullumbimby homes typically takes paint very well once properly prepped."),
    ],
    ("Commercial Painters", "Mullumbimby"): [
        ("Will the work disrupt my business during trading hours?",
         "We can schedule around your opening hours, including early mornings or after close, to minimise disruption to Mullumbimby businesses."),
        ("Do you work with strata or shared commercial buildings?",
         "Yes, we coordinate directly with strata managers and other tenants when needed."),
        ("What sort of businesses do you usually paint for?",
         "We work with local shops, offices and hospitality venues around Mullumbimby's town centre and surrounds."),
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
    """details/summary nativo. FAQ propio de cada (servicio, zona)."""
    items = []
    for q, a in FAQS[(service, zone)]:
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
    for q, a in FAQS[(service, zone)]:
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
