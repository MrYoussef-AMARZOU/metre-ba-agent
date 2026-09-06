#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/paths.py -- Resolution centralisee des chemins.

Gere correctement les deux modes :
  - Script Python standard  : outputs a cote du repo
  - PyInstaller --onefile    : outputs a cote du .exe (pas dans _MEIPASS)
"""
import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """Repertoire racine de l'application (a cote du .exe ou du script)."""
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).parent.parent


def get_output_dir() -> Path:
    """Repertoire de sortie 'output/' a cote de l'application."""
    out = get_base_dir() / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_config_dir() -> Path:
    """Repertoire de configuration 'config/'."""
    return get_base_dir() / "config"
