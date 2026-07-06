#!/usr/bin/env python3
"""
Genera sitemap.xml y robots.txt.

Incluye SOLO la estrategia nueva + páginas core:
- 24 landings (servicio × zona)
- 3 índices por zona (AREAS OF SERVICE)
- core: home, about-us, our-services, contact

NO incluye las 30 /contact/<slug> viejas (estrategia descartada): meterlas
competiría con las landings nuevas por las mismas keywords (canibalización).
No se borran ni se rompen — simplemente no se "empujan" en el sitemap.

    python3 scripts/generate-sitemap.py
"""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://permapainting.com.au"
TODAY = date.today().isoformat()

SERVICES = [
    "House Painters", "Interior Painting", "Exterior Painting", "Roof Painting",
    "Limewash Painting", "Deck Painting", "Kitchen Cabinet Painting", "Commercial Painters",
]
ZONES = ["Byron Bay", "Ballina", "Mullumbimby"]


def slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def url_entry(loc: str, priority: str, changefreq: str = "monthly") -> str:
    return (
        "  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{TODAY}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>"
    )


def main() -> None:
    urls = []

    # Home (prioridad máxima)
    urls.append(url_entry(f"{DOMAIN}/", "1.0", "weekly"))

    # Core
    urls.append(url_entry(f"{DOMAIN}/about-us", "0.6"))
    urls.append(url_entry(f"{DOMAIN}/our-services", "0.7"))
    urls.append(url_entry(f"{DOMAIN}/contact.html", "0.7"))

    # Índices por zona (prioridad media-alta: son hubs)
    for z in ZONES:
        urls.append(url_entry(f"{DOMAIN}/{slugify(z)}", "0.8"))

    # 24 landings (el contenido SEO principal: prioridad alta)
    for s in SERVICES:
        for z in ZONES:
            slug = f"{slugify(s)}-{slugify(z)}"
            urls.append(url_entry(f"{DOMAIN}/{slug}", "0.9"))

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"sitemap.xml generado con {len(urls)} URLs.")

    # robots.txt
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {DOMAIN}/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    print("robots.txt generado.")


if __name__ == "__main__":
    main()
