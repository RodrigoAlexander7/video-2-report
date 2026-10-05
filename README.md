# Video Report Generator (Word & OnlyOffice with Animated GIFs)

Automated pipeline to transcribe local technical and educational videos, extract key moments as visual evidence (annotated screenshots and high-quality GIF animations), and compile professional Microsoft Word (`.docx`) reports optimized for viewing in **OnlyOffice**.

---

## 🚀 Key Features

- **Local Offline Transcription:** Powered by `faster-whisper` (`small` model with `int8` quantization), highly optimized for multi-core CPUs without requiring dedicated GPUs.
- **`progressive-tutorial-builder` Skill:** Transcribes raw video demonstrations into structured, step-by-step written tutorials featuring incremental code snippets, cause-and-effect visual proof, and actionable instructional tone.
- **`figure-enhancer` Skill:** Smart panel cropping (*smart crop*), translucent focus boxes with badges, and clean vector arrows pointing to exact parameters and buttons.
- **Sharp Animated GIFs (HQ):** Extracts video segments in native panel resolution (960px width, 18 fps, 256 adaptive color palette, and `gifsicle` optimization).
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
│       ├── progressive-tutorial-builder/ # Skill for step-by-step tutorial structuring
│       │   └── SKILL.md                 # Rules for incremental code & cause-effect evidence
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

## 🤖 How Future Agents Operate (100% Replicable)

The next time you want to process a video report, simply place:
1. The new `.docx` template in `inputs/input-template.docx`.
2. The new video in `inputs/video/<video_name>.mp4`.

And provide this simple prompt to the agent:

```markdown
Generate the lab report following the repository workflow:
- Video: inputs/video/<video_name>.mp4
- Template: inputs/input-template.docx
- Use the `progressive-tutorial-builder` skill to structure the development section into progressive step-by-step stages with incremental code.
- Use the `figure-enhancer` skill to crop panels and highlight key settings with arrows and focus boxes.
- Output: Word document formatted for OnlyOffice with HQ GIFs.
```

The agent will automatically:
1. Run `transcribe_fast.py` to extract the speech-to-text with timestamps.
2. Segment the video into logical tutorial milestones.
3. Call `figure-enhancer` to extract cropped panels and high-quality GIFs.
4. Compile the styled `.docx` report with Times New Roman 12 pt, JetBrains Mono code blocks, and valid OpenXML schemas.
