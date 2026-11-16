"""Word timings for an edit: python -I scripts/words.py edit.mp4 words.txt
Runs FFmpeg's whisper filter (needs an FFmpeg build with whisper, e.g. gyan.dev "full") and writes "start end word" lines.
Model search: $WHISPER_MODEL, then <skill>/models/, then ~/.claude/skills/pacing-rough-cut/models/ (ggml-*.bin).
No model? Download one (large-v3 is best, small.en is fast) from
https://huggingface.co/ggerganov/whisper.cpp/tree/main into <skill>/models/ (models/ is git-ignored: too big to share).
"""
import glob, json, os, subprocess, sys, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, out = (os.path.abspath(p) for p in sys.argv[1:3])
cands = [os.environ.get("WHISPER_MODEL", "")] + sorted(glob.glob(os.path.join(SKILL, "models", "ggml-*.bin"))) + \
        sorted(glob.glob(os.path.expanduser("~/.claude/skills/pacing-rough-cut/models/ggml-*.bin")))
model = next((c for c in cands if c and os.path.exists(c)), None)
if not model:
    sys.exit(__doc__)
mdir, mname = os.path.split(model)
with tempfile.TemporaryDirectory(dir=mdir) as tmp:
    # run inside the model's folder with relative paths: FFmpeg filter options can't take "C:" style paths cleanly
    dest = os.path.relpath(os.path.join(tmp, "w.json"), mdir).replace("\\", "/")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-af",
                        f"aresample=16000,whisper=model={mname}:language=en:queue=30:use_gpu=false:max_len=1:"
                        f"destination={dest}:format=json", "-f", "null", "-"], cwd=mdir, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg whisper failed:\n" + r.stderr)
    lines = []
    for l in open(os.path.join(tmp, "w.json"), encoding="utf-8"):
        if l.strip():
            d = json.loads(l); w = d["text"].strip()
            if w:
                lines.append(f"{d['start'] / 1000:.2f} {d['end'] / 1000:.2f} {w}")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(len(lines), "words ->", out)
