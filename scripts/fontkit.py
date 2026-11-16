"""Find a font by file name on any computer; fall back to a free look-alike shipped in ../fonts/.
Search order: $SUBTITLE_FONTS (any folder you point it at), the skill's fonts/, then the usual Windows / macOS / Linux
font folders. Licensed fonts (SF Pro, Helvetica Neue) are never shipped: each person installs their own copy or gets
Inter (free) instead, with a one-line warning.
"""
import os
from PIL import ImageFont

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = [os.environ.get("SUBTITLE_FONTS", ""), os.path.join(SKILL, "fonts"),
        os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts"), "C:/Windows/Fonts",
        os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts",
        os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/.fonts"), "/usr/share/fonts"]
# licensed / system font -> (free file in fonts/, weight)
FALLBACK = {
    "SF-Pro-Display-Medium.otf": ("Inter[opsz,wght].ttf", 500),
    "SF-Pro-Display-Semibold.ttf": ("Inter[opsz,wght].ttf", 600),
    "SF-Pro-Display-Bold.otf": ("Inter[opsz,wght].ttf", 700),
    "SF-Pro-Display-SemiboldItalic.otf": ("Inter-Italic[opsz,wght].ttf", 600),
    "HelveticaNeueMedium.otf": ("Inter[opsz,wght].ttf", 500),
    "HelveticaNeueBold.otf": ("Inter[opsz,wght].ttf", 700),
    "PlayfairDisplay-Bold.ttf": ("PlayfairDisplay[wght].ttf", 700),
}
_warned = set()


def find(name):
    for d in DIRS:
        if not d:
            continue
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
        for root, _, files in os.walk(d) if d.startswith(("/usr", os.path.expanduser("~/.local"))) else ():
            if name in files:
                return os.path.join(root, name)
    return None


def font(name, size, wght=None):
    """ImageFont for `name` (a file name like "SF-Pro-Display-Bold.otf"); `wght` sets a variable font's weight."""
    p = find(name)
    if not p:
        if name not in FALLBACK:
            raise FileNotFoundError(f"font {name} not found; put it in {os.path.join(SKILL, 'fonts')} or set SUBTITLE_FONTS")
        alt, wght = FALLBACK[name]
        if name not in _warned:
            print(f"[fonts] {name} not installed -> using free look-alike {alt} (install it, or set SUBTITLE_FONTS)")
            _warned.add(name)
        p = os.path.join(SKILL, "fonts", alt)
    f = ImageFont.truetype(p, size)
    if wght:
        try:
            f.set_variation_by_axes([wght if a["name"] in (b"Weight", "Weight") else a["default"]
                                     for a in f.get_variation_axes()])
        except OSError:
            pass                        # not a variable font: the file already has its weight
    return f


if __name__ == "__main__":              # setup check: python scripts/fontkit.py
    import shutil
    for n in FALLBACK:
        print(("ok      " if find(n) else "MISSING ") + n + ("" if find(n) else f"  -> will use {FALLBACK[n][0]}"))
    for tool in ("ffmpeg", "ffprobe"):
        print(("ok      " if shutil.which(tool) else "MISSING ") + tool)
