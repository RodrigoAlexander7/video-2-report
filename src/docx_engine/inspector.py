#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Inspección y Dry-Run para Documentos Generados (.docx / .typ)
Permite verificar la integridad estructural, tablas, párrafos y figuras sin recompilar.
"""

import os
import sys
import docx

def inspect_docx(file_path: str):
    if not os.path.exists(file_path):
        print(f"❌ Error: El archivo no existe en {file_path}")
        return False

    print("=" * 80)
    print(f"INSPECCIÓN ESTRUCTURAL DE DOCUMENTO (DRY-RUN): {os.path.basename(file_path)}")
    print(f"Ruta completa: {file_path}")
    print(f"Tamaño: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
    print("=" * 80)

    doc = docx.Document(file_path)
    total_p = len(doc.paragraphs)
    total_t = len(doc.tables)

    # Contar dibujos / imágenes en el XML
    drawing_count = doc._part.blob.count(b'<w:drawing>')

    print(f"\n[Métricas Generales]")
    print(f"  - Total de Párrafos: {total_p}")
    print(f"  - Total de Tablas:   {total_t}")
    print(f"  - Figuras / GIFs:    {drawing_count}")

    # Extraer encabezados principales
    print(f"\n[Estructura de Secciones Detectadas]")
    headings_found = []
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if txt and any(txt.startswith(f"{n}. ") for n in range(1, 25)) and not txt.endswith("..."):
            headings_found.append((i, txt))

    if headings_found:
        for idx, (p_num, h_text) in enumerate(headings_found[:20]):
            print(f"  {idx+1:02d}. [P{p_num:03d}] {h_text[:75]}")
        if len(headings_found) > 20:
            print(f"  ... y {len(headings_found) - 20} subsecciones adicionales.")
    else:
        # Fallback a títulos de tabla o primeros párrafos
        print("  (Estructura tabular / compacta)")

    print("\n✓ Inspección finalizada sin anomalías de lectura OpenXML.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_docx(sys.argv[1])
    else:
        print("Uso: python inspector.py <ruta_al_archivo.docx>")
