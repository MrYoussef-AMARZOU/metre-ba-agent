"""
tests/test_civil_engine.py — Suite de tests unitaires pour le CivilEngine.

Valide les calculs déterministes normalisés Béton Armé.
"""
import math
import sys
from pathlib import Path

import pytest

# Ajouter le répertoire parent au path pour importer core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.calculator import CivilEngine, CalculBarre, CalculElement
from core.schemas import (
    BarreAcierSchema,
    ElementStructureSchema,
    FamilleElement,
    ProjetBAParseOutput,
    RoleArmature,
    TypeBarre,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def engine():
    """Instance du CivilEngine avec paramètres par défaut."""
    return CivilEngine()


@pytest.fixture
def engine_custom():
    """Instance avec paramètres personnalisés."""
    return CivilEngine(
        enrobage_m=0.04,
        coef_ancrage=30,
        coef_cadre=20.0,
        coef_epingle=20,
        coef_recouvrement=30,
        espacement_cadres_m=0.20,
    )


# ============================================================================
# Tests: Masses linéiques
# ============================================================================

class TestMasseLineique:
    """Tests des masses linéiques normalisées."""

    def test_T6(self, engine):
        assert engine.masse_lineique(6) == pytest.approx(0.222, abs=1e-3)

    def test_T8(self, engine):
        assert engine.masse_lineique(8) == pytest.approx(0.395, abs=1e-3)

    def test_T10(self, engine):
        assert engine.masse_lineique(10) == pytest.approx(0.617, abs=1e-3)

    def test_T12(self, engine):
        assert engine.masse_lineique(12) == pytest.approx(0.888, abs=1e-3)

    def test_T14(self, engine):
        assert engine.masse_lineique(14) == pytest.approx(1.210, abs=1e-3)

    def test_T16(self, engine):
        assert engine.masse_lineique(16) == pytest.approx(1.580, abs=1e-3)

    def test_T20(self, engine):
        assert engine.masse_lineique(20) == pytest.approx(2.470, abs=1e-3)

    def test_T25(self, engine):
        assert engine.masse_lineique(25) == pytest.approx(3.850, abs=1e-3)

    def test_T32(self, engine):
        assert engine.masse_lineique(32) == pytest.approx(6.310, abs=1e-3)

    def test_diametre_non_standard(self, engine):
        with pytest.raises(ValueError, match="non standard"):
            engine.masse_lineique(7)

    def test_formule_d2_sur_162(self, engine):
        """Vérifie que la formule d²/162 correspond aux valeurs tabulées."""
        for d in [6, 8, 10, 12, 14, 16, 20, 25, 32]:
            formule = engine.masse_lineique_formule(d)
            table = engine.masse_lineique(d)
            assert formule == pytest.approx(table, rel=0.05), (
                f"T{d}: formule={formule:.4f}, table={table:.4f}"
            )


# ============================================================================
# Tests: Longueurs de barres
# ============================================================================

class TestLongueurs:
    """Tests des calculs de longueurs."""

    def test_ancrage_T12(self, engine):
        # 34 × 12 / 1000 = 0.408 m
        assert engine.longueur_ancrage(12) == pytest.approx(0.408, abs=1e-3)

    def test_ancrage_T6(self, engine):
        # 34 × 6 / 1000 = 0.204 m
        assert engine.longueur_ancrage(6) == pytest.approx(0.204, abs=1e-3)

    def test_cadre_25x35_T6(self, engine):
        # 2×(0.25+0.35) - 0.05 + 20.5×6/1000 = 1.20 - 0.05 + 0.123 = 1.273
        assert engine.longueur_developpee_cadre(0.25, 0.35, 6) == pytest.approx(
            1.273, abs=1e-3
        )

    def test_cadre_40x40_T6(self, engine):
        # 2×(0.40+0.40) - 0.05 + 20.5×6/1000 = 1.60 - 0.05 + 0.123 = 1.673
        assert engine.longueur_developpee_cadre(0.40, 0.40, 6) == pytest.approx(
            1.673, abs=1e-3
        )

    def test_epingle_T6(self, engine):
        # 0.25 - 0.05 + 22×6/1000 = 0.20 + 0.132 = 0.332
        assert engine.longueur_epingle(0.25, 6) == pytest.approx(0.332, abs=1e-3)

    def test_nappe_sans_recouvrement(self, engine):
        # (1.50 - 0.05) + 34×12/1000 = 1.45 + 0.408 = 1.858
        assert engine.longueur_nappe(1.50, 12, avec_recouvrement=False) == pytest.approx(
            1.858, abs=1e-3
        )

    def test_nappe_avec_recouvrement(self, engine):
        # 1.858 + 36×12/1000 = 1.858 + 0.432 = 2.290
        assert engine.longueur_nappe(1.50, 12, avec_recouvrement=True) == pytest.approx(
            2.290, abs=1e-3
        )


# ============================================================================
# Tests: Nombre de barres
# ============================================================================

class TestNombreBarres:
    """Tests du calcul du nombre de barres."""

    def test_nb_cadres_3m(self, engine):
        # ceil(3.0 / 0.15) + 2 = 20 + 2 = 22
        assert engine.nb_cadres(3.0, 0.15) == 22

    def test_nb_cadres_2m(self, engine):
        # ceil(2.0 / 0.15) + 2 = 14 + 2 = 16
        assert engine.nb_cadres(2.0, 0.15) == 16

    def test_nb_cadres_4_78m(self, engine):
        # ceil(4.78 / 0.15) + 2 = 32 + 2 = 34
        assert engine.nb_cadres(4.78, 0.15) == 34

    def test_nb_cadres_espacement_zero(self, engine):
        with pytest.raises(ValueError, match="positif"):
            engine.nb_cadres(3.0, 0.0)

    def test_nb_barres_nappe_1m50(self, engine):
        # ceil(1.50 / 0.15) + 1 = 10 + 1 = 11
        assert engine.nb_barres_nappe(1.50, 0.15) == 11

    def test_nb_barres_nappe_1m20(self, engine):
        # ceil(1.20 / 0.15) + 1 = 8 + 1 = 9
        assert engine.nb_barres_nappe(1.20, 0.15) == 9


# ============================================================================
# Tests: Calcul complet d'une semelle isolée
# ============================================================================

class TestCalculSemelle:
    """Tests du calcul complet d'une semelle."""

    def test_semelle_120x120x30_8HA12(self, engine):
        """
        Semelle 1.20 × 1.20 × 0.30 m avec 8HA12 dans chaque sens.
        """
        result = engine.calculer_semelle(
            a_m=1.20, b_m=1.20, h_m=0.30,
            nappe_x_diam=12, nappe_x_nb=8,
            nappe_y_diam=12, nappe_y_nb=8,
        )

        # Volume
        assert result.volume_m3 == pytest.approx(1.20 * 1.20 * 0.30, abs=1e-4)

        # 2 nappes d'armatures
        assert len(result.barres) == 2

        # Nappe X: 8 barres
        nappe_x = result.barres[0]
        assert nappe_x.nombre == 8
        assert nappe_x.diametre_mm == 12
        assert nappe_x.role == "nappe_x"

        # Longueur nappe X: (1.20 - 0.05) + 34×12/1000 + 36×12/1000 = 1.15 + 0.408 + 0.432 = 1.99
        assert nappe_x.longueur_unitaire_m == pytest.approx(1.99, abs=1e-3)

        # Nappe Y: idem (carrée)
        nappe_y = result.barres[1]
        assert nappe_y.nombre == 8
        assert nappe_y.longueur_unitaire_m == pytest.approx(1.99, abs=1e-3)

        # Poids total
        poids_unitaire = 0.888 * 1.99  # HA12 × longueur (avec recouvrement)
        poids_total = 2 * 8 * poids_unitaire
        assert result.poids_total_acier_kg == pytest.approx(poids_total, abs=0.1)

    def test_semelle_150x150x40_11HA12(self, engine):
        """
        Semelle 1.50 × 1.50 × 0.40 m avec 11HA12 dans chaque sens.
        """
        result = engine.calculer_semelle(
            a_m=1.50, b_m=1.50, h_m=0.40,
            nappe_x_diam=12, nappe_x_nb=11,
            nappe_y_diam=12, nappe_y_nb=11,
        )

        assert result.volume_m3 == pytest.approx(1.50 * 1.50 * 0.40, abs=1e-4)
        assert result.poids_total_acier_kg > 0

    def test_semelle_100x100x25_6HA12(self, engine):
        """
        Semelle 1.00 × 1.00 × 0.25 m avec 6HA12 dans chaque sens.
        """
        result = engine.calculer_semelle(
            a_m=1.00, b_m=1.00, h_m=0.25,
            nappe_x_diam=12, nappe_x_nb=6,
            nappe_y_diam=12, nappe_y_nb=6,
        )

        assert result.volume_m3 == pytest.approx(0.25, abs=1e-4)

    def test_semelle_differentiel(self, engine):
        """
        Semelle rectangulaire 1.20 × 0.80 × 0.30 m.
        """
        result = engine.calculer_semelle(
            a_m=1.20, b_m=0.80, h_m=0.30,
            nappe_x_diam=12, nappe_x_nb=8,
            nappe_y_diam=10, nappe_y_nb=6,
        )

        assert result.volume_m3 == pytest.approx(0.288, abs=1e-4)
        assert result.barres[0].diametre_mm == 12  # X
        assert result.barres[1].diametre_mm == 10  # Y


# ============================================================================
# Tests: Calcul complet d'un poteau
# ============================================================================

class TestCalculPoteau:
    """Tests du calcul complet d'un poteau."""

    def test_poteau_25x35(self, engine):
        """Poteau 0.25 × 0.35 m, hauteur 3.0 m, 8 long T14, cadres T6."""
        result = engine.calculer_poteau(
            b_m=0.25, h_m=0.35, hauteur_m=3.0,
            nb_longitudinaux=8, diam_longitudinal=14, diam_cadre=6,
        )

        assert result.volume_m3 == pytest.approx(0.25 * 0.35 * 3.0, abs=1e-4)
        assert len(result.barres) == 2
        assert result.barres[0].role == "longitudinal"
        assert result.barres[0].nombre == 8
        assert result.barres[1].role == "cadre"

    def test_poteau_40x40(self, engine):
        """Poteau 0.40 × 0.40 m, hauteur 3.5 m."""
        result = engine.calculer_poteau(
            b_m=0.40, h_m=0.40, hauteur_m=3.5,
            nb_longitudinaux=12, diam_longitudinal=16, diam_cadre=8,
        )

        assert result.volume_m3 == pytest.approx(0.40 * 0.40 * 3.5, abs=1e-4)
        assert result.poids_total_acier_kg > 0


# ============================================================================
# Tests: Calcul complet d'une poutre
# ============================================================================

class TestCalculPoutre:
    """Tests du calcul complet d'une poutre."""

    def test_poutre_20x30(self, engine):
        """Poutre 0.20 × 0.30 m, longueur 4.0 m."""
        result = engine.calculer_poutre(
            b_m=0.20, h_m=0.30, longueur_m=4.0,
            nb_longitudinaux=4, diam_longitudinal=14, diam_cadre=8,
        )

        assert result.volume_m3 == pytest.approx(0.20 * 0.30 * 4.0, abs=1e-4)
        assert result.barres[0].nombre == 4  # Longitudinaux
        assert result.barres[1].role == "cadre"

    def test_poutre_40x90(self, engine):
        """Poutre principale 0.40 × 0.90 m, longueur 7.0 m."""
        result = engine.calculer_poutre(
            b_m=0.40, h_m=0.90, longueur_m=7.0,
            nb_longitudinaux=6, diam_longitudinal=20, diam_cadre=10,
        )

        assert result.volume_m3 == pytest.approx(2.52, abs=1e-4)
        assert result.poids_total_acier_kg > 0


# ============================================================================
# Tests: Ventilation
# ============================================================================

class TestVentilation:
    """Tests de la ventilation des poids."""

    def test_ventilation_par_diametre(self, engine):
        elems = [
            engine.calculer_semelle(1.0, 1.0, 0.25, 12, 6, 12, 6),
            engine.calculer_semelle(1.2, 1.2, 0.30, 12, 8, 12, 8),
        ]
        vent = CivilEngine.ventiler_par_diamètre(elems)
        assert 12 in vent
        assert vent[12] > 0

    def test_ventilation_par_famille(self, engine):
        sem = engine.calculer_semelle(1.0, 1.0, 0.25, 12, 6, 12, 6)
        # CalculElement is frozen, so we create new ones with explicit famille
        from dataclasses import replace
        sem_with_famille = replace(sem, famille="SEMELLE")
        pot = engine.calculer_poteau(0.25, 0.35, 3.0, 8, 14, 6)
        pot_with_famille = replace(pot, famille="POTEAU")

        vent = CivilEngine.ventiler_par_famille([sem_with_famille, pot_with_famille])
        assert "SEMELLE" in vent
        assert "POTEAU" in vent


# ============================================================================
# Tests: Schémas Pydantic
# ============================================================================

class TestSchemas:
    """Tests des modèles de données Pydantic."""

    def test_barre_acier_creation(self):
        barre = BarreAcierSchema(
            diametre=12,
            type_barre=TypeBarre.HA,
            role=RoleArmature.NAPPE_X,
            nombre=8,
            longueur_unitaire_m=1.558,
            poids_unitaire_kg=0.888,
        )
        assert barre.diametre == 12
        assert barre.type_barre == TypeBarre.HA
        assert barre.role == RoleArmature.NAPPE_X

    def test_element_structure_creation(self):
        elem = ElementStructureSchema(
            famille=FamilleElement.SEMELLE,
            repere="S1",
            axe="A1",
            dimensions={"a": 1.20, "b": 1.20, "h": 0.30},
        )
        assert elem.famille == FamilleElement.SEMELLE
        assert elem.repere == "S1"
        assert elem.dimensions["a"] == 1.20

    def test_projet_ba_parse_output(self):
        proj = ProjetBAParseOutput(
            nom_projet="Test Project",
            elements=[
                ElementStructureSchema(
                    famille=FamilleElement.SEMELLE,
                    repere="S1",
                    dimensions={"a": 1.0, "b": 1.0, "h": 0.25},
                ),
                ElementStructureSchema(
                    famille=FamilleElement.SEMELLE,
                    repere="S2",
                    dimensions={"a": 1.2, "b": 1.2, "h": 0.30},
                ),
                ElementStructureSchema(
                    famille=FamilleElement.POTEAU,
                    repere="P1",
                    dimensions={"b": 0.25, "h": 0.35},
                ),
            ],
        )
        assert proj.count_by_famille() == {"SEMELLE": 2, "POTEAU": 1}
        assert len(proj.by_famille(FamilleElement.SEMELLE)) == 2

    def test_barre_acier_frozen(self):
        barre = BarreAcierSchema(
            diametre=12, type_barre=TypeBarre.HA,
            role=RoleArmature.NAPPE_X, nombre=8,
        )
        with pytest.raises(Exception):
            barre.diametre = 16


# ============================================================================
# Tests: Paramètres personnalisés
# ============================================================================

class TestParametresPersonnalises:
    """Tests avec des paramètres différents des défauts."""

    def test_enrobage_different(self, engine_custom):
        # enrobage = 0.04 (au lieu de 0.05)
        long = engine_custom.longueur_nappe(1.50, 12, avec_recouvrement=False)
        # (1.50 - 0.04) + 30×12/1000 = 1.46 + 0.36 = 1.82
        assert long == pytest.approx(1.82, abs=1e-3)

    def test_coef_cadre_different(self, engine_custom):
        # coef_cadre = 20.0 (au lieu de 20.5)
        long = engine_custom.longueur_developpee_cadre(0.25, 0.35, 6)
        # 2×(0.25+0.35) - 0.04 + 20.0×6/1000 = 1.20 - 0.04 + 0.12 = 1.28
        assert long == pytest.approx(1.28, abs=1e-3)
