#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules/ferraillage.py — Calcul du ferraillage selon BAEL 91 / Eurocode 2.

Ce module intègre les formules des repos de référence :
- vlax-rsr/Armatures-Poteau-rectangulaire-BAEL (poteaux BAEL)
- Damon201202/calcul-section-acier-poutre-automatique-eurocode2 (poutres EC2)
- Damon201202/Eurocode2-Concrete-Cover-Calc (enrobage EC2)
- mondial974/pypyBABA (modules béton armé : poutres, dalles, bielletirant)

Usage :
    from modules.ferraillage import (
        semelle_ferraillage, poteau_ferraillage, longrine_ferraillage,
        poutre_ferraillage, enrobage_ec2, classe_structurale
    )

Chaque fonction retourne un dict avec les barres, cadres, épingles, poids.
Les formules sont documentées et traçables (pas de boîte noire).
"""
import math
from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# Constantes BAEL 91 / Eurocode 2
# ============================================================================

# Aciers courants au Maroc (HA = haute adhérence)
ACIERS = {
    "HA6":  {"diam": 6,  "section": 0.283, "poids_m": 0.222},  # cm², kg/m
    "HA8":  {"diam": 8,  "section": 0.503, "poids_m": 0.395},
    "HA10": {"diam": 10, "section": 0.785, "poids_m": 0.617},
    "HA12": {"diam": 12, "section": 1.131, "poids_m": 0.888},
    "HA14": {"diam": 14, "section": 1.539, "poids_m": 1.210},
    "HA16": {"diam": 16, "section": 2.011, "poids_m": 1.580},
    "HA20": {"diam": 20, "section": 3.142, "poids_m": 2.470},
    "HA25": {"diam": 25, "section": 4.909, "poids_m": 3.850},
    "HA32": {"diam": 32, "section": 8.042, "poids_m": 6.310},
}

# Poids linéaire : d²/162 (kg/m) — formule standard
def poids_lineaire(diam_mm):
    return diam_mm * diam_mm / 162.0


# ============================================================================
# Enrobage et classe structurale (Eurocode 2)
# ============================================================================

def classe_structurale(exposition="XC1", duree=50, qualite="S3"):
    """Classe structurale selon EC2 §4.4.1 (simplifié).
    Retourne la classe (1, 2, 3) utilisée pour le calcul d'enrobage."""
    base = {"XC1": 1, "XC2": 2, "XC3": 3, "XC4": 4, "XD1": 5, "XS1": 6}
    cls = base.get(exposition, 1)
    if duree > 50:
        cls += 1
    if qualite == "S3":
        cls += 1
    return min(cls, 3)


def enrobage_ec2(exposition="XC1", diam_barre=12, diam_granulat=20,
                 duree=50, qualite="S3"):
    """Enrobage nominal c_nom = c_min + Δc_dur + Δc_dev (EC2 §4.4.1).
    Retourne l'enrobage en mm."""
    cls = classe_structurale(exposition, duree, qualite)
    # c_min,dur selon classe d'exposition (table EC2 4.4.1)
    c_min_dur = {"XC1": 10, "XC2": 15, "XC3": 20, "XC4": 25,
                 "XD1": 30, "XS1": 35}.get(exposition, 10)
    c_min_b = max(diam_barre, diam_granulat, 10)  # EC2 §4.4.1.2(3)
    c_min = max(c_min_dur, c_min_b)
    delta_dur = 0  # déjà inclus dans c_min_dur pour les cas courants
    delta_dev = 10  # tolérance d'exécution (mm)
    return c_min + delta_dur + delta_dev


# ============================================================================
# Semelles isolées
# ============================================================================

@dataclass
class ResultatSemelle:
    """Résultat du ferraillage d'une semelle isolée."""
    repere: str = ""
    axe: str = ""
    fill: str = ""
    A: float = 0.0      # longueur (m)
    B: float = 0.0      # largeur (m)
    H: float = 0.0      # hauteur (m)
    bars_x: int = 0     # nombre de barres selon x
    bars_y: int = 0     # nombre de barres selon y
    diam: int = 12      # diamètre (mm)
    long_barre_x: float = 0.0  # longueur barre selon x (m)
    long_barre_y: float = 0.0  # longueur barre selon y (m)
    poids_total: float = 0.0   # poids total (kg)
    enrobage: float = 0.05     # enrobage (m)
    source: str = "tableau p.4"


