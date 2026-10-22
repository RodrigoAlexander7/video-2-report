# -*- coding: utf-8 -*-
"""Modelo y validación del reporte de laboratorio de Unity: ``project.toml [unity]`` + ``content/report.toml``.

``report.toml`` describe el reporte con bloques cerrados (como `slides.toml` en las diapositivas):

    [[block]]                          # encabezado de la sección de ejercicios
    kind = "heading"                   # level = 1 (por defecto) o 2
    text = "Configurar el Rigidbody"

    [[block]]                          # un paso: 1-2 frases + su figura o su código
    kind = "step"
    text = "Agregamos un Rigidbody al GameObject raíz de Mango. La {fig:rigidbody} muestra los valores."
    [block.figure]                     # figura sacada del video (ver figures.py)
    id = "rigidbody"
    t = "2:05"
    expect = ["Rigidbody"]
    caption = "Componente Rigidbody en el Inspector."
    [block.figure.crop]
    panel = "inspector"
    [block.code]                       # fragmento de código: archivo real + líneas (se divide solo si es largo)
    id = "movimiento"
    file = "code/CatControl.cs"
    lines = "13-30"

    [[question]]  q = "..."  a = "..."
    [[conclusion]]  text = "..."
    [[reference]]  text = "..."        # se cita en el texto como [1]
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..video_engine.annotate import AnnotationError, AnnotationSpec, parse_annotation
from ..video_engine.crops import CropError, CropSpec, parse_crop
from ..video_engine.frames import parse_time

# Presupuestos de texto (palabras): el reporte de 18 usaba ~40 palabras por figura; estos topes lo mantienen visual.
LIMITS = {"heading": 14, "step": 45, "caption": 28, "answer": 90, "question": 40, "conclusion": 55, "note": 40}
MAX_CODE_LINES_PER_IMAGE = 20
MAX_CONCLUSIONS = 4
_ID = re.compile(r"^[A-Za-z0-9][\w\-]*$")
META_REQUIRED = ("template", "title", "number", "date", "members")
META_ALLOWED = {"template", "video", "title", "number", "course", "term", "level", "date", "time", "members", "instructor",
                "video_link", "theme", "content", "transcript", "glossary", "style_allow", "spell_ignore", "ocr_langs"}
FIGURE_KEYS = {"id", "kind", "t", "window", "step", "expect", "crop", "annotate", "caption", "legible",
               "frames", "t_start", "t_end", "count", "duration", "gif_rect"}
CODE_KEYS = {"id", "file", "lines", "focus", "caption", "dedent", "path", "max_lines"}
BLOCK_KEYS = {"kind", "text", "level", "figure", "code"}


class ReportError(ValueError):
    """Uno o más problemas en el contenido; ``problems`` los lista todos."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("\n".join(f"  - {p}" for p in self.problems))


def words(text: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"\{fig:[\w\-]+\}|`[^`]*`", " x ", text)))


@dataclass
class FigureSpec:
    id: str
    kind: str = "frame"                       # frame | pair | strip | gif
    t: Optional[float] = None
    window: float = 3.0
    step: float = 0.5
    expect: List[str] = field(default_factory=list)
    crop: Optional[CropSpec] = None
    annotate: Optional[AnnotationSpec] = None
    caption: str = ""
    legible: bool = True                      # false: escena del juego, sin texto de interfaz que deba leerse
    frames: List["FigureSpec"] = field(default_factory=list)   # pair
    t_start: Optional[float] = None
    t_end: Optional[float] = None
    count: int = 3
    duration: float = 5.0
    gif_rect: Optional[tuple] = None
    raw: Dict[str, Any] = field(default_factory=dict)          # tal cual el TOML (clave de caché)


@dataclass
class CodeSpec:
    id: str
    file: str
    lines: Any = None
    focus: List[int] = field(default_factory=list)
    caption: str = ""
    dedent: bool = False
    path: Optional[str] = None
    max_lines: int = MAX_CODE_LINES_PER_IMAGE


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 1
    figure: Optional[FigureSpec] = None
    code: Optional[CodeSpec] = None
    index: int = 0


@dataclass
class Lab:
    meta: Dict[str, Any]
    blocks: List[Block]
    questions: List[Dict[str, str]]
    conclusions: List[str]
    references: List[str]
    project_dir: Path
    content_path: Path
    figures: List[FigureSpec] = field(default_factory=list)    # en orden de aparición (sin los `frames` internos)


