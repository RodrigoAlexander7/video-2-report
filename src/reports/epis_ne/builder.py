#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo Orquestador de Generación del Informe de Negocios Electrónicos (Lab 05)
Distribuidora Inca S.R.L. - Solución SCM con Odoo Community Edition
Universidad Nacional de San Agustín de Arequipa (UNSA) - EPIS
"""

import os
import sys
import docx

# Permitir importaciones relativas dentro del paquete src
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from reports.epis_ne.sections_part1 import (
    build_portada_and_indice,
    build_section_1_planificacion,
    build_section_2_organizacion,
    build_section_3_problema,
    build_section_4_marco_teorico
)

from reports.epis_ne.sections_part2 import (
    build_section_5_comparativas,
    build_section_6_trabajo_equipo,
    build_section_7_alternativas,
    build_section_8_seleccion,
    build_section_9_presentacion,
    build_section_10_prototipo,
    build_section_11_lecciones,
    build_section_12_conclusiones,
    build_section_13_referencias,
    build_section_14_anexos,
    build_section_15_informe,
    build_section_16_autoevaluacion
)

def generate_epis_ne_report(
    template_path: str = "inputs/NE/Lab05/GenericTemplate.docx",
    output_path: str = "output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx"
):
    print("="*80)
    print("GENERADOR DEL INFORME OFICIAL EPIS - NEGOCIOS ELECTRÓNICOS (LAB 05)")
    print(f"Plantilla base: {template_path}")
    print(f"Destino final:  {output_path}")
    print("="*80)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"No se encontró la plantilla institucional en: {template_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = docx.Document(template_path)

    print("\n[1/16] Construyendo Portada e Índice General...")
    build_portada_and_indice(doc)

    print("[2/16] Sección 1: Planificar el tratamiento del problema...")
    build_section_1_planificacion(doc)

    print("[3/16] Sección 2: Organizar el trabajo del equipo...")
    build_section_2_organizacion(doc)

    print("[4/16] Sección 3: Problema (Árbol de causas y efectos)...")
    build_section_3_problema(doc)

    print("[5/16] Sección 4: Marco Teórico (10 conceptos, 4 tesis, 4 artículos)...")
    build_section_4_marco_teorico(doc)

    print("[6/16] Sección 5: Comparativa de la selección de aspectos...")
    build_section_5_comparativas(doc)

    print("[7/16] Sección 6: Trabajar en grupo colaborativamente...")
    build_section_6_trabajo_equipo(doc)

    print("[8/16] Sección 7: Generación de alternativas de solución...")
    build_section_7_alternativas(doc)

    print("[9/16] Sección 8: Selección de la mejor alternativa...")
    build_section_8_seleccion(doc)

    print("[10/16] Sección 9: Presentación de la Solución...")
    build_section_9_presentacion(doc)

    print("[11/16] Sección 10: Prototipo y análisis situacional (Odoo SCM)...")
    build_section_10_prototipo(doc)

    print("[12/16] Sección 11: Lecciones Aprendidas (Estructura dual)...")
    build_section_11_lecciones(doc)

    print("[13/16] Sección 12: Conclusiones vinculadas a objetivos...")
    build_section_12_conclusiones(doc)

    print("[14/16] Sección 13: Referencias Bibliográficas...")
    build_section_13_referencias(doc)

    print("[15/16] Sección 14: Anexos (Láminas, Infografía, Datos)...")
    build_section_14_anexos(doc)

    print("[16/16] Secciones 15 y 16: Informe y Autoevaluación del Equipo...")
    build_section_15_informe(doc)
    build_section_16_autoevaluacion(doc)

    doc.save(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print("\n" + "="*80)
    print(f"✓ INFORME GENERADO CON ÉXITO: {output_path} ({size_mb:.2f} MB)")
    print("="*80)
    return output_path

if __name__ == "__main__":
    generate_epis_ne_report()
