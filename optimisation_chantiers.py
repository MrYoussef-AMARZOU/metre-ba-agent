#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
optimisation_chantiers.py -- Calpinage de decoupe des barres marchandes (12m).
Optimise la coupe des barres d'acier pour minimiser les chutes (< 5%).
"""
import json
import math
import os
import sys
from pathlib import Path

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

THIN = Side(style="thin")
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_DATA = Font(name="Calibri", size=10)
FONT_TOTAL = Font(name="Calibri", size=10, bold=True)
FONT_FORMULE = Font(name="Calibri", size=10, italic=True, color="0000AA")
FILL_HEADER = PatternFill("solid", fgColor="2F5496")
FILL_TOTAL = PatternFill("solid", fgColor="BDD7EE")
FILL_OK = PatternFill("solid", fgColor="C6EFCE")
FILL_WARN = PatternFill("solid", fgColor="FFC7CE")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

LONGUEUR_BARRE_MARCHANDE = 12.0


def _cuts_for_bar(needed_lengths, bar_length=LONGUEUR_BARRE_MARCHANDE):
    """
    Greedy bin-packing: coupe les barres necessaires depuis des barres
    marchandes de 12m. Retourne [(longueurs_coupes, chute), ...].
    """
    remaining = sorted(needed_lengths, reverse=True)
    cuts = []
    while remaining:
        current_bar = bar_length
        pieces = []
        i = 0
        while i < len(remaining):
            if remaining[i] <= current_bar + 0.001:
                pieces.append(remaining[i])
                current_bar -= remaining[i]
                remaining.pop(i)
            else:
                i += 1
        chute = current_bar
        cuts.append((pieces, chute))
    return cuts


def _collect_bar_data(plan_data):
    """Collecte toutes les longueurs de barres necessaires par diametre.
    Retourne (bars_by_diam, warnings) — aucune valeur n'est inventee."""
    catalogue = plan_data.get("catalogue_types", {})
    implantations = plan_data.get("implantations", {})

    bars_by_diam = {}
    warnings = []

    # Semelles
    sem_impl = implantations.get("semelles", [])
    for inst in sem_impl:
        tk = inst.get("type", "")
        dims = catalogue.get("semelles", {}).get(tk, {})
        a = dims.get("a", 0)
        b = dims.get("b", 0)
        ferr_x = dims.get("ferr_x", {})
        ferr_y = dims.get("ferr_y", {})

        if ferr_x.get("nb", 0) > 0:
            phi = ferr_x["phi"]
            long = a + 0.20
            nb = ferr_x["nb"]
            bars_by_diam.setdefault(phi, []).extend([long] * nb)

        if ferr_y.get("nb", 0) > 0:
            phi = ferr_y["phi"]
            long = b + 0.20
            nb = ferr_y["nb"]
            bars_by_diam.setdefault(phi, []).extend([long] * nb)

    # Poteaux
    pot_impl = implantations.get("poteaux", [])
    for inst in pot_impl:
        tk = inst.get("type", "")
        dims = catalogue.get("poteaux", {}).get(tk, {})
        hauteur = inst.get("hauteur", 3.0)
        for lb in dims.get("long_bars", []):
            phi = lb["phi"]
            nb = lb["nb"]
            if phi <= 0 or nb <= 0:
                continue
            long = hauteur + 0.50
            bars_by_diam.setdefault(phi, []).extend([long] * nb)

        cadres = dims.get("cadres", {})
        phi_c = cadres.get("phi", 6)
        esp = cadres.get("esp", 0.15)
        a = dims.get("a", 0.25)
        b = dims.get("b", 0.35)
        if esp > 0:
            nb_cadres = math.ceil(hauteur / esp) + 2
            perimetre = 2 * (a + b) + 0.10
            bars_by_diam.setdefault(phi_c, []).extend([perimetre] * nb_cadres)

    # Poutres
    pou_impl = implantations.get("poutres", [])
    for inst in pou_impl:
        tk = inst.get("type", "")
        dims = catalogue.get("poutres", {}).get(tk, {})
        portee = inst.get("portee")
        if portee is None:
            # Portee non cotee sur le plan : pas d'invention de valeur
            warnings.append(
                f"{tk} : portée non renseignée — poutre exclue du calpinage.")
            continue
        for fi in dims.get("filants_inf", []) + dims.get("filants_sup", []):
            phi = fi["phi"]
            nb = fi["nb"]
            if phi <= 0 or nb <= 0:
                continue
            long = portee + 0.50
            bars_by_diam.setdefault(phi, []).extend([long] * nb)

        cadres = dims.get("cadres", {})
        phi_c = cadres.get("phi", 6)
        esp = cadres.get("esp", 0.18)
        b_sect = dims.get("b", 0.20)
        h_sect = dims.get("h", 0.30)
        if esp > 0:
            nb_cadres = math.ceil(portee / esp) + 2
            perimetre = 2 * (b_sect + h_sect) + 0.10
            bars_by_diam.setdefault(phi_c, []).extend([perimetre] * nb_cadres)

    return bars_by_diam, warnings