def semelle_ferraillage(repere, axe, fill, A, B, H, bars_x, bars_y, diam=12,
                        enrobage_m=0.05):
    """Calcule le ferraillage d'une semelle isolée.
    Longueur barre = dim - 2×enrobage + 2×34d (ancrage BAEL/EC2).
    Formule : L = dim - 0.05 + 34 × d/1000 (d en mm)."""
    d = diam
    ancrage = 34 * d / 1000.0  # 34d en mètres
    lx = A - 2 * enrobage_m + 2 * ancrage
    ly = B - 2 * enrobage_m + 2 * ancrage
    poids = (bars_x * poids_lineaire(d) * lx +
             bars_y * poids_lineaire(d) * ly)
    return ResultatSemelle(
        repere=repere, axe=axe, fill=fill, A=A, B=B, H=H,
        bars_x=bars_x, bars_y=bars_y, diam=diam,
        long_barre_x=round(lx, 3), long_barre_y=round(ly, 3),
        poids_total=round(poids, 2), enrobage=enrobage_m
    )


# ============================================================================
# Poteaux (BAEL 91 — Armatures-Poteau-rectangulaire-BAEL)
# ============================================================================

@dataclass
class ResultatPoteau:
    """Résultat du ferraillage d'un poteau rectangulaire."""
    axe: str = ""
    fill: str = ""
    type_poteau: str = ""  # P1, P2, P3, P4
    b: float = 0.0         # largeur (m)
    h: float = 0.0         # hauteur (m)
    longueur: float = 0.0  # longueur du fût (m)
    bars_long: int = 0     # barres longitudinales
    diam_long: int = 14    # diamètre barres long (mm)
    cadres: int = 0        # nombre de cadres
    diam_cadre: int = 6    # diamètre cadre (mm)
    espacement: float = 0.15  # espacement cadres (m)
    epingles: int = 0
    poids_long: float = 0.0
    poids_cadre: float = 0.0
    poids_epingle: float = 0.0
    poids_total: float = 0.0


def poteau_ferraillage(axe, fill, type_p, b, h, longueur, bars_long, diam_long=14,
                       diam_cadre=6, espacement=0.15, T76=1.8):
    """Ferraillage d'un poteau rectangulaire (BAEL 91).
    Barres longues : L = T76 + 18d (développement).
    Cadres : périmètre intérieur + 20.5d, nombre = ROUNDUP(L/espacement).
    Épingles : largeur - 0.05 + 22d, même nombre que cadres."""
    d_long = diam_long
    d_cad = diam_cadre
    # barres longues
    ll = T76 + 18 * d_long / 1000.0
    poids_long = bars_long * poids_lineaire(d_long) * ll
    # cadres : périmètre intérieur = 2*(b+h) - 8*enrobage + 20.5d
    perim = 2 * (b + h) - 0.05 + 20.5 * d_cad / 1000.0
    n_cad = math.ceil((longueur - 0.25) / espacement) + 2
    poids_cadre = n_cad * poids_lineaire(d_cad) * perim
    # épingles
    lep = b - 0.05 + 22 * d_cad / 1000.0
    poids_ep = n_cad * poids_lineaire(d_cad) * lep
    return ResultatPoteau(
        axe=axe, fill=fill, type_poteau=type_p, b=b, h=h, longueur=longueur,
        bars_long=bars_long, diam_long=diam_long,
        cadres=n_cad, diam_cadre=diam_cad, espacement=espacement,
        epingles=n_cad,
        poids_long=round(poids_long, 2),
        poids_cadre=round(poids_cadre, 2),
        poids_epingle=round(poids_ep, 2),
        poids_total=round(poids_long + poids_cadre + poids_ep, 2)
    )


# ============================================================================
# Longrines / Chaînages
# ============================================================================

@dataclass
class ResultatLongrine:
    axe: str = ""
    fill: str = ""
    nom: str = ""          # LG, LG2, CH
    longueur: float = 0.0
    b: float = 0.0
    h: float = 0.0
    nappe_sup: int = 0     # barres nappe supérieure
    nappe_inf: int = 0     # barres nappe inférieure
    diam_sup: int = 12
    diam_inf: int = 10
    cadres: int = 0
    epingles: int = 0
    poids_total: float = 0.0


