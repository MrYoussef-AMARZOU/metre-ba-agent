# Métré BA Agent — plan PDF → métré Excel + rapport PDF + optimisation

Pipeline Python qui lit un **plan de fondations béton armé (PDF)** et produit :

1. **`output/metre_genere.xlsx`** — métré structuré (3 feuilles) :
   - `Detail quantitatif fondation` : postes 1 (études), 3 (terrassement),
     15 (béton de propreté), 16 (gros béton), 17 (maçonnerie de moellons),
     20 (béton armé : semelles, longrines, chaînages, fûts, massifs, poteaux,
     poutres mezzanine + PH-RDC), 7 (remblaiement), 19 (forme en béton) —
     mêmes colonnes que le métré modèle (`N° | Désignation | U | N | Longueur |
     largeur | Hauteur | Qté partielle | Qté Total`), **formules Excel vivantes**
     (`=K*J*I*H`, `=SUM(...)`, références croisées).
   - `Armatures` : ferraillage agrégé par type + détail par élément
     (nappes, cadres, épingles, barres longues) + poids acier par diamètre.
   - `Comparaison` : écarts champ à champ contre le métré de référence.
2. **`output/rapport_metre.pdf`** — rapport avec synthèse quantitative,
     répartition par famille, insights calculés (ratios kg/m³, sensibilité au
     paramètre H/bon sol), écarts documentés et annexe `a_verifier`.
3. **`output/optimisation_bonnes_pratiques.xlsx`** — agrégations d'optimisation
     (barres commerciales 12 m, chutes, regroupements d'éléments identiques)
     + checklist qualité métré.
4. **`output/rapport_verification.md`** — liste des éléments `a_verifier`
     et des vérifications automatiques.

> **Politique zéro-hallucination** : rien n'est estimé en silence. Chaque
> donnée vient du texte natif du PDF, de la géométrie vectorielle ou d'une
> lecture vision sourcée (`config/readings_vision.yaml`) ; tout le reste est
> signalé. Voir [`docs/ZERO_HALLUCINATION.md`](docs/ZERO_HALLUCINATION.md).

---

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation (pipeline complet)

```bash
python extract_plan.py      --pdf reference/PLAN_BA_final.pdf
python build_metre.py       # -> output/metre_genere.xlsx + rapport_verification.md
python build_report.py      # -> output/rapport_metre.pdf
python build_optimisation.py  # -> output/optimisation_bonnes_pratiques.xlsx
```

### Options de lecture

```bash
# Vision via API Claude (ANTHROPIC_API_KEY requis) — relit les pages en image
python extract_plan.py --vision

# OCR local GLM-OCR (zai-org/GLM-OCR, torch + transformers requis)
python extract_plan.py --ocr glm-ocr
```

## Sur un nouveau plan

1. `python extract_plan.py --pdf mon_plan.pdf`
2. Vérifier `output/plan_data.json` (grille d'axes détectée, comptages).
3. Compléter/corriger `config/readings_vision.yaml` (poteaux, tracés,
   poutres — chaque entrée est sourcée) et `config/postes.yaml`
   (géométrie des travées, catalogues, règles de ferraillage).
4. Relancer `build_metre.py` → les quantités se recalculent par formules.

Aucun mapping de poste n'est codé en dur : tout est dans `config/postes.yaml`.

## Architecture

```
plan PDF ──extract_plan.py──► plan_data.json ──┐
                                               ├─build_metre.py─► metre_genere.xlsx
config/postes.yaml ────────────────────────────┘                │
config/readings_vision.yaml                                     ├─► Comparaison (vs référence)
                                                                └─► rapport_verification.md
 metre_genere.xlsx + summary.json ──build_report.py───────► rapport_metre.pdf
 metre_lines.json  + summary.json ──build_optimisation.py─► optimisation_bonnes_pratiques.xlsx
```

| Fichier | Rôle |
|---|---|
| `extract_plan.py` | PDF → JSON : axes (texte natif), étiquettes de semelles (clusters de mots), boîtes/carrés vectoriels, tableau des semelles (p.4), catalogue poutres (p.5), backends `--vision` / `--ocr glm-ocr`, vérifications de cohérence |
| `metre_core.py` | Géométrie de la grille : longueurs d'axes et travées, formules Excel de longueur (`=3.82+0.4+0.82`) |
| `build_metre.py` | JSON + configs → Excel (3 feuilles), comparaison ligne à ligne vs référence, exports JSON |
| `build_report.py` | Rapport PDF (reportlab) : synthèse, répartition, insights, écarts, annexe |
| `build_optimisation.py` | Excel d'optimisation + bonnes pratiques |
| `config/postes.yaml` | Paramètres site (H/bon sol…), géométrie des travées, catalogues (semelles/poteaux/poutres), règles de ferraillage, descriptions de postes |
| `config/readings_vision.yaml` | Lectures des éléments non textuels du plan, **chacune sourcée** (page + note) |
| `reference/` | Plan d'exemple + métré modèle MZINDA |

## Résultats sur le plan d'exemple (MZINDA, Youssoufia)

- 23 semelles (S1×2, S2×1, S3×8, S4×9, S5×3), 23 poteaux (P1×12, P2×5, P3×4,
  P4×2), 19 longrines, 17 chaînages, 3 massifs, poutres mezzanine (31) et
  PH-RDC (36) extraites du plan.
- Terrassement calculé 222,85 m³ = contrôle manuel du métré de référence (N22).
- ~91 écarts champ à champ documentés vs le métré manuel — dont plusieurs
  **erreurs réelles détectées dans le métré manuel** (largeur S5 à F5 1,3 vs
  1,5 ; longrine axe 2 D→G 5,77 vs 5,05 coté au plan ; hauteur S4 à G2 ;
  axes 6/7/8 PH-RDC N4/N3/N4 vs N3/N1/N3 dessinés ; longueurs 0,65 vs 2,65…).

## Limites

- Plans scannés sans texte ni vecteurs : tout passe par le canal vision
  (plus d'`a_verifier`, relecture humaine recommandée).
- Conventions de dessin différentes → ajuster la géométrie dans la config.
- Ferraillage complexe (T, jumelées) : règles paramétrées et signalées.

## Sources & inspirations

Voir [`docs/SOURCES.md`](docs/SOURCES.md) (GLM-OCR, opentakeoff, OpenConstructionERP,
DDC Skills, ConRebSeg, datasets armatures, papiers associés).
