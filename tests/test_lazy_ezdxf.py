#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_lazy_ezdxf.py -- Import paresseux d'ezdxf (crash numpy dans l'exe).

Le module core.validator ne doit JAMAIS importer ezdxf au niveau global :
ezdxf tire numpy a l'import, ce qui cassait l'analyse PDF dans l'exe.
"""
import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestLazyEzdxf(unittest.TestCase):
    def _top_level_imports(self, relpath):
        path = os.path.join(ROOT, relpath)
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names = []
        for node in tree.body:  # niveau module uniquement
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
        return names

    def test_validator_pas_ezdxf_global(self):
        names = self._top_level_imports(os.path.join("core", "validator.py"))
        self.assertNotIn("ezdxf", names)

    def test_ingestion_pas_ezdxf_global(self):
        names = self._top_level_imports(os.path.join("core", "ingestion.py"))
        self.assertNotIn("ezdxf", names)

    def test_validator_pdf_charge_pas_ezdxf(self):
        """Analyser un PDF ne doit pas charger ezdxf dans sys.modules."""
        # Purger l'etat pour un test deterministe
        for mod in ("ezdxf", "numpy"):
            sys.modules.pop(mod, None)
        from core.validator import PlanSanityValidator
        import fitz
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "plan.pdf")
            doc = fitz.open()
            page = doc.new_page(width=1191, height=842)
            page.insert_text((600, 125), "1")
            page.insert_text((100, 135), "S1(120x120x30)")
            doc.save(pdf)
            doc.close()
            ok, _, _ = PlanSanityValidator.validate_file(pdf)
            self.assertTrue(ok)
        self.assertNotIn("ezdxf", sys.modules)
        self.assertNotIn("numpy", sys.modules)

    def test_validator_dxf_fonctionne(self):
        """Le chemin DXF charge ezdxf a la demande et fonctionne toujours."""
        import ezdxf
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dxf = os.path.join(td, "plan.dxf")
            doc = ezdxf.new("R12")
            msp = doc.modelspace()
            for i in range(25):
                msp.add_line((i, 0), (i + 10, 15))
            doc.saveas(dxf)

            from core.validator import PlanSanityValidator
            ok, msg, score = PlanSanityValidator.validate_file(dxf)
            self.assertTrue(ok)
            self.assertEqual(score, 95)
            self.assertIn("entités DAO", msg)


if __name__ == "__main__":
    unittest.main()
