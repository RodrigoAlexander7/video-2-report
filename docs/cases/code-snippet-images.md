# Funcion `code-image`: fragmentos de codigo como imagen de editor

**Input** (`inputs/<caso>/snippets.toml` + los archivos de codigo que referencia)

**Output** (`output/<caso>/evidence/`): `code/<id>.png` (2x, tamano exacto del contenido) y su registro en `manifest.json` con `source = "code"`, `render = "editor-frame"`, rangos, hash del fragmento y del archivo.

```bash
python main.py code-image inputs/IDSE/lab07                 # todos los fragmentos del caso
python main.py code-image inputs/IDSE/lab07/snippets.toml --out-dir /tmp/ev
python main.py evidence verify --out-dir output/IDSE/lab07/evidence
```

Es independiente de cualquier laboratorio: los reportes docx, Typst y las diapositivas la usan por el `id` del manifiesto. Formato de `snippets.toml`, reglas y uso en cada salida: `.agents/skills/code-snippet-images/SKILL.md`.

## Garantias

| Regla | Como se comprueba |
|---|---|
| El codigo es el real | rango de un archivo; el hash del fragmento se verifica en `evidence verify` |
| Imagen intacta | hash de la imagen en el manifiesto |
| Solo lo relevante | recorte de lineas vacias en los bordes; maximo 40 lineas |
| Legible en el documento | texto >= 8 pt a 6 in de ancho, o el comando falla con la causa |
| Sin recortes ni margenes sobrantes | tamano calculado antes de capturar; la captura se valida |
| Tema oscuro/claro legible | contraste >= 4.5:1 de los tokens (prueba automatica) |

## Codigo

`src/editor_engine/` (spec, extraccion, resaltado con Pygments, render HTML + captura Chrome), `src/core/chrome.py` (busqueda de Chrome compartida con `slides_engine`), `add_cell_code_figure` en `src/docx_engine/cell_helpers.py`. Pruebas: `python -m unittest tests.test_editor_engine`.
