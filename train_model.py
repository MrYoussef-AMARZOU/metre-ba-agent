#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_model.py — Entraîne un modèle d'extraction de métré BA à partir du dataset.

Supporte:
1. Dataset local (dataset/examples/...)
2. Dataset Kaggle (RC_Foundations_PreviewPack_V1)

Usage:
  python train_model.py --all
  python train_model.py --kaggle dataset/kaggle/RC_Foundations_PreviewPack_V1
  python train_model.py --example dataset/examples/001_MZINDA_Youssoufia
"""
import argparse, csv, json, os, re, sys
from pathlib import Path
import pdfplumber
import fitz

sys.stdout.reconfigure(encoding="utf-8")


# ============================================================================
# Extraction de features depuis les plans PDF
# ============================================================================

def extract_text_features(pdf_path):
    """Extrait les features textuelles d'un plan BA."""
    features = {
        "texte_complet": "",
        "mots_cles": {},
        "dimensions": [],
        "labels_elements": [],
        "positions": {},
        "nb_pages": 0,
        "has_sections": False,
        "has_rebar_notation": False,
    }
    
    try:
        with pdfplumber.open(pdf_path) as doc:
            features["nb_pages"] = len(doc.pages)
            
            for page_num, page in enumerate(doc.pages):
                text = page.extract_text() or ""
                features["texte_complet"] += text + "\n"
                
                # Mots-clés BA
                mots_cles = {
                    "semelle": len(re.findall(r"semelle|SEMELLE|S\d", text, re.I)),
                    "poutre": len(re.findall(r"poutre|POUTRE|N\d+|BN\d?", text, re.I)),
                    "colonne": len(re.findall(r"colonne|COLONNE|P\d+|poteau|POTEAU|pilier", text, re.I)),
                    "dalle": len(re.findall(r"dalle|DALLAGE|DALLE|dalles?", text, re.I)),
                    "chainage": len(re.findall(r"chainage|CHAINAGE|CH\d?", text, re.I)),
                    "longrine": len(re.findall(r"longrine|LONGRINE|LG\d?", text, re.I)),
                    "fondation": len(re.findall(r"fondation|FONDATION|FOUND", text, re.I)),
                    "terrassement": len(re.findall(r"terrassement|TERRASSEMENT|terre", text, re.I)),
                    "beton": len(re.findall(r"béton|BETON|B\d+/\d+|C\d+/\d+", text, re.I)),
                    "armature": len(re.findall(r"armature|ARMATURE|HA\d+|Ø\d+|fers? ", text, re.I)),
                    "coffrage": len(re.findall(r"coffrage|COFFRAGE", text, re.I)),
                    "massif": len(re.findall(r"massif|MASSIF", text, re.I)),
                }
                for k, v in mots_cles.items():
                    features["mots_cles"][k] = features["mots_cles"].get(k, 0) + v
                
                # Dimensions (NxN, NxNxN, N.NNxN.NN)
                dims = re.findall(r"(\d+(?:\.\d+)?)[xX×](\d+(?:\.\d+)?)(?:[xX×](\d+(?:\.\d+)?))?", text)
                for d in dims:
                    features["dimensions"].append([float(x) for x in d if x])
                
                # Labels d'éléments
                labels = re.findall(r"\b([A-Z]{1,3}\d{1,3})\b", text)
                features["labels_elements"].extend(labels)
                
                # Sections / coupes
                if re.search(r"section|coupe|COUPE|SECTION|A-A|B-B|C-C", text, re.I):
                    features["has_sections"] = True
                
                # Notation armatures
                if re.search(r"Ø\d+|HA\d+|\d+HA\d+|\d+φ", text, re.I):
                    features["has_rebar_notation"] = True
                
                # Positions des axes (pages 1-3)
                if page_num < 3:
                    words = page.extract_words() or []
                    for w in words:
                        t = w["text"].strip()
                        if len(t) >= 1 and (t.isdigit() or (len(t) == 1 and t.isalpha() and t.isupper())):
                            features["positions"][t] = {"x": w["x0"], "y": w["top"], "page": page_num}
    except Exception as e:
        features["error"] = str(e)
    
    return features


