#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_batch.py — Mode batch : traite un ou tous les exemples du dossier dataset/.

Usage :
  python run_batch.py --example dataset/examples/001_MZINDA_Youssoufia
  python run_batch.py --all
  python run_batch.py --pdf mon_plan.pdf --ref mon_metre.xlsx   # plan isolé

Pour chaque exemple :
  1. Copie le plan dans reference/ et lance le pipeline complet
  2. Compare la sortie générée avec la référence (si présente)
  3. Produit un rapport d'écarts dans l'exemple ET dans output/
"""
import argparse, glob, json, os, shutil, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

PIPELINE = ["extract_plan.py", "build_metre.py", "build_report.py", "build_optimisation.py"]


def run_example(example_dir, ref_override=None):
    """Traite un exemple : input/plan.pdf -> output/ vs output_reference/."""
    inp = os.path.join(example_dir, "input")
    plan = os.path.join(inp, "plan.pdf")
    if not os.path.exists(plan):
        # chercher tout PDF dans input/
        pdfs = glob.glob(os.path.join(inp, "*.pdf"))
        if pdfs:
            plan = pdfs[0]
        else:
            print(f"  SKIP {example_dir} : aucun PDF dans input/")
            return False

    ref_dir = os.path.join(example_dir, "output_reference")
    ref_metre = ref_override
    if not ref_metre:
        refs = glob.glob(os.path.join(ref_dir, "*.xlsx"))
        ref_metre = refs[0] if refs else None

    # copier le plan dans reference/ pour le pipeline
    os.makedirs("reference", exist_ok=True)
    shutil.copy2(plan, "reference/PLAN_BA_final.pdf")
    if ref_metre:
        shutil.copy2(ref_metre, "reference/metre_MZINDA.xlsx")

    print(f"\n{'='*60}")
    print(f"  EXEMPLE : {os.path.basename(example_dir)}")
    print(f"  Plan    : {plan}")
    print(f"  Réf     : {ref_metre or '(aucune)'}")
    print(f"{'='*60}\n")

    # lancer le pipeline
    for script in PIPELINE:
        cmd = [sys.executable, script]
        if script == "extract_plan.py":
            cmd += ["--pdf", plan]
        if script == "build_metre.py" and ref_metre:
            cmd += ["--reference", ref_metre]
        print(f"--- {script} ---")
        r = subprocess.run(cmd, cwd=os.getcwd())
        if r.returncode != 0:
            print(f"  ERREUR : {script} a échoué (code {r.returncode})")
            return False

    # copier les résultats dans l'exemple
    out_ex = os.path.join(example_dir, "output_genere")
    os.makedirs(out_ex, exist_ok=True)
    for f in ["metre_genere.xlsx", "rapport_metre.pdf",
              "optimisation_bonnes_pratiques.xlsx", "rapport_verification.md",
              "summary.json"]:
        src = os.path.join("output", f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out_ex, f))

    print(f"\n  Résultats copiés dans {out_ex}/")
    return True


def main():
    ap = argparse.ArgumentParser(description="Métré BA Agent — mode batch")
    ap.add_argument("--example", help="Chemin vers un exemple spécifique")
    ap.add_argument("--all", action="store_true", help="Traiter tous les exemples")
    ap.add_argument("--pdf", help="Plan PDF isolé (sans structure dataset)")
    ap.add_argument("--ref", help="Métré de référence (optionnel avec --pdf)")
    args = ap.parse_args()

    if args.pdf:
        # mode isolé : traiter un seul PDF
        os.makedirs("reference", exist_ok=True)
        shutil.copy2(args.pdf, "reference/PLAN_BA_final.pdf")
        if args.ref:
            shutil.copy2(args.ref, "reference/metre_MZINDA.xlsx")
        for script in PIPELINE:
            cmd = [sys.executable, script]
            if script == "extract_plan.py":
                cmd += ["--pdf", args.pdf]
            if script == "build_metre.py" and args.ref:
                cmd += ["--reference", args.ref]
            print(f"\n--- {script} ---")
            subprocess.run(cmd, cwd=os.getcwd())
        print("\nTerminé -> output/")
        return

    if args.example:
        run_example(args.example, args.ref)
        return

    if args.all:
        examples = sorted(glob.glob("dataset/examples/*/"))
        if not examples:
            print("Aucun exemple trouvé dans dataset/examples/")
            return
        ok = 0
        for ex in examples:
            if run_example(ex):
                ok += 1
        print(f"\n{ok}/{len(examples)} exemples traités avec succès.")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
