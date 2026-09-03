#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_metre.py — plan_data.json + config/ -> métré Excel + comparaison + rapport.

Feuilles générées :
  1. "Detail quantitatif fondation" — postes 1, 3, 15, 16, 17, 20, 7, 19
     (même structure que le métré de référence, formules Excel réelles)
  2. "Armatures" — bloc agrégé (ferraillage par type) + détail par élément
  3. "Comparaison" — ligne à ligne contre le métré de référence

Politique zéro-hallucination : toute quantité provient du plan (texte natif,
vecteurs, lectures vision sourcées) ou de la référence (signalé) ; rien n'est
estimé silencieusement — le reste part dans output/rapport_verification.md.

Usage : python build_metre.py [--plan output/plan_data.json] [--out output/metre_genere.xlsx]
"""
import argparse, json, os, re, sys
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import metre_core

sys.stdout.reconfigure(encoding="utf-8")

THIN = Side(style="thin")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BOLD = Font(bold=True)
HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")
TOTAL_FILL = PatternFill("solid", fgColor="FCE4D6")


class SheetWriter:
    """Écrit des lignes de métré et garde la trace pour comparaison/formules."""

    def __init__(self, ws, registry):
        self.ws = ws
        self.row = 0
        self.registry = registry          # lignes générées (pour comparaison)
        self.cur_section = None
        self.cur_poste = None

    def next(self):
        self.row += 1
        return self.row

    def cell(self, r, c, v=None, bold=False, fill=None, border=True, wrap=False):
        cell = self.ws.cell(row=r, column=c)
        if v is not None:
            cell.value = v
        if bold:
            cell.font = BOLD
        if fill:
            cell.fill = fill
        if border:
            cell.border = BORDER
        if wrap:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        return cell

    def blank(self):
        self.next()

    def header(self):
        r = self.next()
        self.cell(r, 1, "AO N° :", border=False)
        r = self.next()  # 2
        r = self.next()  # 3
        self.cell(r, 3, "Construction de locaux et travaux de réaménagement à la mine Youssoufia", border=False)
        r = self.next()  # 4
        r = self.next()  # 5
        self.cell(r, 5, "Détail Quantitatif Métré", bold=True, border=False)
        r1, r2 = self.next(), self.next()
        self.ws.merge_cells(start_row=r1, start_column=1, end_row=r2, end_column=1)
        self.ws.merge_cells(start_row=r1, start_column=2, end_row=r2, end_column=6)
        self.ws.merge_cells(start_row=r1, start_column=7, end_row=r2, end_column=7)
        self.ws.merge_cells(start_row=r1, start_column=8, end_row=r2, end_column=8)
        self.ws.merge_cells(start_row=r1, start_column=9, end_row=r2, end_column=9)
        self.ws.merge_cells(start_row=r1, start_column=10, end_row=r2, end_column=10)
        self.ws.merge_cells(start_row=r1, start_column=11, end_row=r2, end_column=11)
        self.ws.merge_cells(start_row=r1, start_column=12, end_row=r2, end_column=12)
        self.ws.merge_cells(start_row=r1, start_column=13, end_row=r2, end_column=13)
        for c, t in [(1, "N°"), (2, "Désignation, détail de calcul, croquis, principe et justificatif"),
                     (7, "U"), (8, "N"), (9, "Longueur"), (10, "largeur"),
                     (11, "Hauteur / épaisseur"), (12, "Qté partielle"),
                     (13, "Qté Total des Métrés")]:
            self.cell(r1, c, t, bold=True, fill=HEADER_FILL)
        return r2

    def poste(self, num, designation):
        r = self.next()
        self.cell(r, 1, num, bold=True)
        self.cell(r, 2, designation, bold=True, wrap=True)
        self.cur_poste = num
        return r

    def section(self, text, col=1, bold=True, key=None):
        r = self.next()
        self.cell(r, col, text, bold=bold)
        self.cur_section = key or text
        return r

    def set_section(self, key):
        self.cur_section = key

    def subheader(self, labels, start=1):
        r = self.next()
        for i, t in enumerate(labels):
            self.cell(r, start + i, t, bold=True, fill=HEADER_FILL)
        return r

    def param(self, col, value, label=None):
        r = self.next()
        if label:
            self.cell(r, col - 1, label)
        self.cell(r, col, value)
        return r

    def line(self, key, *, repere=None, axe=None, fill=None, nom=None, U="M3",
             N=1, I=None, J=None, K=None, L="KJIH", note=None, src="plan"):
        """I/J/K : valeur ou tuple ('expr', "3.82+0.4"). L : forme de la formule."""
        r = self.next()
        self.cell(r, 1, repere)
        self.cell(r, 2, axe)
        self.cell(r, 3, fill)
        self.cell(r, 4, nom)
        self.cell(r, 7, U)
        self.cell(r, 8, N)
        for col, val in ((9, I), (10, J), (11, K)):
            if isinstance(val, tuple):
                self.cell(r, col, "=" + val[1])
            elif val is not None:
                self.cell(r, col, val)
        if L == "KJIH":
            self.cell(r, 12, f"=K{r}*J{r}*I{r}*H{r}")
        elif L == "HIJK":
            self.cell(r, 12, f"=H{r}*I{r}*J{r}*K{r}")
        elif L == "JIHK":
            self.cell(r, 12, f"=J{r}*I{r}*H{r}*K{r}")
        self.cell(r, 13, note or "")
        self.registry.append({
            "poste": self.cur_poste, "section": self.cur_section, "key": key,
            "repere": repere, "axe": axe, "fill": fill, "nom": nom,
            "N": N, "row": r, "src": src,
            "I": I[0] if isinstance(I, tuple) else I,
            "J": J[0] if isinstance(J, tuple) else J,
            "K": K[0] if isinstance(K, tuple) else K,
            "note": note,
        })
        return r

    def total(self, label="total", l_from=None, l_to=None, extra_n=None):
        r = self.next()
        self.cell(r, 1, label, bold=True, fill=TOTAL_FILL)
        self.cell(r, 13, f"=SUM(L{l_from}:L{l_to})", bold=True, fill=TOTAL_FILL)
        if extra_n:
            self.cell(r, 14, extra_n)
        return r


def L(de, a, orient):
    """(valeur, expr) pour une longueur d'axe ; override via readings.géré en amont."""
    val, expr = metre_core.run_length(de, a, orient)
    return (val, expr) if expr else val


def long_of(entry, orient):
    if "long" in entry:
        raw = str(entry["long"])
        expr = raw[1:] if raw.startswith("=") else raw
        try:
            val = eval(expr, {"__builtins__": {}}, {})
        except Exception:
            val = None
        return (val, expr)
    return L(entry["de"], entry["a"], orient)


# ---------------------------------------------------------------------------
# Feuille 1 : Detail quantitatif fondation
# ---------------------------------------------------------------------------

