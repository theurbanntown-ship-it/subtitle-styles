"""Sub 11 "podcast yellow pop": small white Montserrat Bold words build up on one centred line; a key word lands as a huge
UPPERCASE Montserrat ExtraBold in yellow #FFCC00 with a soft yellow glow behind it. Small words before the key word sit
just above it, flush with its left edge; small words after sit just below, flush with its right edge. Words cut in on
their spoken start (no fade). From an Instagram podcast reel (2026-11-25).
Usage: python -E -P sub11_captions.py edit.mp4 words.txt out.mp4|out.mov
PAGES: one card per line, "/" = line break, *word* = key word (a line is all key or all small; one key line per card),
"@y" at the end moves that card's baseline (the key line's, or the small line's) to y.
Tokens must match the spoken words in order (count is asserted).
"""
import os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontkit import font as kfont

IN, WORDS, OUT = sys.argv[1:4]
W, H = 1080, 1920
BASE = 1124                      # default baseline (chest height, sampled from the reference)
YELLOW = (255, 204, 0)
SMALL_SIZE, BIG_SIZE = 50, 108
GAP = 0.26                       # word gap, em
MAXW = 980                       # long key lines shrink to fit

def mont(size, wght):
    f = kfont("Montserrat[wght].ttf", size); f.set_variation_by_axes([wght]); return f
_fonts = {}
def F(key, size=None):
    k = (key, size)
    if k not in _fonts: _fonts[k] = mont(size or (BIG_SIZE if key else SMALL_SIZE), 800 if key else 700)
    return _fonts[k]

PAGES = """*Two* *things* / you should be doing
Straighten / *your* *back*
and say goodbye to your / *toothbrush*"""

words = [(float(p[0]), p[2].strip()) for p in (l.split(None, 2) for l in open(WORDS, encoding="utf-8")) if len(p) == 3]
pages, wi = [], 0
for pg in PAGES.strip().splitlines():
    m = re.search(r"\s@(\d+)\s*$", pg); base = int(m.group(1)) if m else BASE; pg = pg[:m.start()] if m else pg
    lines = []
    for ln in pg.split("/"):
        toks = [{"text": t.strip("*"), "key": t.startswith("*"), "t": words[wi + i][0]} for i, t in enumerate(ln.split())]
        wi += len(toks)
        assert len({t["key"] for t in toks}) == 1, f"mix of key and small words on one line: {ln!r}"
        if toks[0]["key"]:
            for t in toks: t["text"] = t["text"].upper()
        lines.append(toks)
    assert sum(l[0]["key"] for l in lines) <= 1 and len(lines) <= 3, f"one key line, max 3 lines per card: {pg!r}"
    pages.append([lines, base])
assert wi == len(words), f"page tokens {wi} != spoken words {len(words)}"
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
off = 0
for lines, _ in pages:
    for ln in lines:
        for tok in ln:
            if norm(tok["text"]) != norm(words[off][1]): print(f"  note: shown {tok['text']!r} for spoken {words[off][1]!r}")
            off += 1
for i, p in enumerate(pages):
    p.append(p[0][0][0]["t"]); p.append(pages[i + 1][0][0][0]["t"] if i + 1 < len(pages) else 1e9)

def row(toks, f):
    x, items = 0, []
    for tok in toks: items.append((x, tok)); x += f.getlength(tok["text"]) + GAP * f.size
    return items, x - GAP * f.size

def layout(lines, base):
    """-> [(x, baseline, tok, font)]. Key line centred; small line above flush left, below flush right."""
    ki = next((i for i, l in enumerate(lines) if l[0]["key"]), None)
    out = []
    if ki is None:                                   # small-only card: lines centred, stacked upward from base
        f = F(False)
        for i, toks in enumerate(lines):
            items, w = row(toks, f); y = base - (len(lines) - 1 - i) * f.size * 1.05
            out += [((W - w) / 2 + x, y, t, f) for x, t in items]
        return out
    f = F(True); items, kw = row(lines[ki], f)
    if kw > MAXW: f = F(True, int(BIG_SIZE * MAXW / kw)); items, kw = row(lines[ki], f)
    kx = (W - kw) / 2; cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    out += [(kx + x, base, t, f) for x, t in items]
    s = F(False)
    for i, toks in enumerate(lines):
        if i == ki: continue
        items, w = row(toks, s)
        if i < ki: x0, y = kx, base - cap - 6        # sits on the key word's cap line, descenders tuck in
        else:      x0, y = kx + kw - w, base + s.size * 0.78
        out += [(x0 + x, y, t, s) for x, t in items]
    return out

ALPHA = OUT.lower().endswith(".mov")
fps = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", IN],
                          capture_output=True, text=True).stdout.strip())
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", IN], capture_output=True, text=True).stdout)
base_in = ["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={fps},format=rgba"] if ALPHA else ["-i", IN]
enc = (["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16"] if ALPHA
       else ["-map", "0:a?", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-c:a", "copy"])
proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", *base_in, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                         "-filter_complex", f"[0:v][1:v]overlay=0:0:shortest=1,format={'yuva444p10le' if ALPHA else 'yuv420p'}[v]", "-map", "[v]", *enc, OUT],
                        stdin=subprocess.PIPE)
blank, cache = bytes(W * H * 4), {}
for n in range(round(dur * fps)):
    t = n / fps
    pg = next((p for p in pages if p[2] <= t < p[3]), None)
    if not pg: proc.stdin.write(blank); continue
    items = layout(pg[0], pg[1])
    st = tuple(t >= tok["t"] for _, _, tok, _ in items)
    k = (id(pg), st)
    if k not in cache:
        txt, sh, glow = (Image.new("RGBA", (W, H), (0, 0, 0, 0)) for _ in range(3))
        dt, ds, dg = ImageDraw.Draw(txt), ImageDraw.Draw(sh), ImageDraw.Draw(glow)
        for (x, base, tok, f), on in zip(items, st):
            if not on: continue
            y = base - f.getmetrics()[0]
            if tok["key"]:
                dt.text((x, y), tok["text"], font=f, fill=YELLOW + (255,))
                dg.text((x, y), tok["text"], font=f, fill=YELLOW + (255,))
            else:
                dt.text((x, y), tok["text"], font=f, fill=(255, 255, 255, 255))
                ds.text((x, y + 3), tok["text"], font=f, fill=(0, 0, 0, 110))
        wide = glow.filter(ImageFilter.GaussianBlur(70)); g = Image.alpha_composite(Image.alpha_composite(wide, wide), glow.filter(ImageFilter.GaussianBlur(24)))   # warm halo that lifts the footage like the reference
        cache.clear(); cache[k] = Image.alpha_composite(Image.alpha_composite(g, sh.filter(ImageFilter.GaussianBlur(5))), txt).tobytes()
    proc.stdin.write(cache[k])
proc.stdin.close(); proc.wait(); print("done", OUT, proc.returncode)
