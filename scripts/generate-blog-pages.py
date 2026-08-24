#!/usr/bin/env python3
"""
Genera la sección BLOG del sitio:

  blog/index.html      -> el índice (/blog), con destacado + grilla + filtros
  blog/<slug>.html     -> una página por artículo (/blog/<slug>)

Mismo patrón que generate-landing-pages.py: los datos viven ACÁ, el HTML
sale de los templates de la raíz, y las páginas NO se editan a mano
(se pisan al regenerar).

    python3 scripts/generate-blog-pages.py

--------------------------------------------------------------------------
CÓMO CARGAR UNA NOTA NUEVA
--------------------------------------------------------------------------
1. Copiá un bloque de ARTICLES y pegalo ARRIBA de todo (el índice ordena
   por fecha, la más nueva primero — pero conviene mantenerlo prolijo).
2. Completá slug, title, category, excerpt, date, photo y meta_description.
   - "category" tiene que existir en CATEGORIES (si es una categoría nueva,
     agregala ahí primero y sumale su color en css/blog.css).
   - "slug" es la URL: /blog/<slug>. Minúsculas y guiones.
3. Pegá el texto en "body" con este mini-formato:
       ## Título de sección
       (línea en blanco entre párrafos)
       - item de lista
4. Sacá "placeholder": True cuando el texto sea el definitivo (ese flag es
   lo que pinta el cartelito amarillo de "texto provisorio").
5. Corré:  python3 scripts/generate-blog-pages.py
           python3 scripts/generate-sitemap.py

El destacado del índice es el artículo con "featured": True (uno solo).
--------------------------------------------------------------------------
"""

import html as html_mod
import json
import re
import subprocess
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "blog"
DOMAIN = "https://permapainting.com.au"

INDEX_TEMPLATE = ROOT / "template-blog-index.html"
ARTICLE_TEMPLATE = ROOT / "template-blog-article.html"

# El header y el footer se extraen de template-landing.html (una sola
# fuente de verdad) y se pasan a rutas absolutas, porque estas páginas
# viven en /blog/ y no en la raíz.
HEADER_SOURCE = ROOT / "template-landing.html"

# Intro del índice (debajo del H1).
BLOG_INTRO = (
    "Practical advice from the team — what works on Northern Rivers homes, "
    "what the coastal weather does to a finish, and how to plan a job so it "
    "lasts. No jargon, no sales pitch."
)

BLOG_META_DESCRIPTION = (
    "Painting tips, local guides and practical advice for homes in Byron Bay, "
    "Ballina and Mullumbimby, from the Perma Painting team."
)

# CTA de las páginas de artículo (mismo bloque visual que las landings).
ARTICLE_CTA_TEXT = (
    "Tell us what you have in mind and we'll come back with a clear, "
    "no-obligation quote."
)

# ---------------------------------------------------------------------------
# CATEGORÍAS
# El orden acá es el orden de los filtros del índice ("All" se agrega solo).
# Si sumás una categoría, agregale su color en css/blog.css (.blog-tag--<slug>).
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Exterior",
    "Interior",
    "Epoxy floors",
    "Lead paint",
]

