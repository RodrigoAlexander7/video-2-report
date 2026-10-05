#!/usr/bin/env python3
"""
Pipeline principal de generación de reportes automáticos a partir de video.
"""

import argparse
from config import ReportConfig
from media_extractor import generate_and_enhance_figures
from generate_report import build_report

def main():
    parser = argparse.ArgumentParser(description="Generador automatizado de reportes técnicos con GIFs para OnlyOffice")
    parser.add_argument("--video", type=str, help="Ruta al archivo de video de entrada")
    parser.add_argument("--template", type=str, help="Ruta a la plantilla .docx")
    parser.add_argument("--output", type=str, help="Ruta del reporte .docx resultante")
    parser.add_argument("--low-quality", action="store_true", help="Generar GIFs en calidad estándar (menor peso)")
    parser.add_argument("--skip-media", action="store_true", help="Saltar extracción de media si ya existen los archivos")
    args = parser.parse_args()

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
    print("✓ Pipeline completado con éxito.")

if __name__ == "__main__":
    main()
