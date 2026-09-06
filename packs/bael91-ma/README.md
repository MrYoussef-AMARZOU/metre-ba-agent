# BAEL 91 Morocco Partner Pack

Pack Béton Armé Marocain pour OpenConstructionERP.

## Description

Ce pack fournit une base de prix unitaires conforme à la norme BAEL 91 pour le génie civil au Maroc.

## Contenu

- **Base de prix** : Béton, armatures, coffrage, terrassement, isolation
- **Poids linéiques** : Tableau des aciers FeE 400/500
- **Nomenclature** : Codes postes DPGF marocains
- **Locale** : Français + Arabe

## Installation

### Option 1 : Drop-in
Copiez le dossier `openconstructionerp_bael91_ma` dans le répertoire `packs/` d'OpenConstructionERP.

### Option 2 : pip
```bash
cd packs/bael91-ma
pip install -e .
```

### Option 3 : via l'API
```bash
curl -X POST http://localhost:8000/api/v1/partner-pack/install \
  -F "file=@bael91-ma.zip"
```

## Activation

```bash
export OE_PARTNER_PACK=bael91-ma
```

Ou via l'interface utilisateur : Paramètres → Packs Partenaires → BAEL 91 Maroc

## Standards

- BAEL 91 révisé 99 — Règles parasismiques
- RPA 2000 — Règles de parasismage
- Norme CP 2001 — Béton armé
- DCG (2004) — Devis Généraux et Fournitures

## Licence

AGPL-3.0 — Compatible avec OpenConstructionERP