# Structure dataset — ajouter vos plans ici
#
# Chaque exemple suit le même schéma :
#   dataset/examples/<nom_projet>/
#     input/
#       plan.pdf              # le plan BA (PDF)
#       notes.txt             # (optionnel) notes du métreur, paramètres site
#     output_reference/
#       metre_reference.xlsx  # le métré de référence (format MZINDA ou similaire)
#       rapport_reference.pdf # (optionnel) rapport de métré de référence
#
# Pour traiter un exemple :
#   python run_batch.py --example dataset/examples/001_MZINDA_Youssoufia
#
# Pour traiter tous les exemples :
#   python run_batch.py --all
#
# Le pipeline compare systématiquement la sortie générée avec la référence
# et produit un rapport d'écarts (feuille "Comparaison" + rapport PDF).
