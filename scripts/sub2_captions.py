"""Sub No. 2 "stair stack" captions (from an Instagram reel, 2026-11-16): one word per line, each line overlaps the one
above and steps sideways; filler words = white Helvetica Neue Bold with a hard black drop shadow, the key word = big
slate-blue Playfair serif with a thin white edge. Words pop in on the beat; a phrase clears when the next starts.
Place each phrase in empty space (the reference moves them around): end a PAGES line with @<baseline y>.
Usage: python -E -P sub2_captions.py in.mp4 words.txt out.mp4|out.mov    (.mov = transparent ProRes 4444 layer)
words.txt: "start end [tag] word" per line. Edit PAGES: one phrase per line, *word* = key word.
"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

IN, WORDS, OUT = sys.argv[1:4]
W, H = 1080, 1920
FPS = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", IN], capture_output=True, text=True).stdout.strip())   # match the edit (e.g. 30/1)
BAND_Y, BAND_H = 0, 1920              # overlay region = full frame, so phrases can sit anywhere
Y0 = 1200                            # default first baseline; a page ending in @1520 moves it (dodge on-screen graphics)
SMALL = kfont("HelveticaNeueBold.otf", 96)
BIG = kfont("PlayfairDisplay-Bold.ttf", 170)
TRACK = -0.03                        # em
BLUE = (90, 118, 167, 255)           # sampled from the reference
STEP = [0, 90, -70, 70, -50]          # sideways stagger per line (px)
POP = 0.10                            # s, scale 1.2 -> 1

PAGES = """Stranded at *sea*
he drinks the *ocean*
But every *gulp*
is *three*
and a *half*
percent *salt*
His *kidneys*
have to *flush*
that salt *out*
but they *can't* @1520
make *pee* @1520
that *salty* @1520
So to get *rid*
of the *salt*
they *need*
more *water*
than he just *drank*
And that *water*
is pulled *out*
of his own *cells*
They *shrivel* up
like *raisins*
so every *sip*
makes him *thirstier*
So *no*
Even if you're *desperate*
the *ocean*
just *dries* you out
*faster*""".splitlines()

words = []
for line in open(WORDS, encoding="utf-8"):
    p = line.split()
    if len(p) >= 3:
        words.append((float(p[0]), float(p[1]), p[-1]))
strip = lambda s: s.strip(".,?!:;\"")   # outer punctuation only, so 26,000 keeps its comma


def sprite(text, key):
    f = BIG if key else SMALL
    while sum(f.getlength(c) for c in text) * (1 + TRACK) > W - 100:   # long word -> shrink to fit the frame
        f = f.font_variant(size=f.size - 6)
    asc, desc = f.getmetrics()
    w = int(sum(f.getlength(c) for c in text) + TRACK * f.size * len(text)) + 40
    im = Image.new("RGBA", (w, asc + desc + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def run(dx, dy, **kw):
        x = 15 + dx
        for c in text:
            d.text((x, 15 + dy), c, font=f, **kw)
            x += f.getlength(c) + TRACK * f.size
    if key:
        run(5, 6, fill=(0, 0, 0, 150), stroke_width=5, stroke_fill=(0, 0, 0, 150))
        run(0, 0, fill=BLUE, stroke_width=5, stroke_fill=(255, 255, 255, 255))
    else:
        run(6, 7, fill=(0, 0, 0, 235))   # hard shadow, no blur (like the reference)
        run(0, 0, fill=(255, 255, 255, 255))
    return im, 15 + asc                   # sprite, baseline offset inside it


pages, wi = [], 0
ys = []
for pg in PAGES:
    pg, _, y = pg.partition("@")
    ys.append(int(y or Y0) - BAND_Y)
    toks = []
    for tok in pg.split():
        s, e, spoken = words[wi]
        assert strip(tok.strip("*")).lower() == strip(spoken).lower(), (tok, spoken)
        toks.append((s, e, strip(tok.strip("*")), tok.startswith("*")))
        wi += 1
    pages.append(toks)
assert wi == len(words), f"page tokens {wi} != spoken words {len(words)}"

placed = []   # per page: (start, end, [(t, sprite, x, y)])
for i, toks in enumerate(pages):
    nxt = pages[i + 1][0][0] if i + 1 < len(pages) else 99
    items, base = [], ys[i]
    for li, (s, e, text, key) in enumerate(toks):
        im, bo = sprite(text, key)
        f = BIG if key else SMALL
        if li:   # lines overlap slightly, like the reference; a small word under a big serif one needs room for its descenders
            base += int(f.size * 0.92 if key else 0.22 * prev + 0.72 * f.size if prevkey else 0.76 * f.size)
        prev, prevkey = f.size, key
        x = (W - im.width) // 2 + STEP[li % len(STEP)]
        x = max(30, min(W - 30 - im.width, x))
        items.append((s, im, x, base - bo))
    placed.append((toks[0][0], min(nxt, toks[-1][1] + 0.6), items))

ALPHA = OUT.lower().endswith(".mov")
base_in = (["-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={round(FPS, 3)},format=rgba"] if ALPHA else ["-i", IN])
enc = (["-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16"]
       if ALPHA else ["-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "copy"])
proc = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error", *base_in, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{BAND_H}",
     "-r", str(round(FPS, 3)), "-i", "-", "-filter_complex",
     f"[0:v][1:v]overlay=0:{BAND_Y}:shortest=1,format={'yuva444p10le' if ALPHA else 'yuv420p'}[v]", *enc, OUT],
    stdin=subprocess.PIPE)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", IN],
                           capture_output=True, text=True).stdout)
blank, last = bytes(W * BAND_H * 4), None
for n in range(round(dur * FPS)):
    t = n / FPS
    pg = next((p for p in placed if p[0] <= t < p[1]), None)
    if not pg:
        proc.stdin.write(blank); continue
    state = tuple(min(1, round((t - s) / POP, 2)) for s, *_ in pg[2] if t >= s)
    if (pg[0], state) != last:
        band = Image.new("RGBA", (W, BAND_H), (0, 0, 0, 0))
        for (s, im, x, y), k in zip(pg[2], state):
            sc = 1.2 - 0.2 * (1 - (1 - k) ** 2)          # ease-out pop
            if sc != 1:
                im2 = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
                x, y, im = x - (im2.width - im.width) // 2, y - (im2.height - im.height) // 2, im2
            band.alpha_composite(im, (max(0, x), max(0, y)))
        last, frame = (pg[0], state), band.tobytes()
    proc.stdin.write(frame)
proc.stdin.close()
proc.wait()
print("done", OUT, proc.returncode)
