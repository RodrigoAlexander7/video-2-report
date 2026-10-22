# -*- coding: utf-8 -*-
"""Recortes semánticos de una captura de Unity: por panel (pestaña + bordes), entre dos textos o alrededor de uno.

Nada de coordenadas escritas a mano en píxeles: el panel se ubica por el título de su pestaña (OCR) y sus bordes
por las franjas oscuras que separan los paneles de Unity; los límites verticales dentro de un panel, por el texto de
los componentes (`desde = "Rigidbody"`, `hasta = "Capsule Collider"`). Al final el recorte nunca corta una línea de texto.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from .ocr import Box, Word, find_phrase

PANEL_TABS = {"inspector": "Inspector", "hierarchy": "Hierarchy", "project": "Project", "console": "Console",
              "scene": "Scene", "game": "Game"}
GAP_RATIO = 0.62          # una franja separadora es <62 % de la luminosidad del panel
GAP_STD = 4.0             # y casi uniforme a lo largo de su longitud
GAP_MIN_PX = 2            # al menos 2 px de grosor (las líneas de 1 px entre componentes no son bordes)
ALLOWED_KEYS = {"rect", "panel", "desde", "hasta", "around", "margin", "pad", "include_to", "height"}


class CropError(ValueError):
    """El recorte pedido no se puede resolver con este fotograma."""


@dataclass
class CropSpec:
    rect: Optional[Tuple[float, float, float, float]] = None     # fracciones 0-1 del fotograma
    panel: Optional[str] = None
    desde: Optional[str] = None
    hasta: Optional[str] = None
    around: Optional[str] = None
    margin: Tuple[int, int] = (320, 140)
    pad: int = 10
    include_to: bool = False
    height: Optional[int] = None          # alto máximo (px) del recorte de panel, contado desde su borde superior


def parse_crop(raw: Optional[Dict[str, Any]], where: str = "crop") -> Optional[CropSpec]:
    if not raw:
        return None
    unknown = set(raw) - ALLOWED_KEYS
    if unknown:
        raise CropError(f"{where}: claves desconocidas {sorted(unknown)} (válidas: {', '.join(sorted(ALLOWED_KEYS))})")
    spec = CropSpec()
    if "rect" in raw:
        r = raw["rect"]
        if not (isinstance(r, list) and len(r) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in r) and r[0] < r[2] and r[1] < r[3]):
            raise CropError(f"{where}: 'rect' son 4 fracciones del fotograma [x0, y0, x1, y1] entre 0 y 1")
        spec.rect = tuple(float(v) for v in r)
    if "panel" in raw:
        if raw["panel"] not in PANEL_TABS:
            raise CropError(f"{where}: panel '{raw['panel']}' desconocido (usa {', '.join(PANEL_TABS)})")
        spec.panel = raw["panel"]
    for key in ("desde", "hasta", "around"):
        if key in raw:
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise CropError(f"{where}: '{key}' debe ser un texto de la interfaz")
            setattr(spec, key, raw[key])
    if "margin" in raw:
        m = raw["margin"]
        if not (isinstance(m, list) and len(m) == 2 and all(isinstance(v, int) and v >= 0 for v in m)):
            raise CropError(f"{where}: 'margin' son [horizontal, vertical] en píxeles")
        spec.margin = (m[0], m[1])
    spec.pad = int(raw.get("pad", spec.pad))
    spec.include_to = bool(raw.get("include_to", False))
    if "height" in raw:
        if not (isinstance(raw["height"], int) and raw["height"] >= 60):
            raise CropError(f"{where}: 'height' es un alto en píxeles (mínimo 60)")
        spec.height = raw["height"]
        if not spec.panel:
            raise CropError(f"{where}: 'height' solo aplica con 'panel'")
    if (spec.desde or spec.hasta) and not spec.panel:
        raise CropError(f"{where}: 'desde'/'hasta' necesitan 'panel' para fijar el ancho")
    if sum(x is not None for x in (spec.rect, spec.panel, spec.around)) > 1:
        raise CropError(f"{where}: usa solo una de 'rect', 'panel' o 'around'")
    return spec


def _gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float32)


def _runs(mask: np.ndarray, min_len: int) -> np.ndarray:
    """Marca solo los tramos de ``True`` de al menos ``min_len`` valores consecutivos."""
    out = np.zeros_like(mask)
    start = None
    for i, v in enumerate(np.append(mask, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out[start:i] = True
            start = None
    return out


def panel_bounds(img: Image.Image, tab: Box) -> Box:
    """Bordes del panel que contiene la pestaña ``tab``: la franja oscura más cercana por cada lado (o el borde de la imagen)."""
    g = _gray(img)
    height, width = g.shape
    x0, y0, x1, y1 = tab

    # Columnas: franja bajo la pestaña (donde ya hay contenido del panel y no su barra de título)
    band = g[min(height - 1, y1 + 20):min(height, y1 + 260), :]
    if band.size == 0:
        band = g
    m, s = band.mean(axis=0), band.std(axis=0)
    bg = float(np.median(m))
    col_sep = _runs((m < GAP_RATIO * bg) & (s < GAP_STD), GAP_MIN_PX)
    left = 0
    for x in range(max(x0 - 4, 0), -1, -1):
        if col_sep[x]:
            left = x
            while left < width and col_sep[left]:
                left += 1
            break
    right = width
    for x in range(min(x1 + 4, width - 1), width):
        if col_sep[x]:
            right = x
            break

    # Filas: dentro del ancho del panel
    cols = g[:, min(left + 5, width - 1):max(right - 5, left + 6)]
    rm, rs = cols.mean(axis=1), cols.std(axis=1)
    rbg = float(np.median(rm[min(height - 1, y1 + 10):min(height, y1 + 200)]))
    row_sep = _runs((rm < GAP_RATIO * rbg) & (rs < GAP_STD), GAP_MIN_PX)
    top = max(0, y0 - 12)
    for y in range(max(y0 - 2, 0), max(-1, y0 - 60), -1):
        if row_sep[y]:
            top = y
            while top < height and row_sep[top]:
                top += 1
            break
    bottom = height
    for y in range(min(y1 + 40, height - 1), height):
        if row_sep[y]:
            bottom = y
            break
    return left, top, right, bottom


def snap_to_words(box: Box, words: Sequence[Word], size: Tuple[int, int], max_grow: int = 48) -> Box:
    """Amplía el recorte para que ninguna palabra quede cortada por un borde (hasta ``max_grow`` px por lado)."""
    x0, y0, x1, y1 = box
    W, H = size
    for _ in range(3):
        changed = False
        for w in words:
            wx0, wy0, wx1, wy1 = w.box
            inter = (min(x1, wx1) > max(x0, wx0)) and (min(y1, wy1) > max(y0, wy0))
            inside = wx0 >= x0 and wy0 >= y0 and wx1 <= x1 and wy1 <= y1
            if not inter or inside:
                continue
            nx0, ny0 = min(x0, wx0), min(y0, wy0)
            nx1, ny1 = max(x1, wx1), max(y1, wy1)
            if (x0 - nx0 <= max_grow and y0 - ny0 <= max_grow and nx1 - x1 <= max_grow and ny1 - y1 <= max_grow):
                if (nx0, ny0, nx1, ny1) != (x0, y0, x1, y1):
                    x0, y0, x1, y1 = nx0, ny0, nx1, ny1
                    changed = True
        if not changed:
            break
    return max(0, x0), max(0, y0), min(W, x1), min(H, y1)


def resolve_crop(img: Image.Image, words: Sequence[Word], spec: Optional[CropSpec]) -> Box:
    """Caja (px del fotograma) del recorte pedido. Sin ``spec``: el fotograma completo."""
    W, H = img.size
    if spec is None:
        return 0, 0, W, H
    if spec.rect is not None:
        x0, y0, x1, y1 = spec.rect
        box = (round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H))
    elif spec.panel is not None:
        tab = find_phrase(words, PANEL_TABS[spec.panel])
        if tab is None:
            raise CropError(f"no se ve la pestaña «{PANEL_TABS[spec.panel]}» en el fotograma: el panel '{spec.panel}' no está visible")
        left, top, right, bottom = panel_bounds(img, tab)
        if spec.desde:
            a = find_phrase(words, spec.desde)
            if a is None:
                raise CropError(f"no se encuentra el texto «{spec.desde}» (desde) en el fotograma")
            top = max(top, a[1] - spec.pad)
        if spec.hasta:
            b = find_phrase(words, spec.hasta)
            if b is None:
                raise CropError(f"no se encuentra el texto «{spec.hasta}» (hasta) en el fotograma")
            bottom = min(bottom, (b[3] + spec.pad) if spec.include_to else (b[1] - 4))
        if spec.height:
            bottom = min(bottom, top + spec.height)
        box = (left, top, right, bottom)
    elif spec.around is not None:
        a = find_phrase(words, spec.around)
        if a is None:
            raise CropError(f"no se encuentra el texto «{spec.around}» (around) en el fotograma")
        mx, my = spec.margin
        box = (a[0] - mx, a[1] - my, a[2] + mx, a[3] + my)
    else:
        box = (0, 0, W, H)
    box = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
    if box[2] - box[0] < 40 or box[3] - box[1] < 40:
        raise CropError(f"el recorte quedó demasiado pequeño ({box[2] - box[0]}x{box[3] - box[1]} px); revisa 'desde'/'hasta'")
    return snap_to_words(box, words, (W, H))
