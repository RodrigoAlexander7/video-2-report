# -*- coding: utf-8 -*-
"""Revisión del reporte sin tocar el video: tono, ortografía, citas, referencias a figuras, código y balance visual."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..editor_engine.extract import SnippetError
from . import code as codemod
from .figures import FigureResult
from .layout import fit_capture, fit_code
from .model import Lab, words
from .style import Issue, Speller, check_citations, identifiers_from_code, lint_text

MAX_WORDS_PER_FIGURE = 60       # el reporte de nota 18 tenía ~40; más de esto deja de ser visual
FIG_REF = re.compile(r"\{fig:([\w\-]+)\}")


@dataclass
class Report:
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, object] = field(default_factory=dict)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.level == "warning"]


def _texts(lab: Lab) -> Dict[str, str]:
    """Todos los textos revisables con su ubicación, en orden del documento."""
    out: Dict[str, str] = {}
    for b in lab.blocks:
        where = f"bloque {b.index} ({b.kind})"
        if b.text:
            out[where] = b.text
        if b.figure and b.figure.caption:
            out[f"{where} pie de {b.figure.id}"] = b.figure.caption
        if b.code and b.code.caption:
            out[f"{where} pie de {b.code.id}"] = b.code.caption
    for i, q in enumerate(lab.questions, 1):
        out[f"pregunta {i}"] = q["q"]
        out[f"respuesta {i}"] = q["a"]
    for i, c in enumerate(lab.conclusions, 1):
        out[f"conclusión {i}"] = c
    return out


def figure_ids(lab: Lab) -> Dict[str, str]:
    """id -> 'frame' | 'code' para las referencias {fig:id} (los bloques de código dividen en id-1, id-2…, que apunta a la primera)."""
    ids: Dict[str, str] = {}
    for b in lab.blocks:
        if b.figure:
            ids[b.figure.id] = "figure"
        if b.code:
            ids[b.code.id] = "code"
    return ids


def check_lab(lab: Lab, results: Optional[Dict[str, FigureResult]] = None, spell: bool = True) -> Report:
    rep = Report()
    meta = lab.meta
    allow = list(meta.get("style_allow", []))
    texts = _texts(lab)

    # --- tono y frases ---
    for where, text in texts.items():
        sentence = not (where.endswith("(heading)") or " pie de " in where or where.startswith("pregunta "))
        rep.issues += lint_text(text, where, allow, sentence=sentence)

    # --- ortografía ---
    if spell:
        code_files = [lab.project_dir / b.code.file for b in lab.blocks if b.code]
        glossary = set(identifiers_from_code(code_files)) | set(meta.get("spell_ignore", []))
        # El texto de la interfaz (lo que debe verse en las capturas) y los datos de la carátula no son errores de ortografía
        ui_texts = [t for fs in lab.figures for f in [fs, *fs.frames]
                    for t in (*f.expect, *(x for x in (f.annotate.target if f.annotate else None,
                                                       f.crop.desde if f.crop else None, f.crop.hasta if f.crop else None,
                                                       f.crop.around if f.crop else None) if x))]
        cover = [str(meta.get(k, "")) for k in ("title", "course", "instructor")] + list(meta.get("members", []))
        glossary |= {w for t in ui_texts + cover for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", t)}
        gfile = lab.project_dir / meta.get("glossary", "content/glossary.txt")
        if gfile.is_file():
            glossary |= {w.strip() for w in gfile.read_text(encoding="utf-8").split() if w.strip()}
        speller = Speller(glossary)
        if speller.error:
            rep.issues.append(Issue("warning", "ortografía", speller.error))
        for where, text in texts.items():
            rep.issues += speller.check(text, where)

    # --- citas y referencias a figuras ---
    rep.issues += check_citations({w: t for w, t in texts.items()}, len(lab.references))
    known = figure_ids(lab)
    for where, text in texts.items():
        for m in FIG_REF.finditer(text):
            if m.group(1) not in known:
                rep.issues.append(Issue("error", where, f"{{fig:{m.group(1)}}} no existe (ids: {', '.join(sorted(known)) or 'ninguno'})"))

    # --- código ---
    code_images = 0
    for b in lab.blocks:
        if not b.code:
            continue
        try:
            snips = codemod.plan_code(b.code, lab.project_dir, meta.get("theme", "dark"))
            for snip in snips:
                meta_img = codemod._frame_and_meta(snip)[1]
                fit = fit_code(meta_img["width_px"], meta_img["height_px"], f"código {snip.id}")
                if fit.problem:
                    rep.issues.append(Issue("error", f"bloque {b.index}", fit.problem))
            code_images += len(snips)
        except SnippetError as exc:
            for p in exc.problems:
                rep.issues.append(Issue("error", f"bloque {b.index} código {b.code.id}", p))
        except (FileNotFoundError, ValueError) as exc:
            rep.issues.append(Issue("error", f"bloque {b.index} código {b.code.id}", str(exc)))

    # --- figuras (tamaño y legibilidad, si ya se capturaron) ---
    for fs in lab.figures:
        if fs.kind == "gif":
            rep.issues.append(Issue("warning", f"figura {fs.id}", "los GIF no se animan al imprimir ni al exportar a PDF; "
                                    "usa kind = \"pair\" o \"strip\" salvo que el movimiento sea imprescindible"))
        res = (results or {}).get(fs.id)
        if res and res.kind != "gif":
            fit = fit_capture(res.width, res.height, res.ui_text_px, res.legible, f"figura {fs.id}")
            if fit.problem:
                rep.issues.append(Issue("error", f"figura {fs.id}", fit.problem))
    if results is not None:
        missing = [fs.id for fs in lab.figures if fs.id not in results]
        if missing:
            rep.issues.append(Issue("warning", "figuras", f"sin capturar: {', '.join(missing)} (python main.py unity-lab capture)"))

    # --- balance visual ---
    steps = [b for b in lab.blocks if b.kind == "step"]
    no_image = [b for b in steps if not b.figure and not b.code]
    for b in no_image:
        rep.issues.append(Issue("warning", f"bloque {b.index} (step)", "paso sin figura ni código: cada paso se acompaña de su imagen"))
    n_video_figs = len(lab.figures)
    n_images = n_video_figs + code_images
    total_words = sum(words(t) for t in texts.values())
    per_fig = total_words / n_images if n_images else float("inf")
    if n_images == 0:
        rep.issues.append(Issue("error", "reporte", "el reporte no tiene ninguna imagen"))
    elif per_fig > MAX_WORDS_PER_FIGURE:
        rep.issues.append(Issue("warning", "reporte", f"{per_fig:.0f} palabras por imagen (objetivo ≤ {MAX_WORDS_PER_FIGURE}): "
                                "agrega capturas o recorta texto"))
    if not lab.questions:
        rep.issues.append(Issue("warning", "reporte", "no hay cuestionario ([[question]])"))
    if not lab.conclusions:
        rep.issues.append(Issue("warning", "reporte", "no hay conclusiones ([[conclusion]])"))
    if not lab.references:
        rep.issues.append(Issue("warning", "reporte", "no hay referencias ([[reference]])"))
    annotated = sum(1 for fs in lab.figures if fs.annotate or any(c.annotate for c in fs.frames))
    rep.metrics = {
        "pasos": len(steps), "figuras de video": n_video_figs, "imágenes de código": code_images, "imágenes en total": n_images,
        "palabras": total_words, "palabras por imagen": round(per_fig, 1) if n_images else None,
        "pasos sin imagen": len(no_image), "figuras anotadas": annotated,
        "preguntas": len(lab.questions), "conclusiones": len(lab.conclusions), "referencias": len(lab.references),
    }
    return rep


def format_scorecard(rep: Report) -> str:
    lines = ["Resumen del reporte:"]
    lines += [f"  {k:<22} {v}" for k, v in rep.metrics.items()]
    lines.append(f"  {'errores':<22} {len(rep.errors)}")
    lines.append(f"  {'avisos':<22} {len(rep.warnings)}")
    return "\n".join(lines)
