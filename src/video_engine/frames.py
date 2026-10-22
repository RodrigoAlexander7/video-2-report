# -*- coding: utf-8 -*-
"""Elección de fotogramas de un video: candidatos alrededor de un instante, puntuados por nitidez y estabilidad.

El instante que escribe una persona es aproximado (la acción termina un poco después de nombrarla). En vez de
tomar ese segundo exacto se extraen varios fotogramas a su alrededor y se elige el más nítido y quieto; el
OCR (ver `ocr.py`) decide entre los mejores comprobando que se vea lo esperado.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TimeLike = Union[int, float, str]
FFMPEG_TIMEOUT_S = 180
_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]


class VideoError(RuntimeError):
    """El video no se puede leer o ffmpeg falló."""


def parse_time(value: TimeLike) -> float:
    """``95``, ``95.5``, ``"1:35"``, ``"01:35.5"`` o ``"1:02:03"`` -> segundos."""
    if isinstance(value, (int, float)):
        return float(value)
    parts = str(value).strip().split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"tiempo inválido: {value!r} (usa 95, \"1:35\" o \"1:02:03\")") from exc
    if not 1 <= len(nums) <= 3:
        raise ValueError(f"tiempo inválido: {value!r}")
    secs = 0.0
    for n in nums:
        secs = secs * 60 + n
    return secs


def format_time(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _run(cmd: Sequence[str]) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(list(cmd), capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_S)
    except FileNotFoundError as exc:
        raise VideoError(f"No se encontró `{cmd[0]}` (instala ffmpeg).") from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoError(f"`{cmd[0]}` superó {FFMPEG_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise VideoError(f"`{cmd[0]}` falló:\n{proc.stderr.strip()[-500:]}")
    return proc


def probe(video: Union[str, Path]) -> dict:
    """Ancho, alto, fps y duración (s) del primer stream de video."""
    if not Path(video).is_file():
        raise VideoError(f"No existe el video: {video}")
    out = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                "stream=width,height,r_frame_rate,duration:format=duration", "-of", "json", str(video)]).stdout
    data = json.loads(out)
    stream = (data.get("streams") or [{}])[0]
    num, _, den = str(stream.get("r_frame_rate", "0/1")).partition("/")
    duration = stream.get("duration") or data.get("format", {}).get("duration") or 0
    return {"width": int(stream.get("width", 0)), "height": int(stream.get("height", 0)),
            "fps": float(num) / float(den or 1) if float(den or 1) else 0.0, "duration": float(duration)}


def extract_frame(video: Union[str, Path], t: float, out_png: Union[str, Path]) -> Path:
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(video), "-frames:v", "1", str(out_png)])
    if not out_png.is_file():
        raise VideoError(f"No hay fotograma en t={t:.1f}s (¿pasa de la duración del video?)")
    return out_png


@dataclass
class Candidate:
    t: float
    path: Path
    sharp: float = 0.0
    motion: float = 0.0
    quality: float = 0.0
    hits: int = 0                       # frases esperadas halladas por OCR
    found: dict = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)


def extract_window(video: Union[str, Path], t: float, window: float, step: float, out_dir: Union[str, Path],
                   duration: Optional[float] = None) -> List[Candidate]:
    """Fotogramas cada ``step`` s en [t-window, t+window], con una sola llamada a ffmpeg."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = max(0.0, t - window)
    end = t + window if duration is None else min(t + window, max(duration - 0.05, 0))
    if end <= start:
        raise VideoError(f"t={t:.1f}s queda fuera del video (dura {duration:.1f}s)")
    for old in out_dir.glob("c*.png"):
        old.unlink()
    _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(video),
          "-vf", f"fps=1/{step}", str(out_dir / "c%03d.png")])
    files = sorted(out_dir.glob("c*.png"))
    if not files:
        raise VideoError(f"ffmpeg no produjo fotogramas alrededor de t={t:.1f}s")
    return [Candidate(t=start + i * step, path=f) for i, f in enumerate(files)]


def load_rgb(path: Union[str, Path]) -> Image.Image:
    """Imagen cargada en memoria y archivo cerrado."""
    with Image.open(path) as im:
        return im.convert("RGB")


def _gray(img: Image.Image, width: int) -> np.ndarray:
    g = img.convert("L")
    if g.width > width:
        g = g.resize((width, max(1, round(g.height * width / g.width))), Image.BILINEAR)
    return np.asarray(g, dtype=np.float32)


def sharpness(img: Image.Image) -> float:
    """Varianza del laplaciano (más alta = más nítido). Se calcula a 960 px de ancho para no depender de la resolución."""
    a = _gray(img, 960)
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    ga, gb = _gray(a, 240), _gray(b, 240)
    if ga.shape != gb.shape:
        return 255.0
    return float(np.abs(ga - gb).mean())


def is_blank(img: Image.Image) -> bool:
    """Fotograma casi negro o liso (cortes, pantallas de carga)."""
    g = _gray(img, 160)
    return float(g.mean()) < 6 or float(g.std()) < 3


def score(candidates: List[Candidate]) -> List[Candidate]:
    """Rellena ``sharp``, ``motion`` y ``quality`` (0-1) de cada candidato y los devuelve en el mismo orden."""
    imgs = [Image.open(c.path) for c in candidates]
    try:
        for c, im in zip(candidates, imgs):
            c.sharp = 0.0 if is_blank(im) else sharpness(im)
        for i, c in enumerate(candidates):
            diffs = [mean_abs_diff(imgs[i], imgs[j]) for j in (i - 1, i + 1) if 0 <= j < len(imgs)]
            c.motion = max(diffs) if diffs else 0.0
        top_sharp = max((c.sharp for c in candidates), default=0) or 1.0
        top_motion = max((c.motion for c in candidates), default=0) or 1.0
        for c in candidates:
            c.quality = 0.0 if c.sharp == 0 else 0.6 * (c.sharp / top_sharp) + 0.4 * (1 - c.motion / top_motion)
    finally:
        for im in imgs:
            im.close()
    return candidates


def _font(size: int):
    for path in _FONTS:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def contact_sheet(items: Sequence[Tuple[str, Image.Image]], out_png: Union[str, Path], cols: int = 3,
                  thumb_w: int = 560, highlight: Optional[int] = None) -> Path:
    """Hoja de contactos con una etiqueta por miniatura; ``highlight`` marca la elegida con un marco."""
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    font, label_h, gap = _font(15), 26, 10
    thumbs = []
    for label, im in items:
        im = im.convert("RGB")
        im = im.resize((thumb_w, max(1, round(im.height * thumb_w / im.width))), Image.LANCZOS)
        thumbs.append((label, im))
    rows = [thumbs[i:i + cols] for i in range(0, len(thumbs), cols)]
    row_h = [max(im.height for _, im in row) + label_h for row in rows]
    sheet = Image.new("RGB", (cols * (thumb_w + gap) + gap, sum(row_h) + gap * (len(rows) + 1)), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    y, n = gap, 0
    for row, h in zip(rows, row_h):
        for k, (label, im) in enumerate(row):
            x = gap + k * (thumb_w + gap)
            draw.text((x, y + 4), label, fill=(20, 20, 20), font=font)
            sheet.paste(im, (x, y + label_h))
            if highlight is not None and n == highlight:
                draw.rectangle([x - 3, y + label_h - 3, x + im.width + 2, y + label_h + im.height + 2], outline=(200, 49, 14), width=3)
            n += 1
        y += h + gap
    sheet.save(out_png)
    return out_png
