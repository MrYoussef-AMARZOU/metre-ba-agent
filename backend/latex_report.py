#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backend/latex_report.py — Génération de rapport LaTeX détaillé avec calculs
BAEL 91 / Eurocode 2.

Produit un PDF LaTeX contenant :
- Synthèse quantitative du métré
- Détail des calculs de ferraillage (formules, hypothèses, résultats)
- Tableaux de résultats par poste
- Écarts vs référence
- Optimisations et recommandations

Usage standalone : python backend/latex_report.py [job_id]
"""
import json, os, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

LATEX_TEMPLATE = r"""
\documentclass[a4paper,11pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[french]{{babel}}
\usepackage{{geometry}}
\geometry{{margin=2cm}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{amsmath}}
\usepackage{{graphicx}}
\usepackage{{hyperref}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\pagestyle{{fancy}}
\fancyhead[L]{{Métré BA — Rapport de calcul}}
\fancyhead[R]{{\today}}
\definecolor{{vert}}{{RGB}}{{0,128,0}}
\definecolor{{rouge}}{{RGB}}{{200,0,0}}
\definecolor{{bleu}}{{RGB}}{{0,80,160}}

\title{{\textbf{{Rapport de Métré — Fondations Béton Armé}}\\
\large Construction de locaux et travaux de réaménagement}}
\author{{Généré automatiquement par Métré BA Agent}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Synthèse quantitative}}

\begin{{center}}
\begin{{tabular}}{{lr}}
\toprule
\textbf{{Agrégat}} & \textbf{{Valeur}} \\
\midrule
Béton armé — fondation et élévation & {vol_ba:.1f} m³ \\
Gros béton, assises & {vol_gb:.1f} m³ \\
Béton de propreté & {vol_prop:.1f} m³ \\
Terrassement & {vol_ter:.1f} m³ \\
Remblai net & {vol_rem:.1f} m³ \\
Acier total calculé & {acier:.0f} kg \\
Acier +10\% & {acier_10:.0f} kg \\
\bottomrule
\end{{tabular}}
\end{{center}}

\section{{Répartition du béton armé par famille}}

\begin{{center}}
\begin{{tabular}}{{lrc}}
\toprule
\textbf{{Famille}} & \textbf{{Volume (m³)}} & \textbf{{Part poste 20}} \\
\midrule
{famille_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\section{{Calcul du ferraillage}}

\subsection{{Hypothèses de calcul}}

\begin{{itemize}}
\item Code de calcul : BAEL 91 / Eurocode 2 (marocain)
\item Acier : HA (haute adhérence), $f_e = 400$ MPa
\item Béton : C25/30 ($f_{ck} = 25$ MPa)
\item Enrobage : selon classe d'exposition (EC2 §4.4.1)
\item Ancrege des barres : $L_a = 34 \cdot \phi$ (BAEL 91)
\item Développement des cadres : $2 \times (b+h) - 8 \times e + 20.5 \cdot \phi$
\end{{itemize}}

\subsection{{Tableau des semelles}}

\begin{{center}}
\begin{{tabular}}{{lcccccc}}
\toprule
\textbf{{Repère}} & \textbf{{A (m)}} & \textbf{{B (m)}} & \textbf{{H (m)}} & \textbf{{Bars x}} & \textbf{{Bars y}} & \textbf{{Nbre}} \\
\midrule
{semelle_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\subsection{{Tableau des poteaux}}

\begin{{center}}
\begin{{tabular}}{{lcccc}}
\toprule
\textbf{{Type}} & \textbf{{b (m)}} & \textbf{{h (m)}} & \textbf{{Section}} & \textbf{{Nbre}} \\
\midrule
{poteau_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\subsection{{Formules de calcul}}

\subsubsection{{Semelles isolées}}

Pour chaque semelle de type $S_n$ à l'intersection $(axe, travée)$ :

\begin{{align}}
V_{{béton}} &= A \times B \times H \\
L_{{barre,x}} &= A - 2 \cdot e_{{enr}} + 2 \times 34 \cdot \phi \\
L_{{barre,y}} &= B - 2 \cdot e_{{enr}} + 2 \times 34 \cdot \phi \\
P_{{acier}} &= n_x \cdot \frac{{\phi^2}}{{162}} \cdot L_x + n_y \cdot \frac{{\phi^2}}{{162}} \cdot L_y
\end{{align}}

où $e_{{enr}}$ = enrobage (0.05 m), $\phi$ = diamètre des barres (12 mm pour S1-S5).

\subsubsection{{Fûts de poteaux}}

Pour chaque poteau $P_n$ à l'intersection $(axe, travée)$ :

\begin{{align}}
V_{{béton}} &= b \times h \times L_{{fût}} \\
L_{{fût}} &= H_{{bon~sol}} - 0.13 - 0.10 - 0.25 \\
L_{{barre~long}} &= T_{{76}} + 18 \cdot \phi_{{long}} / 1000 \\
n_{{cadres}} &= \left\lceil \frac{{L_{{fût}} - 0.25}}{{0.15}} \right\rceil + 2 \\
L_{{cadre}} &= 2(b + h) - 0.05 + 20.5 \cdot \phi_{{cad}} / 1000
\end{{align}}

\subsubsection{{Longrines et chaînages}}

\begin{{align}}
V_{{béton}} &= L \times b \times h \\
L_{{nappe}} &= L + \left\lceil \frac{{L}}{{12}} \right\rceil \quad \text{{(recouvrement)}} \\
n_{{cadres}} &= \left\lceil \frac{{L}}{{0.20}} \right\rceil
\end{{align}}

\section{{Écarts vs métré de référence}}

{ecarts_text}

\section{{Vérifications automatiques}}

\begin{{itemize}}
{checks_text}
\end{{itemize}}

\section{{Éléments à vérifier}}

\begin{{itemize}}
{a_verifier_text}
\end{{itemize}}

\section{{Optimisations recommandées}}

\begin{{enumerate}}
\item S4 et S5 ont des dimensions identiques (150×150×40) : 12 éléments partagent
      la même section — unification possible si le BET confirme.
\item Axes 6, 7 et 8 portent les mêmes familles de poutres (N3/N1/N3 par niveau) :
      coffrage et débit standardisables.
\item Le ferraillage des semelles S4 et S5 est identique (11HA12) : mêmes nappes
      à préfabriquer.
\item P1 (12 unités) domine le parc de poteaux : un seul type de cage à
      industrialiser.
\item Longueurs de barres : privilégier les barres commerciales de 12 m pour
      minimiser les chutes.
\end{{enumerate}}

\end{{document}}
"""


def generate_latex_report(job_id="default"):
    """Generate a LaTeX report from the pipeline outputs."""
    summary_path = "output/summary.json"
    if os.path.exists(f"output/{job_id}/summary.json"):
        summary_path = f"output/{job_id}/summary.json"

    s = json.load(open(summary_path, encoding="utf-8"))
    vols = s.get("vols", {})
    acier = s.get("acier_total_kg", 0)
    vol_ba = vols.get("BA (poste 20)", 0)

    # Family table
    fam_lines = []
    for k, v in sorted(s.get("par_section", {}).items(), key=lambda x: -x[1]):
        part = f"{v / vol_ba * 100:.0f}\\%" if vol_ba else "---"
        fam_lines.append(f"{k} & {v:.2f} & {part} \\\\")
    famille_table = "\n".join(fam_lines)

    # Semelle table from config
    import metre_core
    cfg = metre_core.load_config("config/postes.yaml")
    sem_lines = []
    for st, cat in cfg["catalogues"]["semelles"].items():
        note = " (plan)" if cat.get("note") else ""
        sem_lines.append(
            f"{st}{note} & {cat['A']:.2f} & {cat['B']:.2f} & {cat['H']:.2f} "
            f"& {cat['fx'][0]} & {cat['fy'][0]} & --- \\\\")
    semelle_table = "\n".join(sem_lines)

    # Poteau table
    pot_lines = []
    for pt, cat in cfg["catalogues"]["poteaux"].items():
        pot_lines.append(
            f"{pt} & {cat['b']:.2f} & {cat['h']:.2f} "
            f"& {cat['b']*100:.0f}×{cat['h']*100:.0f} cm & --- \\\\")
    poteau_table = "\n".join(pot_lines)

    # Ecarts
    ecarts_file = f"output/{job_id}/rapport_verification.md"
    if not os.path.exists(ecarts_file):
        ecarts_file = "output/rapport_verification.md"
    ecarts_text = ""
    if os.path.exists(ecarts_file):
        for ln in open(ecarts_file, encoding="utf-8").read().splitlines():
            if ln.startswith("- ["):
                ecarts_text += f"\\item {ln[2:].replace('&', '\\&')}\n"
    if not ecarts_text:
        ecarts_text = "\\item Aucun écart documenté.\n"

    # Checks
    plan_file = f"output/{job_id}/plan_data.json"
    if not os.path.exists(plan_file):
        plan_file = "output/plan_data.json"
    checks_text = ""
    if os.path.exists(plan_file):
        plan = json.load(open(plan_file, encoding="utf-8"))
        for c in plan.get("checks", []):
            checks_text += f"\\item {json.dumps(c, ensure_ascii=False).replace('&', '\\&')}\n"

    # A verifier
    a_verifier_text = ""
    if os.path.exists(ecarts_file):
        for ln in open(ecarts_file, encoding="utf-8").read().splitlines():
            if ln.startswith("- ["):
                a_verifier_text += f"\\item {ln[2:].replace('&', '\\&')}\n"

    latex = LATEX_TEMPLATE.format(
        vol_ba=vol_ba,
        vol_gb=vols.get("gros béton", 0),
        vol_prop=vols.get("propreté", 0),
        vol_ter=vols.get("terrassement", 0),
        vol_rem=vols.get("remblai net", 0),
        acier=acier,
        acier_10=acier * 1.1,
        famille_table=famille_table,
        semelle_table=semelle_table,
        poteau_table=poteau_table,
        ecarts_text=ecarts_text,
        checks_text=checks_text,
        a_verifier_text=a_verifier_text,
    )

    out_dir = Path(f"output/{job_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / "rapport_metre.tex"
    tex_path.write_text(latex, encoding="utf-8")

    # Compile to PDF (requires pdflatex)
    try:
        for _ in range(2):  # Two passes for TOC
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", str(tex_path)],
                cwd=str(out_dir), capture_output=True, timeout=60)
        pdf_path = out_dir / "rapport_metre_latex.pdf"
        if pdf_path.exists():
            print(f"-> {pdf_path}")
            return str(pdf_path)
        else:
            print(f"LaTeX compilation failed, .tex saved at {tex_path}")
            return str(tex_path)
    except FileNotFoundError:
        print(f"pdflatex not found, .tex saved at {tex_path}")
        return str(tex_path)


if __name__ == "__main__":
    job_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    generate_latex_report(job_id)
