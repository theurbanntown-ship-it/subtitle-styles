"""Subs 4-8: phrase-card caption styles (from a caption-app reference recording, 2026-11-16).
  sub4 "Adrian"   - black bold sans on cream line boxes, the spoken word turns red; hook card = red box, white text
  sub5 "Nora"     - white condensed serif, key words italic, each word blurs/fades in
  sub6 "Kendrick" - Montserrat bold: line 1 white on black box, line 2 black on bright-green box (tilted); card pops in
  sub7 "Kelly"    - white bold sans + italic serif key words; upcoming words wait dimmed, light up when spoken
  sub8 "Bob"      - rounded hand font, white, key words yellow (a lone key word is bigger); dim -> white
  sub9 "Moxie"    - big white lowercase SF Pro Medium, tight ragged lines, key words lime bold italic; words appear as spoken
Usage: python -E -P sub_cards.py sub4 in.mp4 words.txt out.mp4|out.mov [--y 1150] [--moves "12.9-15.35:1480,15.35-16.6:420"]
       [--keys "teeth,26,000,..."]   (words.txt: "start end [tag] word" per line; .mov = transparent ProRes 4444 layer)
--y = vertical centre of the caption block; --moves shifts it for time ranges (keep captions off faces);
--keys overrides the auto key words (auto = longest word of 4+ letters per card, numbers always count).
"""
import argparse, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

ap = argparse.ArgumentParser()
ap.add_argument("style", choices=["sub4", "sub5", "sub6", "sub7", "sub8", "sub9"])
ap.add_argument("inp"); ap.add_argument("words"); ap.add_argument("out")
ap.add_argument("--y", type=int, default=1150)
ap.add_argument("--moves", default="")
ap.add_argument("--keys", default="")
A = ap.parse_args()

W, H = 1080, 1920
FPS = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", A.inp], capture_output=True, text=True).stdout.strip())
FD = __file__.replace("\\", "/").rsplit("/scripts/", 1)[0] + "/fonts/"


def font(name, size, wght=None):
    return kfont(name.rsplit("/", 1)[-1], size, wght)


# per-style settings: max words per card, max chars per line, lines per card
S = {
    "sub4": dict(maxw=4, line=11, lines=2, f=font("SF-Pro-Display-Bold.otf", 66), track=-0.02),
    "sub5": dict(maxw=5, line=14, lines=2, f=font(FD + "InstrumentSerif-Regular.ttf", 96),
                 fk=font(FD + "InstrumentSerif-Italic.ttf", 96), track=0),
    "sub6": dict(maxw=4, line=11, lines=2, f=font(FD + "Montserrat[wght].ttf", 56, 700), track=-0.01),
    "sub7": dict(maxw=5, line=16, lines=2, f=font("SF-Pro-Display-Bold.otf", 62), fk=font(FD + "PlayfairDisplay-Italic[wght].ttf", 74, 700),
                 track=-0.02),
    "sub8": dict(maxw=2, line=14, lines=1, f=font(FD + "Mali-Bold.ttf", 86), track=0),
    "sub9": dict(maxw=4, line=10, lines=4, f=font("SF-Pro-Display-Medium.otf", 108),
                 fk=font("SF-Pro-Display-SemiboldItalic.otf", 108), track=-0.025),
}[A.style]
CREAM, RED, GREEN, YELLOW, LIME = (251, 243, 230), (224, 66, 74), (44, 240, 24), (255, 236, 0), (232, 251, 68)
STOP = set("the a an and or but to of in on at for is it its it's i i'm you your we our my me so that this with be "
           "was are have has had do did don't didn't not too".split())

words = []
for line in open(A.words, encoding="utf-8"):
    p = line.split()
    if len(p) >= 3:
        words.append([float(p[0]), float(p[1]), p[-1]])
norm = lambda s: s.strip(".,?!:;\"").lower()
KEYS = {norm(k) for k in A.keys.split(",") if k.strip()}
MOVES = [(float(a), float(b), int(y)) for a, b, y in
         (m.replace("-", " ", 1).replace(":", " ").split() for m in A.moves.split(",") if m.strip())]

# --- chunk words into cards: break on punctuation, pauses, size ---
cards, cur = [], []
for i, w in enumerate(words):
    cur.append(i)
    gap = words[i + 1][0] - w[1] if i + 1 < len(words) else 9
    chars = sum(len(words[j][2]) + 1 for j in cur)
    if len(cur) >= S["maxw"] or w[2][-1] in ".,?!" or gap > 0.35 or chars > S["line"] * S["lines"] - 4:
        cards.append(cur); cur = []
