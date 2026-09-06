#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_ui_sync.py -- Synchronisation variable fichier <-> UI.

Verifie que self.selected_file_path est la source de verite unique :
  - defini par _on_file_selected (parcourir / depot)
  - synchro avec l'etat du bouton d'analyse
  - lu directement par _run_analysis et passe en argument au worker

Note : une seule instance Tk est creee (re-utilisee masquee) car tkinter
ne supporte pas plusieurs roots successifs dans un meme processus.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REF_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reference", "PLAN_BA_final.pdf")

_APP = None


def _get_app():
    """Instance Tk unique, masquee, avec etat reinitialise entre les tests."""
    global _APP
    if _APP is None:
        from ui.desktop_app import PlanBAMetreApp
        _APP = PlanBAMetreApp()
        _APP.withdraw()
    _reset_app(_APP)
    return _APP


def _reset_app(app):
    app.selected_file_path = None
    app.plan_data = None
    app.btn_action.configure(state="disabled")
    app.drop_zone._reset_validation()


@unittest.skipUnless(os.path.exists(REF_PDF), "PDF de reference absent")
class TestUiFileSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = _get_app()

    def setUp(self):
        # Etat reinitialise pour chaque test (ordre alphabetique pytest)
        _reset_app(self.app)

    def test_init_selected_file_path_none(self):
        self.assertIsNone(self.app.selected_file_path)
        self.assertEqual(str(self.app.btn_action.cget("state")), "disabled")

    def test_valid_file_sets_path_and_enables_button(self):
        self.app._on_file_selected(REF_PDF)
        self.assertEqual(self.app.selected_file_path,
                         os.path.abspath(REF_PDF))
        self.assertEqual(str(self.app.btn_action.cget("state")), "normal")

    def test_rejected_file_clears_path_and_disables_button(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt",
                                         delete=False) as tmp:
            tmp.write(b"facture")
            fake = tmp.name
        self.addCleanup(lambda: os.path.exists(fake) and os.remove(fake))

        self.app._on_file_selected(fake)
        self.assertIsNone(self.app.selected_file_path)
        self.assertEqual(str(self.app.btn_action.cget("state")), "disabled")

    def test_nonexistent_file_rejected(self):
        self.app._on_file_selected("Z:/inexistant/plan.pdf")
        self.assertIsNone(self.app.selected_file_path)
        self.assertEqual(str(self.app.btn_action.cget("state")), "disabled")

    def test_run_analysis_blocked_without_file(self):
        errors = []
        self.app._show_error = lambda msg: errors.append(msg)
        self.app.selected_file_path = None
        self.app._run_analysis()
        self.assertEqual(errors, ["Veuillez sélectionner un fichier d'abord."])

    def test_run_analysis_passes_path_as_arg_to_worker(self):
        """Le chemin est fige en argument du thread (etat partage evite)."""
        self.app._on_file_selected(REF_PDF)

        captured = {}

        class DummyThread:
            def __init__(self, target=None, args=(), daemon=None):
                captured["target"] = target
                captured["args"] = args

            def start(self):
                captured["started"] = True

        with patch("ui.desktop_app.threading.Thread", DummyThread):
            self.app._run_analysis()

        self.assertTrue(captured.get("started"))
        self.assertEqual(captured["args"],
                         (os.path.abspath(REF_PDF),))

    def test_reselect_rejected_after_valid_resets_state(self):
        """Valide puis refuse -> la variable doit revenir a None."""
        self.app._on_file_selected(REF_PDF)
        self.assertIsNotNone(self.app.selected_file_path)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt",
                                         delete=False) as tmp:
            tmp.write(b"x")
            fake = tmp.name
        self.addCleanup(lambda: os.path.exists(fake) and os.remove(fake))

        self.app._on_file_selected(fake)
        self.assertIsNone(self.app.selected_file_path)
        self.assertEqual(str(self.app.btn_action.cget("state")), "disabled")

    # -- Nettoyage des chemins Drag & Drop / Windows --------------------

    def test_path_with_braces_cleaned(self):
        """Format TkinterDnD : {C:/.../PLAN BA final.pdf}"""
        from ui.desktop_app import clean_dropped_path
        wrapped = "{" + REF_PDF + "}"
        self.assertEqual(clean_dropped_path(wrapped),
                         os.path.abspath(REF_PDF))

    def test_path_with_quotes_and_spaces_cleaned(self):
        from ui.desktop_app import clean_dropped_path
        quoted = f'"{REF_PDF}"'
        self.assertEqual(clean_dropped_path(quoted), os.path.abspath(REF_PDF))
        self.assertEqual(clean_dropped_path(f"  {REF_PDF}  "),
                         os.path.abspath(REF_PDF))

    def test_multiple_dropped_paths_takes_first(self):
        from ui.desktop_app import clean_dropped_path
        multi = "{" + REF_PDF + "} {C:/autre/plan.pdf}"
        self.assertEqual(clean_dropped_path(multi), os.path.abspath(REF_PDF))

    def test_braced_path_via_callback_enables_button(self):
        """Flux complet : chemin entoure d'accolades -> import OK."""
        self.app._on_file_selected("{" + REF_PDF + "}")
        self.assertEqual(self.app.selected_file_path,
                         os.path.abspath(REF_PDF))
        self.assertEqual(str(self.app.btn_action.cget("state")), "normal")

    # -- Splash screen PyInstaller --------------------------------------

    def test_dismiss_splash_sans_exception(self):
        """_dismiss_splash ne doit jamais planter (pyi_splash absent en dev)."""
        self.app._dismiss_splash()  # no-op en mode script : pas d'erreur

    def test_dismiss_splash_ferme_si_vivant(self):
        """En mode frozen, close() doit etre appele si is_alive()."""
        import types
        fake = types.SimpleNamespace(is_alive=lambda: True,
                                     close=lambda: calls.append(1))
        calls = []
        with patch.dict("sys.modules", {"pyi_splash": fake}):
            self.app._dismiss_splash()
        self.assertEqual(calls, [1])

    def test_splash_planifie_au_demarrage(self):
        """__init__ doit planifier after(200, _dismiss_splash) (filet de securite)."""
        import inspect
        from ui.desktop_app import PlanBAMetreApp
        source = inspect.getsource(PlanBAMetreApp.__init__)
        self.assertIn("after(200, self._dismiss_splash)", source)

    # -- Drag & Drop (tkinterdnd2) --------------------------------------

    def test_tkinterdnd2_disponible(self):
        """tkdnd doit etre charge sur la fenetre (curseur depot autorise)."""
        from ui.desktop_app import TKDND_AVAILABLE
        if not TKDND_AVAILABLE:
            self.skipTest("tkinterdnd2 non installe")
        # _require a ete appele : TkdndVersion renseigne sur la fenetre
        self.assertTrue(hasattr(self.app, "TkdndVersion"))
        self.assertTrue(self.app.TkdndVersion)

    def test_drop_handler_chemin_accolades_espaces(self):
        """event.data TkinterDnD '{...chemin avec espaces...}' -> import OK."""
        from ui.desktop_app import TKDND_AVAILABLE
        if not TKDND_AVAILABLE:
            self.skipTest("tkinterdnd2 non installe")

        import types
        event = types.SimpleNamespace(data="{" + REF_PDF + "}")
        self.app._on_drop(event)
        self.assertEqual(self.app.selected_file_path,
                         os.path.abspath(REF_PDF))
        self.assertEqual(str(self.app.btn_action.cget("state")), "normal")

    def test_drop_handler_multiples_fichiers_premier_charge(self):
        import types
        from ui.desktop_app import TKDND_AVAILABLE
        if not TKDND_AVAILABLE:
            self.skipTest("tkinterdnd2 non installe")

        event = types.SimpleNamespace(
            data="{" + REF_PDF + "} {C:/autre/plan2.pdf}")
        self.app._on_drop(event)
        self.assertEqual(self.app.selected_file_path,
                         os.path.abspath(REF_PDF))

    def test_parcourir_chemin_avec_espaces(self):
        """Flux complet 'Parcourir' avec un nom de fichier contenant des espaces."""
        import fitz
        import tempfile
        safe_dir = tempfile.mkdtemp(prefix="plan ba espaces ")
        pdf = os.path.join(safe_dir, "PLAN BA final.pdf")
        doc = fitz.open()
        page = doc.new_page(width=1191, height=842)
        page.insert_text((600, 125), "1")
        page.insert_text((100, 135), "S1(120x120x30)")
        doc.save(pdf)
        doc.close()
        self.addCleanup(lambda: __import__("shutil").rmtree(
            safe_dir, ignore_errors=True))

        # Meme chaine que retourne filedialog.askopenfilename()
        self.app._on_file_selected(pdf)
        self.assertEqual(self.app.selected_file_path, os.path.abspath(pdf))
        self.assertEqual(str(self.app.btn_action.cget("state")), "normal")


if __name__ == "__main__":
    unittest.main()