def longrine_ferraillage(axe, fill, nom, longueur, b, h,
                         nappe_sup=3, nappe_inf=3, diam_sup=12, diam_inf=10,
                         diam_cadre=6, espacement=0.20):
    """Ferraillage longrine/chaînage.
    Nappes : L + ROUNDUP(L/12) (recouvrement).
    Cadres : périmètre intérieur + 20.5d.
    Épingles : h - 0.05 + 22d."""
    ls = longueur + math.ceil(longueur / 12)
    li = longueur + math.ceil(longueur / 12)
    poids = (nappe_sup * poids_lineaire(diam_sup) * ls +
             nappe_inf * poids_lineaire(diam_inf) * li)
    perim = 2 * (b + h) - 0.05 + 20.5 * diam_cadre / 1000.0
    n_cad = math.ceil(longueur / espacement)
    poids += n_cad * poids_lineaire(diam_cadre) * perim
    lep = h - 0.05 + 22 * diam_cadre / 1000.0
    poids += n_cad * poids_lineaire(diam_cadre) * lep
    return ResultatLongrine(
        axe=axe, fill=fill, nom=nom, longueur=longueur, b=b, h=h,
        nappe_sup=nappe_sup, nappe_inf=nappe_inf,
        diam_sup=diam_sup, diam_inf=diam_inf,
        cadres=n_cad, epingles=n_cad,
        poids_total=round(poids, 2)
    )


# ============================================================================
# Poutres (N1-N7, CH1, BN1, BN2)
# ============================================================================

@dataclass
class ResultatPoutre:
    nom: str = ""
    axe: str = ""
    fill: str = ""
    longueur: float = 0.0
    b: float = 0.0
    h: float = 0.0
    bars_sup: int = 0
    bars_inf: int = 0
    diam: int = 12
    cadres: int = 0
    poids_total: float = 0.0


def poutre_ferraillage(nom, axe, fill, longueur, b, h,
                       bars_sup=2, bars_inf=2, diam=12, diam_cadre=6,
                       espacement=0.10):
    """Ferraillage simplifié d'une poutre (pour métré, pas note de calcul).
    Longueurs : L + recouvrement. Cadres : périmètre + 20.5d."""
    l_barre = longueur + math.ceil(longueur / 12)
    poids = (bars_sup + bars_inf) * poids_lineaire(diam) * l_barre
    perim = 2 * (b + h) - 0.05 + 20.5 * diam_cadre / 1000.0
    n_cad = math.ceil(longueur / espacement)
    poids += n_cad * poids_lineaire(diam_cadre) * perim
    return ResultatPoutre(
        nom=nom, axe=axe, fill=fill, longueur=longueur, b=b, h=h,
        bars_sup=bars_sup, bars_inf=bars_inf, diam=diam,
        cadres=n_cad, poids_total=round(poids, 2)
    )


# ============================================================================
# Tableau des semelles (lecture directe du plan)
# ============================================================================

TABLEAU_SEMELLES = {
    "S1": {"A": 1.00, "B": 1.00, "H": 0.25, "fx": 6, "fy": 6, "diam": 12},
    "S2": {"A": 1.10, "B": 1.10, "H": 0.25, "fx": 7, "fy": 7, "diam": 12},
    "S3": {"A": 1.20, "B": 1.20, "H": 0.30, "fx": 8, "fy": 8, "diam": 12},
    "S4": {"A": 1.50, "B": 1.50, "H": 0.40, "fx": 11, "fy": 11, "diam": 12},
    "S5": {"A": 1.50, "B": 1.50, "H": 0.40, "fx": 11, "fy": 11, "diam": 12,
           "note": "absente du tableau p.4 — cotes lues sur le plan"},
}

TABLEAU_POTEAUX = {
    "P1": {"b": 0.25, "h": 0.35},
    "P2": {"b": 0.40, "h": 0.40},
    "P3": {"b": 0.30, "h": 0.30},
    "P4": {"b": 0.35, "h": 0.35},
}

TABLEAU_POUTRES = {
    "CH1": {"b": 0.20, "h": 0.20},
    "N1":  {"b": 0.20, "h": 0.30},
    "N2":  {"b": 0.20, "h": 0.35},
    "N3":  {"b": 0.20, "h": 0.40},
    "N4":  {"b": 0.20, "h": 0.45},
    "N5":  {"b": 0.20, "h": 0.50},
    "N6":  {"b": 0.40, "h": 0.90},
    "N7":  {"b": 0.30, "h": 0.90, "note": "en T : 0.30×0.90 + 0.30×0.80"},
    "N7p": {"b": 0.30, "h": 0.80},
    "BN1": {"b": 0.30, "h": 0.30},
    "BN2": {"b": 0.20, "h": 0.20},
}