# ---------------------------------------------------------------------------
# ARTÍCULOS
#
# PROVISORIO (ago 2026): los 7 textos de abajo son de relleno, escritos
# internamente para poder ver la sección funcionando. Ramón manda los reales.
# Cada uno tiene "placeholder": True -> muestra un aviso arriba del cuerpo.
# Al cargar el texto real, borrar ese flag.
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "slug": "best-time-to-paint-your-home-exterior",
        "title": "Why a dry spell is the best time to paint your home's exterior",
        "category": "Exterior",
        "date": "2026-08-18",
        "featured": True,
        "placeholder": True,
        "photo": "assets/photos/exterior/exterior_003.webp",
        "photo_alt": "Exterior painting work on a Byron Bay home",
        "excerpt": "Drier weather across the Northern Rivers opens a real scheduling window — here's why it matters more than most people think.",
        "meta_description": "Why a dry stretch is the best window to repaint your exterior in Byron Bay and the Northern Rivers, and how humidity affects the finish.",
        "body": """
Exterior paint doesn't just need to go on — it needs to cure. Those are two
different things, and the gap between them is where most premature failures
start. A coat can feel dry to the touch in an hour and still be weeks away from
reaching its full hardness.

## What humidity actually does to a finish

When moisture sits in the timber, render or brick underneath, the coating can't
bond the way it's designed to. You get adhesion problems that don't show up for
a season or two, then appear all at once as flaking along the sun-facing walls.

On the Northern Rivers coast this matters more than it does inland. Salt air,
high humidity and long wet stretches mean a substrate can read as dry on the
surface while still holding moisture a few millimetres in.

## The window worth waiting for

A run of dry days does three useful things at once:

- Lets the substrate dry out properly before any prep work starts
- Gives each coat the conditions it needs to cure, not just dry
- Makes the schedule predictable, so the job doesn't stretch out over weeks

## What we do differently in a dry stretch

We use it to do the parts that get rushed otherwise — washing down, sanding
back the failed areas, filling and priming. The prep is what determines how
long the finish lasts; the topcoat is the easy part.

If you've been putting off an exterior repaint, a dry forecast is the cue to
book it in rather than wait for "sometime next year". The window doesn't stay
open long around here.
""",
    },
    {
        "slug": "does-my-home-have-lead-paint",
        "title": "Does my home have lead paint?",
        "category": "Lead paint",
        "date": "2026-08-11",
        "placeholder": True,
        "photo": "assets/photos/residential/residential_002.webp",
        "photo_alt": "Older weatherboard home in the Northern Rivers",
        "excerpt": "What Byron Bay homeowners need to know about older houses, and how to check before anyone starts sanding.",
        "meta_description": "How to tell if your Byron Bay home has lead paint, why it matters before any sanding starts, and what to do about it.",
        "body": """
If your house was painted before 1970, there's a real chance there's lead paint
somewhere in the layers — often buried under decades of newer coats. It's not a
reason to panic, but it is a reason to check before anyone picks up a sander.

## Which homes are most likely

- Anything built or repainted before 1970 (lead was phased down from 1965)
- Weatherboard cottages and Queenslanders with original trim still in place
- Window frames, door jambs, skirtings and eaves — the high-wear spots

## Why the layers matter

Lead paint that's intact and sealed under sound coats is generally low risk.
The danger comes from disturbing it: dry sanding, scraping, water blasting or
heat-gunning turns it into dust and fumes that spread through the house and
garden.

## How to check

A hardware-store swab kit tells you whether lead is present at the surface, but
not what's underneath. For a definitive answer you want a sample from all the
layers, tested by a lab. Any painter working on a pre-1970 home should be
raising this with you before quoting, not after starting.

## What happens if it's there

It changes the method, not necessarily the price bracket. Wet sanding, chemical
stripping, containment sheeting and proper waste disposal replace the usual
prep. Some sections get encapsulated rather than stripped, which is often the
better call.

The one thing worth avoiding is a weekend of DIY sanding on an old
weatherboard. That's the scenario that causes actual harm.
""",
    },
    {
        "slug": "is-epoxy-right-for-your-garage",
        "title": "Is an epoxy floor right for your garage?",
        "category": "Epoxy floors",
        "date": "2026-08-04",
        "placeholder": True,
        "photo": "assets/photos/commercial/commercial_002.webp",
        "photo_alt": "Epoxy floor coating in a commercial space",
        "excerpt": "What epoxy actually is, where it performs, and the two situations where we'd talk you out of it.",
        "meta_description": "What an epoxy garage floor involves, where it works well, and when a different coating system makes more sense.",
        "body": """
Epoxy gets asked about a lot, usually after someone has seen a showroom floor
and wondered what it would take at home. The short version: it's excellent in
the right conditions and disappointing in the wrong ones, and the difference is
almost always the slab underneath.

## What it is

A two-part resin that chemically cures into a hard, seamless surface bonded to
the concrete. It's not a paint sitting on top — done properly it's part of the
floor.

## Where it performs

- Garages that stay reasonably dry
- Workshops and storage areas that see wheeled loads and dropped tools
- Anywhere you want a surface you can actually mop

## Where it struggles

Two situations give us pause. The first is a slab with rising damp — moisture
pushing up from below will lift almost any coating eventually, and no amount of
prep fixes it without addressing the source. The second is a slab in poor
condition, where cracking and spalling need repair first.

We test for moisture before quoting. If the reading comes back high, we'll say
so rather than coat over it.

## The part people underestimate

Preparation. The slab gets ground back mechanically to open the surface so the
resin can key in. It's dusty, it takes time, and it's the single biggest
predictor of whether the floor is still intact in ten years.
""",
    },
    {
        "slug": "warning-signs-your-exterior-needs-paint",
        "title": "Five warning signs your exterior needs repainting",
        "category": "Exterior",
        "date": "2026-07-28",
        "placeholder": True,
        "photo": "assets/photos/exterior/exterior_005.webp",
        "photo_alt": "Exterior wall being prepared for repainting",
        "excerpt": "Catch it at the right moment and it's a repaint. Leave it too long and it becomes a repair job.",
        "meta_description": "Five signs your home's exterior paint is failing, and why acting early keeps a repaint from turning into timber repairs.",
        "body": """
Exterior coatings don't fail overnight. They give you a good year of warning if
you know what to look at — and the difference between acting then and acting
later is usually the difference between painting and carpentry.

## 1. Chalking

Run your hand along a sun-facing wall. If it comes away with a fine powder, the
binder in the paint has broken down. The coating is still there, but it's
stopped protecting.

## 2. Hairline cracking

Fine crazing across the surface means the film has lost its flexibility. It
still looks fine from the street, and it's the last easy moment to repaint.

## 3. Flaking around fixings and joins

Where two materials meet — timber to render, wall to window frame — movement
concentrates. Flaking here means water is getting behind the coating.

## 4. Colour shifting unevenly

North and west walls fade first. When the difference between elevations is
obvious from the driveway, the coating has taken its full UV load.

## 5. Timber that feels soft

Press a fingernail into the weatherboard near the ground line. If it gives,
you're past painting and into replacement for that section.

## Why timing matters

Repainting sound timber is straightforward. Repainting timber that's been open
to the weather for two wet seasons means replacing boards, and that's a
different quote entirely.
""",
    },
    {
        "slug": "how-professional-lead-paint-removal-works",
        "title": "How professional lead paint removal works",
        "category": "Lead paint",
        "date": "2026-07-21",
        "placeholder": True,
        "photo": "assets/photos/residential/residential_004.webp",
        "photo_alt": "Preparation work on an older home before repainting",
        "excerpt": "Containment, wet methods and proper disposal — and why DIY sanding is the one approach to rule out.",
        "meta_description": "What professional lead paint removal involves: containment, wet sanding, encapsulation and safe disposal.",
        "body": """
Once lead paint is confirmed, the work changes shape. It's slower and more
methodical, and most of the effort goes into keeping the dust in one place.

## Containment first

Plastic sheeting seals off the work area, drop sheets catch everything, and
garden beds and play areas get covered. Windows and doors stay shut. This is
the step that protects the rest of the property.

## Wet methods, not dry

Dry sanding is what turns lead paint into a health problem. Instead:

- Wet sanding keeps the dust bound in water
- Chemical strippers lift the layers without airborne particles
- Low-temperature infrared can soften coatings without vaporising lead

## Encapsulation as an option

Sometimes the better answer is not to remove it at all. If the existing layers
are sound and well-adhered, a specialised encapsulating coating seals them
permanently. It's less invasive, cheaper, and often the recommendation for
sections that aren't high-wear.

## Disposal

Waste goes into sealed bags and to a facility licensed to take it — not into
the household bin and not onto the verge.

## The DIY question

We get asked whether it's manageable over a weekend. Honestly, no. The
equipment matters less than the method, and the method is what keeps lead dust
out of the soil, the roof cavity and the people living there.
""",
    },
    {
        "slug": "what-determines-the-price-of-an-epoxy-floor",
        "title": "What actually determines the price of an epoxy floor",
        "category": "Epoxy floors",
        "date": "2026-07-14",
        "placeholder": True,
        "photo": "assets/photos/commercial/commercial_005.webp",
        "photo_alt": "Finished floor coating in a commercial space",
        "excerpt": "Size matters less than you'd think. Prep and the coating system are what move the number.",
        "meta_description": "The three things that set the price of an epoxy floor: slab preparation, the coating system specified, and the site itself.",
        "body": """
Quotes for epoxy floors vary more than people expect, and the reason is rarely
the square metres. Three things move the number.

## 1. The state of the slab

A clean, sound, dry slab needs grinding and not much else. A slab with old
adhesive, oil staining, cracks or spalling needs repair before anything gets
coated. This is the biggest single variable, and it's why an on-site look
matters more than a phone estimate.

## 2. The coating system

"Epoxy" covers a range. A single-coat solvent-based system and a full
build-up with a polyurethane topcoat are different products with different
lifespans. What's right depends on what the floor takes day to day:

- Light domestic garage use
- Workshop with wheeled loads and chemical exposure
- Commercial traffic that can't afford downtime

## 3. The site

Access, power, how much of the space has to be cleared, and whether the job can
run continuously or has to work around you. A garage we can have to ourselves
for three days costs less than the same floor done in stages.

## What a quote should tell you

It should name the system, the number of coats, the preparation method and the
cure time before you can drive on it. If it's a single number with no method
attached, that's worth asking about.
""",
    },
    {
        "slug": "choosing-low-voc-paint-for-your-interior",
        "title": "Choosing low-VOC paint for your interior",
        "category": "Interior",
        "date": "2026-07-07",
        "placeholder": True,
        "photo": "assets/photos/interior/interior_003.webp",
        "photo_alt": "Freshly painted interior of a Northern Rivers home",
        "excerpt": "Low-odour, low-toxicity products have caught up on durability. Here's what to look for on the tin.",
        "meta_description": "How to choose low-VOC interior paint: what the numbers mean, where it matters most, and how the finishes compare on durability.",
        "body": """
VOCs — volatile organic compounds — are the solvents that evaporate as paint
dries. They're what you're smelling for days after a job, and reducing them is
the easiest health improvement available in a repaint.

## What the numbers mean

Look for g/L on the tin. Broadly:

- Under 50 g/L is low
- Under 5 g/L is usually marketed as zero
- Older enamels can sit well above 300 g/L

Tinting adds some back, so a deep colour in a low-VOC base won't be quite as
low as the base itself.

## Where it matters most

Bedrooms and any room used by kids, anyone with asthma, or anyone who'll be
sleeping in the house while the work happens. Enclosed spaces with limited
airflow — bathrooms, hallways, built-ins — hold the smell longest.

## Has durability caught up?

For walls and ceilings, yes. Water-based low-VOC products now match what
solvent-based products did a decade ago on washability and coverage.

Trim and doors are the interesting case. Water-based enamels have improved
enormously and no longer yellow the way oil-based ones do, though they need a
lighter touch during application and a longer window before they reach full
hardness.

## The practical upside

You can use the room again the same day rather than airing it out for a week.
On an occupied house that's usually worth more than any spec on the tin.
""",
    },
]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Debe coincidir con slugify() de js/main.js."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def esc(text: str) -> str:
    return html_mod.escape(text, quote=True)


