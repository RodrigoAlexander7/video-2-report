---
name: lab-report-writing
description: Reglas de redacción y flujo de trabajo para informes de laboratorio (Typst o Word) claros, directos y sin relleno. Úsala al escribir o revisar el contenido de un informe.
---

# Redacción de informes de laboratorio

## Reglas

- Sigue la estructura que dé el usuario o la guía del laboratorio. Si la guía tiene partes y pasos, el informe tiene los mismos encabezados. Máximo tres niveles de encabezado.
- No numeres encabezados a mano (`== 2.1 Título`): la plantilla numera sola.
- Referencia figuras, tablas y listados con el sistema nativo (`@fig:nombre`), nunca con números escritos a mano.
- Prefiere párrafos concisos a listas. Usa una lista solo para elementos paralelos reales, y evita el exceso de negritas, paréntesis y adjetivos.
- Todo resultado que el texto afirme debe salir de una ejecución real (ver `terminal-evidence`). Si una herramienta se comporta distinto a la guía, dilo en el informe en lugar de ajustar el resultado.
- No presentes como captura de un programa algo que no lo es. Las figuras de resultados se generan con `main.py evidence`; Pillow solo anota capturas reales.
- Texto directo y sin adornos: nada de superlativos ni adjetivos de valor (clave, crítico, fundamental, riguroso, robusto, sinergia, paradigma…), ni apreciaciones personales, ni etiquetas en Mayúsculas Iniciales con dos puntos («Advertencia Técnica Clave:»). Se dice el hecho. Para laboratorios de Unity, `python main.py unity-lab check` lo verifica.
- Estilo sobrio, sin recuadros de color: las notas y advertencias van con `callout` (filete vertical gris, texto oscuro). No uses fondos ni bordes rojos, amarillos, verdes o azules ni para alertas críticas; `kind` no cambia el aspecto. En `.docx`, los helpers de `docx_engine` ya dan el mismo estilo (encabezados y viñetas en el color del texto, código en gris con borde fino, pie de figura con la etiqueta en negrita).
- La sección «Información básica» de `typst-lab` sigue el formato institucional: asignatura, título, número de práctica, año lectivo (`semester = "B"` se muestra «2026 - B»), `level = "Octavo VIII"` como nro. de semestre, fecha `DD/MM/AAAA`, hora, integrantes, nota (0-20) y docente.
- Divide el informe en archivos incluidos desde uno principal para evitar conflictos de edición.

## Ejemplo de estilo

Malo, con listas innecesarias y relleno:

> 1. **Instalación del entorno:**
>    * Se desplegó una herramienta de gestión (se utilizó **Redmine** en Docker).
>    * Se definieron los roles: *Solicitante*, *Comité*, *Desarrollador* y *QA*.

Bueno, en prosa directa:

> Se desplegó Redmine en Docker y se definieron cuatro roles: solicitante, comité de cambios, desarrollador y QA.

## Flujo

1. Escribe un borrador sin compilar y comprueba que cubre todo lo que pide la guía y sus criterios de evaluación.
2. Revisa en este orden: sintaxis, estilo (reglas de arriba) y coherencia entre texto, figuras y evidencias.
3. Ejecuta `main.py evidence verify` y compila.
