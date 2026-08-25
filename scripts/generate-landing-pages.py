#!/usr/bin/env python3
from __future__ import annotations

"""
Genera las 60 landing pages SEO (10 servicios x 6 zonas).

Estrategia nueva (jun 2026, marketing Ramón): una página estática por
combinación servicio×zona, URL plana tipo /roof-painting-byron-bay.

Fuente del molde: template-landing.html (placeholders {{...}}).
Salida: <slug>.html en la raíz del proyecto (60 archivos).

Correr desde la raíz cada vez que se modifique el template o los datos:

    python3 scripts/generate-landing-pages.py

Las páginas generadas NO se editan a mano: se pisan al regenerar.

Los pendientes de contenido y assets se centralizan en DEVOLUCION-RAMON.md.
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

# Orden fijo de los 10 servicios. photo_dir = carpeta en assets/photos,
# prefix = prefijo de archivo (la galería usa <prefix>_001..004).
# "hero" (opcional) = foto propia del servicio para el hero de la landing
# (assets/photos/<hero>.jpg + .webp). Misma foto en las 3 zonas del servicio.
# Si no está seteado, se usa la foto genérica landing_005 (comportamiento
# histórico, compartida por todas las landings).
SERVICES = [
    {"name": "House Painters",          "photo_dir": "residential",       "prefix": "residential",  "hero": "residential/residential-hero"},
    {"name": "Interior Painting",       "photo_dir": "interior",          "prefix": "interior",     "hero": "interior/interior-hero"},
    {"name": "Exterior Painting",       "photo_dir": "exterior",          "prefix": "exterior",     "hero": "exterior/exterior-hero"},
    {"name": "Roof Painting",           "photo_dir": "roof",              "prefix": "roof",         "hero": "roof/roof-hero"},
    {"name": "Limewash Painting",       "photo_dir": "limewash",          "prefix": "limewash",     "hero": "limewash/limewash-hero"},
    {"name": "Deck Painting",           "photo_dir": "decks",             "prefix": "decks",        "hero": "decks/decks-hero"},
    {"name": "Kitchen Cabinet Painting","photo_dir": "kitchen-cabinets",  "prefix": "kc",            "hero": "kitchen-cabinets/kc-hero"},
    {"name": "Commercial Painters",     "photo_dir": "commercial",        "prefix": "commercial",   "hero": "commercial/commercial-hero"},
    {"name": "Epoxy Floors",            "photo_dir": "epoxy",             "prefix": "epoxy"},
    {"name": "Lead Paint Removal & Restoration", "photo_dir": "lead-paint", "prefix": "lead-paint"},
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
    "Epoxy Floors": "Tell us about your floor and we'll get back to you with a clear, no-obligation quote.",
    "Lead Paint Removal & Restoration": "Tell us about the paintwork and we'll get back to you with a clear, no-obligation quote.",
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
# ZONAS NUEVAS (ago 2026)
#
# Ramón pidió localidades nuevas con índices DISTINTOS al de las 3 viejas, y
# manda un modelo de página distinto por zona. Todos comparten la misma
# cáscara (template-area-shell.html: head, header, breadcrumb, grilla de
# servicios, otras zonas) y solo cambia el hero, que sale de un parcial:
#
#   modelo "quote" -> template-area-hero-quote.html
#                     texto + trust badges + formulario sticky + foto
#   modelo "local" -> template-area-hero-local.html
#                     texto + badge de trabajos + "Local knowledge" + FAQ
#
# Para sumar un modelo nuevo: un parcial más, su entrada en AREA_HERO_TEMPLATES
# y su rama en generate_new_area_indexes(). La cáscara no se toca.
#
# Decisión (Mariano, ago 2026): Byron Bay / Ballina / Mullumbimby NO cambian;
# siguen con template-area-index.html.
#
# OJO: estas zonas NO están en ZONES a propósito. Meterlas ahí regeneraría
# las 30 landings existentes con crosslinks nuevos (y habría que propagar el
# header).
#
# ago 2026: el dropdown "AREAS OF SERVICE" ya no existe — el nav tiene un link
# simple a /service-areas. Sumar una zona nueva ya no toca el header: alcanza
# con darla de alta acá y en SERVICE_AREA_ORDER (el hub). Los :nth-child de
# fadeDropIn en style.css están tuneados para los 5 items de nivel superior.
NEW_ZONES = ["Kingscliff", "Tweed Heads", "Lismore"]

AREA_HERO_TEMPLATES = {
    "quote": "template-area-hero-quote.html",
    "local": "template-area-hero-local.html",
}

# Íconos de los trust badges (paths sueltos; el stroke/fill lo pone el CSS).
TRUST_ICONS = {
    "shield": '<path d="M12 3l7 3v6c0 5-3.4 7.8-7 9-3.6-1.2-7-4-7-9V6z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "brush": '<path d="M14 3l7 7-8 8-7-7z"/><path d="M6 15l-3 6 6-3"/>',
}

# Datos por zona nueva.
#   headline / intro / nearby / trust -> material entregado por Ramón.
#   meta -> versión definitiva de "Info Nuevas Landings Perma - 20-8.md".
#   photo -> PLACEHOLDER: hoy es una copia de exterior-hero. Cuando lleguen
#            las fotos reales de la zona, pisar assets/photos/area-index/
#            <slug>.jpg + .webp y regenerar.
NEW_ZONE_DATA = {
    "Kingscliff": {
        "model": "quote",
        "title": "Painters Kingscliff | Perma Painting",
        "meta": "Painters in Kingscliff for beach houses and new builds across Salt Village, Casuarina and Cudgen. Salt-air rated finishes, free quotes, fully insured local crews.",
        "headline": "Painting in Kingscliff and the Tweed Coast beaches",
        "intro": "Kingscliff has grown fast, with new builds in the Salt precinct sitting alongside classic beach houses and a steady flow of holiday rental turnovers — get a free quote in under a minute.",
        "nearby": ["Casuarina", "Salt Village", "Cudgen", "Chinderah"],
        "photo": "assets/photos/area-index/kingscliff.jpg",
        "photo_alt": "Recent painting job in Kingscliff",
        "trust": [
            ("shield", "Fully insured &amp; licensed crews"),
            ("clock", "Reply within 24 hours"),
            ("brush", "Salt-air rated finishes"),
        ],
    },

    # Modelo "local": headline, intro, pills, local_knowledge y faqs son de
    # Ramón (croquis D5). jobs_badge queda en None hasta que mande el número
    # real de trabajos hechos en la zona: sin dato, el badge no se renderiza.
    # El croquis traía además un testimonio firmado "Strata Committee Member";
    # se sacó por decisión de Mariano (ago 2026).
    "Tweed Heads": {
        "model": "local",
        "title": "Painters Tweed Heads | Perma Painting",
        "meta": "Trusted painters in Tweed Heads for established homes, unit blocks and strata repaints. Free quotes, fully insured local crews on the NSW/QLD border.",
        "headline": "Painters Tweed Heads &amp; the Border",
        "intro": "Quality painting for established homes and businesses on the NSW/QLD border. Tweed Heads is one of the most established communities on the Tweed Coast, with a mix of long-standing family homes, unit blocks and local businesses.",
        "nearby": ["Banora Point", "Terranora", "Bilambil", "Tweed Heads South"],
        "jobs_badge": None,  # PENDIENTE: número real de trabajos en la zona
        "local_knowledge": [
            "Older weatherboard &amp; brick homes across established Tweed Heads streets",
            "Unit block exteriors &amp; strata repaints near the river",
            "Commercial fit-outs for local Tweed Heads businesses",
            "Rendered homes bordering Banora Point &amp; Terranora",
        ],
        "faqs": [
            ("Do you handle strata or unit block repaints?",
             "Yes — we regularly quote strata and unit block exteriors around Tweed Heads, working with committees on scheduling and access."),
            ("Can you match older weatherboard or rendered brick finishes?",
             "Yes, matching existing finishes on established homes is one of our specialties in this area."),
            ("Do you also service Banora Point and Terranora?",
             "Yes, both are part of our regular Tweed Heads coverage."),
        ],
    },

    # Segundo modelo "local" (croquis D4). Mismo criterio que Tweed Heads:
    # jobs_badge en None hasta tener el número real, y sin el testimonio que
    # traía el croquis ("Homeowner — South Lismore").
    # OJO con el title: el croquis decía "House Painters Lismore", que chocaría
    # con el <title> de la landing house-painters-lismore.html. Se usa
    # "Painters Lismore", igual que las otras dos zonas nuevas.
    "Lismore": {
        "model": "local",
        "title": "Painters Lismore | Perma Painting",
        "meta": "Local painters in Lismore for heritage homes, storm and flood repairs, and Goonellabah properties. Free quotes, fully insured local crews.",
        "headline": "House Painters Lismore &amp; Surrounds",
        "intro": "Trusted interior &amp; exterior painting for Lismore homes and businesses. Perma Painting brings the same quality finish we're known for across Byron Bay, Ballina and Mullumbimby to Lismore and the surrounding Northern Rivers hinterland.",
        "nearby": ["Goonellabah", "East Lismore", "North Lismore", "South Lismore"],
        "jobs_badge": None,  # PENDIENTE: número real de trabajos en la zona
        "local_knowledge": [
            "Heritage homes in East Lismore &amp; Girards Hill",
            "Storm &amp; flood-affected homes across North &amp; South Lismore",
            "Established brick &amp; weatherboard homes in Goonellabah",
            "Rural &amp; acreage properties toward Wyrallah",
        ],
        "faqs": [
            ("Do you handle storm or flood damage repaints?",
             "Yes — we regularly repaint homes across North and South Lismore affected by storm or flood damage, prepping surfaces properly before recoating."),
            ("Can you match heritage colour schemes in East Lismore or Girards Hill?",
             "Yes, we check heritage guidelines where they apply and match existing colour schemes on request."),
            ("Do you also service Goonellabah?",
             "Yes, Goonellabah is part of our regular Lismore coverage."),
        ],
    },
}


# ---------------------------------------------------------------------------
# CONTENIDO DEFINITIVO DE RAMÓN (20 ago 2026)
# 30 páginas de Kingscliff / Tweed Heads / Lismore + los dos servicios
# nuevos en Byron Bay / Ballina / Mullumbimby.
# ---------------------------------------------------------------------------

INTROS.update({('House Painters', 'Kingscliff'): 'Kingscliff mixes new builds in the Salt precinct with classic beach houses along '
                                   'Cudgen Creek and the coast, and every one of them needs paint that can handle '
                                   'the salt air. Our Kingscliff crews prep and coat homes to hold their finish '
                                   'through the coastal weather, not just look good on handover day.',
 ('Interior Painting', 'Kingscliff'): "Whether it's a Salt Village townhouse or an older beach house near the "
                                      'Kingscliff foreshore, interior painting here often means fitting around '
                                      'holiday rental turnovers or young families settling in. We schedule around '
                                      'your calendar and finish with minimal mess.',
 ('Exterior Painting', 'Kingscliff'): "Exterior paint takes a beating this close to the water, and Kingscliff's mix "
                                      'of weatherboard beach houses and rendered new builds each need a different '
                                      'approach. We prep thoroughly for salt exposure so the finish actually lasts.',
 ('Roof Painting', 'Kingscliff'): 'Coastal roofs around Kingscliff cop rust and fading faster than inland areas, '
                                  'especially on older homes near the beach. A proper roof repaint protects the '
                                  'metal underneath as well as lifting the street appeal.',
 ('Limewash Painting', 'Kingscliff'): 'Limewash suits the relaxed coastal look a lot of Kingscliff and Casuarina '
                                      "homeowners are after, especially on brick and render near the beach. It's a "
                                      'finish we apply carefully to get that soft, textured result right.',
 ('Deck Painting', 'Kingscliff'): 'Between salt air and constant sun, decks in Kingscliff and along Cudgen Creek '
                                  'need coatings that can actually take the punishment. We prep and coat decks to '
                                  'handle bare feet, beach sand and coastal weather.',
 ('Kitchen Cabinet Painting', 'Kingscliff'): 'A lot of Kingscliff kitchens, especially in older beach houses, can be '
                                             'transformed without a full renovation. We spray or hand-finish '
                                             'cabinets on site for a durable result that suits either a classic '
                                             'beach house or a newer Salt precinct build.',
 ('Commercial Painters', 'Kingscliff'): 'From Salt precinct retail spaces to established Kingscliff businesses along '
                                        'Marine Parade, we handle commercial jobs with minimal disruption to trade. '
                                        'Scheduling works around your opening hours, not the other way around.',
 ('Epoxy Floors', 'Kingscliff'): 'Epoxy flooring is a newer addition to what we offer at Perma Painting, bringing '
                                 "the same attention to prep and finish we're known for across Kingscliff and the "
                                 "Tweed Coast to garages, alfresco areas and commercial floors. It's a durable "
                                 "option worth considering if you're renovating a Salt precinct build or upgrading "
                                 'an older beach house.',
 ('Lead Paint Removal & Restoration', 'Kingscliff'): 'Older beach houses around Kingscliff built before the 1970s '
                                                     'can have lead-based paint under later coats, and it needs to '
                                                     'be handled properly before any repaint. We follow safe removal '
                                                     'and restoration practices so the job is done without '
                                                     'unnecessary risk.',
 ('House Painters', 'Tweed Heads'): 'Tweed Heads is one of the most established parts of the Tweed Coast, with older '
                                    'weatherboard and brick homes sitting alongside unit blocks near the river. We '
                                    "paint both with the same attention to prep, whether it's a single house or a "
                                    'strata job.',
 ('Interior Painting', 'Tweed Heads'): 'Interior jobs in Tweed Heads range from long-term family homes to units '
                                       'being freshened up for sale or rent. We work cleanly and efficiently so '
                                       "you're not out of your space longer than necessary.",
 ('Exterior Painting', 'Tweed Heads'): 'Established homes around Tweed Heads often have older render or weatherboard '
                                       'that needs proper prep before a repaint holds. We check for underlying '
                                       'issues first so the new coat actually lasts.',
 ('Roof Painting', 'Tweed Heads'): "A lot of Tweed Heads homes have roofs that haven't been touched in years, and "
                                   'river-side properties in particular show wear faster. We repaint to protect the '
                                   'roof, not just refresh the colour.',
 ('Limewash Painting', 'Tweed Heads'): 'Limewash gives older brick homes around Tweed Heads a softer, more '
                                       "contemporary look without a full render job. It's a finish that suits the "
                                       "area's established brick housing stock well.",
 ('Deck Painting', 'Tweed Heads'): 'Decks around Tweed Heads, especially those near the river, take a lot of '
                                   'moisture and sun exposure. We coat and seal properly so the timber underneath is '
                                   'protected, not just painted over.',
 ('Kitchen Cabinet Painting', 'Tweed Heads'): 'A lot of Tweed Heads kitchens, particularly in older homes and units, '
                                              'are solid but dated. Repainting the cabinets is a fast way to '
                                              'modernise without a full renovation.',
 ('Commercial Painters', 'Tweed Heads'): 'Tweed Heads has a solid base of local businesses along the main strip and '
                                         'near the border, and we work around trading hours to get commercial jobs '
                                         'done with minimal disruption. Strata approval and scheduling are handled '
                                         'as part of the job.',
 ('Epoxy Floors', 'Tweed Heads'): "We've recently added epoxy flooring to our services at Perma Painting, applying "
                                  "it with the same care we bring to every paint job across Tweed Heads. It's a "
                                  'strong option for garages, units with shared parking areas or commercial spaces '
                                  'near the border.',
 ('Lead Paint Removal & Restoration', 'Tweed Heads'): 'A lot of the established homes around Tweed Heads predate '
                                                      'modern paint standards, which means lead-based paint is a '
                                                      'real consideration before any repaint. We handle removal and '
                                                      'restoration safely, then finish with a proper repaint.',
 ('House Painters', 'Lismore'): "Lismore's mix of heritage homes in East Lismore and Girards Hill, flood-affected "
                                'properties, and established homes in Goonellabah means every job needs a slightly '
                                "different approach. We prep properly for each, whether it's heritage matching or "
                                'storm damage repair.',
 ('Interior Painting', 'Lismore'): 'Interior repaints in Lismore often follow flood repair work or simply refreshing '
                                   'an older heritage home in Girards Hill. We work carefully around existing '
                                   'features rather than painting over problems.',
 ('Exterior Painting', 'Lismore'): 'Exterior homes across North and South Lismore have often taken a battering from '
                                   "storms and flooding over the years, and Goonellabah's established brick and "
                                   'weatherboard stock needs its own care. We prep thoroughly so the new coat '
                                   'actually holds.',
 ('Roof Painting', 'Lismore'): 'A lot of Lismore roofs, particularly on older homes in North and South Lismore, show '
                               'rust and wear faster after years of storm exposure. We treat rust properly and coat '
                               'for long-term protection.',
 ('Limewash Painting', 'Lismore'): "Limewash suits Lismore's heritage brick homes particularly well, especially in "
                                   'East Lismore and Girards Hill where a softer, period-appropriate finish is often '
                                   "preferred over standard paint. It's a technique we apply carefully to get the "
                                   'texture right.',
 ('Deck Painting', 'Lismore'): "Decks on Lismore's older homes, particularly those that have seen flood or storm "
                               'exposure, need proper assessment before recoating. We check the timber first, then '
                               'coat for durability.',
 ('Kitchen Cabinet Painting', 'Lismore'): 'Many Lismore kitchens, especially in older Goonellabah and heritage '
                                          'homes, are solid but dated. Repainting cabinets is an affordable way to '
                                          'update the space without a full renovation.',
 ('Commercial Painters', 'Lismore'): "Lismore's CBD and surrounding business areas have faced their share of flood "
                                     'recovery work over recent years, and we handle commercial repaints with that '
                                     'history in mind. Scheduling works around your trading hours and any insurance '
                                     'or repair timelines.',
 ('Epoxy Floors', 'Lismore'): "Epoxy flooring is one of the newer services we've added at Perma Painting, and it's a "
                              'particularly practical option for Lismore garages and sheds that have dealt with '
                              'flood exposure over the years. It gives a durable, easy-to-clean surface that holds '
                              'up better than bare concrete.',
 ('Lead Paint Removal & Restoration', 'Lismore'): "Lead paint is a common issue in Lismore's heritage homes, "
                                                  'particularly in East Lismore and Girards Hill, where older layers '
                                                  'can sit beneath decades of repaints. We handle removal safely '
                                                  'before restoring the surface, which matters especially where '
                                                  'flood repairs have already disturbed old paintwork.',
 ('Epoxy Floors', 'Byron Bay'): "We've recently added epoxy flooring to our services at Perma Painting, bringing it "
                                "to Byron Bay alongside our core painting work. It's a practical option for garages, "
                                'studios and the growing number of commercial and hospitality fit-outs around town.',
 ('Lead Paint Removal & Restoration', 'Byron Bay'): 'Byron Bay has plenty of older cottages and heritage-character '
                                                    'homes where lead-based paint can still be present under later '
                                                    'coats. We handle removal and restoration safely before any '
                                                    'repaint goes on.',
 ('Epoxy Floors', 'Ballina'): "Epoxy flooring is a newer addition to what we offer at Perma Painting, and it's a "
                              'solid option for Ballina garages, sheds and commercial spaces near the river. We '
                              'apply it with the same prep standards we use on every paint job.',
 ('Lead Paint Removal & Restoration', 'Ballina'): 'A number of established homes around Ballina predate modern paint '
                                                  'standards, particularly closer to the town centre and river. We '
                                                  'handle lead paint removal safely, then restore the surface ready '
                                                  'for a proper repaint.',
 ('Epoxy Floors', 'Mullumbimby'): "We've recently added epoxy flooring to our services at Perma Painting, and it "
                                  "suits Mullumbimby's mix of older Queenslanders with garages and sheds underneath, "
                                  "as well as the town's growing number of studio and commercial spaces. It's "
                                  'applied with the same care as our painting work.',
 ('Lead Paint Removal & Restoration', 'Mullumbimby'): "Mullumbimby's older Queenslanders and heritage-character "
                                                      'homes are exactly the kind of properties where lead-based '
                                                      'paint often turns up under later coats. We remove it safely '
                                                      'and restore the surface before any repaint.'})

META_DESCS.update({('House Painters', 'Kingscliff'): 'House painters in Kingscliff for new builds, beach houses and renovations. '
                                   'Salt-air rated finishes, free quotes, fully insured local crews.',
 ('Interior Painting', 'Kingscliff'): 'Interior painting in Kingscliff and Salt Village. Fast turnarounds for '
                                      'holiday rentals and family homes, free quote in under a minute.',
 ('Exterior Painting', 'Kingscliff'): 'Exterior house painting in Kingscliff. Salt-air rated coatings for '
                                      'weatherboard and rendered homes, free quote, fully insured.',
 ('Roof Painting', 'Kingscliff'): 'Roof painting in Kingscliff for coastal homes. Rust treatment and salt-air rated '
                                  'coatings, free quote from a local crew.',
 ('Limewash Painting', 'Kingscliff'): 'Limewash painting in Kingscliff for a coastal, textured finish on brick and '
                                      'render. Free quote from an experienced local team.',
 ('Deck Painting', 'Kingscliff'): 'Deck painting and staining in Kingscliff. Coastal-rated coatings built for salt '
                                  'air and sun, free quote available.',
 ('Kitchen Cabinet Painting', 'Kingscliff'): 'Kitchen cabinet painting in Kingscliff. Refresh your kitchen without a '
                                             'full renovation, free quote from a local crew.',
 ('Commercial Painters', 'Kingscliff'): 'Commercial painters in Kingscliff for retail, hospitality and office '
                                        'spaces. Free quote, fully insured, flexible scheduling.',
 ('Epoxy Floors', 'Kingscliff'): 'Epoxy flooring in Kingscliff from Perma Painting. Durable garage, alfresco and '
                                 'commercial floor coatings, free quote from a trusted local team.',
 ('Lead Paint Removal & Restoration', 'Kingscliff'): 'Lead paint removal and restoration in Kingscliff. Safe '
                                                     'handling for older homes, free quote from an experienced local '
                                                     'team.',
 ('House Painters', 'Tweed Heads'): 'House painters in Tweed Heads for established homes and unit blocks. Free '
                                    'quote, fully insured local crews.',
 ('Interior Painting', 'Tweed Heads'): 'Interior painting in Tweed Heads for homes and units. Free quote, tidy work, '
                                       'experienced local painters.',
 ('Exterior Painting', 'Tweed Heads'): 'Exterior painting in Tweed Heads for older homes and rendered properties. '
                                       'Free quote, thorough prep, fully insured.',
 ('Roof Painting', 'Tweed Heads'): 'Roof painting in Tweed Heads for established homes. Rust treatment, proper prep, '
                                   'free quote from a local crew.',
 ('Limewash Painting', 'Tweed Heads'): 'Limewash painting in Tweed Heads for brick homes. A softer, textured finish, '
                                       'free quote from an experienced team.',
 ('Deck Painting', 'Tweed Heads'): 'Deck painting and staining in Tweed Heads. Moisture and sun-rated coatings, free '
                                   'quote available.',
 ('Kitchen Cabinet Painting', 'Tweed Heads'): 'Kitchen cabinet painting in Tweed Heads. Modernise your kitchen '
                                              'without a renovation, free quote from a local crew.',
 ('Commercial Painters', 'Tweed Heads'): 'Commercial painters in Tweed Heads for retail and office spaces. Free '
                                         'quote, flexible scheduling, fully insured.',
 ('Epoxy Floors', 'Tweed Heads'): 'Epoxy flooring in Tweed Heads from Perma Painting. Durable coatings for garages, '
                                  'units and commercial floors, free quote available.',
 ('Lead Paint Removal & Restoration', 'Tweed Heads'): 'Lead paint removal and restoration in Tweed Heads. Safe '
                                                      'handling for older homes, free quote from a local crew.',
 ('House Painters', 'Lismore'): 'House painters in Lismore for heritage homes, flood repairs and established '
                                'properties. Free quote, fully insured local crews.',
 ('Interior Painting', 'Lismore'): 'Interior painting in Lismore for heritage and flood-affected homes. Free quote, '
                                   'careful local work.',
 ('Exterior Painting', 'Lismore'): 'Exterior painting in Lismore for storm-affected and established homes. Thorough '
                                   'prep, free quote, fully insured.',
 ('Roof Painting', 'Lismore'): 'Roof painting in Lismore for storm-affected and established homes. Rust treatment, '
                               'free quote from a local crew.',
 ('Limewash Painting', 'Lismore'): 'Limewash painting in Lismore for heritage brick homes. Period-appropriate '
                                   'finish, free quote from an experienced team.',
 ('Deck Painting', 'Lismore'): 'Deck painting and staining in Lismore. Careful assessment for storm-affected timber, '
                               'free quote available.',
 ('Kitchen Cabinet Painting', 'Lismore'): 'Kitchen cabinet painting in Lismore. Update your kitchen without a '
                                          'renovation, free quote from a local crew.',
 ('Commercial Painters', 'Lismore'): 'Commercial painters in Lismore for retail, office and flood-recovery repaints. '
                                     'Free quote, fully insured, flexible scheduling.',
 ('Epoxy Floors', 'Lismore'): 'Epoxy flooring in Lismore from Perma Painting. Durable, flood-resistant garage and '
                              'shed coatings, free quote from a local team.',
 ('Lead Paint Removal & Restoration', 'Lismore'): 'Lead paint removal and restoration in Lismore for heritage homes. '
                                                  'Safe handling, free quote from an experienced local team.',
 ('Epoxy Floors', 'Byron Bay'): 'Epoxy flooring in Byron Bay from Perma Painting. Durable garage, studio and '
                                'commercial floor coatings, free quote from a trusted local team.',
 ('Lead Paint Removal & Restoration', 'Byron Bay'): 'Lead paint removal and restoration in Byron Bay. Safe handling '
                                                    'for older and heritage-character homes, free quote from a local '
                                                    'team.',
 ('Epoxy Floors', 'Ballina'): 'Epoxy flooring in Ballina from Perma Painting. Durable garage, shed and commercial '
                              'floor coatings, free quote from a local team.',
 ('Lead Paint Removal & Restoration', 'Ballina'): 'Lead paint removal and restoration in Ballina. Safe handling for '
                                                  'older homes, free quote from an experienced local team.',
 ('Epoxy Floors', 'Mullumbimby'): 'Epoxy flooring in Mullumbimby from Perma Painting. Durable garage, studio and '
                                  'commercial floor coatings, free quote from a local team.',
 ('Lead Paint Removal & Restoration', 'Mullumbimby'): 'Lead paint removal and restoration in Mullumbimby for older '
                                                      'Queenslanders and heritage homes. Free quote from a local '
                                                      'team.'})

FAQS.update({('House Painters', 'Kingscliff'): [('Do you paint new builds in the Salt precinct?',
                                     'Yes, we regularly work on new homes in Salt Village and can coordinate '
                                     'directly with builders on handover timing.'),
                                    ('How do you handle salt air near the coast?',
                                     'We use coatings rated for coastal exposure and pay extra attention to prep on '
                                     'any home within a few streets of the beach.'),
                                    ('Do you service Casuarina and Cudgen as well?',
                                     'Yes, Casuarina, Cudgen, Bogangar and Pottsville are all part of our regular '
                                     'Kingscliff coverage.')],
 ('Interior Painting', 'Kingscliff'): [('Can you paint between holiday rental bookings?',
                                        'Yes, we work with several Kingscliff rental owners and can schedule tight '
                                        'turnarounds between guest stays.'),
                                       ('Do you offer colour advice for new builds?',
                                        'Yes, we can talk through colour schemes that suit the newer Salt precinct '
                                        'builds or a more classic beach house feel.'),
                                       ('How long does an average interior repaint take?',
                                        'Most three to four bedroom homes in Kingscliff take two to three days '
                                        'depending on prep needed.')],
 ('Exterior Painting', 'Kingscliff'): [('Does salt air really affect how long paint lasts?',
                                        'Yes, homes within a few streets of the beach need coatings and prep '
                                        'specifically suited to coastal exposure or the paint fails early.'),
                                       ('Do you paint rendered homes in Salt Village?',
                                        'Yes, we regularly quote rendered exteriors on the newer builds in that '
                                        'precinct.'),
                                       ("What's the best time of year to repaint in Kingscliff?",
                                        'We work year-round, though drier stretches make scheduling easier for '
                                        'larger exterior jobs.')],
 ('Roof Painting', 'Kingscliff'): [('Do you treat rust before painting?',
                                    'Yes, rust treatment and proper prep is standard on every roof job, particularly '
                                    'this close to the coast.'),
                                   ('How often should a Kingscliff roof be repainted?',
                                    'Coastal exposure generally means recoating every seven to ten years, sooner on '
                                    'older colorbond roofs.'),
                                   ('Can you match the roof colour to my Salt precinct build?',
                                    'Yes, we can match or advise on colours that suit newer estate guidelines where '
                                    'they apply.')],
 ('Limewash Painting', 'Kingscliff'): [('What surfaces work best for limewash in Kingscliff?',
                                        'Brick and render both take limewash well, which suits a lot of the beach '
                                        'house exteriors around here.'),
                                       ('Does limewash hold up to salt air?',
                                        'Yes, when applied and sealed properly it performs well in coastal '
                                        'conditions.'),
                                       ('Can I see examples before committing?',
                                        "Yes, we're happy to talk through recent limewash work in the area before "
                                        'you decide.')],
 ('Deck Painting', 'Kingscliff'): [('How often do coastal decks need recoating?',
                                    'Generally every one to two years depending on sun exposure and foot traffic.'),
                                   ('Do you stain as well as paint decks?',
                                    'Yes, we offer both staining and solid coatings depending on the timber and look '
                                    'you want.'),
                                   ("Can you fix a deck that's already peeling?",
                                    'Yes, we assess the existing coating and prep properly before recoating so it '
                                    "doesn't just peel again.")],
 ('Kitchen Cabinet Painting', 'Kingscliff'): [('Do you paint cabinets on site or take them away?',
                                               'We generally work on site, which keeps disruption to your Kingscliff '
                                               'home to a minimum.'),
                                              ('What finish do you recommend for kitchens?',
                                               "A durable, wipeable finish that holds up to daily use, we'll talk "
                                               'you through options during the quote.'),
                                              ('How long does a kitchen cabinet repaint take?',
                                               'Most kitchens take two to three days including drying time between '
                                               'coats.')],
 ('Commercial Painters', 'Kingscliff'): [('Can you work outside trading hours?',
                                          'Yes, we regularly schedule commercial jobs early morning, evenings or '
                                          'weekends to avoid disrupting your business.'),
                                         ('Do you handle strata-approved colour schemes?',
                                          'Yes, we can work within body corporate or landlord colour requirements '
                                          'where they apply.'),
                                         ('Do you quote for new commercial fit-outs in Salt Village?',
                                          'Yes, we work with several businesses opening in that precinct.')],
 ('Epoxy Floors', 'Kingscliff'): [('Is epoxy flooring suitable for garages exposed to salt air?',
                                   'Yes, once the concrete is properly prepped and sealed, epoxy holds up well in '
                                   "coastal conditions like Kingscliff's."),
                                  ('What areas of the home suit epoxy flooring?',
                                   'Garages, alfresco spaces and workshops are common choices, and we can talk '
                                   'through whether it suits your space during a quote.'),
                                  ('Can I get pricing over the phone?',
                                   'Every epoxy job is quoted individually based on floor size and condition, so '
                                   "we'll arrange a proper assessment first.")],
 ('Lead Paint Removal & Restoration', 'Kingscliff'): [('How do I know if my home has lead paint?',
                                                       'Homes built before the 1970s are the main risk, and we can '
                                                       'talk through testing options as part of the quote.'),
                                                      ('Is lead paint removal safe to do myself?',
                                                       "We'd recommend against it, disturbing lead paint without "
                                                       'proper containment can create health risks, which is why we '
                                                       'follow safe removal practices.'),
                                                      ('Do you also handle the repaint after removal?',
                                                       'Yes, restoration and repainting is part of the same process '
                                                       'once the surface is safely prepped.')],
 ('House Painters', 'Tweed Heads'): [('Do you work on older weatherboard homes?',
                                      'Yes, matching and restoring older weatherboard finishes is common work for us '
                                      'around Tweed Heads.'),
                                     ('Can you quote for unit blocks near the river?',
                                      'Yes, we regularly quote strata and unit exteriors in that area.'),
                                     ('Do you service Banora Point and Terranora too?',
                                      'Yes, both are part of our regular Tweed Heads coverage.')],
 ('Interior Painting', 'Tweed Heads'): [('Do you paint units as well as houses?',
                                         'Yes, we regularly repaint units around Tweed Heads, including for owners '
                                         'preparing to sell or lease.'),
                                        ('Can you match existing colours in an older home?',
                                         'Yes, colour matching on established homes is something we do often in this '
                                         'area.'),
                                        ('How much notice do you need to book in?',
                                         'Generally a couple of weeks, though we can sometimes fit in shorter notice '
                                         'jobs depending on the season.')],
 ('Exterior Painting', 'Tweed Heads'): [('My render has cracks, can you still paint over it?',
                                         "We assess and repair render issues as part of the job so the paint doesn't "
                                         'just fail again shortly after.'),
                                        ('Do you paint unit block exteriors?',
                                         'Yes, exterior strata work is common for us in Tweed Heads.'),
                                        ('How long does an exterior repaint usually take?',
                                         'Most standalone homes take three to five days depending on size and '
                                         'condition.')],
 ('Roof Painting', 'Tweed Heads'): [('How do I know if my roof needs painting or replacing?',
                                     'We assess the roof during the quote and will tell you honestly if a repaint '
                                     "isn't the right fix."),
                                    ('Do you handle rust spots before coating?',
                                     'Yes, rust treatment is standard prep on every roof job we do.'),
                                    ('Can you paint tile roofs as well as metal?',
                                     'Yes, we work with both tile and colorbond roofing.')],
 ('Limewash Painting', 'Tweed Heads'): [('Does limewash work on older brick?',
                                         "Yes, older brick actually takes limewash very well, and it's a popular "
                                         'option for updating established Tweed Heads homes.'),
                                        ('Is limewash a permanent finish?',
                                         "It's durable but does weather naturally over time, which is part of its "
                                         'character.'),
                                        ('Can you show me examples locally?',
                                         'Yes, we can talk through recent limewash jobs in the area before you '
                                         'decide.')],
 ('Deck Painting', 'Tweed Heads'): [('My deck is near the water, does that change how you paint it?',
                                     'Yes, river-facing decks get extra attention to moisture protection during prep '
                                     'and coating.'),
                                    ('Do you repair timber before painting?',
                                     'We flag any timber issues during the quote and can arrange repairs before '
                                     'coating.'),
                                    ('How long before I can use the deck again?',
                                     'Usually one to two days after the final coat, weather depending.')],
 ('Kitchen Cabinet Painting', 'Tweed Heads'): [('Can you paint laminate cabinets?',
                                                'Yes, with the right prep and primer laminate cabinets take paint '
                                                'well.'),
                                               ('Do I need to empty the kitchen fully?',
                                                "We'll ask you to clear the benches and cupboard contents, we handle "
                                                'the rest.'),
                                               ("What's the typical cost range?",
                                                "It depends on the kitchen size and cabinet material, we'll give you "
                                                'a clear quote after assessing it.')],
 ('Commercial Painters', 'Tweed Heads'): [('Do you work with strata or body corporate approvals?',
                                           "Yes, we're used to working within body corporate requirements for "
                                           'commercial and unit block jobs.'),
                                          ('Can you paint after hours?',
                                           'Yes, we can schedule around your trading hours to avoid disrupting '
                                           'business.'),
                                          ('Do you handle larger commercial fit-outs?',
                                           "Yes, get in touch with the scope and we'll put together a detailed "
                                           'quote.')],
 ('Epoxy Floors', 'Tweed Heads'): [('Can epoxy flooring handle moisture near the river?',
                                    'Yes, properly applied epoxy is moisture resistant, which suits garages and '
                                    'lower-level spaces closer to the water.'),
                                   ('Do you do epoxy for strata or shared parking areas?',
                                    'Yes, we can quote shared or strata-managed spaces, get in touch with the '
                                    'details.'),
                                   ('How long does epoxy flooring take to cure?',
                                    "Cure times vary depending on the product and floor condition, we'll walk you "
                                    'through timing at the quote stage.')],
 ('Lead Paint Removal & Restoration', 'Tweed Heads'): [('Which Tweed Heads homes are most likely to have lead paint?',
                                                        'Generally homes built before the 1970s, which is common '
                                                        "among the area's older established housing."),
                                                       ('What does the removal process involve?',
                                                        'Safe containment and removal of the old paint layer before '
                                                        'any surface prep or repainting begins.'),
                                                       ('Can you also do the repaint afterwards?',
                                                        'Yes, restoration and repainting are handled as part of the '
                                                        'same job.')],
 ('House Painters', 'Lismore'): [('Do you handle flood-damaged homes?',
                                  'Yes, we regularly repaint homes affected by flood or storm damage across Lismore, '
                                  'prepping surfaces properly first.'),
                                 ('Can you match heritage colours in East Lismore?',
                                  'Yes, we check heritage guidelines where they apply and match existing schemes on '
                                  'request.'),
                                 ('Do you service Goonellabah as well?',
                                  'Yes, Goonellabah is part of our regular Lismore coverage.')],
 ('Interior Painting', 'Lismore'): [('Can you paint over walls affected by past water damage?',
                                     "We check for underlying moisture issues first, we don't just paint over a "
                                     'problem that will resurface.'),
                                    ('Do you work on heritage interiors?',
                                     "Yes, we're careful with original features like skirtings and cornices in older "
                                     'East Lismore and Girards Hill homes.'),
                                    ('How soon can you start after a flood clean-up?',
                                     'Once surfaces are properly dried and repaired we can schedule in, timing '
                                     'depends on the extent of the damage.')],
 ('Exterior Painting', 'Lismore'): [('Do you repair damage before painting the exterior?',
                                     'Yes, we assess and repair any storm or flood-related damage as part of the '
                                     'job.'),
                                    ('Can you match weatherboard finishes in Goonellabah?',
                                     'Yes, matching existing weatherboard and brick finishes is common work for us '
                                     'in that area.'),
                                    ('How long does an exterior job typically take?',
                                     'Most homes take three to five days depending on size and prep needed.')],
 ('Roof Painting', 'Lismore'): [('Do you treat rust on older roofs?',
                                 'Yes, rust treatment and proper prep is standard on every roof job we quote.'),
                                ('Can a roof repaint help after storm damage?',
                                 "A repaint protects the metal once any structural damage has been fixed, we'll "
                                 'advise honestly if repairs are needed first.'),
                                ('Do you service acreage properties toward Wyrallah?',
                                 'Yes, rural and acreage properties in that area are part of our regular coverage.')],
 ('Limewash Painting', 'Lismore'): [('Is limewash suitable for heritage-listed homes?',
                                     'In many cases yes, though we always recommend checking any heritage '
                                     'requirements first, which we can help with.'),
                                    ("Does limewash suit East Lismore's older brick homes?",
                                     "Yes, it's a popular choice there for a softer, more traditional look."),
                                    ('How does limewash hold up over time?',
                                     'It weathers naturally, which is part of the appeal, and can be refreshed as '
                                     'needed.')],
 ('Deck Painting', 'Lismore'): [('Can you assess flood-damaged decking?',
                                 'Yes, we check timber condition first and will advise honestly if repairs are '
                                 'needed before painting.'),
                                ('Do you offer staining as well as solid paint finishes?',
                                 "Yes, we offer both depending on the timber and the look you're after."),
                                ('How often should Lismore decks be recoated?',
                                 'Generally every one to two years, though exposure and past water damage can '
                                 'shorten that.')],
 ('Kitchen Cabinet Painting', 'Lismore'): [('Can you paint older timber cabinets?',
                                            "Yes, older solid timber cabinets, common in Lismore's established "
                                            'homes, take paint particularly well.'),
                                           ('Do you work around flood-related kitchen repairs?',
                                            'Yes, if cabinets have been replaced or repaired after flood damage we '
                                            'can paint once everything is properly dry and prepped.'),
                                           ('How long does a typical kitchen take?',
                                            'Most kitchens take two to three days including drying time between '
                                            'coats.')],
 ('Commercial Painters', 'Lismore'): [('Do you handle flood-recovery commercial repaints?',
                                       "Yes, we've worked with several Lismore businesses on repaints as part of "
                                       'their flood recovery.'),
                                      ('Can you work with insurance assessors or timelines?',
                                       'Yes, we can coordinate scheduling around insurance or repair processes where '
                                       'needed.'),
                                      ('Do you work outside business hours?',
                                       'Yes, we can schedule early mornings, evenings or weekends to minimise '
                                       'disruption to trade.')],
 ('Epoxy Floors', 'Lismore'): [('Is epoxy flooring suitable for flood-affected garages?',
                                "It's a durable option once the floor is properly assessed and prepped, we can "
                                'advise honestly during the quote.'),
                               ('How long does an epoxy floor typically last?',
                                'A well-applied epoxy floor generally lasts eight to ten years before recoating is '
                                'needed, depending on use.'),
                               ('Can epoxy be applied over an existing concrete floor?',
                                'In most cases yes, subject to an assessment of the current surface condition.')],
 ('Lead Paint Removal & Restoration', 'Lismore'): [('Is lead paint common in East Lismore and Girards Hill?',
                                                    'Yes, older homes in those areas were often built before the '
                                                    '1970s, when lead-based paint was standard.'),
                                                   ('Does flood damage make lead paint more of a risk?',
                                                    "Water damage can disturb old paint layers, so it's worth having "
                                                    'it assessed as part of any flood-related repair work.'),
                                                   ('Do you handle both removal and the final repaint?',
                                                    'Yes, we manage the full process from safe removal through to '
                                                    'restoration and repainting.')],
 ('Epoxy Floors', 'Byron Bay'): [('Does epoxy suit older concrete garages?',
                                  "Yes, older concrete can usually be prepped for epoxy, we'll assess the surface as "
                                  'part of the quote.'),
                                 ('Do you do epoxy for commercial or hospitality spaces?',
                                  'Yes, we quote retail, studio and hospitality floors as well as residential '
                                  'garages.'),
                                 ('Can I get a price without a site visit?',
                                  "Every epoxy job depends on floor size and condition, so we'll need to assess it "
                                  'properly before quoting.')],
 ('Lead Paint Removal & Restoration', 'Byron Bay'): [('Which Byron Bay homes are most likely to have lead paint?',
                                                      'Generally older cottages and heritage-character homes built '
                                                      'before the 1970s.'),
                                                     ('Is it safe to sand or scrape old paint myself?',
                                                      "We'd recommend against it, disturbing lead paint without "
                                                      'proper containment carries health risks.'),
                                                     ('Do you handle the repaint after removal?',
                                                      'Yes, restoration and repainting are part of the same job once '
                                                      'the surface is safely prepped.')],
 ('Epoxy Floors', 'Ballina'): [('How durable is epoxy compared to a painted floor?',
                                'Epoxy is significantly more durable and easier to clean than a standard painted '
                                'concrete floor, which is why it suits garages and sheds.'),
                               ('Is epoxy suitable for sheds as well as garages?',
                                "Yes, it's a durable option for both, we can assess your space as part of the "
                                'quote.'),
                               ('How long does the floor need to cure before use?',
                                "Cure times depend on the product and conditions, we'll talk you through timing at "
                                'the quote stage.')],
 ('Lead Paint Removal & Restoration', 'Ballina'): [('How do I know if my Ballina home might have lead paint?',
                                                    'Homes built before the 1970s are the main risk, we can talk '
                                                    'through testing options during the quote.'),
                                                   ('What does the removal process involve?',
                                                    'Safe containment and removal of the old paint layer before any '
                                                    'surface prep or repainting begins.'),
                                                   ('Can you do the repaint straight after?',
                                                    'Yes, restoration and repainting are handled as part of the same '
                                                    'job.')],
 ('Epoxy Floors', 'Mullumbimby'): [('Can epoxy flooring handle high foot traffic in a workshop?',
                                    "Yes, it's a popular choice for workshops and studios because it holds up well "
                                    'to regular use.'),
                                   ('Does epoxy suit the space under a Queenslander-style home?',
                                    'Yes, those under-house areas are a common spot for epoxy flooring, we can '
                                    'assess yours during the quote.'),
                                   ('Do you handle commercial floors in the Mullumbimby CBD?',
                                    'Yes, we quote retail and studio spaces as well as residential jobs.')],
 ('Lead Paint Removal & Restoration', 'Mullumbimby'): [("Are Mullumbimby's Queenslanders likely to have lead paint?",
                                                        'Many were built before the 1970s, when lead-based paint was '
                                                        "standard, so it's worth having checked."),
                                                       ('Is DIY removal a bad idea?',
                                                        'Yes, disturbing lead paint without proper containment can '
                                                        'create health risks, which is why we handle it safely.'),
                                                       ('Do you also do the restoration and repaint?',
                                                        "Yes, that's part of the same process once the surface is "
                                                        'safely prepped.')]})


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


def available_fallback(src: str) -> str:
    """Devuelve el raster pedido o su WebP equivalente si el JPG fue retirado."""
    if (ROOT / src).exists():
        return src
    webp = webp_src(src)
    if (ROOT / webp).exists():
        return webp
    raise FileNotFoundError(f"No existe el asset ni su WebP: {src}")


@lru_cache(maxsize=None)
def image_dimensions(src: str) -> tuple[int, int]:
    # La migración a WebP retiró varios JPG. Medimos el formato que realmente
    # existe y available_fallback() evita que el HTML apunte a archivos ausentes.
    src = available_fallback(src)

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
    sl = html_lib.escape(service["name"].lower())
    zone_html = html_lib.escape(zone)
    # alt variados por foto, todos con la zona
    alts = [
        f"{sl} in {zone_html}",
        f"{sl} project in {zone_html}",
        f"{sl} work in {zone_html}",
        f"professional {sl} in {zone_html}",
    ]
    delays = ["0s", "0.12s", "0.24s", "0.36s"]
    rows = []
    for i in range(4):
        n = f"{i+1:03d}"
        src = f"assets/photos/{pdir}/{prefix}_{n}.jpg"
        fallback = available_fallback(src)
        width, height = image_dimensions(src)
        rows.append(
            f'                <figure class="landing-gallery__card os-reveal" style="--reveal-delay: {delays[i]}">\n'
            f'                    <picture class="landing-gallery__picture">\n'
            f'                        <source srcset="{webp_src(src)}" type="image/webp">\n'
            f'                        <img src="{fallback}" alt="{alts[i]}"\n'
            f'                            class="landing-gallery__img" width="{width}" height="{height}" loading="lazy" decoding="async">\n'
            f'                    </picture>\n'
            f'                </figure>'
        )
    return "\n\n".join(rows)


_GENERIC_HERO_PRELOAD = (
    '    <link rel="preload" as="image" type="image/webp" fetchpriority="high"\n'
    '        href="assets/photos/landing-hero/landing_005-600.webp"\n'
    '        imagesrcset="assets/photos/landing-hero/landing_005-600.webp 600w, assets/photos/landing-hero/landing_005-720.webp 720w, assets/photos/landing-hero/landing_005-900.webp 900w, assets/photos/landing-hero/landing_005.webp 1296w"\n'
    '        imagesizes="(max-width: 768px) calc(100vw - 2.4rem), 50vw">'
)


def hero_preload_html(service: dict) -> str:
    """<link rel=preload> del hero. Foto propia del servicio si hay "hero",
    si no la genérica landing_005 (comportamiento histórico)."""
    hero = service.get("hero")
    if not hero:
        return _GENERIC_HERO_PRELOAD
    webp = f"assets/photos/{hero}.webp"
    return (
        '    <link rel="preload" as="image" type="image/webp" fetchpriority="high"\n'
        f'        href="{webp}">'
    )


def hero_picture_html(service: dict, zone: str) -> str:
    """Bloque .landing-hero__right. Foto propia del servicio si hay "hero",
    si no la genérica landing_005 (comportamiento histórico, sin cambios)."""
    sl = html_lib.escape(service["name"].lower())
    alt = f"{sl} in {html_lib.escape(zone)}"
    hero = service.get("hero")

    if not hero:
        return (
            '                <div class="landing-hero__right">\n'
            '                    <div class="hero__right--photo-container">\n'
            '                        <picture class="hero__right--photo-picture">\n'
            '                            <source\n'
            '                                srcset="assets/photos/landing-hero/landing_005-600.webp 600w, assets/photos/landing-hero/landing_005-720.webp 720w, assets/photos/landing-hero/landing_005-900.webp 900w, assets/photos/landing-hero/landing_005.webp 1296w"\n'
            '                                sizes="(max-width: 768px) calc(100vw - 2.4rem), 50vw" type="image/webp">\n'
            f'                            <img src="assets/photos/landing-hero/landing_005.jpg" alt="{alt}"\n'
            '                                srcset="assets/photos/landing-hero/landing_005-600.jpg 600w, assets/photos/landing-hero/landing_005-720.jpg 720w, assets/photos/landing-hero/landing_005-900.jpg 900w, assets/photos/landing-hero/landing_005.jpg 1296w"\n'
            '                                sizes="(max-width: 768px) calc(100vw - 2.4rem), 50vw" class="hero__right--photo"\n'
            '                                width="1296" height="1296" fetchpriority="high">\n'
            '                        </picture>\n'
            '                    </div>\n'
            '                </div>'
        )

    jpg = f"assets/photos/{hero}.jpg"
    webp = f"assets/photos/{hero}.webp"
    fallback = available_fallback(jpg)
    width, height = image_dimensions(jpg)
    return (
        '                <div class="landing-hero__right">\n'
        '                    <div class="hero__right--photo-container">\n'
        '                        <picture class="hero__right--photo-picture">\n'
        f'                            <source srcset="{webp}" type="image/webp">\n'
        f'                            <img src="{fallback}" alt="{alt}" class="hero__right--photo"\n'
        f'                                width="{width}" height="{height}" fetchpriority="high">\n'
        '                        </picture>\n'
        '                    </div>\n'
        '                </div>'
    )


def nearby_of(zone: str) -> list[str]:
    """Localidades cercanas. Las zonas viejas viven en NEARBY; las nuevas
    (NEW_ZONES) traen su lista dentro de NEW_ZONE_DATA."""
    if zone in NEARBY:
        return NEARBY[zone]
    return NEW_ZONE_DATA[zone]["nearby"]


def pills_html(zone: str) -> str:
    rows = [
        f'                    <li class="landing-area__pill">{html_lib.escape(loc)}</li>'
        for loc in nearby_of(zone)
    ]
    return "\n".join(rows)


def faq_html(service: str, zone: str) -> str:
    """details/summary nativo. FAQ propio de cada (servicio, zona)."""
    items = []
    for q, a in FAQS[(service, zone)]:
        q = html_lib.escape(q.format(zone=zone))
        a = html_lib.escape(a.format(zone=zone))
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
    """Los otros servicios de la misma zona."""
    rows = []
    for s in SERVICES:
        if s["name"] == current_service:
            continue
        slug = page_slug(s["name"], zone)
        rows.append(
            f'                        <li><a class="landing-links__link" href="{slug}.html">'
            f'<span>{html_lib.escape(s["name"])}</span>'
            f'<span class="landing-links__arrow" aria-hidden="true">→</span></a></li>'
        )
    return "\n".join(rows)


def crosslinks_zones_html(service: str, current_zone: str) -> str:
    """El mismo servicio en las otras zonas de su grupo de publicación."""
    rows = []
    for z in ZONES:
        if z == current_zone:
            continue
        slug = page_slug(service, z)
        rows.append(
            f'                        <li><a class="landing-links__link" href="{slug}.html">'
            f'<span>{html_lib.escape(service)} in {html_lib.escape(z)}</span>'
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

def render_landing(template: str, service: dict, zone: str) -> tuple[str, str]:
    """Devuelve (slug, html) de una landing de servicio.
    La usan tanto las 24 de siempre como las de las zonas nuevas: mismo
    template-landing.html, mismos datos, solo cambia quién la llama."""
    sname = service["name"]
    sname_html = html_lib.escape(sname)
    zone_html = html_lib.escape(zone)
    slug = page_slug(sname, zone)
    intro = INTROS[(sname, zone)]

    page = template
    replacements = {
        "{{META_TITLE}}": f"{sname_html} in {zone_html} | Perma Painting",
        "{{META_DESCRIPTION}}": html_lib.escape(META_DESCS[(sname, zone)], quote=True),
        "{{DOMAIN}}": DOMAIN,
        "{{SLUG}}": slug,
        "{{HERO_PRELOAD}}": hero_preload_html(service),
        "{{HERO_PICTURE}}": hero_picture_html(service, zone),
        "{{SERVICE}}": sname_html,
        "{{SERVICE_LOWER}}": html_lib.escape(sname.lower()),
        # "Roof Painting" -> "Roof painting" (solo 1ra letra mayúscula)
        "{{SERVICE_LOWER_CAP}}": html_lib.escape(sname[0] + sname[1:].lower()),
        "{{ZONE}}": zone_html,
        "{{INTRO}}": html_lib.escape(intro),
        "{{CTA_TEXT}}": html_lib.escape(CTA_TEXTS[sname]),
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

    return slug, page


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    count = 0

    for service in SERVICES:
        for zone in ZONES:
            slug, page = render_landing(template, service, zone)
            (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
            count += 1
            print(f"  ✓ {slug}.html")

    expected = len(SERVICES) * len(ZONES)
    print(f"\n{count} landing pages de zonas originales generadas.")
    if count != expected:
        raise SystemExit(f"ERROR: se esperaban {expected} páginas, se generaron {count}")

    generate_new_zone_landings()

    generate_area_indexes()
    generate_new_area_indexes()
    generate_service_areas_page()


# ---------------------------------------------------------------------------
# LANDINGS DE SERVICIO DE LAS ZONAS NUEVAS
# Mismo template y misma función de render que las zonas originales: lo único
# distinto es la lista de zonas. Se generan aparte para no meter NEW_ZONES
# dentro de ZONES (eso cambiaría los crosslinks de las 24 páginas viejas).
# ---------------------------------------------------------------------------

def generate_new_zone_landings() -> None:
    if not NEW_ZONES:
        return

    template = TEMPLATE.read_text(encoding="utf-8")
    count = 0

    for service in SERVICES:
        for zone in NEW_ZONES:
            slug, page = render_landing(template, service, zone)
            (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
            count += 1
            print(f"  ✓ {slug}.html")

    expected = len(SERVICES) * len(NEW_ZONES)
    print(f"{count} landings de zonas nuevas generadas.")
    if count != expected:
        raise SystemExit(f"ERROR: se esperaban {expected} páginas, se generaron {count}")

# ---------------------------------------------------------------------------
# ÍNDICES POR ZONA (AREAS OF SERVICE)
# Página simple por zona: solo título + links a los 10 servicios de esa zona.
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

        # links a los 10 servicios de esta zona
        rows = []
        for s in SERVICES:
            s_slug = page_slug(s["name"], zone)
            rows.append(
                f'                        <li><a class="landing-links__link" href="{s_slug}.html">'
                f'<span>{html_lib.escape(s["name"])}</span>'
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
                {"@type": "ListItem", "position": 2, "name": "Service Areas", "item": f"{DOMAIN}/service-areas"},
                {"@type": "ListItem", "position": 3, "name": zone},
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
            fallback = available_fallback(src)
            width, height = image_dimensions(src)
            area_map_html = (
                '                <div class="area-index__head-media">\n'
                '                    <div class="area-index__photo-container">\n'
                f'                        <picture class="area-index__photo-picture">\n'
                f'                            <source srcset="{webp_src(src)}" type="image/webp">\n'
                f'                            <img src="{fallback}"\n'
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



# ---------------------------------------------------------------------------
# ÍNDICES DE ZONA — ZONAS NUEVAS
# Cáscara común (template-area-shell.html) + un hero por modelo. El
# header/footer salen del template-landing, mismo criterio que
# generate_area_indexes(), para tener una sola fuente de verdad.
# ---------------------------------------------------------------------------

def jobs_badge_html(zone: str, number: str | None) -> str:
    """Badge circular con los trabajos hechos en la zona (modelo "local").
    Sin número no se renderiza: no inventamos la cifra."""
    if not number:
        return ""
    return (
        '                    <div class="area-local__badge">\n'
        f'                        <span class="area-local__badge-num">{number}</span>\n'
        f'                        <span class="area-local__badge-label">Jobs completed in {zone}</span>\n'
        '                    </div>\n'
    )


_PIN_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 21s7-6.1 7-12a7 7 0 1 0-14 0c0 5.9 7 12 7 12z"/>'
    '<circle cx="12" cy="9" r="2.3"/></svg>'
)


def local_knowledge_html(items: list[str]) -> str:
    return "\n".join(
        f'                        <li class="area-local__knowledge-item">{_PIN_ICON}<span>{item}</span></li>'
        for item in items
    )


def area_faq_html(faqs: list[tuple[str, str]]) -> str:
    """FAQ de una ZONA (no de un servicio). Mismo markup que faq_html()."""
    items = []
    for q, a in faqs:
        items.append(
            f'                        <details class="landing-faq__item">\n'
            f'                            <summary class="landing-faq__question">{q}</summary>\n'
            f'                            <div class="landing-faq__answer">\n'
            f'                                <p>{a}</p>\n'
            f'                            </div>\n'
            f'                        </details>'
        )
    return "\n\n".join(items)


def schema_area_faq_block(faqs: list[tuple[str, str]]) -> str:
    """Bloque <script> con el schema FAQPage, o vacío si la zona no tiene FAQ.
    Usa el mismo texto visible, así no se desincronizan."""
    if not faqs:
        return ""
    main = [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in faqs
    ]
    data = json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": main},
        indent=8, ensure_ascii=False,
    )
    return (
        "\n    <!-- Schema: FAQPage (reusa el texto visible del FAQ de la zona) -->\n"
        "    <script type=\"application/ld+json\">\n"
        f"{data}\n"
        "    </script>"
    )


def generate_new_area_indexes() -> None:
    if not NEW_ZONES:
        return

    landing = TEMPLATE.read_text(encoding="utf-8")
    header = _extract('<header class="site-header"', "</header>", landing)
    footer = _extract('<footer class="site-footer"', "</footer>", landing)

    shell = (ROOT / "template-area-shell.html").read_text(encoding="utf-8")

    for zone in NEW_ZONES:
        data = NEW_ZONE_DATA[zone]
        model = data["model"]
        slug = slugify(zone)

        hero = (ROOT / AREA_HERO_TEMPLATES[model]).read_text(encoding="utf-8")
        page = shell.replace("{{AREA_HERO}}", hero.rstrip("\n"))

        # links a los 10 servicios de esta zona
        service_links = "\n".join(
            f'                        <li><a class="landing-links__link" href="{page_slug(s["name"], zone)}.html">'
            f'<span>{html_lib.escape(s["name"])}</span>'
            f'<span class="landing-links__arrow" aria-hidden="true">→</span></a></li>'
            for s in SERVICES
        )

        # localidades de la zona como pills (la zona primero)
        area_pills = "\n".join(
            f'                            <li class="landing-area__pill">{loc}</li>'
            for loc in [zone] + data["nearby"]
        )

        # otras zonas: las 3 viejas + las otras nuevas
        other_zone_links = "\n".join(
            f'                            <a class="area-index__zone-btn" href="{slugify(z)}.html">'
            f'<span>{z}</span>'
            f'<span class="area-index__zone-btn-arrow" aria-hidden="true">→</span></a>'
            for z in ZONES + [n for n in NEW_ZONES if n != zone]
        )

        breadcrumb = json.dumps({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": "Service Areas", "item": f"{DOMAIN}/service-areas"},
                {"@type": "ListItem", "position": 3, "name": zone},
            ],
        }, indent=8, ensure_ascii=False)

        replacements = {
            "{{HEADER}}": header,
            "{{FOOTER}}": footer,
            "{{META_TITLE}}": data["title"],
            "{{META_DESCRIPTION}}": data["meta"],
            "{{HEADLINE}}": data["headline"],
            "{{INTRO}}": data["intro"],
            "{{AREA_PILLS}}": area_pills,
            "{{SERVICE_LINKS}}": service_links,
            "{{OTHER_ZONE_LINKS}}": other_zone_links,
            "{{SCHEMA_BREADCRUMB}}": breadcrumb,
            "{{SCHEMA_FAQ_BLOCK}}": schema_area_faq_block(data.get("faqs", [])),
            "{{ZONE}}": zone,
            "{{SLUG}}": slug,
            "{{DOMAIN}}": DOMAIN,
        }

        if model == "quote":
            src = data["photo"]
            fallback = available_fallback(src)
            width, height = image_dimensions(src)
            replacements.update({
                "{{TRUST_ITEMS}}": "\n".join(
                    '                            <li class="area-quote__trust-item">\n'
                    '                                <span class="area-quote__trust-icon">'
                    f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">{TRUST_ICONS[icon]}</svg></span>\n'
                    f'                                <span class="area-quote__trust-label">{label}</span>\n'
                    '                            </li>'
                    for icon, label in data["trust"]
                ),
                "{{SERVICE_OPTIONS}}": "\n".join(
                    f'                                        <option>{html_lib.escape(s["name"])}</option>' for s in SERVICES
                ),
                "{{PHOTO}}": (
                    '                    <figure class="area-quote__photo">\n'
                    '                        <picture class="area-quote__photo-picture">\n'
                    f'                            <source srcset="{webp_src(src)}" type="image/webp">\n'
                    f'                            <img src="{fallback}" alt="{data["photo_alt"]}"\n'
                    f'                                class="area-quote__photo-img" width="{width}" height="{height}"\n'
                    '                                loading="lazy" decoding="async">\n'
                    '                        </picture>\n'
                    '                    </figure>'
                ),
            })
        elif model == "local":
            replacements.update({
                "{{JOBS_BADGE}}": jobs_badge_html(zone, data.get("jobs_badge")),
                "{{LOCAL_KNOWLEDGE}}": local_knowledge_html(data["local_knowledge"]),
                "{{AREA_FAQ}}": area_faq_html(data["faqs"]),
            })
        else:
            raise SystemExit(f"ERROR: modelo desconocido '{model}' en {zone}")

        for k, v in replacements.items():
            page = page.replace(k, v)

        if "{{" in page:
            raise SystemExit(f"ERROR: quedaron placeholders sin reemplazar en {slug}.html")

        (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
        print(f"  ✓ {slug}.html (índice de zona — modelo {model})")

    print(f"{len(NEW_ZONES)} índice(s) de zona nuevos generados.")


# ---------------------------------------------------------------------------
# HUB DE COBERTURA — /service-areas  (ago 2026)
#
# Página general que organiza las 6 zonas. Su responsabilidad es elegir
# REGIÓN, nada más:
#
#   /service-areas          -> elegir región
#   /ballina                -> elegir servicio dentro de Ballina
#   /exterior-painting-...  -> la landing comercial del servicio local
#
# NO lista los 10 servicios dentro de cada tarjeta (eso ya lo hace el índice
# de zona) y NO pelea keywords locales tipo "painters Ballina": esas son de
# la landing local. Mismo criterio anti-canibalización que llevó a noindexar
# las viejas /contact/<slug> y a titular Lismore como "Painters Lismore".
#
# OJO: usa su propia lista ordenada, NO toca ZONES ni NEW_ZONES. Unificarlas
# cambiaría los crosslinks de las 30 landings de las zonas originales.
# ---------------------------------------------------------------------------

SERVICE_AREA_ORDER = [
    "Byron Bay", "Ballina", "Mullumbimby", "Kingscliff", "Tweed Heads", "Lismore",
]

# PROVISORIO: descripciones redactadas internamente (ago 2026) a partir de las
# localidades que ya estaban en NEARBY / NEW_ZONE_DATA. Son geográficas a
# propósito: sin cifras, sin promesas y sin afirmaciones que haya que validar.
# Anotado en DEVOLUCION-RAMON.md para que Ramón mande las definitivas.
SERVICE_AREA_BLURBS = {
    "Byron Bay":   "Our home base — the town centre, the surrounding beaches and out into the hinterland.",
    "Ballina":     "The Richmond River area, from the Ballina town centre out to the coast.",
    "Mullumbimby": "The hinterland town and the coastal villages just north of Byron Bay.",
    "Kingscliff":  "The Tweed Coast beaches and the farmland just behind them.",
    "Tweed Heads": "The NSW\u2013QLD border area, from the coast back to the ridge.",
    "Lismore":     "The inland hub of the Northern Rivers and the suburbs around it.",
}


def service_area_cards_html() -> str:
    """Las 6 tarjetas del hub. La tarjeta entera es el link a la zona."""
    rows = []
    for zone in SERVICE_AREA_ORDER:
        slug = slugify(zone)
        name = html_lib.escape(zone)
        blurb = html_lib.escape(SERVICE_AREA_BLURBS[zone])
        nearby = " \u00b7 ".join(html_lib.escape(n) for n in nearby_of(zone))
        rows.append(
            f'                    <li>\n'
            f'                        <a class="sa-card" href="{slug}.html">\n'
            f'                            <h2 class="sa-card__name">{name}</h2>\n'
            f'                            <p class="sa-card__desc">{blurb}</p>\n'
            f'                            <p class="sa-card__nearby">{nearby}</p>\n'
            f'                            <span class="sa-card__cta">Explore services in {name}'
            f'<span class="sa-card__arrow" aria-hidden="true">\u2192</span></span>\n'
            f'                        </a>\n'
            f'                    </li>'
        )
    return "\n".join(rows)


def generate_service_areas_page() -> None:
    landing = TEMPLATE.read_text(encoding="utf-8")
    header = _extract('<header class="site-header"', "</header>", landing)
    footer = _extract('<footer class="site-footer"', "</footer>", landing)

    template = (ROOT / "template-service-areas.html").read_text(encoding="utf-8")

    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Service Areas"},
        ],
    }, indent=8, ensure_ascii=False)

    page = template
    page = page.replace("{{HEADER}}", header)
    page = page.replace("{{FOOTER}}", footer)
    page = page.replace("{{ZONE_CARDS}}", service_area_cards_html())
    page = page.replace("{{SCHEMA_BREADCRUMB}}", breadcrumb)
    page = page.replace("{{DOMAIN}}", DOMAIN)

    if "{{" in page:
        raise SystemExit("ERROR: quedaron placeholders sin reemplazar en service-areas.html")

    (ROOT / "service-areas.html").write_text(page, encoding="utf-8")
    print("  \u2713 service-areas.html (hub de cobertura)")


if __name__ == "__main__":
    main()