@lru_cache(maxsize=None)
def image_dimensions(src: str) -> tuple[int, int]:
    """Ancho/alto reales de la foto (para reservar espacio y evitar CLS).

    macOS: sips. Linux/otros: Pillow. Si ninguno está disponible cae a una
    proporción 16/10 genérica para que la generación nunca se rompa.
    """
    path = ROOT / src
    try:
        output = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        values: dict[str, str] = {}
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
        return int(values["pixelWidth"]), int(values["pixelHeight"])
    except Exception:
        pass

    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        print(f"  ! no pude leer el tamaño de {src} — uso 1600x1000")
        return (1600, 1000)


def to_abs(markup: str) -> str:
    """Pasa el header/footer de rutas relativas a absolutas.

    Las páginas del blog viven en /blog/, así que 'about-us.html' apuntaría a
    /blog/about-us.html. Convertimos href/src/srcset que no empiecen con "/",
    "http", "#", "mailto:" o "tel:".
    """
    markup = re.sub(
        r'\b(href|src)="(?!/|https?://|#|mailto:|tel:|data:)',
        r'\1="/',
        markup,
    )

    def fix_srcset(match: re.Match) -> str:
        parts = []
        for item in match.group(1).split(","):
            item = item.strip()
            if item and not item.startswith(("/", "http", "data:")):
                item = "/" + item
            parts.append(item)
        return 'srcset="' + ", ".join(parts) + '"'

    markup = re.sub(r'srcset="([^"]+)"', fix_srcset, markup)

    # index.html -> raíz
    markup = markup.replace('href="/index.html"', 'href="/"')

    # El link del blog queda marcado como página actual (lo usa blog.css
    # para subrayarlo en el nav).
    markup = markup.replace(
        '<a class="site-nav__link" href="/blog/">BLOG</a>',
        '<a class="site-nav__link" href="/blog/" aria-current="page">BLOG</a>',
    )
    return markup


