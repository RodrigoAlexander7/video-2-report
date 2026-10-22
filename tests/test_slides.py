import json
import tempfile
import unittest
from pathlib import Path

from src.core import detect
from src.reports.html_slides import build, check, scaffold
from src.slides_engine import (BrowserError, Deck, DeckError, check_layout, check_theme, find_chrome, layout_problems,
                               lint_html, render_deck, theme_css, validate_slides)
from src.slides_engine.renderer import expand_dp, inline
from tests.slides_fixtures import fill, worst_case_toml, write_project

try:
    find_chrome()
    HAS_CHROME = True
except BrowserError:
    HAS_CHROME = False

MINIMAL = '''
[[slide]]
layout = "title"
title = "Título"

[[slide]]
layout = "bullets"
title = "Viñetas"
items = ["Uno", "Dos"]
'''


def problems(*slides):
    return validate_slides(list(slides))


class ModelTests(unittest.TestCase):
    def test_valid_minimal_deck(self):
        self.assertEqual(problems({"layout": "title", "title": "T"}, {"layout": "bullets", "title": "B", "items": ["a"]}), [])

    def test_first_slide_must_be_title(self):
        self.assertTrue(any("primera" in p for p in problems({"layout": "bullets", "title": "B", "items": ["a"]})))

    def test_unknown_layout_suggests_the_closest_one(self):
        self.assertTrue(any("'bullets'" in p for p in problems({"layout": "title", "title": "T"}, {"layout": "bulets"})))

    def test_unknown_field_is_a_typo_hint_not_silently_ignored(self):
        msgs = problems({"layout": "title", "title": "T"}, {"layout": "bullets", "title": "B", "items": ["a"], "item": ["x"]})
        self.assertTrue(any("campo desconocido 'item'" in m for m in msgs))

    def test_budgets_are_enforced_in_characters(self):
        msgs = problems({"layout": "title", "title": "T"},
                        {"layout": "bullets", "title": "B", "items": [fill(200)]})
        self.assertTrue(any("caracteres" in m for m in msgs))
        many = problems({"layout": "title", "title": "T"}, {"layout": "bullets", "title": "B", "items": ["x"] * 7})
        self.assertTrue(any("7 elementos" in m for m in many))

    def test_markup_does_not_count_against_the_budget(self):
        self.assertEqual(problems({"layout": "title", "title": "T"},
                                  {"layout": "bullets", "title": "B", "items": ["**" + "a" * 100 + "**"]}), [])

    def test_table_rows_must_match_header(self):
        msgs = problems({"layout": "title", "title": "T"},
                        {"layout": "table", "title": "X", "header": ["a", "b"], "rows": [["1"]]})
        self.assertTrue(any("fila 1" in m for m in msgs))

    def test_figure_needs_exactly_one_source(self):
        msgs = problems({"layout": "title", "title": "T"},
                        {"layout": "figure", "title": "F", "caption": "c", "image": "a.png", "evidence_id": "x"})
        self.assertTrue(any("exactamente uno" in m for m in msgs))

    def test_all_problems_are_reported_together(self):
        msgs = problems({"layout": "title"}, {"layout": "bullets", "items": []})
        self.assertGreaterEqual(len(msgs), 3)


