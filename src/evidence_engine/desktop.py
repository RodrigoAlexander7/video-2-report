# -*- coding: utf-8 -*-
"""Imagen de escritorio completo (pantalla entera) alrededor de una transcripción real.

IMPORTANTE: es una composición, no una captura de píxeles de un programa en ejecución.
Lo que se muestra dentro de la ventana de terminal es la transcripción literal de la
ejecución real; el fondo, la barra del sistema y el marco de la ventana son dibujados.
El manifiesto lo registra como render = "desktop-frame".
"""

import os
import textwrap
from datetime import datetime
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from .render import CMD, DIM, ERR, FG, _BOLD_CANDIDATES, _FONT_CANDIDATES, _font

_UI = ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
_UI_BOLD = ["/usr/share/fonts/truetype/lato/Lato-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
_DAYS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

THEMES = ("ubuntu", "windows")
SCREEN = (1920, 1080)


def _gradient(size: Tuple[int, int], top: Tuple[int, int, int], bottom: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def _wrap(lines: List[str], cols: int) -> List[str]:
    out: List[str] = []
    for line in lines:
        if len(line) <= cols:
            out.append(line)
            continue
        parts = textwrap.wrap(line, width=cols, subsequent_indent="  ", break_long_words=True, replace_whitespace=False)
        out.extend(parts or [""])
    return out


def _color(line: str):
    if line.startswith("> "):
        return CMD, True
    if "Error" in line or line.startswith("Runtime"):
        return ERR, False
    if line.startswith(("Executed in", "Parsed", "Type checked", "Initialized", "Interpreter", "MainThread")):
        return DIM, False
    return FG, False


def _background(theme: str, screen: Tuple[int, int]):
    """Fondo del escritorio. Devuelve (imagen, alto barra superior, alto barra inferior, ancho del dock)."""
    ubuntu = theme == "ubuntu"
    top_h, bottom_h, dock_w = (36, 0, 84) if ubuntu else (0, 64, 0)
    img = _gradient(screen, (44, 0, 30), (233, 84, 32)) if ubuntu else _gradient(screen, (8, 40, 92), (30, 120, 200))
    return img, top_h, bottom_h, dock_w


def _bars(img: Image.Image, theme: str, when: datetime, screen: Tuple[int, int]) -> None:
    """Barra del sistema y dock; el reloj muestra el momento real de la captura."""
    sw, sh = screen
    ubuntu = theme == "ubuntu"
    top_h, bottom_h, dock_w = (36, 0, 84) if ubuntu else (0, 64, 0)
    d = ImageDraw.Draw(img, "RGBA")
    ui, ui_b = _font(_UI, 17), _font(_UI_BOLD, 17)
    clock = f"{_DAYS[when.weekday()]} {when.day:02d} {_MONTHS[when.month - 1]}  {when:%H:%M}"
    if ubuntu:
        d.rectangle([0, 0, sw, top_h], fill=(18, 18, 18, 235))
        d.text((16, 8), "Actividades", font=ui, fill=(235, 235, 235))
        d.text((sw // 2 - ui_b.getlength(clock) / 2, 8), clock, font=ui_b, fill=(235, 235, 235))
        d.rectangle([0, top_h, dock_w, sh], fill=(30, 30, 30, 215))
        for i, c in enumerate([(233, 84, 32), (90, 160, 230), (110, 200, 120), (240, 190, 60), (170, 120, 210)]):
            iy = top_h + 28 + i * 74
            d.rounded_rectangle([18, iy, 66, iy + 48], radius=12, fill=c)
        d.rounded_rectangle([18, top_h + 28, 66, top_h + 76], radius=12, outline=(255, 255, 255, 200), width=2)
    else:
        d.rectangle([0, sh - bottom_h, sw, sh], fill=(20, 28, 40, 235))
        start = sw // 2 - 190
        for i, c in enumerate([(0, 120, 215), (90, 160, 230), (110, 200, 120), (240, 190, 60), (200, 70, 70), (170, 120, 210)]):
            ix = start + i * 64
            d.rounded_rectangle([ix, sh - bottom_h + 12, ix + 40, sh - bottom_h + 52], radius=8, fill=c)
        d.text((sw - 150, sh - bottom_h + 10), f"{when:%H:%M}", font=ui_b, fill=(235, 235, 235))
        d.text((sw - 150, sh - bottom_h + 34), f"{when.day:02d}/{when.month:02d}/{when.year}", font=ui, fill=(210, 210, 210))



def render_desktop(transcript: str, title: str, out_path: str, theme: str = "ubuntu",
                   when: Optional[datetime] = None, screen: Tuple[int, int] = SCREEN) -> str:
    if theme not in THEMES:
        raise ValueError(f"tema desconocido {theme!r}; disponibles: {', '.join(THEMES)}")
    when = when or datetime.now()
    sw, sh = screen
    ubuntu = theme == "ubuntu"
    top_h, bottom_h, dock_w = (36, 0, 84) if ubuntu else (0, 64, 0)

    img, top_h, bottom_h, dock_w = _background(theme, screen)
    d = ImageDraw.Draw(img, "RGBA")
    ui, ui_b = _font(_UI, 17), _font(_UI_BOLD, 17)

    # --- ventana: tamaño de letra y alto según el contenido ---
    win_x0 = dock_w + 70
    win_w = sw - win_x0 - 70
    avail_h = sh - top_h - bottom_h - 90
    title_h, pad = 46, 22
    raw = transcript.split("\n")
    for size in (26, 24, 22, 20, 18):
        mono, mono_b = _font(_FONT_CANDIDATES, size), _font(_BOLD_CANDIDATES, size)
        cols = int((win_w - 2 * pad) / mono.getlength("M"))
        lines = _wrap(raw, cols)
        lh = int(size * 1.4)
        need = title_h + 2 * pad + lh * len(lines)
        if need <= avail_h:
            break
    visible = lines
    if need > avail_h:  # como una terminal real: se ve el final; el log completo queda en el manifiesto
        keep = (avail_h - title_h - 2 * pad) // lh
        visible = lines[-keep:]
        need = avail_h
    win_h = need
    win_y0 = top_h + (sh - top_h - bottom_h - win_h) // 2
    win_x1, win_y1 = win_x0 + win_w, win_y0 + win_h

    # sombra y marco
    for i in range(14, 0, -2):
        d.rounded_rectangle([win_x0 - i, win_y0 - i + 8, win_x1 + i, win_y1 + i + 8], radius=14 + i, fill=(0, 0, 0, 10))
    d.rounded_rectangle([win_x0, win_y0, win_x1, win_y1], radius=12, fill=(24, 24, 28))
    d.rounded_rectangle([win_x0, win_y0, win_x1, win_y0 + title_h], radius=12, fill=(58, 58, 64))
    d.rectangle([win_x0, win_y0 + title_h - 12, win_x1, win_y0 + title_h], fill=(58, 58, 64))
    shown = title
    while ui_b.getlength(shown) > win_w - 220 and len(shown) > 8:
        shown = shown[:-4] + "…"
    d.text((win_x0 + win_w // 2 - ui_b.getlength(shown) / 2, win_y0 + 12), shown, font=ui_b, fill=(235, 235, 235))
    for k, c in enumerate([(120, 120, 120), (120, 120, 120), (233, 84, 32)]):
        cx = win_x1 - 30 - k * 30
        d.ellipse([cx - 9, win_y0 + title_h // 2 - 9, cx + 9, win_y0 + title_h // 2 + 9], fill=c)

    # --- texto ---
    y = win_y0 + title_h + pad
    for line in visible:
        color, bold = _color(line)
        d.text((win_x0 + pad, y), line, font=mono_b if bold else mono, fill=color)
        y += lh

    _bars(img, theme, when, screen)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path
