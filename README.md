# PlanBA — Métré Extracteur (Béton Armé)

<p>
  <img src="https://img.shields.io/badge/Python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Windows-10%2F11-green" alt="Windows">
  <img src="https://img.shields.io/badge/100%25%20local%20%E2%80%94%20zero%20API-orange" alt="100% local">
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="License MIT">
</p>

**Application desktop qui lit un plan de fondations en béton armé (PDF, image scannée ou AutoCAD) et génère automatiquement un métré Excel, une optimisation de découpe des aciers et un rapport d'audit PDF — 100 % en local, sans clé API, sans cloud.**

Exemple réel : sur un plan de fondation de 6 pages, l'application détecte les semelles positionnées sur leurs axes (ex. `S2 → A/5`), lit le tableau de nomenclature (`S1 : 100×100×25, 6HA12`), les détails poteaux (`P1 : 25×35, 6HA14`) et poutres, puis produit des classeurs Excel **avec formules actives** (quantités recalculées à l'ouverture).

> **Philosophie zéro-mock** : si une donnée n'est pas lisible sur le plan, elle reste absente et signalée (avertissement + hypothèse tracée) — jamais de valeurs inventées. Et si rien d'exploitable n'est détecté, l'application lève une erreur explicite au lieu de générer des classeurs vides.

---

## Table des matières

