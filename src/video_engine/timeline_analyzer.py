#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Análisis de Línea de Tiempo y Detección de Hitos
Permite inspeccionar transcripciones JSON y extraer puntos clave para la generación de evidencias.
"""

import json
import os
from typing import List, Dict, Any, Optional

def load_transcription_segments(transcription_json_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(transcription_json_path):
        raise FileNotFoundError(f"No se encontró el archivo de transcripción: {transcription_json_path}")
    with open(transcription_json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_keywords_in_timeline(
    segments: List[Dict[str, Any]], 
    keywords: List[str]
) -> List[Dict[str, Any]]:
    """Busca segmentos que contengan palabras clave específicas y retorna los timestamps."""
    matches = []
    for seg in segments:
        text_lower = seg.get("text", "").lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                matches.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "keyword": kw,
                    "text": seg["text"]
                })
                break
    return matches

def generate_evidence_manifest(
    matches: List[Dict[str, Any]], 
    output_manifest_path: str
):
    """Guarda un manifiesto JSON con los momentos clave detectados para ser consumidos por el extractor."""
    os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)
    with open(output_manifest_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"✓ Manifiesto de evidencias generado en: {output_manifest_path}")
