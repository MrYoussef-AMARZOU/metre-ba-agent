"""Utilitaires partagés : géométrie de la grille et calcul des longueurs d'axe."""
import yaml, re, functools

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_config(cfg_path="config/postes.yaml"):
    return load_yaml(cfg_path)

@functools.lru_cache(maxsize=8)
def _units(cfg_path):
    cfg = load_config(cfg_path)
    hor = cfg["geometrie"]["horizontal"]
    ver = cfg["geometrie"]["vertical"]
    # segments unitaires (les clés "2-4" cotées d'un bloc restent des unités
    # lorsque le plan les cote d'un seul tenant ; 2-3 / 3-4 servent aux
    # décompositions explicites du plan)
    h_units = {("1-2"): hor["1-2"], ("2-3"): hor["2-3"], ("3-4"): hor["3-4"],
               ("4-5"): hor["4-5"], ("5-6"): hor["5-6"], ("6-7"): hor["6-7"],
               ("7-8"): hor["7-8"]}
    h_named = {"2-4": hor["2-4"]}   # coté d'un seul tenant sur le plan
    v_units = {f"{c}-{d}": ver[f"{c}-{d}"] for c, d in zip("ABCDEFG", "BCDEFG")}
    return h_units, h_named, v_units

def _axis_list(orient):
    return "12345678" if orient == "H" else "ABCDEFG"

def _key(a, b):
    return f"{a}-{b}"

def span(a, b, orient, cfg_path="config/postes.yaml"):
    """Longueur entre deux axes consécutifs ou non.
    Retourne (valeur, expression) : expression = formule Excel sans '='
    reprenant les segments, ou None si valeur directe cotée sur le plan."""
    h_units, h_named, v_units = _units(cfg_path)
    units = h_units if orient == "H" else v_units
    named = h_named if orient == "H" else {}
    seq = _axis_list(orient)
    ia, ib = seq.index(str(a)), seq.index(str(b))
    if ib < ia:
        a, b, ia, ib = b, a, ib, ia
    k = _key(a, b)
    if k in named:
        return named[k], None
    if k in units:
        return units[k], None
    # combinaison : somme des segments unitaires entre a et b
    parts, total = [], 0.0
    for i in range(ia, ib):
        ka = _key(seq[i], seq[i + 1])
        v = units[ka]
        parts.append(str(v))
        total += v
    return round(total, 4), "+".join(parts)

def run_length(de, a, orient, cfg_path="config/postes.yaml"):
    """Longueur d'un élément allant de l'axe `de` à l'axe `a`.
    (de, a) peuvent être '1-2' (déjà une travée) ou des axes simples."""
    if isinstance(de, str) and "-" in str(de):
        k = de
        h_units, h_named, v_units = _units(cfg_path)
        if orient == "H":
            if k in h_named:
                return h_named[k], None
            if k in h_units:
                return h_units[k], None
        else:
            if k in v_units:
                return v_units[k], None
    return span(de, a, orient, cfg_path)

REP_RX = re.compile(r"^S(\d)$", re.I)

def semelle_key(axe, fill):
    return f"{axe}{fill}"
