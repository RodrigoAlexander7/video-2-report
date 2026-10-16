import json
import os
import tempfile
import unittest

from src.evidence_engine import capture_commands, register_image, verify_claims, verify_manifest
from src.evidence_engine.manifest import load_manifest


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_records_real_output_and_hashes(self):
        item = capture_commands("eco", ["echo hola mundo"], self.out)
        self.assertEqual(item["source"], "terminal")
        self.assertEqual(item["returncodes"], [0])
        with open(os.path.join(self.out, item["log"]), encoding="utf-8") as f:
            self.assertIn("hola mundo", f.read())
        self.assertTrue(os.path.isfile(os.path.join(self.out, item["image"])))
        self.assertEqual([i for i in verify_manifest(self.out) if i.level == "error"], [])

    def test_commands_run_without_shell(self):
        item = capture_commands("sin-shell", ["echo a; echo b"], self.out)
        with open(os.path.join(self.out, item["log"]), encoding="utf-8") as f:
            self.assertIn("a; echo b", f.read())  # el ';' es un argumento literal, no un separador

    def test_missing_command_is_reported_not_raised(self):
        item = capture_commands("falta", ["comando-que-no-existe-xyz"], self.out)
        self.assertEqual(item["returncodes"], [127])

    def test_tampered_log_is_detected(self):
        item = capture_commands("eco", ["echo 70"], self.out)
        with open(os.path.join(self.out, item["log"]), "a", encoding="utf-8") as f:
            f.write("edición manual\n")
        errors = [i for i in verify_manifest(self.out) if i.level == "error"]
        self.assertTrue(any("modificado" in e.message for e in errors))

    def test_claim_must_appear_in_real_log(self):
        capture_commands("saldo", ["echo saldo = 70"], self.out)
        doc = os.path.join(self.out, "informe.typ")
        with open(doc, "w", encoding="utf-8") as f:
            f.write("// evidence: saldo expect: saldo = 70\n// evidence: saldo expect: saldo = 200\n"
                    "// evidence: otro expect: x\n")
        issues = verify_claims(self.out, [doc])
        self.assertEqual(len(issues), 2)
        self.assertTrue(any("200" in i.message for i in issues))
        self.assertTrue(any("no registrada" in i.message for i in issues))

    def test_annotated_image_requires_registered_base(self):
        png = os.path.join(self.out, "x.png")
        with open(png, "wb") as f:
            f.write(b"png")
        with self.assertRaises(ValueError):
            register_image("anot", png, self.out, source="annotated")
        register_image("anot", png, self.out, source="annotated", base="no-existe")
        errors = [i for i in verify_manifest(self.out) if i.level == "error"]
        self.assertTrue(any("sin base" in e.message for e in errors))
        self.assertIn("anot", load_manifest(self.out)["items"])


if __name__ == "__main__":
    unittest.main()


class DesktopRenderTests(unittest.TestCase):
    def test_full_screen_image_is_marked_as_composition(self):
        from PIL import Image
        from src.evidence_engine import capture_vdmj  # noqa: F401  (API pública disponible)
        from src.evidence_engine.capture import _finish
        with tempfile.TemporaryDirectory() as d:
            item = _finish(d, "x", "> print 1\n= 1", "t", {"tool": "t", "commands": [], "returncodes": [0]}, screen="ubuntu")
            self.assertEqual(item["render"], "desktop-frame")
            self.assertEqual(Image.open(os.path.join(d, item["image"])).size, (1920, 1080))
            self.assertEqual([i for i in verify_manifest(d) if i.level == "error"], [])

    def test_unknown_theme_is_rejected(self):
        from src.evidence_engine.desktop import render_desktop
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                render_desktop("x", "t", os.path.join(d, "a.png"), theme="beos")
