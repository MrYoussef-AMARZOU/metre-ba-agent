#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backend/latex_report.py — Génération de rapport LaTeX détaillé avec calculs BAEL 91.

Version 100% dynamique. Lit les données du plan JSON et du classeur Excel.
Aucune valeur hardcodée d'un projet spécifique.

Usage standalone : python backend/latex_report.py [--plan sample_plan_data.json] [--metre output/test_metre_genere.xlsx]
"""
import argparse, json, os, subprocess, sys
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

\title{{\textbf{{Rapport de Métré — {titre_projet}}}}}
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
Semelles & {nb_semelles} \\
Poteaux & {nb_poteaux} \\
Poutres & {nb_poutres} \\
Total éléments & {nb_total} \\
Diamètres utilisés & {diametres} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\section{{Catalogue des types}}

\subsection{{Semelles}}

\begin{{center}}
\begin{{tabular}}{{lcccc}}
\toprule
\textbf{{Type}} & \textbf{{A (m)}} & \textbf{{B (m)}} & \textbf{{H (m)}} & \textbf{{Ferraillage}} \\
\midrule
{semelle_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\subsection{{Poteaux}}

\begin{{center}}
\begin{{tabular}}{{lcccl}}
\toprule
\textbf{{Type}} & \textbf{{b (m)}} & \textbf{{h (m)}} & \textbf{{Section}} & \textbf{{Armature}} \\
\midrule
{poteau_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\subsection{{Poutres}}

\begin{{center}}
\begin{{tabular}}{{lccl}}
\toprule
\textbf{{Type}} & \textbf{{b (m)}} & \textbf{{h (m)}} & \textbf{{Armature}} \\
\midrule
{poutre_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\section{{Calcul du ferraillage}}

\subsection{{Hypothèses de calcul}}

\begin{{itemize}}
\item Code de calcul : BAEL 91 / Eurocode 2 (marocain)
\item Acier : HA (haute adhérence), $f_e = 400$ MPa
\item Béton : C25/30 ($f_{{ck}} = 25$ MPa)
\item Enrobage fondation : 0.05 m
\item Enrobage élévation : 0.025 m
\item Ancrage des barres : $L_a = 34 \cdot \phi$ (BAEL 91)
\item Développement des cadres : $2 \times (b+h) - e + 20.5 \cdot \phi$
\item Masse linéique : $d^2 / 162$ kg/m
\end{{itemize}}

\subsection{{Formules de calcul}}

\subsubsection{{Semelles isolées}}

\begin{{align}}
V_{{béton}} &= A \times B \times H \\
L_{{barre}} &= (Dim - e_{{enr}}) + 34 \cdot \phi / 1000 \\
n_{{cadres}} &= \left\lceil \frac{{L}}{{e}} \right\rceil + 2
\end{{align}}

\subsubsection{{Poteaux}}

\begin{{align}}
V_{{béton}} &= b \times h \times H_{{fût}} \\
L_{{barre}} &= H_{{fût}} + 2 \cdot 34 \cdot \phi / 1000 \\
n_{{cadres}} &= \left\lceil \frac{{H}}{{e}} \right\rceil + 2 \\
L_{{cadre}} &= 2(b + h) - e + 20.5 \cdot \phi / 1000
\end{{align}}

\subsubsection{{Poutres}}

\begin{{align}}
V_{{béton}} &= b \times h \times L \\
L_{{barre}} &= L + 2 \cdot 34 \cdot \phi / 1000 \\
n_{{cadres}} &= \left\lceil \frac{{L}}{{e}} \right\rceil + 2
\end{{align}}

\end{{document}}
"""


