# -*- coding: utf-8 -*-
"""Ventana con la apariencia del VDM++ Toolbox y la salida REAL de VDMJ dentro.

La apariencia (menús, barras de iconos, Manager, Interpreter Window, Trace, BreakPoints)
sale de una captura real del Toolbox (assets/toolbox_template.png). El texto que se dibuja
encima (árbol de archivos y transcripción del intérprete) es la salida literal de la
ejecución con VDMJ; no se traduce al formato del Toolbox. La ventana lleva un título
propio que nombra a VDMJ. Es una composición: el manifiesto la registra como
render = "toolbox-frame".
"""

import os
import textwrap
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from . import desktop as dk
from .render import _BOLD_CANDIDATES, _FONT_CANDIDATES, _font

TEMPLATE = os.path.join(os.path.dirname(__file__), "assets", "toolbox_template.png")
SCALE = 0.96
TITLE_H = 30
# Geometría dentro de la plantilla (px nativos del Toolbox)
TEXT_X, TEXT_Y0, LINE_H, TEXT_BOTTOM, TEXT_RIGHT = 328, 119, 19, 506, 1796
FONT_SIZE = 14.7  # el original rinde ~8.8 px por carácter


def _tree(d: ImageDraw.ImageDraw, files: Sequence[str]) -> None:
    f = _font(_FONT_CANDIDATES, 15)
    ink, gray = (0, 0, 0), (128, 128, 128)

    def box(x, y, sign):
        d.rectangle([x, y, x + 8, y + 8], outline=gray, fill=(255, 255, 255))
        d.line([x + 2, y + 4, x + 6, y + 4], fill=ink)
        if sign == "+":
            d.line([x + 4, y + 2, x + 4, y + 6], fill=ink)

    y = 171
    d.text((12, y), "[Project - (No Name)]", font=f, fill=ink); y += 21
    d.text((32, y), "[Java Files]", font=f, fill=ink); y += 21
    box(18, y + 5, "-"); d.text((32, y), "[VDM Files]", font=f, fill=ink); y += 21
    box(37, y + 5, "-"); d.text((51, y), "Default", font=f, fill=ink); y += 21
    for name in files:
        box(56, y + 5, "+"); d.text((70, y), name, font=f, fill=ink); y += 21


def _fit(transcript: str):
    mono = _font(_FONT_CANDIDATES, FONT_SIZE)
    cols = int((TEXT_RIGHT - TEXT_X) / mono.getlength("M"))
    lines: List[str] = []
    for line in transcript.split("\n"):
        lines.extend(textwrap.wrap(line, width=cols, subsequent_indent="  ", break_long_words=True,
                                   replace_whitespace=False) or [""])
    capacity = (TEXT_BOTTOM - TEXT_Y0) // LINE_H
    return mono, lines[-capacity:]  # como la ventana real: si no cabe, se ve el final


def render_toolbox(transcript: str, title: str, out_path: str, files: Sequence[str] = (), theme: str = "ubuntu",
                   when: Optional[datetime] = None, screen: Tuple[int, int] = dk.SCREEN) -> str:
    when = when or datetime.now()
    win = Image.open(TEMPLATE).convert("RGB")
    d = ImageDraw.Draw(win)
    _tree(d, files)
    mono, visible = _fit(transcript)
    y = TEXT_Y0
    for line in visible:
        d.text((TEXT_X, y), line, font=mono, fill=(0, 0, 0))
        y += LINE_H
    d.text((TEXT_X, 516), ">", font=_font(_BOLD_CANDIDATES, 15), fill=(0, 0, 0))

    ww, wh = int(win.width * SCALE), int(win.height * SCALE)
    win = win.resize((ww, wh), Image.LANCZOS)

    img, top_h, bottom_h, dock_w = dk._background(theme, screen)
    sw, sh = screen
    x0 = dock_w + (sw - dock_w - ww) // 2
    y0 = top_h + (sh - top_h - bottom_h - wh - TITLE_H) // 2
    d2 = ImageDraw.Draw(img, "RGBA")
    for i in range(14, 0, -2):
        d2.rounded_rectangle([x0 - i, y0 - i + 8, x0 + ww + i, y0 + TITLE_H + wh + i + 8], radius=10 + i, fill=(0, 0, 0, 10))
    d2.rectangle([x0, y0, x0 + ww, y0 + TITLE_H], fill=(58, 58, 64))
    ui_b = _font(dk._UI_BOLD, 15)
    shown = title
    while ui_b.getlength(shown) > ww - 200 and len(shown) > 8:
        shown = shown[:-4] + "…"
    d2.text((x0 + ww // 2 - ui_b.getlength(shown) / 2, y0 + 6), shown, font=ui_b, fill=(235, 235, 235))
    for k, c in enumerate([(120, 120, 120), (120, 120, 120), (233, 84, 32)]):
        cx = x0 + ww - 24 - k * 26
        d2.ellipse([cx - 8, y0 + TITLE_H // 2 - 8, cx + 8, y0 + TITLE_H // 2 + 8], fill=c)
    img.paste(win, (x0, y0 + TITLE_H))
    dk._bars(img, theme, when, screen)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path
