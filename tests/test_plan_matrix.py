"""Matrice d'acceptation des formats et libelles de plans BA."""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.local_extractor import (
    ExtractionError, extract_plan_auto, partial_plan_data)
from core.pdf_render import get_adaptive_dpi
from core.tokenizer import tokenize_composite


@pytest.mark.parametrize("label, expected", [
    ("S1/P1", ["S1", "P1"]),
    ("S2-P1", ["S2", "P1"]),
    ("LG2(30*50)", ["LG2", "(30x50)"]),
    ("P1(25x30)6HA14", ["P1", "(25x30)", "6HA14"]),
    ("S1(90x90x25)", ["S1(90x90x25)"]),
])
def test_tokenizer_matrix(label, expected):
    assert tokenize_composite(label) == expected


def test_adaptive_dpi_limits_grand_format():
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=2384, height=3370)  # A0 en points environ
    try:
        assert get_adaptive_dpi(page) <= 150
    finally:
        doc.close()


def test_partial_livrable_explicit():
    data = partial_plan_data("scan illisible")
    assert data["implantations"]["semelles"][0]["position_par_defaut"] is True
    assert data["catalogue_types"]["semelles"]["SEMELLE_DEFAULT"][
        "dimensions_par_defaut"] is True
    assert data["_meta"]["avertissements"]


def test_empty_pdf_auto_produit_un_livrable(tmp_path):
    import fitz

    path = tmp_path / "empty-a4.pdf"
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    doc.save(str(path))
    doc.close()

    data = extract_plan_auto(str(path))
    assert data["catalogue_types"]["semelles"]
    assert data["_meta"]["avertissements"]


def test_raster_ocr_indisponible_produit_un_livrable(tmp_path):
    image = tmp_path / "scan.png"
    image.write_bytes(b"not-a-real-image")
    with patch("core.local_extractor.RasterPlanExtractor",
               side_effect=ExtractionError("OCR indisponible")):
        data = extract_plan_auto(str(image))
    assert data["implantations"]["semelles"]
    assert "OCR indisponible" in data["_meta"]["avertissements"][0]
