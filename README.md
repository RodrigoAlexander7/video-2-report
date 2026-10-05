# Automated Report & Video Tutorial Generator

Modular pipeline for generating technical reports, step-by-step video tutorials with animated GIFs (OnlyOffice / Typst), and formal institutional academic reports (EPIS - UNSA).

---

## 🚀 Key Features

- **Local Offline Video Processing:** Speech-to-text with `faster-whisper` (`int8` multi-core CPU inference) and deterministic frame extraction via `ffmpeg`.
- **`progressive-tutorial-builder` Skill:** Transforms video demonstrations into structured, procedural tutorials with incremental code snippets and cause-and-effect evidence.
- **`figure-enhancer` Skill:** Smart panel cropping, focus boxes with badges, and clean vector arrows for technical screenshots.
- **`epis-ne-report-builder` Skill:** Exhaustive institutional reports for Negocios Electrónicos (EPIS - UNSA), adhering to university rubrics, budgeting limits, 16 mandatory chapters, and formal screenshot placeholders for unreleased prototypes.
- **Strict Visual & OpenXML Standards:** Clean typography (Times New Roman / Calibri, JetBrains Mono for code), sober palette (no loud colors), and full compatibility with Word, OnlyOffice, and Typst.

---

## 📂 Repository Structure

```text
video-report/
├── .agents/
│   ├── rules/
│   │   └── workspace-organization.md     # Mandatory isolation rules (no root pollution)
│   └── skills/
│       ├── epis-ne-report-builder/       # Skill for EPIS Negocios Electrónicos reports
│       ├── figure-enhancer/              # Skill for screenshot crops, arrows & focus boxes
│       ├── progressive-tutorial-builder/ # Skill for step-by-step incremental tutorials
│       └── onlyoffice-docx-builder/      # OpenXML compatibility guide
├── inputs/
│   ├── IDSE-Lab05/                       # Unity physics laboratory inputs
│   └── NE/Lab05/                         # Negocios Electrónicos Lab 05 (GenericTemplate.docx & StudyCase.md)
├── output/                               # ALL generated artifacts are isolated here
│   ├── .cache/                           # Temporary audio & raw transcription dumps
│   ├── autocad-addin-manual/             # AutoCAD Addin User Manual (Typst & PDF)
│   ├── unity-practice-02/                # Unity lab report (.docx with HQ GIFs)
│   └── NE/Lab05/                         # EPIS Negocios Electrónicos Lab 05 Report (.docx)
├── src/                                  # REUSABLE CORE ENGINES
│   ├── docx_engine/                      # OpenXML formatting helpers, clean tables, callouts
│   │   ├── helpers.py
│   │   └── __init__.py
│   ├── video_engine/                     # Whisper transcription & media extraction
│   │   ├── media_extractor.py
│   │   └── transcribe_fast.py
│   └── reports/                          # Domain-specific report builders
│       ├── epis_ne/                      # EPIS NE Lab 05 generator
│       │   ├── builder.py
│       │   ├── sections_part1.py
│       │   └── sections_part2.py
│       └── unity_practice/               # Unity Lab 02 generator
│           └── generate_report.py
├── config.py                             # Central configuration
├── main.py                               # Unified modular CLI entry point
├── pyproject.toml                        # uv dependency specification
└── README.md
```

---

## 🛠️ Installation & Setup

1. **System Requirements:**
   - Linux with `ffmpeg` and `gifsicle`:
     ```bash
     sudo apt update && sudo apt install -y ffmpeg gifsicle
     ```
   - OnlyOffice Desktop Editors (Flatpak):
     ```bash
     flatpak install flathub org.onlyoffice.desktopeditors
     ```

2. **Python Environment (with `uv`):**
   ```bash
   uv sync
   ```

---

## 💻 CLI Usage

The repository provides a single, unified CLI entry point via `main.py`:

### 1. Generate Academic Report (EPIS Negocios Electrónicos):
```bash
uv run python main.py epis-ne \
  --template inputs/NE/Lab05/GenericTemplate.docx \
  --output output/NE/Lab05/Informe_Lab05_Distribuidora_Inca_SCM.docx
```

### 2. Generate Video Report with GIFs (OnlyOffice):
```bash
uv run python main.py video-report \
  --video "inputs/video/2026-10-04 13-52-34.mp4" \
  --template inputs/IDSE-Lab05/input-template.docx \
  --output output/unity-practice-02/Reporte_Practica_02_Unity.docx
```

---

## 🤖 Instructions for AI Agents & Subagents

When instructed to generate or modify reports in this repository:
1. **Never write scripts or output files in the root folder.**
2. Place all deliverables inside `output/<slug>/`.
3. Reuse `src/docx_engine/helpers.py` for Word styling and `src/video_engine/` for video extraction.
4. Keep the styling academic, sober, and free of unnecessary bright colors.
