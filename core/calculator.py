"""
core/calculator.py — Moteur déterministe d'ingénierie civile.

Effectue les calculs normalisés Béton Armé sans jamais solliciter de LLM.
Toutes les formules sont purement mathématiques et vérifiables.

Références :
- Masse linéique: d² / 162 (kg/m) — formule normalisée aciers
- Longueur développée avec ancrage standard: (L - enrobage) + coef_ancrage * d
- Nombre de cadres: ceil(L / espacement) + 2
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .schemas import (
    BarreAcierSchema,
    ElementStructureSchema,
    FamilleElement,
    ProjetBAParseOutput,
    RoleArmature,
    TypeBarre,
)


# ============================================================================
# Constantes normalisées (indépendantes du projet)
# ============================================================================

# Masse linéique des aciers HA (kg/m) — valeurs normalisées NF EN 10080
MASSES_LINÉAIRES_KG_M: Dict[int, float] = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.210,
    16: 1.580,
    20: 2.470,
    25: 3.850,
    32: 6.310,
}

# Diamètres standardisés autorisés
DIAMÈTRES_AUTORISÉS: Tuple[int, ...] = (6, 8, 10, 12, 14, 16, 20, 25, 32)

# Enrobage standard (m) — selon Eurocode 2, Table 4.4N
ENROBAGE_STANDARD: float = 0.05

# Coefficients d'ancrage (multiples du diamètre)
COEF_ANCRAGE: int = 34          # Ancrage statique
COEF_CADRE: float = 20.5        # Cadres (développé)
COEF_EPIGLE: int = 22           # Épingles
COEF_RECOUVREMENT: int = 36     # Recouvrement

# Espacement par défaut des cadres (m)
ESPACEMENT_CADRES_DEFAUT: float = 0.15


# ============================================================================
# Classes de calcul
# ============================================================================

@dataclass(frozen=True)
class CalculBarre:
    """Résultat du calcul d'une barre d'acier."""
    diametre_mm: int
    type_barre: str
    role: str
    nombre: int
    longueur_unitaire_m: float
    masse_lineique_kg_m: float
    poids_total_kg: float


@dataclass(frozen=True)
class CalculElement:
    """Résultat du calcul complet d'un élément."""
    repere: str
    famille: str
    volume_m3: float
    surface_contact_m2: float
    barres: List[CalculBarre] = field(default_factory=list)
    poids_total_acier_kg: float = 0.0


@dataclass(frozen=True)
class CalculProjet:
    """Résumé des calculs pour un projet complet."""
    elements: List[CalculElement] = field(default_factory=list)
    volume_total_beton_m3: float = 0.0
    poids_total_acier_kg: float = 0.0
    ventilation_par_diamètre: Dict[int, float] = field(default_factory=dict)
    ventilation_par_famille: Dict[str, float] = field(default_factory=dict)


# ============================================================================
# Moteur CivilEngine
# ============================================================================

