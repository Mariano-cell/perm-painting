#!/usr/bin/env python3
"""Valida las 60 landings y los 6 índices generados antes de publicar."""

from __future__ import annotations

import html
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "scripts/generate-landing-pages.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("perma_landings", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def resolve_local(page: Path, value: str) -> Path | None:
    value = html.unescape(value.strip())
    if not value or value.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return None
    raw_path = parts.path
    if not raw_path:
        return None
    candidate = ROOT / raw_path.lstrip("/") if raw_path.startswith("/") else page.parent / raw_path
    candidate = candidate.resolve()
    if raw_path.endswith("/"):
        return candidate / "index.html"
    if candidate.suffix:
        return candidate
    if candidate.with_suffix(".html").exists():
        return candidate.with_suffix(".html")
    return candidate / "index.html"


def capture(pattern: str, source: str, page: Path, label: str) -> str:
    match = re.search(pattern, source, re.I | re.S)
    if not match:
        raise AssertionError(f"{page.name}: falta {label}")
    return html.unescape(match.group(1).strip())


def main() -> None:
    generator = load_generator()
    zones = generator.ZONES + generator.NEW_ZONES
    landing_paths = [
        ROOT / f"{generator.page_slug(service['name'], zone)}.html"
        for service in generator.SERVICES
        for zone in zones
    ]
    index_paths = [ROOT / f"{generator.slugify(zone)}.html" for zone in zones]
    generated = landing_paths + index_paths

    assert len(generator.SERVICES) == 10
    assert len(zones) == 6
    assert len(landing_paths) == 60
    assert len(index_paths) == 6
    missing_pages = [str(path.relative_to(ROOT)) for path in generated if not path.exists()]
    assert not missing_pages, f"Páginas faltantes: {missing_pages}"

    errors: list[str] = []
    titles: dict[str, list[str]] = {}
    metas: dict[str, list[str]] = {}
    canonicals: dict[str, list[str]] = {}

    for page in generated:
        source = page.read_text(encoding="utf-8")
        if "{{" in source:
            errors.append(f"{page.name}: placeholder sin resolver")

        try:
            title = capture(r"<title>(.*?)</title>", source, page, "title")
            meta = capture(r'<meta\s+name="description"\s+content="(.*?)"', source, page, "meta description")
            canonical = capture(r'<link\s+rel="canonical"\s+href="(.*?)"', source, page, "canonical")
            titles.setdefault(title, []).append(page.name)
            metas.setdefault(meta, []).append(page.name)
            canonicals.setdefault(canonical, []).append(page.name)
        except AssertionError as exc:
            errors.append(str(exc))

        for block in re.findall(
            r'<script\s+type="application/ld\+json">(.*?)</script>', source, re.I | re.S
        ):
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                errors.append(f"{page.name}: schema JSON inválido ({exc})")

        refs = re.findall(r'(?:href|src)="([^"]+)"', source)
        for srcset in re.findall(r'srcset="([^"]+)"', source):
            refs.extend(item.strip().split()[0] for item in srcset.split(",") if item.strip())
        for ref in refs:
            target = resolve_local(page, ref)
            if target is not None and not target.exists():
                errors.append(f"{page.name}: referencia rota -> {ref}")

    for label, values in (("title", titles), ("meta", metas), ("canonical", canonicals)):
        for value, pages in values.items():
            if len(pages) > 1:
                errors.append(f"{label} duplicado en {pages}: {value}")

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locations = re.findall(r"<loc>(.*?)</loc>", sitemap)
    if len(locations) != len(set(locations)):
        errors.append("sitemap.xml contiene URLs duplicadas")
    for page in generated:
        slug = page.stem
        expected_url = f"{generator.DOMAIN}/{slug}"
        if expected_url not in locations:
            errors.append(f"sitemap.xml: falta {expected_url}")

    if errors:
        print("VALIDACIÓN FALLIDA")
        print("\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)

    print("Validación completa OK")
    print("- 60 landings + 6 índices")
    print("- placeholders, links y assets OK")
    print("- titles, metas y canonicals únicos")
    print("- schema JSON válido")
    print(f"- sitemap.xml: {len(locations)} URLs únicas")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"VALIDACIÓN FALLIDA: {exc}")
        sys.exit(1)
