#!/usr/bin/env python3
"""
Genera una página estática por localidad para SEO local.

Fuente de verdad: contact.html (las localidades salen del dropdown).
Salida: contact/<slug>.html — igual a contact.html pero con
<title>, meta description, canonical y h2 propios de cada localidad.

Correr desde la raíz del proyecto cada vez que:
- se modifique contact.html (form, footer, estilos, etc.)
- se agregue o quite una localidad del dropdown

    python3 scripts/generate-location-pages.py
"""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "contact.html"
OUT_DIR = ROOT / "contact"
DOMAIN = "https://permapainting.com.au"

# Variantes de texto por página, para que las 30 URLs no sean idénticas.
# La elección es determinística (hash del slug): regenerar no cambia los textos.

H2_VARIANTS = [
    "Tell us about<br>your project in {loc}!",
    "Let&rsquo;s talk about<br>your project in {loc}",
    "Planning a paint job<br>in {loc}? Tell us more",
    "Got a project<br>in {loc}? Let&rsquo;s hear it",
    "Tell us what you&rsquo;re<br>planning in {loc}",
    "Your painting project<br>in {loc} starts here",
]

LABEL_VARIANTS = [
    "Write your message here",
    "Tell us a bit about the job",
    "Describe your project",
    "What can we help you with?",
    "Share the details of your project",
]

# Texto del h2 de la sección LOCATIONS (el dropdown vive adentro del h2
# y se preserva intacto). {loc} menciona la localidad de la página.
LOCATIONS_TITLE_VARIANTS = [
    "We&rsquo;re proudly based in Byron Bay.<br />\n                    We also work across The Northern Rivers region, including:",
    "Proudly serving {loc} from our Byron Bay base.<br />\n                    We work across the whole Northern Rivers region, including:",
    "Byron Bay is home base &mdash; and {loc} is part of our patch.<br />\n                    We paint right across the Northern Rivers, including:",
    "Based in Byron Bay, painting in {loc}<br />\n                    and all over the Northern Rivers region, including:",
    "From Byron Bay to {loc}:<br />\n                    we service the entire Northern Rivers region, including:",
]

TITLE_VARIANTS = [
    "Painters in {loc} | Perma P.",
    "House Painters in {loc} | Perma P.",
    "Painting Services in {loc} | Perma P.",
    "Professional Painters in {loc} | Perma P.",
]

META_VARIANTS = [
    "Professional painting services in {loc}, NSW. Get a free quote from Perma Painting, your local Northern Rivers painters.",
    "Looking for painters in {loc}? Perma Painting offers interior and exterior painting across the Northern Rivers. Free quotes.",
    "Perma Painting services {loc} and the Northern Rivers region, NSW. Quality workmanship, free quotes, Byron Bay based.",
    "Need a painter in {loc}, NSW? Contact Perma Painting for a free quote on interior, exterior and commercial painting.",
]


def slugify(name: str) -> str:
    """Debe coincidir con slugify() de js/main.js."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def pick(variants: list, slug: str, salt: str) -> str:
    """Elige una variante de forma estable según el slug."""
    digest = hashlib.md5(f"{salt}:{slug}".encode()).hexdigest()
    return variants[int(digest, 16) % len(variants)]


def main() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")

    locations = re.findall(r'data-location="([^"]+)"', html)
    if not locations:
        raise SystemExit("No se encontraron localidades en contact.html")

    OUT_DIR.mkdir(exist_ok=True)

    # limpiar páginas viejas (por si se quitó una localidad)
    expected = {f"{slugify(loc)}.html" for loc in locations}
    for old in OUT_DIR.glob("*.html"):
        try:
            old.unlink()
        except PermissionError:
            if old.name not in expected:
                print(f"AVISO: no pude borrar {old.name} (página huérfana, borrala a mano)")

    for loc in locations:
        slug = slugify(loc)
        page = html

        title = pick(TITLE_VARIANTS, slug, "title").format(loc=loc)
        meta = pick(META_VARIANTS, slug, "meta").format(loc=loc)
        h2 = pick(H2_VARIANTS, slug, "h2").format(loc=loc)
        label = pick(LABEL_VARIANTS, slug, "label")

        page = page.replace(
            "<title>Contact | Perma P.</title>",
            f"<title>{title}</title>",
        )
        page = re.sub(
            r'(<meta name="description"\s+content=")[^"]*(")',
            lambda m: m.group(1) + meta + m.group(2),
            page,
        )
        page = re.sub(
            r'(<link rel="canonical" href=")[^"]*(")',
            rf"\g<1>{DOMAIN}/contact/{slug}\g<2>",
            page,
        )
        page = page.replace(
            '<h2 class="contact-form__title text-animate-in">Tell us about<br>your project</h2>',
            f'<h2 class="contact-form__title text-animate-in">{h2}</h2>',
        )
        page = page.replace(
            '<label for="message" class="contact-form__label-text">Write your message here</label>',
            f'<label for="message" class="contact-form__label-text">{label}</label>',
        )

        # "Proudly serving Byron Bay from our Byron Bay base" queda redundante:
        # para localidades que mencionan Byron Bay usamos la variante neutra.
        if "byron" in slug:
            loc_title = LOCATIONS_TITLE_VARIANTS[0]
        else:
            loc_title = pick(LOCATIONS_TITLE_VARIANTS, slug, "loctitle").format(loc=loc)
        page = re.sub(
            r'(<h2 class="locations__title">).*?(<span class="locations__dropdown)',
            lambda m: f"{m.group(1)}\n                    {loc_title}\n                    {m.group(2)}",
            page,
            flags=re.DOTALL,
        )

        (OUT_DIR / f"{slug}.html").write_text(page, encoding="utf-8")

    print(f"{len(locations)} páginas generadas en {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
