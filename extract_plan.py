#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_plan.py — Lecture d'un plan de fondation BA (PDF) -> données structurées.

Étapes :
  1. Texte natif (pdfplumber) : positions des axes (1-8 / A-G), étiquettes des
     semelles S?(AxBxH) sur le plan, TABLEAU DES SEMELLES (page 4), catalogue
     poutres (page 5).
  2. Dessins vectoriels (PyMuPDF) : boîtes des semelles, carrés rouges des
     poteaux, massifs -> position par intersection d'axes.
  3. Lectures "vision" : config/readings_vision.yaml (poteaux, tracés CH/LG,
     poutres, annexes) — éléments dont le texte est en courbes dans le PDF.
     Option --vision : interroger l'API Claude (ANTHROPIC_API_KEY) pour
     relire automatiquement les pages avant fusion.
  4. Recoupements : comptages, position axe par axe, incohérences -> a_verifier.

Sortie : output/plan_data.json
Usage : python extract_plan.py [--pdf reference/PLAN_BA_final.pdf] [--vision]
"""
import argparse, json, os, re, sys
import pdfplumber
import fitz
import metre_core

sys.stdout.reconfigure(encoding="utf-8")

SEMELLE_RX = re.compile(r"S(\d)\((\d+)x(\d+)x(\d+)\)", re.I)


def axis_grids(pdf):
    """Positions (pt) des labels d'axes sur les pages 1-3."""
    grids = {}
    with pdfplumber.open(pdf) as doc:
        for pi in range(3):
            page = doc.pages[pi]
            words = page.extract_words(keep_blank_chars=False)
            xs, ys = {}, {}
            for w in words:
                t = w["text"].strip()
                if len(t) == 1 and t.isdigit() and w["top"] < 200:
                    xs.setdefault(t, w["x0"])          # 1..8 en tête de page
                if len(t) == 1 and t in "ABCDEFG" and w["x0"] < 100:
                    ys.setdefault(t, w["top"])          # A..G à gauche
            grids[pi + 1] = {"x": xs, "y": ys}
    return grids


def collect_semelle_labels(pdf, tableau=None):
    """Étiquettes de semelles de la page 1 : S?(AxBxH) et étiquettes nues S?
    (sans cotes — dimensions alors reprises du TABLEAU DES SEMELLES p.4)."""
    out = []
    with pdfplumber.open(pdf) as doc:
        words = doc.pages[0].extract_words(keep_blank_chars=False)
        words.sort(key=lambda w: (w["top"], w["x0"]))
        clusters = []
        for w in words:
            if clusters and abs(w["top"] - clusters[-1][0]) <= 2.5:
                clusters[-1][1].append(w)
            else:
                clusters.append([w["top"], [w]])
        for top, ws in clusters:
            ws.sort(key=lambda w: w["x0"])
            seg, prev = [], None
            groups = []
            for w in ws:
                if prev is None or w["x0"] - prev <= 12:
                    seg.append(w)
                else:
                    groups.append(seg)
                    seg = [w]
                prev = w["x1"]
            groups.append(seg)
            for seg in groups:
                txt = "".join(w["text"] for w in seg)
                m = SEMELLE_RX.search(txt)
                if m:
                    out.append({"text": m.group(0), "x": seg[0]["x0"], "y": top})
                else:
                    m2 = re.search(r"\bS(\d)\b", txt)
                    if m2 and tableau:
                        rep = f"S{m2.group(1)}"
                        trow = next((t for t in tableau if t["repere"] == rep), None)
                        if trow:
                            out.append({"text": rep, "x": seg[0]["x0"], "y": top,
                                        "from_tableau": True,
                                        "A": trow["A"], "B": trow["B"], "H": trow["H"]})
    return out


def vector_features(pdf):
    """Boîtes de semelles / carrés rouges (poteaux) / massifs via PyMuPDF.
    Classification sur la bbox de chaque groupe de dessin (d['rect']) :
    les exports AutoCAD tracent les rectangles en polylignes ('l'), pas 're'."""
    doc = fitz.open(pdf)
    page = doc[0]
    sem_boxes, red_squares, massif_boxes = [], [], []
    for d in page.get_drawings():
        fill = d.get("fill")
        r = d.get("rect")
        if r is None:
            continue
        w, h = r.width, r.height
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if fill and fill[0] > 0.75 and fill[1] < 0.35 and w < 30 and h < 30:
            red_squares.append({"x": cx, "y": cy, "w": w, "h": h})
        elif not fill and 36 <= w <= 70 and 36 <= h <= 70 and abs(w - h) < 6:
            sem_boxes.append({"x": cx, "y": cy, "w": w, "h": h})
        elif not fill and 17 <= w <= 26 and 17 <= h <= 26:
            massif_boxes.append({"x": cx, "y": cy})
    return sem_boxes, red_squares, massif_boxes