def build_fondation(w, cfg, rd):
    reg = w.registry
    w.header()
    p = cfg["parametres"]

    # ---- Poste 1 -----------------------------------------------------------
    w.poste("1", "A-  ETUDES TECHNIQUES, ESSAIS, CONTROLES ET RECEPTIONS")
    w.section("Etude suivant descriptif (géotechnique, technique, formulations bétons, "
              "essais et contrôles, réceptions, récolement)", col=2)
    r = w.next()
    w.cell(r, 7, "f")
    w.cell(r, 8, 1)
    w.cell(r, 13, 1)

    # ---- Poste 3 : terrassement -------------------------------------------
    w.poste("3", "B-  GROS ŒUVRES et maconnerie")
    w.section("Terrassement en fouilles, en tranchées ou en plein masse y compris "
              "décapage de la terre végétale", col=2, key="terrassement")
    rn = w.next()
    w.cell(rn, 14, "H/ bon sol + terre végétale $$$")
    rn = w.next()
    w.cell(rn, 14, p["H_bon_sol"])
    n13 = f"$N${rn}"
    w.subheader(["axe", "fill"], start=2)
    first = None
    for f in rd["fouilles"]:
        kv = p["H_bon_sol"] + f["h_plus"]
        r = w.line("terrassement", axe=f["axe"], fill=f["de"], U="M3", N=1,
                   I=f["long"], J=p["largeur_fouille"],
                   K=(kv, f"{n13}+{f['h_plus']}" if f["h_plus"] else n13),
                   src="référence (implantation fouilles non cotée)")
        first = first or r
    w.total("total", first, reg[-1]["row"])

    # ---- Poste 15 : béton de propreté --------------------------------------
    w.poste("15", " Béton de propreté ")
    w.section("pour semelle isolee", bold=False, key="semelles_prop")
    w.subheader(["axe", "fill"], start=2)
    first = None
    for k, axe in enumerate(rd["semelles_proprete"]):
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        r = w.line(f"prop_sem_{axe}", repere=st, axe=axe[0], fill=axe[1:],
                   U="M3", N=1, I=(None, f"D{0}") if False else None,
                   src="plan (texte natif)")
        rr = reg[-1]["row"]
        w.cell(rr, 4, cat["A"])
        w.cell(rr, 5, cat["B"])
        w.cell(rr, 6, cat["H"])
        w.cell(rr, 9, f"=D{rr}")
        w.cell(rr, 10, f"=E{rr}")
        w.cell(rr, 11, p["ep_proprete"])
        w.cell(rr, 12, f"=H{rr}*I{rr}*J{rr}*K{rr}")
        reg[-1]["I"], reg[-1]["J"], reg[-1]["K"] = cat["A"], cat["B"], p["ep_proprete"]
        first = first or r
    tot_sem_prop = w.total("total", first, reg[-1]["row"])

    w.section("pour longrines ", bold=False, key="longrines_prop")
    w.subheader(["axe", "fill", "Nom"])
    first = None
    for lg in rd["longrines"]:
        r = w.line(f"prop_lg_{lg['axe']}_{lg['de']}_{lg['a']}", axe=lg["axe"],
                   fill=f"{lg['de']}-{lg['a']}", nom=lg["nom"], U="M3", N=1,
                   I=long_of(lg, "V" if str(lg["axe"]).isdigit() else "H"),
                   J=p["largeur_fouille"] - 1.2, K=p["ep_proprete"],
                   src="plan (lecture vision)")
        first = first or r
    tot_lg_prop = w.total("total", first, reg[-1]["row"])

    w.section("pour chainage", bold=False, key="chainages_prop")
    w.subheader(["axe", "fill", "Nom"])
    first = None
    for ch in rd["chainages"]:
        r = w.line(f"prop_ch_{ch['axe']}_{ch['de']}_{ch['a']}", axe=ch["axe"],
                   fill=f"{ch['de']}-{ch['a']}", nom="CH", U="M3", N=1,
                   I=long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"),
                   J=0.5, K=p["ep_proprete"], src="plan (lecture vision)")
        first = first or r
    tot_ch_prop = w.total("total", first, reg[-1]["row"])
    w.cell(tot_ch_prop, 14, f"=M{tot_sem_prop}+M{tot_lg_prop}+M{tot_ch_prop}")

    # ---- Poste 16 : gros béton ---------------------------------------------
    w.poste("16", "Gros béton ")
    w.set_section("gros_beton")
    w.subheader(["axe", "fill"], start=2)
    first = None
    for axe in rd["semelles_gros_beton"]:
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        r = w.line(f"gb_sem_{axe}", repere=st, axe=axe[0], fill=axe[1:], U="M3",
                   N=1, I=cat["A"], J=cat["B"], K=p["ep_gros_beton"],
                   src="plan (texte natif + détail p.6 « assise en gros béton »)")
        first = first or r
    for i in range(rd.get("semelles_perdues", 0)):
        r = w.line(f"gb_perdue_{i+1}", repere="semelle perdu", U="M3", N=1,
                   I=1.6, J=1.6, K=1.4,
                   src="référence (zone DP — non identifiable sur le plan)")
        first = first or r
    for g in rd.get("gb_assise_rangée_G", []):
        r = w.line(f"gb_g_{g['de']}_{g['a']}", axe="G", fill=f"{g['de']}-{g['a']}",
                   U="M3", N=1, I=L(g["de"], g["a"], "H"), J=0.4, K=0.3,
                   src="référence (assise rangée G)")
        first = first or r
    w.total("total", first, reg[-1]["row"])

    # ---- Poste 17 : maçonnerie de moellons ---------------------------------
    w.poste("17", " Maçonnerie de moellons en fondation exécutée selon descriptif ")
    w.set_section("maconnerie")
    w.subheader(["axe", "fill"], start=2)
    first = None
    for ch in rd["chainages"]:
        r = w.line(f"mac_{ch['axe']}_{ch['de']}_{ch['a']}", axe=ch["axe"],
                   fill=f"{ch['de']}-{ch['a']}", U="M3", N=1,
                   I=long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"),
                   J=0.4, K=(p["H_bon_sol"] - 0.1, f"{n13}-0.1"),
                   src="plan (lecture vision) + hauteur site")
        first = first or r
    w.total("total", first, reg[-1]["row"])

    # ---- Poste 20 : béton armé ---------------------------------------------
    w.poste("20", " Béton pour béton armé en fondation et en élévation")
    w.section("pour semelle isolee", bold=False, key="semelles_ba")
    w.subheader(["axe", "fill"], start=2)
    first = None
    for axe in rd["semelles"]:
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        r = w.line(f"ba_sem_{axe}", repere=st, axe=axe[0], fill=axe[1:], U="M3",
                   N=1, I=cat["A"], J=cat["B"], K=cat["H"], src="plan (texte natif)")
        first = first or r
    tot_sem_ba = w.total("total", first, reg[-1]["row"])

    w.section("pour longrines ", bold=False, key="longrines_ba")
    w.subheader(["axe", "fill", "Nom"])
    first = None
    for lg in rd["longrines"]:
        b = 0.5 if lg["nom"] == "LG" else 0.4
        r = w.line(f"ba_lg_{lg['axe']}_{lg['de']}_{lg['a']}", axe=lg["axe"],
                   fill=f"{lg['de']}-{lg['a']}", nom=lg["nom"], U="M3", N=1,
                   I=long_of(lg, "V" if str(lg["axe"]).isdigit() else "H"),
                   J=b, K=0.2, src="plan (lecture vision)")
        first = first or r
    tot_lg_ba = w.total("total", first, reg[-1]["row"])

    w.section("pour chainage", bold=False, key="chainages_ba")
    w.subheader(["axe", "fill", "Nom"])
    first = None
    for ch in rd["chainages"]:
        r = w.line(f"ba_ch_{ch['axe']}_{ch['de']}_{ch['a']}", axe=ch["axe"],
                   fill=f"{ch['de']}-{ch['a']}", nom="CH", U="M3", N=1,
                   I=long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"),
                   J=0.4, K=0.2, src="plan (lecture vision)")
        first = first or r
    tot_ch_ba = w.total("total", first, reg[-1]["row"])

    w.section("fût des poteaux", bold=False, key="futs")
    w.subheader(["axe", "fill", "Nom"], start=2)
    first = None
    for axe, pt in rd["poteaux"].items():
        cat = cfg["catalogues"]["poteaux"][pt]
        r = w.line(f"fut_{axe}", axe=axe[0], fill=axe[1:], nom=pt, U="M3", N=1,
                   I=cat["b"], J=cat["h"],
                   K=(p["H_bon_sol"] - 0.13 - 0.1 - 0.25, f"{n13}-0.13-0.1-0.25"),
                   src="plan (lecture vision)")
        first = first or r
    tot_fut = w.total("total", first, reg[-1]["row"])

    w.section("pour les massifs", bold=False, key="massifs")
    r = w.next()
    w.cell(r, 8, rd["massifs"])
    w.cell(r, 9, 0.5)
    w.cell(r, 10, 0.5)
    w.cell(r, 11, 0.5)
    w.cell(r, 12, f"=K{r}*J{r}*I{r}*H{r}")
    reg.append({"poste": "20", "section": "massifs", "key": "massifs",
                "repere": None, "axe": None, "fill": None, "nom": "MASSIF",
                "N": rd["massifs"], "row": r, "src": "plan (lecture vision)",
                "I": 0.5, "J": 0.5, "K": 0.5, "note": None})
    tot_massif = w.total("total", r, r)

    w.section("poteaux (élévation)", bold=False, key="poteaux_elev")
    w.cell(w.row, 14, "")
    w.subheader(["axe", "fill", "Nom"], start=2)
    first = None
    for axe, pt in rd["poteaux"].items():
        cat = cfg["catalogues"]["poteaux"][pt]
        r = w.line(f"pot_{axe}", axe=axe[0], fill=axe[1:], nom=pt, U="M3", N=1,
                   I=cat["b"], J=cat["h"], K=p["h_poteau_elevation"],
                   src="plan (lecture vision) + hauteur élévation")
        first = first or r
    w.total("total", first, reg[-1]["row"])

    for niveau, cle, key in (("POUTRE MEZZANINE", "poutres_mezzanine", "poutres_mezz"),
                             ("POUTRE PH RDC", "poutres_ph_rdc", "poutres_ph")):
        w.section(niveau, key=key)
        w.subheader(["NOM", "axe", "fill"])
        bloc = rd[cle]
        first = None
        for sens, orient in (("horizontales", "H"), ("verticales", "V")):
            for pt in bloc.get(sens, []):
                cat = cfg["catalogues"]["poutres"][pt["nom"]]
                r = w.line(f"{cle}_{pt['axe']}_{pt['de']}_{pt['a']}_{pt['nom']}",
                           repere=pt["nom"], axe=pt["axe"],
                           fill=f"{pt['de']}-{pt['a']}", nom=pt["nom"], U="M3",
                           N=2 if pt.get("jumelée") else 1,
                           I=long_of(pt, orient), J=cat["b"], K=cat["h"],
                           note=pt.get("note"), src="plan (lecture vision)")
                first = first or r
                if pt["nom"] == "N7":
                    cat2 = cfg["catalogues"]["poutres"]["N7p"]
                    r = w.line(f"{cle}_{pt['axe']}_{pt['de']}_{pt['a']}_N7p",
                               repere="+", axe=pt["axe"], fill=f"{pt['de']}-{pt['a']}",
                               nom="+", U="M3", N=1, I=(None, f"I{r}"), J=cat2["b"],
                               K=cat2["h"], note=cat2.get("note"),
                               src="plan + règle métreur")
        for pt in bloc.get("bn", []):
            cat = cfg["catalogues"]["poutres"][pt["nom"]]
            r = w.line(f"{cle}_bn_{pt['axe']}_{pt['de']}_{pt['a']}", repere=pt["nom"],
                       axe=pt["axe"], fill=f"{pt['de']}-{pt['a']}", nom=pt["nom"],
                       U="M3", N=1,
                       I=long_of(pt, "V" if str(pt["axe"]).isdigit() else "H"),
                       J=cat["b"], K=cat["h"], note=pt.get("note"),
                       src="plan (lecture vision)")
            first = first or r
        w.total("total", first, reg[-1]["row"])
        if cle == "poutres_mezzanine":
            pass
    tot_poutres = None

    # ---- Poste 7 : remblaiement --------------------------------------------
    w.poste("7", " Remblaiement en tout-venant ")
    w.section("adduction", bold=False, key="remblai_add")
    w.subheader(["axe", "fill"], start=2)
    first = None
    for f in rd["remblai_adduction"]:
        kv = p["H_bon_sol"] + f["h_plus"]
        r = w.line("remblai_add", axe=f["axe"], fill=f["de"], U="M3", N=1,
                   I=f["long"], J=p["largeur_fouille"],
                   K=(kv, f"{n13}+{f['h_plus']}" if f["h_plus"] else n13),
                   src="référence (implantation non cotée)")
        first = first or r
    w.section("reduire", bold=False, key="remblai_red")
    w.subheader(["axe", "fill"], start=2)

    def neg(key, axe, fill, repere, nom, N, I, J, K, src):
        return w.line(key, repere=repere, axe=axe, fill=fill, nom=nom, U="M3",
                      N=-N, I=I, J=J, K=K, src=src)

    for axe in rd["semelles_proprete"]:
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        neg("rem_sem_p_" + axe, axe[0], axe[1:], st, None, 1, (None, f"D{{}}"), None,
            p["ep_proprete"], "plan")
    # (les formules D/E ci-dessus sont réécrites explicitement ci-dessous)
    for e in reg:
        if e["key"].startswith("rem_sem_p_"):
            rr = e["row"]
            cat = cfg["catalogues"]["semelles"][rd["semelles"][e["axe"] + e["fill"]]]
            w.cell(rr, 4, cat["A"])
            w.cell(rr, 5, cat["B"])
            w.cell(rr, 6, cat["H"])
            w.cell(rr, 9, f"=D{rr}")
            w.cell(rr, 10, f"=E{rr}")
            w.cell(rr, 12, f"=H{rr}*I{rr}*J{rr}*K{rr}")
            e["I"], e["J"] = cat["A"], cat["B"]
    for lg in rd["longrines"]:
        neg("rem_lg_" + lg["axe"] + lg["de"] + lg["a"], lg["axe"],
            f"{lg['de']}-{lg['a']}", None, lg["nom"], 1,
            long_of(lg, "V" if str(lg["axe"]).isdigit() else "H"),
            p["largeur_fouille"] - 1.2, p["ep_proprete"], "plan")
    for ch in rd["chainages"]:
        neg("rem_ch_" + ch["axe"] + ch["de"] + ch["a"], ch["axe"],
            f"{ch['de']}-{ch['a']}", None, "CH", 1,
            long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"), 0.5,
            p["ep_proprete"], "plan")
    for axe in rd["semelles_gros_beton"]:
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        neg("rem_gb_" + axe, axe[0], axe[1:], st, None, 1, cat["A"], cat["B"],
            p["ep_gros_beton"], "plan")
    for ch in rd["chainages"]:
        neg("rem_mac_" + ch["axe"] + ch["de"] + ch["a"], ch["axe"],
            f"{ch['de']}-{ch['a']}", None, None, 1,
            long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"), 0.4,
            (None, f"{n13}-0.1"), "plan")
    r = w.line("rem_forme", axe="A-F", fill="1-6", U="M2", N=-1, I=24.44,
               J=(None, "3.82+0.4+0.82+1.08+0.15+3.82+0.15+0.15"), K=0.13,
               L="JIHK", src="référence (déduction forme, non cotée)")
    for axe in rd["semelles"]:
        st = rd["semelles"][axe]
        cat = cfg["catalogues"]["semelles"][st]
        neg("rem_ba_sem_" + axe, axe[0], axe[1:], st, None, 1, cat["A"], cat["B"],
            cat["H"], "plan")
    for lg in rd["longrines"]:
        neg("rem_ba_lg_" + lg["axe"] + lg["de"] + lg["a"], lg["axe"],
            f"{lg['de']}-{lg['a']}", None, lg["nom"], 1,
            long_of(lg, "V" if str(lg["axe"]).isdigit() else "H"),
            0.5 if lg["nom"] == "LG" else 0.4, 0.2, "plan")
    for ch in rd["chainages"]:
        neg("rem_ba_ch_" + ch["axe"] + ch["de"] + ch["a"], ch["axe"],
            f"{ch['de']}-{ch['a']}", None, "CH", 1,
            long_of(ch, "V" if str(ch["axe"]).isdigit() else "H"), 0.4, 0.2, "plan")
    for axe, pt in rd["poteaux"].items():
        cat = cfg["catalogues"]["poteaux"][pt]
        neg("rem_fut_" + axe, axe[0], axe[1:], None, pt, 1, cat["b"], cat["h"],
            (None, f"{n13}-0.13-0.1-0.25"), "plan")
    r = w.line("rem_massif", repere="MASSIF", U="M3", N=-rd["massifs"], I=0.5,
               J=0.5, K=0.5, src="plan")
    w.total("total", first, reg[-1]["row"])

    # ---- Poste 19 : forme en béton ------------------------------------------
    w.poste("19", "Forme en béton ")
    w.set_section("forme")
    w.section("POUR DALLAGE TYPE 13", bold=False, key="forme")
    w.subheader(["axe", "fill"], start=2)
    fb = rd["forme_beton"]["type13"]
    vlen, vexpr = metre_core.span("A", "G", "V")
    r = w.line("forme13", axe="A-G", fill=f"{fb['de']}-{fb['a']}", U="M3", N=1,
               I=L(fb["de"], fb["a"], "H"), J=(vlen, vexpr), K=fb["ep"],
               L="JIHK", src="plan (zonage DALLAGE p.6)")
    rr = reg[-1]["row"]
    w.cell(rr, 12, f"=I{rr}*J{rr}")
    w.cell(rr, 13, f"=I{rr}*J{rr}*{fb['ep']}")
    reg[-1]["qte_m"] = True
    w.section("POUR DALLAGE TYPE 20", bold=False, key="forme")
    w.subheader(["axe", "fill"], start=2)
    fb = rd["forme_beton"]["type20"]
    r = w.line("forme20", axe="A-G", fill=f"{fb['de']}-{fb['a']}", U="M3", N=1,
               I=L(fb["de"], fb["a"], "H"), J=(vlen, vexpr), K=fb["ep"],
               L="JIHK", src="plan (zonage DALLAGE p.6)")
    rr = reg[-1]["row"]
    w.cell(rr, 12, f"=I{rr}*J{rr}")
    w.cell(rr, 13, f"=I{rr}*J{rr}*{fb['ep']}")
    w.cell(rr, 14, f"=I{rr}*J{rr}*{fb['extra']}")
    return {"n13_row": rn}