def render_body(body: str) -> tuple[str, int]:
    """Mini-formato -> HTML. Devuelve (html, cantidad de palabras).

    '## Texto'  -> <h2>
    '- Texto'   -> <li> (agrupados en <ul>)
    resto       -> <p>, separando por líneas en blanco
    """
    out: list[str] = []
    words = 0
    paragraph: list[str] = []
    bullets: list[str] = []
    pad = " " * 20

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(paragraph).strip()
            out.append(f"{pad}<p>{text}</p>")
            paragraph = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            items = "\n".join(f"{pad}    <li>{b}</li>" for b in bullets)
            out.append(f"{pad}<ul>\n{items}\n{pad}</ul>")
            bullets = []

    for raw in body.strip().splitlines():
        line = raw.strip()
        words += len(line.split())

        if not line:
            flush_paragraph()
            flush_bullets()
        elif line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            out.append(f"{pad}<h2>{line[3:].strip()}</h2>")
        elif line.startswith("- "):
            flush_paragraph()
            bullets.append(line[2:].strip())
        else:
            flush_bullets()
            paragraph.append(line)

    flush_paragraph()
    flush_bullets()
    return "\n\n".join(out), words


def read_time(words: int) -> int:
    return max(2, round(words / 200))


def human_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {d.strftime('%B %Y')}"


