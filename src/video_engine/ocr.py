# -*- coding: utf-8 -*-
"""OCR con la CLI de Tesseract (sin dependencias de Python): palabras con su caja, búsqueda de frases y alto de texto.

Se usa para tres cosas: comprobar que una captura muestra lo que debe (`expect`), anclar recortes y anotaciones al
texto real de la interfaz (sin coordenadas escritas a mano) y medir si el texto de la figura será legible en el documento.
"""

from __future__ import annotations

import csv
import io
import re
import shutil
import statistics
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from PIL import Image

Box = Tuple[int, int, int, int]          # x0, y0, x1, y1
TIMEOUT_S = 60


class OcrError(RuntimeError):
    """Tesseract no está disponible o falló."""


@dataclass(frozen=True)
class Word:
    text: str
    x: int
    y: int
    w: int
    h: int
    conf: float
    line: Tuple[int, int, int] = (0, 0, 0)       # (bloque, párrafo, línea) de Tesseract

    @property
    def box(self) -> Box:
        return (self.x, self.y, self.x + self.w, self.y + self.h)


def norm(text: str) -> str:
    """Minúsculas, sin acentos ni signos: «Pestaña:» y «pestana» comparan igual."""
    text = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in text if not unicodedata.combining(c)))


def tesseract_path() -> str:
    path = shutil.which("tesseract")
    if not path:
        raise OcrError("No se encontró `tesseract` (OCR). Instálalo con: sudo apt install tesseract-ocr tesseract-ocr-spa")
    return path


def parse_tsv(tsv: str, min_conf: float = 40) -> List[Word]:
    words: List[Word] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5":
            continue
        text = (row.get("text") or "").strip()
        try:
            conf = float(row["conf"])
        except (KeyError, ValueError):
            continue
        if not text or conf < min_conf:
            continue
        words.append(Word(text, int(row["left"]), int(row["top"]), int(row["width"]), int(row["height"]), conf,
                          (int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))))
    return words


def ocr_words(image: Union[str, Path, Image.Image], langs: str = "eng", psm: int = 11, min_conf: float = 40) -> List[Word]:
    """Palabras reconocidas (coordenadas de ``image``). `psm 11` = texto disperso, el adecuado para interfaces."""
    exe = tesseract_path()
    with tempfile.TemporaryDirectory(prefix="ocr-") as tmp:
        if isinstance(image, Image.Image):
            path = Path(tmp) / "in.png"
            image.convert("RGB").save(path)
        else:
            path = Path(image)
        try:
            proc = subprocess.run([exe, str(path), "stdout", "-l", langs, "--psm", str(psm), "tsv"],
                                  capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            raise OcrError(f"Tesseract superó {TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise OcrError(f"Tesseract terminó con código {proc.returncode}: {proc.stderr.strip()[-300:]}")
    return parse_tsv(proc.stdout, min_conf)


def _close(a: str, b: str) -> bool:
    """Igualdad tolerante: una errata de OCR en palabras de 5+ caracteres."""
    if a == b:
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    short, long_ = sorted((a, b), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def union(boxes: Iterable[Box]) -> Box:
    boxes = list(boxes)
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def find_phrase(words: Sequence[Word], phrase: str) -> Optional[Box]:
    """Caja de la frase (palabras consecutivas de la misma línea). ``None`` si no aparece. Prefiere la de mayor confianza."""
    tokens = [norm(t) for t in phrase.split() if norm(t)]
    if not tokens:
        return None
    best: Optional[Tuple[float, Box]] = None
    for i in range(len(words)):
        run = []
        j, k = i, 0
        while k < len(tokens) and j < len(words):
            wn = norm(words[j].text)
            if not wn:                       # signos sueltos: se saltan
                j += 1
                continue
            if run and words[j].line != run[-1].line:
                break
            if not _close(wn, tokens[k]):
                break
            run.append(words[j])
            j, k = j + 1, k + 1
        if k == len(tokens):
            score = statistics.fmean(w.conf for w in run)
            if best is None or score > best[0]:
                best = (score, union(w.box for w in run))
    return best[1] if best else None


def find_all(words: Sequence[Word], phrases: Sequence[str]) -> Tuple[Dict[str, Box], List[str]]:
    """(frases halladas con su caja, frases que faltan)."""
    found: Dict[str, Box] = {}
    missing: List[str] = []
    for phrase in phrases:
        box = find_phrase(words, phrase)
        if box is None:
            missing.append(phrase)
        else:
            found[phrase] = box
    return found, missing


def text_height_px(words: Sequence[Word], region: Optional[Box] = None) -> Optional[float]:
    """Alto mediano de las palabras de 3+ letras dentro de ``region``: aproxima el tamaño de letra de la interfaz."""
    heights = []
    for w in words:
        if len(norm(w.text)) < 3 or w.conf < 60:
            continue
        if region and not (w.x >= region[0] and w.y >= region[1] and w.x + w.w <= region[2] and w.y + w.h <= region[3]):
            continue
        heights.append(w.h)
    return statistics.median(heights) if len(heights) >= 3 else None