# ---------------------------------------------------------------------------
# Feuille 2 : Armatures
# ---------------------------------------------------------------------------

ARM_COLS = list(range(11, 20))  # K..S diamètres 6..32

def arm_if(w, r, diam):
    """Colonnes K..S : =IF(I{r}=d, G*H*J, "")"""
    for c, d in zip(ARM_COLS, [6, 8, 10, 12, 14, 16, 20, 25, 32]):
        w.cell(r, c, f'=IF(I{r}={d},G{r}*H{r}*J{r},"")')


def build_armatures(w, cfg, rd, fond_sheet_rows):
    reg = w.registry
    cat = cfg["catalogues"]
    fer = cfg["ferraillage"]
    T20, T76 = cfg["parametres"]["T20"], cfg["parametres"]["T76"]

    w.header()
    w.poste("21", "Armature pour béton armé en fondation et en élévation")
    w.section("semelle isolee", bold=False)
    counts = {}
    for axe, st in rd["semelles"].items():
        counts[st] = counts.get(st, 0) + 1
    first = None
    for st in ["S1", "S2", "S3", "S4", "S5"]:
        if st not in counts:
            continue
        c = cat["semelles"][st]
        for axay, dim, bars in (("ax", "A", c["fx"]), ("ay", "B", c["fy"])):
            r = w.next()
            w.cell(r, 1, axay)
            w.cell(r, 7, counts[st])
            w.cell(r, 8, bars[0])
            w.cell(r, 9, bars[1])
            w.cell(r, 10, f"={c[dim]}-0.05+34*I{r}/1000")
            arm_if(w, r, bars[1])
            reg.append({"poste": "21", "section": "semelle isolee", "key": f"arm_{st}_{axay}",
                        "repere": st, "axe": axay, "fill": None, "nom": None,
                        "N": counts[st], "row": r, "src": "tableau p.4",
                        "I": bars[1], "J": None, "K": None, "note": None})
            first = first or r
    w.total("total", first, reg[-1]["row"])

    w.section("fût poteau", bold=False)
    rT = w.next()
    w.cell(rT, 20, T20)
    w.cell(rT - 0, 20, T20)
    tcell = f"$T${rT}"
    first = None
    pcounts = {}
    for axe, pt in rd["poteaux"].items():
        pcounts[pt] = pcounts.get(pt, 0) + 1
    for pt in ["P1", "P2", "P3", "P4"]:
        if pt not in pcounts:
            continue
        c = cat["poteaux"][pt]
        r = w.next()
        w.cell(r, 5, pt)
        arm_if(w, r, 14)
        reg.append({"poste": "21", "section": "fût poteau", "key": f"arm_{pt}",
                    "repere": pt, "axe": None, "fill": None, "nom": None,
                    "N": pcounts[pt], "row": r, "src": "plan",
                    "I": None, "J": None, "K": None, "note": None})
        first = first or r
        bars = fer["fut_poteau"]["long_bars_P123"] if pt != "P4" else fer["fut_poteau"]["long_bars_P4"]
        for nb in bars:
            r = w.next()
            w.cell(r, 1, "ARM LONG ")
            w.cell(r, 7, pcounts[pt])
            w.cell(r, 8, nb)
            w.cell(r, 9, 14)
            w.cell(r, 10, f"=({tcell}-0.1-0.05)+70*I{r}/1000+18*I{r}/1000")
            arm_if(w, r, 14)
        r = w.next()
        w.cell(r, 1, "CADRE")
        w.cell(r, 7, pcounts[pt])
        w.cell(r, 8, f"=ROUNDUP(1.2/{fer['fut_poteau']['esp_cadre']},0)+2")
        w.cell(r, 9, fer["fut_poteau"]["diam_cadre"])
        w.cell(r, 10, f"=(2*({c['b']}+{c['h']})-0.05+20.5*I{r}/1000)")
        arm_if(w, r, 6)
        r = w.next()
        w.cell(r, 1, "EPINGLE")
        w.cell(r, 7, pcounts[pt])
        w.cell(r, 8, f"=ROUNDUP(1.2/{fer['fut_poteau']['esp_cadre']},0)+2")
        w.cell(r, 9, fer["fut_poteau"]["diam_cadre"])
        w.cell(r, 10, f"={c['b']}-0.05+22*I{r}/1000")
        arm_if(w, r, 6)
    w.total("total", first, reg[-1]["row"])

    # longueurs totales CH / LG1 / LG2 (références vers la feuille fondation)
    def sum_ref(keys):
        cells = [f"'Detail quantitatif fondation'!I{e['row']}" for e in fond_sheet_rows
                 if e["key"] in keys]
        return "=" + "+".join(cells)

    ch_keys = {e["key"] for e in fond_sheet_rows if e["key"].startswith("ba_ch_")}
    lg1_keys = {e["key"] for e in fond_sheet_rows if e["key"].startswith("ba_lg_")
                and "LG2" not in str(e["nom"])}
    lg2_keys = {e["key"] for e in fond_sheet_rows if e["key"].startswith("ba_lg_")
                and "LG2" in str(e["nom"])}

    w.section("chainage ", bold=False)
    r = w.next()
    w.cell(r, 4, sum_ref(ch_keys))
    w.cell(r, 5, 0.4)
    w.cell(r, 6, 0.2)
    ch_hdr = r
    for lbl, h_formula, i_d, j_formula in (
            ("ARM LONG ", None, 10, f"=D{ch_hdr}+ROUNDUP(D{ch_hdr}/12,0)"),
            ("CADRE", f"=ROUNDUP((J{ch_hdr+1}-0.3*(12+7+4))/0.2,0)", 6,
             f"=2*(E{ch_hdr}+F{ch_hdr})-0.05+20.5*I{r+2}/1000"),
            ("EPINGLE ", None, 6, f"=F{ch_hdr}-0.05+22*I{{r}}/1000")):
        r = w.next()
        w.cell(r, 1, lbl)
        w.cell(r, 7, 1)
        if h_formula:
            w.cell(r, 8, h_formula)
        else:
            w.cell(r, 8, 6)
        w.cell(r, 9, i_d)
        w.cell(r, 10, j_formula.replace("{r}", str(r)))
        arm_if(w, r, i_d)

    for nom_lg, keys, F in (("LG1", lg1_keys, 0.5), ("LG2", lg2_keys, 0.4)):
        w.section("LONGRINE " + nom_lg, bold=False)
        r = w.next()
        w.cell(r, 1, nom_lg)
        w.cell(r, 4, sum_ref(keys))
        w.cell(r, 5, 0.2)
        w.cell(r, 6, F)
        hdr = r
        sup = fer["longrine"]["nappe_sup"]
        inf = fer["longrine"]["nappe_inf"]
        for lbl, bars, jf in (("ARM LONG SUPP", sup, f"=D{hdr}"),
                              ("ARM LONG INF", inf, f"=D{hdr}"),
                              ("CADRE", [None], f"=2*(E{hdr}+F{hdr})-0.05+20.5*I{{r}}/1000"),
                              ("EPINGLE", [None], f"=F{hdr}-0.05+22*I{{r}}/1000")):
            r = w.next()
            w.cell(r, 1, lbl)
            w.cell(r, 7, 1)
            if lbl.startswith("ARM"):
                w.cell(r, 8, bars[0])
                w.cell(r, 9, bars[1])
                w.cell(r, 10, jf)
            else:
                w.cell(r, 8, f"=ROUNDUP(D{hdr}/0.2,0)")
                w.cell(r, 9, 6)
                w.cell(r, 10, jf.replace("{r}", str(r)))
            arm_if(w, r, bars[1] if lbl.startswith("ARM") else 6)

    w.section("NAPPE DU DALLAGE ", bold=False)
    first = None
    for nom, dk, n in (("DALLAGE TYPE 13CM", "type13", 1), ("DALLAGE TYPE 20CM", "type20", 2)):
        d = fer["dallage"][dk]
        r = w.next()
        w.cell(r, 1, nom)
        w.cell(r, 5, d["Lx"])
        w.cell(r, 6, d["Ly"])
        arm_if(w, r, 8)
        hdr = r
        reg.append({"poste": "21", "section": "NAPPE DU DALLAGE", "key": f"arm_dallage_{dk}",
                    "repere": nom, "axe": None, "fill": None, "nom": None,
                    "N": n, "row": r, "src": "référence (zonage dallage)",
                    "I": 8, "J": None, "K": None, "note": None})
        first = first or r
        for axay, dim, plus in (("AX", "Lx", 0), ("AY", "Ly", 1)):
            r = w.next()
            w.cell(r, 1, axay)
            w.cell(r, 7, n)
            w.cell(r, 8, f"=ROUNDUP(E{hdr}/0.15,0)" if axay == "AX"
                   else f"=ROUNDUP(F{hdr}/0.15,0)")
            w.cell(r, 9, d["diam"])
            w.cell(r, 10, f"={d[dim]}" + (f"+{plus}" if plus else ""))
            arm_if(w, r, d["diam"])
    w.total("total", first, reg[-1]["row"])

    # ---- rollup poids acier -------------------------------------------------
    r = w.next()
    w.cell(r, 7, " LONGUEUR  TOTALE", bold=True)
    for c in ARM_COLS:
        cl = get_column_letter(c)
        w.cell(r, c, f"=SUM({cl}{first}:{cl}{reg[-1]['row']})", bold=True)
    r = w.next()
    w.cell(r, 7, " POIDS / ML", bold=True)
    for c, d in zip(ARM_COLS, [6, 8, 10, 12, 14, 16, 20, 25, 32]):
        w.cell(r, c, f"={d}*{d}/162", bold=True)
    r_pml = r
    r = w.next()
    w.cell(r, 7, " POIDS PARTIELS", bold=True)
    for c in ARM_COLS:
        cl = get_column_letter(c)
        w.cell(r, c, f"={cl}{r_pml}*{cl}{r_pml-1}", bold=True)
    r_pp = r
    r = w.next()
    w.cell(r, 7, " POIDS TOTAL (kg)", bold=True)
    w.cell(r, 11, f"=SUM(K{r_pp}:S{r_pp})", bold=True, fill=TOTAL_FILL)
    return r_pp


