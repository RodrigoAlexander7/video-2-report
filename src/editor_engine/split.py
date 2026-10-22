# -*- coding: utf-8 -*-
"""Divide un fragmento largo en varias imágenes de a lo sumo ``cap`` líneas, cortando donde el código lo permite.

Los cortes caen en una línea en blanco o justo después de una llave de cierre sola en su línea (fin de método o bloque);
si en la mitad final de la ventana no hay ninguno, se corta en ``cap``. Cada trozo conserva la numeración real del
archivo, así que las imágenes se leen una tras otra sin saltos.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

Range = Tuple[int, int]


def _is_break(lines: Sequence[str], n: int) -> bool:
    """¿Se puede terminar un trozo en la línea ``n`` (1-indexada)?"""
    text = lines[n - 1].strip()
    if text in ("}", "};", "})", "});", ")"):
        return True
    nxt = lines[n].strip() if n < len(lines) else ""
    return text == "" or nxt == ""


def split_range(lines: Sequence[str], start: int, end: int, cap: int) -> List[Range]:
    """Parte ``[start, end]`` en tramos de a lo sumo ``cap`` líneas."""
    if cap < 4:
        raise ValueError("cap debe ser al menos 4 líneas")
    parts: List[Range] = []
    pos = start
    while end - pos + 1 > cap:
        remaining = end - pos + 1
        target = pos + -(-remaining // -(-remaining // cap)) - 1        # tamaños parejos: ceil(restante / nº de trozos)
        limit = min(pos + cap - 1, end - 1)
        options = [n for n in range(pos + cap // 2, limit + 1) if _is_break(lines, n)]
        cut = min(options, key=lambda n: abs(n - target)) if options else min(target, limit)
        parts.append((pos, cut))
        pos = cut + 1
        while pos <= end and not lines[pos - 1].strip():      # sin líneas en blanco al inicio del trozo siguiente
            pos += 1
    if pos <= end:
        parts.append((pos, end))
    return parts


def split_ranges(lines: Sequence[str], ranges: Sequence[Range], cap: int) -> List[List[Range]]:
    """Agrupa ``ranges`` en imágenes: si todo cabe en ``cap`` líneas, una sola imagen (con ⋯ entre tramos);
    si no, cada tramo se divide por separado y cada trozo es una imagen."""
    total = sum(e - s + 1 for s, e in ranges)
    if total <= cap:
        return [list(ranges)]
    return [[part] for s, e in ranges for part in split_range(lines, s, e, cap)]
