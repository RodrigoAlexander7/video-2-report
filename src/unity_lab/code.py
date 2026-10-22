# -*- coding: utf-8 -*-
"""Bloques de código del reporte: archivo + líneas -> una o varias imágenes de editor (editor_engine), con caché."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..editor_engine.api import _frame_and_meta, render_snippet
from ..editor_engine.extract import SnippetError, parse_ranges, read_source
from ..editor_engine.spec import Snippet
from ..editor_engine.split import split_ranges
from ..evidence_engine import manifest as mf
from .model import CodeSpec


def _lines_arg(ranges) -> Any:
    parts = [f"{s}-{e}" if s != e else str(s) for s, e in ranges]
    return parts[0] if len(parts) == 1 else parts


def plan_code(spec: CodeSpec, project_dir: Path, theme: str = "dark") -> List[Snippet]:
    """Snippets (una imagen cada uno) de un bloque de código; se divide en tramos de ``spec.max_lines`` líneas."""
    path = (Path(project_dir) / spec.file).resolve()
    lines = read_source(path)
    ranges = parse_ranges(spec.lines, len(lines))
    groups = split_ranges(lines, ranges, spec.max_lines)
    shown = Path(spec.path).as_posix() if spec.path else path.name
    out: List[Snippet] = []
    for k, group in enumerate(groups, 1):
        nums = {n for s, e in group for n in range(s, e + 1)}
        out.append(Snippet(id=spec.id if len(groups) == 1 else f"{spec.id}-{k}", file=path, raw_file=spec.file,
                           lines=_lines_arg(group), focus=sorted(n for n in spec.focus if n in nums), path=shown,
                           theme=theme, dedent=spec.dedent, caption=spec.caption))
    stray = sorted(set(spec.focus) - {n for s, e in ranges for n in range(s, e + 1)})
    if stray:
        raise SnippetError([f"{spec.id}: las líneas enfocadas {stray} no están dentro de 'lines'"])
    return out


def validate(snips: List[Snippet]) -> List[Dict[str, Any]]:
    """Comprueba cada imagen sin Chrome (límites de líneas, columnas y legibilidad); devuelve sus metadatos."""
    return [_frame_and_meta(s)[1] for s in snips]


def ensure_image(snip: Snippet, evidence_dir: Path) -> Dict[str, Any]:
    """Imagen de ``snip`` en ``<evidencia>/code/<id>.png``; se reutiliza si el fragmento no cambió."""
    evidence_dir = Path(evidence_dir)
    meta = _frame_and_meta(snip)[1]
    item: Optional[Dict[str, Any]] = mf.load_manifest(str(evidence_dir)).get("items", {}).get(snip.id)
    if item and item.get("source") == "code" and (evidence_dir / item["image"]).is_file():
        same = (item.get("snippet_sha256") == meta["snippet_sha256"] and item.get("theme") == snip.theme
                and item.get("focus") == meta["focus"] and item.get("ranges") == meta["ranges"]
                and mf.sha256_file(str(evidence_dir / item["image"])) == item.get("image_sha256"))
        if same:
            return item
    return render_snippet(snip, evidence_dir / "code", evidence_dir)
