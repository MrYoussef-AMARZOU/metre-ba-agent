from pathlib import Path
import openpyxl

def set_cell_safe(ws, row: int, col: int, value):
    cell = ws.cell(row, col)
    if type(cell).__name__ == "MergedCell":
        for rng in ws.merged_cells.ranges:
            if rng.min_row <= row <= rng.max_row and rng.min_col <= col <= rng.max_col:
                ws.cell(rng.min_row, rng.min_col).value = value
                return
    else:
        cell.value = value

def injecter_metre_dans_modele(plan_data: dict, template_path: str, output_path: str):
    wb = openpyxl.load_workbook(template_path)
    semelles = plan_data.get("semelles", [])
    nom_projet = plan_data.get("projet", "Projet BTP")
    
    # -------------------------------------------------------------
    # FEUILLE 1 : 01_Detail_Quantitatif
    # -------------------------------------------------------------
    ws1 = wb["01_Detail_Quantitatif"]
    
    # Cartouche
    for r in range(1, 6):
        for c in range(1, ws1.max_column + 1):
            if "projet" in str(ws1.cell(r, c).value or "").lower():
                set_cell_safe(ws1, r, c + 1, nom_projet)
                break

    for idx, s in enumerate(semelles):
        a = float(s.get("a", 1.0))
        b = float(s.get("b", 1.0))
        h = float(s.get("h", 0.3))
        axe = s.get("axe", "")
        file_ = s.get("file", "")
        nom = f"Semelle {s.get('type', 'S')}"
        
        # 1. Fouilles (Article 1, démarre ligne 9)
        r_f = 9 + idx
        set_cell_safe(ws1, r_f, 2, axe)
        set_cell_safe(ws1, r_f, 3, file_)
        set_cell_safe(ws1, r_f, 4, f"Fouille {nom}")
        set_cell_safe(ws1, r_f, 5, "M3")
        set_cell_safe(ws1, r_f, 6, 1)
        set_cell_safe(ws1, r_f, 7, a + 0.20)  # Débord fouille +10cm de chaque côté
        set_cell_safe(ws1, r_f, 8, b + 0.20)
        set_cell_safe(ws1, r_f, 9, 1.20)      # Profondeur bon sol
        
        # 2. Béton de propreté (Article 2, démarre ligne 21)
        r_p = 21 + idx
        set_cell_safe(ws1, r_p, 2, axe)
        set_cell_safe(ws1, r_p, 3, file_)
        set_cell_safe(ws1, r_p, 4, f"BP {nom}")
        set_cell_safe(ws1, r_p, 5, "M3")
        set_cell_safe(ws1, r_p, 6, 1)
        set_cell_safe(ws1, r_p, 7, a + 0.10)
        set_cell_safe(ws1, r_p, 8, b + 0.10)
        set_cell_safe(ws1, r_p, 9, 0.10)      # Épaisseur 10 cm
        
        # 3. Béton Armé en Fondation (Article 3, démarre ligne 33)
        r_ba = 33 + idx
        set_cell_safe(ws1, r_ba, 2, axe)
        set_cell_safe(ws1, r_ba, 3, file_)
        set_cell_safe(ws1, r_ba, 4, nom)
        set_cell_safe(ws1, r_ba, 5, "M3")
        set_cell_safe(ws1, r_ba, 6, 1)
        set_cell_safe(ws1, r_ba, 7, a)
        set_cell_safe(ws1, r_ba, 8, b)
        set_cell_safe(ws1, r_ba, 9, h)

    # -------------------------------------------------------------
    # FEUILLE 2 : 02_Armatures
    # -------------------------------------------------------------
    ws2 = wb["02_Armatures"]
    diametres = [6, 8, 10, 12, 14, 16, 20, 25, 32]
    r_arm = 4
    
    for s in semelles:
        label = s.get("type", "S1")
        a = float(s.get("a", 1.0))
        b = float(s.get("b", 1.0))
        h = float(s.get("h", 0.3))
        phi = int(s.get("phi", 12))
        nb_x = int(s.get("nb_x", 8))
        nb_y = int(s.get("nb_y", 8))
        
        # Lit X
        set_cell_safe(ws2, r_arm, 1, f"{label} - Nappe INF X")
        set_cell_safe(ws2, r_arm, 2, s.get("axe", ""))
        set_cell_safe(ws2, r_arm, 3, s.get("file", ""))
        set_cell_safe(ws2, r_arm, 4, a)
        set_cell_safe(ws2, r_arm, 5, b)
        set_cell_safe(ws2, r_arm, 6, h)
        set_cell_safe(ws2, r_arm, 7, 1)
        set_cell_safe(ws2, r_arm, 8, nb_x)
        set_cell_safe(ws2, r_arm, 9, phi)
        set_cell_safe(ws2, r_arm, 10, f"=(E{r_arm}-0.05)+34*I{r_arm}/1000")
        for col_idx, d in enumerate(diametres, 11):
            set_cell_safe(ws2, r_arm, col_idx, f'=IF($I{r_arm}={d}, $G{r_arm}*$H{r_arm}*$J{r_arm}, "")')
        r_arm += 1
        
        # Lit Y
        set_cell_safe(ws2, r_arm, 1, f"{label} - Nappe INF Y")
        set_cell_safe(ws2, r_arm, 2, s.get("axe", ""))
        set_cell_safe(ws2, r_arm, 3, s.get("file", ""))
        set_cell_safe(ws2, r_arm, 4, a)
        set_cell_safe(ws2, r_arm, 5, b)
        set_cell_safe(ws2, r_arm, 6, h)
        set_cell_safe(ws2, r_arm, 7, 1)
        set_cell_safe(ws2, r_arm, 8, nb_y)
        set_cell_safe(ws2, r_arm, 9, phi)
        set_cell_safe(ws2, r_arm, 10, f"=(D{r_arm}-0.05)+34*I{r_arm}/1000")
        for col_idx, d in enumerate(diametres, 11):
            set_cell_safe(ws2, r_arm, col_idx, f'=IF($I{r_arm}={d}, $G{r_arm}*$H{r_arm}*$J{r_arm}, "")')
        r_arm += 1

    # Renseigner le volume béton de référence en K26 pour le ratio kg/m³
    set_cell_safe(ws2, 26, 11, "='01_Detail_Quantitatif'!K41")

    # -------------------------------------------------------------
    # FEUILLE 3 : 03_Attachement_Ferraillage (Synthèse)
    # -------------------------------------------------------------
    ws3 = wb["03_Attachement_Ferraillage"]
    r_syn = 4
    for s in semelles:
        label = s.get("type", "S1")
        phi = int(s.get("phi", 12))
        nb_x = int(s.get("nb_x", 8))
        a = float(s.get("a", 1.0))
        long_u = round((a - 0.05) + 34 * phi / 1000, 3)
        
        set_cell_safe(ws3, r_syn, 1, f"Semelle {label}")
        set_cell_safe(ws3, r_syn, 2, "Lit INF X & Y")
        set_cell_safe(ws3, r_syn, 3, 1)          # Nb d'ouvrages
        set_cell_safe(ws3, r_syn, 4, nb_x * 2)   # Barres totales
        set_cell_safe(ws3, r_syn, 5, phi)
        set_cell_safe(ws3, r_syn, 6, long_u)
        r_syn += 1

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"✅ Métré 4 feuilles complet généré : {output_path}")

if __name__ == "__main__":
    sample_data = {
        "projet": "Projet R+2 Maroc",
        "semelles": [
            {"type": "S1", "axe": "A", "file": "1", "a": 1.2, "b": 1.2, "h": 0.3, "phi": 12, "nb_x": 8, "nb_y": 8},
            {"type": "S2", "axe": "B", "file": "2", "a": 1.5, "b": 1.5, "h": 0.4, "phi": 12, "nb_x": 10, "nb_y": 10}
        ]
    }
    injecter_metre_dans_modele(sample_data, "output/modele_metre_BA.xlsx", "output/test_metre_complet.xlsx")
