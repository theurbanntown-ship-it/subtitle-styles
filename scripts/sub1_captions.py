"""Burn reference-style captions (white SF Pro, small words + big bold key word, word-by-word fade-in,
2 lines, block centred, lines left-aligned, lower third) onto a video.
Usage: python captions.py in.mp4 words.txt out.mp4
words.txt: "start end word" per line (whisper word timings).
"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

IN, WORDS, OUT = sys.argv[1:4]
FPS, W, H = 25, 1080, 1920
BAND_Y, BAND_H = 1060, 640          # caption band (overlay region)
TOP = 1180 - BAND_Y                 # block top inside band
# sizes measured from the reference at 1080 px wide: line-1 small words ~42, line-2 small words ~54, key words ~82 bold
SMALL1 = kfont("SF-Pro-Display-Semibold.ttf", 50)
SMALL2 = kfont("SF-Pro-Display-Semibold.ttf", 64)
BIG = kfont("SF-Pro-Display-Bold.otf", 98)
TRACK = -0.045          # letter spacing in em (very tight, like the reference)
WORD_GAP = 0.22         # space between words in em
FADE, RISE = 0.12, 6

# pages: "/" = line break, *word* = key word. Tokens must match the spoken words in order.
PAGES = """My favourite / *adulting* *upgrade*
I didn't think / I would *care*
this *much* about it
But honestly it's / *life-changing*
I used to brush / on total *autopilot*
Half asleep / not *thinking*
Then I switched to
the *Perfora* / Rechargeable Electric / *Toothbrush*
*Sonic* cleaning
Up to *26,000* / strokes a minute
A built-in *timer*
tells me when to / *switch* *sides*
So I don't even / have to *think*
*Charcoal-infused* / soft bristles
*IPX7* waterproof
And one charge / lasts up to *90* *days*
If you've never / really thought about
your *toothbrush*
this is your *sign*
Get your *Perfora* / Rechargeable Electric / *Toothbrush*""".splitlines()

words = []
for line in open(WORDS, encoding="utf-8"):
    p = line.split(None, 2)
    if len(p) == 3:
        words.append((float(p[0]), float(p[1]), p[2].strip()))

pages, wi = [], 0
for pg in PAGES:
    lines = []
    for ln in pg.split("/"):
        toks = []
        for tok in ln.split():
            key = tok.startswith("*")
            toks.append({"text": tok.strip("*"), "key": key, "t": words[wi][0]})
            wi += 1
        lines.append(toks)
    pages.append(lines)
assert wi == len(words), f"page tokens {wi} != spoken words {len(words)}"
for i, pg in enumerate(pages):
    pg_start = pg[0][0]["t"]
    pg_end = pages[i + 1][0][0]["t"] if i + 1 < len(pages) else 99
    pages[i] = (pg_start, pg_end, pg)


def wlen(text, f):
    return sum(f.getlength(c) for c in text) + TRACK * f.size * (len(text) - 1)


def layout(lines):
    """-> list of (x, baseline_y, tok, font): block centred, lines left-aligned, mixed sizes on one baseline."""
    rows, widths = [], []
    for li, toks in enumerate(lines):
        small = SMALL1 if li == 0 and len(lines) > 1 else SMALL2
        x, items, asc_max = 0, [], 0
        for tok in toks:
            f = BIG if tok["key"] else small
            items.append([x, tok, f])
            x += wlen(tok["text"], f) + WORD_GAP * f.size
            asc_max = max(asc_max, f.getmetrics()[0])
        widths.append(x - WORD_GAP * items[-1][2].size)
        rows.append((items, asc_max))
    x0 = (W - max(widths)) / 2
    out, y = [], TOP
    for items, asc in rows:
        base = y + asc * 0.80
        for x, tok, f in items:
            out.append((x0 + x, base, tok, f))
        y = base + 16
    return out


def draw_word(d, x, y, text, f, fill):
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + TRACK * f.size


cache = {}
ALPHA = OUT.lower().endswith(".mov")   # .mov -> transparent caption layer only (ProRes 4444 + alpha) for Premiere
base_in = (["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={FPS},format=rgba"] if ALPHA else ["-i", IN])
enc = (["-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16"]
       if ALPHA else ["-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-c:a", "copy"])
proc = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error", *base_in, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{BAND_H}",
     "-r", str(FPS), "-i", "-", "-filter_complex", f"[0:v][1:v]overlay=0:{BAND_Y}:shortest=1,format={'yuva444p10le' if ALPHA else 'yuv420p'}[v]",
     *enc, OUT],
    stdin=subprocess.PIPE)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", IN],
                           capture_output=True, text=True).stdout)
blank = bytes(W * BAND_H * 4)
for n in range(round(dur * FPS)):
    t = n / FPS
    pg = next((p for p in pages if p[0] <= t < p[1]), None)
    if not pg:
        proc.stdin.write(blank); continue
    items = layout(pg[2])
    alphas = tuple(round(min(1, max(0, (t - tok["t"]) / FADE)), 2) for _, _, tok, _ in items)
    key = (pg[0], alphas)
    if key not in cache:
        txt = Image.new("RGBA", (W, BAND_H), (0, 0, 0, 0))
        sh = Image.new("RGBA", (W, BAND_H), (0, 0, 0, 0))
        dt, ds = ImageDraw.Draw(txt), ImageDraw.Draw(sh)
        for (x, base, tok, f), a in zip(items, alphas):
            if a <= 0:
                continue
            y = base - f.getmetrics()[0] + (1 - a) * RISE
            draw_word(dt, x, y, tok["text"], f, (255, 255, 255, int(255 * a)))
            draw_word(ds, x, y + 2, tok["text"], f, (0, 0, 0, int(60 * a)))
        glow = txt.filter(ImageFilter.GaussianBlur(9))          # soft white bloom around the letters
        glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.55)))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        cache.clear()
        cache[key] = Image.alpha_composite(Image.alpha_composite(sh, glow), txt).tobytes()
    proc.stdin.write(cache[key])
proc.stdin.close()
proc.wait()
print("done", OUT, proc.returncode)
