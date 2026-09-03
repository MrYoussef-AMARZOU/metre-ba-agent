# Protocole zéro-hallucination

Objectif : pouvoir fournir **n'importe quel plan BA** et obtenir un métré dont
chaque quantité est traçable — sans invention, sans estimation silencieuse.

## Principe fondamental

> Un modèle (OCR, vision, LLM) peut se tromper. Le pipeline est donc conçu pour
> que **rien ne passe en silence** : toute donnée non certaine est marquée
> `a_verifier` et listée dans `output/rapport_verification.md` + annexe du PDF.

## Les trois canaux de lecture et leurs garanties

| Canal | Ce qu'il lit | Fiabilité | Rôle |
|---|---|---|---|
| **Texte natif** (pdfplumber) | Axes, étiquettes `S3(120x120x30)`, tableau des semelles, catalogue poutres | Élevée (c'est le texte du plan lui-même) | Source primaire des repères et cotes |
| **Vecteurs** (PyMuPDF) | Boîtes de semelles, carrés rouges des poteaux, massifs | Élevée (géométrie exacte) | Vérification par comptage (23 semelles = 23 carrés = 23 lectures) |
| **Vision / OCR** (readings_vision.yaml, API Claude, GLM-OCR) | Types de poteaux, tracés CH/LG, poutres des niveaux, annexes | Moyenne (lecture d'image) | Source primaire pour le non-textuel, **toujours sourcée et datée** |

## Règles appliquées par le code

1. **Aucun remplissage d'angle mort.** Si une donnée n'est ni dans le texte,
   ni dans les vecteurs, ni dans une lecture sourcée, elle n'existe pas : la
   ligne est absente, pas « approximée ».
2. **Recoupement obligatoire.** `extract_plan.py` vérifie :
   comptage étiquettes texte = boîtes vectorielles = lectures vision ;
   mapping automatique vs lecture manuelle ; carrés rouges vs poteaux lus.
3. **Toute cote absente du plan est signalée.** Exemple réel : l'axe 3 n'est
   pas coté entre les axes 2 et 4 → les longueurs concernées portent une note
   et reprennent la valeur de référence à faire confirmer.
4. **Formules vivantes.** Le classeur généré ne contient pas de quantités
   figées : `L = K*J*I*H`, `total = SUM(...)`, références croisées
   (`N34 = M33+M55+M75`). On peut auditer chaque cellule.
5. **Traçabilité de source.** Chaque ligne du registre porte sa provenance :
   `plan (texte natif)`, `plan (lecture vision)`, `référence (non coté au plan)`,
   `tableau p.4`… Elle alimente la colonne Commentaire et le rapport.
6. **Comparaison à la référence.** Quand un métré de référence existe, la
   feuille « Comparaison » liste champ à champ (longueur, largeur, hauteur, N,
   Qté) chaque écart, avec sa note d'explication. La référence n'écrase jamais
   la lecture du plan : elle sert de contre-expertise.

## Ce que « 0 erreur » veut dire ici

L'objectif opérationnel est : **zéro écart silencieux entre le plan et le
métré produit**. Le pipeline ne promet pas que la première lecture d'un plan
inconnu soit parfaite — il garantit que :
- tout ce qui est produit est justifiable (source citée) ;
- tout ce qui est douteux est remonté (`a_verifier`) ;
- la correction se fait en éditant `config/readings_vision.yaml` (une ligne par
  lecture), puis en relançant `build_metre.py` — sans toucher au code.

## Limites connues (assumées)

- Les plans scannés (image pure, sans texte ni vecteurs) basculent
  entièrement sur le canal vision → plus d'`a_verifier`.
- Les conventions de dessin varient (certains bureaux ne numérotent pas les
  axes de la même façon) → adapter `config/postes.yaml` (géométrie).
- Le ferraillage complexe (sections en T, jumelées) suit des règles de métreur
  ; elles sont paramétrées dans la config et signalées.
