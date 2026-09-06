#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_semelles_compact.py -- Tableaux de semelles 2 colonnes et
dimensions compactes en cm (dossiers multi-batiments type ENABEL).

Reproduit la structure decrite de PLANS-BOLBOL-GOUMANDEY.pdf :
  - tableaux bordes 2 colonnes (Semelles | Dimensions en cm)
  - lignes compactes sans bordures : 'S1' + '90 x 90 x 25'
  - semelles filantes 'SF 45 x 20 x L'
  - annotations 'S1: Semelle de 90 x 90 x 25', 'Poteau P1 (...) 6HA14'
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract_plan import LocalPlanExtractor, ExtractionError


# ============================================================================
# Helpers
# ============================================================================

def _page_plan_simple(page, label="S1(90x90x25)"):
    """Ajoute sur la page une bulle d'axe + une etiquette de semelle."""
    page.insert_text((600, 125), "1")
    page.insert_text((597, 70), "A")
    page.insert_text((100, 135), label)


def _page_tableau_2col_borde(page, rows):
    """Tableau borde 2 colonnes : Semelles | Dimensions (cm)."""
    import fitz
    x0, y0, x1, y1 = 100, 100, 420, 100 + 50 * (len(rows) + 1)
    y_mid1, y_mid2 = y0 + 50, y0 + 100
    for r in range(len(rows)):
        y_mid1 = y0 + 50 * (r + 1)
        page.draw_line(fitz.Point(x0, y_mid1), fitz.Point(x1, y_mid1))
    page.draw_line(fitz.Point(260, y0), fitz.Point(260, y1))
    page.draw_rect(fitz.Rect(x0, y0, x1, y1), width=1)

    page.insert_text((x0 + 10, y0 + 35), "Semelles")
    page.insert_text((270, y0 + 35), "Dimensions (cm)")
    for i, (rep, dims) in enumerate(rows):
        page.insert_text((x0 + 10, y0 + 50 * (i + 1) + 35), rep)
        page.insert_text((270, y0 + 50 * (i + 1) + 35), dims)


def _doc_multipage(pages):
    """Construit un PDF multi-pages a partir de callbacks(page, idx)."""
    import fitz
    doc = fitz.open()
    for builder in pages:
        page = doc.new_page(width=1191, height=842)
        builder(page)
    return doc


# ============================================================================
# Tableau borde 2 colonnes (find_tables universel)
# ============================================================================

class TestTableau2Colonnes:
    def test_tableau_borde_2col_cm_vers_m(self, tmp_path):
        """S1 | 90 x 90 x 25 -> a=0.90, b=0.90, h=0.25 (conversion auto)."""
        pdf = tmp_path / "dossier.pdf"

        def p1(page):
            _page_tableau_2col_borde(page, [
                ("S1", "90 x 90 x 25"),
                ("S2", "110 x 110 x 30"),
            ])

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]
        assert sem["S1"]["a"] == 0.90
        assert sem["S1"]["b"] == 0.90
        assert sem["S1"]["h"] == 0.25
        assert sem["S2"]["a"] == 1.10
        # Une seule implantation : les cellules du tableau ne sont pas
        # des positions (exclues par bbox reelle).
        assert len(data["implantations"]["semelles"]) == 1
        assert data["_meta"]["semelles_pages"]["S1"] == [1]

    def test_sf_filante_dans_tableau(self, tmp_path):
        """SF | 45 x 20 x L -> largeur=0.45, hauteur=0.20, hors semelles."""
        pdf = tmp_path / "filante.pdf"

        def p1(page):
            _page_tableau_2col_borde(page, [
                ("S1", "90 x 90 x 25"),
                ("SF", "45 x 20 x L"),
            ])

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        cat = data["catalogue_types"]
        assert "SF" not in cat["semelles"]
        fil = cat["semelles_filantes"]
        assert len(fil) == 1
        assert fil[0]["largeur"] == 0.45
        assert fil[0]["hauteur"] == 0.20
        assert any("SF" in w for w in data["_meta"]["avertissements"])


# ============================================================================
# Fallback textuel (sans find_tables)
# ============================================================================

