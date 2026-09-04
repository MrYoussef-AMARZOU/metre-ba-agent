# Métré BA Agent — Plan PDF/AutoCAD → Métré Excel + Rapports

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/Electron-33-green" alt="Electron">
  <img src="https://img.shields.io/badge/GLM--OCR-0.9B-orange" alt="GLM-OCR">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License">
</p>

**Application desktop professionnelle** qui lit un plan de fondations béton armé (PDF, image, ou AutoCAD) et génère automatiquement :
- Un **métré Excel structuré** (3 feuilles : fondation, armatures, comparaison)
- Un **rapport PDF** avec insights calculés (ratios kg/m³, sensibilité paramètres)
- Un **rapport LaTeX** avec calculs BAEL/EC2 détaillés et formules
- Un **Excel d'optimisation** (barres commerciales 12m, chutes, regroupements)

---

## Démarrage rapide

### Option 1 — App Desktop (recommandé)

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

L'interface Electron s'ouvre avec :
- **Dashboard** : vue d'ensemble des 16 modules intégrés
- **Nouveau Métré** : importez un plan (PDF/image/AutoCAD DWG/DXF) → lancez → téléchargez
- **Modules & Repos** : visualisez les 16 repos forkés et leurs contributions
- **Résultats** : suivi en temps réel + téléchargements

### Option 2 — Ligne de commande

```bash
# Pipeline complet
python run_all.py

# Ou étape par étape
python extract_plan.py --pdf plan.pdf
python build_metre.py
python build_report.py
python build_optimisation.py

# Avec OCR local GLM-OCR (pas de clé API nécessaire)
python extract_plan.py --pdf plan.pdf --ocr glm-ocr
```

### Option 3 — API

```bash
python -m uvicorn backend.api:app --port 8765
curl -X POST http://127.0.0.1:8765/pipeline -F "pdf=@plan.pdf"
```

---

## Formats supportés

| Format | Usage | Fiabilité |
|--------|-------|-----------|
| **PDF natif** | Extraction texte + vecteurs | ~95% automatique |
| **Images (PNG/JPG)** | OCR GLM-OCR ou Vision API | ~80-90% |
| **AutoCAD DWG/DXF** | Nécessite conversion ou vision | Via config manuelle |

---

## Architecture

```
metre-ba-agent/
├── start.bat / start.sh          ← Démarrage un clic
├── electron/                     ← App desktop (UI professionnelle)
│   ├── main.js                   (backend Python intégré)
│   └── src/                      (HTML/CSS/JS — dashboard, upload, résultats)
├── backend/
│   ├── api.py                    (FastAPI : pipeline via HTTP)
│   └── latex_report.py           (rapport LaTeX calculs BAEL/EC2)
├── extract_plan.py               (PDF → JSON : texte natif + vecteurs + vision)
├── build_metre.py                (JSON → Excel 3 feuilles, formules vivantes)
├── build_report.py               (rapport PDF insights)
├── build_optimisation.py         (Excel optimisation + checklist)
├── modules/ferraillage.py        (calculs BAEL 91 / Eurocode 2)
├── config/
│   ├── postes.yaml               (géométrie, catalogues, règles — éditable)
│   └── readings_vision.yaml      (lectures vision sourcées — éditable)
├── dataset/examples/             (vos plans + références)
└── research/                     (16 repos forkés — non versionnés)
```

---

## 16 Repos Forkés Intégrés

Tous forkés dans votre compte GitHub et documentés dans [`docs/SOURCES.md`](docs/SOURCES.md).

### Ferraillage BAEL/EC2 (6 repos)