class ThemeAndLintTests(unittest.TestCase):
    def test_bundled_theme_is_light_and_accessible(self):
        self.assertEqual(check_theme(theme_css("academic-light"), "academic-light"), [])

    def test_dark_theme_is_rejected(self):
        dark = theme_css("academic-light").replace("--p-white: #FFFFFF;", "--p-white: #0B0F19;")
        self.assertTrue(any("demasiado oscuro" in p for p in check_theme(dark)))

    def test_low_contrast_is_rejected(self):
        weak = theme_css("academic-light").replace("--p-slate-600: #475569;", "--p-slate-600: #B0B8C4;")
        self.assertTrue(any("contraste" in p for p in check_theme(weak)))

    def test_lint_flags_motion_dark_mode_and_scripts(self):
        css = ("color-scheme: light; @keyframes a{} .x{animation: a 1s} .y{transition: all .2s} "
               "html{scroll-behavior: smooth} @media (prefers-color-scheme: dark){}")
        found = lint_html(f"<style>{css}</style><body><script>1</script></body>")
        for word in ("keyframes", "animation", "transition", "smooth", "prefers-color-scheme", "script"):
            self.assertTrue(any(word in p for p in found), word)

    def test_lint_ignores_prose_and_css_comments(self):
        html = ("<style>/* sin animation ni transition: */ :root{color-scheme: light}</style>"
                "<body><p>Explica la transition y la animation del sistema</p></body>")
        self.assertEqual(lint_html(html), [])

    def test_lint_flags_external_resources(self):
        self.assertTrue(lint_html('<style>:root{color-scheme: light}</style><img src="https://x.test/a.png">'))
        self.assertTrue(lint_html("<style>@import url(https://f.test/x.css);:root{color-scheme: light}</style>"))


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def png(self, path: Path) -> Path:
        from PIL import Image
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (40, 20), (200, 30, 30)).save(path)
        return path

    def test_dp_unit_is_expanded_including_negatives(self):
        self.assertEqual(expand_dp("a{margin:0 -96dp;font-size:44dp;x:1.5dp}"),
                         "a{margin:0 calc(-96 * var(--px));font-size:calc(44 * var(--px));x:calc(1.5 * var(--px))}")

    def test_inline_markup_is_escaped_first(self):
        self.assertEqual(str(inline("<b>x</b> **n** `c`")), "&lt;b&gt;x&lt;/b&gt; <strong>n</strong> <code>c</code>")

    def test_rendered_deck_is_light_static_and_self_contained(self):
        project = write_project(self.root / "d", worst_case_toml(self.png(self.root / "img.png")))
        html = check(project, evidence_dir=self.root / "none")
        self.assertEqual(html.count('<section class="slide '), 11)
        self.assertNotIn("<script", html)
        self.assertIn("color-scheme: light", html)
        self.assertEqual(lint_html(html), [])

    def test_user_text_cannot_inject_markup(self):
        toml = MINIMAL.replace('"Título"', '"<script>alert(1)</script>"', 1)
        html = check(write_project(self.root / "x", toml))
        self.assertNotIn("<script", html)
        self.assertIn("&lt;script&gt;", html)

    def test_institutional_logos_can_be_turned_off(self):
        on = check(write_project(self.root / "a", MINIMAL))
        off = check(write_project(self.root / "b", MINIMAL, institutional=False))
        self.assertIn('<img class="logo-unsa"', on)
        self.assertNotIn('<img class="logo-unsa"', off)
        self.assertLess(len(off), len(on))

    def test_missing_image_and_unknown_evidence_are_reported(self):
        toml = MINIMAL + '''
[[slide]]
layout = "figure"
title = "A"
image = "no-existe.png"
caption = "c"

[[slide]]
layout = "figure"
title = "B"
evidence_id = "fantasma"
caption = "c"
'''
        with self.assertRaises(DeckError) as ctx:
            check(write_project(self.root / "m", toml), evidence_dir=self.root / "ev")
        text = str(ctx.exception)
        self.assertIn("no existe la imagen", text)
        self.assertIn("fantasma", text)

    def test_evidence_id_resolves_through_the_manifest(self):
        ev = self.root / "ev"
        self.png(ev / "fig" / "p1.png")
        (ev / "manifest.json").write_text(json.dumps({"version": 1, "items": {"pasada1": {"image": "fig/p1.png"}}}))
        toml = MINIMAL + '\n[[slide]]\nlayout = "figure"\ntitle = "R"\nevidence_id = "pasada1"\ncaption = "Pasada 1"\n'
        html = check(write_project(self.root / "e", toml), evidence_dir=ev)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("Figura 1.", html)

    def test_code_file_lines_are_sliced_and_budgeted(self):
        project = write_project(self.root / "c", MINIMAL)
        (project / "code" / "a.py").write_text("\n".join(f"linea{i}" for i in range(1, 40)), encoding="utf-8")
        ok = MINIMAL + '\n[[slide]]\nlayout = "code"\ntitle = "C"\nfile = "code/a.py"\nlines = "3-5"\n'
        (project / "content" / "slides.toml").write_text(ok, encoding="utf-8")
        html = check(project)
        self.assertIn("linea3", html)
        self.assertNotIn("linea6", html)
        (project / "content" / "slides.toml").write_text(ok.replace('lines = "3-5"', 'lines = "1-30"'), encoding="utf-8")
        with self.assertRaisesRegex(DeckError, "líneas"):
            check(project)

    def test_english_labels(self):
        project = write_project(self.root / "en", MINIMAL)
        toml = project / "project.toml"
        toml.write_text(toml.read_text(encoding="utf-8").replace("[slides]", '[slides]\nlang = "en"'), encoding="utf-8")
        self.assertIn("Authors", check(project))

    def test_only_16_9_is_supported(self):
        project = write_project(self.root / "r", MINIMAL)
        toml = project / "project.toml"
        toml.write_text(toml.read_text(encoding="utf-8").replace("[slides]", '[slides]\nratio = "4:3"'), encoding="utf-8")
        with self.assertRaisesRegex(DeckError, "16:9"):
            check(project)

    def test_unknown_theme_lists_available_ones(self):
        project = write_project(self.root / "t", MINIMAL)
        toml = project / "project.toml"
        toml.write_text(toml.read_text(encoding="utf-8").replace("[slides]", '[slides]\ntheme = "oscuro"'), encoding="utf-8")
        with self.assertRaisesRegex(DeckError, "academic-light"):
            check(project)

    def test_metadata_is_inherited_from_theory_table(self):
        project = write_project(self.root / "i", MINIMAL)
        (project / "project.toml").write_text(
            '[theory]\ncourse = "Calidad de Software"\ninstructor = "Mg. X"\nmembers = [{ name = "Ana Pérez", role = "R1" }]\n'
            '[slides]\ntitle = "Deck"\n', encoding="utf-8")
        html = check(project)
        self.assertIn("Calidad de Software", html)
        self.assertIn("Ana Pérez", html)


class RegistryAndScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detected_by_slides_table(self):
        write_project(self.root, MINIMAL)
        (self.root / "project.toml").write_text('[slides]\ntitle = "X"\n', encoding="utf-8")
        self.assertEqual(detect(self.root).name, "html-slides")

    def test_report_and_deck_in_one_folder_need_an_explicit_choice(self):
        (self.root / "project.toml").write_text('[theory]\ncourse = "c"\n[slides]\ntitle = "X"\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Ambiguo"):
            detect(self.root)
        self.assertEqual(detect(self.root, "html-slides").name, "html-slides")
        self.assertEqual(detect(self.root, "typst-theory").name, "typst-theory")

    def test_scaffold_passes_check_and_never_overwrites(self):
        project = scaffold(self.root / "nuevo")
        self.assertIn("<section", check(project))
        with self.assertRaises(FileExistsError):
            scaffold(project)


@unittest.skipUnless(HAS_CHROME, "Chrome/Chromium no está instalado")
class ChromeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_worst_case_of_every_layout_fits_and_exports_one_page_per_slide(self):
        from PIL import Image
        img = self.root / "img.png"
        Image.new("RGB", (1600, 900), (230, 235, 245)).save(img)
        project = write_project(self.root / "d", worst_case_toml(img))
        pdf = build(project, out_dir=self.root / "out", evidence_dir=self.root / "none")
        data = pdf.read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        from src.slides_engine.browser import count_pdf_pages
        self.assertEqual(count_pdf_pages(pdf), 11)
        self.assertTrue((self.root / "out" / "d-slides.html").is_file())

    def test_overflow_is_detected_in_a_real_browser(self):
        deck = Deck(meta={"title": "T", "theme": "academic-light", "institutional": False, "footer": "f", "lang": "es",
                          "authors": [], "course": "", "instructor": "", "semester": "", "date": "2026-01-01"},
                    slides=[{"layout": "title", "title": "T"},
                            {"layout": "bullets", "title": "Demasiado", "items": [fill(300)] * 6}])
        found = layout_problems(check_layout(render_deck(deck, self.root)))
        self.assertTrue(any("diapositiva 2" in p for p in found), found)

    def test_html_only_when_pdf_is_disabled(self):
        project = write_project(self.root / "h", MINIMAL)
        out = build(project, out_dir=self.root / "o", pdf=False)
        self.assertEqual(out.suffix, ".html")
        self.assertFalse(list((self.root / "o").glob("*.pdf")))


if __name__ == "__main__":
    unittest.main()
