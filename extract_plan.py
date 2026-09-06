#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_plan.py -- Point d'entree historique de l'extraction locale.

Le moteur reel vit desormais dans core/local_extractor.py
(VectorPlanExtractor : multi-pages, find_tables, spatial, zero mock).
Ce module conserve l'API historique pour main.py, l'UI et les tests.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.local_extractor import (  # noqa: F401
    ExtractionError,
    VectorPlanExtractor,
    RasterPlanExtractor,
    extract_plan_auto,
    is_raster_pdf,
)

# Regex historiques conserves pour compatibilite
from core.local_extractor import (  # noqa: F401
    SEMELLE_DIM_RX,
    FERRA_RX,
)


class LocalPlanExtractor(VectorPlanExtractor):
    """Alias historique du moteur vectoriel multi-pages."""

    def extract_from_words(self, words, progress_callback=None):
        return super().extract_from_words(words)


def dump_raw_blocks(words):
    """Affiche la liste BRUTE des blocs textes lus sur le plan (preuve)."""
    print("\n--- LISTE BRUTE DES BLOCS TEXTE EXTRAITS (coordonnees reelles) ---")
    by_page = {}
    for w in words:
        by_page.setdefault(w.get("page", 1), []).append(w)
    for page in sorted(by_page):
        print(f"\n[Page {page}] {len(by_page[page])} mots")
        for w in sorted(by_page[page], key=lambda w: (w["y"], w["x"])):
            print(f"  x={w['x']:7.1f} y={w['y']:7.1f} : {w['text']}")
    print("--- FIN LISTE BRUTE ---\n")


def main():
    import argparse
    import json
    import logging
    import os

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    ap = argparse.ArgumentParser(description="Extraction spatiale reelle de plans BA")
    ap.add_argument("--input", "-i", required=True)
    ap.add_argument("--out", "-o", default="output/plan_data.json")
    ap.add_argument("--raw", action="store_true",
                    help="Afficher la liste brute de tous les blocs textes")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Fichier introuvable : {input_path}")
        sys.exit(1)

    extractor = LocalPlanExtractor()

    if input_path.suffix.lower() == ".pdf":
        import pymupdf
        if args.raw:
            doc = pymupdf.open(str(input_path))
            words = []
            for pi in range(len(doc)):
                for w in doc[pi].get_text("words"):
                    words.append({"text": w[4], "x": round(w[0], 2),
                                  "y": round(w[1], 2), "page": pi + 1})
            doc.close()
            dump_raw_blocks(words)
        plan_data = extractor.process_all_pages(
            str(input_path),
            progress_callback=lambda p, t, r: logger.info(
                f"Page {p}/{t} : {r}"))
    else:
        plan_data = extract_plan_auto(str(input_path))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, ensure_ascii=False, indent=2)

    c = plan_data["catalogue_types"]
    impl = plan_data["implantations"]
    logger.info(f"-> {args.out}")
    logger.info(
        f"Semelles : {len(c['semelles'])} types / "
        f"{len(impl['semelles'])} positionnees | "
        f"Poteaux : {len(c['poteaux'])} | Poutres : {len(c['poutres'])}")
    for a in plan_data["_meta"]["avertissements"]:
        logger.warning(a)
    for h in plan_data["_meta"]["hypotheses"]:
        logger.info(f"Hypothese : {h}")


if __name__ == "__main__":
    main()
