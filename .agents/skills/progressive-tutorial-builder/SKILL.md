---
name: progressive-tutorial-builder
description: Transforma transcripciones de video técnico y código fuente en tutoriales escritos estructurados en etapas progresivas, con código incremental, evidencias causa-efecto y tono procedimental.
---

# Progressive Tutorial Builder Skill

Esta skill define el contrato pedagógico y metodológico para transformar videos de programación, ingeniería o talleres técnicos en **tutoriales escritos paso a paso**, listos para incrustarse en reportes de laboratorio (`.docx` para OnlyOffice o `.typ` para PDF).

---

## 🎯 Principios Fundamentales

1. **Estructura Didáctica por Etapas Cronológicas:**
   - La sección de desarrollo nunca debe redactarse como un resumen ejecutivo pasivo (*"Se realizó..."*), sino como una **guía procedimental orientada a la acción** (*"Paso 1: Configurar...", "Paso 2: Implementar..."*).
   - Cada etapa representa un hito funcional del video.

2. **Código Progresivo e Incremental:**
   - **Prohibido volcar el script completo al inicio.**
   - Cada etapa solo muestra el fragmento de código que se introduce en ese momento.
   - El código completo y consolidado se ubica exclusivamente al final de la última etapa de implementación como bloque de referencia.

3. **Colocación de Evidencias Causa $\rightarrow$ Efecto:**
   - Las figuras y GIFs deben insertarse **inmediatamente después** de la instrucción que los genera.
   - Si una etapa introduce una prueba intermedia con error (ej. torque indeseado), se inserta la evidencia del fallo, seguida de la explicación de la causa raíz, la instrucción correctiva y la evidencia del comportamiento corregido.

4. **Tono Instructivo e Imperativo:**
   - Uso de verbos de acción en modo imperativo o infinitivo profesional (*"Abra el Inspector...", "Declare las variables públicas...", "Verifique el comportamiento en modo Play"*).

---

## 📋 Estructura Estándar de una Etapa de Tutorial

Cada etapa del desarrollo debe seguir este patrón:

```markdown
### Etapa N: [Nombre del Hito Funcional]
1. **Objetivo de la etapa:** Breve descripción de lo que se logrará.
2. **Instrucciones paso a paso:** Acciones en el software o IDE.
3. **Fragmento de código incremental:** Solo las líneas añadidas o modificadas.
4. **Prueba y Verificación (Evidencia Visual):**
   - Captura anotada (con figure-enhancer) o GIF animado.
   - Descripción del resultado observado.
5. **Incidencias y Consideraciones Técnicas (si aplica):**
   - Problema encontrado $\rightarrow$ Causa física/lógica $\rightarrow$ Solución aplicada.
```

---

## 🧩 Integración con Otras Skills

- **`faster-whisper`:** Provee `transcription.txt` y `transcription_segments.json` con timestamps.
- **`progressive-tutorial-builder` (Esta skill):** Divide los timestamps en etapas didácticas y redacta el tutorial incremental.
- **`figure-enhancer`:** Genera los recortes de paneles, flechas y animaciones GIF para cada una de las etapas.
- **Generador de Reporte (`generate_report.py` / `typst`):** Compila el documento final.
