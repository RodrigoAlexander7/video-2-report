# -*- coding: utf-8 -*-
"""Renderiza una transcripción de terminal como imagen PNG.

Es solo presentación: el texto llega ya capturado de una ejecución real
(ver runner.py) y la cabecera de la imagen indica el comando que lo produjo.
"""

import os
from typing import List

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
_BOLD_CANDIDATES = [p.replace("Regular", "Bold").replace("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf")
                    for p in _FONT_CANDIDATES]

BG, TITLE_BG = (30, 30, 30), (50, 50, 50)
FG, DIM, ERR, CMD = (220, 220, 220), (140, 140, 140), (240, 110, 110), (130, 190, 255)


def _font(candidates: List[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError("No hay fuente monoespaciada disponible: " + ", ".join(candidates))


def render_terminal(transcript: str, title: str, out_path: str, size: int = 15, width: int = 1100) -> str:
    font, bold = _font(_FONT_CANDIDATES, size), _font(_BOLD_CANDIDATES, size)
    lines = transcript.split("\n")
    # Ancho según la línea más larga (acotado) y título truncado con puntos suspensivos
    longest = max([bold.getlength(l) for l in lines] + [0])
    width = int(min(max(width, longest + 40), 1600))
    while font.getlength(title) > width - 32 and len(title) > 4:
        title = title[:-4] + "…"
    line_h, pad, title_h = size + 7, 16, 34
    height = title_h + pad * 2 + line_h * len(lines)
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, title_h], fill=TITLE_BG)
    d.text((pad, 8), title, font=font, fill=FG)
    y = title_h + pad
    for line in lines:
        f, color = font, FG
        if line.startswith("> "):
            f, color = bold, CMD
        elif "Error" in line:
            color = ERR
        elif line.startswith("Executed in") or line.startswith("Parsed") or line.startswith("Type checked") \
                or line.startswith("Initialized") or line.startswith("Interpreter"):
            color = DIM
        d.text((pad, y), line, font=f, fill=color)
        y += line_h
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path
