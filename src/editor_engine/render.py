# -*- coding: utf-8 -*-
"""Composición HTML de la ventana de editor y captura PNG con Chrome headless (2x).

Las dimensiones se calculan antes de capturar (líneas x alto de fila, columnas x ancho de carácter),
por eso la imagen queda del tamaño exacto del contenido: sin márgenes vacíos ni recortes.
"""

from __future__ import annotations

import base64
import subprocess
import tempfile
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from ..core.chrome import BrowserError, find_chrome
from .extract import Row
from .highlight import Tok

ASSETS = Path(__file__).parent / "assets"
THEMES_DIR = Path(__file__).parent / "themes"
FONT_PX, LINE_PX = 18, 27
CHAR_W = FONT_PX * 0.6                    # JetBrains Mono: avance de 600/1000 em
TABS_H, CRUMBS_H, PAD_TOP, PAD_BOTTOM = 42, 34, 14, 16
NUM_LEFT, NUM_GAP, CODE_RIGHT, MIN_W = 24, 28, 32, 560
SCALE = 2
TIMEOUT_S = 60
MIN_PT, DOC_WIDTH_IN = 8.0, 6.0           # texto mínimo legible al insertar la imagen a 6 in de ancho
THEMES = ("dark", "light")

_FONTS = {("normal", 400): "JetBrainsMono-Regular.ttf", ("normal", 700): "JetBrainsMono-Bold.ttf",
          ("italic", 400): "JetBrainsMono-Italic.ttf", ("italic", 700): "JetBrainsMono-BoldItalic.ttf"}
_UI_STACK = '"Inter", "Liberation Sans", "Segoe UI", Arial, sans-serif'
_BADGES = {"csharp": ("C#", "#68217a", "#ffffff"), "python": ("Py", "#3776ab", "#ffd43b"), "python3": ("Py", "#3776ab", "#ffd43b"),
           "java": ("J", "#c0532a", "#ffffff"), "javascript": ("JS", "#f0db4f", "#1e1e1e"), "typescript": ("TS", "#3178c6", "#ffffff"),
           "cpp": ("C+", "#00599c", "#ffffff"), "c": ("C", "#5c6bc0", "#ffffff"), "json": ("{}", "#8a8f98", "#ffffff"),
           "toml": ("T", "#9c4221", "#ffffff"), "typst": ("t", "#239dad", "#ffffff"), "vdmpp": ("VD", "#6a5acd", "#ffffff")}


@dataclass
class Frame:
    rows: List[Row]
    lines_tokens: dict                    # no de línea -> [(clase, texto)]
    cols: int
    focus: set
    theme: str
    path: str                             # ruta mostrada en el breadcrumb
    title: str                            # nombre de la pestaña
    lang: str
    chrome: bool = True
    whitespace: bool = True
    dedent_by: int = 0

    @property
    def show_crumbs(self) -> bool:
        """El breadcrumb solo aparece si hay una ruta con carpetas; con solo el nombre repetiría la pestaña."""
        return self.chrome and len([s for s in self.path.replace("\\", "/").split("/") if s]) > 1


def legibility_pt(width_px: float, doc_width_in: float = DOC_WIDTH_IN) -> float:
    """Tamaño aparente del texto (pt) al insertar la imagen con ``doc_width_in`` pulgadas de ancho."""
    return FONT_PX * 0.75 * (doc_width_in * 96) / width_px


def size_of(rows: List[Row], cols: int, chrome: bool, crumbs: bool = True) -> Tuple[int, int]:
    digits = max(3, len(str(max((r.no or 0 for r in rows), default=1))))
    width = NUM_LEFT + digits * CHAR_W + NUM_GAP + cols * CHAR_W + CODE_RIGHT
    height = (TABS_H + (CRUMBS_H if crumbs else 0) if chrome else 0) + PAD_TOP + len(rows) * LINE_PX + PAD_BOTTOM
    return max(MIN_W, int(width + 0.999)), height


def _font_faces() -> str:
    css = []
    for (style, weight), name in _FONTS.items():
        data = base64.b64encode((ASSETS / "fonts" / name).read_bytes()).decode()
        css.append(f'@font-face{{font-family:"Editor Mono";font-style:{style};font-weight:{weight};'
                   f'src:url(data:font/ttf;base64,{data}) format("truetype");}}')
    return "\n".join(css)


def _tokens_html(tokens: List[Tok], whitespace: bool) -> str:
    html: List[str] = []
    first = True
    for cls, text in tokens:
        if first and whitespace and text.strip() == "":
            html.append(_indent_html(text))
        elif first and whitespace and text[:1] == " ":
            lead = len(text) - len(text.lstrip(" "))
            html.append(_indent_html(text[:lead]))
            html.append(_span(cls, text[lead:]))
        else:
            html.append(_span(cls, text))
        first = False
    return "".join(html)


def _span(cls: str, text: str) -> str:
    return f'<span class="{cls}">{escape(text)}</span>' if cls else escape(text)


