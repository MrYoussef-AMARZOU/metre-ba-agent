# Rapport de vérification — métré généré

Plan : reference/PLAN_BA_final.pdf
Écarts vs référence : 91 | éléments à contrôler : 48

## Éléments signalés (aucun estimé silencieusement)

- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [3] terrassement — référence (implantation fouilles non cotée)
- [16] gb_perdue_1 — référence (zone DP — non identifiable sur le plan)
- [16] gb_perdue_2 — référence (zone DP — non identifiable sur le plan)
- [16] gb_g_4_5 — référence (assise rangée G)
- [16] gb_g_5_6 — référence (assise rangée G)
- [16] gb_g_6_7 — référence (assise rangée G)
- [16] gb_g_7_8 — référence (assise rangée G)
- [20] poutres_mezzanine_G_2_4_CH1 — le plan suggère un arrêt au poteau G3 (CH1 2-3 + 3-4) ; total identique — segmentation référence reprise
- [20] poutres_mezzanine_5_F_G_N4 — présent sur le plan, absent du métré de référence
- [20] poutres_mezzanine_8_A_C_N3 — axe 8 absent du métré de référence
- [20] poutres_mezzanine_8_C_E_N1 — axe 8 absent du métré de référence
- [20] poutres_mezzanine_8_E_G_N3 — axe 8 absent du métré de référence
- [20] poutres_ph_rdc_A_1_2_N1 — référence : longueur erronée 5.05 au lieu de 2.48
- [20] poutres_ph_rdc_A_6_7_N1 — référence : longueur 0.65 au lieu de 2.65
- [20] poutres_ph_rdc_G_2_3_N1 — longueur référence 7.25/2 (axe 3 non coté) ; géométrie: 3.74
- [20] poutres_ph_rdc_G_3_5_N4 — longueur référence (axe 3 non coté) ; géométrie: 5.89
- [20] poutres_ph_rdc_G_6_7_N1 — référence : longueur 0.65 au lieu de 2.65
- [20] poutres_ph_rdc_1_A_D_N5 — callout '25+5 jumelée' sur le plan ; métré référence compte N=1
- [20] poutres_ph_rdc_1_D_G_N5 — callout '25+5 jumelée' sur le plan ; métré référence compte N=1
- [20] poutres_ph_rdc_3_A_G_N7 — N7 en T 40x90 — décomposition référence : 0.30x0.90 + 0.30x0.80
- [20] poutres_ph_rdc_3_A_G_N7p — second élément du N7 en T
- [20] poutres_ph_rdc_6_A_C_N3 — référence : N4 A-B / N3 B-E / N4 E-G (différent du plan)
- [20] poutres_ph_rdc_6_C_E_N1 — référence : N3 B-E
- [20] poutres_ph_rdc_6_E_G_N3 — référence : N4 E-G
- [20] poutres_ph_rdc_7_A_C_N3 — référence : N4 A-B / N3 B-E / N4 E-G (différent du plan)
- [20] poutres_ph_rdc_7_C_E_N1 — référence : N3 B-E
- [20] poutres_ph_rdc_7_E_G_N3 — référence : N4 E-G
- [20] poutres_ph_rdc_8_A_C_N3 — référence : N4 A-B / N3 B-E / N4 E-G (différent du plan)
- [20] poutres_ph_rdc_8_C_E_N1 — référence : N3 B-E
- [20] poutres_ph_rdc_8_E_G_N3 — référence : N4 E-G
- [20] poutres_ph_rdc_bn_D_1_3 — BN1 30x30 sur le plan ; référence comptée en 0.20x0.20
- [20] poutres_ph_rdc_bn_D_3_5 — BN1 30x30 sur le plan ; référence comptée en 0.20x0.20
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] remblai_add — référence (implantation non cotée)
- [7] rem_forme — référence (déduction forme, non cotée)

## Vérifications automatiques (extract_plan.py)

- {"type": "comptage_semelles", "etiquettes_texte": 23, "boites_vectorielles": 23, "lectures_vision": 23, "ok": true}
- {"type": "semelles_mapping", "assignees_auto": 19, "non_assignees": ["S3", "S3", "S3", "S3"], "divergences_texte_vs_lecture": []}
- {"type": "poteaux", "carres_rouges": 23, "lectures": 23, "ok": true}
- {"type": "massifs_vectoriels", "boxes_19_23pt": 18, "lectures": 3}