def extract_vector_features(pdf_path):
    """Extrait les features vectorielles (formes, couleurs)."""
    features = {
        "rectangles": [],
        "lignes": [],
        "points": [],
        "nb_drawings": 0,
    }
    
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        drawings = page.get_drawings()
        features["nb_drawings"] = len(drawings)
        
        for d in drawings:
            fill = d.get("fill")
            r = d.get("rect")
            if r is None:
                continue
            
            w, h = r.width, r.height
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            
            # Classification par taille et couleur
            if fill and fill[0] > 0.75 and fill[1] < 0.35 and w < 30 and h < 30:
                features["points"].append({"type": "carre_rouge", "x": cx, "y": cy})
            elif not fill and 36 <= w <= 70 and 36 <= h <= 70 and abs(w - h) < 6:
                features["rectangles"].append({"type": "semelle_box", "x": cx, "y": cy, "w": w, "h": h})
            elif not fill and 17 <= w <= 26 and 17 <= h <= 26:
                features["rectangles"].append({"type": "massif_box", "x": cx, "y": cy})
            elif not fill and w > 100 and h < 5:
                features["lignes"].append({"type": "axe", "x": cx, "y": cy, "w": w})
    except Exception as e:
        features["error"] = str(e)
    
    return features


# ============================================================================
# Classification et analyse
# ============================================================================

def classify_element_type(text_features, vector_features):
    """Classe le type d'élément BA."""
    scores = {
        "semelle": 0,
        "poutre": 0,
        "colonne": 0,
        "dalle": 0,
        "fondation_complete": 0,
    }
    
    mots = text_features.get("mots_cles", {})
    labels = text_features.get("labels_elements", [])
    rects = vector_features.get("rectangles", [])
    pts = vector_features.get("points", [])
    
    # Semelles
    scores["semelle"] = (
        mots.get("semelle", 0) * 3 +
        len([l for l in labels if re.match(r"^S\d", l)]) * 2 +
        len([r for r in rects if r["type"] == "semelle_box"]) * 2
    )
    
    # Poutres
    scores["poutre"] = (
        mots.get("poutre", 0) * 3 +
        len([l for l in labels if re.match(r"^(N\d|BN)", l)]) * 2
    )
    
    # Colonnes
    scores["colonne"] = (
        mots.get("colonne", 0) * 3 +
        len([l for l in labels if re.match(r"^P\d", l)]) * 2 +
        len(pts) * 1
    )
    
    # Dalles
    scores["dalle"] = (
        mots.get("dalle", 0) * 3 +
        len([l for l in labels if re.match(r"^D\d", l)]) * 2
    )
    
    # Fondation complète
    scores["fondation_complete"] = (
        mots.get("fondation", 0) * 2 +
        mots.get("terrassement", 0) * 2 +
        mots.get("beton", 0) * 1
    )
    
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "unknown"


def extract_elements_from_text(text_features):
    """Extrait les éléments détectés dans le texte."""
    elements = {
        "semelles": [],
        "poutres": [],
        "colonnes": [],
        "chainages": [],
        "longrines": [],
        "massifs": [],
    }
    
    labels = text_features.get("labels_elements", [])
    
    for label in labels:
        if re.match(r"^S\d", label):
            elements["semelles"].append(label)
        elif re.match(r"^(N\d|BN\d?)", label):
            elements["poutres"].append(label)
        elif re.match(r"^P\d", label):
            elements["colonnes"].append(label)
        elif re.match(r"^CH", label):
            elements["chainages"].append(label)
        elif re.match(r"^LG", label):
            elements["longrines"].append(label)
        elif re.match(r"^M\d", label):
            elements["massifs"].append(label)
    
    return elements


def extract_rebar_info(text_features):
    """Extrait les informations sur les armatures."""
    text = text_features.get("texte_complet", "")
    
    info = {
        "has_rebar": False,
        "diameters": [],
        "classes": [],
        "notations": [],
    }
    
    # Diamètres
    diams = re.findall(r"Ø\s*(\d+)", text)
    info["diameters"] = list(set(diams))
    
    # Classes d'aciers
    classes = re.findall(r"FeE\s*(\d+)", text, re.I)
    info["classes"] = list(set(classes))
    
    # Notations d'armatures
    notations = re.findall(r"(\d+HA\d+)", text)
    info["notations"] = list(set(notations))
    
    info["has_rebar"] = bool(diams or classes or notations)
    
    return info


# ============================================================================
# Pipeline d'entraînement
# ============================================================================

