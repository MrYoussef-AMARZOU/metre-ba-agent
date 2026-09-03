# Sources, outils et références du projet

Chaque source est listée avec la façon dont elle est utilisée ici. Rien n'est
copié aveuglément : les repos clonés (dossier `research/`, non versionné)
servent de référence d'architecture et de méthodes.

## Moteurs d'extraction

| Source | Usage dans ce projet |
|---|---|
| [GLM-OCR (zai-org)](https://huggingface.co/zai-org/GLM-OCR) | Backend OCR local optionnel (`extract_plan.py --ocr glm-ocr`). Modèle multimodal 0.9B (MIT) — mode « information extraction » avec schéma JSON strict : le modèle doit laisser vide ce qui est illisible (politique zéro-hallucination). Intégration via `transformers.AutoModelForImageTextToText`. |
| API Claude (anthropic SDK) | Backend vision optionnel (`extract_plan.py --vision`) : relecture des pages rendues en image avec obligation de marquer `a_verifier` plutôt que de deviner. |
| pdfplumber / PyMuPDF | Cœur de l'extraction : texte natif (axes, étiquettes de semelles, tableau des semelles p.4, catalogue poutres p.5) et dessins vectoriels (boîtes de semelles, carrés rouges des poteaux, massifs). |

## Repos de référence (clonés dans `research/`)

| Repo | Ce qu'on en retient |
|---|---|
| [Kentucky-ai/opentakeoff](https://github.com/Kentucky-ai/opentakeoff) (Apache-2.0) | Architecture « PDF takeoff » piloté par agent : découpage plan→moteur→quantités, outillage MCP, jeux d'évaluation (evals). |
| [datadrivenconstruction/OpenConstructionERP](https://github.com/datadrivenconstruction/OpenConstructionERP) (AGPL-3.0) | Référence de structure BOQ/métré multi-postes et de catalogues régionaux ; aucune réutilisation de code (AGPL), inspiration de format seulement. |
| [datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction](https://github.com/datadrivenconstruction/DDC_Skills_for_AI_Agents_in_Construction) | Catalogue de compétences IA construction (221 skills) — modèle de découpage des tâches métré/BIM/cost. |
| [LordHarsh/layerwise.ai](https://github.com/LordHarsh/layerwise.ai) | Exemple d'API Python + frontend pour pipeline documentaire. |
| [DTU-PAS/ConRebSeg](https://github.com/DTU-PAS/ConRebSeg) + [dataset](https://data.dtu.dk/articles/dataset/Self-collected_sequences_and_metadata_of_ConRebSeg/26213762) | Dataset de segmentation de ferraillage — perspective pour la lecture photo/scan d'armatures (hors périmètre v1). |
| [whiesty/synthetic-datasets-for-rebar](https://github.com/whiesty/synthetic-datasets-for-rebar) | Génération de datasets synthétiques d'armatures (entraînement futur de détecteurs). |
| [Armin1337/RebarDSC](https://github.com/Armin1337/RebarDSC) | Détection/comptage d'armatures. |

## Papiers & articles

- [Frontiers in Built Environment (2026) — AI in construction takeoff](https://www.frontiersin.org/journals/built-environment/articles/10.3389/fbuil.2026.1839808/full)
- [Automation in Construction — LLM/vision pour l'extraction de plans](https://www.sciencedirect.com/science/article/abs/pii/S0926580524006897)
- [Data in Brief — dataset armatures](https://www.sciencedirect.com/science/article/pii/S2666165924000644)
- GLM-OCR Technical Report : <https://arxiv.org/abs/2603.10910>
- ConRebSeg : <https://github.com/DTU-PAS/ConRebSeg>

## Note sur la cible « 0 erreur, 0 hallucination »

Aucun extracteur (OCR, LLM de vision) n'est fiable à 100 % sur un plan quelconque.
La garantie de ce projet n'est pas « le modèle ne se trompe jamais » mais
« **rien ne passe en silence** » :

1. trois canaux indépendants (texte natif, géométrie vectorielle, lecture vision
   sourcée) sont recoupés ;
2. tout désaccord ou absence de cote produit un `a_verifier` explicite dans le
   rapport et le PDF ;
3. les quantités sont des formules Excel vivantes (`=K*J*I*H`, `=SUM(...)`),
   vérifiables cellule par cellule ;
4. une feuille « Comparaison » liste champ à champ les écarts avec un métré de
   référence quand il en existe un.

Voir `docs/ZERO_HALLUCINATION.md` pour le détail du protocole.
