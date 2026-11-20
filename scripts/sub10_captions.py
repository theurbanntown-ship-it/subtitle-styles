"""Sub 10 "Yellow key line": small white regular words build word by word on one line, the key word(s) land on their own
line below in huge heavy yellow (#F3EB57), letters packed tight; block left-aligned, centred, chest height.
From an Instagram "how I edit my videos on Claude" reel (2026-11-20).
Usage: python -E -P sub10_captions.py edit.mp4 words.txt out.mp4|out.mov
PAGES: one card per line, "/" = line break, *word* = key word (a line is all key or all small),
"@y" at the end moves that card's top to y. Tokens must match the spoken words in order (count is asserted).
"""
import os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontkit import font as kfont

IN, WORDS, OUT = sys.argv[1:4]
W, H = 1080, 1920
TOP = 1150                       # default card top
YELLOW = (243, 235, 87)
SMALL_SIZE, BIG_SIZE = 46, 104
SMALL_TRACK, BIG_TRACK = -0.02, -0.065   # em; key words are packed so tight the letters touch
GAP = 0.24                       # word gap, em
POP = 0.08                       # key word grows 92% -> 100% over 2 frames; small words fade in over the same time

def inter(size, wght):
    f = kfont("Inter[opsz,wght].ttf", size)
    f.set_variation_by_axes([wght if a["name"] in (b"Weight", "Weight") else min(32, a["maximum"]) for a in f.get_variation_axes()])
    return f
_fonts = {}
def F(key, scale=1.0):
    k = (key, round(scale, 3))
    if k not in _fonts: _fonts[k] = inter(round((BIG_SIZE if key else SMALL_SIZE) * scale), 900 if key else 420)
    return _fonts[k]

PAGES = """*Two* *things* / you should be doing
Straighten / *your* *back*
and say goodbye to your / *toothbrush*
Everything around us has / *evolved*
Pac-Man became / *modern* *gaming*
cassettes became / *cloud* *storage*
and the toothbrush / still stuck in the / *past*
So why are we still / brushing the / *old* *way*
This is the / *Perfora* / Oscillating Toothbrush
a 360-degree / *rotating* *head*
up to / *8,800* *RPM*
a two-minute / *timer*
that reminds you to / *switch* *zones*
every / *30* *seconds*
*IPX7* / waterproof
and up to / *21* *days*
on a single / *USB-C* *charge*
Your brush deserves an / *upgrade*
Get / *Perfora's* / oscillating electric toothbrush now"""

words = [(float(p[0]), p[2].strip()) for p in (l.split(None, 2) for l in open(WORDS, encoding="utf-8")) if len(p) == 3]
pages, wi = [], 0
for pg in PAGES.strip().splitlines():
    m = re.search(r"\s@(\d+)\s*$", pg); top = int(m.group(1)) if m else TOP; pg = pg[:m.start()] if m else pg
    lines = []
    for ln in pg.split("/"):
        toks = [{"text": t.strip("*"), "key": t.startswith("*"), "t": words[wi + i][0]} for i, t in enumerate(ln.split())]
        wi += len(toks)
        assert len({t["key"] for t in toks}) == 1, f"mix of key and small words on one line: {ln!r}"
        lines.append(toks)
    pages.append([lines, top])
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

def wlen(text, f, track): return sum(f.getlength(c) for c in text) + track * f.size * (len(text) - 1)

def layout(lines, top):
    rows = []
    for toks in lines:
        key = toks[0]["key"]; f = F(key); tr = BIG_TRACK if key else SMALL_TRACK
        x, items = 0, []
        for tok in toks:
            items.append((x, tok)); x += wlen(tok["text"], f, tr) + GAP * f.size
        rows.append((items, key, x - GAP * f.size))
    x0 = (W - max(r[2] for r in rows)) / 2
    out, y, prev = [], top, None
    for items, key, _ in rows:
        f = F(key); asc = f.getmetrics()[0]
        y += (asc * 0.74) if prev is None else (asc * 0.74 + (14 if key or prev else 10))   # baseline; tight stacking like the reference
        for x, tok in items: out.append((x0 + x, y, tok))
        prev = key
    return out

def draw(d, x, base, tok, a, scale, fill):
    f = F(tok["key"], scale); tr = BIG_TRACK if tok["key"] else SMALL_TRACK
    y = base - f.getmetrics()[0]
    for c in tok["text"]:
        d.text((x, y), c, font=f, fill=fill + (int(255 * a),)); x += f.getlength(c) + tr * f.size

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
    st = tuple(round(min(1, max(0, (t - tok["t"]) / POP)), 2) if t >= tok["t"] else -1 for _, _, tok in items)
    k = (id(pg), st)
    if k not in cache:
        txt, sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)), Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dt, ds = ImageDraw.Draw(txt), ImageDraw.Draw(sh)
        for (x, base, tok), u in zip(items, st):
            if u < 0: continue
            a, s = (1.0, 0.92 + 0.08 * u) if tok["key"] else (0.35 + 0.65 * u, 1.0)
            col = YELLOW if tok["key"] else (255, 255, 255)
            draw(dt, x, base, tok, a, s, col); draw(ds, x, base + 3, tok, a * 0.35, s, (0, 0, 0))
        cache.clear(); cache[k] = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), txt).tobytes()
    proc.stdin.write(cache[k])
proc.stdin.close(); proc.wait(); print("done", OUT, proc.returncode)