if cur:
    cards.append(cur)


def split_lines(idx):
    if A.style == "sub9":               # greedy: fill each line up to S["line"] chars
        out = [[]]
        for j in idx:
            if out[-1] and sum(len(words[k][2]) + 1 for k in out[-1]) + len(words[j][2]) > S["line"]:
                out.append([])
            out[-1].append(j)
        return out
    if S["lines"] == 1 or len(idx) == 1 or sum(len(words[j][2]) + 1 for j in idx) <= S["line"]:
        return [idx]
    best = min(range(1, len(idx)), key=lambda k: abs(sum(len(words[j][2]) for j in idx[:k]) -
                                                       sum(len(words[j][2]) for j in idx[k:])))
    return [idx[:best], idx[best:]]


def is_key(j, idx):
    t = norm(words[j][2])
    if KEYS:
        return t in KEYS
    if any(c.isdigit() for c in t):
        return True
    cand = [k for k in idx if len(norm(words[k][2])) >= 4 and norm(words[k][2]) not in STOP]
    return bool(cand) and j == max(cand, key=lambda k: len(words[k][2]))


def disp(j):
    t = words[j][2]
    if A.style == "sub9":               # reference: all lowercase, punctuation kept
        return t.lower()
    return t if A.style in ("sub5", "sub7") else t.rstrip(".,!?:;") if not any(c.isdigit() for c in t[-2:]) else t


def tlen(s, f):
    return sum(f.getlength(c) for c in s) + S["track"] * f.size * max(0, len(s) - 1)


def text(d, x, y, s, f, fill):          # y = baseline
    for c in s:
        d.text((x, y), c, font=f, fill=fill, anchor="ls")
        x += f.getlength(c) + S["track"] * f.size


ease = lambda k: 1 - (1 - max(0.0, min(1.0, k))) ** 3


