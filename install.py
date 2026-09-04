#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install.py — Installateur autonome pour Métré BA Agent.

Usage : python install.py
Ouvre un wizard d'installation pas à pas dans le terminal.
"""
import os, sys, subprocess, shutil, json
from pathlib import Path

INSTALL_DIR = Path(__file__).resolve().parent

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ███╗███████╗████████╗██████╗ ███████╗              ║
║   ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██╔════╝              ║
║   ██╔████╔██║█████╗     ██║   ██████╔╝█████╗                ║
║   ██║╚██╔╝██║██╔══╝     ██║   ██╔══██╗██╔══╝                ║
║   ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║███████╗              ║
║   ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝              ║
║                                                              ║
║   ██████╗  █████╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗  ║
║   ██╔══██╗██╔══╝    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝  ║
║   ██████╔╝███████╗   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║     ║
║   ██╔══██╗██╔════╝   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║     ║
║   ██████╔╝███████╗   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║     ║
║   ╚═════╝ ╚══════╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝     ║
║                                                              ║
║          Installateur v1.0.0 — Métre BA Agent                ║
╚══════════════════════════════════════════════════════════════╝
"""

COMPONENTS = [
    {"id": "core", "name": "Core Python", "desc": "pdfplumber, openpyxl, PyMuPDF, reportlab", "size": "~50 MB", "required": True},
    {"id": "api", "name": "Backend API", "desc": "FastAPI, uvicorn", "size": "~30 MB", "required": True},
    {"id": "electron", "name": "App Desktop Electron", "desc": "Interface professionnelle", "size": "~150 MB", "required": True},
    {"id": "vision", "name": "Vision IA (torch)", "desc": "transformers, torch, accelerate", "size": "~2 GB", "required": False},
    {"id": "ocr", "name": "GLM-OCR modèle", "desc": "OCR local open-source", "size": "~2 GB", "required": False},
    {"id": "latex", "name": "LaTeX (TeX Live)", "desc": "Rapports PDF avec formules", "size": "~4 GB", "required": False},
]

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def header(step, total=5):
    clear()
    print(BANNER)
    print(f"\n  Étape {step}/{total}  {'█' * (step * 4)}{'░' * ((total - step) * 4)}\n")

def pause(): input("\n  Appuyez sur Entrée pour continuer...")

def run_cmd(cmd, desc=""):
    if desc: print(f"  → {desc}...")
    r = subprocess.run(cmd, cwd=str(INSTALL_DIR), capture_output=True, shell=True)
    return r.returncode == 0

def detect():
    state = {"core": False, "api": False, "electron": False, "vision": False}
    try:
        import pdfplumber, openpyxl, fitz, reportlab
        state["core"] = True
    except: pass
    try:
        import fastapi, uvicorn
        state["api"] = True
    except: pass
    try:
        import torch, transformers
        state["vision"] = True
    except: pass
    if (INSTALL_DIR / "electron" / "node_modules" / ".package-lock.json").exists():
        state["electron"] = True
    return state

def main():
    # Step 1: Welcome
    header(1)
    print("  Bienvenue dans l'installation de Métré BA Agent !")
    print("  Cet assistant va installer les composants nécessaires.\n")
    print("  Fonctionnalités :")
    print("    • Métré Excel professionnel (3 feuilles)")
    print("    • Vision IA + OCR local (GLM-OCR)")
    print("    • Rapports PDF + LaTeX")
    print("    • 16 modules BAEL/EC2 intégrés")
    pause()

    # Step 2: Detect existing
    header(2)
    print("  Détection des composants déjà installés...\n")
    state = detect()
    for c in COMPONENTS:
        status = "✓ Installé" if state.get(c["id"], False) else "✗ Non installé"
        req = " (obligatoire)" if c["required"] else ""
        print(f"    {c['name']:30s} {status}{req}")
    pause()

    # Step 3: Choose components
    header(3)
    print("  Sélectionnez les composants à installer :\n")
    selected = []
    for c in COMPONENTS:
        req = " *" if c["required"] else ""
        default = "O" if c["required"] or not c["id"] in ["vision", "ocr", "latex"] else "n"
        inp = input(f"    [{default}] {c['name']} ({c['size']}){req} : ").strip().lower()
        if inp == "" and default == "O":
            selected.append(c["id"])
        elif inp in ("o", "oui", "y", "yes"):
            selected.append(c["id"])
    pause()

    # Step 4: Install
    header(4)
    print("  Installation en cours...\n")
    if "core" in selected:
        run_cmd([sys.executable, "-m", "pip", "install", "--quiet",
                 "pdfplumber", "openpyxl", "PyMuPDF", "PyYAML", "reportlab"],
                "Installation Core Python")
    if "api" in selected:
        run_cmd([sys.executable, "-m", "pip", "install", "--quiet",
                 "fastapi", "uvicorn", "python-multipart"],
                "Installation Backend API")
    if "electron" in selected:
        run_cmd(["npm", "install"], "Installation Electron")
    if "vision" in selected:
        run_cmd([sys.executable, "-m", "pip", "install", "--quiet",
                 "transformers", "torch", "torchvision", "accelerate"],
                "Installation Vision IA (~2GB, peut prendre du temps)")
    if "ocr" in selected:
        print("  → Téléchargement GLM-OCR (~2GB)...")
        subprocess.run([sys.executable, "-c",
            "from transformers import AutoProcessor; AutoProcessor.from_pretrained('zai-org/GLM-OCR')"],
            cwd=str(INSTALL_DIR))
    pause()

    # Step 5: Done
    header(5)
    print("  ✓ Installation terminée !\n")
    print("  Pour lancer l'application :")
    print("    • Double-cliquez sur start.bat")
    print("    • Ou : python run_all.py")
    print("    • Ou : cd electron && npm start\n")
    pause()

if __name__ == "__main__":
    main()
