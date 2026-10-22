# typst_engine

Backend Typst del proyecto: un compilador (`compiler.py`) y plantillas (`templates/`).
El pipeline que lo usa es `src/reports/typst_lab/`.

## Compilador

```python
from src.typst_engine import compile_typst, typst_version
compile_typst("main.typ", "out/informe.pdf", root=".", inputs={"fecha": "2026-01-31"}, font_paths=["fonts"])
```

- Invoca `typst compile` con lista de argumentos (sin shell), `--root`, `--font-path`, `--input k=v`.
- `TypstNotFoundError` si no hay `typst` (o define `TYPST_BIN`); `TypstCompileError` con el mensaje de Typst si falla.
- Los warnings de una compilación correcta salen por `logging` (WARNING); `compile_typst_detailed` los devuelve.
- `typst_fonts()` lista las familias disponibles (Typst avisa por cada familia desconocida, así que el pipeline filtra).

## Plantilla `informe-laboratorio`

```typst
#import "template/lib.typ": *
#show: template.with(config: json("config.json"))   // o config: (course: "...", ...)
#section-box("SOLUCIÓN Y RESULTADOS")[
  #listing("code/suma.py", caption: [Suma.], label: "lst:suma")
  #figure-img("figures/a.png", caption: [Captura.], label: "fig:a")
  #evidence-figure("figures/b.png", [Salida.], cmd: "python3 code/suma.py")
  #result-table(("Prueba", "Esperado"), (("T1", "3"),), caption: [Pruebas.])
  #callout(kind: "tip", title: "Consejo")[Texto con #cmd("typst compile").]
]
```

Rutas de los helpers: relativas a la raíz del proyecto (con o sin `/` inicial). Los logos se
resuelven relativos a `lib.typ`. Fecha/hora: `--input fecha=AAAA-MM-DD`, `--input hora=HH:MM`
> `config.date`/`config.time` > hoy (hora: "—"). Si no se pasa `config`, se lee `--input config=<json>`.

Claves de config (ver `default-config` en `lib.typ`): `course title number instructor semester level year
members date time institution doc-title doc-format doc-approval doc-code logo-left logo-right
note-placeholder font mono-font accent toc list-of-figures feedback results-title bibliography
bib-style max-unbreakable-lines code-keep-lines`.

Los listados de hasta 36 líneas no se parten entre páginas; los largos se parten dejando al menos 6
líneas juntas en cada extremo. El encabezado verifica con `assert` que cabe en el margen superior (4 cm).

## project.toml (pipeline typst-lab)

```toml
[lab]
course = "Asignatura"        # obligatorios: course, title, number, instructor, members
title = "Título"
number = "05"
instructor = "Mg. Nombre"
semester = "B"
members = ["Apellidos, Nombres"]
# opcionales: year, date = "2026-01-31", time = "20:00", institution = ["línea 1", ...]

[build]
sections = ["content/ejercicios.typ", "content/cuestionario.typ", "content/conclusiones.typ"]
# opcionales: name, toc, list-of-figures, feedback, bibliography, font, mono-font,
#             copy = ["code"], font-paths = ["fonts"]
```

```python
from src.reports.typst_lab import run
run("output/mi-lab", scaffold_only=True)   # crea project.toml, content/, references.bib, figures/
run("output/mi-lab")                       # -> output/mi-lab/build/mi-lab.pdf
```

`build()` deja `build/_stage/` (main.typ, config.json, copia de plantilla y contenido) para depurar.
Se copian `content figures evidence code assets` y lo listado en `copy`. A las secciones sin
`#import "/template/lib.typ": *` se les antepone (los errores en ellas se desplazan +1 línea).
