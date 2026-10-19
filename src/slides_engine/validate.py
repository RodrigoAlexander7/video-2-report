# -*- coding: utf-8 -*-
"""Reglas duras del deck: tema claro, cero animaciones, sin recursos externos y contraste legible."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

MIN_BG_LUMINANCE = {"color-bg": 0.85, "color-surface": 0.70, "color-canvas": 0.70}
CONTRAST_PAIRS: Tuple[Tuple[str, str, float], ...] = (
    ("color-text", "color-bg", 4.5), ("color-text", "color-surface", 4.5),
    ("color-text-muted", "color-bg", 4.5), ("color-text-muted", "color-surface", 4.5),
    ("color-primary", "color-bg", 4.5), ("color-accent", "color-bg", 4.5), ("color-link", "color-bg", 4.5),
    ("color-on-primary", "color-primary", 4.5), ("color-on-accent", "color-accent", 4.5),
)
REQUIRED_TOKENS = tuple(sorted({t for p in CONTRAST_PAIRS for t in p[:2]} | set(MIN_BG_LUMINANCE)))

FORBIDDEN_CSS = (
    (r"@keyframes", "@keyframes (animaciones)"),
    (r"(?<![\w-])animation(?:-[a-z-]+)?\s*:", "propiedad animation"),
    (r"(?<![\w-])transition(?:-[a-z-]+)?\s*:", "propiedad transition"),
    (r"scroll-behavior\s*:\s*smooth", "scroll-behavior: smooth"),
    (r"prefers-color-scheme\s*:\s*dark", "media query prefers-color-scheme: dark (solo tema claro)"),
    (r"color-scheme\s*:[^;}]*dark", "color-scheme con dark (solo tema claro)"),
    (r"@import", "@import (recursos externos)"),
    (r"url\(\s*[\"']?https?:", "url() externa"),
)
FORBIDDEN_MARKUP = (
    (r"<script", "etiqueta <script> (los decks no llevan JavaScript)"),
    (r"<link\b", "etiqueta <link> (recursos externos)"),
    (r"<iframe|<video|<audio|<embed|<object", "contenido multimedia incrustado"),
    (r"\b(?:src|href)\s*=\s*[\"']https?:", "recurso externo por URL"),
)


def lint_html(html: str) -> List[str]:
    """Problemas del HTML ya renderizado (vacío = correcto). Solo mira CSS, atributos y etiquetas, no la prosa."""
    problems: List[str] = []
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    inline_styles = "\n".join(re.findall(r'\bstyle\s*=\s*"([^"]*)"', html))
    css = re.sub(r"/\*.*?\*/", "", styles, flags=re.S) + "\n" + inline_styles   # los comentarios pueden nombrar lo prohibido
    for pattern, what in FORBIDDEN_CSS:
        if re.search(pattern, css, re.I):
            problems.append(f"CSS no permitido: {what}")
    markup = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
    for pattern, what in FORBIDDEN_MARKUP:
        if re.search(pattern, markup, re.I):
            problems.append(f"HTML no permitido: {what}")
    if not re.search(r"color-scheme\s*:\s*light", css):
        problems.append("falta `color-scheme: light` en el CSS")
    return problems


# --------------------------------------------------------------------------- tema: tokens y contraste
def _custom_properties(css: str) -> Dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+);", css)}


def _resolve(value: str, props: Dict[str, str], depth: int = 0) -> str:
    m = re.fullmatch(r"var\(--([\w-]+)\)", value.strip())
    if m and depth < 8:
        return _resolve(props.get(m.group(1), ""), props, depth + 1)
    return value.strip()


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    h = value.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    def lin(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    a, b = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def check_theme(css: str, name: str = "tema") -> List[str]:
    """Tokens semánticos presentes y en hex, fondos claros y pares de color con contraste WCAG AA."""
    props = _custom_properties(css)
    problems: List[str] = []
    colors: Dict[str, str] = {}
    for token in REQUIRED_TOKENS:
        value = _resolve(props.get(token, ""), props)
        if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value):
            problems.append(f"{name}: --{token} debe resolverse a un color hex (valor: '{value or 'ausente'}')")
        else:
            colors[token] = value
    for token, minimum in MIN_BG_LUMINANCE.items():
        if token in colors and relative_luminance(colors[token]) < minimum:
            problems.append(f"{name}: --{token} ({colors[token]}) es demasiado oscuro para un tema claro "
                            f"(luminancia {relative_luminance(colors[token]):.2f} < {minimum})")
    for fg, bg, minimum in CONTRAST_PAIRS:
        if fg in colors and bg in colors:
            ratio = contrast_ratio(colors[fg], colors[bg])
            if ratio < minimum:
                problems.append(f"{name}: contraste {ratio:.2f}:1 entre --{fg} y --{bg} (mínimo {minimum}:1)")
    return problems
