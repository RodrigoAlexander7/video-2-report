# -*- coding: utf-8 -*-
"""Vista previa de un .docx: DOCX -> PDF -> PNG por página y hoja de contactos, sin instalar nada en el sistema.

Convierte con lo que haya: LibreOffice (`soffice`) o el conversor `x2t` de ONLYOFFICE Desktop Editors (nativo o flatpak),
el mismo motor con el que se edita el reporte. Las páginas se rasterizan con `pdftoppm` (poppler) y la hoja de contactos
se arma con Pillow. También mide cuánto de cada página está ocupado para detectar páginas casi vacías.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

FLATPAK_ID = "org.onlyoffice.desktopeditors"
X2T_FLATPAK = "/app/bin/opt/onlyoffice/desktopeditors/converter/x2t"
X2T_NATIVE = ("/opt/onlyoffice/desktopeditors/converter/x2t", "/usr/lib/onlyoffice/desktopeditors/converter/x2t")
TIMEOUT_S = 300
PDF_FORMAT = 513


class RenderError(RuntimeError):
    """No hay conversor disponible o la conversión falló."""


def _run(cmd: List[str], timeout: int = TIMEOUT_S) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"`{cmd[0]}` superó {timeout}s") from exc


def _flatpak_installed() -> bool:
    return bool(shutil.which("flatpak")) and _run(["flatpak", "info", FLATPAK_ID], 30).returncode == 0


def _fonts_index(flatpak: bool) -> Optional[Path]:
    home = Path.home()
    candidates = [home / ".var/app" / FLATPAK_ID / "data/onlyoffice/desktopeditors/data/fonts/AllFonts.js"] if flatpak else []
    candidates.append(home / ".local/share/onlyoffice/desktopeditors/data/fonts/AllFonts.js")
    return next((c for c in candidates if c.is_file()), None)


def converter() -> str:
    """Nombre del conversor que se usará: 'soffice', 'x2t' o 'x2t-flatpak'."""
    if shutil.which("soffice") or shutil.which("libreoffice"):
        return "soffice"
    if any(Path(p).is_file() for p in X2T_NATIVE):
        return "x2t"
    if _flatpak_installed():
        return "x2t-flatpak"
    raise RenderError("No hay conversor de .docx: instala LibreOffice (sudo apt install libreoffice-writer) "
                      "u ONLYOFFICE Desktop Editors (flatpak install --user flathub org.onlyoffice.desktopeditors).")


def docx_to_pdf(docx_path, pdf_path) -> Path:
    docx_path, pdf_path = Path(docx_path).resolve(), Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    kind = converter()
    with tempfile.TemporaryDirectory(prefix="docx-render-") as tmp:
        tmp = Path(tmp)
        if kind == "soffice":
            exe = shutil.which("soffice") or shutil.which("libreoffice")
            proc = _run([exe, "--headless", f"-env:UserInstallation=file://{tmp / 'profile'}", "--convert-to", "pdf",
                         "--outdir", str(tmp), str(docx_path)])
            produced = tmp / (docx_path.stem + ".pdf")
            if proc.returncode != 0 or not produced.is_file():
                raise RenderError(f"LibreOffice no produjo el PDF: {proc.stderr.strip()[-300:]}")
            shutil.copy(produced, pdf_path)
            return pdf_path
        flatpak = kind == "x2t-flatpak"
        fonts = _fonts_index(flatpak)
        if fonts is None:
            raise RenderError("ONLYOFFICE no ha generado su índice de fuentes (AllFonts.js): ábrelo una vez y vuelve a intentarlo.")
        src = tmp / "in.docx"
        shutil.copy(docx_path, src)
        out = tmp / "out.pdf"
        params = tmp / "params.xml"
        params.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n<TaskQueueDataConvert xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'
            f"<m_sFileFrom>{src}</m_sFileFrom>\n<m_sFileTo>{out}</m_sFileTo>\n<m_nFormatTo>{PDF_FORMAT}</m_nFormatTo>\n"
            f"<m_bIsNoBase64>true</m_bIsNoBase64>\n<m_sAllFontsPath>{fonts}</m_sAllFontsPath>\n"
            f"<m_sFontDir>{'/run/host/fonts' if flatpak else '/usr/share/fonts'}</m_sFontDir>\n<m_sTempDir>{tmp}</m_sTempDir>\n"
            "</TaskQueueDataConvert>\n", encoding="utf-8")
        if flatpak:
            cmd = ["flatpak", "run", f"--filesystem={tmp}", f"--command={X2T_FLATPAK}", FLATPAK_ID, str(params)]
        else:
            cmd = [next(p for p in X2T_NATIVE if Path(p).is_file()), str(params)]
        proc = _run(cmd)
        if not out.is_file():
            raise RenderError(f"x2t no produjo el PDF: {(proc.stdout + proc.stderr).strip()[-400:]}")
        shutil.copy(out, pdf_path)
    return pdf_path


def pdf_to_pages(pdf_path, out_dir, dpi: int = 70) -> List[Path]:
    if not shutil.which("pdftoppm"):
        raise RenderError("Falta `pdftoppm` (sudo apt install poppler-utils)")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page-*.png"):
        old.unlink()
    proc = _run(["pdftoppm", "-r", str(dpi), "-png", str(pdf_path), str(out_dir / "page")])
    if proc.returncode != 0:
        raise RenderError(f"pdftoppm falló: {proc.stderr.strip()[-300:]}")
    return sorted(out_dir.glob("page-*.png"))


def page_fill(png: Path, header: float = 0.17, footer: float = 0.04) -> float:
    """Fracción de filas con contenido en la zona útil de la página (sin el encabezado institucional ni el pie)."""
    with Image.open(png) as im:
        g = np.asarray(im.convert("L"), dtype=np.uint8)
    h = g.shape[0]
    body = g[int(h * header):int(h * (1 - footer))]
    if body.size == 0:
        return 0.0
    # una fila cuenta si tiene tinta; el borde de la tabla institucional (columna fina) se descarta
    inked = (body[:, int(g.shape[1] * 0.08):int(g.shape[1] * 0.92)] < 200).sum(axis=1) > 3
    return float(inked.mean())


@dataclass
class Review:
    pdf: Path
    pages: List[Path]
    sheets: List[Path]
    sparse: List[int]                          # números de página (1-indexados) casi vacías


def review_docx(docx_path, out_dir, dpi: int = 70, per_sheet: int = 8, sparse_below: float = 0.2) -> Review:
    from ..video_engine.frames import contact_sheet, load_rgb
    out_dir = Path(out_dir)
    pdf = docx_to_pdf(docx_path, out_dir / (Path(docx_path).stem + ".pdf"))
    pages = pdf_to_pages(pdf, out_dir, dpi)
    fills = [page_fill(p) for p in pages]
    sparse = [n for n, f in enumerate(fills, 1) if f < sparse_below and n != len(pages)]
    sheets: List[Path] = []
    for k in range(0, len(pages), per_sheet):
        chunk = pages[k:k + per_sheet]
        items: List[Tuple[str, Image.Image]] = [(f"página {k + i + 1}" + ("  (casi vacía)" if k + i + 1 in sparse else ""), load_rgb(p))
                                                for i, p in enumerate(chunk)]
        sheets.append(contact_sheet(items, out_dir / f"hoja-{k // per_sheet + 1}.png", cols=4, thumb_w=360))
    return Review(pdf=pdf, pages=pages, sheets=sheets, sparse=sparse)
