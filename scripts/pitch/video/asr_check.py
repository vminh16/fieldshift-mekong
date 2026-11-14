import difflib
import glob
import os
import re
import sys

from faster_whisper import WhisperModel

lines = {
    row.split("|")[0]: row.split("|", 2)[2].strip()
    for row in open(sys.argv[1], encoding="utf-8")
    if row.strip() and not row.startswith("#")
}
m = WhisperModel("small.en", device="cpu", compute_type="int8")


def norm(s):
    return re.sub(
        r"[^a-z0-9 ]",
        "",
        s.lower()
        .replace("-", " ")
        .replace("177", "one hundred seventy seven")
        .replace("84", "eighty four"),
    )


for f in sorted(glob.glob(sys.argv[2] + "/*_t*.wav")):
    scene = os.path.basename(f).split("_")[2]
    segs, _ = m.transcribe(f, beam_size=5, word_timestamps=True)
    segs = list(segs)
    txt = " ".join(s.text for s in segs).strip()
    words = [w for s in segs for w in s.words]
    end = words[-1].end if words else 0
    ratio = difflib.SequenceMatcher(None, norm(txt).split(), norm(lines[scene]).split()).ratio()
    print(f"{os.path.basename(f):28s} match={ratio:.2f} speech_end={end:.2f}s | {txt}")