def nearest_intersection(x, y, grid, tol=48.0):
    """Intersection d'axes la plus proche ; renvoie (axe, fill, dist) ou None."""
    best = (None, None, 1e9)
    for f, fx in grid["x"].items():
        for a, ay in grid["y"].items():
            d = ((x - fx) ** 2 + (y - ay) ** 2) ** 0.5
            if d < best[2]:
                best = (a, f, d)
    return best if best[2] <= tol else (None, None, best[2])


def parse_tableau_semelles(pdf):
    """Tableau des semelles (page 4) : repère, AxB, H, ferraillage."""
    rows = []
    with pdfplumber.open(pdf) as doc:
        txt = doc.pages[3].extract_text() or ""
    for line in txt.splitlines():
        m = re.match(r"^(S\d)\s+(\d+)x(\d+)\s+(\d+)\s+(\d+)\s+(\d+HA\d+)\s+(\d+HA\d+)", line.strip())
        if m:
            s, axb, a, b, h, fx, fy = m.groups()
            rows.append({"repere": s, "A": int(a) / 100, "B": int(b) / 100,
                         "H": int(h) / 100, "fx": fx, "fy": fy})
    return rows


def parse_poutres_catalogue(pdf):
    """Types de poutres (page 5) : N1..N7, BN1/BN2 + sections 20x30 etc."""
    with pdfplumber.open(pdf) as doc:
        txt = doc.pages[4].extract_text() or ""
    found = {}
    for m in re.finditer(r"(N[1-7]|BN\d?)\s*(\d+)x(\d+)", txt):
        found.setdefault(m.group(1), f"{m.group(2)}x{m.group(3)}")
    return found


def read_vision_api(pdf, pages=(0, 1, 2)):
    """Option --vision : relit les pages via l'API Claude (ANTHROPIC_API_KEY).
    Renvoie un dict comparable à readings_vision.yaml (best effort)."""
    import anthropic
    client = anthropic.Anthropic()
    doc = fitz.open(pdf)
    prompt = """Lis ce plan de fondation BA. Réponds UNIQUEMENT en JSON avec:
{"poteaux": {"A1": "P3", ...}, "chainages": [{"axe":"A","de":"1","a":"2"}...],
 "longrines": [{"axe":"C","de":"5","a":"6","nom":"LG"}...],
 "poutres_mezzanine": {"horizontales":[...], "verticales":[...], "bn":[...]},
 "poutres_ph_rdc": {...}}
Ne devine rien : si un repère est illisible, mets "a_verifier": true sur l'entrée."""
    out = {}
    for pi in pages:
        pix = doc[pi].get_pixmap(dpi=200)
        png = pix.tobytes("png")
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=8000,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": png}},
                {"type": "text", "text": prompt}]}])
        try:
            m = re.search(r"\{.*\}", resp.content[0].text, re.S)
            out[f"page{pi+1}"] = json.loads(m.group(0))
        except Exception as e:
            out[f"page{pi+1}"] = {"erreur": str(e)}
    return out


