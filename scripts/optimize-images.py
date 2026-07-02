#!/usr/bin/env python3
"""
Genera copias .webp para las imágenes raster referenciadas por el sitio.

Escanea HTML/CSS/JS del proyecto para encontrar assets usados en producción,
crea el .webp junto al original y nunca borra el archivo fuente.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_SUFFIXES = {".html", ".css", ".js"}
SKIP_DIRS = {".git", "fotos-nuevas", "otras-infos"}
ASSET_PATTERN = re.compile(
    r'/?(assets/[^"\')\s>]+\.(?:jpe?g|png))',
    re.IGNORECASE,
)


def referenced_rasters() -> list[Path]:
    paths: set[Path] = set()

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(ROOT)
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in ASSET_PATTERN.finditer(text):
            candidate = ROOT / match.group(1)
            if candidate.exists():
                paths.add(candidate)

    return sorted(paths)


def convert_to_webp(source: Path, quality: int, force: bool, cwebp: str) -> tuple[str, int, int]:
    target = source.with_suffix(".webp")

    if target.exists() and not force and target.stat().st_mtime >= source.stat().st_mtime:
        return ("skipped", source.stat().st_size, target.stat().st_size)

    before = source.stat().st_size
    subprocess.run(
        [cwebp, "-quiet", "-mt", "-q", str(quality), str(source), "-o", str(target)],
        check=True,
    )
    return ("converted", before, target.stat().st_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate WebP copies for referenced raster assets.")
    parser.add_argument("--quality", type=int, default=80, help="WebP quality (default: 80)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if target is newer")
    args = parser.parse_args()

    cwebp = shutil.which("cwebp")
    if not cwebp:
        raise SystemExit("ERROR: cwebp no está disponible en PATH.")

    assets = referenced_rasters()
    if not assets:
        print("No se encontraron imágenes raster referenciadas.")
        return

    converted = 0
    skipped = 0
    total_before = 0
    total_after = 0

    for asset in assets:
        status, before, after = convert_to_webp(asset, args.quality, args.force, cwebp)
        total_before += before
        total_after += after
        rel = asset.relative_to(ROOT)

        if status == "converted":
            converted += 1
            print(f"  + {rel} -> {rel.with_suffix('.webp')}")
        else:
            skipped += 1
            print(f"  = {rel.with_suffix('.webp')} (ya al día)")

    saved = total_before - total_after
    print(
        f"\nListo: {converted} convertidas, {skipped} ya existentes. "
        f"Fuente {total_before / 1024:.1f} KiB -> WebP {total_after / 1024:.1f} KiB "
        f"(ahorro {saved / 1024:.1f} KiB)."
    )


if __name__ == "__main__":
    main()