def process_kaggle_dataset(kaggle_dir):
    """Traite le dataset Kaggle RC_Foundations."""
    kaggle_path = Path(kaggle_dir)
    pdf_dir = kaggle_path / "01_PDF"
    index_csv = kaggle_path / "03_Documentation" / "INDEX.csv"
    
    if not pdf_dir.exists():
        print(f"ERROR: PDF directory not found: {pdf_dir}")
        return []
    
    # Lire l'index
    index_data = {}
    if index_csv.exists():
        with open(index_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pdf_name = row.get("pdf_file", "")
                if pdf_name:
                    index_data[pdf_name] = row
    
    training_data = []
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    print(f"\nProcessing {len(pdf_files)} PDF files from Kaggle dataset...")
    
    for i, pdf_path in enumerate(pdf_files):
        print(f"  [{i+1}/{len(pdf_files)}] {pdf_path.name}")
        
        # Extraction features
        text_feat = extract_text_features(pdf_path)
        vector_feat = extract_vector_features(pdf_path)
        
        # Classification
        element_type = classify_element_type(text_feat, vector_feat)
        elements = extract_elements_from_text(text_feat)
        rebar_info = extract_rebar_info(text_feat)
        
        # Métadonnées de l'index
        meta = index_data.get(pdf_path.name, {})
        
        sample = {
            "id": pdf_path.stem,
            "source": "kaggle",
            "element_type": element_type,
            "declared_type": meta.get("type", "unknown"),
            "description": meta.get("description", ""),
            "text_features": {
                "mots_cles": text_feat["mots_cles"],
                "nb_pages": text_feat["nb_pages"],
                "nb_dimensions": len(text_feat["dimensions"]),
                "nb_labels": len(text_feat["labels_elements"]),
                "labels_uniques": list(set(text_feat["labels_elements"]))[:50],
                "has_sections": text_feat["has_sections"],
                "has_rebar_notation": text_feat["has_rebar_notation"],
            },
            "vector_features": {
                "nb_drawings": vector_feat["nb_drawings"],
                "nb_rectangles": len(vector_feat["rectangles"]),
                "nb_points": len(vector_feat["points"]),
                "nb_lignes": len(vector_feat["lignes"]),
            },
            "elements": elements,
            "rebar": rebar_info,
            "dimensions_sample": text_feat["dimensions"][:20],
        }
        
        training_data.append(sample)
    
    return training_data


def process_local_dataset(dataset_dir):
    """Traite le dataset local (dataset/examples/...)."""
    dataset_path = Path(dataset_dir)
    training_data = []
    
    for example_dir in dataset_path.iterdir():
        if not example_dir.is_dir():
            continue
        
        input_dir = example_dir / "input"
        output_dir = example_dir / "output_reference"
        
        pdf_path = input_dir / "plan.pdf"
        xlsx_path = output_dir / "metre_reference.xlsx"
        
        if not pdf_path.exists():
            continue
        
        print(f"Processing {example_dir.name}...")
        
        text_feat = extract_text_features(pdf_path)
        vector_feat = extract_vector_features(pdf_path)
        
        element_type = classify_element_type(text_feat, vector_feat)
        elements = extract_elements_from_text(text_feat)
        rebar_info = extract_rebar_info(text_feat)
        
        sample = {
            "id": example_dir.name,
            "source": "local",
            "element_type": element_type,
            "has_reference": xlsx_path.exists(),
            "text_features": {
                "mots_cles": text_feat["mots_cles"],
                "nb_pages": text_feat["nb_pages"],
                "nb_dimensions": len(text_feat["dimensions"]),
                "nb_labels": len(text_feat["labels_elements"]),
                "labels_uniques": list(set(text_feat["labels_elements"]))[:50],
                "has_sections": text_feat["has_sections"],
                "has_rebar_notation": text_feat["has_rebar_notation"],
            },
            "vector_features": {
                "nb_drawings": vector_feat["nb_drawings"],
                "nb_rectangles": len(vector_feat["rectangles"]),
                "nb_points": len(vector_feat["points"]),
                "nb_lignes": len(vector_feat["lignes"]),
            },
            "elements": elements,
            "rebar": rebar_info,
            "dimensions_sample": text_feat["dimensions"][:20],
        }
        
        training_data.append(sample)
    
    return training_data


def process_raw_dataset(raw_dir):
    """Traite le dataset raw complet (beams, columns, foundations, walls, precast)."""
    raw_path = Path(raw_dir)
    training_data = []
    
    categories = {
        "beams": "poutre",
        "columns": "colonne",
        "foundations": "semelle",
        "walls": "mur",
        "precast": "colonne",
    }
    
    for cat_dir_name, declared_type in categories.items():
        cat_dir = raw_path / cat_dir_name
        if not cat_dir.exists():
            continue
        
        print(f"\nProcessing category: {cat_dir_name} (declared: {declared_type})")
        
        # Process PDFs
        pdf_files = list(cat_dir.rglob("*.pdf"))
        for i, pdf_path in enumerate(pdf_files):
            print(f"  [{i+1}/{len(pdf_files)}] {pdf_path.name}")
            
            text_feat = extract_text_features(pdf_path)
            vector_feat = extract_vector_features(pdf_path)
            element_type = classify_element_type(text_feat, vector_feat)
            elements = extract_elements_from_text(text_feat)
            rebar_info = extract_rebar_info(text_feat)
            
            sample = {
                "id": pdf_path.stem,
                "source": f"raw_{cat_dir_name}",
                "element_type": element_type,
                "declared_type": declared_type,
                "category": cat_dir_name,
                "text_features": {
                    "mots_cles": text_feat["mots_cles"],
                    "nb_pages": text_feat["nb_pages"],
                    "nb_dimensions": len(text_feat["dimensions"]),
                    "nb_labels": len(text_feat["labels_elements"]),
                    "labels_uniques": list(set(text_feat["labels_elements"]))[:50],
                    "has_sections": text_feat["has_sections"],
                    "has_rebar_notation": text_feat["has_rebar_notation"],
                },
                "vector_features": {
                    "nb_drawings": vector_feat["nb_drawings"],
                    "nb_rectangles": len(vector_feat["rectangles"]),
                    "nb_points": len(vector_feat["points"]),
                    "nb_lignes": len(vector_feat["lignes"]),
                },
                "elements": elements,
                "rebar": rebar_info,
                "dimensions_sample": text_feat["dimensions"][:20],
            }
            training_data.append(sample)
        
        # Also process PNGs (extract metadata from filenames)
        png_files = list(cat_dir.rglob("*.png"))
        for png_path in png_files:
            sample = {
                "id": png_path.stem,
                "source": f"raw_{cat_dir_name}",
                "element_type": declared_type,
                "declared_type": declared_type,
                "category": cat_dir_name,
                "is_image": True,
                "file_size_kb": png_path.stat().st_size // 1024,
                "text_features": {
                    "mots_cles": {},
                    "nb_pages": 1,
                    "nb_dimensions": 0,
                    "nb_labels": 0,
                    "labels_uniques": [],
                    "has_sections": False,
                    "has_rebar_notation": False,
                },
                "vector_features": {
                    "nb_drawings": 0,
                    "nb_rectangles": 0,
                    "nb_points": 0,
                    "nb_lignes": 0,
                },
                "elements": {},
                "rebar": {"has_rebar": False, "diameters": [], "classes": [], "notations": []},
                "dimensions_sample": [],
            }
            training_data.append(sample)
        
        print(f"  Found {len(pdf_files)} PDFs, {len(png_files)} PNGs")
    
    return training_data


# ============================================================================
# Construction du modèle
# ============================================================================

def build_model(training_data):
    """Construit le modèle à partir des données d'entraînement."""
    model = {
        "version": "2.0",
        "nb_samples": len(training_data),
        "type_distribution": {},
        "element_patterns": {},
        "rebar_patterns": {},
        "classification_rules": {},
        "keyword_weights": {},
        "dimension_ranges": {},
    }
    
    # Distribution des types
    for sample in training_data:
        et = sample["element_type"]
        model["type_distribution"][et] = model["type_distribution"].get(et, 0) + 1
        
        # Also count declared types
        dt = sample.get("declared_type", "unknown")
        if dt and dt != "unknown":
            model["type_distribution"][f"declared_{dt}"] = model["type_distribution"].get(f"declared_{dt}", 0) + 1
    
    # Patterns d'éléments
    element_counts = {}
    for sample in training_data:
        for elem_type, labels in sample["elements"].items():
            element_counts.setdefault(elem_type, {"total": 0, "samples": 0})
            element_counts[elem_type]["total"] += len(labels)
            if labels:
                element_counts[elem_type]["samples"] += 1
    
    model["element_patterns"] = element_counts
    
    # Patterns d'armatures
    rebar_stats = {"has_rebar": 0, "diameters": {}, "classes": {}}
    for sample in training_data:
        if sample["rebar"]["has_rebar"]:
            rebar_stats["has_rebar"] += 1
        for d in sample["rebar"]["diameters"]:
            rebar_stats["diameters"][d] = rebar_stats["diameters"].get(d, 0) + 1
        for c in sample["rebar"]["classes"]:
            rebar_stats["classes"][c] = rebar_stats["classes"].get(c, 0) + 1
    
    model["rebar_patterns"] = rebar_stats
    
    # Règles de classification par mots-clés
    keyword_scores = {}
    for sample in training_data:
        et = sample["element_type"]
        for kw, count in sample["text_features"]["mots_cles"].items():
            if count > 0:
                keyword_scores.setdefault(kw, {})
                keyword_scores[kw][et] = keyword_scores[kw].get(et, 0) + count
    
    model["keyword_weights"] = keyword_scores
    
    # Règles de classification
    for elem_type in ["semelle", "poutre", "colonne", "dalle", "fondation_complete"]:
        rules = {
            "required_keywords": [],
            "optional_keywords": [],
            "min_score": 3,
        }
        
        for kw, scores in keyword_scores.items():
            if scores.get(elem_type, 0) > 0:
                rules["required_keywords"].append(kw)
        
        model["classification_rules"][elem_type] = rules
    
    # Plages de dimensions
    all_dims = []
    for sample in training_data:
        all_dims.extend(sample["dimensions_sample"])
    
    if all_dims:
        model["dimension_ranges"] = {
            "min": [min(d[i] for d in all_dims if len(d) > i) for i in range(3)],
            "max": [max(d[i] for d in all_dims if len(d) > i) for i in range(3)],
            "avg": [sum(d[i] for d in all_dims if len(d) > i) / max(1, len([d for d in all_dims if len(d) > i])) for i in range(3)],
        }
    
    return model


def save_model(model, output_path):
    """Sauvegarde le modèle."""
    output = Path(output_path)
    output.mkdir(parents=True, exist_ok=True)
    
    with open(output / "model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    
    print(f"\nModèle sauvegardé: {output / 'model.json'}")
    print(f"  Échantillons: {model['nb_samples']}")
    print(f"  Distribution: {model['type_distribution']}")
    print(f"  Éléments: {model['element_patterns']}")
    print(f"  Armatures: {model['rebar_patterns']['has_rebar']}/{model['nb_samples']} avec armatures")
    
    return model


# ============================================================================
# Main
# ============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Traiter tout le dataset (local + kaggle + raw)")
    ap.add_argument("--kaggle", default=None, help="Répertoire du dataset Kaggle")
    ap.add_argument("--local", default="dataset/examples", help="Répertoire du dataset local")
    ap.add_argument("--raw", default="dataset/raw", help="Répertoire du dataset raw complet")
    ap.add_argument("--output", default="models", help="Répertoire de sortie")
    ap.add_argument("--example", default=None, help="Traiter un seul exemple")
    args = ap.parse_args()
    
    all_data = []
    
    if args.example:
        # Un seul exemple
        example_path = Path(args.example)
        pdf_path = example_path / "input" / "plan.pdf"
        if pdf_path.exists():
            text_feat = extract_text_features(pdf_path)
            vector_feat = extract_vector_features(pdf_path)
            et = classify_element_type(text_feat, vector_feat)
            elems = extract_elements_from_text(text_feat)
            rebar = extract_rebar_info(text_feat)
            
            print(f"\nExemple: {example_path.name}")
            print(f"  Type: {et}")
            print(f"  Éléments: {elems}")
            print(f"  Armatures: {rebar}")
        return
    
    # Dataset Kaggle
    kaggle_dir = args.kaggle or "dataset/kaggle/RC_Foundations_PreviewPack_V1"
    if Path(kaggle_dir).exists():
        kaggle_data = process_kaggle_dataset(kaggle_dir)
        all_data.extend(kaggle_data)
        print(f"\nKaggle: {len(kaggle_data)} exemples")
    
    # Dataset local
    if Path(args.local).exists():
        local_data = process_local_dataset(args.local)
        all_data.extend(local_data)
        print(f"Local: {len(local_data)} exemples")
    
    # Dataset raw complet
    if Path(args.raw).exists():
        raw_data = process_raw_dataset(args.raw)
        all_data.extend(raw_data)
        print(f"Raw: {len(raw_data)} exemples")
    
    if not all_data:
        print("Aucun exemple trouvé")
        return
    
    # Construire et sauvegarder le modèle
    model = build_model(all_data)
    save_model(model, args.output)
    
    # Sauvegarder les données d'entraînement
    with open(Path(args.output) / "training_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDonnées d'entraînement sauvegardées: {Path(args.output) / 'training_data.json'}")


if __name__ == "__main__":
    main()