def _num(value: Any, where: str, problems: List[str]) -> Optional[float]:
    try:
        return parse_time(value)
    except (ValueError, TypeError) as exc:
        problems.append(f"{where}: {exc}")
        return None


def _figure(raw: Dict[str, Any], where: str, problems: List[str], inner: bool = False) -> Optional[FigureSpec]:
    unknown = set(raw) - FIGURE_KEYS
    for key in sorted(unknown):
        problems.append(f"{where}: clave desconocida '{key}' (válidas: {', '.join(sorted(FIGURE_KEYS))})")
    fid = raw.get("id")
    if not inner and (not isinstance(fid, str) or not _ID.match(fid)):
        problems.append(f"{where}: falta 'id' (letras, números y guiones; es el nombre del archivo y de {{fig:id}})")
        return None
    kind = raw.get("kind", "frame")
    if kind not in ("frame", "pair", "strip", "gif"):
        problems.append(f"{where}: kind '{kind}' inválido (frame, pair, strip o gif)")
        return None
    fs = FigureSpec(id=fid or "", kind=kind, caption=raw.get("caption", ""), legible=bool(raw.get("legible", True)),
                    window=float(raw.get("window", 3.0)), step=float(raw.get("step", 0.5)), raw=raw)
    if not inner:
        if not isinstance(fs.caption, str) or not fs.caption.strip():
            problems.append(f"{where}: falta 'caption' (qué muestra la figura, sin interpretaciones)")
        elif words(fs.caption) > LIMITS["caption"]:
            problems.append(f"{where}: el pie de figura tiene {words(fs.caption)} palabras (máximo {LIMITS['caption']})")
    if not 0.5 <= fs.window <= 10 or not 0.25 <= fs.step <= 2:
        problems.append(f"{where}: 'window' va de 0,5 a 10 s y 'step' de 0,25 a 2 s")
    expect = raw.get("expect", [])
    if not (isinstance(expect, list) and all(isinstance(e, str) and e.strip() for e in expect)):
        problems.append(f"{where}: 'expect' es una lista de textos que deben verse en la captura")
    else:
        fs.expect = list(expect)
    try:
        fs.crop = parse_crop(raw.get("crop"), f"{where}.crop")
        fs.annotate = parse_annotation(raw.get("annotate"), f"{where}.annotate")
    except (CropError, AnnotationError) as exc:
        problems.append(str(exc))
    if kind in ("frame", "gif") and "t" not in raw:
        problems.append(f"{where}: falta 't' (segundo del video, p. ej. 125 o \"2:05\")")
    elif "t" in raw:
        fs.t = _num(raw["t"], f"{where}.t", problems)
    if kind == "pair":
        sub = raw.get("frames")
        if not (isinstance(sub, list) and len(sub) == 2):
            problems.append(f"{where}: un 'pair' necesita exactamente 2 tablas [[...frames]] (antes y después)")
        else:
            for k, s in enumerate(sub, 1):
                child = _figure({**{key: raw[key] for key in ("window", "step", "legible") if key in raw}, **s},
                                f"{where}.frames[{k}]", problems, inner=True)
                if child:
                    child.kind = "frame"
                    fs.frames.append(child)
        if fs.annotate:
            problems.append(f"{where}: anota cada fotograma dentro de 'frames', no la figura 'pair'")
    if kind == "strip":
        if "t_start" not in raw or "t_end" not in raw:
            problems.append(f"{where}: un 'strip' necesita 't_start' y 't_end'")
        else:
            fs.t_start, fs.t_end = _num(raw["t_start"], f"{where}.t_start", problems), _num(raw["t_end"], f"{where}.t_end", problems)
            if fs.t_start is not None and fs.t_end is not None and fs.t_end <= fs.t_start:
                problems.append(f"{where}: 't_end' debe ser mayor que 't_start'")
        fs.count = int(raw.get("count", 3))
        if not 2 <= fs.count <= 4:
            problems.append(f"{where}: 'count' va de 2 a 4 fotogramas")
        if fs.annotate:
            problems.append(f"{where}: un 'strip' no admite anotación")
    if kind == "gif":
        fs.duration = float(raw.get("duration", 5.0))
        if not 1 <= fs.duration <= 10:
            problems.append(f"{where}: 'duration' va de 1 a 10 s")
        r = raw.get("gif_rect")
        if r is not None:
            if not (isinstance(r, list) and len(r) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in r) and r[0] < r[2] and r[1] < r[3]):
                problems.append(f"{where}: 'gif_rect' son 4 fracciones [x0, y0, x1, y1] del fotograma")
            else:
                fs.gif_rect = tuple(float(v) for v in r)
        if fs.annotate:
            problems.append(f"{where}: un 'gif' no admite anotación")
    return fs


