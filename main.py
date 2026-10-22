#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI principal del generador de reportes.

Cada caso es un pipeline con contrato de entrada/salida (ver `main.py list`).
La forma general es `main.py run <directorio-de-inputs>`: el pipeline se elige por
`pipeline = "..."` en project.toml o por los archivos del directorio.

Los subcomandos históricos (video-report, epis-ne, inspect) se mantienen.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Los módulos de src se importan como `src.*` (desde la raíz) y, por compatibilidad, como paquetes sueltos.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


# ----------------------------------------------------------------------------- pipelines
def cmd_list(args):
    from src.core import PIPELINES
    width = max(len(n) for n in PIPELINES)
    for name, pl in PIPELINES.items():
        flags = []
        if not pl.auto:
            flags.append("explícito")
        if pl.deprecated:
            flags.append("deprecado")
        suffix = f"  ({', '.join(flags)})" if flags else ""
        print(f"{name:<{width}}  {pl.summary}{suffix}")


def cmd_describe(args):
    from src.core import PIPELINES
    if args.name not in PIPELINES:
        sys.exit(f"Pipeline desconocido '{args.name}'. Disponibles: {', '.join(PIPELINES)}")
    pl = PIPELINES[args.name]
    print(f"{pl.name}: {pl.summary}\n")
    print(f"  requiere   : {', '.join(pl.requires) or '(nada fijo; ver project.toml)'}")
    print(f"  acepta     : {', '.join(pl.accepts)}")
    print(f"  produce    : {pl.produces}")
    print(f"  plantilla  : {pl.template}")
    print(f"  detección  : {'automática' if pl.auto else 'solo explícita (--pipeline o project.toml)'}")
    print(f"  ejemplo    : {pl.example}")


def cmd_run(args):
    from src.core import detect, plan_for
    project_dir = Path(args.inputs)
    try:
        pipeline = detect(project_dir, args.pipeline)
        plan = plan_for(pipeline, project_dir)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        sys.exit(f"Error: {exc.args[0] if isinstance(exc, KeyError) else exc}")
    print(f"Pipeline: {pipeline.name}")
    for key, value in plan.items():
        print(f"  {key:<10} {value}")
    if args.dry_run:
        print("(dry-run: no se ejecutó nada)")
        return
    try:
        outputs = pipeline.run(plan)
    except Exception as exc:
        from src.slides_engine import BrowserError, DeckError   # solo en la ruta de error
        if isinstance(exc, (BrowserError, DeckError)):
            sys.exit(f"Error en {pipeline.name}:\n{exc}")
        raise
    for path in outputs:
        print(f"✓ {path}")


# ------------------------------------------------------------------ subcomandos históricos
def run_video_report(args):
    from config import ReportConfig
    from src.video_engine.media_extractor import generate_and_enhance_figures
    from src.reports.unity_practice.generate_report import build_report

    cfg = ReportConfig(high_quality_gifs=not args.low_quality)
    if args.video:
        cfg.video_path = args.video
    if args.template:
        cfg.template_path = args.template
    if args.output:
        cfg.output_path = args.output

    if not args.skip_media:
        print("[1/2] Extrayendo y optimizando figuras y GIFs (skill figure-enhancer)...")
        generate_and_enhance_figures(cfg, args.stages)
    else:
        print("[1/2] Omitiendo extracción de media...")

    print("[2/2] Compilando reporte estructurado en Word...")
    build_report(cfg)
    print("✓ Reporte de video completado con éxito.")


def run_epis_ne_report(args):
    from src.reports.epis_ne.builder import generate_epis_ne_report
    template = args.template or "inputs/templates/academic-epis.docx"
    output = args.output or "output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx"
    generate_epis_ne_report(template_path=template, output_path=output)


def run_inspect(args):
    from src.docx_engine.inspector import inspect_docx
    ok = inspect_docx(args.file)
    sys.exit(0 if ok in (None, True) else 1)