def generer_optimisation(plan_data, output_path):
    """Genere le fichier Excel d'optimisation de decoupe."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Calpinage"

    bars_by_diam, skip_warnings = _collect_bar_data(plan_data)
    for w in skip_warnings:
        print(f"  ⚠ {w}")

    # En-tetes
    headers = [
        "Diametre (mm)", "Nbre barres", "Longueur totale (m)",
        "Barres 12m necessaires", "Chute totale (m)", "Taux chute (%)",
        "Poids total (kg)", "Poids acier (kg)", "Economie vs achat brut"
    ]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER_ALL

    masse_lineaire = {
        6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888,
        14: 1.210, 16: 1.580, 20: 2.470, 25: 3.850, 32: 6.310,
    }

    row = 2
    total_longueur = 0
    total_barres = 0
    total_chute = 0
    total_poids = 0

    for phi in sorted(bars_by_diam.keys()):
        longueurs = bars_by_diam[phi]
        nb_total = len(longueurs)
        long_totale = sum(longueurs)

        cuts = _cuts_for_bar(longueurs)
        nb_barres_marchandes = len(cuts)
        chute_totale = sum(c for _, c in cuts)

        ml = masse_lineaire.get(phi, phi * phi / 162.0)
        poids = long_totale * ml

        taux_chute = (chute_totale / (nb_barres_marchandes * LONGUEUR_BARRE_MARCHANDE) * 100
                      if nb_barres_marchandes > 0 else 0)

        ws.cell(row=row, column=1, value=phi)
        ws.cell(row=row, column=2, value=nb_total)
        ws.cell(row=row, column=3, value=round(long_totale, 2))
        ws.cell(row=row, column=4, value=nb_barres_marchandes)
        ws.cell(row=row, column=5, value=round(chute_totale, 2))
        ws.cell(row=row, column=6, value=round(taux_chute, 1))
        ws.cell(row=row, column=7, value=round(poids, 2))
        ws.cell(row=row, column=8, value=round(poids, 2))
        ws.cell(row=row, column=9, value=0)

        fill = FILL_OK if taux_chute < 5 else FILL_WARN
        for c in range(1, 10):
            ws.cell(row=row, column=c).font = FONT_DATA
            ws.cell(row=row, column=c).border = BORDER_ALL
            ws.cell(row=row, column=c).alignment = ALIGN_RIGHT
        ws.cell(row=row, column=6).fill = fill

        total_longueur += long_totale
        total_barres += nb_barres_marchandes
        total_chute += chute_totale
        total_poids += poids
        row += 1

    # Ligne totaux
    ws.cell(row=row, column=1, value="TOTAL").font = FONT_TOTAL
    ws.cell(row=row, column=2, value=sum(len(v) for v in bars_by_diam.values()))
    ws.cell(row=row, column=3, value=round(total_longueur, 2))
    ws.cell(row=row, column=4, value=total_barres)
    ws.cell(row=row, column=5, value=round(total_chute, 2))
    taux_global = (total_chute / (total_barres * LONGUEUR_BARRE_MARCHANDE) * 100
                   if total_barres > 0 else 0)
    ws.cell(row=row, column=6, value=round(taux_global, 1))
    ws.cell(row=row, column=7, value=round(total_poids, 2))
    ws.cell(row=row, column=8, value=round(total_poids, 2))
    for c in range(1, 10):
        ws.cell(row=row, column=c).font = FONT_TOTAL
        ws.cell(row=row, column=c).fill = FILL_TOTAL
        ws.cell(row=row, column=c).border = BORDER_ALL

    # Ajuster largeurs
    widths = [14, 12, 18, 20, 16, 14, 14, 14, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wb.save(output_path)
    print(f"Optimisation generee : {output_path}")
    print(f"  Barres 12m : {total_barres}")
    print(f"  Taux chute global : {taux_global:.1f}%")
    print(f"  Poids total : {total_poids:.1f} kg")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="output/plan_data.json")
    ap.add_argument("--out", default="output/optimisation_chantiers.xlsx")
    args = ap.parse_args()
    with open(args.plan, encoding="utf-8") as f:
        plan_data = json.load(f)
    generer_optimisation(plan_data, args.out)
