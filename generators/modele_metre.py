#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generators/modele_metre.py -- Générateur du classeur modèle standardisé
Métré & Attachement Gros Œuvre (référence BET / bureaux de contrôle).

100% vierge : AUCUNE donnée de projet en dur (pas d'overfit). Les seules
valeurs numériques sont des constantes normatives (poids ml nominaux,
coefficients forfaitaires) et des formules Excel.

4 feuilles interconnectées :
  1. 01_Detail_Quantitatif   — métré fondations & élévation (3 blocs vierges)
  2. 02_Armatures            — décorticage ferraillage + totaux acier
  3. 03_Attachement_Ferraillage — synthèse par type d'ouvrage + taux kg/m³
  4. 04_GO_Attachement       — bordereau lié dynamiquement (1, 2)

Charte "Génie Civil Prestige" :
  - En-têtes/titres : Bleu Nuit #1B365D, blanc, centré
  - Sections/sous-totaux : Bleu Acier #2E5B88, blanc
  - Saisie géométrique : blanc #FFFFFF, bordures #D1D5DB
  - Calcul auto : Bleu Givré #F0F4F8
  - Totaux généraux : Émeraude #0D9488, souligné double
  - Police Segoe UI (10 données / 11 en-têtes / 13 titres)
  - Aucune fusion hors cartouche (lignes 1-5)

Usage :
  python generators/modele_metre.py [--out output/modele_metre_BA.xlsx]

Macros VBA : voir vba/Module1.bas (Développeur > Visual Basic >
Fichier > Importer, puis Enregistrer sous .xlsm).
"""
import argparse
import os
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ============================================================================
# Charte graphique "Génie Civil Prestige"
# ============================================================================

NAVY = "1B365D"        # en-têtes / titres
STEEL = "2E5B88"       # sections / sous-totaux
WHITE = "FFFFFF"       # saisie
FROST = "F0F4F8"       # calcul automatique
EMERALD = "0D9488"     # totaux généraux
GRAY_BORDER = "D1D5DB"
AMBER = "D97706"       # alertes (VBA)

FONT_TITLE = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
FONT_HEAD = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
FONT_SECTION = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
FONT_DATA = Font(name="Segoe UI", size=10)
FONT_TOTAL = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
FONT_FORMULE = Font(name="Segoe UI", size=10, italic=True, color="0000AA")
FONT_LABEL = Font(name="Segoe UI", size=10, italic=True, color="555555")

FILL_NAVY = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
FILL_STEEL = PatternFill(start_color=STEEL, end_color=STEEL, fill_type="solid")
FILL_WHITE = PatternFill(start_color=WHITE, end_color=WHITE, fill_type="solid")
FILL_FROST = PatternFill(start_color=FROST, end_color=FROST, fill_type="solid")
FILL_EMERALD = PatternFill(
    start_color=EMERALD, end_color=EMERALD, fill_type="solid")

THIN = Side(style="thin", color=GRAY_BORDER)
DOUBLE_BOTTOM = Side(style="double", color=NAVY)
BORDER_CELL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BORDER_TOTAL = Border(left=THIN, right=THIN, top=THIN, bottom=DOUBLE_BOTTOM)

ALIGN_CENTER = Alignment(horizontal="center", vertical="center",
                         wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

FMT_M = "#,##0.00"     # longueurs / volumes / surfaces
FMT_INT = "0"          # entiers et diamètres
FMT_KG = "#,##0"       # poids en kg
FMT_KGML = "#,##0.000"  # poids unitaires nominaux
FMT_PCT = "0.0%"       # pourcentages

DIAMETRES = [6, 8, 10, 12, 14, 16, 20, 25, 32]
# Poids nominaux kg/ml (référence BET — constantes normatives, pas projet)
POIDS_ML = [0.222, 0.395, 0.617, 0.888, 1.208, 1.578, 2.466, 3.853, 6.313]

ENROBAGE = 0.05
COEF_ANCRAGE = 34


# ============================================================================
# Utilitaires
# ============================================================================

def _style_range(ws, row, ncols, font=FONT_DATA, fill=None,
                 border=BORDER_CELL):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = font
        cell.border = border
        if fill:
            cell.fill = fill


def _titre(ws, row, ncols, text):
    """Cartouche titre (lignes 1-5 : fusions autorisees)."""
    ws.merge_cells(start_row=row, start_column=1,
                   end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = FONT_TITLE
    cell.fill = FILL_NAVY
    cell.alignment = ALIGN_CENTER


def _cartouche_ligne(ws, row, champs):
    """Une ligne de cartouche : [(label, col_label, col_val_debut,
    col_val_fin), ...]. Fusions autorisees (lignes 1-5)."""
    for label, col_l, col_v0, col_v1 in champs:
        lab = ws.cell(row=row, column=col_l, value=label)
        lab.font = FONT_LABEL
        lab.alignment = ALIGN_RIGHT
        ws.merge_cells(start_row=row, start_column=col_v0,
                       end_row=row, end_column=col_v1)
        val = ws.cell(row=row, column=col_v0)
        val.fill = FILL_WHITE
        val.border = BORDER_CELL


def _entetes(ws, row, headers, ncols):
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_NAVY
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_CELL


def _largeurs(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ============================================================================
# FEUILLE 1 : 01_Detail_Quantitatif
# ============================================================================

# Blocs d'articles types : (numero, libelle)
BLOCS_S1 = [
    (1, "Terrassement en fouilles / Fouilles en pleine masse"),
    (2, "Béton de propreté dosé à 150 kg/m³"),
    (3, "Béton armé en fondation et en élévation dosé à 350 kg/m³"),
]
LIGNES_PAR_BLOC = 8  # lignes de saisie vierges par bloc


def feuille_detail(wb):
    ws = wb.active
    ws.title = "01_Detail_Quantitatif"
    NCOLS = 11  # A-K

    _titre(ws, 1, NCOLS, "DÉTAIL QUANTITATIF ESTIMATIF — GROS ŒUVRES")
    _cartouche_ligne(ws, 2, [
        ("N° Marché :", 1, 2, 3),
        ("Projet :", 4, 5, 7),
        ("Bâtiment :", 8, 9, 11),
    ])
    _cartouche_ligne(ws, 3, [
        ("Date :", 1, 2, 3),
        ("Établi par :", 4, 5, 7),
        ("Vérifié par :", 8, 9, 11),
    ])
    _titre(ws, 5, NCOLS, "DÉTAIL QUANTITATIF — FONDATIONS & ÉLÉVATION")

    headers = ["N°", "Axe", "File", "Désignation des Ouvrages", "U", "N",
               "Longueur (m)", "Largeur (m)", "Hauteur (m)",
               "Qté Partielle", "Qté Totale"]
    _entetes(ws, 6, headers, NCOLS)

    row = 7
    subtotaux = []  # (ligne, debut, fin, col) pour liens feuille 4
    for num, libelle in BLOCS_S1:
        # Ligne section (pas de fusion) + libelle
        ws.cell(row=row, column=1, value=num).font = FONT_SECTION
        ws.cell(row=row, column=4, value=libelle).font = FONT_SECTION
        _style_range(ws, row, NCOLS, font=FONT_SECTION, fill=FILL_STEEL)
        row += 1

        # Sous-labels axe/file
        ws.cell(row=row, column=2, value="Axe").font = FONT_LABEL
        ws.cell(row=row, column=3, value="File").font = FONT_LABEL
        _style_range(ws, row, NCOLS)
        row += 1

        debut = row
        # Lignes de saisie vierges
        for _ in range(LIGNES_PAR_BLOC):
            for c in range(1, NCOLS + 1):
                cell = ws.cell(row=row, column=c)
                cell.font = FONT_DATA
                cell.border = BORDER_CELL
                if c in (1, 2, 3, 5):
                    cell.alignment = ALIGN_CENTER
                    cell.fill = FILL_WHITE
                elif c == 4:
                    cell.alignment = ALIGN_LEFT
                    cell.fill = FILL_WHITE
                else:
                    cell.alignment = ALIGN_RIGHT
                    cell.fill = FILL_FROST
                    if c in (6,):
                        cell.number_format = FMT_INT
                    else:
                        cell.number_format = FMT_M
            # Qté Partielle : =IF(COUNTA(G:I)>0, F*PRODUCT(G:I), F)
            cell_j = ws.cell(
                row=row, column=10,
                value=f"=IF(COUNTA(G{row}:I{row})>0,"
                      f"F{row}*PRODUCT(G{row}:I{row}),F{row})")
            cell_j.font = FONT_FORMULE
            row += 1
        fin = row - 1

        # Sous-total du bloc : J = SUM(partiels), K = SUM(partiels J)
        ws.cell(row=row, column=1, value="Ss-total").font = FONT_TOTAL
        ws.cell(row=row, column=10,
                value=f"=SUM(J{debut}:J{fin})").font = FONT_FORMULE
        ws.cell(row=row, column=11,
                value=f"=SUM(J{debut}:J{fin})").font = FONT_FORMULE
        _style_range(ws, row, NCOLS, font=FONT_TOTAL, fill=FILL_STEEL)
        subtotaux.append((row, debut, fin))
        row += 2  # ligne blanche de séparation

    row -= 1
    # TOTAL GÉNÉRAL (émeraude, souligné double)
    ws.cell(row=row, column=1, value="TOTAL GÉNÉRAL").font = FONT_TOTAL
    plages_j = "+".join(f"J{r}" for r, _, _ in subtotaux)
    plages_k = "+".join(f"K{r}" for r, _, _ in subtotaux)
    ws.cell(row=row, column=10, value=f"={plages_j}").font = FONT_FORMULE
    ws.cell(row=row, column=11, value=f"={plages_k}").font = FONT_FORMULE
    for c in range(1, NCOLS + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = FILL_EMERALD
        cell.border = BORDER_TOTAL
        if c == 1:
            cell.font = Font(name="Segoe UI", size=10, bold=True,
                             color="FFFFFF")
    _largeurs(ws, [6, 7, 7, 42, 6, 6, 12, 12, 14, 14, 14])
    return ws, subtotaux


# ============================================================================
# FEUILLE 2 : 02_Armatures
# ============================================================================

def feuille_armatures(wb, nb_lignes=16):
    ws = wb.create_sheet("02_Armatures")
    headers_main = ["Repère / Ouvrage", "Axe", "File", "a (m)", "b (m)",
                    "h (m)", "N° ELE", "NOMB B", "DIAM", "LONG (m)"]
    NM = len(headers_main)          # 10
    ND = len(DIAMETRES)             # 9
    NCOLS = NM + ND                 # 19 (A-S)

    _titre(ws, 1, NCOLS,
           "NOMENCLATURE ET DÉCORTICAGE DÉTAILLÉ DES ARMATURES")
    _cartouche_ligne(ws, 2, [
        ("Projet :", 1, 2, 6),
        ("Date :", 11, 12, 14),
        ("Indice :", 15, 16, 19),
    ])

    for c, h in enumerate(headers_main, 1):
        cell = ws.cell(row=3, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_NAVY
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_CELL
    for i, d in enumerate(DIAMETRES):
        cell = ws.cell(row=3, column=NM + 1 + i, value=f"T{d}")
        cell.font = FONT_HEAD
        cell.fill = FILL_NAVY
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_CELL

    debut = 4
    for r in range(debut, debut + nb_lignes):
        for c in range(1, NCOLS + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = FONT_DATA
            cell.border = BORDER_CELL
            if c == 1:
                cell.alignment = ALIGN_LEFT
                cell.fill = FILL_WHITE
            elif c in (2, 3, 7, 8, 9):
                cell.alignment = ALIGN_CENTER
                cell.fill = FILL_WHITE
                cell.number_format = FMT_INT if c in (7, 8, 9) else "@"
            elif c <= NM:
                cell.alignment = ALIGN_RIGHT
                cell.fill = FILL_FROST
                cell.number_format = FMT_M
            else:
                cell.alignment = ALIGN_RIGHT
                cell.fill = FILL_FROST
                cell.number_format = FMT_M
        # Ventilation : =IF($I=diametre, $G*$H*$J, "")
        for i, d in enumerate(DIAMETRES):
            ws.cell(row=r, column=NM + 1 + i,
                    value=f'=IF($I{r}={d},$G{r}*$H{r}*$J{r},"")'
                    ).font = FONT_FORMULE
    fin = debut + nb_lignes - 1

    # --- Récapitulatif ---
    def _recap(row, label, kind):
        ws.cell(row=row, column=1, value=label).font = FONT_TOTAL
        ws.cell(row=row, column=1).alignment = ALIGN_RIGHT
        for i, d in enumerate(DIAMETRES):
            col = NM + 1 + i
            letter = get_column_letter(col)
            if kind == "sum":
                ws.cell(row=row, column=col,
                        value=f"=SUM({letter}{debut}:{letter}{fin})")
            elif kind == "pml":
                ws.cell(row=row, column=col,
                        value=POIDS_ML[i]).number_format = FMT_KGML
            elif kind == "part":
                ws.cell(row=row, column=col,
                        value=f"={letter}{row_long_tot}*{letter}{row_pml}")
            for c in range(1, col + 1):
                cell = ws.cell(row=row, column=c)
                cell.font = FONT_FORMULE if c > 1 else FONT_TOTAL
                cell.border = BORDER_CELL
                if c == 1:
                    continue
                cell.fill = FILL_EMERALD if kind == "total" else FILL_FROST
                cell.number_format = (
                    FMT_KG if kind in ("part", "total") else FMT_M)

    row_long_tot = fin + 2
    _recap(row_long_tot, "LONGUEUR TOTALE (ml)", "sum")
    row_pml = row_long_tot + 1
    _recap(row_pml, "POIDS UNITAIRE NOMINAL (kg/ml)", "pml")
    row_part = row_pml + 1
    _recap(row_part, "POIDS PARTIEL PAR DIAMÈTRE (kg)", "part")

    ws.cell(row=row_part + 1, column=1,
            value="POIDS TOTAL DES ACIERS (KG)").font = FONT_TOTAL
    ws.cell(row=row_part + 1, column=1).alignment = ALIGN_RIGHT
    first = get_column_letter(NM + 1)
    last = get_column_letter(NM + ND)
    ws.cell(row=row_part + 1, column=NM + 1,
            value=f"=SUM({first}{row_part}:{last}{row_part})")
    ws.cell(row=row_part + 1, column=NM + 1).font = FONT_FORMULE
    for c in range(1, NM + 2):
        cell = ws.cell(row=row_part + 1, column=c)
        cell.fill = FILL_EMERALD
        cell.border = BORDER_TOTAL
    row_total = row_part + 1

    ws.cell(row=row_total + 1, column=1,
            value="POIDS TOTAL (tonnes)").font = FONT_TOTAL
    ws.cell(row=row_total + 1, column=1).alignment = ALIGN_RIGHT
    ws.cell(row=row_total + 1, column=NM + 1,
            value=f"={get_column_letter(NM + 1)}{row_total}/1000")
    ws.cell(row=row_total + 1, column=NM + 1).font = FONT_FORMULE
    for c in range(1, NM + 2):
        ws.cell(row=row_total + 1, column=c).border = BORDER_CELL

    ws.cell(row=row_total + 2, column=1,
            value="Volume béton de référence (m³) — à saisir").font = FONT_LABEL
    ws.cell(row=row_total + 2, column=1).alignment = ALIGN_RIGHT
    ws.cell(row=row_total + 2, column=NM + 1).number_format = FMT_M
    ws.cell(row=row_total + 2, column=NM + 1).fill = FILL_WHITE
    ws.cell(row=row_total + 2, column=NM + 1).border = BORDER_CELL
    row_beton = row_total + 2

    ws.cell(row=row_total + 3, column=1,
            value="TAUX DE FERRAILLAGE MOYEN (kg/m³)").font = FONT_TOTAL
    ws.cell(row=row_total + 3, column=1).alignment = ALIGN_RIGHT
    ws.cell(row=row_total + 3, column=NM + 1,
            value=f"=IF({get_column_letter(NM + 1)}{row_beton}>0,"
                  f"{get_column_letter(NM + 1)}{row_total}/"
                  f"{get_column_letter(NM + 1)}{row_beton},\"\")")
    ws.cell(row=row_total + 3, column=NM + 1).font = FONT_FORMULE

    _largeurs(ws, [26, 6, 6, 8, 8, 8, 8, 8, 8, 11] + [9] * ND)
    return ws, {"long_tot": row_long_tot, "total_kg": row_total,
                "tonnes": row_total + 1}


# ============================================================================
# FEUILLE 3 : 03_Attachement_Ferraillage
# ============================================================================

def feuille_synthese(wb, nb_lignes=12):
    ws = wb.create_sheet("03_Attachement_Ferraillage")
    headers_main = ["Type d'Ouvrage", "Type d'Armature", "N° Ouvrages cumulés",
                    "Nb barres", "Diamètre (mm)", "Longueur unitaire (m)"]
    NM = len(headers_main)          # 6
    ND = len(DIAMETRES)             # 9
    NCOLS = NM + ND                 # 15 (A-O)

    _titre(ws, 1, NCOLS,
           "ATTACHEMENT — SYNTHÈSE DES ARMATURES PAR TYPE D'OUVRAGE")
    _cartouche_ligne(ws, 2, [
        ("Projet :", 1, 2, 5),
        ("Attachement n° :", 6, 7, 9),
        ("Date :", 10, 11, 15),
    ])

    for c, h in enumerate(headers_main, 1):
        cell = ws.cell(row=3, column=c, value=h)
        cell.font = FONT_HEAD
        cell.fill = FILL_NAVY
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_CELL
    for i, d in enumerate(DIAMETRES):
        cell = ws.cell(row=3, column=NM + 1 + i, value=f"T{d}")
        cell.font = FONT_HEAD
        cell.fill = FILL_NAVY
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_CELL

    debut = 4
    for r in range(debut, debut + nb_lignes):
        for c in range(1, NCOLS + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = FONT_DATA
            cell.border = BORDER_CELL
            if c in (1, 2):
                cell.alignment = ALIGN_LEFT
                cell.fill = FILL_WHITE
            elif c in (3, 4, 5):
                cell.alignment = ALIGN_CENTER
                cell.fill = FILL_WHITE
                cell.number_format = FMT_INT
            else:
                cell.alignment = ALIGN_RIGHT
                cell.fill = FILL_FROST
                cell.number_format = FMT_M
        # Rapprochement : =IF($E=diametre, $C*$D*$F, "")
        for i, d in enumerate(DIAMETRES):
            ws.cell(row=r, column=NM + 1 + i,
                    value=f'=IF($E{r}={d},$C{r}*$D{r}*$F{r},"")'
                    ).font = FONT_FORMULE
    fin = debut + nb_lignes - 1

    ws.cell(row=fin + 2, column=1,
            value="LONGUEUR TOTALE (ml)").font = FONT_TOTAL
    ws.cell(row=fin + 2, column=1).alignment = ALIGN_RIGHT
    for i in range(ND):
        col = NM + 1 + i
        letter = get_column_letter(col)
        ws.cell(row=fin + 2, column=col,
                value=f"=SUM({letter}{debut}:{letter}{fin})")
        ws.cell(row=fin + 2, column=col).font = FONT_FORMULE
        ws.cell(row=fin + 2, column=col).border = BORDER_CELL
    row_tot = fin + 2

    ws.cell(row=row_tot + 1, column=1,
            value="POIDS TOTAL SYNTHÈSE (kg)").font = FONT_TOTAL
    ws.cell(row=row_tot + 1, column=1).alignment = ALIGN_RIGHT
    parts = "+".join(
        f"{get_column_letter(NM + 1 + i)}{row_tot}*{POIDS_ML[i]}"
        for i in range(ND))
    ws.cell(row=row_tot + 1, column=NM + 1, value=f"={parts}")
    ws.cell(row=row_tot + 1, column=NM + 1).font = FONT_FORMULE
    for c in range(1, NM + 2):
        ws.cell(row=row_tot + 1, column=c).fill = FILL_EMERALD
        ws.cell(row=row_tot + 1, column=c).border = BORDER_TOTAL
    _largeurs(ws, [22, 24, 12, 10, 10, 14] + [9] * ND)
    return ws, row_tot + 1


# ============================================================================
# FEUILLE 4 : 04_GO_Attachement
# ============================================================================

# Lignes types du bordereau : (n° prix, designation, unite, feuille, cellule)
PRIX_TYPES = [
    ("1", "Terrassement en fouilles", "M3", "s1", 0),
    ("2", "Béton de propreté dosé à 150 kg/m³", "M3", "s1", 1),
    ("3", "Béton armé en fondation et élévation dosé à 350 kg/m³", "M3",
     "s1", 2),
    ("4", "Aciers Haute Adhérence FeE500", "KG", "s2", None),
]


def feuille_bordereau(wb, subtotaux_s1, recap_s2):
    ws = wb.create_sheet("04_GO_Attachement")

    _titre(ws, 1, 7, "ATTACHEMENT — GROS ŒUVRES & DÉCOMPTE DES QUANTITÉS")
    _cartouche_ligne(ws, 2, [
        ("N° Marché :", 1, 2, 2),
        ("Situation n° :", 3, 4, 4),
        ("Période :", 5, 6, 7),
    ])

    headers = ["N° Prix", "Désignation des Travaux", "Unité", "Qté Marché",
               "Qté Réalisée", "Reste", "% Avancement"]
    _entetes(ws, 3, headers, 7)

    row = 4
    for num, des, unite, feuille, idx in PRIX_TYPES:
        ws.cell(row=row, column=1, value=num).alignment = ALIGN_CENTER
        ws.cell(row=row, column=2, value=des).alignment = ALIGN_LEFT
        ws.cell(row=row, column=3, value=unite).alignment = ALIGN_CENTER
        # Qté Marché : VIERGE (aucune donnée projet en dur)
        ws.cell(row=row, column=4).number_format = FMT_M
        ws.cell(row=row, column=4).fill = FILL_WHITE
        # Qté Réalisée : lien dynamique vers totaux feuilles 1 et 2
        if feuille == "s1":
            sub_row = subtotaux_s1[idx][0]
            ws.cell(row=row, column=5,
                    value=f"='01_Detail_Quantitatif'!K{sub_row}")
        else:
            col_k = get_column_letter(10 + 1)
            ws.cell(row=row, column=5,
                    value=f"='02_Armatures'!{col_k}{recap_s2['total_kg']}")
        ws.cell(row=row, column=5).number_format = (
            FMT_KG if unite == "KG" else FMT_M)
        ws.cell(row=row, column=5).fill = FILL_FROST
        ws.cell(row=row, column=6, value=f"=D{row}-E{row}")
        ws.cell(row=row, column=6).number_format = FMT_M
        ws.cell(row=row, column=7, value=f"=IF(D{row}>0,E{row}/D{row},0)")
        ws.cell(row=row, column=7).number_format = FMT_PCT
        for c in range(1, 8):
            cell = ws.cell(row=row, column=c)
            cell.font = FONT_DATA
            cell.border = BORDER_CELL
        row += 1

    _largeurs(ws, [10, 46, 8, 14, 14, 14, 12])
    return ws


# ============================================================================
# Point d'entree
# ============================================================================

def generer_modele(output_path):
    wb = openpyxl.Workbook()
    _, subtotaux = feuille_detail(wb)
    _, recap = feuille_armatures(wb)
    feuille_synthese(wb)
    feuille_bordereau(wb, subtotaux, recap)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wb.save(output_path)
    print(f"Modele standardise genere : {output_path}")
    return output_path


def main():
    ap = argparse.ArgumentParser(
        description="Generateur du classeur modele Metre BA standardise")
    ap.add_argument("--out", "-o", default="output/modele_metre_BA.xlsx",
                    help="Chemin de sortie (.xlsx)")
    args = ap.parse_args()
    generer_modele(args.out)


if __name__ == "__main__":
    main()
