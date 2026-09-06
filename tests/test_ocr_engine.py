#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ocr_engine.py -- Fallback OCR paresseux (RapidOCR local).

Verifie :
  - le chargement paresseux (aucun import rapidocr/numpy au demarrage) ;
  - les gardes : pages vectorielles >= 15 mots jamais OCR-ees, pages sans
    image jamais OCR-ees ;
  - l'OCR reel d'une page scannen (texte rendu en image) ;
  - l'integration complete : nomenclature scannee -> semelles reelles.
"""
import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import rapidocr_onnxruntime  # noqa: F401
    RAPIDOCR_AVAILABLE = True
except Exception:
    RAPIDOCR_AVAILABLE = False


def _page_scanned(textes, width=1191, height=842, dpi=200):
    """Cree une page 'scannee' : texte rendu en image, aucun texte vectoriel."""
    import fitz
    src = fitz.open()
    p = src.new_page(width=width, height=height)
    y = 100
    for t in textes:
        p.insert_text((100, y), t)
        y += 50
    png = p.get_pixmap(dpi=dpi).tobytes("png")
    src.close()

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_image(fitz.Rect(0, 0, width, height), stream=png)
    return doc, page


@unittest.skipUnless(RAPIDOCR_AVAILABLE, "rapidocr non installe")
class TestOcrEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import fitz
        from core.ocr_engine import PlanOCREngine
        cls.fitz = fitz
        cls.engine = PlanOCREngine()
        cls.doc_scan, cls.page_scan = _page_scanned(
            ["Semelles", "S1", "90 x 90 x 25"])

    @classmethod
    def tearDownClass(cls):
        cls.doc_scan.close()

    def test_pas_dimport_global_rapidocr(self):
        """core/ocr_engine.py ne doit pas importer rapidocr au niveau module."""
        path = os.path.join(ROOT, "core", "ocr_engine.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("rapidocr", a.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn("rapidocr", node.module)

    def test_page_vectorielle_jamais_ocr(self):
        """Page avec >= 15 mots vectoriels : OCR jamais declenche."""
        doc = self.fitz.open()
        page = doc.new_page(width=1191, height=842)
        for i in range(20):
            page.insert_text((50 + (i % 10) * 40, 100 + (i // 10) * 30),
                             f"T{i}")
        try:
            self.assertEqual(self.engine.ocr_page_if_scanned(page), [])
        finally:
            doc.close()

    def test_page_sans_image_jamais_ocr(self):
        """Page sparse (<15 mots) mais sans image : pas d'OCR."""
        doc = self.fitz.open()
        page = doc.new_page(width=1191, height=842)
        page.insert_text((100, 200), "S1")
        try:
            self.assertEqual(self.engine.ocr_page_if_scanned(page), [])
        finally:
            doc.close()

    def test_page_scannee_ocr_reel(self):
        """Page scannee (texte rendu en image) : l'OCR lit les mots."""
        words = self.engine.ocr_page_if_scanned(self.page_scan)
        self.assertGreaterEqual(len(words), 2)
        joined = " ".join(w["text"] for w in words)
        self.assertIn("S1", joined)
        self.assertIn("90", joined)

    def test_ocr_lazyness_premier_appel(self):
        """Le moteur n'est instancie qu'apres le premier appel utile."""
        from core.ocr_engine import PlanOCREngine
        fresh = PlanOCREngine()
        self.assertIsNone(fresh._engine)
        self.assertFalse(fresh._unavailable)
        self.assertIn(self.engine._ensure_engine() is not None, (True,))


@unittest.skipUnless(RAPIDOCR_AVAILABLE, "rapidocr non installe")
class TestIntegrationOcrPipeline(unittest.TestCase):
    def test_nomenclature_scannee_detectee(self):
        """Page 1 scannee (nomenclature image) + page 2 vectorielle (plan)
        -> semelles reelles via OCR + implantations via parseur spatial."""
        from core.local_extractor import VectorPlanExtractor
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            doc, page1 = _page_scanned(
                ["Semelles", "S1", "90 x 90 x 25",
                 "S2", "110 x 110 x 30"])
            page2 = doc.new_page(width=1191, height=842)
            page2.insert_text((600, 125), "1")
            page2.insert_text((597, 70), "A")
            page2.insert_text((100, 135), "S1(90x90x25)")

            pdf = os.path.join(td, "mixte.pdf")
            doc.save(pdf)
            doc.close()

            data = VectorPlanExtractor().process_all_pages(pdf)
            cat = data["catalogue_types"]["semelles"]
            self.assertIn("S1", cat)
            self.assertEqual(cat["S1"]["a"], 0.90)
            self.assertEqual(cat["S1"]["h"], 0.25)
            self.assertEqual(data["implantations"]["semelles"][0]["type"],
                             "S1")
            self.assertEqual(data["_meta"]["pages_ocr"], [1])


if __name__ == "__main__":
    unittest.main()
