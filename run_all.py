#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chaîne le pipeline complet : extraction -> métré -> rapport -> optimisation."""
import subprocess, sys

STEPS = [
    ["extract_plan.py"],
    ["build_metre.py"],
    ["build_report.py"],
    ["build_optimisation.py"],
]
for cmd in STEPS:
    print(f"\n=== {cmd[0]} ===")
    r = subprocess.run([sys.executable] + cmd)
    if r.returncode != 0:
        sys.exit(f"Échec : {cmd[0]}")
print("\nPipeline terminé -> output/")
