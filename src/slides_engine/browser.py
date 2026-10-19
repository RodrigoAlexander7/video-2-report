# -*- coding: utf-8 -*-
"""Chrome/Chromium headless: PDF vectorial (una página por diapositiva) y chequeo de desbordes.

Todas las llamadas usan lista de argumentos (sin shell). El navegador se busca en PATH o en ``CHROME_BIN``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from html import unescape
from pathlib import Path
from typing import Any, Dict, List

CANDIDATES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
MIN_FONT_PX = 24          # tamaño mínimo de texto a 1920x1080
TIMEOUT_S = 120

CHECK_SCRIPT = """
(() => {
  const out = [];
  document.querySelectorAll('.slide').forEach((slide, i) => {
    const issues = [];
    const inner = slide.querySelector('.slide-inner');
    const body = slide.querySelector('.slide-body');
    if (body && (body.scrollHeight > body.clientHeight + 1 || body.scrollWidth > body.clientWidth + 1)) issues.push('overflow-body');
    if (inner.scrollHeight > inner.clientHeight + 1 || inner.scrollWidth > inner.clientWidth + 1) issues.push('overflow-slide');
    let minFont = 1e9;
    slide.querySelectorAll('*').forEach(el => {
      if (el.getClientRects().length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
        const f = parseFloat(getComputedStyle(el).fontSize);
        if (f < minFont) minFont = f;
      }
    });
    slide.querySelectorAll('img').forEach(im => { if (!im.complete || im.naturalWidth === 0) issues.push('image-not-loaded'); });
    out.push({index: i + 1, issues, minFont: minFont === 1e9 ? null : Math.round(minFont * 10) / 10});
  });
  const pre = document.createElement('pre');
  pre.id = '__slides_check';
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
})();
"""


class BrowserError(RuntimeError):
    """Chrome no está disponible o terminó con error."""


def find_chrome() -> str:
    env = os.environ.get("CHROME_BIN")
    if env:
        if not (Path(env).is_file() and os.access(env, os.X_OK)):
            raise BrowserError(f"CHROME_BIN apunta a un ejecutable inexistente: {env}")
        return env
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    raise BrowserError("No se encontró Chrome/Chromium (probé: " + ", ".join(CANDIDATES) + "). "
                       "Instálalo o define CHROME_BIN=/ruta/al/ejecutable.")


def _run(args: List[str], profile: Path) -> subprocess.CompletedProcess:
    cmd = [find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--disable-extensions", "--force-device-scale-factor=1", f"--user-data-dir={profile}", *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise BrowserError(f"Chrome superó {TIMEOUT_S}s sin terminar") from exc
    if proc.returncode != 0:
        raise BrowserError(f"Chrome terminó con código {proc.returncode}:\n{proc.stderr.strip()[-800:]}")
    return proc


def count_pdf_pages(pdf: Path) -> int:
    data = pdf.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page(?![\w])", data))
    if pages:
        return pages
    counts = [int(c) for c in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data)]
    return max(counts, default=0)


def export_pdf(html_path: Path, pdf_path: Path, expected_pages: int) -> Path:
    """PDF vectorial: ``@page`` define 1920x1080 y cada diapositiva es una página."""
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="slides-chrome-") as profile:
        _run(["--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()], Path(profile))
    if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF"):
        raise BrowserError(f"Chrome no produjo un PDF válido en {pdf_path}")
    pages = count_pdf_pages(pdf_path)
    if pages != expected_pages:
        raise BrowserError(f"El PDF tiene {pages} páginas y el deck {expected_pages} diapositivas: "
                           "alguna diapositiva se desbordó o quedó vacía.")
    return pdf_path


def check_layout(html: str) -> List[Dict[str, Any]]:
    """Mide cada diapositiva en un Chrome real a 1920x1080 (script solo en una copia temporal, no en el entregable)."""
    probe = html.replace(
        "</body>", f"<style>.slide{{width:1920px!important}}</style><script>{CHECK_SCRIPT}</script></body>", 1)
    with tempfile.TemporaryDirectory(prefix="slides-check-") as tmp:
        page = Path(tmp) / "probe.html"
        page.write_text(probe, encoding="utf-8")
        proc = _run(["--window-size=1920,1080", "--virtual-time-budget=4000", "--dump-dom", page.as_uri()],
                    Path(tmp) / "profile")
    m = re.search(r'<pre id="__slides_check">(.*?)</pre>', proc.stdout, re.S)
    if not m:
        raise BrowserError("El chequeo de diseño no devolvió resultados (¿falló el script en Chrome?).")
    return json.loads(unescape(m.group(1)))


def layout_problems(results: List[Dict[str, Any]]) -> List[str]:
    problems: List[str] = []
    texts = {"overflow-body": "el contenido no cabe en el área de la diapositiva (recorta texto o divide la diapositiva)",
             "overflow-slide": "la diapositiva se desborda (título muy largo o contenido excesivo)",
             "image-not-loaded": "una imagen no se cargó"}
    for r in results:
        for issue in dict.fromkeys(r["issues"]):
            problems.append(f"diapositiva {r['index']}: {texts.get(issue, issue)}")
        if r["minFont"] is not None and r["minFont"] < MIN_FONT_PX - 0.5:
            problems.append(f"diapositiva {r['index']}: texto de {r['minFont']}px (mínimo {MIN_FONT_PX}px a 1920x1080)")
    return problems