# ---------------------------------------------------------------------------
# Détail armatures par élément (feuille 2, suite)
# ---------------------------------------------------------------------------

def build_armatures_detail(w, cfg, rd, fond_rows):
    reg = w.registry
    cat = cfg["catalogues"]
    fer = cfg["ferraillage"]
    T76 = cfg["parametres"]["T76"]
    w.section("DETAIL PAR ELEMENT", col=1)
    w.section("semelle isolee", bold=False)
    w.subheader(["repère", "axe", "fill", "A", "B", "H"])
    for axe, st in rd["semelles"].items():
        c = cat["semelles"][st]
        r = w.next()
        w.cell(r, 1, st)
        w.cell(r, 2, axe[0])
        w.cell(r, 3, axe[1:])
        w.cell(r, 4, c["A"])
        w.cell(r, 5, c["B"])
        w.cell(r, 6, c["H"])
        for axay, dim, bars in (("Armature INF X", "B", c["fx"]),
                                ("Armature INF Y", "A", c["fy"])):
            rr = w.next()
            w.cell(rr, 1, axay)
            w.cell(rr, 7, 1)
            w.cell(rr, 8, bars[0])
            w.cell(rr, 9, bars[1])
            w.cell(rr, 10, f"=({c[dim]}-0.05)+34*I{rr}/1000")
            arm_if(w, rr, bars[1])
            reg.append({"poste": "21", "section": "détail semelles", "key": f"armd_{st}_{axe}",
                        "repere": st, "axe": axe, "fill": None, "nom": axay,
                        "N": 1, "row": rr, "src": "tableau p.4",
                        "I": bars[1], "J": None, "K": None, "note": None})

    w.section("fût des poteaux", bold=False)
    rT = w.next()
    w.cell(rT, 20, T76)
    tcell = f"$T${rT}"
    w.subheader(["axe", "fill", "Nom", "b", "h"])
    for axe, pt in rd["poteaux"].items():
        c = cat["poteaux"][pt]
        r = w.next()
        w.cell(r, 2, axe[0])
        w.cell(r, 3, axe[1:])
        w.cell(r, 4, pt)
        w.cell(r, 5, c["b"])
        w.cell(r, 6, c["h"])
        bars = fer["fut_poteau"]["long_bars_P123"] if pt != "P4" else fer["fut_poteau"]["long_bars_P4"]
        for nb in bars:
            rr = w.next()
            w.cell(rr, 1, "Armature LONG")
            w.cell(rr, 7, 1)
            w.cell(rr, 8, nb)
            w.cell(rr, 9, 14)
            w.cell(rr, 10, f"={tcell}+18*I{rr}/1000")
            arm_if(w, rr, 14)
            reg.append({"poste": "21", "section": "détail fûts", "key": f"armd_fut_{axe}",
                        "repere": pt, "axe": axe, "fill": None, "nom": None,
                        "N": 1, "row": rr, "src": "plan",
                        "I": 14, "J": None, "K": None, "note": None})
        for lbl, jf, count_h in (
                ("CADRE", f"=2*(E{r}+F{r})+20.5*I{{r}}/1000",
                 f"=ROUNDUP(({tcell}-0.25)/0.15,0)"),
                ("EPINGLE", f"=E{r}+22*I{{r}}/1000",
                 f"=ROUNDUP(({tcell}-0.25)/0.15,0)")):
            rr = w.next()
            w.cell(rr, 1, lbl)
            w.cell(rr, 7, 1)
            w.cell(rr, 8, count_h)
            w.cell(rr, 9, 6)
            w.cell(rr, 10, jf.replace("{r}", str(rr)))
            arm_if(w, rr, 6)

    for titre, entries, E, F, inf_d, sup_d, epingle in (
            ("longrines", "ba_lg_", None, None, 12, 10, False),
            ("chainage", "ba_ch_", 0.4, 0.2, 10, 10, True)):
        w.section(titre, bold=False)
        w.subheader(["axe", "fill", "Nom", "Long", "b", "h"])
        for e in [x for x in fond_rows if x["key"].startswith(entries)
                  and x["poste"] == "20"]:
            r = w.next()
            w.cell(r, 2, e["axe"])
            w.cell(r, 3, e["fill"])
            w.cell(r, 4, e["nom"])
            w.cell(r, 5, f"='Detail quantitatif fondation'!I{e['row']}")
            if E:
                w.cell(r, 6, E)
                w.cell(r, 7, F)
            for lbl, diam, jf in (("NAPPE INF1", inf_d, f"=E{r}+36*I{{r}}/1000"),
                                  ("NAPPE SUP", sup_d, f"=E{r}+36*I{{r}}/1000")):
                rr = w.next()
                w.cell(rr, 1, lbl)
                w.cell(rr, 7, 1)
                w.cell(rr, 8, 3)
                w.cell(rr, 9, diam)
                w.cell(rr, 10, jf.replace("{r}", str(rr)))
                arm_if(w, rr, diam)
                reg.append({"poste": "21", "section": f"détail {titre}",
                            "key": f"armd_{e['key']}_{lbl}", "repere": e["nom"],
                            "axe": e["axe"], "fill": e["fill"], "nom": lbl,
                            "N": 1, "row": rr, "src": "plan",
                            "I": diam, "J": None, "K": None, "note": None})
            if epingle:
                rr = w.next()
                w.cell(rr, 1, "EPINGLE")
                w.cell(rr, 7, 1)
                w.cell(rr, 8, f"=ROUNDUP((E{r}/0.2)+10,0)")
                w.cell(rr, 9, 6)
                w.cell(rr, 10, f"=(G{r}-0.025)+22*I{rr}/1000")
                arm_if(w, rr, 6)
                reg.append({"poste": "21", "section": f"détail {titre}",
                            "key": f"armd_{e['key']}_EP", "repere": e["nom"],
                            "axe": e["axe"], "fill": e["fill"], "nom": "EPINGLE",
                            "N": 1, "row": rr, "src": "plan",
                            "I": 6, "J": None, "K": None, "note": None})


