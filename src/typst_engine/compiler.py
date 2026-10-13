"""Envoltorio fino sobre el CLI de Typst.

Todas las llamadas usan una lista de argumentos (sin ``shell=True``). Los errores
de Typst se propagan como excepciones con el mensaje original del compilador.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Union

log = logging.getLogger(__name__)

PathLike = Union[str, "os.PathLike[str]"]

__all__ = [
    "TypstError",
    "TypstNotFoundError",
    "TypstCompileError",
    "CompileResult",
    "find_typst",
    "typst_version",
    "typst_fonts",
    "compile_typst",
    "compile_typst_detailed",
]


class TypstError(RuntimeError):
    """Error base del motor Typst."""


class TypstNotFoundError(TypstError):
    """El ejecutable ``typst`` no esta instalado o no es ejecutable."""


class TypstCompileError(TypstError):
    """``typst compile`` termino con error. ``stderr`` conserva el texto completo."""

    def __init__(self, message: str, stderr: str = "", returncode: int = 1):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


@dataclass
class CompileResult:
    pdf: Path
    stderr: str = ""

    @property
    def warnings(self) -> list[str]:
        """Bloques ``warning: ...`` emitidos por Typst durante una compilacion correcta."""
        return [b.strip() for b in re.split(r"\n(?=warning:)", self.stderr) if b.lstrip().startswith("warning:")]


def find_typst() -> str:
    """Ruta al ejecutable de Typst (variable ``TYPST_BIN`` o el PATH)."""
    override = os.environ.get("TYPST_BIN")
    candidate = override or shutil.which("typst")
    if not candidate or not (shutil.which(candidate) or Path(candidate).is_file()):
        raise TypstNotFoundError(
            "No se encontro el ejecutable 'typst'. Instalalo (https://github.com/typst/typst/releases) "
            "o define TYPST_BIN con su ruta."
        )
    return candidate


def _run(args: Sequence[str], cwd: Optional[PathLike] = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:  # el binario desaparecio entre find_typst() y la llamada
        raise TypstNotFoundError(f"No se pudo ejecutar typst: {exc}") from exc


def typst_version() -> str:
    """Linea de version, por ejemplo ``typst 0.15.0 (3ae52774)``."""
    proc = _run([find_typst(), "--version"])
    if proc.returncode != 0:
        raise TypstError(f"'typst --version' fallo: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _font_args(font_paths: Optional[Iterable[PathLike]]) -> list[str]:
    args: list[str] = []
    for fp in font_paths or ():
        args += ["--font-path", str(fp)]
    return args


def typst_fonts(font_paths: Optional[Iterable[PathLike]] = None) -> set[str]:
    """Familias de fuente visibles para Typst (sistema, embebidas y ``font_paths``).

    Typst emite un warning por cada familia desconocida de una lista de fuentes, aun
    si otra de la lista existe; el pipeline usa esto para filtrar candidatas.
    """
    proc = _run([find_typst(), "fonts", *_font_args(font_paths)])
    if proc.returncode != 0:
        return set()
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def compile_typst_detailed(
    main_file: PathLike,
    out_pdf: PathLike,
    root: Optional[PathLike] = None,
    inputs: Optional[Mapping[str, object]] = None,
    font_paths: Optional[Iterable[PathLike]] = None,
) -> CompileResult:
    """Como :func:`compile_typst`, pero devuelve tambien stderr/warnings."""
    typst = find_typst()
    main = Path(main_file).resolve()
    if not main.is_file():
        raise FileNotFoundError(f"No existe el archivo Typst de entrada: {main}")
    out = Path(out_pdf).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    args = [typst, "compile"]
    root_dir = Path(root).resolve() if root else main.parent
    args += ["--root", str(root_dir)]
    args += _font_args(font_paths)
    for key, value in (inputs or {}).items():
        args += ["--input", f"{key}={value}"]
    args += [str(main), str(out)]

    proc = _run(args)
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        detail = stderr or (proc.stdout or "").strip() or "sin salida"
        raise TypstCompileError(
            f"typst compile fallo (codigo {proc.returncode}) al compilar {main}:\n{detail}",
            stderr=stderr,
            returncode=proc.returncode,
        )
    result = CompileResult(pdf=out, stderr=stderr)
    for warning in result.warnings:
        log.warning("typst: %s", warning)
    return result


def compile_typst(
    main_file: PathLike,
    out_pdf: PathLike,
    root: Optional[PathLike] = None,
    inputs: Optional[Mapping[str, object]] = None,
    font_paths: Optional[Iterable[PathLike]] = None,
) -> Path:
    """Compila ``main_file`` a PDF y devuelve la ruta del PDF.

    - ``root``: carpeta raiz de Typst (``--root``); por defecto, la del archivo principal.
    - ``inputs``: pares clave/valor visibles como ``sys.inputs`` (``--input k=v``).
    - ``font_paths``: carpetas extra con fuentes (``--font-path``).

    Levanta :class:`TypstNotFoundError` si typst no esta instalado y
    :class:`TypstCompileError` (con el mensaje de Typst) si la compilacion falla. Los
    warnings de una compilacion correcta se registran con ``logging`` (nivel WARNING).
    """
    return compile_typst_detailed(main_file, out_pdf, root=root, inputs=inputs, font_paths=font_paths).pdf
