#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_validator.py -- Tests du pre-flight PlanSanityValidator.

Valide :
  - L'acceptation d'un plan PDF / DXF contenant des mots-cles de ferraillage
  - Le rejet formel d'un fichier texte ou d'un PDF sans termes de beton arme
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.validator import PlanSanityValidator, CIVIL_KEYWORDS


# ============================================================================
# Helpers : fabrication de documents de test
# ============================================================================

def _creer_pdf_plan(path, paysage=True):
    """Genere un PDF simulant un plan BA : grand format paysage, texte metier,
    codes HA et dessins vectoriels."""
    import fitz

    largeur, hauteur = (1191, 842) if paysage else (842, 1191)
    doc = fitz.open()
    page = doc.new_page(width=largeur, height=hauteur)

    texte = (
        "Plan de fondation - Implantation generale\n"
        "semelle poteau poutre armature cadre coffrage enrobage axe\n"
        "Ferraillage : 6HA14 nappe inferieure, cadres T6 espacement 0.15\n"
        "Echelle 1:50 - Coupe detail repartition"
    )
    page.insert_textbox(fitz.Rect(50, 50, largeur - 50, 300), texte,
                        fontsize=12)

    # Densite vectorielle : plus de 50 entites dessinees
    for i in range(60):
        x = 50 + (i % 10) * 40
        y = 350 + (i // 10) * 40
        page.draw_rect(fitz.Rect(x, y, x + 30, y + 30), width=0.5)

    doc.save(str(path))
    doc.close()


def _creer_pdf_texte(path, paysage=False):
    """Genere un PDF administratif (CV / contrat) sans aucun terme de BA."""
    import fitz

    largeur, hauteur = (1191, 842) if paysage else (595, 842)
    doc = fitz.open()
    page = doc.new_page(width=largeur, height=hauteur)

    texte = (
        "Curriculum Vitae\n"
        "Experience professionnelle\n"
        "Formation et competences linguistiques\n"
        "Centres d'interet : lecture, course a pied\n"
        "References disponibles sur demande."
    )
    page.insert_textbox(fitz.Rect(50, 50, largeur - 50, 400), texte,
                        fontsize=12)

    doc.save(str(path))
    doc.close()


def _creer_dxf_plan(path, nb_entites=25):
    """Genere un DXF technique avec un modelspace peuple."""
    import ezdxf

    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    for i in range(nb_entites):
        msp.add_line((i, 0), (i + 10, 15))
    doc.saveas(str(path))


# ============================================================================
# PDF : plan valide
# ============================================================================

class TestPdfPlanValide:
    def test_pdf_plan_paysage_accepte(self, tmp_path):
        pdf = tmp_path / "plan_ba.pdf"
        _creer_pdf_plan(pdf, paysage=True)
        is_valid, message, score = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert score >= 40
        assert "validé" in message.lower() or "plan" in message.lower()

    def test_pdf_plan_score_suffisant(self, tmp_path):
        pdf = tmp_path / "plan_ba.pdf"
        _creer_pdf_plan(pdf)
        _, _, score = PlanSanityValidator.validate_file(str(pdf))
        assert score >= 60

    def test_pdf_plan_termes_cles_detectes(self, tmp_path):
        pdf = tmp_path / "plan_ba.pdf"
        _creer_pdf_plan(pdf)
        import fitz
        with fitz.open(str(pdf)) as doc:
            mots = {w[4].lower().strip(":,.;()") for w in doc[0].get_text("words")}
        assert len(CIVIL_KEYWORDS.intersection(mots)) >= 5


# ============================================================================
# PDF : documents textuels acceptes avec reserve (JAMAIS de blocage dur)
# ============================================================================

class TestPdfRejetes:
    def test_pdf_cv_accepte_avec_reserve(self, tmp_path):
        """Un PDF textuel (CV) n'est plus bloque : accepte avec reserve,
        l'extraction en aval levera l'erreur explicite."""
        pdf = tmp_path / "cv.pdf"
        _creer_pdf_texte(pdf)
        is_valid, message, score = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert score < 40
        assert "réserve" in message.lower()

    def test_pdf_vide_accepte_avec_reserve(self, tmp_path):
        import fitz
        pdf = tmp_path / "vide.pdf"
        doc = fitz.open()
        doc.new_page(width=595, height=842)
        doc.save(str(pdf))
        doc.close()
        is_valid, message, _ = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert "réserve" in message.lower()

    def test_pdf_corrompu_accepte_pour_analyse(self, tmp_path):
        pdf = tmp_path / "corrompu.pdf"
        pdf.write_bytes(b"ceci n'est pas un pdf valide")
        is_valid, message, _ = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert "accepté pour analyse" in message.lower()

    def test_pdf_multipage_page_de_garde(self, tmp_path):
        """Page 1 = garde sans mots-cles, page 2 = nomenclature :
        le scan multi-pages doit detecter le contenu reel."""
        import fitz
        pdf = tmp_path / "multipage_garde.pdf"
        doc = fitz.open()
        # Page de garde : aucun terme metier
        p1 = doc.new_page(width=595, height=842)
        p1.insert_text((50, 100), "Dossier de consultation des entreprises")
        # Page technique
        _page_plan = doc.new_page(width=1191, height=842)
        _page_plan.insert_textbox(
            fitz.Rect(50, 50, 1100, 300),
            "Plan de fondation - semelle poteau armature cadre coffrage "
            "enrobage axe - Ferraillage : 6HA14 nappe, cadres T6 - Echelle 1:50",
            fontsize=12)
        for i in range(60):
            _page_plan.draw_rect(fitz.Rect(50 + (i % 10) * 40,
                                           350 + (i // 10) * 40,
                                           80 + (i % 10) * 40,
                                           380 + (i // 10) * 40), width=0.5)
        doc.save(str(pdf))
        doc.close()

        is_valid, message, score = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert score >= 50
        assert "validé" in message.lower()
        assert "Pages : 2" in message

    def test_pdf_vectoriel_plancher_50(self, tmp_path):
        """PDF vectoriel sans mots-cles lisibles : plancher de 50 d'office."""
        import fitz
        pdf = tmp_path / "vectoriel.pdf"
        doc = fitz.open()
        page = doc.new_page(width=1191, height=842)
        for i in range(60):
            page.draw_rect(fitz.Rect(50 + (i % 10) * 40,
                                     50 + (i // 10) * 40,
                                     80 + (i % 10) * 40,
                                     80 + (i // 10) * 40), width=0.5)
        doc.save(str(pdf))
        doc.close()
        is_valid, message, score = PlanSanityValidator.validate_file(str(pdf))
        assert is_valid is True
        assert score >= 50


# ============================================================================
# AutoCAD : DXF / DWG
# ============================================================================

class TestCad:
    def test_dxf_plan_accepte(self, tmp_path):
        dxf = tmp_path / "plan.dxf"
        _creer_dxf_plan(dxf, nb_entites=25)
        is_valid, message, score = PlanSanityValidator.validate_file(str(dxf))
        assert is_valid is True
        assert score == 95
        assert "entités DAO" in message

    def test_dxf_vide_accepte_avec_reserve(self, tmp_path):
        """DXF quasi vide : accepte avec reserve, jamais de blocage dur."""
        import ezdxf
        dxf = tmp_path / "vide.dxf"
        doc = ezdxf.new("R12")
        doc.saveas(str(dxf))
        is_valid, message, score = PlanSanityValidator.validate_file(str(dxf))
        assert is_valid is True
        assert score == 10
        assert "réserve" in message.lower()

    def test_dwg_accepte_par_defaut(self, tmp_path):
        dwg = tmp_path / "plan.dwg"
        dwg.write_bytes(b"AC1024")  # contenu quelconque
        is_valid, message, score = PlanSanityValidator.validate_file(str(dwg))
        assert is_valid is True
        assert score == 90

    def test_dxf_corrompu_accepte_pour_analyse(self, tmp_path):
        dxf = tmp_path / "corrompu.dxf"
        dxf.write_bytes(b"ceci n'est pas un dxf")
        is_valid, message, _ = PlanSanityValidator.validate_file(str(dxf))
        assert is_valid is True
        assert "accepté pour analyse" in message.lower()


# ============================================================================
# Images
# ============================================================================

class TestImages:
    def test_grande_image_acceptee(self, tmp_path):
        from PIL import Image
        img = tmp_path / "scan.png"
        Image.new("RGB", (3000, 1500), color="white").save(str(img))
        is_valid, message, score = PlanSanityValidator.validate_file(str(img))
        assert is_valid is True
        assert score >= 40

    def test_petite_image_rejetee(self, tmp_path):
        from PIL import Image
        img = tmp_path / "photo.jpg"
        Image.new("RGB", (400, 400), color="white").save(str(img))
        is_valid, message, _ = PlanSanityValidator.validate_file(str(img))
        assert is_valid is False
        assert "résolution" in message.lower()


# ============================================================================
# Cas limites
# ============================================================================

class TestCasLimites:
    def test_fichier_introuvable(self):
        is_valid, message, score = PlanSanityValidator.validate_file(
            "Z:/inexistant/plan.pdf")
        assert is_valid is False
        assert score == 0
        assert "introuvable" in message.lower()

    def test_extension_texte_rejetee(self, tmp_path):
        txt = tmp_path / "facture.txt"
        txt.write_text("Facture numero 1234, montant 500 EUR", encoding="utf-8")
        is_valid, message, _ = PlanSanityValidator.validate_file(str(txt))
        assert is_valid is False
        assert "non supportée" in message.lower()

    def test_extension_docx_rejetee(self, tmp_path):
        docx = tmp_path / "contrat.docx"
        docx.write_bytes(b"PK\x03\x04")
        is_valid, _, _ = PlanSanityValidator.validate_file(str(docx))
        assert is_valid is False

    def test_retour_tuple(self, tmp_path):
        txt = tmp_path / "x.txt"
        txt.write_text("hello")
        result = PlanSanityValidator.validate_file(str(txt))
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(v, t) for v, t in
                   zip(result, (bool, str, int)))