def _code(raw: Dict[str, Any], where: str, project_dir: Path, problems: List[str]) -> Optional[CodeSpec]:
    for key in sorted(set(raw) - CODE_KEYS):
        problems.append(f"{where}: clave desconocida '{key}' (válidas: {', '.join(sorted(CODE_KEYS))})")
    cid, file = raw.get("id"), raw.get("file")
    if not isinstance(cid, str) or not _ID.match(cid):
        problems.append(f"{where}: falta 'id'")
        return None
    if not isinstance(file, str):
        problems.append(f"{where}: falta 'file' (archivo de código, relativo a la carpeta del caso)")
        return None
    if not (project_dir / file).is_file():
        problems.append(f"{where}: no existe {project_dir / file}")
    focus = raw.get("focus", [])
    if not (isinstance(focus, list) and all(isinstance(n, int) for n in focus)):
        problems.append(f"{where}: 'focus' es una lista de números de línea")
        focus = []
    cap = raw.get("caption", "")
    if cap and words(cap) > LIMITS["caption"]:
        problems.append(f"{where}: el pie tiene {words(cap)} palabras (máximo {LIMITS['caption']})")
    ml = int(raw.get("max_lines", MAX_CODE_LINES_PER_IMAGE))
    if not 6 <= ml <= 40:
        problems.append(f"{where}: 'max_lines' va de 6 a 40")
    return CodeSpec(id=cid, file=file, lines=raw.get("lines"), focus=list(focus), caption=cap,
                    dedent=bool(raw.get("dedent", False)), path=raw.get("path"), max_lines=ml)


def load_meta(project_dir: Path) -> Dict[str, Any]:
    toml_path = project_dir / "project.toml"
    if not toml_path.is_file():
        raise FileNotFoundError(f"No existe {toml_path}")
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)
    meta = data.get("unity")
    if not isinstance(meta, dict):
        raise ReportError([f"{toml_path.name}: falta la tabla [unity] (plantilla, título, número, fecha, integrantes)"])
    problems = [f"[unity]: clave desconocida '{k}' (válidas: {', '.join(sorted(META_ALLOWED))})" for k in sorted(set(meta) - META_ALLOWED)]
    problems += [f"[unity]: falta '{k}'" for k in META_REQUIRED if meta.get(k) in (None, "", [])]
    if "members" in meta and not (isinstance(meta["members"], list) and all(isinstance(m, str) for m in meta["members"])):
        problems.append("[unity]: 'members' es una lista de nombres")
    if meta.get("theme", "dark") not in ("dark", "light"):
        problems.append("[unity]: theme debe ser 'dark' o 'light'")
    tpl = meta.get("template")
    if isinstance(tpl, str) and not (project_dir / tpl).is_file():
        problems.append(f"[unity]: no existe la plantilla {project_dir / tpl}")
    if problems:
        raise ReportError(problems)
    return meta