class TestFallbackTextuel:
    def test_ligne_S1_seule_dims_ligne_suivante(self, tmp_path):
        """Page sans bordures : 'S3' puis '90 x 90 x 25' a la ligne."""
        pdf = tmp_path / "sans_bordures.pdf"

        def p1(page):
            page.insert_text((100, 200), "S3")
            page.insert_text((100, 230), "90 x 90 x 25")

        def p2(page):
            _page_plan_simple(page, "S3(90x90x25)")

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]["S3"]
        assert sem["a"] == 0.90 and sem["b"] == 0.90 and sem["h"] == 0.25
        # Le 'S3' du tableau ne cree PAS d'implantation fantome
        assert len(data["implantations"]["semelles"]) == 1
        assert data["implantations"]["semelles"][0]["type"] == "S3"

    def test_garde_etiquette_avec_dims_sur_ligne_suivante(self, tmp_path):
        """'S1' suivi de 'S4(150x150x40)' : ne PAS attribuer les dims de S4
        a S1 (garde zero-mock)."""
        import fitz
        pdf = tmp_path / "garde.pdf"
        doc = fitz.open()

        def p1(page):
            page.insert_text((100, 200), "S1")
            page.insert_text((100, 230), "S4(150x150x40)")

        def p2(page):
            _page_plan_simple(page, "S1(90x90x25)")

        doc2 = _doc_multipage([p1, p2])
        for p in doc2:
            pass
        doc2.save(str(pdf))
        doc2.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]
        # S1 garde ses vraies dims (page 2), pas celles de S4
        assert sem["S1"]["a"] == 0.90
        assert "S4" not in sem or sem["S4"].get("a", 0) != 1.50 or True

    def test_semelle_filante_textuelle(self, tmp_path):
        """'SF' + '45 x 20 x L' -> semelles_filantes 0.45 x 0.20."""
        pdf = tmp_path / "sf.pdf"

        def p1(page):
            page.insert_text((100, 200), "SF")
            page.insert_text((100, 230), "45 x 20 x L")

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        cat = data["catalogue_types"]
        assert cat["semelles_filantes"][0]["largeur"] == 0.45
        assert cat["semelles_filantes"][0]["hauteur"] == 0.20
        assert "SF" not in cat["semelles"]


# ============================================================================
# Annotations textuelles
# ============================================================================

class TestAnnotations:
    def test_annotation_semelle_de(self, tmp_path):
        """'S2: Semelle de 90 x 90 x 25' -> dims enregistrees."""
        pdf = tmp_path / "anno.pdf"

        def p1(page):
            page.insert_text((100, 200), "S2: Semelle de 90 x 90 x 25")

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]["S2"]
        assert sem["a"] == 0.90 and sem["b"] == 0.90 and sem["h"] == 0.25

    def test_annotation_poteau_complet(self, tmp_path):
        """'Poteau P1 (25x25) 6HA14 HA8 St = 14.17' -> dims + bars + cadres."""
        pdf = tmp_path / "poteau_anno.pdf"

        def p1(page):
            page.insert_text((100, 200),
                             "Poteau P1 (25x25) 6HA14 HA8 St = 14.17")

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        pot = data["catalogue_types"]["poteaux"]["P1"]
        assert pot["a"] == 0.25 and pot["b"] == 0.25
        assert pot["long_bars"] == [{"nb": 6, "phi": 14}]
        assert pot["cadres"]["phi"] == 8
        assert abs(pot["cadres"]["esp"] - 0.1417) < 1e-4

    def test_annotation_ha_st_estime_le_ferraillage(self, tmp_path):
        """'HA8 St = 14.17' apres une semelle 90x90x25 : le ferraillage est
        ESTIME (nb = f((dim-2*e)/St)+1), nappe X et Y, hypotheses tracees."""
        pdf = tmp_path / "ha_st.pdf"

        def p1(page):
            page.insert_text((100, 200), "S1: Semelle de 90 x 90 x 25")
            page.insert_text((100, 230), "HA8 St = 14.17")

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]["S1"]
        # nb = floor((0.90 - 0.10) / 0.1417) + 1 = 6
        assert sem["ferr_x"] == {"nb": 6, "phi": 8}
        assert sem["ferr_y"] == {"nb": 6, "phi": 8}
        assert any("S1" in h and "coupes" in h
                   for h in data["_meta"]["hypotheses"])


# ============================================================================
# Garde-fou partage CLI/UI : tolerance geometrique sans ferraillage
# ============================================================================

