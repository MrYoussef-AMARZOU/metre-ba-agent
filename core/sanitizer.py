from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional

DEFAULT_A = 1.00
DEFAULT_B = 1.00
DEFAULT_H = 0.30
DEFAULT_PHI = 12
DEFAULT_NB = 1
DEFAULT_AXE = "A"
DEFAULT_FILE = "1"


def clean_cad_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    cleaned = []
    for char in text:
        code = ord(char)
        if code in (9, 10, 13):
            cleaned.append(char)
        elif code < 32 or code == 127:
            cleaned.append(" ")
        else:
            cleaned.append(char)
    result = "".join(cleaned)
    result = result.replace("\u00a0", " ")
    result = re.sub(r"[ \t]+", " ", result)
    return result.strip()


def _parse_number(value: Any, default: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_cad_text(value).replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return default
    try:
        return float(match.group(0))
    except (TypeError, ValueError):
        return default


def _dimension_to_meters(value: Any, default: float) -> float:
    number = _parse_number(value, default)
    if number <= 0:
        return default
    if number > 10:
        return number / 100.0
    return number


def parse_dimensions(
    value: Any,
    default_a: float = DEFAULT_A,
    default_b: float = DEFAULT_B,
    default_h: float = DEFAULT_H,
) -> Dict[str, float]:
    text = clean_cad_text(value).upper().replace("×", "X").replace("*", "X")
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if len(numbers) >= 2:
        a = _dimension_to_meters(numbers[0], default_a)
        b = _dimension_to_meters(numbers[1], default_b)
    else:
        a = default_a
        b = default_b

    if len(numbers) >= 3:
        h = _dimension_to_meters(numbers[2], default_h)
    else:
        h = default_h

    return {"a": round(a, 6), "b": round(b, 6), "h": round(h, 6)}


def parse_rebar(
    value: Any,
    default_nb: int = DEFAULT_NB,
    default_phi: int = DEFAULT_PHI,
) -> Dict[str, int]:
    text = clean_cad_text(value).upper().replace(",", ".")
    match = re.search(r"(?:(\d+)\s*)?(?:HA|T|TOR|Ø|PHI)?\s*(\d{1,2})\b", text)
    if not match:
        return {"nb": default_nb, "phi": default_phi}
    raw_nb, raw_phi = match.groups()
    try:
        nb = int(raw_nb) if raw_nb else default_nb
    except (TypeError, ValueError):
        nb = default_nb
    try:
        phi = int(raw_phi)
    except (TypeError, ValueError):
        phi = default_phi

    return {"nb": max(nb, 1), "phi": max(phi, 6)}


def parse_spacing(value: Any, default: float = 15.0) -> float:
    text = clean_cad_text(value).upper()
    match = re.search(r"(?:E|ESP|@)\s*[=:]?\s*(\d+(?:[.,]\d+)?)", text)
    if not match:
        return default
    try:
        spacing = float(match.group(1).replace(",", "."))
        return spacing if spacing > 0 else default
    except (TypeError, ValueError):
        return default


def sanitize_element(element: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = dict(element or {})
    dim_source = (
        source.get("dimensions") or source.get("dimension") or source.get("section")
        or source.get("cote") or source.get("description") or ""
    )
    parsed_dim = parse_dimensions(
        dim_source,
        default_a=_parse_number(source.get("a"), DEFAULT_A),
        default_b=_parse_number(source.get("b"), DEFAULT_B),
        default_h=_parse_number(source.get("h"), DEFAULT_H),
    )
    rebar_source = (
        source.get("ferraillage") or source.get("armatures") or source.get("rebar")
        or source.get("acier") or source.get("description") or ""
    )
    parsed_rebar = parse_rebar(
        rebar_source,
        default_nb=int(_parse_number(source.get("nb"), DEFAULT_NB)),
        default_phi=int(_parse_number(source.get("phi"), DEFAULT_PHI)),
    )
    el_type = clean_cad_text(source.get("type") or source.get("nature") or "ELEMENT").upper()
    axe = clean_cad_text(source.get("axe") or DEFAULT_AXE)
    file_num = clean_cad_text(source.get("file") or DEFAULT_FILE)

    result = dict(source)
    result.update(parsed_dim)
    result.update(parsed_rebar)
    result["type"] = el_type
    result["axe"] = axe or DEFAULT_AXE
    result["file"] = file_num or DEFAULT_FILE
    result["espacement"] = parse_spacing(source.get("espacement") or "", default=15.0)
    result["a"] = max(float(result["a"]), 0.001)
    result["b"] = max(float(result["b"]), 0.001)
    result["h"] = max(float(result["h"]), 0.001)
    result["nb"] = max(int(result["nb"]), 1)
    result["phi"] = max(int(result["phi"]), 6)
    return result


def sanitize_elements(elements: Any) -> list[Dict[str, Any]]:
    if not elements:
        return []
    if isinstance(elements, dict):
        elements = [elements]
    return [sanitize_element(item if isinstance(item, dict) else {"description": item}) for item in elements]


def safe_get(element: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    if not isinstance(element, dict):
        return default
    val = element.get(key, default)
    return default if val is None else val