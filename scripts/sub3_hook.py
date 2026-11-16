"""Sub No. 3 HOOK animation (from the same reel): the opening line is split into two justified stacks placed around the
subject (one straight, one tilted), words enter by pop / zoom-from-tiny-with-blur / slide-in-with-motion-blur, the
whole shot slowly zooms out with the text locked to it inside a dark oval vignette, hand-drawn doodles pop and wobble
above the head, and the shot exits with a sideways whip blur into the next one.
Usage: python -E -P sub3_hook.py clean.mp4 sub3_burned.mp4 out.mp4
  clean.mp4 = the edit without captions; sub3_burned.mp4 = the same edit run through sub3_captions.py (used after the cut).
  out.mov = transparent ProRes 4444 layer of the hook text + doodles only (zoom and whip applied to the text; no footage,
  no vignette): put it over the edit in Premiere. Frames after the hook are empty.
Edit HOOK below per video (times come from words.txt; CUT = first frame of the next shot).
"""
import math, random, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

CLEAN, BURNED, OUT = sys.argv[1:4]
W, H = 1080, 1920
FPS = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", CLEAN], capture_output=True, text=True).stdout.strip())
TRACK = -0.03

CUT = 34                       # frame index of the first frame after the hook shot
ZOOM = (1.14, 1.0)             # scene scale at start -> at the cut (slow zoom-out, text locked to the scene)
# stacks: centre-x, top-y, width, tilt (deg); words: (text, start s, stack, line, entrance, extra tilt)
STACKS = {"A": (790, 300, 300, 0), "B": (330, 1130, 520, 7)}   # tilt +: rises to the right, like the reference
WORDS = [("My", 0.04, "A", 0, "pop", 0), ("favorite", 0.09, "A", 1, "zoom", 0),
         ("adulting", 0.46, "B", 0, "slide", 0), ("upgrade.", 0.82, "B", 1, "slide", 4)]
DOODLES = [(380, 400, 44, 0.20), (500, 300, 66, 0.32), (615, 390, 44, 0.44)]   # sparkles: x, y, size, pop time
DOODLE_C = (226, 32, 38)       # red, like the reference's "?" marks (reads on yellow/cream walls too)
DOODLE_SHAPE = "sparkle"       # "sparkle" or "?" (the reference's hand-drawn question marks)
ENTER = 0.2                    # s per entrance


def tlen(text, f):
    return sum(f.getlength(c) for c in text) + TRACK * f.size * (len(text) - 1)


def sprite(text, f):
    asc, desc = f.getmetrics(); pad = 30
    im = Image.new("RGBA", (int(tlen(text, f)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    sh, tx = im.copy(), im.copy()
    for layer, dx, dy, col in ((sh, 3, 6, (0, 0, 0, 170)), (tx, 0, 0, (255, 255, 255, 255))):
        d, x = ImageDraw.Draw(layer), pad + dx
        for c in text:
            d.text((x, pad + asc + dy), c, font=f, fill=col, anchor="ls"); x += f.getlength(c) + TRACK * f.size
    return Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), tx)


def mblur(im, dx, n=None):
    """horizontal motion blur: average of n copies spread over dx px"""
    if abs(dx) < 2:
        return im
    if im.mode == "RGBA":                   # sprites: pad so the shifted copies don't wrap around
        p = int(abs(dx) / 2) + 2
        im = im.crop((-p, 0, im.width + p, im.height))
    n = n or max(6, min(48, int(abs(dx) / 6)))   # enough copies for a smooth smear, not strobing
    acc = None
    for i in range(n):
        s = ImageChops.offset(im, int(dx * (i / (n - 1) - 0.5)), 0)
        acc = s if acc is None else Image.blend(acc, s, 1 / (i + 1))
    return acc


ease = lambda k: 1 - (1 - max(0, min(1, k))) ** 3

# --- lay out the stacks (justified: each line scaled to the stack width) ---
lines = {}                      # (stack, line) -> word indexes (index, not text: a line may repeat a word like "I")
for i, (text, _, st, ln, *_) in enumerate(WORDS):
    lines.setdefault((st, ln), []).append(i)
base = kfont("SF-Pro-Display-Bold.otf", 100)
place = {}                      # word index -> (sprite, centre x, centre y, tilt)
for st, (cx, top, bw, tilt) in STACKS.items():
    y = top
    for ln in sorted(l for s, l in lines if s == st):
        txt = " ".join(WORDS[i][0] for i in lines[(st, ln)])
        f = base.font_variant(size=int(100 * bw / tlen(txt, base)))
        y += int(f.size * (0.80 if ln == 0 else 0.86))
        x = cx - tlen(txt, f) / 2
        for w in lines[(st, ln)]:
            sp = sprite(WORDS[w][0], f)
            place[w] = (sp, x - 30 + sp.width / 2, y - (30 + f.getmetrics()[0]) + sp.height / 2, tilt)
            x += tlen(WORDS[w][0] + " ", f)
    # rotate the whole stack about its centre: move each word centre accordingly
    if tilt:
        ws = [i for i, wd in enumerate(WORDS) if wd[2] == st]
        cy = sum(place[w][2] for w in ws) / len(ws); a = math.radians(-tilt)
        for w in ws:
            sp, px, py, t = place[w]
            dx, dy = px - cx, py - cy
            place[w] = (sp, cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a), t)

