import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalization import normalize_plan_data


def test_normalization_common_contract():
    data = {
        "catalogue_types": {
            "semelles": {
                "S1": {
                    "a": 1.2, "b": 1.2, "h": 0.3,
                    "ferr_x": {"nb": 8, "phi": 12},
                    "ferr_y": {"nb": 8, "phi": 12},
                }
            }
        },
        "implantations": {
            "semelles": [{"id": "S1_1", "type": "S1", "axe": "A", "file": "1"}]
        },
        "_meta": {
            "moteur": "synthetic",
            "semelles_pages": {"S1": [2]},
            "avertissements": ["test"],
            "hypotheses": [],
        },
    }
    result = normalize_plan_data(data)
    element = result["elements"][0]
    assert element["family"] == "SEMELLE"
    assert element["section_m"] == {"a": 1.2, "b": 1.2, "h": 0.3}
    assert len(element["reinforcement"]) == 2
    assert element["source"]["pages"] == [2]
    assert element["confidence"] == "high"
    assert result["units"]["diameter"] == "mm"


def test_normalization_marks_partial_geometry():
    data = {
        "catalogue_types": {"semelles": {"SEMELLE_DEFAULT": {
            "a": 1.0, "b": 1.0, "h": 0.3, "dimensions_par_defaut": True}}},
        "implantations": {"semelles": [{"type": "SEMELLE_DEFAULT",
                                         "position_par_defaut": True}]},
        "_meta": {"avertissements": ["missing"]},
    }
    element = normalize_plan_data(data)["elements"][0]
    assert element["confidence"] == "low"
    assert element["warnings"]
