import tempfile
import unittest
from pathlib import Path

from src.core import PIPELINES, detect, plan_for


def touch(d: Path, *names: str):
    for n in names:
        p = d / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detects_epis_by_study_case(self):
        touch(self.dir, "StudyCase.md", "plantilla.docx")
        self.assertEqual(detect(self.dir).name, "epis-ne")

    def test_detects_video_report_by_mp4(self):
        touch(self.dir, "demo.mp4", "plantilla.docx")
        self.assertEqual(detect(self.dir).name, "video-report")

    def test_unknown_directory_is_rejected_with_hint(self):
        touch(self.dir, "notas.txt")
        with self.assertRaisesRegex(ValueError, "Ningún pipeline"):
            detect(self.dir)

    def test_explicit_pipeline_in_project_toml(self):
        touch(self.dir, "a.docx")
        (self.dir / "project.toml").write_text('pipeline = "epis-ne-short"\n', encoding="utf-8")
        touch(self.dir, "input-template.docx")
        self.assertEqual(detect(self.dir).name, "epis-ne-short")

    def test_explicit_only_pipelines_are_never_guessed(self):
        touch(self.dir, "input-template.docx", "video.mp4")
        self.assertNotIn(detect(self.dir).name, ("epis-ne-short", "unity-lab06"))

    def test_ambiguity_is_reported_not_guessed(self):
        touch(self.dir, "StudyCase.md", "demo.mp4")
        with self.assertRaisesRegex(ValueError, "Ambiguo"):
            detect(self.dir)

    def test_typst_lab_requires_lab_table(self):
        (self.dir / "project.toml").write_text("[build]\nsections = []\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            detect(self.dir)
        (self.dir / "project.toml").write_text('[lab]\ntitle = "x"\n', encoding="utf-8")
        self.assertEqual(detect(self.dir).name, "typst-lab")

    def test_missing_template_gives_actionable_error(self):
        touch(self.dir, "demo.mp4")
        with self.assertRaisesRegex(FileNotFoundError, "Falta 'template'"):
            plan_for(PIPELINES["video-report"], self.dir)


if __name__ == "__main__":
    unittest.main()