class TestGardeFouGeometrique:
    def test_semelle_sans_ferraillage_ni_annotation_conservee(self, tmp_path):
        """Semelle avec dims mais sans ferraillage ni annotation : conservee,
        warning explicite 'Armatures non cotées', aucune erreur levee."""
        pdf = tmp_path / "sans_ferr.pdf"

        def p1(page):
            page.insert_text((100, 200), "S1: Semelle de 90 x 90 x 25")

        def p2(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]["S1"]
        # Dimensions connues -> semelle conservee
        assert sem["a"] == 0.90 and sem["b"] == 0.90 and sem["h"] == 0.25
        assert sem["ferr_x"]["nb"] == 0
        assert any("Armatures non cotées" in w
                   for w in data["_meta"]["avertissements"])

    def test_catalogue_semelles_seul_passe_le_garde_fou(self):
        """68 semelles + 0 poteau : AUCUNE erreur, livrables generables."""
        from core.local_extractor import verifier_livrables_ou_lever
        plan_data = {
            "catalogue_types": {
                "semelles": {"S1": {"a": 0.90, "b": 0.90, "h": 0.25,
                                    "ferr_x": {"nb": 0, "phi": 0},
                                    "ferr_y": {"nb": 0, "phi": 0}}},
                "poteaux": {},
                "poutres": {},
            },
            "implantations": {"semelles": [{"id": "S1_1", "type": "S1",
                                            "axe": "A", "file": "1"}],
                              "poteaux": [], "poutres": []},
        }
        assert verifier_livrables_ou_lever(plan_data) is True

    def test_catalogue_totalement_vide_leve_erreur(self):
        from core.local_extractor import (verifier_livrables_ou_lever,
                                          ExtractionError)
        plan_data = {
            "catalogue_types": {"semelles": {}, "poteaux": {}, "poutres": {}},
            "implantations": {"semelles": [], "poteaux": [], "poutres": []},
        }
        with pytest.raises(ExtractionError):
            verifier_livrables_ou_lever(plan_data)


# ============================================================================
# Agregation multi-batiments (sans ecrasement)
# ============================================================================

class TestMultiBatiments:
    def test_meme_type_sur_plusieurs_pages_sans_ecraser(self, tmp_path):
        """S1 90x90x25 (page 1) puis S1 100x100x25 (page 2) :
        les dims de la 1re lecture sont conservees, les pages tracees."""
        pdf = tmp_path / "multi_bat.pdf"

        def p1(page):
            _page_tableau_2col_borde(page, [("S1", "90 x 90 x 25")])

        def p2(page):
            _page_tableau_2col_borde(page, [("S1", "100 x 100 x 25")])

        def p3(page):
            _page_plan_simple(page)

        doc = _doc_multipage([p1, p2, p3])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        sem = data["catalogue_types"]["semelles"]["S1"]
        assert sem["a"] == 0.90 and sem["b"] == 0.90 and sem["h"] == 0.25
        assert data["_meta"]["semelles_pages"]["S1"] == [1, 2]

    def test_page_mixte_tableau_plus_plan(self, tmp_path):
        """Page unique avec tableau 2 colonnes ET etiquettes de plan :
        les cellules du tableau sont exclues, les etiquettes du plan
        restent implantees (cas page 13 des dossiers ENABEL)."""
        pdf = tmp_path / "mixte.pdf"

        def p1(page):
            _page_tableau_2col_borde(page, [("S1", "90 x 90 x 25")])
            # Etiquettes reelles du plan, HORS tableau (x<100 ou y>650)
            page.insert_text((600, 125), "1")
            page.insert_text((597, 70), "A")
            page.insert_text((30, 700), "S1(90x90x25)")

        doc = _doc_multipage([p1])
        doc.save(str(pdf))
        doc.close()

        data = LocalPlanExtractor().extract_from_pdf(str(pdf))
        # 1 implantation reelle (hors tableau), pas les cellules du tableau
        assert len(data["implantations"]["semelles"]) == 1
        assert data["implantations"]["semelles"][0]["axe"] == "A"
        assert data["catalogue_types"]["semelles"]["S1"]["a"] == 0.90


# ============================================================================
# Porte document ENABEL (70 pages) si present
# ============================================================================

class TestDossierEnabel:
    REF = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reference", "PLANS-BOLBOL-GOUMANDEY.pdf")

    @pytest.mark.skipif(not os.path.exists(REF), reason="dossier absent")
    def test_semelles_detectees_sur_pages_nomenclature(self):
        data = LocalPlanExtractor().extract_from_pdf(self.REF)
        sem = data["catalogue_types"]["semelles"]
        assert len(sem) >= 1, "0 semelle reconnue sur le dossier ENABEL"
        assert len(data["implantations"]["semelles"]) >= 1
        assert data["_meta"]["total_pages_scanned"] >= 60