1. [Démarrage en 2 minutes](#-démarrage-en-2-minutes)
2. [Fonctionnalités](#-fonctionnalités)
3. [Les 4 livrables](#-les-4-livrables)
4. [Utilisation — interface graphique](#-utilisation--interface-graphique)
5. [Utilisation — ligne de commande](#-utilisation--ligne-de-commande)
6. [Modèle Excel standardisé + macros VBA](#-modèle-excel-standardisé--macros-vba)
7. [Comment ça marche (moteur)](#-comment-ça-marche-moteur)
8. [Formats et conventions de plans lus](#-formats-et-conventions-de-plans-lus)
9. [Hypothèses et limites connues](#-hypothèses-et-limites-connues)
10. [Développement : tests, structure, build](#-développement--tests-structure-build)
11. [Dépannage (FAQ)](#-dépannage-faq)
12. [Licence](#-licence)

---

## 🚀 Démarrage en 2 minutes

### Prérequis

- **Windows 10/11** (recommandé — glisser-déposer natif, exécutable)
- **Python 3.12** ([python.org](https://www.python.org/downloads/)) — cocher *« Add python.exe to PATH »* à l'installation
- ~500 Mo d'espace disque (environnement + dépendances)

> Linux/macOS : utilisation depuis les sources possible (interface Tk), glisser-déposer selon l'environnement.

### Option A — Depuis les sources (le plus simple pour commencer)

```powershell
# 1. Cloner le dépôt
git clone https://github.com/Youssef-AMARZOU/metre-ba-agent.git
cd metre-ba-agent

# 2. Créer l'environnement et installer les dépendances
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install customtkinter openpyxl reportlab PyMuPDF ezdxf Pillow pydantic tkinterdnd2

# 3. Lancer l'application
python main.py
```

> **Astuce :** `start.bat` (double-clic) automatise les étapes 2 et 3 s'il est à jour sur votre poste.

### Option B — Exécutable Windows autonome (sans Python)

```powershell
.\.venv\Scripts\python.exe build_executable.py
```

Après ~5 à 10 minutes de compilation, lancez :

```
dist\PlanBA_Metre_Extractor\PlanBA_Metre_Extractor.exe
```

- Mode **dossier** (`--onedir`) : démarrage instantané, aucune extraction temporaire à chaque lancement.
- Un **splash screen** natif s'affiche pendant le chargement puis se referme automatiquement.
- ⚠️ Le dossier `dist/` pèse ~300 Mo (moteur OCR embarqué) et **n'est pas versionné** — chaque poste construit son propre `.exe`.

---

## ✨ Fonctionnalités

| Fonction | Détail |
|---|---|
| 📄 **Lecture multi-formats** | PDF vectoriel (1 à 1000+ pages), PDF scanné (OCR local), images PNG/JPG/TIFF/BMP/WebP, DXF/DWG AutoCAD |
| 🧠 **Extraction 100 % locale** | `find_tables()` PyMuPDF + parsing spatial par coordonnées — aucune API, aucune clé |
| 🗺️ **Repérage réel** | Semelles positionnées sur leurs axes (lettres A–G, files 1–8) lues sur le plan |
| 🇫🇷🇲🇦 **Conventions FR + marocaines** | Poteaux `P`/`Q`, étiquettes couplées `(S1,Q1)` (tolérance OCR `0/O→Q`), poutres `N`/`BN`/`PN`/`PC`/`LG`/`CH`, ferraillage `HA` ou `T` (`8T12`, `2CAD T6 e=15`) |
| 📊 **Excel avec formules actives** | Quantités, ventilation acier par diamètre, totaux `SUM/IF` recalculés à l'ouverture |
| ✂️ **Optimisation de découpe** | Calpinage des barres 12 m (cutting-stock), chutes réelles, taux de chute, poids |
| 📑 **Rapport d'audit PDF** | Bilan matière, ratios kg/m³, ventilation par famille/diamètre, alertes |
| 🖱️ **Interface moderne** | Thème sombre, glisser-déposer natif Windows, validation pré-import (pre-flight), progression page par page |
| 📐 **Modèle vierge standardisé** | Classeur 4 feuilles type BET + macros VBA (`vba/Module1.bas`) |
| 🛡️ **Zéro donnée fictive** | Donnée absente = signalée, jamais inventée ; échec explicite si plan inexploitable |

---

## 📦 Les 4 livrables

Tous générés dans `output/` (à côté du script, ou à côté du `.exe` en mode compilé) :

| Fichier | Contenu |
|---|---|
| `plan_data.json` | Données structurées extraites : `catalogue_types` (semelles/poteaux/poutres + specs réelles), `implantations` (positions sur axes), `_meta` (pages scannées, avertissements, hypothèses) |
| `metre_genere.xlsx` | **Feuille 1** `Detail quontitafif fondation` : postes Terrassement `(a+0,40)×(b+0,40)×1,50`, Béton de propreté `(a+0,20)×(b+0,20)×0,10`, Béton armé `a×b×h`, fûts poteaux — **Feuille 2** `Armatures` : ligne mère par élément + nappes INF X/Y avec `LONG = (dim−0,05) + 34×Φ/1000`, ventilation `=IF($I=diam,$G*$H*$J,"")`, totaux `LONGUEUR TOTALE / POIDS-ML (Φ²/162) / POIDS PARTIELS / POIDS TOTAL` |
| `optimisation_chantiers.xlsx` | Calpinage : par diamètre, barres 12 m nécessaires, chute réelle par barre, taux de chute, poids. Les poutres sans portée cotée sont exclues avec avertissement (pas de valeur inventée) |
| `rapport_metre.pdf` | Bilan matière (volume béton, poids acier, ratio kg/m³), ventilation par famille et par diamètre, observations + avertissements d'extraction. Si volume ou poids = 0 : **« ⚠ ALERTE : Données manquantes »** (jamais « dans la norme ») |

Fichier bonus : `output/modele_metre_BA.xlsx` — le modèle vierge (voir section dédiée).

---

## 🖱️ Utilisation — interface graphique

1. **Lancez** `python main.py` (ou le `.exe`).
2. **Chargez un plan** : bouton **Parcourir…** ou **glisser-déposer** le fichier n'importe où sur la fenêtre.
   - Le validateur pré-import analyse le document (mots-clés génie civil, format, densité vectorielle) :
     - ✅ vert : plan technique reconnu → bouton d'analyse activé ;
     - ⚠ accepté avec réserve : le fichier passe quand même (PDF/DXF/DWG ne sont **jamais bloqués**) — l'extraction vérifiera le contenu réel.
   - Les chemins avec espaces, guillemets ou accolades (format Drag & Drop Windows) sont nettoyés automatiquement.
3. **Cliquez « 🚀 Lancer l'Analyse & Générer le Métré »** : la barre suit le traitement **page par page** (`Page X/N : plan/tableau/ocr`).
4. **Ouvrez les résultats** : boutons d'ouverture directe du classeur et du dossier `output/`.

> Si le plan est inexploitable, aucun classeur vide n'est produit : un message d'erreur explicite s'affiche (ex. *« Échec d'extraction : Aucun élément structural détecté »*).

---

## ⌨️ Utilisation — ligne de commande

```powershell
# Pipeline complet : extraction → métré → optimisation → rapport
.\.venv\Scripts\python.exe main.py --cli --input "reference/PLAN_BA_final.pdf"

# Avec nom de projet et dossier de sortie personnalisés
.\.venv\Scripts\python.exe main.py --cli --input "mon_plan.pdf" --out "C:\Chantiers\ProjetX" --projet-nom "Villa R+2"

# Extraction seule (avec liste brute des blocs lus = preuve d'extraction)
.\.venv\Scripts\python.exe extract_plan.py --input "plan.pdf" --out output/plan_data.json

# Métré seul depuis un JSON existant
.\.venv\Scripts\python.exe build_metre.py --input output/plan_data.json --out output/metre_genere.xlsx

# Modèle vierge standardisé
.\.venv\Scripts\python.exe generators/modele_metre.py --out output/modele_metre_BA.xlsx

# Tests (191 tests)
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

---

## 📐 Modèle Excel standardisé + macros VBA

`generators/modele_metre.py` génère un **classeur modèle 100 % vierge** (aucune donnée projet — seules des constantes normatives et des formules), conforme aux standards BET / bureaux de contrôle :

| Feuille | Contenu |
|---|---|
| `01_Detail_Quantitatif` | Cartouche (N° Marché, Projet, Bâtiment, Date, Établi/Vérifié par) + 3 blocs vierges (Fouilles, Béton propreté, Béton armé) avec `=IF(COUNTA(G:I)>0,F*PRODUCT(G:I),F)` et sous-totaux |
| `02_Armatures` | Décorticage par barre + ventilation T6→T32, longueurs totales, poids nominaux (0,222…6,313 kg/ml), poids partiels, **total kg + tonnes**, taux kg/m³ |
| `03_Attachement_Ferraillage` | Synthèse par type d'ouvrage + poids synthèse |
| `04_GO_Attachement` | Bordereau lié dynamiquement (réalisé `=D-E`, avancement `=E/D`, Qté Marché à saisir) |

Charte « Génie Civil Prestige » (Bleu Nuit `#1B365D`, Bleu Acier `#2E5B88`, Émeraude `#0D9488`), police Segoe UI, formats stricts, **zéro fusion hors cartouche**.

**Macros** (`vba/Module1.bas`, à importer via Développeur → Visual Basic → Fichier → Importer, puis enregistrer en `.xlsm`) :
- `NaviguerVers` (+ raccourcis `AllerDetail/Armatures/Synthese/Bordereau`)
- `VerifierCoherenceMetre` — audit : équilibre acier (tolérance 1 kg), textes/valeurs négatives, MsgBox bilan (béton m³, acier kg/tonnes)
- `ReinitialiserDonneesTemplate` — vide les saisies (formules et mise en page conservées)

---

## 🧠 Comment ça marche (moteur)

```
Plan PDF/DXF/Image
   │  1. VALIDATION (core/validator.py) — mots-clés GC, format, densité vectorielle
   ▼
   │  2. EXTRACTION (core/local_extractor.py — VectorPlanExtractor)
   │     • boucle TOUTES les pages (streaming, ~150 Mo RAM constants)
   │     • classification par page : tableau / plan / autre
   │     • page.find_tables() natif + détecteur textuel universel
   │       (triplets compacts « 90 x 90 x 25 », SF filantes, annotations)
   │     • grille spatiale : bulles d'axes + étiquettes → intersections
   │     • fallback OCR local (RapidOCR/ONNX) si page scannée < 15 mots
   ▼  plan_data.json (+ _meta : avertissements, hypothèses, pages)
   │  3. CALCUL (build_metre.py) → metre_genere.xlsx (formules actives)
   │  4. OPTIMISATION (optimisation_chantiers.py) → calpinage 12 m
   │  5. RAPPORT (rapport_metre.py) → rapport_metre.pdf
```

---

## 🗂️ Formats et conventions de plans lus

**Formats** : PDF vectoriel (1 à 1000+ pages), PDF scanné (OCR local RapidOCR, modèles embarqués), PNG/JPG/TIFF/BMP/WebP, DXF/DWG (moteur ezdxf embarqué).

**Conventions lues** (françaises + marocaines) :
- Semelles : `S4(150x150x40)`, tableaux `Semelles | Dimensions (cm)` avec triplets `90 x 90 x 25` (conversion cm→m auto, seuil 15 cm), semelles filantes `SF 45 x 20 x L`, annotations `S1: Semelle de 90 x 90 x 25`
- Poteaux : `P1..P4` et `Q1..Q4`, sections `(25x30)`, barres `6HA14` / `8T12` / `4T12+4T10`, cadres `Cad T6+Ep` / `2CAD T6 e=15` / `CAD+ETR T6 e=15`, étiquettes couplées `(S1,Q1)` (tolérance OCR `0/O→Q`)
- Poutres : `N` / `BN` / `PN` / `PC` / `LG` / `CH` (+`BIS`), sections `20x30` ou `(25x40)`, filants `3T14`, chapeaux `CHAP.2HA12`, renforts `Renf 2T14 L=2.00m`

**Dossiers validés** : `reference/PLAN_BA_final.pdf` (6 pages → 23 semelles, 629,7 kg d'acier), `reference/PLANS-BOLBOL-GOUMANDEY.pdf` (70 pages → 67 semelles), `reference/ilide.info-plan-ba-r-2.pdf` (R+2 → 17 semelles / 17 poteaux Q1–Q4 / 15 poutres).

---

## ⚠️ Hypothèses et limites connues (transparence)

Quand le plan ne cote pas une donnée, le moteur applique une hypothèse **tracée** (visible console + `_meta` + rapport), jamais silencieuse :

| Donnée absente du plan | Traitement |
|---|---|
| Hauteur des poteaux | Hypothèse 3,00 m (à ajuster selon l'étage) |
| Portées des poutres | Exclues du calpinage/bilan + avertissement (aucune portée inventée) |
| Espacement `e=(10x9 …)` | Lu 0,10 m, marqué « à confirmer » |
| Ferraillage `HA· St=…` des coupes | `nb = ⌊(dim − 2×0,05) / St⌋ + 1`, nappes X/Y supposées identiques |
| Semelle sans dimensions | Conservée avec mention « Dimensions à renseigner », volumes à 0 signalés |

---

## 🛠️ Développement : tests, structure, build

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q   # 191 tests (extraction, calcul, UI, OCR, template)
```

```
metre-ba-agent/
├── main.py                  # Entrée GUI + CLI (pipeline 4 étapes)
├── ui/desktop_app.py        # Interface customtkinter (DnD, pre-flight, progression)
├── core/
│   ├── local_extractor.py   # Moteur vectoriel multi-pages (find_tables + spatial)
│   ├── validator.py         # Pre-flight : score multi-pages, jamais de blocage dur
│   ├── ocr_engine.py        # Fallback OCR paresseux (RapidOCR/ONNX)
│   ├── ingestion.py         # Ingestion DXF/images/raster
│   ├── calculator.py        # Mathématiques béton armé pures (testées)
│   ├── schemas.py           # Modèles Pydantic
│   └── paths.py             # Chemins .exe-proof (jamais de _MEIPASS)
├── build_metre.py           # Classeur métré (formules actives)
├── optimisation_chantiers.py # Calpinage 12 m (aussi generators/excel_optimisation.py)
├── rapport_metre.py         # Rapport PDF (ReportLab)
├── generators/modele_metre.py # Modèle vierge 4 feuilles
├── vba/Module1.bas          # Macros : navigation, audit, réinitialisation
├── build_executable.py      # Packaging PyInstaller --onedir + splash + tkdnd/numpy/OCR
├── assets/splash.png        # Splash screen natif (généré si absent)
├── tests/                   # 191 tests (dont anti-mock et non-régression plans réels)
├── reference/               # Plans + métré de référence (petits fichiers uniquement)
├── config/                  # YAML postes et options
└── output/                  # Livrables générés (régénérables, non versionnés en détail)
```

**Build exe** (`build_executable.py`) : mode `--onedir` (démarrage instantané, pas d'extraction `%TEMP%`), splash natif auto-fermé (`pyi_splash.close()`), Drag & Drop tkdnd embarqué, ezdxf+numpy et RapidOCR embarqués (imports paresseux : le PDF n'active jamais ezdxf).

---

## ❓ Dépannage (FAQ)

| Symptôme | Cause / Solution |
|---|---|
| `ModuleNotFoundError: No module named 'numpy'` à la sélection de fichier | **Corrigé** : `ezdxf` est importé paresseusement (DXF uniquement) et `numpy` est embarqué dans l'exe |
| Splash « Chargement… » figé au premier plan | **Corrigé** : `pyi_splash.close()` après rendu (`app.update()`) + filet `after(200)` ; idem en mode `--cli` |
| « Veuillez sélectionner un fichier d'abord » alors qu'il est affiché | **Corrigé** : source de vérité unique `selected_file_path` + nettoyage `{accolades}`/guillemets/espaces |
| Curseur interdit au glisser-déposer | Utilisez l'exe rebuildé (tkdnd embarqué) ; en source : `pip install tkinterdnd2` |
| Demarrage très lent la 1ʳᵉ fois (OneDrive) | Hydratation des fichiers cloud — un seul passage, ensuite ~1,5 s |
| Scan antivirus à chaque lancement | Normal en `--onefile` ; le build `--onedir` fourni évite l'extraction répétée |
| Classeur avec `0.0 kg dans la norme` | **Impossible** : volume/poids nuls → `⚠ ALERTE : Données manquantes` |
| Plan accepté « avec réserve » puis erreur d'extraction | Comportement voulu : le pré-import ne bloque jamais, l'extraction exige des éléments réels |
| Dossiers `_MEI*` résiduels dans `%TEMP%` | Restes d'anciens builds `--onefile` — supprimables sans risque |

---

## 📄 Licence

MIT — © 2025 Youssef-AMARZOU. Voir [LICENSE](LICENSE).