def article_url(article: dict) -> str:
    return f"/blog/{article['slug']}"


# ---------------------------------------------------------------------------
# BLOQUES DE HTML
# ---------------------------------------------------------------------------

def filters_html() -> str:
    rows = ['                    <button class="blog-filter is-active" type="button" '
            'data-filter="all" aria-pressed="true">All</button>']
    for cat in CATEGORIES:
        rows.append(
            f'                    <button class="blog-filter" type="button" '
            f'data-filter="{slugify(cat)}" aria-pressed="false">{esc(cat)}</button>'
        )
    return "\n".join(rows)


def featured_html(article: dict) -> str:
    src = article["photo"]
    width, height = image_dimensions(src)
    cat_slug = slugify(article["category"])
    return f"""                <div class="blog-featured">
                    <div class="blog-featured__media">
                        <img src="/{src}" alt="{esc(article['photo_alt'])}" class="blog-featured__img"
                            width="{width}" height="{height}" fetchpriority="high" decoding="async">
                    </div>

                    <div class="blog-featured__text">
                        <span class="blog-tag blog-tag--{cat_slug}">{esc(article['category'])}</span>
                        <h2 class="blog-featured__title">{esc(article['title'])}</h2>
                        <p class="blog-featured__excerpt">{esc(article['excerpt'])}</p>
                        <p class="blog-featured__meta">
                            <time datetime="{article['date']}">{human_date(article['date'])}</time>
                            <span aria-hidden="true">·</span>
                            <span>{article['read_time']} min read</span>
                        </p>
                    </div>

                    <a class="blog-featured__link" href="{article_url(article)}"
                        aria-label="Read: {esc(article['title'])}"></a>
                </div>"""


