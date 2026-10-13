import json
import os
import tempfile
import unittest
from pathlib import Path

from config import DEFAULT_CONFIG, REPO_ROOT


class ConfigTests(unittest.TestCase):
    def test_default_paths_derive_from_repo_not_from_home(self):
        for path in (DEFAULT_CONFIG.video_path, DEFAULT_CONFIG.output_path, DEFAULT_CONFIG.media_dir):
            self.assertTrue(path.startswith(str(REPO_ROOT)), path)


class VideoModulesTests(unittest.TestCase):
    def test_transcription_modules_do_not_run_on_import(self):
        import src.video_engine.transcribe_batch  # noqa: F401
        import src.video_engine.transcribe_fast  # noqa: F401
        import src.video_engine.transcriber  # noqa: F401

    def test_stages_default_matches_original_hardcoded_values(self):
        from src.video_engine.media_extractor import DEFAULT_STAGES, load_stages
        self.assertEqual(load_stages(None), DEFAULT_STAGES)
        self.assertEqual([g["t"] for g in DEFAULT_STAGES["gifs"]], [818, 942, 1340])
        self.assertEqual(DEFAULT_STAGES["frames"][0]["t"], 855)

    def test_stages_load_from_json(self):
        from src.video_engine.media_extractor import load_stages
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"frames": [], "gifs": []}, f)
            self.assertEqual(load_stages(p), {"frames": [], "gifs": []})


if __name__ == "__main__":
    unittest.main()
