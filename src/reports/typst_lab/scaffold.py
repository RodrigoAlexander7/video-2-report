"""Esqueleto de un proyecto typst-lab (``project.toml`` + ``content/`` + bibliografia)."""

from __future__ import annotations

from pathlib import Path

PROJECT_TOML = """\
# Proyecto typst-lab: informe de laboratorio con la plantilla institucional.
# Se compila con:  .venv/bin/python -c "from src.reports.typst_lab import run; run('<esta carpeta>')"

[lab]
course = "Nombre de la asignatura"
title = "Título de la práctica"
number = "01"
instructor = "Grado. Nombres y apellidos del docente"
semester = "A"
members = [
  "Apellidos, Nombres",
]
# Opcionales:
# year = 2026                  # por defecto, el año de la fecha de presentación
# date = "2026-01-31"          # por defecto, la fecha de hoy (o --input fecha=AAAA-MM-DD)
# time = "20:00"               # por defecto "—" (o --input hora=HH:MM)
# institution = ["UNIVERSIDAD ...", "FACULTAD ...", "ESCUELA PROFESIONAL ..."]

[build]
# Orden en que se incluyen las secciones (rutas relativas a esta carpeta).
sections = [
  "content/ejercicios.typ",
  "content/cuestionario.typ",
  "content/conclusiones.typ",
]
# Opcionales:
# name = "lab01"               # nombre del PDF (por defecto, el de la carpeta)
# toc = false                  # tabla de contenidos
# list-of-figures = false      # lista de figuras
# feedback = true              # caja "Retroalimentación general"
# bibliography = "references.bib"
# font = "Lato"                # familia preferida (con respaldo automático)
# copy = ["code"]              # carpetas/archivos extra que las secciones leen (listing, imágenes)
"""

IMPORT_LINE = '#import "/template/lib.typ": *\n'

EJERCICIOS_TYP = IMPORT_LINE + """\

= Solución de Ejercicios y Problemas

// TODO(autor): reemplazar por el enunciado real de cada ejercicio y su solución.
== Ejercicio 1

Resumen del enunciado propuesto en la guía @guia-laboratorio y de la estrategia seguida para resolverlo.

// Helpers disponibles (las rutas son relativas a la raíz del proyecto):
//
// Código leído desde un archivo (se cita con @lst:ejemplo):
// #listing("code/ejemplo.py", lang: "python", caption: [Descripción del código.], label: "lst:ejemplo")
//
// Imagen simple y figura de evidencia (imagen + comando que la generó):
// #figure-img("figures/captura-01.png", caption: [Descripción de la captura.], label: "fig:captura-01")
// #evidence-figure("figures/captura-02.png", [Resultado de la ejecución.], cmd: "python3 code/ejemplo.py", label: "fig:captura-02")
//
// Tabla de resultados con filas alternadas:
// #result-table(
//   ("Prueba", "Entrada", "Esperado", "Obtenido"),
//   (("T1", "...", "...", "..."),),
//   caption: [Resultados de las pruebas.], label: "tab:pruebas",
// )
"""

CUESTIONARIO_TYP = IMPORT_LINE + """\

= Solución del Cuestionario

// Una pregunta por elemento de la lista numerada; la respuesta va indentada debajo.
+ *Enunciado de la pregunta 1.*

  Respuesta fundamentada en lo trabajado en el laboratorio, citando la bibliografía cuando corresponda @guia-laboratorio.

+ *Enunciado de la pregunta 2.*

  Respuesta.
"""

CONCLUSIONES_TYP = IMPORT_LINE + """\

= Conclusiones

// Cada conclusión debe poder rastrearse a un resultado o evidencia del informe.
1. Conclusión sobre el objetivo principal de la práctica y cómo se verificó con los resultados obtenidos.
2. Conclusión sobre una dificultad encontrada y cómo se resolvió.
"""

REFERENCES_BIB = """\
@misc{guia-laboratorio,
  title        = {Guía de práctica de laboratorio},
  author       = {{Escuela Profesional de Ingeniería de Sistemas}},
  year         = {2026},
  howpublished = {Documento del curso},
  note         = {Reemplazar por la referencia real de la guía y agregar las demás fuentes}
}
"""

_FILES = {
    "project.toml": PROJECT_TOML,
    "content/ejercicios.typ": EJERCICIOS_TYP,
    "content/cuestionario.typ": CUESTIONARIO_TYP,
    "content/conclusiones.typ": CONCLUSIONES_TYP,
    "references.bib": REFERENCES_BIB,
    "figures/.gitkeep": "",
}


def scaffold(case_dir) -> Path:
    """Crea el esqueleto en ``case_dir`` sin sobrescribir archivos existentes.

    Devuelve la ruta de ``project.toml``.
    """
    root = Path(case_dir)
    root.mkdir(parents=True, exist_ok=True)
    for rel, text in _FILES.items():
        target = root / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root / "project.toml"
