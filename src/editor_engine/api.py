# -*- coding: utf-8 -*-
"""Orquestación: Snippet -> filas -> HTML -> PNG -> manifiesto de evidencia."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from ..evidence_engine import manifest as mf
from .extract import (SnippetError, build_rows, parse_ranges, read_source, snippet_sha256, snippet_text,
                      trim_blank_edges)
from .highlight import get_lexer, highlight_lines, language_key
from .render import Frame, MIN_PT, capture, compose_html, legibility_pt, size_of
from .spec import Snippet, load_snippets


def _frame_and_meta(snip: Snippet) -> tuple[Frame, Dict[str, Any]]:
    label = f"snippet '{snip.id}'"
    if snip.file is not None:
        lines = read_source(snip.file)
        ranges = trim_blank_edges(lines, parse_ranges(snip.lines, len(lines)))
        source = "\n".join(lines)
        origin, shown = "file", snippet_text(lines, ranges)
    else:
        body = [ln.rstrip() for ln in snip.text.splitlines()]
        lines = [""] * (snip.start - 1) + body          # los números de línea mostrados empiezan en `start`
        ranges = trim_blank_edges(lines, [(snip.start, snip.start + len(body) - 1)])
        source = "\n".join(lines)
        origin, shown = "inline", snippet_text(lines, ranges)
    rows, cols = build_rows(lines, ranges, set(snip.focus), snip.dedent, label)

    lexer = get_lexer(snip.raw_file or snip.title or snip.path, snip.language)
    tokens = highlight_lines(source, lexer)
    by_no = {r.no: tokens[r.no - 1] if r.no - 1 < len(tokens) else [] for r in rows if r.kind == "code"}
    indent = 0
    if snip.dedent:
        body = [ln for s, e in ranges for ln in lines[s - 1:e] if ln.strip()]
        indent = min((len(ln) - len(ln.lstrip(" ")) for ln in body), default=0)
    name = os.path.basename(snip.raw_file or snip.title or snip.path or "snippet")
    frame = Frame(rows=rows, lines_tokens=by_no, cols=cols, focus=set(snip.focus), theme=snip.theme,
                  path=snip.path or snip.raw_file or snip.title or name, title=snip.title or name,
                  lang=language_key(lexer), chrome=snip.chrome, whitespace=snip.whitespace, dedent_by=indent)
    width, height = size_of(rows, cols, snip.chrome, frame.show_crumbs)
    pt = legibility_pt(width)
    if pt < MIN_PT:
        raise SnippetError([f"{label}: el texto quedaría de {pt:.1f} pt a 6 in de ancho (mínimo {MIN_PT} pt); "
                            "acorta las líneas, usa dedent = true o divide el fragmento"])
    meta = {"origin": origin, "language": language_key(lexer), "theme": snip.theme, "render": "editor-frame",
            "ranges": [list(r) for r in ranges], "focus": sorted(snip.focus), "snippet_sha256": snippet_sha256(shown),
            "width_px": width, "height_px": height, "scale": 2, "text_pt_at_6in": round(pt, 1)}
    return frame, meta


def render_snippet(snip: Snippet, out_dir, manifest_dir=None) -> Dict[str, Any]:
    """Genera ``<out_dir>/<id>.png`` y lo registra en el manifiesto de ``manifest_dir`` (por defecto, el padre de out_dir)."""
    out_dir = Path(out_dir)
    manifest_dir = Path(manifest_dir) if manifest_dir else out_dir.parent
    frame, meta = _frame_and_meta(snip)
    html, width, height = compose_html(frame)
    png = capture(html, width, height, out_dir / f"{snip.id}.png")
    item = {"source": "code", "captured_at": mf.now_iso(), "image": mf.rel(str(manifest_dir), str(png)),
            "image_sha256": mf.sha256_file(str(png)), "note": snip.note, **meta}
    if snip.file is not None:
        item["file"] = mf.rel(str(manifest_dir), str(snip.file))
        item["file_sha256"] = mf.sha256_file(str(snip.file))
    return mf.upsert(str(manifest_dir), snip.id, item)


def build_snippets(spec_path, out_dir=None) -> List[Dict[str, Any]]:
    """Valida TODO el ``snippets.toml`` (sin Chrome) y luego genera todas las imágenes."""
    spec_path = Path(spec_path)
    snippets = load_snippets(spec_path)
    problems: List[str] = []
    for s in snippets:
        try:
            _frame_and_meta(s)
        except SnippetError as exc:
            problems.extend(exc.problems)
    if problems:
        raise SnippetError(problems)
    if out_dir is None:
        from ..core.registry import REPO_ROOT, resolve_slug
        out_dir = REPO_ROOT / "output" / resolve_slug(spec_path.resolve().parent) / "evidence"
    out_dir = Path(out_dir)
    return [render_snippet(s, out_dir / "code", out_dir) for s in snippets]