# ---------------------------------------------------------------------------
# Comparaison vs référence
# ---------------------------------------------------------------------------

def resolve(cell, ws, cache):
    """Résout une valeur/formule simple du fichier de référence."""
    if cell is None:
        return None
    if isinstance(cell, (int, float)):
        return float(cell)
    s = str(cell)
    if not s.startswith("="):
        try:
            return float(s)
        except ValueError:
            return s
    if s in cache:
        return cache[s]
    expr = s[1:]
    # références de cellules -> valeurs
    def repl(m):
        col, row = m.group(1), int(m.group(2))
        v = resolve(ws.cell(row=row, column=openpyxl.utils.column_index_from_string(col)).value, ws, cache)
        return str(v if isinstance(v, (int, float)) else 0)
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r"\$?([A-Z]{1,2})\$?(\d+)", repl, expr)
    expr = re.sub(r"SUM\(([A-Z]{1,2})\$?(\d+):([A-Z]{1,2})\$?(\d+)\)",
                  lambda m: str(sum(resolve(ws.cell(row=rr, column=openpyxl.utils.column_index_from_string(m.group(1))).value, ws, cache)
                                    or 0 for rr in range(int(m.group(2)), int(m.group(4)) + 1))), expr)
    expr = re.sub(r"ROUNDUP\(([^,]+),0\)", r"(\1+0.9999)//1", expr)
    try:
        val = eval(expr, {"__builtins__": {}}, {})
        val = float(val)
    except Exception:
        val = None
    cache[s] = val
    return val