def card_html(article: dict, indent: str = " " * 20) -> str:
    src = article["photo"]
    width, height = image_dimensions(src)
    cat_slug = slugify(article["category"])
    body = f"""<li class="blog-card" data-category="{cat_slug}">
    <div class="blog-card__media">
        <img src="/{src}" alt="{esc(article['photo_alt'])}" class="blog-card__img"
            width="{width}" height="{height}" loading="lazy" decoding="async">
    </div>

    <div class="blog-card__text">
        <span class="blog-tag blog-tag--{cat_slug}">{esc(article['category'])}</span>
        <h3 class="blog-card__title">{esc(article['title'])}</h3>
        <p class="blog-card__excerpt">{esc(article['excerpt'])}</p>
        <p class="blog-card__meta">
            <time datetime="{article['date']}">{human_date(article['date'])}</time>
            <span aria-hidden="true">·</span>
            <span>{article['read_time']} min read</span>
        </p>
    </div>

    <a class="blog-card__link" href="{article_url(article)}"
        aria-label="Read: {esc(article['title'])}"></a>
</li>"""
    return "\n".join(indent + line if line else "" for line in body.splitlines())


PLACEHOLDER_NOTE = (
    '                    <p class="blog-prose__placeholder">Placeholder text — '
    'this article is a sample while the final copy is being written.</p>'
)


def related_articles(current: dict, articles: list[dict], limit: int = 3) -> list[dict]:
    """Primero las de la misma categoría, después las más recientes."""
    same = [a for a in articles if a is not current and a["category"] == current["category"]]
    other = [a for a in articles if a is not current and a["category"] != current["category"]]
    return (same + other)[:limit]


def schema_blog(articles: list[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Perma Painting Blog",
        "url": f"{DOMAIN}/blog/",
        "description": BLOG_META_DESCRIPTION,
        "publisher": {"@type": "Organization", "name": "Perma Painting", "url": f"{DOMAIN}/"},
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": a["title"],
                "url": f"{DOMAIN}/blog/{a['slug']}",
                "datePublished": a["date"],
                "description": a["excerpt"],
            }
            for a in articles
        ],
    }
    return json.dumps(data, indent=8, ensure_ascii=False)


