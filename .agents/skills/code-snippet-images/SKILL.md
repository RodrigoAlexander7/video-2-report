---
name: code-snippet-images
description: Genera imagenes de fragmentos de codigo con aspecto de editor (pestana, breadcrumb, numeros de linea reales, tema oscuro por defecto) desde un snippets.toml, para usarlas como evidencia en reportes de cualquier laboratorio (docx, Typst, diapositivas). Usar cuando un reporte muestre un fragmento de codigo, no el codigo completo.
---

# Code Snippet Images

Un `snippets.toml` en la carpeta del caso declara los fragmentos; `main.py code-image` genera un PNG por fragmento y lo registra en `output/<caso>/evidence/manifest.json` (`source = "code"`). Cualquier pipeline lo usa por su `id`: no hay codigo por laboratorio.

## Cuando usarlo

- **Fragmento** (una funcion, un bloque, unas lineas relevantes) -> imagen de editor, solo con el contenido que se explica.
- **Codigo completo** -> bloque de texto del documento (o apendice), no imagen.
- Resultados de ejecucion -> `terminal-evidence`, no esta skill.

## Flujo

```bash
# inputs/<caso>/snippets.toml
python main.py code-image inputs/<caso>        # o la ruta al snippets.toml
python main.py evidence verify --out-dir output/<caso>/evidence
```

```toml
[defaults]
theme = "dark"                   # "dark" (por defecto) o "light"

[[snippet]]
id    = "audio-start"            # letras, numeros, . _ -
file  = "source-code.cs"         # relativo al snippets.toml; el codigo sale del archivo real
lines = "12-30"                  # "12-30", 12, o ["12-18", "24-30"] (⋯ entre tramos)
focus = [20, 21]                 # lineas resaltadas (opcional)
path  = "Assets/Scripts/CatControl.cs"   # ruta que muestra el breadcrumb (opcional)
# title, language, dedent = true, whitespace = false, chrome = false, note
```

## Uso en cada salida

| Salida | Como |
|---|---|
| docx (celdas de plantilla) | `add_cell_code_figure(cell, "audio-start", evidence_dir, "Figura 5: ...", cfg)` en `src/docx_engine/cell_helpers.py`; fija el ancho para que el texto mida ~9,5 pt en todos los fragmentos |
| Typst (`typst-lab`, `typst-theory`) | `evidence-figure("evidence/code/audio-start.png", ...)` o `figure-img` |
| Diapositivas (`html-slides`) | layout `figure` con `evidence_id = "audio-start"`; usar `theme = "light"` (las diapositivas son siempre claras) |

## Reglas

1. **El codigo sale de un archivo real** (`file` + `lines`). Los numeros de linea de la imagen son los del archivo. Si hace falta un fragmento que no existe literalmente, `text = "..."` + `title`: queda como `origin = "inline"` y `evidence verify` avisa que no es verificable. No se usa para esconder cambios al codigo real.
2. **Solo lo relevante.** Maximo 40 lineas; el ancho debe dejar el texto en >= 8 pt a 6 in (~78 columnas). Si no cabe, el comando falla y dice que hacer: dividir, `dedent = true` o acortar lineas.
3. **Nunca editar el PNG.** `evidence verify` falla si la imagen o el fragmento del fuente cambian despues de generarla; se regenera con `code-image`.
4. Sin ligaduras (`!=` se ve `!=`), fuente JetBrains Mono incrustada, sin animaciones ni recursos externos.
5. Requiere Chrome/Chromium (`CHROME_BIN=/ruta` si no esta en el PATH).

## Temas

`dark` (por defecto, paleta Nord tomada de la captura de referencia) y `light` (Nord claro con contraste >= 4.5:1). Un tema nuevo es un CSS con las mismas variables en `src/editor_engine/themes/`; `tests/test_editor_engine.py` exige contraste de los tokens.
