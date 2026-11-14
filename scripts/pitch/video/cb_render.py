"""Chatterbox takes per scene: python cb_render.py <lines> <outdir> <ref.wav> <tag> <takes>"""
import sys, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
lines, out, ref, tag, takes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
m = ChatterboxTTS.from_pretrained(device="cuda")
for l in open(lines, encoding="utf-8"):
    if not l.strip() or l.startswith("#"): continue
    scene, _, text = l.split("|", 2)
    text = text.strip().replace("Sóc Trăng", "Sock Trang")
    if not text: continue
    for k in range(takes):
        torch.manual_seed(100 + k)
        with torch.inference_mode():
            w = m.generate(text, audio_prompt_path=ref, exaggeration=0.62, cfg_weight=0.45, temperature=0.75)
        ta.save(f"{out}/{tag}_{scene}_t{k}.wav", w.cpu(), m.sr)
        print(tag, scene, k, round(w.shape[-1] / m.sr, 2), flush=True)
        del w; torch.cuda.empty_cache()
