#!/usr/bin/env python3
"""
Propaga el header nuevo (con dropdowns OUR SERVICES / AREAS OF SERVICE)
a las páginas que NO genera generate-landing-pages.py.

Reemplaza el bloque <nav class="site-nav">...</nav> por el nav nuevo,
en la variante de rutas que corresponda:
- relativa  -> index, about-us, our-services (raíz, rutas sin "/")
- absoluta  -> contact.html y contact/<slug>.html (rutas con "/")

Las 24 landings y los 3 índices ya traen el header nuevo desde su
template, así que NO se tocan acá.

OJO contact/<slug>: esas 30 páginas se regeneran desde contact.html con
scripts/generate-location-pages.py. Este script las actualiza directo
para que queden alineadas ya; si después se regeneran desde contact.html
(que también actualizamos), el resultado es el mismo.

    python3 scripts/propagate-header.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Páginas con rutas RELATIVAS (viven en la raíz, links sin "/")
REL_PAGES = ["index.html", "about-us.html", "our-services.html"]

# Páginas con rutas ABSOLUTAS (contact.html + las 30 contact/<slug>)
ABS_PAGES = ["contact.html"] + [
    f"contact/{p.name}" for p in (ROOT / "contact").glob("*.html")
] if (ROOT / "contact").exists() else ["contact.html"]


def build_nav(prefix: str) -> str:
    """prefix = '' (relativo) o '/' (absoluto)."""
    p = prefix
    return f'''<nav class="site-nav" id="site-nav" aria-label="Main navigation">
                <div class="site-nav__panel" role="dialog" aria-modal="true" aria-label="Menu">
                    <ul class="site-nav__list">
                        <li class="site-nav__item"><a class="site-nav__link" href="{p}about-us.html">ABOUT US</a></li>

                        <li class="site-nav__item site-nav__item--has-dropdown">
                            <span class="site-nav__link-row">
                                <a class="site-nav__link" href="{p}our-services.html">OUR SERVICES</a>
                                <button class="site-nav__caret" type="button" aria-label="Toggle services menu" aria-expanded="false">▾</button>
                            </span>
                            <ul class="site-nav__dropdown">
                                <li><a class="site-nav__dropdown-link" href="{p}house-painters-byron-bay.html">House Painters</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}interior-painting-byron-bay.html">Interior Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}exterior-painting-byron-bay.html">Exterior Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}roof-painting-byron-bay.html">Roof Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}limewash-painting-byron-bay.html">Limewash Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}deck-painting-byron-bay.html">Deck Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}kitchen-cabinet-painting-byron-bay.html">Kitchen Cabinet Painting</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}commercial-painters-byron-bay.html">Commercial Painters</a></li>
                            </ul>
                        </li>

                        <li class="site-nav__item site-nav__item--has-dropdown">
                            <span class="site-nav__link-row">
                                <a class="site-nav__link" href="{p}byron-bay.html">AREAS OF SERVICE</a>
                                <button class="site-nav__caret" type="button" aria-label="Toggle areas menu" aria-expanded="false">▾</button>
                            </span>
                            <ul class="site-nav__dropdown">
                                <li><a class="site-nav__dropdown-link" href="{p}byron-bay.html">Byron Bay</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}ballina.html">Ballina</a></li>
                                <li><a class="site-nav__dropdown-link" href="{p}mullumbimby.html">Mullumbimby</a></li>
                            </ul>
                        </li>

                        <li class="site-nav__item"><a class="site-nav__link site-nav__link--cta"
                                href="{p}contact.html">CONTACT</a></li>
                    </ul>
                </div>
            </nav>'''


NAV_RE = re.compile(r'<nav class="site-nav".*?</nav>', re.DOTALL)


def patch(page_path: Path, prefix: str) -> bool:
    if not page_path.exists():
        print(f"  ⚠ no existe: {page_path.relative_to(ROOT)}")
        return False
    html = page_path.read_text(encoding="utf-8")
    if not NAV_RE.search(html):
        print(f"  ⚠ sin <nav>: {page_path.relative_to(ROOT)}")
        return False
    new_html = NAV_RE.sub(lambda m: build_nav(prefix), html, count=1)
    page_path.write_text(new_html, encoding="utf-8")
    print(f"  ✓ {page_path.relative_to(ROOT)}")
    return True


def main() -> None:
    n = 0
    print("Rutas relativas:")
    for f in REL_PAGES:
        if patch(ROOT / f, ""):
            n += 1
    print("Rutas absolutas:")
    for f in ABS_PAGES:
        if patch(ROOT / f, "/"):
            n += 1
    print(f"\n{n} páginas actualizadas con el header nuevo.")


if __name__ == "__main__":
    main()