def read_glm_ocr(pdf, pages=(0, 1, 2)):
    """Backend OCR local zai-org/GLM-OCR (0.9B, transformers, MIT).
    Mode « information extraction » avec schéma JSON strict — le modèle ne
    doit rien compléter : les champs illisibles restent vides (-> a_verifier).
    Nécessite : pip install git+https://github.com/huggingface/transformers.git + torch."""
    import torch  # noqa
    from transformers import AutoProcessor, AutoModelForImageTextToText
    doc = fitz.open(pdf)
    model_path = "zai-org/GLM-OCR"
    processor = AutoProcessor.from_pretrained(model_path)
    model = AutoModelForImageTextToText.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto")
    schema = """请按下列JSON格式输出图中信息 (ne devine rien, laisse vide si illisible):
{"type_poteaux": {"A1": "", "A2": "", "...": "P1/P2/P3/P4"},
 "chainages": [{"axe": "", "de": "", "a": ""}],
 "longrines": [{"axe": "", "de": "", "a": "", "nom": "LG/LG2"}],
 "poutres": [{"axe": "", "de": "", "a": "", "nom": "N1..N7/BN1/BN2/CH1"}]}"""
    out = {}
    for pi in pages:
        pix = doc[pi].get_pixmap(dpi=200)
        os.makedirs("output/pages", exist_ok=True)
        tmp = f"output/pages/ocr_p{pi+1}.png"
        pix.save(tmp)
        messages = [{"role": "user", "content": [
            {"type": "image", "url": tmp},
            {"type": "text", "text": schema}]}]
        inputs = processor.apply_chat_template(messages, tokenize=True,
                                               add_generation_prompt=True,
                                               return_dict=True,
                                               return_tensors="pt").to(model.device)
        inputs.pop("token_type_ids", None)
        gen = model.generate(**inputs, max_new_tokens=4096)
        out[f"page{pi+1}"] = processor.decode(gen[0][inputs["input_ids"].shape[-1]:],
                                              skip_special_tokens=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="reference/PLAN_BA_final.pdf")
    ap.add_argument("--config", default="config/postes.yaml")
    ap.add_argument("--readings", default="config/readings_vision.yaml")
    ap.add_argument("--out", default="output/plan_data.json")
    ap.add_argument("--vision", action="store_true",
                    help="relire les pages via l'API Claude (ANTHROPIC_API_KEY requis)")
    ap.add_argument("--ocr", choices=["glm-ocr"], default=None,
                    help="OCR local zai-org/GLM-OCR (torch + transformers requis)")
    args = ap.parse_args()

    cfg = metre_core.load_config(args.config)
    readings = metre_core.load_yaml(args.readings)

    grids = axis_grids(args.pdf)
    tableau = parse_tableau_semelles(args.pdf)
    labels = collect_semelle_labels(args.pdf, tableau)
    sem_boxes, red_squares, massif_boxes = vector_features(args.pdf)
    cat_poutres_pdf = parse_poutres_catalogue(args.pdf)

    # --- auto-mapping des étiquettes de semelles sur la grille (page 1) ----
    # tolérance large : les étiquettes sont décalées des intersections (au-
    # dessus/dessous des boîtes). Mapping = VÉRIFICATION ; la source primaire
    # est readings['semelles'] (lecture vision sourcée).
    semelles_auto, ambigus = [], []
    for lb in labels:
        m = SEMELLE_RX.match(lb["text"])
        if m:
            s, a, b, h = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        else:
            s = re.match(r"S(\d)", lb["text"]).group(1)
            a, b, h = round(lb["A"] * 100), round(lb["B"] * 100), round(lb["H"] * 100)
        axe, fill, dist = nearest_intersection(lb["x"], lb["y"], grids[1], tol=90)
        entry = {"repere": f"S{s}", "A": a / 100, "B": b / 100, "H": h / 100,
                 "label_xy": [round(lb["x"]), round(lb["y"])], "dist_pt": round(dist, 1)}
        if lb.get("from_tableau"):
            entry["cotes_source"] = "tableau p.4 (étiquette sans cotes sur le plan)"
        if axe:
            entry.update({"axe": axe, "fill": fill})
            semelles_auto.append(entry)
        else:
            entry["a_verifier"] = True
            ambigus.append(entry)

    # --- recoupement : comptages et cohérence lectures vs vectoriel ---------
    checks = []
    poteaux_read = readings.get("poteaux", {})
    n_red, n_sem, n_box = len(red_squares), len(semelles_auto), len(sem_boxes)
    checks.append({"type": "comptage_semelles",
                   "etiquettes_texte": len(semelles_auto) + len(ambigus),
                   "boites_vectorielles": n_box,
                   "lectures_vision": len(rd_sem := readings.get("semelles", {})),
                   "ok": (len(semelles_auto) + len(ambigus)) == n_box == len(rd_sem)})

    # cohérence mapping auto vs lectures (vérification, pas source de vérité)
    auto_map = {f"{e['axe']}{e['fill']}": e["repere"] for e in semelles_auto if e.get("axe")}
    read_map = dict(rd_sem)
    mismatches = []
    for k in sorted(set(auto_map) & set(read_map)):
        if auto_map[k].upper() != str(read_map[k]).upper():
            mismatches.append({"intersection": k, "texte": auto_map[k],
                               "lecture": read_map[k]})
    checks.append({"type": "semelles_mapping",
                   "assignees_auto": len(auto_map),
                   "non_assignees": [e["repere"] for e in ambigus],
                   "divergences_texte_vs_lecture": mismatches})

    # poteaux : les carrés rouges confirment le NOMBRE de poteaux lus
    checks.append({"type": "poteaux", "carres_rouges": n_red,
                   "lectures": len(poteaux_read),
                   "ok": n_red == len(poteaux_read)})
    checks.append({"type": "massifs_vectoriels", "boxes_19_23pt": len(massif_boxes),
                   "lectures": readings.get("massifs")})

    vision_out = None
    ocr_out = None
    if args.vision:
        vision_out = read_vision_api(args.pdf)
    if args.ocr == "glm-ocr":
        ocr_out = read_glm_ocr(args.pdf)

    data = {
        "meta": {
            "pdf": args.pdf,
            "echelle_pt_par_cm": round((grids[1]["x"]["8"] - grids[1]["x"]["1"]) / (23.14 + 1.0), 4),
            "grille": grids,
            "vision_api": vision_out,
            "ocr_glm": ocr_out,
        },
        "tableau_semelles": tableau,
        "catalogue_poutres_pdf": cat_poutres_pdf,
        "semelles_auto": semelles_auto,
        "semelles_ambigues": ambigus,
        "massifs_auto": len(massif_boxes),
        "readings": readings,
        "checks": checks,
        "a_verifier": [e for e in ambigus],
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"axes: page1 x={grids[1]['x']} y={grids[1]['y']}")
    print(f"semelles (texte): {len(labels)} | boîtes vectorielles: {n_box} | "
          f"carrés rouges (poteaux): {n_red}")
    print(f"tableau des semelles p.4: {[r['repere'] for r in tableau]}")
    print(f"poutres p.5: {cat_poutres_pdf}")
    for c in checks:
        print("check:", json.dumps(c, ensure_ascii=False))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