def _indent_html(spaces: str) -> str:
    n, out = len(spaces), []
    for _ in range(n // 4):
        out.append('<span class="ig"> ···</span>')
    if n % 4:
        out.append(f'<span class="ig2">{"·" * (n % 4)}</span>')
    return "".join(out)


def _indent_of(row: Row) -> int:
    return len(row.text) - len(row.text.lstrip(" "))


def _blank_guides(rows: List[Row], idx: int, whitespace: bool) -> str:
    """Línea en blanco: las guías de indentación continúan (como en el editor) con la menor sangría vecina."""
    if not whitespace:
        return ""
    def neighbour(step: int) -> Optional[int]:
        for j in range(idx + step, len(rows) if step > 0 else -1, step):
            if rows[j].kind != "code":
                return None
            if rows[j].text.strip():
                return _indent_of(rows[j])
        return None
    near = [n for n in (neighbour(-1), neighbour(1)) if n is not None]
    return "".join('<span class="ig">    </span>' for _ in range(min(near, default=0) // 4))


def _badge(lang: str) -> str:
    label, bg, fg = _BADGES.get(lang, ("≡", "#7b8394", "#ffffff"))
    return f'<span class="badge" style="background:{bg};color:{fg}">{escape(label)}</span>'


def compose_html(fr: Frame) -> Tuple[str, int, int]:
    width, height = size_of(fr.rows, fr.cols, fr.chrome, fr.show_crumbs)
    digits = max(3, len(str(max((r.no or 0 for r in fr.rows), default=1))))
    no_w = NUM_LEFT + digits * CHAR_W
    parts: List[str] = []
    if fr.chrome:
        segs = [s for s in fr.path.replace("\\", "/").split("/") if s]
        crumbs = '<span class="sep">›</span>'.join(f"<span>{escape(s)}</span>" for s in segs[:-1])
        crumbs += ('<span class="sep">›</span>' if crumbs else "") + f'<span class="last">{_badge(fr.lang)}{escape(segs[-1] if segs else fr.title)}</span>'
        parts.append(f'<div class="tabs"><div class="tab">{_badge(fr.lang)}<span>{escape(fr.title)}</span></div></div>')
        if fr.show_crumbs:
            parts.append(f'<div class="crumbs">{crumbs}</div>')
    parts.append('<div class="code">')
    for idx, r in enumerate(fr.rows):
        if r.kind == "fold":
            parts.append(f'<div class="ln fold"><span class="no" style="width:{no_w}px"></span>'
                         f'<span class="tx" style="padding-left:{NUM_GAP}px">⋯</span></div>')
            continue
        toks = fr.lines_tokens.get(r.no, [])
        if fr.dedent_by:
            toks = _cut_indent(toks, fr.dedent_by)
        body = _tokens_html(toks, fr.whitespace) if r.text.strip() else _blank_guides(fr.rows, idx, fr.whitespace)
        hi = " hi" if r.no in fr.focus else ""
        parts.append(f'<div class="ln{hi}"><span class="no" style="width:{no_w}px">{r.no}</span>'
                     f'<span class="tx" style="padding-left:{NUM_GAP}px">{body}</span></div>')
    parts.append("</div>")
    css = (THEMES_DIR / "base.css").read_text(encoding="utf-8") + (THEMES_DIR / f"{fr.theme}.css").read_text(encoding="utf-8")
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{escape(fr.title)}</title>'
            f"<style>{_font_faces()}\n:root{{--ui:{_UI_STACK};}}\n{css}\n.ig2{{color:var(--dots)}}</style></head><body>"
            f'<div class="win" style="width:{width}px;height:{height}px">{"".join(parts)}</div></body></html>')
    return html, width, height


def _cut_indent(tokens: List[Tok], n: int) -> List[Tok]:
    out, left = [], n
    for cls, text in tokens:
        if left:
            cut = min(left, len(text) - len(text.lstrip(" ")))
            text, left = text[cut:], left - cut
            if text:
                left = 0
        if text:
            out.append((cls, text))
    return out


def capture(html: str, width: int, height: int, out_png: Path) -> Path:
    """Captura PNG a ``SCALE``x. Ventana más alta que la imagen y recorte final: la altura del viewport
    de Chrome headless varía entre versiones, así el resultado es siempre del tamaño calculado."""
    out_png = Path(out_png).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="editor-chrome-") as tmp:
        page, shot = Path(tmp) / "snippet.html", Path(tmp) / "shot.png"
        page.write_text(html, encoding="utf-8")
        cmd = [find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--disable-extensions", f"--force-device-scale-factor={SCALE}", f"--user-data-dir={Path(tmp) / 'profile'}",
               f"--window-size={max(width, 500)},{height + 200}", "--virtual-time-budget=3000",
               f"--screenshot={shot}", page.as_uri()]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            raise BrowserError(f"Chrome superó {TIMEOUT_S}s sin terminar") from exc
        if proc.returncode != 0 or not shot.is_file():
            raise BrowserError(f"Chrome no produjo la captura (código {proc.returncode}):\n{proc.stderr.strip()[-600:]}")
        img = Image.open(shot).convert("RGB")
        need = (width * SCALE, height * SCALE)
        if img.width < need[0] or img.height < need[1]:
            raise BrowserError(f"La captura mide {img.size} y se esperaban al menos {need}")
        img.crop((0, 0, *need)).save(out_png, optimize=True, dpi=(96 * SCALE, 96 * SCALE))
    return out_png
