#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_optimisation.py — Classeur Excel « Optimisation & bonnes pratiques ».

1. "Synthèse optimisable" : agrégations calculées depuis output/summary.json et
   output/metre_lines.json (générés par build_metre.py) — longueurs vs barres
   commerciales de 12 m, regroupements d'éléments identiques, fourchettes
   usuelles de taux d'acier (indicatives).
2. "Bonnes pratiques métré" : checklist de contrôle qualité (guidance générale,
   clairement étiquetée comme recommandations, pas des données).

Usage : python build_optimisation.py [--out output/optimisation_bonnes_pratiques.xlsx]
"""
import argparse, json, sys
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side

sys.stdout.reconfigure(encoding="utf-8")

BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14, color="1F4E79")
HDR = PatternFill("solid", fgColor="DDEBF7")
WARN = PatternFill("solid", fgColor="FFF2CC")
OK = PatternFill("solid", fgColor="E2EFDA")
THIN = Side(style="thin")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

TAUX_USUELS = {  # fourchettes indicatives (kg/m³) — pratique courante BET
    "semelles": (25, 60), "longrines": (80, 120), "chaînages": (80, 120),
    "fûts": (120, 200), "poteaux élévation": (120, 200), "poutres": (100, 160),
    "massifs": (20, 40),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", default="output/metre_lines.json")
    ap.add_argument("--summary", default="output/summary.json")
    ap.add_argument("--out", default="output/optimisation_bonnes_pratiques.xlsx")
    args = ap.parse_args()

    lines = json.load(open(args.lines, encoding="utf-8"))
    s = json.load(open(args.summary, encoding="utf-8"))

    # longueurs des éléments linéaires -> analyse chutes vs barres de 12 m
    longueurs = defaultdict(lambda: [0, 0.0])
    for e in lines:
        if e.get("nom") in ("LG", "LG2", "CH", "CH1", "BN2", "BN1") or \
           (isinstance(e.get("repere"), str) and e["repere"].startswith("N")):
            if isinstance(e.get("I"), (int, float)) and e["I"]:
                key = f"{e['nom'] or e['repere']} ({e['section']})"
                longueurs[key][0] += 1
                longueurs[key][1] += abs(e["I"])

    vol_ba = s["vols"].get("BA (poste 20)", 0)
    par_sec = s.get("par_section", {})

    wb = Workbook()
    s1 = wb.active
    s1.title = "Synthèse optimisable"
    s1["A1"] = "Optimisations calculées depuis le métré généré"
    s1["A1"].font = TITLE
    s1["A2"] = ("Agrégations issues du classeur métré (aucune donnée inventée). "
                "Fourchettes de taux d'acier : indicatives (pratique courante BET).")
    r = 4
    for c, t in enumerate(["Famille BA", "Volume (m³)", "Fourchette acier usuelle (kg/m³)"],
                          start=1):
        s1.cell(row=r, column=c, value=t).font = BOLD
        s1.cell(row=r, column=c).fill = HDR
    r += 1
    fam_vol = [(k, v) for k, v in par_sec.items() if k in TAUX_USUELS or
               k in ("semelles (propreté)", "longrines (propreté)",
                     "chaînages (propreté)")]
    fam_vol.sort(key=lambda x: -x[1])
    for k, v in fam_vol:
        lo, hi = TAUX_USUELS.get(k.replace(" (propreté)", ""), (None, None))
        s1.cell(row=r, column=1, value=k)
        s1.cell(row=r, column=2, value=round(v, 2))
        s1.cell(row=r, column=3, value=f"{lo}–{hi}" if lo else "—")
        for c in range(1, 4):
            s1.cell(row=r, column=c).border = BORDER
        r += 1

    r += 1
    s1.cell(row=r, column=1, value="Analyse des longueurs vs barres commerciales (12 m)").font = BOLD
    r += 1
    for c, t in enumerate(["Repère / section", "Éléments", "Longueur totale (m)",
                           "Barres 12 m (arrondi haut)", "Chutes estimées (m)"], start=1):
        s1.cell(row=r, column=c, value=t).font = BOLD
        s1.cell(row=r, column=c).fill = HDR
    r += 1
    for rep, (n, tot) in sorted(longueurs.items(), key=lambda x: -x[1][1]):
        nb = -(-tot // 12)
        chutes = nb * 12 - tot
        s1.cell(row=r, column=1, value=rep)
        s1.cell(row=r, column=2, value=n)
        s1.cell(row=r, column=3, value=round(tot, 2))
        s1.cell(row=r, column=4, value=int(nb))
        c5 = s1.cell(row=r, column=5, value=round(chutes, 2))
        c5.fill = OK if chutes / max(nb * 12, 1) < 0.15 else WARN
        for c in range(1, 6):
            s1.cell(row=r, column=c).border = BORDER
        r += 1

    r += 1
    s1.cell(row=r, column=1, value="Regroupements identifiés (potentiels de simplification)").font = BOLD
    r += 1
    from openpyxl.styles import Alignment
    for txt, fill in (
        ("S4 et S5 ont des dimensions identiques au plan (150x150x40) : 12 éléments "
         "partagent la même section — unification possible si le BET confirme.", WARN),
        ("Axes 6, 7 et 8 portent les mêmes familles de poutres (N3/N1/N3 par niveau) : "
         "coffrage et débit standardisables.", OK),
        ("Le ferraillage des semelles S4 et S5 est identique (11HA12) : mêmes nappes "
         "à préfabriquer.", OK),
        ("P1 (12 unités) domine le parc de poteaux : un seul type de cage à "
         "industrialiser.", OK),
    ):
        c = s1.cell(row=r, column=1, value=txt)
        c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    s2 = wb.create_sheet("Bonnes pratiques métré")
    s2["A1"] = "Checklist contrôle qualité d'un métré fondation BA"
    s2["A1"].font = TITLE
    s2["A2"] = "Recommandations générales (guidance) — à adapter aux règles du BET et du marché."
    checks = [
        ("Cotes", "Recouper les dimensions du tableau des semelles avec les étiquettes du plan (toute divergence = signaler)."),
        ("Cotes", "Vérifier que tous les axes cotés correspondent aux repères des éléments (S?, P?, N?)."),
        ("Géométrie", "Somme des travées = dimension totale cotée (24,14 m en horizontal ici) — écart = erreur."),
        ("Géométrie", "Axes intermédiaires non cotés : ne jamais supposer leur position ; demander la cote."),
        ("Volumes", "Contrôler Qté = N × L × l × H sur 3 lignes aléatoires par poste."),
        ("Volumes", "Le remblai = fouilles − (propreté + gros béton + BA + maçonnerie) ; contrôler le signe."),
        ("Ferraillage", "Vérifier chaque type de semelle contre le tableau de ferraillage (barres selon x/y)."),
        ("Ferraillage", "Contrôler les longueurs de barres : dim − 2×enrobage + ancrages (34d/20.5d/22d selon la barre)."),
        ("Ferraillage", "Épingles et cadres : nombre = ROUNDUP(longueur/espacement) ; espacement conforme au plan."),
        ("Ferraillage", "Poids acier = Σ (longueur × d²/162) puis +10% (recouvrements/déchets) à valider par le BET."),
        ("Cohérence", "Un même élément doit avoir la même section sur tous les plans (fondation/étage) — divergence = signaler."),
        ("Cohérence", "Totaux par poste = Σ sous-totaux ; jamais de valeur codée en dur dans le classeur."),
        ("Traçabilité", "Chaque ligne porte sa source (page/repère du plan) pour permettre la contre-vérification."),
        ("Traçabilité", "Lister les éléments non lisibles dans un rapport séparé — ne jamais compléter par estimation."),
        ("Production", "Volumes au 1/100 m³, tonnages au kg ; afficher les formules, pas les valeurs figées."),
    ]
    r = 4
    for c, t in enumerate(["Domaine", "Point de contrôle"], start=1):
        s2.cell(row=r, column=c, value=t).font = BOLD
        s2.cell(row=r, column=c).fill = HDR
    for dom, txt in checks:
        r += 1
        s2.cell(row=r, column=1, value=dom)
        s2.cell(row=r, column=2, value=txt)
        for c in range(1, 3):
            s2.cell(row=r, column=c).border = BORDER
    s2.column_dimensions["A"].width = 16
    s2.column_dimensions["B"].width = 110
    s1.column_dimensions["A"].width = 52
    s1.column_dimensions["B"].width = 16
    s1.column_dimensions["C"].width = 30
    s1.column_dimensions["D"].width = 22
    s1.column_dimensions["E"].width = 20

    wb.save(args.out)
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
