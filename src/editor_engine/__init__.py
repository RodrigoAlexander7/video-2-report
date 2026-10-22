# -*- coding: utf-8 -*-
"""Imágenes de fragmentos de código con aspecto de editor (tema oscuro por defecto) para reportes y diapositivas.

Genérico: no sabe nada de laboratorios. Un ``snippets.toml`` declara los fragmentos; cada imagen se registra en
``manifest.json`` de evidencia (``source = "code"``) con el hash del fragmento para detectar cambios en el fuente.
"""
from .api import build_snippets, render_snippet
from .extract import SnippetError
from .render import BrowserError, legibility_pt
from .spec import Snippet, load_snippets

__all__ = ["build_snippets", "render_snippet", "load_snippets", "Snippet", "SnippetError", "BrowserError", "legibility_pt"]