def schema_article(article: dict) -> str:
    data = [
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": article["title"],
            "description": article["excerpt"],
            "image": f"{DOMAIN}/{article['photo']}",
            "datePublished": article["date"],
            "dateModified": article["date"],
            "articleSection": article["category"],
            "mainEntityOfPage": {"@type": "WebPage", "@id": f"{DOMAIN}/blog/{article['slug']}"},
            "author": {"@type": "Organization", "name": "Perma Painting", "url": f"{DOMAIN}/"},
            "publisher": {"@type": "Organization", "name": "Perma Painting", "url": f"{DOMAIN}/"},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{DOMAIN}/blog/"},
                {"@type": "ListItem", "position": 3, "name": article["title"]},
            ],
        },
    ]
    return json.dumps(data, indent=8, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    landing = HEADER_SOURCE.read_text(encoding="utf-8")
    header = to_abs(_extract('<header class="site-header"', "</header>", landing))
    footer = to_abs(_extract('<footer class="site-footer"', "</footer>", landing))

    articles = sorted(ARTICLES, key=lambda a: a["date"], reverse=True)

    # Validaciones tempranas: mejor romper acá que publicar algo raro.
    slugs = [a["slug"] for a in articles]
    duplicated = {s for s in slugs if slugs.count(s) > 1}
    if duplicated:
        raise SystemExit(f"ERROR: slugs repetidos: {', '.join(sorted(duplicated))}")

    for a in articles:
        if a["category"] not in CATEGORIES:
            raise SystemExit(
                f"ERROR: '{a['slug']}' usa la categoría '{a['category']}', que no está "
                f"en CATEGORIES. Agregala ahí y sumale su color en css/blog.css."
            )
        if not (ROOT / a["photo"]).exists():
            raise SystemExit(f"ERROR: '{a['slug']}' apunta a una foto que no existe: {a['photo']}")

    featured_list = [a for a in articles if a.get("featured")]
    if len(featured_list) != 1:
        raise SystemExit(
            f"ERROR: tiene que haber exactamente 1 artículo con 'featured': True "
            f"(hay {len(featured_list)})."
        )
    featured = featured_list[0]

    # Cuerpo + minutos de lectura de cada artículo (se usa en el índice también)
    for a in articles:
        a["body_html"], words = render_body(a["body"])
        a["read_time"] = read_time(words)

    OUT_DIR.mkdir(exist_ok=True)

    # --- Índice ---------------------------------------------------------
    rest = [a for a in articles if a is not featured]
    index = INDEX_TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{HEADER}}": header,
        "{{FOOTER}}": footer,
        "{{META_TITLE}}": "Blog | Perma Painting",
        "{{META_DESCRIPTION}}": BLOG_META_DESCRIPTION,
        "{{DOMAIN}}": DOMAIN,
        "{{INTRO}}": BLOG_INTRO,
        "{{FILTERS}}": filters_html(),
        "{{FEATURED}}": featured_html(featured),
        "{{FEATURED_CATEGORY_SLUG}}": slugify(featured["category"]),
        "{{CARDS}}": "\n\n".join(card_html(a) for a in rest),
        "{{SCHEMA_BLOG}}": schema_blog(articles),
    }
    for k, v in replacements.items():
        index = index.replace(k, v)
    (OUT_DIR / "index.html").write_text(index, encoding="utf-8")
    print("  ✓ blog/index.html")

    # --- Artículos ------------------------------------------------------
    article_template = ARTICLE_TEMPLATE.read_text(encoding="utf-8")
    for a in articles:
        width, height = image_dimensions(a["photo"])
        body_html = a["body_html"]
        if a.get("placeholder"):
            body_html = PLACEHOLDER_NOTE + "\n\n" + body_html

        preload = (
            '    <link rel="preload" as="image" type="image/webp" fetchpriority="high"\n'
            f'        href="/{a["photo"]}">'
        )

        page = article_template
        page_replacements = {
            "{{HEADER}}": header,
            "{{FOOTER}}": footer,
            "{{META_TITLE}}": f"{a['title']} | Perma Painting",
            "{{META_DESCRIPTION}}": a["meta_description"],
            "{{DOMAIN}}": DOMAIN,
            "{{SLUG}}": a["slug"],
            "{{HERO_PRELOAD}}": preload,
            "{{HERO_IMG}}": f"/{a['photo']}",
            "{{HERO_ALT}}": esc(a["photo_alt"]),
            "{{HERO_W}}": str(width),
            "{{HERO_H}}": str(height),
            "{{TITLE}}": esc(a["title"]),
            "{{EXCERPT}}": esc(a["excerpt"]),
            "{{CATEGORY}}": esc(a["category"]),
            "{{CATEGORY_SLUG}}": slugify(a["category"]),
            "{{DATE_ISO}}": a["date"],
            "{{DATE_HUMAN}}": human_date(a["date"]),
            "{{READ_TIME}}": str(a["read_time"]),
            "{{BODY}}": body_html,
            "{{RELATED}}": "\n\n".join(
                card_html(r) for r in related_articles(a, articles)
            ),
            "{{SCHEMA_ARTICLE}}": schema_article(a),
            "{{CTA_TEXT}}": ARTICLE_CTA_TEXT,
        }
        for k, v in page_replacements.items():
            page = page.replace(k, v)

        (OUT_DIR / f"{a['slug']}.html").write_text(page, encoding="utf-8")
        print(f"  ✓ blog/{a['slug']}.html")

    print(f"\nBlog generado: índice + {len(articles)} artículos en blog/.")
    print("Acordate de correr: python3 scripts/generate-sitemap.py")


def _extract(tag_open_marker: str, tag_close: str, markup: str) -> str:
    start = markup.index(tag_open_marker)
    end = markup.index(tag_close, start) + len(tag_close)
    return markup[start:end]


if __name__ == "__main__":
    main()
