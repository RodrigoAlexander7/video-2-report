# -*- coding: utf-8 -*-
"""Tamaño de las figuras en la página: ancho según su forma, alto acotado y texto de interfaz legible.

Antes todas las imágenes entraban a 5,4 in de ancho, así que un Inspector alto llegaba a medir 10 in y ocupaba más
de una página. Ahora el ancho sale del alto máximo y de la forma de la imagen; si el texto de la interfaz quedaría
por debajo de ``MIN_UI_PT`` el build falla y pide recortar a la zona relevante en vez de encoger.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

MAX_W_IN = 6.1            # ancho útil de la celda de contenido de la plantilla EPIS
MAX_H_IN = 4.6            # alto máximo de una captura
MAX_H_CODE_IN = 5.0       # alto máximo de una imagen de código
MIN_UI_PT = 8.0           # tamaño mínimo aparente del texto de la interfaz
MAX_UPSCALE = 1.25        # no se amplía más de 1,25x respecto a 96 dpi (se vería borroso)
TARGET_DPI = 220          # resolución máxima del bitmap insertado
CODE_TEXT_PT = 9.0        # tamaño de letra objetivo en las imágenes de código
CODE_MIN_PT = 8.0
CODE_FONT_PX = 18         # tamaño de letra con el que editor_engine dibuja (px lógicos)


@dataclass
class Fit:
    width_in: float
    height_in: float
    ui_pt: Optional[float] = None
    problem: Optional[str] = None


def fit_capture(width_px: int, height_px: int, ui_text_px: Optional[float] = None, legible: bool = True, label: str = "figura") -> Fit:
    w = min(MAX_W_IN, MAX_H_IN * width_px / height_px, width_px / 96 * MAX_UPSCALE)
    ui_pt = ui_text_px * (w * 72 / width_px) if ui_text_px else None
    problem = None
    if legible and ui_pt is not None and ui_pt < MIN_UI_PT:
        problem = (f"{label}: el texto de la interfaz mediría {ui_pt:.1f} pt en el documento (mínimo {MIN_UI_PT:.0f} pt). "
                   f"La captura de {width_px}x{height_px}px es demasiado grande para mostrarla completa: recórtala al panel o al "
                   "componente relevante (crop.panel + desde/hasta) o márcala legible = false si es una escena del juego.")
    return Fit(w, w * height_px / width_px, ui_pt, problem)


def fit_code(width_px: int, height_px: int, label: str = "código") -> Fit:
    """Ancho para ~9 pt de texto; si el alto pasa del máximo se reduce, y por debajo de 8 pt se pide dividir."""
    natural_in = width_px / 96
    w = min(MAX_W_IN, natural_in * CODE_TEXT_PT / (CODE_FONT_PX * 0.75))
    if w * height_px / width_px > MAX_H_CODE_IN:
        w = MAX_H_CODE_IN * width_px / height_px
    pt = CODE_FONT_PX * 0.75 * w / natural_in
    problem = None
    if pt < CODE_MIN_PT:
        problem = (f"{label}: el texto del código mediría {pt:.1f} pt (mínimo {CODE_MIN_PT:.0f} pt): "
                   "usa un 'max_lines' menor para dividirlo en más imágenes o acorta las líneas")
    return Fit(w, w * height_px / width_px, pt, problem)


def prepare_bitmap(src: Path, dst: Path, width_in: float, photographic: bool = False) -> Path:
    """Copia reducida a ``TARGET_DPI`` para el documento (los PNG de origen quedan intactos). GIF se copia tal cual."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".gif":
        dst = dst.with_suffix(".gif")
        dst.write_bytes(src.read_bytes())
        return dst
    with Image.open(src) as im:
        im = im.convert("RGB")
        target = round(width_in * TARGET_DPI)
        if im.width > target:
            im = im.resize((target, max(1, round(im.height * target / im.width))), Image.LANCZOS)
        if photographic:
            dst = dst.with_suffix(".jpg")
            im.save(dst, quality=88, optimize=True)
        else:
            dst = dst.with_suffix(".png")
            im.save(dst, optimize=True)
    return dst
