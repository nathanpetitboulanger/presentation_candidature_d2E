#!/usr/bin/env python3
"""Assemble deck/ (format Slides : deck.json + une <section> par fichier) en un seul strajo.html présentable."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECK = ROOT / "deck"
TEMPLATE = ROOT / "viewer" / "template.html"
OUT = ROOT / "strajo.html"

EMBED_RE = re.compile(r"<x-embed([^>]*)>(.*?)</x-embed>", re.S)


def embed_to_iframe(m: re.Match) -> str:
    # Un <x-embed> est une petite page isolée : on la sert en iframe sandboxée pour que
    # son <script> ne tourne pas dans le document principal.
    attrs, inner = m.group(1), m.group(2)
    doc = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + inner + "</body></html>"
    return f'<iframe class="x-embed"{attrs} sandbox="allow-scripts" scrolling="no" srcdoc="{html.escape(doc, quote=True)}"></iframe>'


def main() -> None:
    deck = json.loads((DECK / "deck.json").read_text(encoding="utf-8"))
    files = {p.stem: p for p in (DECK / "slides").glob("*.html")}

    missing = [sid for sid in deck["order"] if sid not in files]
    if missing:
        raise SystemExit(f"Slides absentes de deck/slides/ : {', '.join(missing)}")
    # Comme le lecteur Slides : une slide absente de "order" s'affiche à la fin.
    ids = deck["order"] + sorted(set(files) - set(deck["order"]))

    slides = [EMBED_RE.sub(embed_to_iframe, files[sid].read_text(encoding="utf-8").strip()) for sid in ids]
    fonts = "\n".join(
        f'<link rel="stylesheet" href="{html.escape(face["href"])}">'
        for face in deck.get("faces", {}).values()
        if "href" in face
    )

    page = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{TITLE}}", html.escape(deck.get("title", "Slides")))
        .replace("{{FONTS}}", fonts)
        .replace("{{SLIDES}}", "\n".join(slides))
    )
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} : {len(slides)} slides")


if __name__ == "__main__":
    main()
