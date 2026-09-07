"""Tokenisation tolérante des étiquettes CAO/OCR composites."""
from __future__ import annotations

import re
from typing import Iterable

_LABEL = re.compile(r"^(S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*))$", re.I)
_DIM = re.compile(r"^\(?\d{2,3}\s*[xX*]\s*\d{2,3}\)?$")
_REBAR = re.compile(r"^\d+\s*(?:HA|T)\s*\d+(?:\+\d+\s*(?:HA|T)\s*\d+)*$", re.I)
_COMPOSITE = re.compile(
    r"^((?:S\d+|[PQ]\d+|(?:B?N\d+(?:BIS)?|PN\d+|LG\d+|CH\d*)))"
    r"(\(\d{2,3}\s*[xX*]\s*\d{2,3}(?:\s*[xX*]\s*\d{2,3})?\))?"
    r"((?:\d+\s*(?:HA|T)\s*\d+(?:\+\d+\s*(?:HA|T)\s*\d+)*)?)$",
    re.I,
)


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
