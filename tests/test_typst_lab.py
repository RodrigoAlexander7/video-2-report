import shutil
import tempfile
import unittest
from pathlib import Path

HAS_TYPST = shutil.which("typst") is not None


@unittest.skipUnless(HAS_TYPST, "typst no está instalado")
class TypstLabTests(unittest.TestCase):
    def test_scaffold_builds_a_pdf(self):
        from src.reports.typst_lab import build, scaffold
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / "mi-lab"
            scaffold(str(project))
            pdf = build(str(project), out_dir=str(Path(d) / "out"), inputs={"fecha": "2026-01-31", "hora": "20:00"})
            self.assertTrue(pdf.is_file())
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))

    def test_basic_info_section_follows_the_institutional_layout(self):
        import subprocess
        from src.reports.typst_lab import build, scaffold
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / "info"
            scaffold(str(project))
            toml = project / "project.toml"
            toml.write_text(toml.read_text(encoding="utf-8").replace('semester = "A"', 'semester = "A"\nlevel = "Octavo VIII"'), encoding="utf-8")
            pdf = build(str(project), out_dir=str(Path(d) / "out"), inputs={"fecha": "2026-09-30"})   # sin hora: por defecto 12:00:00
            text = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"], capture_output=True, text=True).stdout
            text = " ".join(text.split())      # las etiquetas largas se parten en dos líneas dentro de su celda
        for expected in ("INFORMACIÓN BÁSICA", "ASIGNATURA:", "TÍTULO DE LA PRÁCTICA:", "NÚMERO DE PRÁCTICA:", "AÑO LECTIVO:",
                         "2026 - A", "NRO. SEMESTRE:", "Octavo VIII", "30/09/2026", "12:00:00", "INTEGRANTE (S)", "NOTA (0-20)", "DOCENTE(S):"):
            self.assertIn(expected, text)

    def test_callout_has_no_colors_even_for_danger(self):
        lib = (Path(__file__).resolve().parents[1] / "src/typst_engine/templates/informe-laboratorio/lib.typ").read_text(encoding="utf-8")
        body = lib[lib.index("#let callout"):lib.index("/// Diagrama de clases")]
        self.assertNotRegex(body, r"rgb\(|fill:")
        self.assertIn("luma(100)", body)

    def test_serif_request_resolves_to_an_available_serif_and_indents_headings(self):
        import json
        from src.reports.typst_lab import build, scaffold
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / "serif"
            scaffold(str(project))
            toml = project / "project.toml"
            toml.write_text(toml.read_text(encoding="utf-8").replace("[build]", '[build]\nfont = "Times New Roman"\nheading-indent = 1.0', 1), encoding="utf-8")
            build(str(project), out_dir=str(Path(d) / "out"))
            cfg = json.loads((Path(d) / "out" / "_stage" / "config.json").read_text(encoding="utf-8"))
            self.assertNotIn("Lato", cfg["font"])
            self.assertEqual(cfg["heading-indent"], 1.0)

    def test_failed_evidence_claim_blocks_the_build(self):
        from src.core.evidence_steps import EvidenceError, verify_project
        from src.evidence_engine import capture_commands
        with tempfile.TemporaryDirectory() as d:
            project = Path(d) / "p"
            (project / "content").mkdir(parents=True)
            (project / "content" / "a.typ").write_text("// evidence: x expect: 200\n", encoding="utf-8")
            capture_commands("x", ["echo 100"], str(Path(d) / "ev"))
            with self.assertRaises(EvidenceError):
                verify_project(project, Path(d) / "ev")


if __name__ == "__main__":
    unittest.main()
