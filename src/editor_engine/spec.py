# -*- coding: utf-8 -*-
"""``snippets.toml``: una tabla ``[[snippet]]`` por imagen. Valida todo y reporta todos los problemas juntos.

    [defaults]                 # opcional; cualquier clave de [[snippet]] salvo id/file/text
    theme = "dark"

    [[snippet]]
    id    = "audio-start"      # identificador en el manifiesto (letras, números, . _ -)
    file  = "source-code.cs"   # relativo a la carpeta del snippets.toml
    lines = "12-30"            # "12-30", 12, ["12-18", "24-30"] (⋯ entre tramos) o se omite (archivo entero)
    focus = [20, 21]           # líneas resaltadas (opcional)
    # path, title, language, theme ("dark"|"light"), dedent, whitespace, chrome, note
    # text = "..."             # fragmento ILUSTRATIVO en lugar de file (queda marcado como no verificable)
    # start = 122              # solo con text: numero de la primera linea mostrada (con file se usan los reales)
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .extract import SnippetError
from .render import THEMES

ALLOWED = {"id", "file", "lines", "focus", "path", "title", "language", "theme", "dedent", "whitespace", "chrome",
           "note", "text", "caption", "start"}
DEFAULTABLE = ALLOWED - {"id", "file", "text", "caption", "note", "lines", "focus", "start"}
_ID = re.compile(r"^[\w.\-]+$")


@dataclass
class Snippet:
    id: str
    file: Optional[Path] = None           # resuelto; None si es ilustrativo (text)
    text: Optional[str] = None
    lines: Any = None
    focus: List[int] = field(default_factory=list)
    path: Optional[str] = None
    title: Optional[str] = None
    language: Optional[str] = None
    theme: str = "dark"
    dedent: bool = False
    whitespace: bool = True
    chrome: bool = True
    note: str = ""
    caption: str = ""
    start: int = 1
    raw_file: Optional[str] = None        # el valor tal cual está en el TOML (para el breadcrumb)


def _check(entry: Dict[str, Any], where: str, problems: List[str]) -> None:
    for key in entry:
        if key not in ALLOWED:
            hint = next((k for k in sorted(ALLOWED) if k.startswith(key[:3])), None)
            problems.append(f"{where}: clave desconocida '{key}'" + (f" (¿'{hint}'?)" if hint else ""))
    types = {"theme": str, "path": str, "title": str, "language": str, "note": str, "caption": str, "text": str,
             "file": str, "dedent": bool, "whitespace": bool, "chrome": bool}
    for key, typ in types.items():
        if key in entry and not isinstance(entry[key], typ):
            problems.append(f"{where}: '{key}' debe ser {'texto' if typ is str else 'true/false'}")
    if "start" in entry and not (isinstance(entry["start"], int) and not isinstance(entry["start"], bool) and entry["start"] >= 1):
        problems.append(f"{where}: 'start' debe ser un número de línea >= 1")
    if "focus" in entry and not (isinstance(entry["focus"], list) and all(isinstance(n, int) for n in entry["focus"])):
        problems.append(f"{where}: 'focus' debe ser una lista de números de línea, p. ej. [20, 21]")
    if entry.get("theme") not in (None, *THEMES):
        problems.append(f"{where}: tema '{entry.get('theme')}' desconocido (usa {', '.join(THEMES)})")


def load_snippets(spec_path) -> List[Snippet]:
    spec_path = Path(spec_path).resolve()
    if not spec_path.is_file():
        raise FileNotFoundError(f"No existe {spec_path}")
    try:
        data = tomllib.loads(spec_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SnippetError([f"{spec_path.name}: TOML inválido: {exc}"]) from exc
    entries = data.get("snippet") or []
    problems: List[str] = []
    if not entries:
        raise SnippetError([f"{spec_path.name}: no hay ninguna tabla [[snippet]]"])
    defaults = data.get("defaults") or {}
    for key in defaults:
        if key not in DEFAULTABLE:
            problems.append(f"[defaults]: '{key}' no admite valor por defecto (usa {', '.join(sorted(DEFAULTABLE))})")
    _check({k: v for k, v in defaults.items() if k in DEFAULTABLE}, "[defaults]", problems)

    out: List[Snippet] = []
    seen = set()
    for i, raw in enumerate(entries, 1):
        entry = {**{k: v for k, v in defaults.items() if k in DEFAULTABLE}, **raw}
        sid = entry.get("id")
        where = f"snippet {i}" + (f" ({sid})" if isinstance(sid, str) else "")
        _check(entry, where, problems)
        if not isinstance(sid, str) or not _ID.match(sid):
            problems.append(f"{where}: falta 'id' (letras, números, . _ -)")
            continue
        if sid in seen:
            problems.append(f"{where}: id duplicado")
        seen.add(sid)
        has_file, has_text = "file" in entry, "text" in entry
        if has_file == has_text:
            problems.append(f"{where}: indica 'file' (fragmento real) o 'text' (ilustrativo), no ambos ni ninguno")
            continue
        snip = Snippet(id=sid, lines=entry.get("lines"), focus=list(entry.get("focus", [])), path=entry.get("path"),
                       title=entry.get("title"), language=entry.get("language"), theme=entry.get("theme", "dark"),
                       dedent=bool(entry.get("dedent", False)), whitespace=bool(entry.get("whitespace", True)),
                       chrome=bool(entry.get("chrome", True)), note=entry.get("note", ""), caption=entry.get("caption", ""),
                       start=entry.get("start", 1))
        if has_file and "start" in entry:
            problems.append(f"{where}: 'start' solo aplica a 'text'; con 'file' se muestran los números reales del archivo")
        if has_file:
            snip.raw_file = entry["file"]
            snip.file = (spec_path.parent / entry["file"]).resolve()
            if not snip.file.is_file():
                problems.append(f"{where}: no existe el archivo {snip.file}")
        else:
            snip.text = entry["text"].strip("\n")
            if "lines" in entry:
                problems.append(f"{where}: 'lines' no aplica a un fragmento ilustrativo (text)")
            if not snip.title and not snip.path:
                problems.append(f"{where}: un fragmento ilustrativo necesita 'title' o 'path' (nombre del archivo que se muestra)")
        out.append(snip)
    if problems:
        raise SnippetError(problems)
    return out
