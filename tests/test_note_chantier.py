#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_note_chantier.py -- Note de calculs PDF chantier.

Verifie : generation sans crash, exemple chiffre de la mission
(S1 1.20 m HA12 -> L = 1.508 m), poteaux/poutres, ratios cibles,
pagination dynamique, cartouche et hypotheses.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.generate_pdf_note import generer_note_calcul_chantier

SAMPLE_MISSION = {
    "projet": "Projet R+2 MZINDA",
    "semelles": [
        {"type": "S1", "axe": "A", "file": "1", "a": 1.2, "b": 1.2,
         "h": 0.3, "phi": 12, "nb_x": 8, "nb_y": 8},
        {"type": "S2", "axe": "B", "file": "2", "a": 1.5, "b": 1.5,
         "h": 0.4, "phi": 12, "nb_x": 10, "nb_y": 10},
    ],
}

SAMPLE_COMPLET = {
    "projet": {"nom": "Chantier Test"},
    "localisation": "Casablanca",
    "batiment": "Bloc A",
    "entreprise": "Entreprise Test",
    "redacteur": "T.Methodes",
    "visa": "BC-001",
    "date": "01/01/2026",
    "semelles": [
        {"type": "S1", "axe": "A", "file": "1", "a": 1.2, "b": 1.2,
         "h": 0.3, "phi": 12, "nb_x": 8, "nb_y": 8},
    ],
    "poteaux": [
        {"type": "P1", "axe": "A", "file": "1", "a": 0.25, "b": 0.35,
         "hauteur": 3.0, "long_bars": [{"nb": 6, "phi": 14}],
         "cadres": {"phi": 6, "esp": 0.15}},
    ],
    "poutres": [
        {"type": "N1", "axe": "", "b": 0.20, "h": 0.30, "portee": 4.0,
         "filants_inf": [{"nb": 3, "phi": 14}],
         "filants_sup": [{"nb": 2, "phi": 12}],
         "cadres": {"phi": 6, "esp": 0.18}},
    ],
}


def _texte_pdf(path):
    import fitz
    doc = fitz.open(path)
    texte = "".join(p.get_text() for p in doc)
    n = len(doc)
    doc.close()
    return texte, n


class TestNoteChantier(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.out = os.path.join(self._td.name, "note.pdf")

    def test_generation_exemple_mission(self):
        """L'exemple exact de la mission genere un PDF valide."""
        retour = generer_note_calcul_chantier(SAMPLE_MISSION, self.out)
        self.assertEqual(retour, self.out)
        self.assertTrue(os.path.exists(self.out))
        self.assertGreater(os.path.getsize(self.out), 5000)
        with open(self.out, "rb") as f:
            self.assertTrue(f.read(4) == b"%PDF")

    def test_exemple_chiffre_1508(self):
        """S1 (1.20 m, HA12) : L = (1.20-0.10) + 34x0.012 = 1.508 m."""
        generer_note_calcul_chantier(SAMPLE_MISSION, self.out)
        texte, _ = _texte_pdf(self.out)
        self.assertIn("1.508", texte)
        self.assertIn("Semelle S1", texte)
        self.assertIn("Semelle S2", texte)

    def test_poteaux_poutres_et_ratios(self):
        generer_note_calcul_chantier(SAMPLE_COMPLET, self.out)
        texte, _ = _texte_pdf(self.out)
        self.assertIn("ARM LONG", texte)
        self.assertIn("CADRE", texte)
        self.assertIn("Filants", texte)
        # Ratios cibles mission : semelles 35-50, poteaux 80-120
        self.assertIn("35", texte)
        self.assertIn("80", texte)
        self.assertIn("BON POUR", texte)
        self.assertIn("+5%", texte)
        self.assertIn("+3%", texte)

    def test_cartouche_et_hypotheses(self):
        generer_note_calcul_chantier(SAMPLE_COMPLET, self.out)
        texte, _ = _texte_pdf(self.out)
        self.assertIn("Chantier Test", texte)
        self.assertIn("Casablanca", texte)
        self.assertIn("Bloc A", texte)
        self.assertIn("HYPOTH", texte.upper())
        self.assertIn("C25/30", texte)
        self.assertIn("B500B", texte)

    def test_pagination_dynamique(self):
        generer_note_calcul_chantier(SAMPLE_MISSION, self.out)
        _, n = _texte_pdf(self.out)
        self.assertGreaterEqual(n, 1)
        texte, _ = _texte_pdf(self.out)
        import re
        pages = re.findall(r"Page (\d+) sur (\d+)", texte)
        self.assertTrue(pages)
        self.assertEqual(pages[0][1], str(n))

    def test_vide_sans_crash(self):
        """Aucune semelle : genere quand meme (totaux a zero)."""
        generer_note_calcul_chantier({"projet": "Vide", "semelles": []},
                                     self.out)
        self.assertTrue(os.path.exists(self.out))
        texte, _ = _texte_pdf(self.out)
        self.assertIn("0.00", texte)


if __name__ == "__main__":
    unittest.main()