def parse_reference(path, sheet="Detail quontitafif fondation"):
    """Extrait les lignes du métré de référence avec normalisation des colonnes
    (l'ordre repère/axe/fill/nom varie selon les sections du fichier original)."""
    wb = openpyxl.load_workbook(path, data_only=False)
    ws = wb[sheet]
    cache = {}
    poste, section = None, None
    lines = []

    for r in range(1, ws.max_row + 1):
        a = ws.cell(row=r, column=1).value
        b = ws.cell(row=r, column=2).value
        c3 = ws.cell(row=r, column=3).value
        g = ws.cell(row=r, column=7).value
        if isinstance(a, (int, float)):
            poste = str(int(a))
        if isinstance(a, str):
            t = a.strip().lower()
            if t.startswith("pour semelle"):
                section = "semelles_prop" if poste == "15" else "semelles_ba"
            elif t.startswith("pour longrines"):
                section = "longrines_prop" if poste == "15" else "longrines_ba"
            elif t.startswith("pour chainage"):
                section = "chainages_prop" if poste == "15" else "chainages_ba"
            elif t.startswith("fût des poteaux"):
                section = "futs"
            elif t.startswith("pour les massifs"):
                section = "massifs"
            elif t == "poteaux":
                section = "poteaux_elev"
            elif t.startswith("poutre mezzanine"):
                section = "poutres_mezz"
            elif t.startswith("poutre ph rdc"):
                section = "poutres_ph"
            elif t.startswith("adduction"):
                section = "remblai_add"
            elif t.startswith("reduire"):
                section = "remblai_red"
        if isinstance(b, str):
            tb = b.strip().lower()
            if tb.startswith("reduire") and poste == "7":
                section = "remblai_red"
            elif tb.startswith("adduction") and poste == "7":
                section = "remblai_add"
        if poste == "16" and isinstance(a, str) and a.strip() != "total":
            section = "gros_beton"
        if poste == "17" and isinstance(b, str) and b == "axe":
            section = "maconnerie"
        if poste == "3" and isinstance(b, str) and b == "axe":
            section = "terrassement"
        if poste == "19":
            section = "forme"

        is_total = isinstance(a, str) and a.strip() == "total"
        massif_row = (section == "massifs" and g not in ("M3", "M2", "f")
                      and ws.cell(row=r, column=9).value is not None)
        no_u_row = (section in ("poutres_mezz", "poutres_ph", "forme")
                    and g not in ("M3", "M2", "f")
                    and ws.cell(row=r, column=9).value is not None
                    and not (isinstance(a, str) and a.strip().lower() in
                             ("axe", "nom", "fill")))
        if ((g in ("M3", "M2", "f") and not is_total) or massif_row or no_u_row):
            rep, axe, fill, nom = a, b, c3, ws.cell(row=r, column=4).value

            def _orient(col_a, col_b):
                """horizontal: axe=lettre, fill='1-2' ; vertical: axe='1', fill='A-D'."""
                ca, cb = str(col_a or ""), str(col_b or "")
                if "-" in cb and re.fullmatch(r"\d", ca):
                    return ca, cb          # déjà axe numéroté / plage lettres
                if "-" in ca and re.fullmatch(r"\d", cb):
                    return cb, ca          # vertical : B contient la plage lettres
                return ca, cb

            if section == "maconnerie":
                if str(fill or "").isdigit() and "-" in str(axe or ""):
                    axe, fill = fill, axe
            if section in ("longrines_prop", "chainages_prop",
                           "longrines_ba", "chainages_ba"):
                axe, fill = _orient(a, b)
                nom, rep = c3, None
            elif section in ("poutres_mezz", "poutres_ph"):
                nom = a
                axe, fill = _orient(b, c3)
                rep = None
            elif section == "massifs":
                nom, axe, fill, rep = "MASSIF", None, None, None
            elif section in ("semelles_prop", "semelles_ba"):
                nom = None  # D/E/F sont des dimensions, pas un nom
            elif section == "remblai_red":
                if isinstance(a, str) and re.match(r"^S\d", a.strip(), re.I):
                    nom = None  # négatif de semelle : même layout que semelles
                elif isinstance(c3, str) and c3 in ("LG", "LG2", "CH"):
                    axe, fill, nom, rep = a, b, c3, None
            if section == "semelles_prop":
                i = resolve(ws.cell(row=r, column=4).value, ws, cache)
                j = resolve(ws.cell(row=r, column=5).value, ws, cache)
            else:
                i = resolve(ws.cell(row=r, column=9).value, ws, cache)
                j = resolve(ws.cell(row=r, column=10).value, ws, cache)
            k = resolve(ws.cell(row=r, column=11).value, ws, cache)
            qcol = 13 if poste == "19" else 12
            q = resolve(ws.cell(row=r, column=qcol).value, ws, cache)
            n = ws.cell(row=r, column=8).value
            lines.append({"poste": str(poste), "section": section, "row": r,
                          "repere": rep if isinstance(rep, str) else None,
                          "axe": axe, "fill": fill, "nom": nom,
                          "N": n, "I": i, "J": j, "K": k, "qte": q})
        if is_total:
            m = resolve(ws.cell(row=r, column=13).value, ws, cache)
            lines.append({"poste": str(poste), "section": section, "row": r,
                          "repere": "total", "axe": None, "fill": None, "nom": None,
                          "N": None, "I": None, "J": None, "K": None, "qte": m})
    return lines


