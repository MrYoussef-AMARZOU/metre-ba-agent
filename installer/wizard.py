#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
installer/wizard.py — Installation wizard logic.

Détecte l'état actuel, installe les composants choisis, rapporte la progression.
Appelé par le frontend Electron via subprocess ou HTTP.
"""
import os, sys, subprocess, json, shutil
from pathlib import Path

INSTALL_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = INSTALL_DIR / ".install_state.json"

COMPONENTS = {
    "core": {
        "name": "Core Python",
        "pip": ["pdfplumber>=0.11", "PyMuPDF>=1.24", "openpyxl>=3.1", "PyYAML>=6.0", "reportlab>=4.0"],
        "size_mb": 50, "required": True
    },
    "api": {
        "name": "Backend API",
        "pip": ["fastapi>=0.115", "uvicorn>=0.34", "python-multipart>=0.0.18"],
        "size_mb": 30, "required": True
    },
    "electron": {
        "name": "Application Electron",
        "npm": True, "size_mb": 150, "required": True
    },
    "vision": {
        "name": "Vision IA (torch)",
        "pip": ["transformers>=4.45", "torch>=2.2", "torchvision>=0.17", "accelerate>=0.34"],
        "size_mb": 2000, "required": False
    },
    "ocr": {
        "name": "GLM-OCR modèle",
        "model": "zai-org/GLM-OCR",
        "size_mb": 2000, "required": False
    },
    "latex": {
        "name": "LaTeX (TeX Live)",
        "external": True, "size_mb": 4000, "required": False
    },
}


def detect_state():
    """Détecte ce qui est déjà installé."""
    state = {"components": {}, "python_ok": False, "node_ok": False, "electron_ok": False}
    # Python
    try:
        import pdfplumber, openpyxl, fitz, yaml, reportlab
        state["components"]["core"] = True
        state["python_ok"] = True
    except ImportError:
        pass
    try:
        import fastapi, uvicorn, multipart
        state["components"]["api"] = True
    except ImportError:
        pass
    try:
        import torch, transformers
        state["components"]["vision"] = True
    except ImportError:
        pass
    # Node / Electron
    if shutil.which("node"):
        state["node_ok"] = True
    if (INSTALL_DIR / "electron" / "node_modules" / "electron" / "dist" / "electron.exe").exists():
        state["electron_ok"] = True
        state["components"]["electron"] = True
    # Save
    STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return state


def install_pip_packages(packages, progress_cb=None):
    """Installe des packages pip avec rapport de progression."""
    total = len(packages)
    for i, pkg in enumerate(packages):
        if progress_cb:
            progress_cb(i / total, f"Installation de {pkg}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg],
                       cwd=str(INSTALL_DIR), capture_output=True)
    if progress_cb:
        progress_cb(1.0, "Packages pip installés")


def install_electron(progress_cb=None):
    """Installe les dépendances Electron."""
    if progress_cb:
        progress_cb(0.0, "Installation des dépendances Electron...")
    subprocess.run(["npm", "install"], cwd=str(INSTALL_DIR / "electron"),
                   capture_output=True, shell=True)
    if progress_cb:
        progress_cb(1.0, "Electron installé")


def download_model(model_id, progress_cb=None):
    """Télécharge un modèle HuggingFace."""
    try:
        from transformers import AutoProcessor, AutoProcessor
        if progress_cb:
            progress_cb(0.0, f"Téléchargement du modèle {model_id}...")
        AutoProcessor.from_pretrained(model_id)
        if progress_cb:
            progress_cb(1.0, "Modèle téléchargé")
    except Exception as e:
        if progress_cb:
            progress_cb(0.0, f"Erreur modèle: {e}")
        raise


def install_components(selected, progress_cb=None):
    """Installe les composants sélectionnés."""
    total = len(selected)
    results = {"success": [], "failed": []}
    
    for i, comp_id in enumerate(selected):
        comp = COMPONENTS[comp_id]
        base_pct = i / total
        
        def sub_cb(p, msg):
            if progress_cb:
                progress_cb(base_pct + (p / total), msg)
        
        try:
            if "pip" in comp:
                install_pip_packages(comp["pip"], sub_cb)
            elif comp.get("npm"):
                install_electron(sub_cb)
            elif "model" in comp:
                download_model(comp["model"], sub_cb)
            results["success"].append(comp_id)
        except Exception as e:
            results["failed"].append({"id": comp_id, "error": str(e)})
        
        # Save state
        state = detect_state()
        state["last_install"] = results
        STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--install", nargs="+", help="Component IDs to install")
    args = ap.parse_args()
    
    if args.detect:
        print(json.dumps(detect_state(), ensure_ascii=False))
    elif args.install:
        results = install_components(args.install)
        print(json.dumps(results, ensure_ascii=False))
