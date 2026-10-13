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