def key_of(l):
    return (str(l["axe"]), str(l["fill"]), str(l["nom"]),
            str(l["repere"]).upper() if l["repere"] else "None")


def build_comparaison(ws, generated, ref_lines, cfg, rd):
    """Comparaison ligne à ligne (sections élémentaires) + totaux par poste."""
    r = 1
    ws.cell(row=r, column=1, value="Comparaison générée vs métré de référence").font = BOLD
    r += 1
    for c, t in [(1, "Poste"), (2, "Section"), (3, "Élément"), (4, "Champ"),
                 (5, "Référence"), (6, "Généré"), (7, "Écart"), (8, "Commentaire")]:
        ws.cell(row=r, column=c, value=t).font = BOLD
    r += 2
    diffs = 0

    def elem_label(l):
        s = f"{l.get('repere') or ''} {l.get('axe') or ''}"
        if l.get("fill") is not None:
            s += f" /{l['fill']}"
        if l.get("nom"):
            s += f" {l['nom']}"
        return s.strip() or f"ligne {l.get('row')}"

    def add_diff(poste, sec, label, champ, rv, gv, note=None):
        nonlocal r
        try:
            delta = round(float(gv) - float(rv), 3)
        except (TypeError, ValueError):
            delta = ""
        for c, v in [(1, poste), (2, sec), (3, label), (4, champ),
                     (5, round(float(rv), 3) if isinstance(rv, (int, float)) else rv),
                     (6, round(float(gv), 3) if isinstance(gv, (int, float)) else gv),
                     (7, delta), (8, note or "")]:
            ws.cell(row=r, column=c, value=v)
        r += 1

    LINE_SECTIONS = ["semelles_prop", "longrines_prop", "chainages_prop",
                     "gros_beton", "maconnerie", "semelles_ba", "longrines_ba",
                     "chainages_ba", "futs", "massifs", "poteaux_elev",
                     "poutres_mezz", "poutres_ph", "terrassement", "remblai_add",
                     "forme"]
    ref_by_sec = {}
    for l in ref_lines:
        if l["repere"] == "total":
            continue
        ref_by_sec.setdefault((l["poste"], l["section"]), []).append(l)

    for sec in LINE_SECTIONS:
        gs = [g for g in generated if g["section"] == sec]
        if not gs:
            continue
        poste = gs[0]["poste"]
        pool = list(ref_by_sec.get((poste, sec), []))
        for g in gs:
            k = key_of(g)
            match = next((x for x in pool if key_of(x) == k), None)
            if match is None:
                k2 = (str(g["axe"]), str(g["fill"]), str(g["nom"]), "None")
                match = next((x for x in pool if key_of(x) == k2), None)
            if match is not None:
                pool.remove(match)
                for champ, gv, rv in (("Longueur", g["I"], match["I"]),
                                      ("largeur", g["J"], match["J"]),
                                      ("Hauteur", g["K"], match["K"]),
                                      ("N", g["N"], match["N"]),
                                      ("Qté", g.get("qte"), match["qte"])):
                    if gv is None or rv is None:
                        continue
                    try:
                        if abs(float(gv) - float(rv)) > 1e-6:
                            diffs += 1
                            add_diff(poste, sec, elem_label(g), champ, rv, gv,
                                     g.get("note"))
                    except (TypeError, ValueError):
                        pass
            else:
                diffs += 1
                add_diff(poste, sec, elem_label(g), "LIGNE", "absente (réf.)",
                         "ajoutée (générée)", g.get("note")
                         or "présente sur le plan / absente du métré de référence")
        for x in pool:
            diffs += 1
            add_diff(poste, sec, elem_label(x), "LIGNE", "présente (réf.)",
                     "non reproduite", "du métré de référence — voir rapport")

    # totaux par poste
    r += 1
    ws.cell(row=r, column=1, value="Totaux par poste (m³ / unités)").font = BOLD
    r += 1
    for c, t in [(1, "Poste"), (5, "Référence"), (6, "Généré"), (7, "Écart")]:
        ws.cell(row=r, column=c, value=t).font = BOLD
    r += 1
    gen_tot = {}
    for g in generated:
        try:
            gen_tot[g["poste"]] = gen_tot.get(g["poste"], 0) + float(g.get("qte") or 0)
        except (TypeError, ValueError):
            pass
    ref_tot = {}
    for l in ref_lines:
        if l["repere"] == "total" and isinstance(l.get("qte"), (int, float)):
            ref_tot[l["poste"]] = ref_tot.get(l["poste"], 0) + l["qte"]
    for p in sorted(set(list(gen_tot) + list(ref_tot)), key=lambda x: str(x)):
        gv, rv = gen_tot.get(p), ref_tot.get(p)
        ws.cell(row=r, column=1, value=p)
        ws.cell(row=r, column=5, value=round(rv, 2) if isinstance(rv, (int, float)) else "—")
        ws.cell(row=r, column=6, value=round(gv, 2) if isinstance(gv, (int, float)) else "—")
        if isinstance(gv, (int, float)) and isinstance(rv, (int, float)):
            ws.cell(row=r, column=7, value=round(gv - rv, 2))
        r += 1
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="output/plan_data.json")
    ap.add_argument("--config", default="config/postes.yaml")
    ap.add_argument("--readings", default="config/readings_vision.yaml")
    ap.add_argument("--reference", default="reference/metre_MZINDA.xlsx")
    ap.add_argument("--out", default="output/metre_genere.xlsx")
    args = ap.parse_args()

    cfg = metre_core.load_config(args.config)
    rd = metre_core.load_yaml(args.readings)
    plan = json.load(open(args.plan, encoding="utf-8")) if os.path.exists(args.plan) else {}

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Detail quantitatif fondation"
    reg1 = []
    w1 = SheetWriter(ws1, reg1)
    build_fondation(w1, cfg, rd)

    # calcul des quantités générées (valeur attendue des formules)
    for e in reg1:
        try:
            if e["key"].startswith(("forme",)):
                e["qte"] = float(e["I"]) * float(e["J"]) * float(e["K"]) * abs(e["N"])
            else:
                e["qte"] = float(e["I"]) * float(e["J"]) * float(e["K"]) * float(e["N"] or 1)
        except (TypeError, ValueError):
            e["qte"] = None

    ws2 = wb.create_sheet("Armatures")
    reg2 = []
    w2 = SheetWriter(ws2, reg2)
    r_pp = build_armatures(w2, cfg, rd, reg1)
    build_armatures_detail(w2, cfg, rd, reg1)

    widths1 = {1: 7, 2: 34, 3: 10, 4: 8, 5: 8, 6: 8, 7: 6, 8: 6, 9: 10, 10: 9,
               11: 12, 12: 12, 13: 16, 14: 12}
    for c, wd in widths1.items():
        ws1.column_dimensions[get_column_letter(c)].width = wd
    for c, wd in list(widths1.items())[:13]:
        ws2.column_dimensions[get_column_letter(c)].width = wd

    ref_lines = parse_reference(args.reference)
    ws3 = wb.create_sheet("Comparaison")
    diffs = build_comparaison(ws3, reg1, ref_lines, cfg, rd)
    ws3.column_dimensions["A"].width = 8
    for c in "BCDEFG":
        ws3.column_dimensions[c].width = 22
    ws3.column_dimensions["H"].width = 60

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    wb.save(args.out)

    # ---- exports pour le rapport PDF et l'optimisation ----------------------
    summary = {"vols": {}, "acier": {}, "totaux_poste": {}, "par_section": {}}
    fam_map = {"semelles_prop": "semelles (propreté)", "semelles_ba": "semelles",
               "longrines_ba": "longrines", "chainages_ba": "chaînages",
               "futs": "fûts", "poteaux_elev": "poteaux élévation",
               "poutres_mezz": "poutres mezzanine", "poutres_ph": "poutres PH-RDC",
               "massifs": "massifs", "gros_beton": "gros béton",
               "longrines_prop": "longrines (propreté)",
               "chainages_prop": "chaînages (propreté)"}
    for e in reg1:
        p_, s_, q = e["poste"], e["section"], e.get("qte") or 0
        summary["totaux_poste"][p_] = summary["totaux_poste"].get(p_, 0) + q
        key = fam_map.get(s_, s_)
        summary["par_section"].setdefault(key, 0)
        summary["par_section"][key] += q
    summary["vols"] = {
        "BA (poste 20)": summary["totaux_poste"].get("20", 0),
        "gros béton": summary["totaux_poste"].get("16", 0),
        "propreté": summary["totaux_poste"].get("15", 0),
        "terrassement": summary["totaux_poste"].get("3", 0),
        "remblai net": summary["totaux_poste"].get("7", 0),
    }
    # tonnage acier : évaluation des lignes d'armatures (G × H × J par diamètre)
    ws2v = wb["Armatures"]
    acier = {}
    for rr in range(1, ws2v.max_row + 1):
        g_ = ws2v.cell(row=rr, column=7).value
        h_ = ws2v.cell(row=rr, column=8).value
        i_ = ws2v.cell(row=rr, column=9).value
        j_ = ws2v.cell(row=rr, column=10).value
        if isinstance(g_, (int, float)) and isinstance(i_, int) and i_ in (6, 8, 10, 12, 14, 16, 20, 25, 32):
            try:
                jl = float(resolve(j_, ws2v, {})) if isinstance(j_, str) else float(j_ or 0)
                hl = float(h_) if not isinstance(h_, str) else None
                gl = float(g_)
                if hl is not None and isinstance(h_, (int, float)):
                    acier[i_] = acier.get(i_, 0) + gl * hl * jl
            except (TypeError, ValueError):
                pass
    summary["acier"] = {str(k): round(v, 1) for k, v in sorted(acier.items())}
    summary["acier_total_kg"] = round(sum(acier.values()), 1)
    with open("output/metre_lines.json", "w", encoding="utf-8") as f:
        json.dump(reg1, f, ensure_ascii=False, indent=1)
    with open("output/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    # rapport de vérification
    a_verifier = []
    for e in reg1:
        if e.get("note") or (e.get("src") or "").startswith("référence"):
            a_verifier.append(e)
    lines = ["# Rapport de vérification — métré généré", "",
             f"Plan : {plan.get('meta', {}).get('pdf', 'reference/PLAN_BA_final.pdf')}",
             f"Écarts vs référence : {diffs} | éléments à contrôler : {len(a_verifier)}", "",
             "## Éléments signalés (aucun estimé silencieusement)", ""]
    for e in a_verifier:
        lines.append(f"- [{e['poste']}] {e['key']} — {e.get('note') or e.get('src')}")
    lines += ["", "## Vérifications automatiques (extract_plan.py)", ""]
    for c in plan.get("checks", []):
        lines.append(f"- {json.dumps(c, ensure_ascii=False)}")
    os.makedirs("output", exist_ok=True)
    with open("output/rapport_verification.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"lignes fondation : {len(reg1)} | lignes armatures : {len(reg2)}")
    print(f"écarts vs référence : {diffs}")
    print(f"-> {args.out}")
    print("-> output/rapport_verification.md")


if __name__ == "__main__":
    main()



