#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generators/excel_optimisation.py -- Calpinage (Cutting Stock) des barres 12 m.

Re-export du moteur d'optimisation : algorithme glouton de decoupe sur barres
marchandes de 12.00 m, chute residuelle reelle par barre, taux de chute moyen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from optimisation_chantiers import (  # noqa: F401,E402
    generer_optimisation,
    _collect_bar_data,
    _cuts_for_bar,
)
