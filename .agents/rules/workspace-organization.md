# Workspace Organization & Output Conventions

All agents, subagents, and automated scripts operating within this repository MUST strictly follow these storage and output conventions to prevent project pollution:

## 1. Output Isolation Policy
- **NEVER** write generated PDFs, DOCX files, media crops, audio extractions, or temporary scripts into the root directory of the repository.
- **Every report job MUST have its own isolated folder** inside `output/<report-slug>/`:
  ```text
  output/<report-slug>/
  ├── figures/            # All final images, crops, and GIFs used by the report
  ├── <report-name>.typ   # (If Typst) Source file
  ├── template.typ        # (If Typst) Local layout template if customized
  ├── <report-name>.pdf   # (If Typst) Final compiled PDF
  └── <report-name>.docx  # (If Word) Final compiled DOCX
  ```

## 2. Temporary & Intermediate Artifacts
- Audio files (`*.wav`), temporary transcription JSONs/TXTs, and model download caches MUST be stored in:
  `output/.cache/` or `<appDataDir>/brain/<conversation-id>/scratch/`.
- Never create ad-hoc scratch scripts in the root directory (such as `test_*.py`, `transcribe_*.py`, `crop_*.py`). Execute Python one-liners directly or use `scratch/`.
- Do NOT create multiple duplicate folders like `media_manual`, `media_manual_clean`, etc. Clean and process images directly in `output/<report-slug>/figures/`.

## 3. Git Cleanliness
- The `.gitignore` is configured to ignore `output/`, `media/`, `*.wav`, `*.mp3`, `*.pdf`, and `inputs/video/*.mp4`.
- Under no circumstances should raw videos, heavy media files, or transient intermediate states be committed to Git.
