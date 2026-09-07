# Compatibilite des plans BA

Le pipeline accepte les PDF vectoriels, raster et hybrides, les images usuelles
(PNG, JPG, TIFF, BMP, WEBP), ainsi que les DXF lorsque leur lecture native est
possible. Les pages sont traitees individuellement : le texte vectoriel est
toujours conserve et l'OCR est ajoute seulement pour les pages contenant des
images ou des zones peu lisibles. Les mots issus des deux sources sont
fusionnes et dedupliques par texte et position.

Les formats A0 et A1 utilisent un rendu adaptatif limite a 135 DPI et une
largeur maximale de 2200 pixels afin d'eviter les gels et les allocations
excessives. Les formats A2 a A4 utilisent le DPI normal, avec la meme limite
de pixels. Un timeout OCR par page permet de continuer le traitement des pages
suivantes.

Les libelles CAO courants sont tokenises lorsqu'ils sont composites, par
exemple `S1/P1`, `S2-P1`, `LG2(30*50)` ou `P1(25x30)6HA14`. Les dimensions et
armatures absentes ne sont pas inventees : une geometrie par defaut peut etre
inscrite uniquement dans un livrable partiel, avec les marqueurs
`dimensions_par_defaut` ou `position_par_defaut` et un avertissement dans
`_meta.avertissements`.

## Limites reelles

- Le DWG n'est pas lu nativement. Il faut le convertir en DXF ou exporter un
  PDF depuis AutoCAD/ODA.
- Un scan trop flou, trop contraste ou protege ne fournit pas de texte OCR
  fiable ; le livrable reste inspectable mais doit etre verifie manuellement.
- Une cote absente ne peut pas etre deduite de facon fiable. Les valeurs par
  defaut sont des placeholders de controle, jamais des mesures de chantier.
- Les chartes proprietaires et symboles non textuels peuvent necessiter une
  correction manuelle des avertissements et hypotheses.
