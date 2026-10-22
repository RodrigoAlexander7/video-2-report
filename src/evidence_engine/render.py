# -*- coding: utf-8 -*-
"""Renderiza una transcripción de terminal como imagen PNG con apariencia de terminal real.

Es solo presentación: el texto llega ya capturado de una ejecución real
(ver capture.py) y la imagen se estiliza como una ventana de terminal moderna.
"""

import os
import re
from typing import List

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
_BOLD_CANDIDATES = [p.replace("Regular", "Bold").replace("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf")
                    for p in _FONT_CANDIDATES]

_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

BG, TITLE_BG = (24, 24, 28), (42, 42, 48)
FG, DIM, ERR, CMD = (225, 225, 230), (140, 140, 150), (248, 113, 113), (96, 165, 250)
PROMPT_COLOR = (74, 222, 128)


def _font(candidates: List[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError("No hay fuente monoespaciada disponible: " + ", ".join(candidates))


def render_terminal(transcript: str, title: str, out_path: str, size: int = 15, width: int = 1100) -> str:
    # Eliminar cualquier secuencia ANSI residual para evitar caracteres basura o cajas
    transcript = _ANSI.sub("", transcript)
    font, bold = _font(_FONT_CANDIDATES, size), _font(_BOLD_CANDIDATES, size)
    lines = transcript.split("\n")

    display_title = title   # el título lo decide quien llama (ver capture.window_title); aquí no se inventa nada

    longest = max([bold.getlength(l) for l in lines] + [0])
    width = int(min(max(width, longest + 44), 1600))
    while font.getlength(display_title) > width - 120 and len(display_title) > 4:
        display_title = display_title[:-4] + "…"

    line_h, pad, title_h = size + 7, 16, 36
    height = title_h + pad * 2 + line_h * len(lines)
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    # Barra superior con estilo de ventana de terminal
    d.rectangle([0, 0, width, title_h], fill=TITLE_BG)
    d.line([(0, title_h), (width, title_h)], fill=(55, 55, 62), width=1)

    # Botones de control de ventana (estilo Ubuntu / GNOME)
    cy = title_h // 2
    btn_radius = 5
    for idx, col in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
        cx = 16 + idx * 16
        d.ellipse([cx - btn_radius, cy - btn_radius, cx + btn_radius, cy + btn_radius], fill=col)

    # Título de ventana centrado
    tw = font.getlength(display_title)
    tx = max(72, int((width - tw) / 2))
    d.text((tx, 9), display_title, font=font, fill=(205, 205, 215))

    y = title_h + pad
    for line in lines:
        if line.startswith("$ "):
            # Resaltar prompt $ en verde y comando en blanco bold
            d.text((pad, y), "$ ", font=bold, fill=PROMPT_COLOR)
            offset = bold.getlength("$ ")
            d.text((pad + offset, y), line[2:], font=bold, fill=(255, 255, 255))
        elif line.startswith("> "):
            d.text((pad, y), line, font=bold, fill=CMD)
        elif "Error" in line or "[ERROR]" in line or "FAILURE" in line:
            d.text((pad, y), line, font=font, fill=ERR)
        elif line.startswith("Executed in") or line.startswith("Parsed") or line.startswith("Type checked") \
                or line.startswith("Initialized") or line.startswith("Interpreter") or line.startswith("[INFO]"):
            color = (160, 160, 170) if line.startswith("[INFO]") else DIM
            d.text((pad, y), line, font=font, fill=color)
        else:
            d.text((pad, y), line, font=font, fill=FG)
        y += line_h

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path
