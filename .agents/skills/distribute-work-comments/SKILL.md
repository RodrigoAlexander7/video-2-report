---
name: distribute-work-comments
description: Cómo dejar tareas, asignaciones y notas en comentarios del código fuente (Typst, Python, Bash) para que nunca aparezcan en el documento compilado.
---

# Reparto de trabajo mediante comentarios

Las tareas, asignaciones y recordatorios van como comentarios en los archivos fuente, nunca como texto visible del documento.

Convenciones (en Typst `//`; en Python/Bash `#`):

- `// TODO(usuario): descripción de la tarea`
- `// NOTE(Apellido, Nombre): contexto o responsable de la sección`
- `// WARNING: restricción crítica`

Nunca escribas en el documento frases como "Ejercicio 1 (asignado a: X)".

Divide el documento en archivos que se incluyen desde uno principal (`#include`), de modo que cada integrante edite el suyo sin conflictos.

El generador puede listar estos comentarios sin imprimirlos en el PDF.
