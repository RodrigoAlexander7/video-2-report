# Caso `typst-lab`: informe de laboratorio en PDF con evidencia real

**Input** (`inputs/<caso>/`)

```text
project.toml        # [lab] datos de la carátula, [build] secciones, [evidence] sesiones
content/*.typ       # secciones del informe (ya traen `#import "/template/lib.typ": *`)
content/references.bib
specs/ scripts/     # material que las sesiones de evidencia ejecutan (p. ej. VDM++)
```

**Output** (`output/<caso>/`): `evidence/` (logs, figuras, `manifest.json`) y `build/<caso>.pdf` (la carpeta `build/_stage` queda para depurar).

```bash
python main.py typst-lab new inputs/mi-lab     # esqueleto sin relleno
python main.py run inputs/mi-lab               # captura evidencia, verifica y compila
```

## project.toml

```toml
pipeline = "typst-lab"

[lab]                                  # obligatorios: course, title, number, instructor, members
course = "..."; title = "..."; number = "06"; instructor = "..."
semester = "2026B"                     # año lectivo: se muestra "2026 - B" (también vale "B" con year/date)
level = "Octavo VIII"                  # opcional: "Nro. semestre" (por defecto "—")
members = ["Apellidos, Nombres"]

[build]
sections = ["content/ejercicios.typ", "content/cuestionario.typ"]
bibliography = "content/references.bib"
copy = ["specs"]                       # carpetas que los helpers leen (listing, imágenes)
# toc = true, list-of-figures = true, feedback = true, name = "..."

[evidence]                             # opcional
tool = "vdmj"                          # dialect = "vdmpp", release = "classic"
[[evidence.sessions]]
name = "ej1"
specs = ["specs/Mapas.vpp"]
script = "scripts/ej1.script"          # un comando del intérprete por línea; '--' comenta
```

## Helpers de la plantilla (`src/typst_engine/templates/informe-laboratorio/lib.typ`)

`listing(path, lang:, caption:, label:)`, `evidence-figure(path, caption, cmd:, label:)`, `figure-img`, `result-table(headers, rows, caption:)`, `uml-diagram(..clases, relations:, caption:)`, `callout` (sobrio: filete gris sin colores; `kind` no cambia el aspecto), `cmd`, `section-box`. Las rutas son relativas a la raíz del proyecto.

## Evidencia y verificación

Cada sesión se ejecuta de verdad (VDMJ, desde la carpeta del proyecto) y su figura sale del log. Antes de compilar se verifica el manifiesto y las directivas del texto; si una afirmación no aparece en el log real, el build se detiene:

```typst
// evidence: ej1 expect: = {|->}
```

Ver `.agents/skills/terminal-evidence/SKILL.md`. Notas (`// NOTE(...)`, `// TODO(...)`) no aparecen en el PDF.

## Dependencias
Typst (`typst`), Java y VDMJ (extensión VDM de VS Code o `VDMJ_JAR`), `pdftoppm` solo para revisar el PDF.