def render(ci, t):
    idx = cards[ci]; lines = split_lines(idx)
    cy = next((y for a, b, y in MOVES if a <= words[idx[0]][0] < b), A.y)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    f = S["f"]; asc, desc = f.getmetrics()
    st = A.style
    # word fonts / sizes
    wf = {}
    for j in idx:
        k = is_key(j, idx)
        wf[j] = (S.get("fk", f) if k and st in ("sub5", "sub7", "sub9") else
                 f.font_variant(size=int(f.size * 1.3)) if st == "sub8" and k and len(idx) == 1 else f)
    gap = 0.26 * f.size
    lw = [sum(tlen(disp(j), wf[j]) for j in ln) + gap * (len(ln) - 1) for ln in lines]
    lh = int(f.size * (1.12 if st in ("sub4", "sub6") else 0.84 if st == "sub9" else 1.0))
    top = cy - lh * len(lines) // 2
    hook = st == "sub4" and (ci == 0 or (len(idx) == 1 and is_key(idx[0], idx)))
    for li, ln in enumerate(lines):
        base = top + li * lh + asc
        if st == "sub4":
            x0 = (W - max(lw)) / 2
        elif st == "sub9":              # ragged right-aligned block, like the reference
            x0 = (W + max(lw)) / 2 - lw[li] + (0, -34, 22, -12)[li % 4]
        else:
            x0 = (W - lw[li]) / 2
        # boxes
        if st == "sub4":
            px, py = 18, 10
            box = (x0 - px, base - asc + 4 - py, x0 + lw[li] + px, base + desc - 6 + py)
            d.rectangle(box, fill=RED if hook else CREAM)
        if st == "sub6":
            px, py = 20, 6
            box = (x0 - px, base - asc + 8 - py, x0 + lw[li] + px, base + desc - 4 + py)
            green = li == 1 or len(lines) == 1
            d.rounded_rectangle(box, 12, fill=GREEN if green else (0, 0, 0))
        x = x0
        for j in ln:
            s, e = words[j][0], words[j][1]
            shown = t >= s
            ff = wf[j]
            if st == "sub4":
                if shown:
                    nxt = words[j + 1][0] if j + 1 < len(words) else e + 0.3
                    active = s <= t < max(e, nxt)
                    text(d, x, base, disp(j), ff, (255, 255, 255) if hook else RED if active else (0, 0, 0))
            elif st == "sub6":
                text(d, x, base, disp(j), ff, (0, 0, 0) if (li == 1 or len(lines) == 1) else (255, 255, 255))
            elif st == "sub9":
                if shown:
                    text(d, x, base, disp(j), ff, LIME if is_key(j, idx) else (255, 255, 255))
            else:
                k = ease((t - s) / 0.15) if shown else 0
                col = YELLOW if (st == "sub8" and is_key(j, idx)) else (255, 255, 255)
                if st == "sub5":
                    a = int(255 * k)
                    if a:
                        wl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                        text(ImageDraw.Draw(wl), x, base, disp(j), ff, col + (a,))
                        if k < 1:
                            wl = wl.filter(ImageFilter.GaussianBlur(8 * (1 - k)))
                        layer.alpha_composite(wl)
                else:                   # sub7 / sub8: waits dimmed, lights up when spoken
                    a = int(255 * (0.35 + 0.65 * k))
                    text(d, x, base, disp(j), ff, col + (a,))
            x += tlen(disp(j), ff) + gap
    if st == "sub6":                    # tilt + pop the whole card
        k = (t - words[idx[0]][0]) / 0.18
        sc = 0.55 + 0.53 * ease(k) - 0.08 * ease((k - 1) * 2) if k < 1.5 else 1.0
        bb = layer.getbbox()
        if bb:
            card = layer.crop(bb).rotate(-2 if len(lines) == 1 else 0, expand=True, resample=Image.BICUBIC)
            if len(lines) == 2:          # tilt only the green (second) line, like the reference
                l1 = layer.crop((0, 0, W, top + lh + 6)); l2 = layer.crop((0, top + lh + 6, W, H))
                l2 = l2.rotate(-2, center=(W / 2, 30), resample=Image.BICUBIC)
                tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmp.alpha_composite(l1); tmp.alpha_composite(l2, (0, top + lh + 6))
                card = tmp.crop(bb)
            card = card.resize((max(1, int(card.width * sc)), max(1, int(card.height * sc))), Image.LANCZOS)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.alpha_composite(card, (int((bb[0] + bb[2]) / 2 - card.width / 2), int((bb[1] + bb[3]) / 2 - card.height / 2)))
    if hook and A.style == "sub4":
        bb = layer.getbbox()
        if bb:
            c = layer.crop(bb).rotate(2, expand=True, resample=Image.BICUBIC)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.alpha_composite(c, ((bb[0] + bb[2] - c.width) // 2, (bb[1] + bb[3] - c.height) // 2))
    if st in ("sub5", "sub7", "sub8", "sub9"):  # soft shadow so white text reads on real footage
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(layer.getchannel("A").point(lambda v: min(255, int(v * 0.9))))
        sh = sh.filter(ImageFilter.GaussianBlur(5))   # strong enough for white walls
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(sh, (0, 3)); out.alpha_composite(layer)
        layer = out
    return layer


spans = []
for ci, idx in enumerate(cards):
    s = max(0, words[idx[0]][0] - (0.0 if A.style in ("sub4", "sub5") else 0.05))
    nxt = words[cards[ci + 1][0]][0] if ci + 1 < len(cards) else 99
    spans.append((s, min(nxt, words[idx[-1]][1] + 0.4)))

ALPHA = A.out.lower().endswith(".mov"); r = str(round(FPS, 3))
base_in = (["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={r},format=rgba"] if ALPHA else ["-i", A.inp])
enc = (["-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16"]
       if ALPHA else ["-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "copy"])
proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", *base_in, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                         "-r", r, "-i", "-", "-filter_complex",
                         f"[0:v][1:v]overlay=0:0:shortest=1,format={'yuva444p10le' if ALPHA else 'yuv420p'}[v]", *enc, A.out],
                        stdin=subprocess.PIPE)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", A.inp],
                           capture_output=True, text=True).stdout)
blank, last, frame = bytes(W * H * 4), None, None
for n in range(round(dur * FPS)):
    t = n / FPS
    ci = next((i for i, (a, b) in enumerate(spans) if a <= t < b), None)
    if ci is None:
        proc.stdin.write(blank); continue
    key = (ci, tuple(round(min(1, max(-1, (t - words[j][0]) / 0.15)), 2) for j in cards[ci]),
           round(min(1.5, t - spans[ci][0]), 2) if A.style == "sub6" else 0)
    if key != last:
        last, frame = key, render(ci, t).tobytes()
    proc.stdin.write(frame)
proc.stdin.close(); proc.wait()
print("done", A.out, len(cards), "cards")
