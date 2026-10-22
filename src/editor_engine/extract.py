# -*- coding: utf-8 -*-
"""Selección de líneas de un archivo real: rangos, enfoque, dedent y límites de legibilidad."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple, Union

MAX_LINES = 40          # más de esto deja de ser "un fragmento"
MAX_COLS = 100         # techo de cordura; el límite real lo da la legibilidad (render.MIN_PT, ~78 columnas)
TAB_WIDTH = 4

Range = Tuple[int, int]
LinesSpec = Union[str, int, Sequence[Union[str, int]], None]


class SnippetError(ValueError):
    """Uno o más problemas en un fragmento; ``problems`` los lista todos."""

    def __init__(self, problems: Iterable[str]):
        self.problems = list(problems)
        super().__init__("\n".join(f"  - {p}" for p in self.problems))


@dataclass
class Row:
    """Fila a dibujar: línea de código (``no`` real del archivo) o marcador de tramo omitido."""
    kind: str                    # "code" | "fold"
    no: Optional[int] = None
    text: str = ""


def parse_ranges(spec: LinesSpec, total: int) -> List[Range]:
    """``"12-30"``, ``12``, ``["12-18", "24-30"]`` o ``None`` (archivo entero) -> rangos 1-indexados, ordenados."""
    if spec is None:
        return [(1, total)]
    items = [spec] if isinstance(spec, (str, int)) else list(spec)
    ranges: List[Range] = []
    problems: List[str] = []
    for item in items:
        text = str(item).strip()
        try:
            a, _, b = text.partition("-")
            start, end = int(a), int(b or a)
        except ValueError:
            problems.append(f"rango de líneas inválido: {item!r} (usa \"12-30\" o 12)")
            continue
        if start < 1 or end < start or end > total:
            problems.append(f"rango {text} fuera del archivo (tiene {total} líneas)")
            continue
        ranges.append((start, end))
    if problems:
        raise SnippetError(problems)
    ranges.sort()
    for (_, e1), (s2, _) in zip(ranges, ranges[1:]):
        if s2 <= e1:
            raise SnippetError([f"los rangos {ranges} se solapan"])
    return ranges


def trim_blank_edges(lines: List[str], ranges: List[Range]) -> List[Range]:
    """Quita líneas en blanco al inicio y al final: la imagen muestra solo contenido relevante."""
    out = list(ranges)
    while out and not lines[out[0][0] - 1].strip():
        s, e = out[0]
        out[0:1] = [(s + 1, e)] if s < e else []
    while out and not lines[out[-1][1] - 1].strip():
        s, e = out[-1]
        out[-1:] = [(s, e - 1)] if s < e else []
    return out


def snippet_text(lines: List[str], ranges: List[Range]) -> str:
    return "\n".join("\n".join(lines[s - 1:e]) for s, e in ranges)


def snippet_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_source(path) -> List[str]:
    with open(path, encoding="utf-8-sig") as fh:
        return [line.expandtabs(TAB_WIDTH).rstrip() for line in fh.read().splitlines()]


def build_rows(lines: List[str], ranges: List[Range], focus: Set[int], dedent: bool,
               label: str = "fragmento") -> Tuple[List[Row], int]:
    """Filas a dibujar y número de columnas de la línea más larga. Valida límites de tamaño."""
    problems: List[str] = []
    shown = {n for s, e in ranges for n in range(s, e + 1)}
    for n in sorted(focus - shown):
        problems.append(f"{label}: la línea enfocada {n} no está dentro de las líneas mostradas")
    if not ranges:
        problems.append(f"{label}: el rango no contiene líneas con texto")
    count = sum(e - s + 1 for s, e in ranges)
    if count > MAX_LINES:
        problems.append(f"{label}: {count} líneas (máximo {MAX_LINES}); divídelo en fragmentos más cortos")
    if problems:
        raise SnippetError(problems)

    indent = 0
    if dedent:
        body = [ln for s, e in ranges for ln in lines[s - 1:e] if ln.strip()]
        indent = min((len(ln) - len(ln.lstrip(" ")) for ln in body), default=0)
    rows: List[Row] = []
    for i, (s, e) in enumerate(ranges):
        if i:
            rows.append(Row("fold"))
        rows.extend(Row("code", n, lines[n - 1][indent:]) for n in range(s, e + 1))
    cols = max((len(r.text) for r in rows if r.kind == "code"), default=0)
    if cols > MAX_COLS:
        hint = "" if dedent else ", o usa dedent = true si el fragmento está muy indentado"
        raise SnippetError([f"{label}: línea de {cols} columnas (máximo {MAX_COLS}); acorta el fragmento{hint}"])
    return rows, cols
