# -*- coding: utf-8 -*-
"""Captura de figuras: OCR, elección de fotogramas, recortes por panel, anotaciones y tamaños (sin depender de Unity)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from src.video_engine import ocr
from src.video_engine.annotate import (AnnotationError, GAP, MAX_AREA_RATIO, annotate, arrow_to, distance_to_box, outline,
                                       parse_annotation)
from src.video_engine.crops import CropError, panel_bounds, parse_crop, resolve_crop, snap_to_words
from src.video_engine.frames import Candidate, contact_sheet, format_time, is_blank, parse_time, score, sharpness

TSV = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
       "5\t1\t1\t1\t1\t1\t100\t50\t60\t14\t96\tPlay\n5\t1\t1\t1\t1\t2\t165\t50\t30\t14\t95\tOn\n5\t1\t1\t1\t1\t3\t200\t50\t60\t14\t93\tAwake\n"
       "5\t1\t1\t1\t2\t1\t100\t80\t50\t14\t90\tLoop\n5\t1\t2\t1\t1\t1\t400\t50\t70\t14\t30\truido\n5\t1\t3\t1\t1\t1\t10\t10\t10\t10\t-1\t\n")


def words():
    return ocr.parse_tsv(TSV)


class OcrTests(unittest.TestCase):
    def test_tsv_keeps_confident_words_only(self):
        self.assertEqual([w.text for w in words()], ["Play", "On", "Awake", "Loop"])

    def test_find_phrase_returns_the_union_box(self):
        self.assertEqual(ocr.find_phrase(words(), "play on awake"), (100, 50, 260, 64))

    def test_phrase_must_be_on_one_line(self):
        self.assertIsNone(ocr.find_phrase(words(), "Awake Loop"))

    def test_one_typo_is_tolerated_in_long_words(self):
        w = [ocr.Word("Rigidbbdy", 0, 0, 80, 14, 90)]
        self.assertIsNotNone(ocr.find_phrase(w, "Rigidbody"))
        self.assertIsNone(ocr.find_phrase([ocr.Word("Coll", 0, 0, 80, 14, 90)], "Cell"))      # 4 letras: exacto

    def test_accents_and_case_do_not_matter(self):
        self.assertEqual(ocr.norm("Pestaña: ÁÉÍ"), "pestanaaei")

    def test_find_all_reports_missing(self):
        found, missing = ocr.find_all(words(), ["Loop", "Spatial Blend"])
        self.assertEqual(list(found), ["Loop"])
        self.assertEqual(missing, ["Spatial Blend"])

    def test_text_height_is_the_median_of_confident_words(self):
        ws = [ocr.Word(t, 0, 0, 40, h, 95) for t, h in (("Aaaa", 12), ("Bbbb", 14), ("Cccc", 13), ("Dd", 50))]
        self.assertEqual(ocr.text_height_px(ws), 13)

    @unittest.skipUnless(shutil.which("tesseract"), "requiere tesseract")
    def test_real_tesseract_reads_big_text(self):
        img = Image.new("RGB", (500, 120), "white")
        ImageDraw.Draw(img).text((20, 30), "Rigidbody", fill="black", font=_big_font(48))
        self.assertIsNotNone(ocr.find_phrase(ocr.ocr_words(img), "Rigidbody"))


def _big_font(size):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


class FrameScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _save(self, name, img):
        path = self.dir / name
        img.save(path)
        return path

    def _text_image(self, blur=0.0):
        img = Image.new("RGB", (640, 360), (50, 50, 50))
        d = ImageDraw.Draw(img)
        for y in range(20, 340, 30):
            d.text((30, y), "Inspector Rigidbody Collider", fill=(230, 230, 230), font=_big_font(18))
        return img.filter(ImageFilter.GaussianBlur(blur)) if blur else img

    def test_time_parsing(self):
        self.assertEqual(parse_time(95), 95.0)
        self.assertEqual(parse_time("1:35"), 95.0)
        self.assertEqual(parse_time("1:02:03"), 3723.0)
        self.assertEqual(parse_time("0:09.5"), 9.5)
        with self.assertRaises(ValueError):
            parse_time("1:xx")
        self.assertEqual(format_time(125), "2:05")

    def test_sharp_frame_beats_blurred_and_blank_is_discarded(self):
        cands = [Candidate(1.0, self._save("a.png", self._text_image(blur=4))),
                 Candidate(1.5, self._save("b.png", self._text_image())),
                 Candidate(2.0, self._save("c.png", Image.new("RGB", (640, 360), "black")))]
        score(cands)
        self.assertGreater(cands[1].quality, cands[0].quality)
        self.assertEqual(cands[2].quality, 0.0)
        self.assertTrue(is_blank(Image.new("RGB", (64, 64), "black")))

    def test_still_frame_beats_one_in_motion(self):
        base = self._text_image()
        moving = base.copy()
        ImageDraw.Draw(moving).rectangle([0, 0, 640, 200], fill=(200, 60, 60))
        cands = [Candidate(1.0, self._save("a.png", base)), Candidate(1.5, self._save("b.png", base)),
                 Candidate(2.0, self._save("c.png", moving))]
        score(cands)
        self.assertGreater(cands[0].quality, cands[2].quality)
        self.assertGreater(sharpness(base), sharpness(base.filter(ImageFilter.GaussianBlur(3))))

    def test_contact_sheet_is_written(self):
        sheet = contact_sheet([("uno", self._text_image()), ("dos", self._text_image(3))], self.dir / "s.png", cols=2, thumb_w=200, highlight=0)
        with Image.open(sheet) as im:
            self.assertGreater(im.width, 400)


def unity_like(width=640, height=420):
    """Dos paneles con la franja oscura de 4 px que separa los de Unity, y contenido (texto) dentro."""
    img = Image.new("RGB", (width, height), (56, 56, 56))
    d = ImageDraw.Draw(img)
    d.rectangle([300, 0, 303, height], fill=(20, 20, 20))                 # franja vertical
    d.rectangle([304, 300, width, 303], fill=(20, 20, 20))                # franja horizontal bajo el panel derecho
    for y in range(70, 290, 24):
        d.rectangle([320, y, 320 + 100 + (y % 50), y + 8], fill=(170, 170, 170))   # "texto"
    d.line([304, 150, width, 150], fill=(35, 35, 35), width=1)             # línea de 1 px entre componentes: no es borde de panel
    return img


class CropTests(unittest.TestCase):
    def test_panel_bounds_use_the_dark_gaps(self):
        img = unity_like()
        self.assertEqual(panel_bounds(img, (320, 20, 380, 34)), (304, 8, 640, 300))

    def test_one_pixel_component_separators_are_not_panel_edges(self):
        left, top, right, bottom = panel_bounds(unity_like(), (320, 20, 380, 34))
        self.assertEqual(bottom, 300)

    def test_crop_spec_validation(self):
        with self.assertRaises(CropError):
            parse_crop({"panel": "inspector", "bogus": 1})
        with self.assertRaises(CropError):
            parse_crop({"panel": "juego"})
        with self.assertRaises(CropError):
            parse_crop({"desde": "Rigidbody"})                                 # sin panel no hay ancho
        with self.assertRaises(CropError):
            parse_crop({"rect": [0.5, 0, 0.2, 1]})
        with self.assertRaises(CropError):
            parse_crop({"panel": "inspector", "around": "x"})
        self.assertIsNone(parse_crop(None))

    def test_desde_hasta_limits_the_panel_vertically(self):
        img = unity_like()
        ws = [ocr.Word("Inspector", 320, 20, 60, 14, 95), ocr.Word("Rigidbody", 330, 100, 70, 14, 95),
              ocr.Word("Capsule", 330, 200, 50, 14, 95), ocr.Word("Collider", 385, 200, 50, 14, 95)]
        box = resolve_crop(img, ws, parse_crop({"panel": "inspector", "desde": "Rigidbody", "hasta": "Capsule Collider"}))
        self.assertEqual((box[0], box[2]), (304, 640))
        self.assertEqual((box[1], box[3]), (90, 196))

    def test_missing_anchor_text_is_an_error(self):
        with self.assertRaisesRegex(CropError, "Inspector"):
            resolve_crop(unity_like(), [], parse_crop({"panel": "inspector"}))

    def test_height_limits_a_panel_crop(self):
        ws = [ocr.Word("Inspector", 320, 20, 60, 14, 95)]
        box = resolve_crop(unity_like(), ws, parse_crop({"panel": "inspector", "height": 120}))
        self.assertEqual(box[3] - box[1], 120)

    def test_crop_never_cuts_a_word(self):
        ws = [ocr.Word("Advanced", 90, 40, 40, 14, 50)]          # cruza el borde derecho del recorte (x = 100)
        self.assertEqual(snap_to_words((0, 0, 100, 100), ws, (400, 300))[2], 130)

    def test_rect_crop_is_resolution_independent(self):
        for size in ((640, 400), (1280, 800)):
            img = Image.new("RGB", size, "gray")
            box = resolve_crop(img, [], parse_crop({"rect": [0.25, 0.25, 0.75, 0.75]}))
            self.assertEqual(box, (size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4))


class AnnotationTests(unittest.TestCase):
    def img(self):
        return Image.new("RGB", (600, 400), (60, 60, 60))

    def test_outline_has_no_fill(self):
        res = outline(self.img(), (200, 150, 300, 180))
        self.assertEqual(res.image.getpixel((250, 165)), (60, 60, 60))          # el interior queda intacto
        self.assertNotEqual(res.image.getpixel((res.box[0], 160)), (60, 60, 60))

    def test_a_box_that_covers_most_of_the_figure_is_rejected(self):
        with self.assertRaisesRegex(AnnotationError, "cubre"):
            outline(self.img(), (10, 10, 590, 390))
        self.assertLessEqual(MAX_AREA_RATIO, 0.25)

    def test_arrow_tip_stops_next_to_the_target(self):
        for direction in ("left", "right", "up", "down", "auto"):
            target = (250, 180, 350, 220)
            res = arrow_to(self.img(), target, direction)
            self.assertAlmostEqual(distance_to_box(res.tip, target), GAP, delta=1.5)

    def test_arrow_without_room_is_an_error(self):
        with self.assertRaisesRegex(AnnotationError, "espacio"):
            arrow_to(self.img(), (2, 150, 40, 200), "left")

    def test_spec_validation(self):
        with self.assertRaises(AnnotationError):
            parse_annotation({"target": "x", "rect": [0, 0, 1, 1]})              # uno de los dos
        with self.assertRaises(AnnotationError):
            parse_annotation({"style": "box"})
        with self.assertRaises(AnnotationError):
            parse_annotation({"target": "x", "style": "flecha"})
        spec = parse_annotation({"target": "Play On Awake", "extend": [0, 0, 60, 0]})
        self.assertEqual(spec.extend, (0, 0, 60, 0))

    def test_annotate_dispatches_by_style(self):
        spec = parse_annotation({"target": "x", "style": "arrow", "direction": "left"})
        res = annotate(self.img(), spec, (300, 180, 400, 220))
        self.assertIsNotNone(res.tip)


if __name__ == "__main__":
    unittest.main()
