"""Tokenisation tolérante des étiquettes CAO/OCR composites."""
from __future__ import annotations

import re
from typing import Any, Iterable

_LABEL = re.compile(r"^(S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*))$", re.I)
_DIM = re.compile(r"^\(?\d{2,3}\s*[xX*]\s*\d{2,3}\)?$")
_REBAR = re.compile(r"^\d+\s*(?:HA|T)\s*\d+(?:\+\d+\s*(?:HA|T)\s*\d+)*$", re.I)
_COMPOSITE = re.compile(
    r"^((?:S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*)))"
    r"(\(\d{2,3}\s*[xX*]\s*\d{2,3}(?:\s*[xX*]\s*\d{2,3})?\))?"
    r"((?:\d+\s*(?:HA|T)\s*\d+(?:\+\d+\s*(?:HA|T)\s*\d+)*)?)$",
    re.I,
)
_REFERENCE = re.compile(
    r"^(?P<reference>S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*))$",
    re.I,
)
_DIMENSIONS = re.compile(
    r"(?P<a>\d+(?:[.,]\d+)?)\s*[xX*]\s*"
    r"(?P<b>\d+(?:[.,]\d+)?)"
    r"(?:\s*[xX*]\s*(?P<h>\d+(?:[.,]\d+)?))?"
)
_REINFORCEMENT = re.compile(
    r"(?P<nb>\d+)\s*(?P<kind>HA|T|TOR|Ø|PHI)\s*(?P<phi>\d{1,2})",
    re.I,
)


def _metres(value: str) -> float:
    number = float(value.replace(",", "."))
    return number / 100.0 if number > 10 else number


def decompose_etiquette_technique(texte: Any) -> dict:
    """Décompose une étiquette BA et reste tolérant aux variantes OCR/CAO.

    Le résultat conserve la compatibilité historique (`repere`, `a`, `b`,
    `h`, `ferr_x`) et expose le contrat commun (`reference`, `family`,
    `dimensions_m`, `reinforcement`).
    """
    text = str(texte or "").replace("×", "x").replace("*", "x").strip()
    compact = re.sub(r"\s+", " ", text)
    ref_match = re.search(r"\b(S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*))\b",
                          compact, re.I)
    reference = ref_match.group(1).upper() if ref_match else ""
    if reference.startswith("S"):
        family = "SEMELLE"
    elif reference.startswith(("P", "Q")):
        family = "POTEAU"
    elif reference:
        family = "POUTRE"
    else:
        family = "INCONNU"
    dims_match = _DIMENSIONS.search(compact)
    dimensions = {}
    if dims_match:
        dimensions = {
            key: _metres(value)
            for key, value in (
                ("a", dims_match.group("a")),
                ("b", dims_match.group("b")),
                ("h", dims_match.group("h")),
            ) if value is not None
        }
    bars = []
    for match in _REINFORCEMENT.finditer(compact):
        bars.append({
            "count": int(match.group("nb")),
            "diameter_mm": int(match.group("phi")),
            "type": match.group("kind").upper(),
            "role": "nappe_x" if family == "SEMELLE" else "longitudinal",
            "unit": "mm",
        })
    result = {
        "reference": reference,
        "repere": reference,
        "family": family,
        "dimensions_m": dimensions,
        "reinforcement": bars,
        "warnings": [],
    }
    if bars and family == "SEMELLE":
        result["ferr_x"] = {"nb": bars[0]["count"], "phi": bars[0]["diameter_mm"]}
    result.update(dimensions)
    return result


def tokenize_composite(text: object) -> list[str]:
    """Retourne les sous-étiquettes d'un mot OCR sans perdre sa forme utile."""
    value = str(text or "").strip()
    if not value:
        return []
    normalized = value.replace("×", "x").replace("*", "x")
    if _DIM.match(normalized) or _REBAR.match(normalized):
        return [normalized]
    compact = normalized.replace(" ", "")
    composite = _COMPOSITE.match(compact)
    if composite and (composite.group(2) or composite.group(3)):
        if composite.group(1).upper().startswith("S") and composite.group(2):
            if composite.group(2).count("x") == 2:
                return [normalized]
        return [part for part in (
            composite.group(1).upper(), composite.group(2), composite.group(3)
        ) if part]
    if _LABEL.match(compact):
        return [compact.upper()]
    parts = [part for part in re.split(r"[/,;+\-]+", compact) if part]
    labels = [part.upper() for part in parts if _LABEL.match(part)]
    if labels and len(labels) == len(parts):
        return labels
    return [normalized]


def expand_words(words: Iterable[dict]) -> list[dict]:
    """Duplique les étiquettes composites en conservant leur géométrie."""
    expanded = []
    for word in words:
        tokens = tokenize_composite(word.get("text"))
        if not tokens:
            continue
        for index, token in enumerate(tokens):
            item = dict(word)
            item["text"] = token
            item["composite"] = len(tokens) > 1
            if len(tokens) > 1:
                item["x"] = float(word.get("x", 0)) + index * 0.1
                item["x1"] = float(word.get("x1", word.get("x", 0))) + index * 0.1
            expanded.append(item)
    return expanded
