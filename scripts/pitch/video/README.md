# Demo video pipeline (30 s, 1080p30)

Everything runs locally; dependencies live in throwaway venvs / a local npm folder, never globally.

| Step | Script | What it does |
|---|---|---|
| 1. Record | `record.mjs` (playwright-core + system Chrome, ffmpeg `x11grab`) | Drives the real UI fullscreen (API on :8000, `frontend/` on :5180) and records 6 shots: landing globe → map, El Niño outlook, drawing a parcel, digital twin (chart + 3D blocks), the answer (177 → 84), NASA data sources. |
| 2. Voice | `cb_render.py` (Chatterbox, MIT) in `.venv-cb` | 2 takes per line of `docs/pitch/voiceover_en.txt`, male voice cloned from a Kokoro-82M (Apache-2.0) reference clip. Needs `setuptools<81` for the `perth` watermarker. On a 4 GB GPU set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. |
| 3. Check | `asr_check.py` (faster-whisper small.en) | Transcribes every take and scores it against the script; reject takes that repeat or misread numbers. |
| 4. Build | `assemble.py` (+ `music.py`, `render_overlay.mjs`, `overlay.html`) | Voice-driven timeline → overlay frames (HTML/CSS, app fonts and colours, Vietnamese subtitles) → retimed shots with Ken Burns + crossfades → synthesized royalty-free music ducked under the voice → loudnorm −14 LUFS → H.264/AAC MP4. |

`overlay.html` expects the Be Vietnam Pro woff2 files in `fonts/` next to it (copy from `frontend/node_modules/@fontsource/be-vietnam-pro/files/`, weights 400/600/800, latin + vietnamese).

Every number on screen comes from `contracts/fixtures/plan_soctrang.json` (see `docs/pitch/VIDEO_SCRIPT.md`). If the engine output changes, update the overlay text and the voice-over before rebuilding.