def load_lab(project_dir) -> Lab:
    project_dir = Path(project_dir).resolve()
    meta = load_meta(project_dir)
    content = project_dir / meta.get("content", "content/report.toml")
    if not content.is_file():
        raise FileNotFoundError(f"No existe {content} (crea el esqueleto con: python main.py unity-lab new {project_dir})")
    try:
        data = tomllib.loads(content.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ReportError([f"{content.name}: TOML inválido: {exc}"]) from exc

    problems: List[str] = []
    blocks: List[Block] = []
    figures: List[FigureSpec] = []
    seen_ids: Dict[str, str] = {}

    def claim(ident: str, where: str):
        if ident in seen_ids:
            problems.append(f"{where}: el id '{ident}' ya se usa en {seen_ids[ident]}")
        seen_ids[ident] = where

    for i, raw in enumerate(data.get("block") or [], 1):
        kind = raw.get("kind")
        where = f"bloque {i} ({kind})"
        for key in sorted(set(raw) - BLOCK_KEYS):
            problems.append(f"{where}: clave desconocida '{key}' (válidas: {', '.join(sorted(BLOCK_KEYS))})")
        if kind not in ("heading", "step", "code", "figure"):
            problems.append(f"bloque {i}: kind '{kind}' inválido (heading, step, code o figure)")
            continue
        text = raw.get("text", "")
        blk = Block(kind=kind, text=text.strip() if isinstance(text, str) else "", index=i)
        if kind in ("heading", "step") and not blk.text:
            problems.append(f"{where}: falta 'text'")
        if kind in ("code", "figure") and blk.text:
            problems.append(f"{where}: un bloque '{kind}' no lleva 'text' (usa un 'step' si necesitas texto)")
        if kind == "heading":
            blk.level = int(raw.get("level", 1))
            if blk.level not in (1, 2):
                problems.append(f"{where}: level debe ser 1 o 2")
            if words(blk.text) > LIMITS["heading"]:
                problems.append(f"{where}: el encabezado tiene {words(blk.text)} palabras (máximo {LIMITS['heading']})")
            for extra in ("figure", "code"):
                if extra in raw:
                    problems.append(f"{where}: un encabezado no lleva '{extra}'")
        if kind == "step" and words(blk.text) > LIMITS["step"]:
            problems.append(f"{where}: el paso tiene {words(blk.text)} palabras (máximo {LIMITS['step']}): "
                            "divídelo en dos pasos, cada uno con su figura")
        if "figure" in raw and kind in ("step", "figure"):
            fs = _figure(raw["figure"], f"{where}.figure", problems)
            if fs:
                claim(fs.id, f"{where}.figure")
                blk.figure = fs
                figures.append(fs)
        elif kind == "figure":
            problems.append(f"{where}: falta la tabla [block.figure]")
        if "code" in raw and kind in ("step", "code"):
            cs = _code(raw["code"], f"{where}.code", project_dir, problems)
            if cs:
                claim(cs.id, f"{where}.code")
                blk.code = cs
        elif kind == "code":
            problems.append(f"{where}: falta la tabla [block.code]")
        blocks.append(blk)
    if not blocks:
        problems.append(f"{content.name}: no hay ningún [[block]]")

    questions: List[Dict[str, str]] = []
    for i, raw in enumerate(data.get("question") or [], 1):
        q, a = raw.get("q", ""), raw.get("a", "")
        if not (isinstance(q, str) and q.strip() and isinstance(a, str) and a.strip()):
            problems.append(f"pregunta {i}: necesita 'q' y 'a'")
            continue
        if words(a) > LIMITS["answer"]:
            problems.append(f"pregunta {i}: la respuesta tiene {words(a)} palabras (máximo {LIMITS['answer']})")
        if words(q) > LIMITS["question"]:
            problems.append(f"pregunta {i}: el enunciado tiene {words(q)} palabras (máximo {LIMITS['question']})")
        questions.append({"q": q.strip(), "a": a.strip()})
    conclusions: List[str] = []
    for i, raw in enumerate(data.get("conclusion") or [], 1):
        text = raw.get("text", "")
        if not (isinstance(text, str) and text.strip()):
            problems.append(f"conclusión {i}: falta 'text'")
        elif words(text) > LIMITS["conclusion"]:
            problems.append(f"conclusión {i}: tiene {words(text)} palabras (máximo {LIMITS['conclusion']})")
        else:
            conclusions.append(text.strip())
    if len(conclusions) > MAX_CONCLUSIONS:
        problems.append(f"hay {len(conclusions)} conclusiones (máximo {MAX_CONCLUSIONS}): deja las que salen de lo observado")
    references: List[str] = []
    for i, raw in enumerate(data.get("reference") or [], 1):
        text = raw.get("text", "")
        if not (isinstance(text, str) and text.strip()):
            problems.append(f"referencia {i}: falta 'text'")
        else:
            references.append(text.strip())
    for key in set(data) - {"block", "question", "conclusion", "reference"}:
        problems.append(f"{content.name}: sección desconocida '{key}'")
    if problems:
        raise ReportError(problems)
    return Lab(meta=meta, blocks=blocks, questions=questions, conclusions=conclusions, references=references,
               project_dir=project_dir, content_path=content, figures=figures)
