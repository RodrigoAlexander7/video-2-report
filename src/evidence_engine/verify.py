# -*- coding: utf-8 -*-
"""Verificación de evidencias y de afirmaciones del texto contra los logs.

Directiva en el texto (comentario Typst, Markdown o Python, invisible en el documento):

    // evidence: monedero-nominal expect: = 70
    <!-- evidence: monedero-nominal expect: = 70 -->

`verify_claims` comprueba que el literal aparece en el log del item indicado.
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List

from . import manifest as mf

_CLAIM = re.compile(r"(?://|#|<!--)\s*evidence:\s*(?P<id>[\w.\-]+)\s+expect:\s*(?P<lit>.+?)\s*(?:-->)?\s*$")


@dataclass
class Issue:
    level: str   # "error" | "warning"
    item: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.item}: {self.message}"


def verify_manifest(out_dir: str) -> List[Issue]:
    data = mf.load_manifest(out_dir)
    issues: List[Issue] = []
    items: Dict[str, Dict] = data.get("items", {})
    if not items:
        issues.append(Issue("warning", "-", "el manifiesto no tiene items"))
    for item_id, item in items.items():
        if item.get("source") not in mf.SOURCES:
            issues.append(Issue("error", item_id, f"source inválido: {item.get('source')!r}"))
        for key in ("log", "image"):
            if not item.get(key):
                if key == "image" or item.get("source") == "terminal":
                    issues.append(Issue("error", item_id, f"falta '{key}'"))
                continue
            path = os.path.join(out_dir, item[key])
            if not os.path.isfile(path):
                issues.append(Issue("error", item_id, f"no existe {key}: {item[key]}"))
            elif mf.sha256_file(path) != item.get(f"{key}_sha256"):
                issues.append(Issue("error", item_id, f"el {key} fue modificado después de capturarse ({item[key]})"))
        if item.get("source") == "code":
            issues.extend(_verify_code(out_dir, item_id, item))
        if item.get("source") == "annotated":
            base = item.get("base")
            if base not in items:
                issues.append(Issue("error", item_id, f"imagen anotada sin base registrada: {base!r}"))
        if item.get("source") == "terminal" and any(c not in (0, None) for c in item.get("returncodes", [])):
            issues.append(Issue("warning", item_id, f"algún comando terminó con código distinto de 0: {item['returncodes']}"))
    return issues


def _verify_code(out_dir: str, item_id: str, item: Dict) -> List[Issue]:
    """Imagen de un fragmento de código: el fuente debe seguir diciendo lo mismo que cuando se generó."""
    if item.get("origin") == "inline":
        return []            # el texto es el propio contenido del reporte: no hay archivo fuente con el que compararlo
    from ..editor_engine.extract import read_source, snippet_sha256, snippet_text
    src = os.path.normpath(os.path.join(out_dir, item.get("file", "")))
    if not item.get("file") or not os.path.isfile(src):
        return [Issue("error", item_id, f"no existe el archivo fuente: {item.get('file')}")]
    lines = read_source(src)
    ranges = [tuple(r) for r in item.get("ranges", [])]
    if any(e > len(lines) for _, e in ranges):
        return [Issue("error", item_id, "el archivo fuente es más corto que el rango mostrado: regenera la imagen")]
    if snippet_sha256(snippet_text(lines, ranges)) != item.get("snippet_sha256"):
        return [Issue("error", item_id, f"el fuente cambió después de generar la imagen ({item['file']}, líneas {ranges}): regénerala")]
    return []


def _transcript(out_dir: str, item: Dict) -> str:
    if not item.get("log"):
        return ""
    with open(os.path.join(out_dir, item["log"]), encoding="utf-8") as f:
        return f.read()


def verify_claims(out_dir: str, text_files: Iterable[str]) -> List[Issue]:
    items = mf.load_manifest(out_dir).get("items", {})
    issues: List[Issue] = []
    for path in text_files:
        with open(path, encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                m = _CLAIM.search(line)
                if not m:
                    continue
                where = f"{os.path.basename(path)}:{lineno}"
                item = items.get(m["id"])
                if item is None:
                    issues.append(Issue("error", m["id"], f"{where}: evidencia no registrada en el manifiesto"))
                elif m["lit"] not in _transcript(out_dir, item):
                    issues.append(Issue("error", m["id"], f"{where}: '{m['lit']}' no aparece en el log real"))
    return issues
