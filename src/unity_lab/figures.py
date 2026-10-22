# -*- coding: utf-8 -*-
"""Figuras del video: fotograma elegido por calidad y OCR, recorte semántico, anotación opcional y registro verificable.

Por cada figura de ``report.toml``:
  1. se extraen fotogramas alrededor de ``t`` y se puntúan (nitidez y estabilidad);
  2. con OCR se comprueba que se vean los textos esperados (``expect``, el objetivo de la anotación y los anclajes del recorte);
  3. se recorta (por panel o entre dos textos) sin cortar líneas de texto y se anota como máximo un control;
  4. se guarda ``<id>.png`` más una hoja de revisión con los candidatos, y se registra en el manifiesto de evidencia.
El resultado queda en ``captures.json``: ``build`` lo reutiliza si la especificación y el video no cambiaron.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from ..evidence_engine import manifest as mf
from ..video_engine import ocr
from ..video_engine.annotate import AnnotationError, annotate
from ..video_engine.crops import CropError, resolve_crop
from ..video_engine.frames import (Candidate, VideoError, contact_sheet, extract_window, format_time, load_rgb, probe, score)
from .model import FigureSpec, Lab

CODE_VERSION = "1"            # súbelo si cambia el algoritmo de captura: invalida la caché
TOP_K = 4                     # candidatos que siempre pasan por OCR
MAX_OCR = 10                  # tope de candidatos con OCR cuando faltan textos
GAP_PX = 18


class FigureError(RuntimeError):
    """No se pudo obtener una o más figuras; ``problems`` explica cada una."""

    def __init__(self, problems: List[str]):
        self.problems = list(problems)
        super().__init__("\n".join(f"  - {p}" for p in self.problems))


@dataclass
class FigureResult:
    id: str
    path: str                                  # relativo al directorio de figuras
    width: int
    height: int
    kind: str
    legible: bool
    ui_text_px: Optional[float] = None
    t_chosen: List[float] = field(default_factory=list)
    spec_hash: str = ""

    def to_json(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _needed_texts(fs: FigureSpec) -> List[str]:
    from ..video_engine.crops import PANEL_TABS
    texts = list(fs.expect)
    if fs.annotate and fs.annotate.target:
        texts.append(fs.annotate.target)
    if fs.crop:
        if fs.crop.panel:
            texts.append(PANEL_TABS[fs.crop.panel])
        texts += [t for t in (fs.crop.desde, fs.crop.hasta, fs.crop.around) if t]
    return list(dict.fromkeys(texts))


def _needs_ocr(fs: FigureSpec) -> bool:
    return bool(_needed_texts(fs)) or fs.legible


def spec_hash(fs: FigureSpec, video_sha: str) -> str:
    payload = json.dumps(fs.raw, sort_keys=True, ensure_ascii=False, default=str) + video_sha + CODE_VERSION
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _capture_frame(video: Path, vinfo: Dict[str, Any], fs: FigureSpec, work: Path, langs: str) -> Tuple[Image.Image, Dict[str, Any], List[Tuple[str, Image.Image]]]:
    """Un fotograma final (recortado y anotado) + datos de la elección + miniaturas de candidatos para la hoja de revisión."""
    cands = score(extract_window(video, fs.t, fs.window, fs.step, work / "cands", vinfo.get("duration")))
    ranked = sorted(cands, key=lambda c: -c.quality)
    if ranked[0].quality == 0:
        raise FigureError([f"{fs.id}: todos los fotogramas cerca de t={format_time(fs.t)} están en negro; revisa el segundo"])
    needed = _needed_texts(fs)
    words: List[ocr.Word] = []
    best: Candidate = ranked[0]
    if _needs_ocr(fs):
        best = None
        for n, c in enumerate(ranked[:MAX_OCR] if needed else ranked[:1]):
            if n >= TOP_K and best is not None and not best.missing:
                break
            w = ocr.ocr_words(c.path, langs=langs, min_conf=15)       # con baja confianza también: sirve para no cortar texto al recortar
            c.found, c.missing = ocr.find_all([x for x in w if x.conf >= 40], needed)
            c.hits = len(c.found)
            if best is None or (c.hits, c.quality) > (best.hits, best.quality):
                best, words = c, w
        if needed and best.missing:
            raise _MissingText(fs, best, cands, ranked, needed)
    img = load_rgb(best.path)
    try:
        box = resolve_crop(img, words, fs.crop)
    except CropError as exc:
        raise FigureError([f"{fs.id}: {exc}"]) from exc
    final = img.crop(box)
    note: Dict[str, Any] = {"t": round(best.t, 2), "crop": list(box), "hits": best.hits, "needed": needed,
                            "ui_text_px": ocr.text_height_px(words, box) if words else None}
    if fs.annotate:
        spec = fs.annotate
        if spec.target:
            tb = best.found.get(spec.target)
            tbox = (tb[0] - box[0], tb[1] - box[1], tb[2] - box[0], tb[3] - box[1])
            if tbox[0] < 0 or tbox[1] < 0 or tbox[2] > final.width or tbox[3] > final.height:
                raise FigureError([f"{fs.id}: «{spec.target}» queda fuera del recorte; amplía 'crop' o cambia el objetivo"])
            el, et, er, eb = spec.extend
            tbox = (max(0, tbox[0] - el), max(0, tbox[1] - et), min(final.width, tbox[2] + er), min(final.height, tbox[3] + eb))
        else:
            fw, fh = final.size
            tbox = (round(spec.rect[0] * fw), round(spec.rect[1] * fh), round(spec.rect[2] * fw), round(spec.rect[3] * fh))
        try:
            res = annotate(final, spec, tbox)
        except AnnotationError as exc:
            raise FigureError([f"{fs.id}: {exc}"]) from exc
        final = res.image
        note["annotation"] = {"style": spec.style, "box": list(res.box), "tip": list(res.tip) if res.tip else None}
    thumbs = [(f"{'*' if c is best else ' '} t={format_time(c.t)}  calidad={c.quality:.2f}  textos={c.hits}/{len(needed)}",
               load_rgb(c.path)) for c in ranked[:MAX_OCR if needed else TOP_K]]
    return final, note, thumbs


class _MissingText(FigureError):
    def __init__(self, fs: FigureSpec, best: Candidate, cands, ranked, needed):
        super().__init__([f"{fs.id}: no se ve «{'», «'.join(best.missing)}» en ningún fotograma cerca de t={format_time(fs.t)} "
                          f"(mejor candidato t={format_time(best.t)}, {best.hits}/{len(needed)} textos). "
                          "Cambia 't', amplía 'window' o corrige el texto esperado; mira la hoja de revisión."])
        self.fs, self.ranked, self.needed = fs, ranked, needed


def _hstack(images: List[Image.Image]) -> Image.Image:
    height = min(im.height for im in images)
    scaled = [im.resize((round(im.width * height / im.height), height), Image.LANCZOS) for im in images]
    out = Image.new("RGB", (sum(i.width for i in scaled) + GAP_PX * (len(scaled) - 1), height), "white")
    x = 0
    for im in scaled:
        out.paste(im, (x, 0))
        x += im.width + GAP_PX
    return out


def _clone(fs: FigureSpec, **changes) -> FigureSpec:
    data = {**fs.__dict__, **changes}
    return FigureSpec(**data)


def _capture(video: Path, vinfo: Dict[str, Any], fs: FigureSpec, out_dir: Path, work: Path, langs: str):
    """Devuelve (ruta, imagen o None, ui_text_px, tiempos, miniaturas de revisión)."""
    review: List[Tuple[str, Image.Image]] = []
    if fs.kind == "gif":
        from ..video_engine.media_extractor import generate_gif
        out = out_dir / f"{fs.id}.gif"
        crop = ""
        if fs.gif_rect:
            x0, y0, x1, y1 = fs.gif_rect
            crop = f"crop=iw*{x1 - x0:.4f}:ih*{y1 - y0:.4f}:iw*{x0:.4f}:ih*{y0:.4f}"
        generate_gif(str(video), fs.t, fs.duration, str(out), crop_filter=crop)
        with Image.open(out) as im:
            size = im.size
        return out, size, None, [fs.t], review
    if fs.kind == "frame":
        frames = [fs]
    elif fs.kind == "pair":
        frames = [_clone(child, id=f"{fs.id}-{k}", caption=fs.caption, window=child.window, legible=child.legible)
                  for k, child in enumerate(fs.frames, 1)]
    else:  # strip
        n = fs.count
        times = [fs.t_start + (fs.t_end - fs.t_start) * k / (n - 1) for k in range(n)]
        frames = [_clone(fs, id=f"{fs.id}-{k}", kind="frame", t=t) for k, t in enumerate(times, 1)]
    images, texts, times = [], [], []
    for k, f in enumerate(frames):
        img, note, thumbs = _capture_frame(video, vinfo, f, work / f"f{k}", langs)
        images.append(img)
        times.append(note["t"])
        if note["ui_text_px"]:
            texts.append(note["ui_text_px"])
        review.append((f"FINAL {f.id}  t={format_time(note['t'])}", img))
        review.extend(thumbs[:4])
    final = images[0] if len(images) == 1 else _hstack(images)
    out = out_dir / f"{fs.id}.png"
    final.save(out, optimize=True)
    return out, final.size, (min(texts) if texts else None), times, review


def capture_figures(lab: Lab, video: Optional[Path], out_dir: Path, evidence_dir: Path, force: bool = False,
                    only: Optional[List[str]] = None, langs: str = "eng") -> Dict[str, FigureResult]:
    """Genera (o reutiliza de la caché) todas las figuras de video del reporte."""
    out_dir, evidence_dir = Path(out_dir), Path(evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "captures.json"
    cache: Dict[str, Any] = json.loads(index_path.read_text(encoding="utf-8")) if index_path.is_file() else {}
    results: Dict[str, FigureResult] = {}
    problems: List[str] = []
    pending = [fs for fs in lab.figures if not only or fs.id in only]
    if pending and (video is None or not Path(video).is_file()):
        raise FigureError([f"no existe el video ({video}): define [unity] video en project.toml"])
    vinfo = probe(video) if pending else {}
    video_sha = mf.sha256_file(str(video)) if pending else ""
    for fs in pending:
        h = spec_hash(fs, video_sha)
        old = cache.get(fs.id)
        target = out_dir / (old["path"] if old else f"{fs.id}.png")
        if old and old.get("spec_hash") == h and target.is_file() and not force:
            results[fs.id] = FigureResult(**old)
            continue
        work = out_dir / "_work" / fs.id
        try:
            path, size, ui_px, times, review = _capture(Path(video), vinfo, fs, out_dir, work, langs)
        except _MissingText as exc:
            sheet = contact_sheet([(f"t={format_time(c.t)} calidad={c.quality:.2f} textos={c.hits}/{len(exc.needed)}", load_rgb(c.path))
                                   for c in exc.ranked[:6]], out_dir / "_review" / f"{fs.id}.png", cols=3, thumb_w=520)
            problems.append(f"{exc.problems[0]} [{sheet}]")
            continue
        except (FigureError, VideoError, ocr.OcrError) as exc:
            problems.append(str(exc).strip().lstrip("- ").strip())
            continue
        sheet = None
        if review:
            sheet = contact_sheet(review, out_dir / "_review" / f"{fs.id}.png", cols=3, thumb_w=520, highlight=0)
        res = FigureResult(id=fs.id, path=path.name, width=size[0], height=size[1], kind=fs.kind, legible=fs.legible,
                           ui_text_px=ui_px, t_chosen=times, spec_hash=h)
        results[fs.id] = res
        cache[fs.id] = res.to_json()
        mf.upsert(str(evidence_dir), fs.id, {
            "source": "video", "captured_at": mf.now_iso(), "image": mf.rel(str(evidence_dir), str(path)),
            "image_sha256": mf.sha256_file(str(path)), "video": mf.rel(str(evidence_dir), str(video)), "video_sha256": video_sha,
            "kind": fs.kind, "t_requested": [fs.t] if fs.t is not None else [fs.t_start, fs.t_end], "t_chosen": times,
            "expect": fs.expect, "ui_text_px": ui_px, "review": mf.rel(str(evidence_dir), str(sheet)) if sheet else None, "note": ""})
        print(f"✓ {fs.id}: t={', '.join(format_time(t) for t in times)}  {size[0]}x{size[1]}px  "
              f"texto UI {ui_px:.0f}px" if ui_px else f"✓ {fs.id}: t={', '.join(format_time(t) for t in times)}  {size[0]}x{size[1]}px")
    index_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if problems:
        raise FigureError(problems)
    return results


def load_results(out_dir: Path) -> Dict[str, FigureResult]:
    index = Path(out_dir) / "captures.json"
    if not index.is_file():
        return {}
    return {k: FigureResult(**v) for k, v in json.loads(index.read_text(encoding="utf-8")).items()}
