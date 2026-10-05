# Video Report Generator (Word & OnlyOffice con GIFs Animados)

Pipeline automatizado para transcribir videos técnicos/educativos locales, extraer momentos clave como evidencia visual (capturas anotadas y animaciones GIF de alta calidad) y compilar reportes profesionales en formato Microsoft Word (`.docx`), optimizados para ser visualizados en **OnlyOffice**.

---

## 🚀 Características Principales

- **Transcripción Local Offline:** Utiliza `faster-whisper` (modelo `small` con cuantización `int8`), altamente optimizado para procesadores multinúcleo en CPU sin requerir GPUs dedicadas.
- **GIFs Animados Nítidos (HQ):** Extrae bucles de video en resolución nativa de panel (960px, 18 fps, paleta adaptativa de 256 colores y optimización `gifsicle`).
- **Skill `figure-enhancer`:** Recorte inteligente de paneles (*smart crop*), cajas de enfoque semitransparentes (*focus box* con badge) y flechas vectoriales que señalan botones y parámetros exactos.
- **Estética Editorial Estricta:**
  - Tipografía académica: **Times New Roman** a **12 pt** (cuerpo) y **14/13 pt** (títulos corporativos azul marino `#1B365D`).
  - Código fuente: **JetBrains Mono** a **9.5 pt** dentro de cajas con borde lateral y fondo suave.
  - Sangrías jerárquicas multinivel (`0.25"` y `0.50"`) y márgenes internos en celdas de tabla.
- **Compatible con OnlyOffice:** Mantiene animaciones fluidas y preserva la validación de esquemas OpenXML sin advertencias de archivo dañado.

---

## 📂 Estructura del Repositorio

```text
video-report/
├── .agents/
│   └── skills/
│       ├── figure-enhancer/             # Skill para recortar y anotar capturas
│       │   ├── scripts/
│       │   │   └── enhance_image.py     # Funciones deterministas (crop, arrow, focus_box)
│       │   └── SKILL.md                 # Documentación y guía de uso de la skill
│       └── onlyoffice-docx-builder/     # Reglas y compatibilidad OpenXML
├── inputs/
│   ├── input-template.docx              # Plantilla institucional (.docx)
│   └── video/                           # Video(s) MP4 a procesar
├── media/                               # Capturas y GIFs generados (ignorado en git)
├── config.py                            # Configuración global (HQ, fuentes, tamaños, rutas)
├── media_extractor.py                   # Extractor y enriquecedor de figuras/GIFs
├── generate_report.py                   # Motor de llenado y estilización del documento
├── transcribe_fast.py                   # Script de transcripción local con faster-whisper
├── main.py                              # CLI principal del proyecto
├── pyproject.toml                       # Dependencias gestionadas con uv
└── README.md
```

---

## 🛠️ Instalación y Requisitos

1. **Requisitos del Sistema:**
   - Linux con `ffmpeg` y `gifsicle` instalados:
     ```bash
     sudo apt update && sudo apt install -y ffmpeg gifsicle
     ```
   - OnlyOffice Desktop Editors (Flatpak):
     ```bash
     flatpak install flathub org.onlyoffice.desktopeditors
     ```

2. **Entorno Virtual con `uv`:**
   ```bash
   uv sync
   ```

---

## 💻 Uso del Pipeline

### 1. Transcripción del Video (si es un nuevo video):
```bash
uv run python transcribe_fast.py
```

### 2. Generación Completa del Reporte:
```bash
# Modo alta calidad por defecto:
uv run python main.py

# Modo liviano (GIFs más pequeños y ligeros):
uv run python main.py --low-quality
```

### 3. Visualizar el Reporte en OnlyOffice:
```bash
flatpak run org.onlyoffice.desktopeditors Reporte_Practica_02_Unity.docx &
```

---

## 📝 Formato de Prompt para Nuevos Reportes

Para solicitar al asistente la creación de un nuevo reporte a partir de otro video, puedes usar esta plantilla:

```markdown
Hola, por favor genera un nuevo reporte para la plantilla en `inputs/input-template.docx` usando el video en `inputs/video/<archivo>.mp4`:

1. **Contexto del tema:** [Ej: Taller de Robótica con ROS 2 / Taller de Shaders en Godot].
2. **Momentos clave a capturar:**
   - Captura 1: Configuración de parámetros en [nombre de la ventana/panel].
   - GIF 1: Demostración de la falla o comportamiento inicial.
   - GIF 2: Demostración del comportamiento corregido.
3. **Uso de la skill `figure-enhancer`:**
   - Recortar únicamente el panel relevante para evitar pantallas completas.
   - Dibujar recuadros y flechas rojas sobre [parámetros específicos].
4. **Configuración de texto:** Times New Roman 12 pt, código en JetBrains Mono, sangría jerárquica y respuestas técnicas en el cuestionario.
```