# dark oval vignette (fixed on screen)
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse((-140, 60, W + 140, H - 60), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(120))
VIG = Image.new("RGBA", (W, H), (0, 0, 0, 0)); VIG.putalpha(vig.point(lambda v: int((255 - v) * 0.85)))   # dark outside the oval only


QFONT = kfont("Mali-Bold.ttf", 200)


def qmark(scene, x, y, s, tick, i):
    """hand-drawn red "?" that wobbles (tilt + size jitter re-drawn every 3 frames)"""
    rnd = random.Random(tick * 7 + i)
    f = QFONT.font_variant(size=max(8, int(s * 2.2)))
    im = Image.new("RGBA", (int(s * 3), int(s * 3)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((im.width / 2, im.height / 2), "?", font=f, anchor="mm", fill=DOODLE_C + (255,),
           stroke_width=max(2, int(s * 0.09)), stroke_fill=(0, 0, 0, 140))
    im = im.rotate(rnd.uniform(-14, 14) + (i - 1) * 12, resample=Image.BICUBIC)
    scene.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))


def sparkle(d, x, y, s, tick, i):
    rnd = random.Random(tick * 7 + i)           # hand-drawn wobble, re-drawn every 3 frames ("boil")
    j = lambda: rnd.uniform(-s * 0.08, s * 0.08)
    pts = []
    for k in range(9):
        a = math.pi / 2 * k / 2
        r = s if k % 2 == 0 else s * 0.28
        pts.append((x + r * math.cos(a) + j(), y + r * math.sin(a) + j()))
    d.line(pts, fill=(0, 0, 0, 120), width=16, joint="curve")
    d.line(pts, fill=DOODLE_C + (255,), width=11, joint="curve")


ALPHA = OUT.lower().endswith(".mov")


def smear(im, dx, n=None):
    """motion blur for a full RGBA layer without wrapping around the frame edges"""
    if abs(dx) < 2:
        return im
    n = n or max(6, min(48, int(abs(dx) / 6))); p = int(abs(dx) / 2) + 2
    big = Image.new("RGBA", (im.width + 2 * p, im.height), (0, 0, 0, 0)); big.paste(im, (p, 0))
    acc = None
    for i in range(n):
        sh = Image.new("RGBA", big.size, (0, 0, 0, 0)); sh.paste(big, (int(dx * (i / (n - 1) - 0.5)), 0))
        acc = sh if acc is None else Image.blend(acc, sh, 1 / (i + 1))
    return acc.crop((p, 0, p + im.width, im.height))