# -------------------------------------------------------------------------------- video
def run_transcribe(args):
    from src.video_engine.transcriber import extract_audio, load_model, transcribe_audio
    source = args.source
    prefix = args.out or os.path.splitext(source)[0]
    audio = source
    if not source.lower().endswith((".wav", ".flac", ".ogg")):
        audio = extract_audio(source, f"{prefix}.wav")
    transcribe_audio(audio, prefix, load_model(args.model, args.threads))


# ----------------------------------------------------------------------------- evidencia
def run_evidence(args):
    from src import evidence_engine as ev
    if args.action == "capture":
        item = ev.capture_commands(args.name, args.commands, args.out_dir, cwd=args.cwd)
        print(f"✓ {args.name}: {item['image']} (códigos de salida {item['returncodes']})")
    elif args.action == "vdmj":
        from src.evidence_engine.vdmj import read_script
        item = ev.capture_vdmj(args.name, args.specs, read_script(args.script), args.out_dir,
                               dialect=args.dialect, release=args.release)
        print(f"✓ {args.name}: {item['image']}")
    elif args.action == "add-image":
        item = ev.register_image(args.name, args.path, args.out_dir, source=args.source, base=args.base, note=args.note)
        print(f"✓ {args.name} registrada como '{item['source']}'")
    elif args.action == "verify":
        issues = ev.verify_manifest(args.out_dir) + ev.verify_claims(args.out_dir, args.text or [])
        for issue in issues:
            print(issue)
        errors = [i for i in issues if i.level == "error"]
        print(f"{len(errors)} error(es), {len(issues) - len(errors)} aviso(s)")
        sys.exit(1 if errors else 0)


def run_typst_lab(args):
    from src.reports import typst_lab
    if args.action == "new":
        print(f"✓ Esqueleto creado en {typst_lab.scaffold(args.project_dir)}")
    else:
        cmd_run(argparse.Namespace(inputs=args.project_dir, pipeline="typst-lab", dry_run=False))


def run_code_image(args):
    from src.editor_engine import BrowserError, SnippetError, build_snippets
    target = Path(args.target)
    spec = target / "snippets.toml" if target.is_dir() else target
    try:
        items = build_snippets(spec, out_dir=args.out_dir)
    except (SnippetError, BrowserError, FileNotFoundError) as exc:
        sys.exit(f"Error en code-image:\n{exc}")
    for item in items:
        print(f"✓ {item['image']}  ({item['width_px']}x{item['height_px']}, texto {item['text_pt_at_6in']} pt a 6 in)")


def run_unity_lab(args):
    from src import unity_lab as ul
    from src.core.docx_render import RenderError, review_docx
    from src.editor_engine import BrowserError
    from src.video_engine.frames import VideoError
    from src.video_engine.ocr import OcrError
    project = Path(args.project_dir)
    problems = (ul.ReportError, ul.FigureError, FileNotFoundError, FileExistsError, BrowserError, VideoError, OcrError, RenderError)
    try:
        if args.action == "new":
            print(f"✓ Esqueleto creado en {ul.scaffold(project)}")
        elif args.action == "plan":
            groups = ul.outline(project)
            for g in groups:
                print(f"{g['when']:>8}  {g['text'][:170]}")
            print(f"\n{len(groups)} pasos candidatos. Usa estos tiempos en `t` de cada figura de content/report.toml.")
        elif args.action == "check":
            lab = ul.load_lab(project)
            out, figures, _ = ul.default_dirs(project.resolve())
            from src.unity_lab.figures import load_results
            rep = ul.check_lab(lab, load_results(figures) or None)
            for issue in rep.issues:
                print(issue)
            print(ul.format_scorecard(rep))
            if rep.errors or (args.strict and rep.warnings):
                sys.exit(1)
        elif args.action == "capture":
            lab = ul.load_lab(project)
            out, figures, evidence = ul.default_dirs(project.resolve())
            video = project.resolve() / lab.meta["video"] if lab.meta.get("video") else None
            ul.capture_figures(lab, video, figures, evidence, force=args.force, only=args.only,
                               langs=lab.meta.get("ocr_langs", "eng"))
            print(f"Hojas de revisión (candidatos y recorte final): {figures / '_review'}")
        elif args.action in ("build", "review"):
            if args.action == "build":
                docx_path = ul.build(project, args.out_dir, force=args.force, strict=args.strict, only=args.only)
            else:
                lab = ul.load_lab(project)
                out, _, _ = ul.default_dirs(project.resolve())
                docx_path = Path(args.docx) if args.docx else out / f"Reporte_Practica_{lab.meta['number']}_Unity.docx"
            if args.action == "review" or args.review:
                rev = review_docx(docx_path, docx_path.parent / "review")
                print(f"✓ {len(rev.pages)} páginas -> {rev.pdf}")
                for sheet in rev.sheets:
                    print(f"  hoja: {sheet}")
                if rev.sparse:
                    print(f"  ATENCIÓN: páginas casi vacías: {rev.sparse} (una figura alta o un salto de página las deja con espacio en blanco)")
    except problems as exc:
        sys.exit(f"Error en unity-lab:\n{exc}")