class CivilEngine:
    """
    Moteur déterministe de calcul Béton Armé.

    Tous les calculs sont purement mathématiques et vérifiables.
    Aucune dépendance à une interface graphique ou à un API externe.
    """

    def __init__(
        self,
        enrobage_m: float = ENROBAGE_STANDARD,
        coef_ancrage: int = COEF_ANCRAGE,
        coef_cadre: float = COEF_CADRE,
        coef_epingle: int = COEF_EPIGLE,
        coef_recouvrement: int = COEF_RECOUVREMENT,
        espacement_cadres_m: float = ESPACEMENT_CADRES_DEFAUT,
    ):
        self.enrobage_m = enrobage_m
        self.coef_ancrage = coef_ancrage
        self.coef_cadre = coef_cadre
        self.coef_epingle = coef_epingle
        self.coef_recouvrement = coef_recouvrement
        self.espacement_cadres_m = espacement_cadres_m

    # ------------------------------------------------------------------
    # Masses linéiques
    # ------------------------------------------------------------------

    @staticmethod
    def masse_lineique(diametre_mm: int) -> float:
        """
        Masse linéique normalisée d'une barre d'acier.

        Formule: d² / 162 (kg/m)

        Args:
            diametre_mm: Diamètre de la barre en mm.

        Returns:
            Masse linéique en kg/m.

        Raises:
            ValueError: Si le diamètre n'est pas dans la liste standard.
        """
        if diametre_mm not in DIAMÈTRES_AUTORISÉS:
            raise ValueError(
                f"Diamètre {diametre_mm} mm non standard. "
                f"Autorisés: {DIAMÈTRES_AUTORISÉS}"
            )
        return MASSES_LINÉAIRES_KG_M[diametre_mm]

    @staticmethod
    def masse_lineique_formule(diametre_mm: int) -> float:
        """
        Calcul de la masse linéique par la formule d²/162.

        Utile pour vérification ou pour des diamètres non dans la table.
        """
        return (diametre_mm ** 2) / 162.0

    # ------------------------------------------------------------------
    # Longueurs de barres
    # ------------------------------------------------------------------

    def longueur_ancrage(self, diametre_mm: int) -> float:
        """
        Longueur d'ancrage standard.

        Formule: coef_ancrage × d (en mm) → converti en m.

        Args:
            diametre_mm: Diamètre en mm.

        Returns:
            Longueur d'ancrage en mètres.
        """
        return self.coef_ancrage * diametre_mm / 1000.0

    def longueur_developpee_cadre(
        self, largeur_m: float, hauteur_m: float, diametre_mm: int
    ) -> float:
        """
        Longueur développée d'un cadre.

        Formule: 2×(b + h) - enrobage + coef_cadre × d

        Args:
            largeur_m: Largeur de la section en m.
            hauteur_m: Hauteur de la section en m.
            diametre_mm: Diamètre du cadre en mm.

        Returns:
            Longueur développée en mètres.
        """
        perimetre = 2.0 * (largeur_m + hauteur_m)
        ancrage = self.coef_cadre * diametre_mm / 1000.0
        return perimetre - self.enrobage_m + ancrage

    def longueur_epingle(self, largeur_m: float, diametre_mm: int) -> float:
        """
        Longueur d'une épinglette.

        Formule: b - enrobage + coef_epingle × d

        Args:
            largeur_m: Largeur de la section en m.
            diametre_mm: Diamètre de l'épingle en mm.

        Returns:
            Longueur en mètres.
        """
        return largeur_m - self.enrobage_m + self.coef_epingle * diametre_mm / 1000.0

    def longueur_nappe(
        self, dimension_m: float, diametre_mm: int, avec_recouvrement: bool = True
    ) -> float:
        """
        Longueur d'une nappe d'armature.

        Formule: (dimension - enrobage) + ancrage  [± recouvrement]

        Args:
            dimension_m: Dimension de l'élément en m.
            diametre_mm: Diamètre de la barre en mm.
            avec_recouvrement: Si True, ajoute le recouvrement.

        Returns:
            Longueur en mètres.
        """
        longueur = dimension_m - self.enrobage_m + self.coef_ancrage * diametre_mm / 1000.0
        if avec_recouvrement:
            longueur += self.coef_recouvrement * diametre_mm / 1000.0
        return longueur

    # ------------------------------------------------------------------
    # Nombre de barres
    # ------------------------------------------------------------------

    @staticmethod
    def nb_cadres(longueur_element_m: float, espacement_m: float) -> int:
        """
        Nombre de cadres dans un élément.

        Formule: ⌈longueur / espacement⌉ + 2

        Args:
            longueur_element_m: Longueur de l'élément en m.
            espacement_m: Espacement entre cadres en m.

        Returns:
            Nombre entier de cadres.
        """
        if espacement_m <= 0:
            raise ValueError(f"Espacement doit être positif, reçu: {espacement_m}")
        return math.ceil(longueur_element_m / espacement_m) + 2

    @staticmethod
    def nb_barres_nappe(
        dimension_perpendiculaire_m: float, espacement_m: float
    ) -> int:
        """
        Nombre de barres dans une nappe.

        Formule: ⌈dimension / espacement⌉ + 1

        Args:
            dimension_perpendiculaire_m: Dimension perpendiculaire aux barres (m).
            espacement_m: Entre-barres en m.

        Returns:
            Nombre de barres.
        """
        if espacement_m <= 0:
            raise ValueError(f"Espacement doit être positif, reçu: {espacement_m}")
        return math.ceil(dimension_perpendiculaire_m / espacement_m) + 1

    # ------------------------------------------------------------------
    # Calcul complet d'un élément
    # ------------------------------------------------------------------

    def calculer_semelle(
        self,
        a_m: float,
        b_m: float,
        h_m: float,
        nappe_x_diam: int,
        nappe_x_nb: int,
        nappe_y_diam: int,
        nappe_y_nb: int,
    ) -> CalculElement:
        """
        Calcul complet d'une semelle isolée.

        Args:
            a_m: Longueur en m.
            b_m: Largeur en m.
            h_m: Hauteur en m.
            nappe_x_diam: Diamètre des barresnappe X (mm).
            nappe_x_nb: Nombre de barres nappe X.
            nappe_y_diam: Diamètre des barres nappe Y (mm).
            nappe_y_nb: Nombre de barres nappe Y.

        Returns:
            CalculElement avec volume, surface et armatures.
        """
        volume = a_m * b_m * h_m
        # Surface de contact = 2×(a×h + b×h) + a×b (fond + dessus)
        surface = 2.0 * (a_m * h_m + b_m * h_m) + a_m * b_m

        barres = []

        # Nappe X (longueur = a_m)
        long_x = self.longueur_nappe(a_m, nappe_x_diam)
        poids_x = self.masse_lineique(nappe_x_diam) * long_x * nappe_x_nb
        barres.append(CalculBarre(
            diametre_mm=nappe_x_diam,
            type_barre="HA",
            role="nappe_x",
            nombre=nappe_x_nb,
            longueur_unitaire_m=long_x,
            masse_lineique_kg_m=self.masse_lineique(nappe_x_diam),
            poids_total_kg=poids_x,
        ))

        # Nappe Y (longueur = b_m)
        long_y = self.longueur_nappe(b_m, nappe_y_diam)
        poids_y = self.masse_lineique(nappe_y_diam) * long_y * nappe_y_nb
        barres.append(CalculBarre(
            diametre_mm=nappe_y_diam,
            type_barre="HA",
            role="nappe_y",
            nombre=nappe_y_nb,
            longueur_unitaire_m=long_y,
            masse_lineique_kg_m=self.masse_lineique(nappe_y_diam),
            poids_total_kg=poids_y,
        ))

        poids_total = poids_x + poids_y

        return CalculElement(
            repere="",
            famille="SEMELLE",
            volume_m3=volume,
            surface_contact_m2=surface,
            barres=barres,
            poids_total_acier_kg=poids_total,
        )

    def calculer_poteau(
        self,
        b_m: float,
        h_m: float,
        hauteur_m: float,
        nb_longitudinaux: int,
        diam_longitudinal: int,
        diam_cadre: int,
        espacement_cadres: Optional[float] = None,
    ) -> CalculElement:
        """
        Calcul complet d'un poteau.

        Args:
            b_m: Largeur en m.
            h_m: Profondeur en m.
            hauteur_m: Hauteur du poteau en m.
            nb_longitudinaux: Nombre de barres longitudinales.
            diam_longitudinal: Diamètre longitudinal (mm).
            diam_cadre: Diamètre des cadres (mm).
            espacement_cadres: Espacement des cadres (m), défaut: self.espacement_cadres_m.

        Returns:
            CalculElement.
        """
        esp = espacement_cadres or self.espacement_cadres_m
        volume = b_m * h_m * hauteur_m
        surface = 2.0 * (b_m + h_m) * hauteur_m

        barres = []

        # Longitudinaux
        long_long = hauteur_m + 2.0 * self.coef_ancrage * diam_longitudinal / 1000.0
        poids_long = self.masse_lineique(diam_longitudinal) * long_long * nb_longitudinaux
        barres.append(CalculBarre(
            diametre_mm=diam_longitudinal,
            type_barre="HA",
            role="longitudinal",
            nombre=nb_longitudinaux,
            longueur_unitaire_m=long_long,
            masse_lineique_kg_m=self.masse_lineique(diam_longitudinal),
            poids_total_kg=poids_long,
        ))

        # Cadres
        nb_cadres = self.nb_cadres(hauteur_m, esp)
        long_cadre = self.longueur_developpee_cadre(b_m, h_m, diam_cadre)
        poids_cadres = self.masse_lineique(diam_cadre) * long_cadre * nb_cadres
        barres.append(CalculBarre(
            diametre_mm=diam_cadre,
            type_barre="HA",
            role="cadre",
            nombre=nb_cadres,
            longueur_unitaire_m=long_cadre,
            masse_lineique_kg_m=self.masse_lineique(diam_cadre),
            poids_total_kg=poids_cadres,
        ))

        poids_total = poids_long + poids_cadres

        return CalculElement(
            repere="",
            famille="POTEAU",
            volume_m3=volume,
            surface_contact_m2=surface,
            barres=barres,
            poids_total_acier_kg=poids_total,
        )

    def calculer_poutre(
        self,
        b_m: float,
        h_m: float,
        longueur_m: float,
        nb_longitudinaux: int,
        diam_longitudinal: int,
        diam_cadre: int,
        espacement_cadres: Optional[float] = None,
    ) -> CalculElement:
        """
        Calcul complet d'une poutre.

        Args:
            b_m: Largeur en m.
            h_m: Hauteur en m.
            longueur_m: Longueur de la poutre en m.
            nb_longitudinaux: Nombre de barres longitudinales (haut + bas).
            diam_longitudinal: Diamètre longitudinal (mm).
            diam_cadre: Diamètre des cadres (mm).
            espacement_cadres: Espacement des cadres (m).

        Returns:
            CalculElement.
        """
        esp = espacement_cadres or self.espacement_cadres_m
        volume = b_m * h_m * longueur_m
        surface = 2.0 * (b_m + h_m) * longueur_m

        barres = []

        # Longitudinaux (haut + bas)
        long_long = longueur_m + 2.0 * self.coef_ancrage * diam_longitudinal / 1000.0
        poids_long = self.masse_lineique(diam_longitudinal) * long_long * nb_longitudinaux
        barres.append(CalculBarre(
            diametre_mm=diam_longitudinal,
            type_barre="HA",
            role="longitudinal",
            nombre=nb_longitudinaux,
            longueur_unitaire_m=long_long,
            masse_lineique_kg_m=self.masse_lineique(diam_longitudinal),
            poids_total_kg=poids_long,
        ))

        # Cadres
        nb_cadres_val = self.nb_cadres(longueur_m, esp)
        long_cadre = self.longueur_developpee_cadre(b_m, h_m, diam_cadre)
        poids_cadres = self.masse_lineique(diam_cadre) * long_cadre * nb_cadres_val
        barres.append(CalculBarre(
            diametre_mm=diam_cadre,
            type_barre="HA",
            role="cadre",
            nombre=nb_cadres_val,
            longueur_unitaire_m=long_cadre,
            masse_lineique_kg_m=self.masse_lineique(diam_cadre),
            poids_total_kg=poids_cadres,
        ))

        poids_total = poids_long + poids_cadres

        return CalculElement(
            repere="",
            famille="POUTRE",
            volume_m3=volume,
            surface_contact_m2=surface,
            barres=barres,
            poids_total_acier_kg=poids_total,
        )

    # ------------------------------------------------------------------
    # Ventilation des poids
    # ------------------------------------------------------------------

    @staticmethod
    def ventiler_par_diamètre(
        elements: List[CalculElement],
    ) -> Dict[int, float]:
        """
        Ventilation du poids total d'acier par diamètre.

        Args:
            elements: Liste des éléments calculés.

        Returns:
            Dict {diamètre_mm: poids_kg}.
        """
        vent: Dict[int, float] = {}
        for elem in elements:
            for barre in elem.barres:
                d = barre.diametre_mm
                vent[d] = vent.get(d, 0.0) + barre.poids_total_kg
        return dict(sorted(vent.items()))

    @staticmethod
    def ventiler_par_famille(
        elements: List[CalculElement],
    ) -> Dict[str, float]:
        """
        Ventilation du poids total d'acier par famille d'élément.

        Args:
            elements: Liste des éléments calculés.

        Returns:
            Dict {famille: poids_kg}.
        """
        vent: Dict[str, float] = {}
        for elem in elements:
            fam = elem.famille
            vent[fam] = vent.get(fam, 0.0) + elem.poids_total_acier_kg
        return dict(sorted(vent.items()))

    # ------------------------------------------------------------------
    # Calcul projet complet
    # ------------------------------------------------------------------

    def calculer_projet(
        self, parse_output: ProjetBAParseOutput
    ) -> CalculProjet:
        """
        Calcule le bilan complet d'un projet à partir des données extraites.

        Note: Cette méthode est un pont entre les schémas et le moteur.
        Elle sera enrichie au fur et à mesure que les parsers seront ajoutés.
        """
        elements_calc: List[CalculElement] = []
        volume_total = 0.0
        poids_total = 0.0

        for elem in parse_output.elements:
            dims = elem.dimensions
            if elem.famille == FamilleElement.SEMELLE:
                calc = self.calculer_semelle(
                    a_m=dims.get("a", 0),
                    b_m=dims.get("b", 0),
                    h_m=dims.get("h", 0),
                    nappe_x_diam=12,  # Sera rempli par le parser
                    nappe_x_nb=8,
                    nappe_y_diam=12,
                    nappe_y_nb=8,
                )
            elif elem.famille == FamilleElement.POTEAU:
                calc = self.calculer_poteau(
                    b_m=dims.get("b", 0),
                    h_m=dims.get("h", 0),
                    hauteur_m=dims.get("hauteur", 3.0),
                    nb_longitudinaux=8,
                    diam_longitudinal=14,
                    diam_cadre=6,
                )
            elif elem.famille == FamilleElement.POUTRE:
                calc = self.calculer_poutre(
                    b_m=dims.get("b", 0),
                    h_m=dims.get("h", 0),
                    longueur_m=dims.get("longueur", 3.0),
                    nb_longitudinaux=4,
                    diam_longitudinal=14,
                    diam_cadre=8,
                )
            else:
                # Pour les autres familles, calcul basique
                calc = CalculElement(
                    repere=elem.repere,
                    famille=elem.famille.value,
                    volume_m3=0.0,
                    surface_contact_m2=0.0,
                )

            calc = CalculElement(
                repere=elem.repere,
                famille=calc.famille,
                volume_m3=calc.volume_m3,
                surface_contact_m2=calc.surface_contact_m2,
                barres=calc.barres,
                poids_total_acier_kg=calc.poids_total_acier_kg,
            )
            elements_calc.append(calc)
            volume_total += calc.volume_m3
            poids_total += calc.poids_total_acier_kg

        return CalculProjet(
            elements=elements_calc,
            volume_total_beton_m3=volume_total,
            poids_total_acier_kg=poids_total,
            ventilation_par_diamètre=self.ventiler_par_diamètre(elements_calc),
            ventilation_par_famille=self.ventiler_par_famille(elements_calc),
        )
