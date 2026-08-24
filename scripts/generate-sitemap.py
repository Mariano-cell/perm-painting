#!/usr/bin/env python3
"""
Genera sitemap.xml y robots.txt.

Incluye SOLO la estrategia nueva + páginas core:
- 60 landings (servicio × zona)
- 6 índices por zona (AREAS OF SERVICE)
- el blog: /blog/ + un artículo por cada .html de la carpeta blog/
- core: home, about-us, our-services, contact

OJO: las URLs del blog salen de leer la carpeta blog/, así que correr
generate-blog-pages.py ANTES que este script.

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
    "Epoxy Floors", "Lead Paint Removal & Restoration",
]
ZONES = ["Byron Bay", "Ballina", "Mullumbimby", "Kingscliff", "Tweed Heads", "Lismore"]


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

    # Blog: el índice + un artículo por archivo generado en blog/.
    # (La lista de artículos vive en generate-blog-pages.py; acá leemos el
    # resultado en disco para no duplicar los datos en dos lados.)
    blog_dir = ROOT / "blog"
    if blog_dir.exists():
        urls.append(url_entry(f"{DOMAIN}/blog/", "0.7", "weekly"))
        for f in sorted(blog_dir.glob("*.html")):
            if f.name == "index.html":
                continue
            urls.append(url_entry(f"{DOMAIN}/blog/{f.stem}", "0.6"))
    else:
        print("  ! no existe blog/ — corré antes: python3 scripts/generate-blog-pages.py")

    # 60 landings (el contenido SEO principal: prioridad alta)
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