def hook_frame(clean, n):
    t = n / FPS
    scene = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if ALPHA else clean.convert("RGBA")
    for wi, (text, s, st, ln, how, extra) in enumerate(WORDS):
        if t < s:
            continue
        sp, px, py, tilt = place[wi]
        k = (t - s) / ENTER; e = ease(k)
        im = sp.rotate(tilt + extra, resample=Image.BICUBIC, expand=True) if (tilt + extra) else sp
        if how == "pop" and k < 1:
            sc = 1.25 - 0.25 * e; im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        elif how == "zoom" and k < 1:
            sc = 0.25 + 0.75 * e
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
            im = im.filter(ImageFilter.GaussianBlur(10 * (1 - e)))
        elif how == "slide" and k < 1:
            off = -(px + im.width / 2 + 40) * (1 - e)      # from beyond the left edge
            vel = (px + im.width / 2 + 40) * (ease(k + 0.15) - e)
            px += off; im = mblur(im, vel * 1.6)
        if k < 1:
            a = im.getchannel("A").point(lambda v: int(v * min(1, k * 2.5))); im.putalpha(a)
        scene.alpha_composite(im, (int(px - im.width / 2), int(py - im.height / 2)))
    d = ImageDraw.Draw(scene)
    for i, (x, y, s, ts) in enumerate(DOODLES):
        if t >= ts:
            pop = 1 + 0.35 * math.sin(min(1, (t - ts) / 0.15) * math.pi)
            if DOODLE_SHAPE == "?":
                qmark(scene, x, y, s * pop, n // 3, i)
            else:
                sparkle(d, x, y, s * pop, n // 3, i)
    # slow zoom-out, text locked to the scene
    sc = ZOOM[0] + (ZOOM[1] - ZOOM[0]) * ease(n / CUT)
    big = scene.resize((int(W * sc), int(H * sc)), Image.BICUBIC)
    l, tp = (big.width - W) // 2, (big.height - H) // 2
    big = big.crop((l, tp, l + W, tp + H))
    return big if ALPHA else Image.alpha_composite(big, VIG)


def rd(p):
    b = p.stdout.read(W * H * 3)
    return Image.frombytes("RGB", (W, H), b) if len(b) == W * H * 3 else None


src = lambda f: subprocess.Popen(["ffmpeg", "-v", "error", "-i", f, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                 stdout=subprocess.PIPE)
pc, pb = src(CLEAN), src(BURNED)
r = str(round(FPS, 3))
out = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba" if ALPHA else "rgb24",
                        "-s", f"{W}x{H}", "-r", r, "-i", "-"] +
                       (["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", OUT] if ALPHA else
                        ["-i", CLEAN, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                         "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", OUT]), stdin=subprocess.PIPE)
EMPTY = bytes(W * H * 4)
WHIP = 4                                   # frames of whip-out before the cut and whip-in after it
n = 0
while True:
    c, b = rd(pc), rd(pb)
    if c is None or b is None:
        break
    if ALPHA:                               # text-only layer
        if n < CUT:
            f = hook_frame(c, n); k = n - (CUT - WHIP)
            if k >= 0:
                g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g.paste(f, (-int(70 * (k + 1) ** 1.5), 0))
                f = smear(g, 90 * (k + 1))
            out.stdin.write(f.tobytes())
        else:
            out.stdin.write(EMPTY)
        n += 1; continue
    if n < CUT:
        f = hook_frame(c, n).convert("RGB")
        k = n - (CUT - WHIP)
        if k >= 0:                          # whip out: smear and push left
            f = mblur(ImageChops.offset(f, -int(70 * (k + 1) ** 1.5), 0), 90 * (k + 1))
    elif n < CUT + WHIP - 1:                # whip in: arrive from the right, sharpening
        k = CUT + WHIP - 1 - n
        f = mblur(ImageChops.offset(c, int(60 * k ** 1.5), 0), 90 * k)   # clean frame: captions appear once it settles
    else:
        f = b
    out.stdin.write(f.tobytes())
    n += 1
out.stdin.close(); out.wait()
print("done", OUT, n, "frames")
