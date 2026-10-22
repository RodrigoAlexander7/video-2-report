# -*- coding: utf-8 -*-
"""Anotaciones sobrias de capturas: un contorno fino o una flecha, siempre ligados a algo que existe.

Reglas (las que faltaban en `figure-enhancer`):
  * La caja es solo contorno (sin relleno que oscurezca el texto) y no puede ocupar más de un cuarto de la figura.
  * No lleva etiqueta dentro de la imagen: la explicación va en el pie de figura.
  * La flecha termina junto al objetivo (a ``GAP`` px de su borde), nunca "en el aire".
  * Como máximo una anotación por figura.
El objetivo es una caja ya resuelta (texto hallado por OCR o rectángulo relativo al recorte), no coordenadas sueltas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageDraw

Box = Tuple[int, int, int, int]
ACCENT = (200, 49, 14)            # #C8310E, el color institucional de la plantilla
MAX_AREA_RATIO = 0.25
GAP = 6                           # separación entre la punta de la flecha y el objetivo
DIRECTIONS = ("auto", "left", "right", "up", "down")
STYLES = ("box", "arrow")
ALLOWED_KEYS = {"target", "rect", "style", "direction", "pad", "extend"}


class AnnotationError(ValueError):
    """La anotación pedida no es válida para esta figura."""


@dataclass
class AnnotationSpec:
    target: Optional[str] = None                                  # texto de la interfaz (OCR)
    rect: Optional[Tuple[float, float, float, float]] = None      # alternativa: fracciones del recorte
    style: str = "box"
    direction: str = "auto"
    pad: int = 6
    extend: Tuple[int, int, int, int] = (0, 0, 0, 0)               # px extra [izq, arriba, der, abajo] sobre el texto hallado


@dataclass
class Annotated:
    image: Image.Image
    box: Box
    tip: Optional[Tuple[int, int]] = None


def parse_annotation(raw: Optional[Dict[str, Any]], where: str = "annotate") -> Optional[AnnotationSpec]:
    if not raw:
        return None
    unknown = set(raw) - ALLOWED_KEYS
    if unknown:
        raise AnnotationError(f"{where}: claves desconocidas {sorted(unknown)} (válidas: {', '.join(sorted(ALLOWED_KEYS))})")
    spec = AnnotationSpec(style=raw.get("style", "box"), direction=raw.get("direction", "auto"), pad=int(raw.get("pad", 6)))
    if spec.style not in STYLES:
        raise AnnotationError(f"{where}: style '{spec.style}' inválido (usa {', '.join(STYLES)})")
    if spec.direction not in DIRECTIONS:
        raise AnnotationError(f"{where}: direction '{spec.direction}' inválida (usa {', '.join(DIRECTIONS)})")
    if "extend" in raw:
        e = raw["extend"]
        if not (isinstance(e, list) and len(e) == 4 and all(isinstance(v, int) and v >= 0 for v in e)):
            raise AnnotationError(f"{where}: 'extend' son 4 píxeles [izquierda, arriba, derecha, abajo], p. ej. [0, 0, 60, 0] para incluir el valor a la derecha")
        spec.extend = tuple(e)
    if ("target" in raw) == ("rect" in raw):
        raise AnnotationError(f"{where}: indica 'target' (texto de la interfaz) o 'rect' (fracciones del recorte), uno de los dos")
    if "target" in raw:
        if not isinstance(raw["target"], str) or not raw["target"].strip():
            raise AnnotationError(f"{where}: 'target' debe ser un texto visible en la captura")
        spec.target = raw["target"]
    else:
        r = raw["rect"]
        if not (isinstance(r, list) and len(r) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in r) and r[0] < r[2] and r[1] < r[3]):
            raise AnnotationError(f"{where}: 'rect' son 4 fracciones [x0, y0, x1, y1] entre 0 y 1 del recorte")
        spec.rect = tuple(float(v) for v in r)
    return spec


def _clamp(box: Box, size: Tuple[int, int]) -> Box:
    return max(0, box[0]), max(0, box[1]), min(size[0], box[2]), min(size[1], box[3])


def check_area(box: Box, size: Tuple[int, int]) -> None:
    ratio = (box[2] - box[0]) * (box[3] - box[1]) / float(size[0] * size[1])
    if ratio > MAX_AREA_RATIO:
        raise AnnotationError(f"la anotación cubre el {ratio:.0%} de la figura (máximo {MAX_AREA_RATIO:.0%}): señala el control "
                              "concreto o quita la anotación; un recuadro que lo encierra todo no informa")


def stroke(size: Tuple[int, int]) -> int:
    return max(3, round(size[0] / 320))


def outline(img: Image.Image, box: Box, pad: int = 6) -> Annotated:
    """Contorno fino alrededor de ``box`` (sin relleno)."""
    out = img.convert("RGB").copy()
    padded = _clamp((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad), out.size)
    check_area(padded, out.size)
    ImageDraw.Draw(out).rectangle(padded, outline=ACCENT, width=stroke(out.size))
    return Annotated(out, padded)


def _free_space(box: Box, size: Tuple[int, int]) -> Dict[str, int]:
    return {"left": box[0], "right": size[0] - box[2], "up": box[1], "down": size[1] - box[3]}


def arrow_to(img: Image.Image, box: Box, direction: str = "auto") -> Annotated:
    """Flecha cuya punta queda a ``GAP`` px del borde de ``box`` y que apunta hacia él desde el lado con más espacio."""
    out = img.convert("RGB").copy()
    size = out.size
    length = max(60, round(min(size) * 0.18))
    free = _free_space(box, size)
    if direction == "auto":
        direction = max(free, key=lambda k: free[k])
    if free[direction] < GAP + length // 2:
        raise AnnotationError(f"no hay espacio para una flecha desde '{direction}' (quedan {free[direction]} px): "
                              "amplía el recorte o usa style = \"box\"")
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    tip = {"left": (box[0] - GAP, cy), "right": (box[2] + GAP, cy), "up": (cx, box[1] - GAP), "down": (cx, box[3] + GAP)}[direction]
    dx, dy = {"left": (1, 0), "right": (-1, 0), "up": (0, 1), "down": (0, -1)}[direction]   # sentido de avance hacia la punta
    tail = (tip[0] - dx * length, tip[1] - dy * length)
    tail = (min(max(tail[0], 0), size[0]), min(max(tail[1], 0), size[1]))
    width, head = stroke(size), max(14, round(length * 0.3))
    draw = ImageDraw.Draw(out)
    angle = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
    base = (tip[0] - head * math.cos(angle), tip[1] - head * math.sin(angle))
    draw.line([tail, base], fill=ACCENT, width=width)
    spread = math.radians(28)
    draw.polygon([tip,
                  (tip[0] - head * 1.15 * math.cos(angle - spread), tip[1] - head * 1.15 * math.sin(angle - spread)),
                  (tip[0] - head * 1.15 * math.cos(angle + spread), tip[1] - head * 1.15 * math.sin(angle + spread))], fill=ACCENT)
    return Annotated(out, box, (round(tip[0]), round(tip[1])))


def distance_to_box(point: Tuple[float, float], box: Box) -> float:
    dx = max(box[0] - point[0], 0, point[0] - box[2])
    dy = max(box[1] - point[1], 0, point[1] - box[3])
    return math.hypot(dx, dy)


def annotate(img: Image.Image, spec: AnnotationSpec, target_box: Box) -> Annotated:
    """Dibuja la anotación sobre ``img`` (recorte) para ``target_box`` (en coordenadas del recorte)."""
    box = _clamp(target_box, img.size)
    if spec.style == "arrow":
        check_area(box, img.size)
        return arrow_to(img, box, spec.direction)
    return outline(img, box, spec.pad)