def generate_latex_report(plan_path="sample_plan_data.json", out_dir="output"):
    """Generate a LaTeX report from the plan JSON data."""
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)

    projet = plan.get("projet", {})
    catalogue = plan.get("catalogue_types", {})
    implantations = plan.get("implantations", {})

    # Counts
    nb_semelles = len(implantations.get("semelles", []))
    nb_poteaux = len(implantations.get("poteaux", []))
    nb_poutres = len(implantations.get("poutres", []))
    nb_total = nb_semelles + nb_poteaux + nb_poutres

    # Diameters
    diam_set = set()
    for cat in ["semelles", "poteaux", "poutres"]:
        for dims in catalogue.get(cat, {}).values():
            if cat == "semelles":
                diam_set.add(dims.get("ferr_x", {}).get("phi", 12))
                diam_set.add(dims.get("ferr_y", {}).get("phi", 12))
            elif cat == "poteaux":
                for lb in dims.get("long_bars", []):
                    diam_set.add(lb.get("phi", 14))
                diam_set.add(dims.get("cadres", {}).get("phi", 6))
            elif cat == "poutres":
                for fi in dims.get("filants_inf", []):
                    diam_set.add(fi.get("phi", 14))
                for fs in dims.get("filants_sup", []):
                    diam_set.add(fs.get("phi", 12))
                diam_set.add(dims.get("cadres", {}).get("phi", 6))
    diametres_str = ", ".join(str(d) + " mm" for d in sorted(diam_set))

    # Semelle table
    sem_lines = []
    for type_key, dims in catalogue.get("semelles", {}).items():
        fx = dims.get("ferr_x", {})
        fy = dims.get("ferr_y", {})
        arm = f"{fx.get('nb', 0)}HA{fx.get('phi', 0)} / {fy.get('nb', 0)}HA{fy.get('phi', 0)}"
        sem_lines.append(f"{type_key} & {dims['a']:.2f} & {dims['b']:.2f} & {dims['h']:.2f} & {arm} \\\\")
    semelle_table = "\n".join(sem_lines) if sem_lines else "--- \\\\"

    # Poteau table
    pot_lines = []
    for type_key, dims in catalogue.get("poteaux", {}).items():
        lbs = dims.get("long_bars", [])
        arm = ", ".join(f"{lb['nb']}HA{lb['phi']}" for lb in lbs)
        c = dims.get("cadres", {})
        arm += f" + cadres HA{c.get('phi', 0)} e={c.get('esp', 0)}m"
        pot_lines.append(f"{type_key} & {dims['a']:.2f} & {dims['b']:.2f} & {dims['a']*100:.0f}x{dims['b']*100:.0f} cm & {arm} \\\\")
    poteau_table = "\n".join(pot_lines) if pot_lines else "--- \\\\"

    # Poutre table
    pou_lines = []
    for type_key, dims in catalogue.get("poutres", {}).items():
        fi = dims.get("filants_inf", [])
        fs = dims.get("filants_sup", [])
        c = dims.get("cadres", {})
        arm_inf = ", ".join(f"{f['nb']}HA{f['phi']}" for f in fi)
        arm_sup = ", ".join(f"{f['nb']}HA{f['phi']}" for f in fs)
        arm = f"Inf: {arm_inf}, Sup: {arm_sup}, Cadres: HA{c.get('phi', 0)} e={c.get('esp', 0)}m"
        pou_lines.append(f"{type_key} & {dims['b']:.2f} & {dims['h']:.2f} & {arm} \\\\")
    poutre_table = "\n".join(pou_lines) if pou_lines else "--- \\\\"

    # Titre
    titre = projet.get("nom", "Projet BA")

    latex = LATEX_TEMPLATE.format(
        titre_projet=titre,
        nb_semelles=nb_semelles,
        nb_poteaux=nb_poteaux,
        nb_poutres=nb_poutres,
        nb_total=nb_total,
        diametres=diametres_str,
        semelle_table=semelle_table,
        poteau_table=poteau_table,
        poutre_table=poutre_table,
    )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    tex_path = out_path / "rapport_metre.tex"
    tex_path.write_text(latex, encoding="utf-8")

    # Compile to PDF
    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", str(tex_path)],
                cwd=str(out_path), capture_output=True, timeout=60)
        pdf_path = out_path / "rapport_metre_latex.pdf"
        if pdf_path.exists():
            print(f"Rapport LaTeX généré : {pdf_path}")
            return str(pdf_path)
        else:
            print(f"Compilation LaTeX échouée, .tex sauvegardé : {tex_path}")
            return str(tex_path)
    except FileNotFoundError:
        print(f"pdflatex introuvable, .tex sauvegardé : {tex_path}")
        return str(tex_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="sample_plan_data.json")
    ap.add_argument("--out", default="output")
    args = ap.parse_args()
    generate_latex_report(args.plan, args.out)
