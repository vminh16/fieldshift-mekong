"""Build the 30 s demo: voice-driven timeline -> overlay frames -> edit -> mix -> MP4.

Usage: python assemble.py <video_dir> <voice_dir> <voice_prefix> [--overlay-only|--no-overlay-render]
Voice files: <voice_dir>/<voice_prefix>_<scene>.wav (one per non-silent scene).
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

V = Path(sys.argv[1])
VOICE_DIR = Path(sys.argv[2])
PREFIX = sys.argv[3]
FLAGS = set(sys.argv[4:])
LINES = V.parent / "pr3/docs/pitch/voiceover_en.txt"
SR = 48000
MAX_DUR = 30.0
XF = 0.3  # crossfade between scenes

# Vietnamese subtitles per scene (split proportionally to text length within the line).
SUBS_VI = {
    "landing": ["Một nửa lúa gạo Việt Nam trồng ở đây.", "Năm nay, mặn đến sớm."],
    "outlook": ["El Niño mạnh.", "Những năm như vậy, NASA chỉ ghi nhận\n30% lượng mưa mùa khô bình thường."],
    "draw": ["Vẽ thửa ruộng của bạn."],
    "twin": ["FieldShift thử mọi chuỗi luân canh,\ntheo từng ngày, qua 12 kịch bản."],
    "answer": ["Gieo sớm, nghỉ vụ mặn nhất:", "số ngày cây phơi mặn giảm từ 177 xuống 84."],
    "sources": ["Mỗi con số đều có nguồn."],
    "end": ["FieldShift. Lên kế hoạch trước khi mặn về."],
}
# Source clip, in/out seconds, Ken Burns zoom target (x, y in 0..1) and end zoom.
EDL = {
    "landing": ("landing", 1.6, 9.4, (0.62, 0.55), 1.04),
    "outlook": ("outlook", 0.4, 6.6, (0.45, 0.40), 1.07),
    "draw": ("draw", 0.45, 6.3, (0.55, 0.32), 1.05),
    "twin": ("twin", 1.0, 13.5, (0.50, 0.62), 1.05),
    "answer": ("answer", 0.6, 7.0, (0.40, 0.45), 1.06),
    "sources": ("sources", 0.4, 6.0, (0.45, 0.45), 1.04),
    "end": ("sources", 5.0, 6.0, (0.5, 0.5), 1.0),
}
DRAW_SILENT_S = 2.15


def run(cmd):
    subprocess.run(cmd, check=True)


def voice_timeline():
    rows = []
    for raw in LINES.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.startswith("#"):
            scene, pause, text = raw.split("|", 2)
            rows.append((scene, float(pause), text.strip()))
    t, scenes, voice = 0.0, {}, []
    for scene, pause, text in rows:
        scenes[scene] = t
        if text:
            audio, sr = sf.read(VOICE_DIR / f"{PREFIX}_{scene}.wav", dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            if sr != SR:
                x = np.arange(int(len(audio) * SR / sr)) * sr / SR
                audio = np.interp(x, np.arange(len(audio)), audio).astype("float32")
            voice.append((t + pause, audio))
            t += pause + len(audio) / SR + 0.15
        else:
            t += DRAW_SILENT_S
    total = min(MAX_DUR, t + 0.9)
    return rows, scenes, voice, total


def subs(rows, scenes, voice, total):
    order = [r[0] for r in rows]
    vstart = {}
    vi = iter(voice)
    for scene, _, text in rows:
        vstart[scene] = next(vi) if text else None
    cues = []
    for i, scene in enumerate(order):
        nxt = scenes[order[i + 1]] if i + 1 < len(order) else total
        if vstart[scene]:
            a = vstart[scene][0]
            b = a + len(vstart[scene][1]) / SR + 0.25
        else:
            a, b = scenes[scene] + 0.1, nxt - 0.1
        b = min(b, nxt - 0.05)
        parts = SUBS_VI[scene]
        w = np.array([len(p) for p in parts], float)
        edges = a + np.concatenate([[0], np.cumsum(w / w.sum())]) * (b - a)
        cues += [[round(edges[k], 3), round(edges[k + 1], 3), p] for k, p in enumerate(parts)]
    return cues


def mix_audio(voice, total, scenes, out):
    n = int(total * SR)
    vtrack = np.zeros(n, "float32")
    for start, audio in voice:
        a = int(start * SR)
        b = min(n, a + len(audio))
        vtrack[a:b] += audio[: b - a]
    vtrack /= np.max(np.abs(vtrack)) + 1e-9
    sf.write(V / "audio/voice_track.wav", vtrack * 0.9, SR)
    tl = {"duration": total, "scenes": scenes}
    json.dump(tl, open(V / "audio/music_tl.json", "w"))
    run([str(Path(sys.executable)), "-I", str(Path(__file__).parent / "music.py"), str(V / "audio/music_tl.json"), str(V / "audio/music.wav")])
    # Voice: light high-pass + presence + compression; music ducked under the voice.
    run(["ffmpeg", "-v", "error", "-y", "-i", str(V / "audio/voice_track.wav"), "-i", str(V / "audio/music.wav"),
         "-filter_complex",
         "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,highpass=f=80,equalizer=f=3000:t=q:w=1.2:g=2.5,"
         "acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,asplit=2[vo][sc];"
         "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=0.55[mu];[mu][sc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[duck];"
         "[vo][duck]amix=inputs=2:duration=longest,volume=2,loudnorm=I=-14:TP=-1.5:LRA=9",
         "-ar", str(SR), "-c:a", "pcm_s16le", str(out)])


def edit(scenes, total, overlay_dir, audio, out):
    order = list(EDL)
    starts = [scenes[s] for s in order]
    durs = [(starts[i + 1] if i + 1 < len(order) else total) - starts[i] for i in range(len(order))]
    inputs, chains = [], []
    for i, scene in enumerate(order):
        clip, a, b, (fx, fy), z1 = EDL[scene]
        d = durs[i] + (XF if i + 1 < len(order) else 0)
        frames = int(round(d * 30))
        speed = (b - a) / d
        inputs += ["-ss", str(a), "-t", str(b - a), "-i", str(V / f"clips/{clip}.mkv")]
        # retime -> upscale (smooth sub-pixel zoom) -> Ken Burns towards (fx, fy)
        zx = f"(iw-iw/zoom)*{fx}"
        zy = f"(ih-ih/zoom)*{fy}"
        chain = (f"[{i}:v]setpts=(PTS-STARTPTS)/{speed:.5f},fps=30,trim=end_frame={frames},"
                 f"scale=3840:2160:flags=lanczos,"
                 f"zoompan=z='1+({z1}-1)*on/{frames}':x='{zx}':y='{zy}':d=1:s=1920x1080:fps=30,"
                 f"setsar=1,format=yuv420p[v{i}]")
        if scene == "end":
            chain = (f"[{i}:v]trim=end_frame=1,loop=loop={frames}:size=1,setpts=N/30/TB,fps=30,"
                     f"gblur=sigma=30,scale=1920:1080,setsar=1,format=yuv420p[v{i}]")
        chains.append(chain)
    # crossfades
    prev, acc = "v0", durs[0]
    for i in range(1, len(order)):
        chains.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={acc:.3f}[x{i}]")
        prev, acc = f"x{i}", acc + durs[i]
    n_in = len(order)
    inputs += ["-framerate", "30", "-i", str(overlay_dir / "%04d.png"), "-i", str(audio)]
    chains.append(f"[{prev}]trim=duration={total},setpts=PTS-STARTPTS[base];"
                  f"[{n_in}:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,"
                  f"fade=t=in:st=0:d=0.35,fade=t=out:st={total - 0.45:.2f}:d=0.45,format=yuv420p[vout]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains),
         "-map", "[vout]", "-map", f"{n_in + 1}:a", "-t", f"{total}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])


rows, scenes, voice, total = voice_timeline()
cues = subs(rows, scenes, voice, total)
tl = {"duration": total, "scenes": scenes, "subs": cues}
json.dump(tl, open(V / "timeline.json", "w"), ensure_ascii=False, indent=1)
print("total", round(total, 2), {k: round(v, 2) for k, v in scenes.items()})
# SRT for the record
with open(V / "subtitles_vi.srt", "w", encoding="utf-8") as f:
    ts = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round(s % 1 * 1000)) % 1000:03d}"
    for k, (a, b, txt) in enumerate(cues, 1):
        f.write(f"{k}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
if "--timeline-only" in FLAGS:
    sys.exit(0)
ov = V / "ovframes"
if "--no-overlay-render" not in FLAGS:
    run(["rm", "-rf", str(ov)])
    run(["node", str(V / "rec/render_overlay.mjs"), str(V / "overlay"), str(V / "timeline.json"), str(ov)])
mix_audio(voice, total, scenes, V / "audio/final_mix.wav")
edit(scenes, total, ov, V / "audio/final_mix.wav", V / f"FieldShift_demo_{PREFIX}.mp4")
print("done", V / f"FieldShift_demo_{PREFIX}.mp4")
