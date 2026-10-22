"""Motor Typst: compilador (``compiler``) y plantillas (``templates/``)."""

from pathlib import Path

from .compiler import (
    CompileResult,
    TypstCompileError,
    TypstError,
    TypstNotFoundError,
    compile_typst,
    compile_typst_detailed,
    find_typst,
    typst_fonts,
    typst_version,
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

__all__ = [
    "TEMPLATES_DIR",
    "CompileResult",
    "TypstCompileError",
    "TypstError",
    "TypstNotFoundError",
    "compile_typst",
    "compile_typst_detailed",
    "find_typst",
    "typst_fonts",
    "typst_version",
]
