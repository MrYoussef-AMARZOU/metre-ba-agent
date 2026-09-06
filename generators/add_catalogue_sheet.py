from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def injecter_catalogue_standard(wb):
    sheet_name = "05_Catalogue_Armatures_Standard"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]
        
    ws = wb.create_sheet(sheet_name)
    ws.views.sheetView[0].showGridLines = True

    # --- Palette "Génie Civil Prestige" ---
    NAVY = "1B365D"
    STEEL = "2E5B88"
    LIGHT_SUB = "E2E8F0"
    BORDER_COLOR = "D1D5DB"

    font_title = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
    font_sec = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_tbl_head = Font(name="Segoe UI", size=10, bold=True, color="1B365D")
    font_body = Font(name="Segoe UI", size=10)

    fill_navy = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
    fill_steel = PatternFill(start_color=STEEL, end_color=STEEL, fill_type="solid")
    fill_sub = PatternFill(start_color=LIGHT_SUB, end_color=LIGHT_SUB, fill_type="solid")

    thin = Side(style="thin", color=BORDER_COLOR)
    border_cell = Border(left=thin, right=thin, top=thin, bottom=thin)

    align_c = Alignment(horizontal="center", vertical="center")
    align_l = Alignment(horizontal="left", vertical="center")
    align_r = Alignment(horizontal="right", vertical="center")

    # --- Cartouche de Titre Principal (Lignes 1-2) ---
    ws.merge_cells("A1:K1")
    ws["A1"] = "RÉFÉRENTIEL TECHNIQUE — CATALOGUE DES ARMATURES STANDARDISÉES (FIMUREX / EUROCODE 2)"
    ws["A1"].font = font_title
    ws["A1"].fill = fill_navy
    ws["A1"].alignment = align_c

    ws.merge_cells("A2:K2")
    ws["A2"] = "Abaques de dimensionnement, sections d'acier, charges admissibles et nomenclatures de chantier"
    ws["A2"].font = Font(name="Segoe UI", size=10, italic=True, color="FFFFFF")
    ws["A2"].fill = fill_steel
    ws["A2"].alignment = align_c

    current_row = 4

    def add_section_header(title):
        nonlocal current_row
        ws.cell(current_row, 1, title)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=11)
        c = ws.cell(current_row, 1)
        c.font = font_sec
        c.fill = fill_steel
        c.alignment = align_l
        current_row += 1

    def add_table(headers, data, col_aligns=None):
        nonlocal current_row
        # En-têtes de colonnes
        for c_idx, h in enumerate(headers, 1):
            cell = ws.cell(current_row, c_idx, h)
            cell.font = font_tbl_head
            cell.fill = fill_sub
            cell.alignment = align_c
            cell.border = border_cell
        current_row += 1
        
        # Données
        for r_data in data:
            for c_idx, val in enumerate(r_data, 1):
                cell = ws.cell(current_row, c_idx, val)
                cell.font = font_body
                cell.border = border_cell
                cell.alignment = col_aligns[c_idx - 1] if col_aligns else align_c
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    cell.number_format = "#,##0" if isinstance(val, int) or val > 100 else "0.00"
            current_row += 1
        current_row += 1

    # =========================================================================
    # 1. POTEAUX PRÉFABRIQUÉS STANDARD (PN)
    # =========================================================================
    add_section_header("1. POTEAUX PRÉFABRIQUÉS STANDARD (FIMUREX PN - 4 ET 6 FILANTS, H <= 2.80 m)")
    headers_pot = ["Réf. Armature", "Type", "Section Béton (cm)", "Aciers Filants", "Cadres / Espac.", "Pser Intérieur (daN)", "Pser Extérieur (daN)", "Pser Int. (kN)", "Pser Ext. (kN)", "Attente PA", "Domaine / Norme"]
    data_pot = [
        ["PN4108X8", "Type I", "15 x 15", "4 HA 10", "HA 5 e=15", 11780, 19500, 117.8, 195.0, "PA4108X8", "Eurocode 2 / Non sismique"],
        ["PN41010X10", "Type I", "15 x 15", "4 HA 10", "HA 5 e=15", 11840, 25650, 118.4, 256.5, "PA41010X10", "Eurocode 2 / Non sismique"],
        ["PN41015X15", "Type I", "20 x 20", "4 HA 10", "HA 5 e=15", 25810, 45180, 258.1, 451.8, "PA1015X15", "Eurocode 2 / Non sismique"],
        ["PN41020X20", "Type I", "25 x 25", "4 HA 10", "HA 5 e=15", 45320, 70840, 453.2, 708.4, "PA1015X15", "Eurocode 2 / Non sismique"],
        ["P6N41025X25", "Type I", "30 x 30", "4 HA 10", "HA 5 e=15", 70960, 97560, 709.6, 975.6, "Sur mesure", "Eurocode 2 / Non sismique"],
        ["PN41010X20", "Type I", "15 x 25", "4 HA 10", "HA 5 e=15", 17770, 36470, 177.7, 364.7, "PA41010X10", "Eurocode 2 / Section rect."],
        ["PN41015X20", "Type I", "20 x 25", "4 HA 10", "HA 5 e=15", 31210, 53230, 312.1, 532.3, "PA1015X15", "Eurocode 2 / Section rect."],
        ["P6N61015X30", "Type III", "20 x 35", "6 HA 10", "HA 5 e=15", 42010, 69330, 420.1, 693.3, "PA661010X25", "Eurocode 2 / 6 filants"],
        ["P6N61015X40", "Type III", "20 x 45", "6 HA 10", "HA 5 e=15", 52820, 85430, 528.2, 854.3, "PA661010X35", "Eurocode 2 / 6 filants"],
    ]
    aligns_pot = [align_c, align_c, align_c, align_c, align_c, align_r, align_r, align_r, align_r, align_c, align_l]
    add_table(headers_pot, data_pot, aligns_pot)

    # =========================================================================
    # 2. SEMELLES ISOLÉES SOUS POTEAUX (SIC)
    # =========================================================================
    add_section_header("2. SEMELLES ISOLÉES SOUS POTEAUX (FIMUREX SIC CARRÉES)")
    headers_sem = ["Réf. Armature", "Section AxAxH (cm)", "Pser à 1.0 bar (daN)", "Pser à 1.5 bar (daN)", "Pser à 2.0 bars (daN)", "Pser 1.5b (kN)", "Nappes Inf. X", "Nappes Inf. Y", "Crochets (e cm)", "Abouts (cm)", "Enrobage (cm)"]
    data_sem = [
        ["SIC4655 / 4855", "65 x 65 x 20", 4230, 6340, 8450, 63.4, "4 HA 8", "4 HA 8", "e = 15", 5, 5],
        ["SIC5775", "85 x 85 x 25", 7230, 10840, 14450, 108.4, "5 HA 8", "5 HA 8", "e = 15", 5, 5],
        ["SIC6895", "105 x 105 x 30", 11030, 16540, 22050, 165.4, "6 HA 8", "6 HA 8", "e = 15", 5, 5],
        ["SIC610115", "125 x 125 x 35", 15630, 23440, 31250, 234.4, "6 HA 10", "6 HA 10", "e = 15", 5, 5],
        ["SIC710135", "145 x 145 x 40", 21030, 31540, 38090, 315.4, "7 HA 10", "7 HA 10", "e = 15", 5, 5],
    ]
    aligns_sem = [align_c, align_c, align_r, align_r, align_r, align_r, align_c, align_c, align_c, align_c, align_c]
    add_table(headers_sem, data_sem, aligns_sem)

    # =========================================================================
    # 3. SEMELLES FILANTES (PLATES & RENFORCÉES)
    # =========================================================================
    add_section_header("3. SEMELLES FILANTES PLATES & RENFORCÉES (FIMUREX S / F / FM - Lg = 6.00 m)")
    headers_fil = ["Réf. Armature", "Type Ouvrage", "Largeur (cm)", "Hauteur (cm)", "Aciers Filants", "Armatures Transv.", "Espac. (cm)", "Nuance Acier", "Conditionnement", "Usage Sol Recommandé", "Conformité"]
    data_fil = [
        ["S3835", "Semelle plate", 35, 5, "3 HA 8", "Crochets HA 5", "e = 30", "B500A / B500B", "48 unités", "Sol homogène sans tassement", "EC2 / FD P18-717"],
        ["S31040", "Semelle plate", 40, 5, "3 HA 10", "Crochets HA 5", "e = 30", "B500A / B500B", "48 unités", "Sol homogène standard", "EC2 / FD P18-717"],
        ["S41050", "Semelle plate", 50, 5, "4 HA 10", "Crochets HA 5", "e = 30", "B500A / B500B", "48 unités", "Murs porteurs lourds", "EC2 / FD P18-717"],
        ["F6835X15", "Semelle renforcée", 35, 15, "6 HA 8 (2 nappes)", "Cadres HA 5", "e = 30", "B500B", "8 unités", "Faibles tassements diff.", "EC2 / FD P18-717"],
        ["F6835X20", "Semelle renforcée", 35, 20, "6 HA 8 (2 nappes)", "Cadres HA 5", "e = 30", "B500B", "6 unités", "Faibles tassements diff.", "EC2 / FD P18-717"],
        ["FM61035X20", "Semelle renforcée", 35, 20, "6 HA 10 (2 nappes)", "Cadres HA 5", "e = 25", "B500B", "6 unités", "Charges élevées", "EC2 / FD P18-717"],
        ["FM612140X20", "Semelle renforcée", 40, 20, "4 HA 12 + 2 HA 10", "Cadres HA 5", "e = 25", "B500B", "6 unités", "Rigidité renforcée", "EC2 / FD P18-717"],
    ]
    aligns_fil = [align_c, align_c, align_c, align_c, align_c, align_c, align_c, align_c, align_c, align_l, align_c]
    add_table(headers_fil, data_fil, aligns_fil)

    # =========================================================================
    # 4. CHAÎNAGES & RÈGLES SISMIQUES (DTU 20.1 & CPMI EC8)
    # =========================================================================
    add_section_header("4. CHAÎNAGES HORIZONTAUX & VERTICAUX (DTU 20.1 & ZONE SISMIQUE Z1 À Z4)")
    headers_ch = ["Réf. Armature", "Zone Sismique", "Section Béton (cm)", "Aciers Filants", "Section An (cm²)", "Armat. Transversales", "Espac. (cm)", "Fermeture Cadres", "Positionnement Nœud", "Application", "Règle Normative"]
    data_ch = [
        ["CH2104X10", "Z1 - Z2 (Très faible / Faible)", "15 x 20", "2 HA 10", 1.57, "Épingles Ø 4", "e = 30 à 50", "Libre", "-", "Chaînage horizontal / pignon", "DTU 20.1 (An >= 1.50 cm²)"],
        ["CH4710X10", "Z1 - Z2 (Très faible / Faible)", "15 x 15", "4 HA 7", 1.54, "Cadres Ø 4", "e = 30 à 40", "Libre", "-", "Chaînage horizontal / vertical", "DTU 20.1 (An >= 1.50 cm²)"],
        ["CH4815X15", "Z1 - Z2 (Très faible / Faible)", "20 x 20", "4 HA 8", 2.01, "Cadres Ø 4", "e = 30 à 40", "Libre", "-", "Chaînage niveaux courants", "DTU 20.1 (An >= 1.50 cm²)"],
        ["CHR41010X10", "Z1 - Z2 (Très faible / Faible)", "20 x 20", "4 HA 10", 3.14, "Cadres HA 5", "e = 20", "135° ou soudé", "-", "Planchers-terrasses", "DTU 20.1 (An >= 3.08 cm²)"],
        ["CS108X8", "Z3 - Z4 (Modérée / Moyenne)", "15 x 15 min", "4 HA 10", 3.14, "Cadres HA 5", "e = 15", "Crochets 135°", "1er cadre à <= 7.5 cm", "Chaînage vert. / horiz. sismique", "CPMI EC8 / EC8-1"],
        ["CS1210X10", "Z3 - Z4 (Modérée / Moyenne)", "20 x 20 min", "4 HA 12", 4.52, "Cadres HA 5", "e = 15", "Crochets 135°", "1er cadre à <= 7.5 cm", "Chaînage vert. / horiz. sismique", "CPMI EC8 / EC8-1"],
        ["ATCS108X8", "Z3 - Z4 (Modérée / Moyenne)", "15 x 15 min", "4 HA 10", 3.14, "Cadres HA 5", "25-4x15-85", "Crochets 135°", "Recouvrement >= 60 cm", "Attente soubassement sismique", "CPMI EC8 (HA10 >= 60 cm)"],
        ["ATCS128X8", "Z3 - Z4 (Modérée / Moyenne)", "15 x 15 min", "4 HA 12", 4.52, "Cadres HA 5", "25-4x15-105", "Crochets 135°", "Recouvrement >= 72 cm", "Attente soubassement sismique", "CPMI EC8 (HA12 >= 72 cm)"],
    ]
    aligns_ch = [align_c, align_c, align_c, align_c, align_r, align_c, align_c, align_c, align_c, align_l, align_l]
    add_table(headers_ch, data_ch, aligns_ch)

    # =========================================================================
    # 5. POUTRES MANUPORTABLES (VULCAIN & DEMETER)
    # =========================================================================
    add_section_header("5. POUTRES À HAUTE RÉSISTANCE MANUPORTABLES (FIMUREX VULCAIN & DEMETER)")
    headers_pt = ["Réf. Poutre", "Famille", "Portée Franchie (cm)", "Portée Réf. (cm)", "Section Béton BxH", "Plancher Façade (m)", "Plancher Refend (m)", "Pser Admissible (daN/m)", "Pser Appuis (daN)", "Ancrage Mini", "Flèche Admissible"]
    data_pt = [
        ["V25012X20", "Vulcain (Refend)", "160 à 210", 200, "20 x 25", 2.5, 7.4, 2670, 2670, "13 cm mini", "L/500 (FD P18-717)"],
        ["V35012X25", "Vulcain (Refend)", "260 à 310", 300, "20 x 30", 3.6, 7.3, 2650, 3980, "13 cm mini", "L/500 (FD P18-717)"],
        ["V45012X35", "Vulcain (Refend)", "360 à 410", 400, "20 x 40", 4.1, 8.6, 3150, 6300, "13 cm mini", "L/500 (FD P18-717)"],
        ["V55012X40", "Vulcain (Refend)", "460 à 510", 500, "20 x 45", 3.6, 8.2, 3040, 7600, "13 cm mini", "L/500 (FD P18-717)"],
        ["D35014X30", "Demeter (Fortes charges)", "260 à 310", 300, "20 x 35", 11.2, 14.8, 5190, 7790, "18 cm mini", "L/500 (FD P18-717)"],
        ["D45014X35", "Demeter (Fortes charges)", "360 à 410", 400, "20 x 40", 9.0, 12.9, 4570, 9140, "18 cm mini", "L/500 (FD P18-717)"],
        ["D55014X45", "Demeter (Fortes charges)", "460 à 510", 500, "20 x 50", 8.6, 12.5, 4500, 11250, "18 cm mini", "L/500 (FD P18-717)"],
        ["D65014X50", "Demeter (Fortes charges)", "560 à 610", 600, "20 x 55", 6.6, 10.8, 3940, 11820, "18 cm mini", "L/500 (FD P18-717)"],
    ]
    aligns_pt = [align_c, align_c, align_c, align_c, align_c, align_r, align_r, align_r, align_r, align_c, align_l]
    add_table(headers_pt, data_pt, aligns_pt)

    # =========================================================================
    # 6. TREILLIS SOUDÉS ADETS & LIAISONS
    # =========================================================================
    add_section_header("6. TREILLIS SOUDÉS ADETS & ACCESSOIRES DE LIAISON / CONTINUITÉ")
    headers_acc = ["Réf. Composant", "Catégorie", "Dimensions / Format", "Aciers / Diamètre", "Maille (cm)", "Poids Unitaire", "Nuance Acier", "Norme / Certificat", "Rôle Structurel", "-", "-"]
    data_acc = [
        ["ST15C", "Treillis ADETS", "Panneau 4.00 x 2.40 m", "Filants HA 6 + HA 6", "20 x 20", "2.22 kg/m²", "B500A / B500B", "NF AFCAB / ADETS", "Dallage & compression", "", ""],
        ["ST25C", "Treillis ADETS", "Panneau 6.00 x 2.40 m", "Filants HA 7 + HA 7", "15 x 15", "4.02 kg/m²", "B500B", "NF AFCAB / ADETS", "Structure dalle BA", "", ""],
        ["ST50C", "Treillis ADETS", "Panneau 6.00 x 2.40 m", "Filants HA 8 + HA 8", "10 x 10", "7.90 kg/m²", "B500B", "NF AFCAB / ADETS", "Radiers et dalles fortes", "", ""],
        ["EQ1060", "Équerre de liaison", "Branches 60 x 60 cm", "Barre HA 10", "-", "0.617 kg/ml", "B500B", "Eurocode 2", "Liaisons d'angles chaînages", "", ""],
        ["EQ1270", "Équerre de liaison", "Branches 70 x 70 cm", "Barre HA 12", "-", "0.888 kg/ml", "B500B", "Eurocode 2", "Liaisons d'angles semelles", "", ""],
        ["CD12200", "Chapeau de continuité", "Longueur 2.00 m", "Barre HA 12", "-", "0.888 kg/ml", "B500B", "Eurocode 2", "Continuité poutrelles plancher", "", ""],
        ["NOVABOX N48CX50", "Boîte d'attente", "Profil 0.80 m (recouv. 50 cm)", "Barres HA 8 (e=200)", "-", "Standard", "B500B", "AFCAB R15/008", "Reprise de coulage voiles/dalles", "", ""],
    ]
    aligns_acc = [align_c, align_c, align_c, align_c, align_c, align_c, align_c, align_c, align_l, align_c, align_c]
    add_table(headers_acc, data_acc, aligns_acc)

    # Calibrage explicite des largeurs de colonnes
    col_widths = {
        "A": 18, "B": 18, "C": 22, "D": 22, "E": 20,
        "F": 20, "G": 20, "H": 18, "I": 18, "J": 26, "K": 30
    }
    for col_let, w in col_widths.items():
        ws.column_dimensions[col_let].width = w

if __name__ == "__main__":
    target = Path("output/modele_metre_BA.xlsx")
    if target.exists():
        wb = openpyxl.load_workbook(target)
        injecter_catalogue_standard(wb)
        wb.save(target)
        print(f"✅ Feuille '05_Catalogue_Armatures_Standard' ajoutée avec succès dans : {target}")
    else:
        print(f"❌ Le fichier cible {target} est introuvable.")
