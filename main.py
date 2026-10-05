#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Principal y Orquestador Modular de Reportes
Permite compilar:
- Reportes basados en Video (con GIFs y skills figure-enhancer / progressive-tutorial)
- Informes institucionales EPIS (Negocios Electrónicos con Odoo, rúbricas y plantillas .docx)
- Inspección estructural rápida (--inspect)
"""

import sys
import os
import argparse

# Asegurar que 'src' esté en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

def run_video_report(args):
    from config import ReportConfig, DEFAULT_CONFIG
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
        print("[1/2] Extrayendo y optimizando figuras y GIFs con la skill figure-enhancer...")
        generate_and_enhance_figures(cfg)
    else:
        print("[1/2] Omitiendo extracción de media...")

    print("[2/2] Compilando reporte estructurado en Word...")
    build_report(cfg)
    print("✓ Reporte de video completado con éxito.")

def run_epis_ne_report(args):
    from src.reports.epis_ne.builder import generate_epis_ne_report
    template = args.template if args.template else "inputs/templates/academic-epis.docx"
    output = args.output if args.output else "output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx"
    generate_epis_ne_report(template_path=template, output_path=output)

def run_inspect(args):
    from src.docx_engine.inspector import inspect_docx
    inspect_docx(args.file)

def main():
    parser = argparse.ArgumentParser(description="Orquestador Modular de Generación de Reportes")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Subcomando: video-report
    parser_video = subparsers.add_parser("video-report", help="Genera reporte a partir de video con GIFs/Typst")
    parser_video.add_argument("--video", type=str, help="Ruta al video MP4")
    parser_video.add_argument("--template", type=str, help="Ruta a la plantilla")
    parser_video.add_argument("--output", type=str, help="Ruta del documento resultante")
    parser_video.add_argument("--low-quality", action="store_true", help="Generar GIFs en calidad estándar")
    parser_video.add_argument("--skip-media", action="store_true", help="Saltar regeneración de GIFs")

    # Subcomando: epis-ne
    parser_epis = subparsers.add_parser("epis-ne", help="Genera informe académico EPIS Negocios Electrónicos")
    parser_epis.add_argument("--template", type=str, help="Ruta a la plantilla canónica (.docx)")
    parser_epis.add_argument("--output", type=str, help="Ruta de salida del .docx")

    # Subcomando: inspect
    parser_inspect = subparsers.add_parser("inspect", help="Inspección estructural dry-run de un documento .docx")
    parser_inspect.add_argument("file", type=str, help="Ruta al archivo .docx a inspeccionar")

    args = parser.parse_args()

    if args.command == "video-report":
        run_video_report(args)
    elif args.command == "epis-ne":
        run_epis_ne_report(args)
    elif args.command == "inspect":
        run_inspect(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
