"""Sub No. 3 "one word + hero stack" (from an Instagram reel, 2026-11-16).
Body: one spoken word at a time, centred mid-frame, white SF Pro Display Bold, faint soft shadow, punctuation kept.
Hero moments: a key phrase becomes a justified stack (every line scaled to the same width, so short words get huge),
building word by word; *line* = gold accent with an orange glow.
Usage: python -E -P sub3_captions.py in.mp4 words.txt out.mp4|out.mov    (.mov = transparent ProRes 4444 layer)
words.txt: "start end [tag] word" per line. Edit HEROES (spoken words in order, "/" = line break, optional @x,y = block
centre-x and top-y). Every word not inside a hero is shown on its own; BODY_MOVES shifts them off faces.
"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

IN, WORDS, OUT = sys.argv[1:4]
W, H = 1080, 1920
FPS = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", IN], capture_output=True, text=True).stdout.strip())
BODY = kfont("SF-Pro-Display-Bold.otf", 128)
BODY_Y = 1030                          # body word baseline (mid-frame, like the reference)
TRACK = -0.03                          # em
HERO_W = 560                           # default hero block width (px); every line is scaled to this width
GOLD, GLOW = (248, 210, 74), (255, 120, 30)
HOLD = 0.4                             # s a card stays after its word ends if nothing follows

HEROES = """My favorite / adulting / upgrade. @540,1120
the Perfora / Rechargeable / Electric / Toothbrush. @540,1180
Up to / *26,000* / strokes a minute. @540,1150
*90* / *days.* @540,1150
this is / your sign. @540,1180
Get your / *Perfora* / Rechargeable / Electric / Toothbrush. @540,1050""".splitlines()
BODY_MOVES = [(12.9, 15.35, 1480), (15.35, 16.6, 420), (21.2, 24.3, 1330)]   # (from s, to s, baseline y): move body words off faces

words = []
for line in open(WORDS, encoding="utf-8"):
    p = line.split()
    if len(p) >= 3:
        words.append((float(p[0]), float(p[1]), p[-1]))
norm = lambda s: s.strip(".,?!:;\"").lower()


def tlen(text, f):
    return sum(f.getlength(c) for c in text) + TRACK * f.size * (len(text) - 1)


def draw_text(d, x, y, text, f, fill):          # y = baseline
    for c in text:
        d.text((x, y), c, font=f, fill=fill, anchor="ls")
        x += f.getlength(c) + TRACK * f.size


def sprite(text, f, color, glow=False):
    asc, desc = f.getmetrics()
    pad = 60 if glow else 24
    im = Image.new("RGBA", (int(tlen(text, f)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    txt = im.copy()
    draw_text(ImageDraw.Draw(txt), pad, pad + asc, text, f, color + (255,))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(sh), pad + 2, pad + asc + 4, text, f, (0, 0, 0, 170))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(7)))   # readable on white walls too
    if glow:
        g = Image.new("RGBA", im.size, GLOW + (0,))
        g.putalpha(txt.getchannel("A").filter(ImageFilter.GaussianBlur(28)).point(lambda a: min(255, int(a * 1.6))))
        im = Image.alpha_composite(im, g)
    return Image.alpha_composite(im, txt), pad, pad + asc   # sprite, x offset, baseline offset


# --- match heroes to the transcript, build cards: (start, end, [(word_start, sprite, x, y)]) ---
cards, wi = [], 0
hero_at = {}
for h in HEROES:
    h, _, pos = h.partition("@")
    cx, top = (int(v) for v in pos.split(",")) if pos.strip() else (W // 2, 1100)
    lines = [[t for t in ln.split()] for ln in h.split("/")]
    toks = [t for ln in lines for t in ln]
    seq = [norm(t.strip("*")) for t in toks]
    i = next(i for i in range(wi, len(words)) if [norm(w[2]) for w in words[i:i + len(seq)]] == seq)
    hero_at[i] = (lines, cx, top, len(seq))
    wi = i + len(seq)

i = 0
while i < len(words):
    if i in hero_at:
        lines, cx, top, n = hero_at[i]
        items, y, k = [], top, i
        for ln in lines:
            gold = all(t.startswith("*") for t in ln)
            text = " ".join(t.strip("*") for t in ln)
            size = max(40, min(300, int(100 * HERO_W / tlen(text, BODY.font_variant(size=100)))))
            f = BODY.font_variant(size=size)
            asc = f.getmetrics()[0]
            y += int(asc * 0.80) if not items else int(size * 0.86)   # tight leading, like the reference
            x = cx - tlen(text, f) / 2
            # one sprite per word so the stack builds word by word
            for t in ln:
                wt = t.strip("*")
                im, ox, oy = sprite(wt, f, GOLD if gold else (255, 255, 255), glow=gold)
                items.append((words[k][0], im, int(x - ox), int(y - oy)))
                x += tlen(wt + " ", f)
                k += 1
        end = words[i + n][0] if i + n < len(words) else words[i + n - 1][1] + HOLD
        cards.append((words[i][0], min(end, words[i + n - 1][1] + 0.8), items))
        i += n
    else:
        s, e, text = words[i]
        im, ox, oy = sprite(text, BODY, (255, 255, 255))
        nxt = words[i + 1][0] if i + 1 < len(words) else 99
        by = next((y for a, b, y in BODY_MOVES if a <= s < b), BODY_Y)
        cards.append((s, min(nxt, e + HOLD), [(s, im, (W - im.width) // 2, by - oy)]))
        i += 1

# --- render ---
ALPHA = OUT.lower().endswith(".mov")
r = str(round(FPS, 3))
base_in = (["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={r},format=rgba"] if ALPHA else ["-i", IN])
enc = (["-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16"]
       if ALPHA else ["-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "copy"])
proc = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error", *base_in, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", r, "-i", "-",
     "-filter_complex", f"[0:v][1:v]overlay=0:0:shortest=1,format={'yuva444p10le' if ALPHA else 'yuv420p'}[v]", *enc, OUT],
    stdin=subprocess.PIPE)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", IN],
                           capture_output=True, text=True).stdout)
IN_T, RISE = 0.10, 14                   # word entrance: fade + small rise
blank, last, frame = bytes(W * H * 4), None, None
for n in range(round(dur * FPS)):
    t = n / FPS
    c = next((c for c in cards if c[0] <= t < c[1]), None)
    if not c:
        proc.stdin.write(blank); continue
    state = tuple(min(1.0, round((t - s) / IN_T, 2)) for s, *_ in c[2] if t >= s)
    if (c[0], state) != last:
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for (s, im, x, y), k in zip(c[2], state):
            e = 1 - (1 - k) ** 3
            if k < 1:
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * e)))
            band.alpha_composite(im, (max(0, x), max(0, y + int((1 - e) * RISE))))
        last, frame = (c[0], state), band.tobytes()
    proc.stdin.write(frame)
proc.stdin.close()
proc.wait()
print("done", OUT, proc.returncode)
