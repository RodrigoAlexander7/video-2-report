# Video Report Generator (Word & OnlyOffice with Animated GIFs)

Automated pipeline to transcribe local technical and educational videos, extract key moments as visual evidence (annotated screenshots and high-quality GIF animations), and compile professional Microsoft Word (`.docx`) reports optimized for viewing in **OnlyOffice**.

---

## 🚀 Key Features

- **Local Offline Transcription:** Powered by `faster-whisper` (`small` model with `int8` quantization), highly optimized for multi-core CPUs without requiring dedicated GPUs.
- **Sharp Animated GIFs (HQ):** Extracts video segments in native panel resolution (960px width, 18 fps, 256 adaptive color palette, and `gifsicle` optimization).
- **`figure-enhancer` Skill:** Smart panel cropping (*smart crop*), translucent focus boxes with badges, and clean vector arrows pointing to exact parameters and buttons.
- **Strict Editorial Aesthetics:**
  - Academic typography: **Times New Roman** at **12 pt** (body) and **14/13 pt** (corporate navy headers `#1B365D`).
  - Source code: **JetBrains Mono** at **9.5 pt** inside styled containers with a side accent bar and subtle background fill.
  - Multi-level hierarchical indents (`0.25"` and `0.50"`) and internal cell padding across document tables.
- **OnlyOffice Compatibility:** Delivers smooth GIF playback within the document while strictly adhering to OpenXML schemas without file-corruption warnings.

---

## 📂 Repository Structure

```text
video-report/
├── .agents/
│   └── skills/
│       ├── figure-enhancer/             # Skill to crop, focus, and annotate screenshots
│       │   ├── scripts/
│       │   │   └── enhance_image.py     # Deterministic graphics functions (crop, arrow, focus_box)
│       │   └── SKILL.md                 # Documentation and usage guide for the skill
│       └── onlyoffice-docx-builder/     # OpenXML compatibility reference
├── inputs/
│   ├── input-template.docx              # Institutional template (.docx)
│   └── video/                           # Input MP4 video(s)
├── media/                               # Generated screenshots and GIFs (git-ignored)
├── config.py                            # Central settings (HQ toggle, fonts, metrics, paths)
├── media_extractor.py                   # Media extraction and figure enhancement module
├── generate_report.py                   # Report compilation and document formatting engine
├── transcribe_fast.py                   # Local faster-whisper transcription script
├── main.py                              # Unified CLI pipeline entry point
├── pyproject.toml                       # Dependencies managed with uv
└── README.md
```

---

## 🛠️ Installation & Prerequisites

1. **System Requirements:**
   - Linux with `ffmpeg` and `gifsicle` installed:
     ```bash
     sudo apt update && sudo apt install -y ffmpeg gifsicle
     ```
   - OnlyOffice Desktop Editors (via Flatpak):
     ```bash
     flatpak install flathub org.onlyoffice.desktopeditors
     ```

2. **Virtual Environment Setup (with `uv`):**
   ```bash
   uv sync
   ```

---

## 💻 Running the Pipeline

### 1. Transcribe Video (for a new input video):
```bash
uv run python transcribe_fast.py
```

### 2. Generate the Complete Report:
```bash
# High-quality mode (default):
uv run python main.py

# Lightweight mode (smaller, compressed GIFs):
uv run python main.py --low-quality
```

### 3. Open Report in OnlyOffice:
```bash
flatpak run org.onlyoffice.desktopeditors Reporte_Practica_02_Unity.docx &
```

---

## 📝 Prompt Template for Future Reports

When requesting a new report for a different video, you can provide this prompt to the assistant:

```markdown
Please generate a new laboratory report using the template at `inputs/input-template.docx` and the video at `inputs/video/<file>.mp4`:

1. **Topic Context:** [e.g., Robotics Workshop with ROS 2 / Shader Programming in Godot].
2. **Key Moments to Capture:**
   - Screenshot 1: Parameter configuration in [window/panel name].
   - GIF 1: Initial bug or unbalanced behavior demonstration.
   - GIF 2: Fixed behavior demonstration.
3. **Use of `figure-enhancer` Skill:**
   - Crop only the relevant panel (avoid full-screen captures).
   - Add focus boxes and red arrows pointing to [specific parameters/buttons].
4. **Document Formatting:** Times New Roman 12 pt, code in JetBrains Mono, hierarchical indents, and rigorous technical answers in the questionnaire.
```
