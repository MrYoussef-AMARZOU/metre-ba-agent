"""Utilitaires partagés — version générique.

Ce module fournit des helpers de base pour charger des fichiers YAML/JSON.
Plus de dépendance à la structure spécifique du projet MZINDA.
"""
import json
import yaml


def load_yaml(path):
    """Charge un fichier YAML."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path):
    """Charge un fichier JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_config(cfg_path=None):
    """Charge un fichier de configuration. Fallback sur les règles universelles."""
    if cfg_path:
        return load_yaml(cfg_path)
    # Règles par défaut (universelles)
    return {
        "rules": {
            "enrobage_fondation": 0.05,
            "enrobage_elevation": 0.025,
            "coef_ancrage": 34,
            "coef_cadre": 20.5,
            "coef_epingle": 22,
            "coef_recouvrement": 36,
            "poids_lineique": "d*d/162",
        },
        "diametres_standard": [6, 8, 10, 12, 14, 16, 20, 25, 32],
    }