| Repo | Contribution |
|------|-------------|
| [Armatures-Poteau-rectangulaire-BAEL](https://github.com/Youssef-AMARZOU/Armatures-Poteau-rectangulaire-BAEL) | Calcul ferraillage poteaux BAEL 91 |
| [calcul-section-acier-poutre-automatique-eurocode2](https://github.com/Youssef-AMARZOU/calcul-section-acier-poutre-automatique-eurocode2) | Sections acier poutres EC2 |
| [calcul-automatique-sections-acier-linteau-beton-arme](https://github.com/Youssef-AMARZOU/calcul-automatique-sections-acier-linteau-beton-arme) | Sections acier linteaux |
| [concrete-beam-diameters-quantities-reinforcement-Eurocode2](https://github.com/Youssef-AMARZOU/concrete-beam-diameters-quantities-reinforcement-Eurocode2) | Diamètres/quantités poutres EC2 |
| [Eurocode2-Concrete-Cover-Calc](https://github.com/Youssef-AMARZOU/Eurocode2-Concrete-Cover-Calc) | Enrobage béton EC2 |
| [eurocode2-concrete-structural-class-calculator](https://github.com/Youssef-AMARZOU/eurocode2-concrete-structural-class-calculator) | Classe structurale EC2 |

### Vision & OCR (4 repos)

| Repo | Contribution |
|------|-------------|
| [GLM-OCR (zai-org)](https://huggingface.co/zai-org/GLM-OCR) | OCR open-source 0.9B, mode JSON strict |
| [ConRebSeg (DTU-PAS)](https://github.com/Youssef-AMARZOU/ConRebSeg) | Segmentation ferraillage |
| [synthetic-datasets-for-rebar](https://github.com/Youssef-AMARZOU/synthetic-datasets-for-rebar) | Datasets synthétiques armatures |
| [RebarDSC](https://github.com/Youssef-AMARZOU/RebarDSC) | Détection/comptage armatures |

### Takeoff & Quantités (4 repos)

| Repo | Contribution |
|------|-------------|
| [opentakeoff (Kentucky-ai)](https://github.com/Youssef-AMARZOU/opentakeoff) | PDF takeoff engine MCP |
| [OpenConstructionERP](https://github.com/Youssef-AMARZOU/OpenConstructionERP) | BOQ, PDF/CAD/BIM takeoff |
| [DDC_Skills (221 skills)](https://github.com/Youssef-AMARZOU/DDC_Skills_for_AI_Agents_in_Construction) | BIM, cost estimation, scheduling |
| [layerwise.ai](https://github.com/Youssef-AMARZOU/layerwise.ai) | API pipeline documentaire |

### ERP & Outils (2 repos)

| Repo | Contribution |
|------|-------------|
| [wall-load-bearing-calculation-tool](https://github.com/Youssef-AMARZOU/wall-load-bearing-calculation-tool) | Calcul murs porteurs |
| [pypyBABA](https://github.com/Youssef-AMARZOU/pypyBABA) | Modules Python BA (poutres, dalles, RDM) |

---

## GLM-OCR — OCR Local Open-Source

**GLM-OCR** est un modèle multimodal 0.9B (MIT) pour la compréhension de documents complexes. Intégré en mode « information extraction » avec schéma JSON strict — le modèle laisse vide ce qui est illisible (politique zéro-hallucination).

### Installation

```bash
pip install transformers torch torchvision accelerate
```

Le modèle (~2GB) se télécharge automatiquement au premier usage :

```bash
python extract_plan.py --pdf plan.pdf --ocr glm-ocr
```

### Configuration dans l'UI

Cochez **GLM-OCR** dans les options — aucune clé API nécessaire.

---

## Outputs générés

| Fichier | Contenu |
|---------|---------|
| `metre_genere.xlsx` | 3 feuilles : fondation (postes 1/3/15/16/17/20/7/19), armatures (agrégat + détail + poids acier), comparaison vs référence |
| `rapport_metre.pdf` | Synthèse, répartition BA, insights (kg/m³, sensibilité N13), écarts, annexe a_verifier |
| `rapport_metre_latex.pdf` | Calculs BAEL/EC2 détaillés avec formules LaTeX |
| `optimisation.xlsx` | Barres 12m/chutes, regroupements (S4≡S5, P1×12), checklist qualité |
| `rapport_verification.md` | Éléments a_verifier + vérifications automatiques |

---

## Politique zéro-hallucination

> Aucune donnée n'est estimée silencieusement. Chaque quantité vient du texte natif du PDF, de la géométrie vectorielle ou d'une lecture vision sourcée. Tout le reste est signalé dans le rapport.

Voir [`docs/ZERO_HALLUCINATION.md`](docs/ZERO_HALLUCINATION.md) pour le détail du protocole.

---

## Résultats sur le plan d'exemple (MZINDA, Youssoufia)

- 23 semelles (S1×2, S2×1, S3×8, S4×9, S5×3), 23 poteaux, 19 longrines, 17 chaînages, poutres mezzanine + PH-RDC
- Terrassement calculé **222,85 m³** = contrôle manuel du métré de référence (N22)
- ~91 écarts documentés vs le métré manuel — dont plusieurs **erreurs réelles détectées** dans le métré manuel

---

## Limites connues

- Plans scannés sans texte ni vecteurs : tout passe par le canal vision (plus d'`a_verifier`)
- Conventions de dessin différentes → ajuster la géométrie dans `config/postes.yaml`
- Ferraillage complexe (T, jumelées) : règles paramétrées et signalées

---

## Licence

MIT — voir [`LICENSE`](LICENSE).
