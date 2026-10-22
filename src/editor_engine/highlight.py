# -*- coding: utf-8 -*-
"""Resaltado con Pygments sobre el archivo completo (las cadenas y comentarios multilínea quedan bien)
y reparto de los tokens por línea con una clase CSS propia, independiente de los estilos de Pygments."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from pygments import lex
from pygments.lexers import TextLexer, get_lexer_by_name, get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound

Tok = Tuple[str, str]          # (clase CSS, texto); "" = color de texto normal

# Lenguajes con tipos y métodos en Mayúscula Inicial / minúscula( : el lexer no distingue nombres.
_NAMED = {"csharp", "java", "python", "python3", "cpp", "c", "javascript", "typescript", "kotlin", "go", "rust",
          "swift", "php", "dart", "scala"}


# stripnl/stripall=False: Pygments por defecto quita las líneas en blanco iniciales y desplazaría
# todas las líneas respecto a la numeración real del archivo.
_OPTS = {"stripnl": False, "stripall": False, "ensurenl": True}


def get_lexer(path: Optional[str], language: Optional[str]):
    try:
        if language:
            return get_lexer_by_name(language, **_OPTS)
        if path:
            return get_lexer_for_filename(os.path.basename(path), **_OPTS)
    except ClassNotFound:
        pass
    return TextLexer(**_OPTS)


def language_key(lexer) -> str:
    return lexer.aliases[0] if getattr(lexer, "aliases", None) else "text"


def _css_class(ttype) -> str:
    if ttype in Token.Comment:
        return "pp" if ttype in Token.Comment.Preproc else "cm"
    if ttype in Token.Literal.String:
        return "st"
    if ttype in Token.Literal.Number:
        return "nu"
    if ttype in Token.Keyword.Type or ttype in Token.Name.Class or ttype in Token.Name.Exception:
        return "ty"
    if ttype in Token.Keyword or ttype in Token.Operator.Word:
        return "kw"
    if ttype in Token.Name.Function or ttype in Token.Name.Function.Magic:
        return "fn"
    if ttype in Token.Name.Decorator or ttype in Token.Name.Attribute:
        return "at"
    if ttype in Token.Name.Builtin.Pseudo:
        return ""
    if ttype in Token.Name.Builtin:
        return "bi"
    if ttype in Token.Operator:
        return "op"
    return ""


def _refine_names(tokens: List[Tok], plain: List[bool]) -> List[Tok]:
    """Nombres genéricos: ``Nombre(`` -> función; ``Mayúscula`` -> tipo (salvo tras ``.`` o CONSTANTES)."""
    out: List[Tok] = []
    for i, (cls, text) in enumerate(tokens):
        if plain[i] and text.isidentifier():
            nxt = next((t for _, t in tokens[i + 1:] if t.strip()), "")
            prev = next((t for _, t in reversed(tokens[:i]) if t.strip()), "")
            if prev == "new" and text[0].isupper():
                cls = "ty"
            elif nxt.startswith("("):
                cls = "fn"
            elif text[0].isupper() and prev != "." and not (len(text) > 1 and text.isupper()):
                cls = "ty"
        out.append((cls, text))
    return out


def highlight_lines(source: str, lexer) -> List[List[Tok]]:
    """Un listado de tokens por línea de ``source`` (sin salto de línea)."""
    raw = list(lex(source, lexer))
    flat: List[Tok] = []
    plain: List[bool] = []
    for ttype, text in raw:
        pieces = text.replace("\r\n", "\n").split("\n")
        for k, piece in enumerate(pieces):
            if k:
                flat.append(("", "\n"))
                plain.append(False)
            if piece:
                flat.append((_css_class(ttype), piece))
                plain.append(ttype in Token.Name and _css_class(ttype) == "")
    if language_key(lexer) in _NAMED:
        flat = _refine_names(flat, plain)
    lines: List[List[Tok]] = [[]]
    for cls, text in flat:
        if text == "\n":
            lines.append([])
        else:
            lines[-1].append((cls, text))
    return lines
