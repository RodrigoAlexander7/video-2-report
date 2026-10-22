---
name: terminal-evidence
description: Genera figuras de evidencia a partir de comandos o sesiones reales (VDMJ), con log, hash y verificación contra el texto. Úsala cuando un informe muestre salidas de terminal o de un intérprete.
---

# Evidencia de terminal

La figura debe ser la salida real de un comando, no un dibujo. El motor está en `src/evidence_engine`.

## Comandos

```bash
# Comandos arbitrarios (sin shell: para tuberías usa `sh -c '...'`)
python main.py evidence capture NOMBRE "ls -la" "cat archivo.txt" --out-dir output/<caso>/evidence

# Sesión interactiva de VDMJ con un script de comandos ('--' = comentario)
python main.py evidence vdmj NOMBRE --specs A.vpp B.vpp --script prueba.script --out-dir output/<caso>/evidence

# Registrar una captura tomada a mano, o una versión anotada de otra
python main.py evidence add-image NOMBRE captura.png --out-dir ... --source manual --note "..."
python main.py evidence add-image NOMBRE anotada.png --out-dir ... --source annotated --base NOMBRE_BASE

# Verificar hashes, orígenes y afirmaciones del texto
python main.py evidence verify --out-dir ... --text content/*.typ
```

Cada captura produce `NOMBRE.log` (transcripción), `NOMBRE.png` (figura) y una entrada en `manifest.json` con comando, fecha y hashes.

## Directivas en el texto

Para que el texto no contradiga la evidencia, marca cada afirmación con un comentario (invisible en el documento):

```typst
// evidence: monedero-nominal expect: = 70
```

`verify` falla si el literal no aparece en el log real, si el log o la imagen se modificaron después de capturarse, o si una imagen anotada no tiene base registrada.

## Límites

- Los comandos interactivos no son compatibles con `capture`; usa un adaptador (como el de VDMJ) o una captura manual.
- Si un error deja líneas residuales en una sesión de VDMJ, separa los casos de fallo en sesiones propias.