def run_slides(args):
    from src.reports import html_slides
    if args.action == "new":
        try:
            print(f"✓ Esqueleto creado en {html_slides.scaffold(args.project_dir)}")
        except FileExistsError as exc:
            sys.exit(f"Error: {exc}")
    elif args.action == "check":
        from src.slides_engine import DeckError
        try:
            html_slides.check(args.project_dir)
        except (DeckError, FileNotFoundError, ValueError) as exc:
            sys.exit(f"Error en html-slides:\n{exc}")
        print("✓ Contenido, tema y reglas (claro, sin animaciones) correctos. Chrome mide los desbordes en `build`.")
    else:
        cmd_run(argparse.Namespace(inputs=args.project_dir, pipeline="html-slides", dry_run=False))


# ------------------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generador de reportes por casos (inputs -> pipeline -> output)")
    sub = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    sub.add_parser("list", help="Lista los pipelines disponibles").set_defaults(func=cmd_list)

    p = sub.add_parser("describe", help="Muestra el contrato de un pipeline")
    p.add_argument("name")
    p.set_defaults(func=cmd_describe)

    p = sub.add_parser("run", help="Ejecuta el pipeline que corresponde a un directorio de inputs")
    p.add_argument("inputs", help="Directorio de inputs (p. ej. inputs/NE/Lab05)")
    p.add_argument("--pipeline", help="Fuerza un pipeline (si no, se detecta o se toma de project.toml)")
    p.add_argument("--dry-run", action="store_true", help="Muestra qué entradas y salidas usaría, sin ejecutar")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("video-report", help="Reporte Word a partir de video (GIFs y figuras anotadas)")
    p.add_argument("--video")
    p.add_argument("--template")
    p.add_argument("--output")
    p.add_argument("--stages", help="JSON con los hitos a extraer (por defecto, la práctica Unity 02)")
    p.add_argument("--low-quality", action="store_true", help="GIFs en calidad estándar")
    p.add_argument("--skip-media", action="store_true", help="No regenerar GIFs")
    p.set_defaults(func=run_video_report)

    p = sub.add_parser("epis-ne", help="Informe EPIS de Negocios Electrónicos")
    p.add_argument("--template")
    p.add_argument("--output")
    p.set_defaults(func=run_epis_ne_report)

    p = sub.add_parser("inspect", help="Inspección estructural de un .docx (código de salida 1 si hay anomalías)")
    p.add_argument("file")
    p.set_defaults(func=run_inspect)

    p = sub.add_parser("transcribe", help="Transcribe un video o WAV (faster-whisper, offline)")
    p.add_argument("source", help="Video o audio")
    p.add_argument("--out", help="Prefijo de salida (.txt/.json); por defecto junto al origen")
    p.add_argument("--model", default="small")
    p.add_argument("--threads", type=int, default=8)
    p.set_defaults(func=run_transcribe)

    ev = sub.add_parser("evidence", help="Evidencia real: capturar, registrar y verificar")
    esub = ev.add_subparsers(dest="action", required=True)
    e = esub.add_parser("capture", help="Ejecuta comandos (sin shell) y guarda log + figura + manifiesto")
    e.add_argument("name")
    e.add_argument("commands", nargs="+")
    e.add_argument("--out-dir", required=True)
    e.add_argument("--cwd")
    e = esub.add_parser("vdmj", help="Sesión interactiva real de VDMJ")
    e.add_argument("name")
    e.add_argument("--specs", nargs="+", required=True)
    e.add_argument("--script", required=True, help="Comandos del intérprete ('--' = comentario)")
    e.add_argument("--out-dir", required=True)
    e.add_argument("--dialect", default="vdmpp")
    e.add_argument("--release", default="classic")
    e = esub.add_parser("add-image", help="Registra una captura tomada a mano o una versión anotada")
    e.add_argument("name")
    e.add_argument("path")
    e.add_argument("--out-dir", required=True)
    e.add_argument("--source", choices=["manual", "annotated"], default="manual")
    e.add_argument("--base", help="Item base (obligatorio si --source annotated)")
    e.add_argument("--note", default="")
    e = esub.add_parser("verify", help="Comprueba hashes, orígenes y afirmaciones del texto contra los logs")
    e.add_argument("--out-dir", required=True)
    e.add_argument("--text", nargs="*", help="Archivos .typ/.md con directivas `evidence: <id> expect: <literal>`")
    ev.set_defaults(func=run_evidence)

    p = sub.add_parser("typst-lab", help="Informe de laboratorio en Typst/PDF")
    p.add_argument("action", choices=["new", "build"])
    p.add_argument("project_dir")
    p.set_defaults(func=run_typst_lab)

    p = sub.add_parser("code-image", help="Imágenes de fragmentos de código (aspecto de editor) desde snippets.toml")
    p.add_argument("target", help="carpeta del caso (con snippets.toml) o ruta al snippets.toml")
    p.add_argument("--out-dir", help="directorio de evidencia (por defecto output/<caso>/evidence)")
    p.set_defaults(func=run_code_image)

    p = sub.add_parser("unity-lab", help="Reporte de laboratorio de Unity (docx): figuras del video, código como imagen, revisión")
    p.add_argument("action", choices=["new", "plan", "check", "capture", "build", "review"],
                   help="new: esqueleto; plan: pasos candidatos desde la transcripción; check: revisa texto/código/citas; "
                        "capture: figuras del video; build: .docx completo; review: renderiza el .docx a imágenes")
    p.add_argument("project_dir")
    p.add_argument("--force", action="store_true", help="recaptura las figuras aunque estén en caché")
    p.add_argument("--only", nargs="*", help="ids de figuras a capturar")
    p.add_argument("--strict", action="store_true", help="los avisos también detienen el build")
    p.add_argument("--review", action="store_true", help="tras el build, renderiza el .docx (PDF + hojas de páginas)")
    p.add_argument("--out-dir", help="carpeta de salida (por defecto output/<caso>)")
    p.add_argument("--docx", help="(review) .docx a renderizar")
    p.set_defaults(func=run_unity_lab)

    p = sub.add_parser("slides", help="Diapositivas HTML (tema claro, sin animaciones) + PDF")
    p.add_argument("action", choices=["new", "check", "build"],
                   help="new: esqueleto; check: valida contenido/tema sin Chrome; build: HTML + PDF")
    p.add_argument("project_dir")
    p.set_defaults(func=run_slides)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
