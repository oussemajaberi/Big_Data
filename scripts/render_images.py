#!/usr/bin/env python3
"""Génère des captures d'écran (PNG) style terminal / éditeur de code
à partir de texte réel, pour les insérer dans le rapport LaTeX.

Sortie : rapport/image/*.png
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join("rapport", "image")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FS = 26                      # taille de police
PAD = 28                     # marge interne
LINE = int(FS * 1.45)        # hauteur de ligne
TITLEBAR = 52                # hauteur de la barre de titre

font = ImageFont.truetype(FONT_PATH, FS)
font_bold = ImageFont.truetype(FONT_PATH, FS, index=1)
font_title = ImageFont.truetype(FONT_PATH, int(FS * 0.8))

# ── Thèmes ────────────────────────────────────────────────────────────────
TERM_BG = (30, 33, 39)
TERM_FG = (220, 223, 228)
TERM_GREEN = (126, 211, 33)
TERM_BLUE = (90, 169, 255)
TERM_YELLOW = (240, 200, 80)
TERM_CYAN = (90, 215, 220)
TERM_GREY = (130, 135, 145)

CODE_BG = (40, 44, 52)
CODE_FG = (200, 204, 212)
KW = (198, 120, 221)        # mots-clés violet
STR = (152, 195, 121)       # chaînes vert
COM = (110, 120, 135)       # commentaires gris
FUNC = (97, 175, 239)       # fonctions bleu
NUM = (209, 154, 102)       # nombres orange

KEYWORDS = {
    "from", "import", "as", "def", "return", "for", "in", "if", "else",
    "elif", "with", "True", "False", "None", "and", "or", "not", "class",
    "print", "lambda",
}


def char_w(f):
    bbox = f.getbbox("M")
    return bbox[2] - bbox[0]


def measure_width(lines, f):
    cw = char_w(f)
    maxlen = max((len(l) for l in lines), default=10)
    return maxlen, cw


def draw_window(lines, title, height_lines):
    cw = char_w(font)
    maxlen = max((len(re.sub(r"\033\[[0-9;]*m", "", l)) for l in lines), default=20)
    W = PAD * 2 + max(maxlen, len(title) + 6) * cw
    W = max(W, 760)
    H = TITLEBAR + PAD * 2 + height_lines * LINE
    return Image.new("RGB", (W, H), TERM_BG), W, H


def titlebar(img, draw, W, title, bg):
    draw.rectangle([0, 0, W, TITLEBAR], fill=(48, 52, 60) if bg == TERM_BG else (55, 60, 70))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 26 + i * 28
        draw.ellipse([cx - 8, TITLEBAR // 2 - 8, cx + 8, TITLEBAR // 2 + 8], fill=col)
    tb = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((W - (tb[2] - tb[0])) / 2, (TITLEBAR - (tb[3] - tb[1])) / 2 - tb[1]),
              title, font=font_title, fill=(190, 195, 205))


_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF✅❌⭐]",
    flags=re.UNICODE,
)


def strip_emoji(s):
    if not isinstance(s, str):
        return s
    if _EMOJI.search(s):                 # ligne avec emoji -> on nettoie le préfixe
        return _EMOJI.sub("", s).lstrip()
    return s


def render_terminal(name, lines, title="Terminal — bash"):
    """lines: liste de tuples (texte, couleur) ou str (couleur par défaut)."""
    norm = [(strip_emoji(l[0]), l[1]) if isinstance(l, tuple) else (strip_emoji(l), TERM_FG) for l in lines]
    plain = [t for t, _ in norm]
    img, W, H = draw_window(plain, title, len(norm))
    draw = ImageDraw.Draw(img)
    titlebar(img, draw, W, title, TERM_BG)
    y = TITLEBAR + PAD
    for text, col in norm:
        draw.text((PAD, y), text, font=font, fill=col)
        y += LINE
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    print("écrit", path, f"({W}x{H})")


def tokenize_code_line(line):
    """Retourne une liste de (segment, couleur) avec coloration syntaxique simple."""
    # Commentaire
    if "#" in line:
        # ne pas couper dans une chaîne (approche simple)
        idx = line.find("#")
        before, comment = line[:idx], line[idx:]
    else:
        before, comment = line, ""
    segments = []
    # chaînes
    parts = re.split(r'("[^"]*"|\'[^\']*\')', before)
    for part in parts:
        if not part:
            continue
        if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
            segments.append((part, STR))
        else:
            # mots
            for tok in re.split(r"(\W)", part):
                if not tok:
                    continue
                if tok in KEYWORDS:
                    segments.append((tok, KW))
                elif re.fullmatch(r"\d+(\.\d+)?", tok):
                    segments.append((tok, NUM))
                elif re.fullmatch(r"[A-Za-z_]\w*", tok):
                    segments.append((tok, CODE_FG))
                else:
                    segments.append((tok, CODE_FG))
    if comment:
        segments.append((comment, COM))
    return segments


def render_code(name, code, title="analyse_ventes.ipynb"):
    lines = code.split("\n")
    cw = char_w(font)
    maxlen = max((len(l) for l in lines), default=20)
    gutter = 4 * cw
    W = PAD * 2 + gutter + max(maxlen, len(title) + 6) * cw
    W = max(W, 820)
    H = TITLEBAR + PAD * 2 + len(lines) * LINE
    img = Image.new("RGB", (W, H), CODE_BG)
    draw = ImageDraw.Draw(img)
    titlebar(img, draw, W, title, CODE_BG)
    y = TITLEBAR + PAD
    for i, line in enumerate(lines, 1):
        draw.text((PAD, y), f"{i:>3}", font=font, fill=(95, 100, 110))
        x = PAD + gutter
        for seg, col in tokenize_code_line(line):
            draw.text((x, y), seg, font=font, fill=col)
            x += len(seg) * cw
        y += LINE
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    print("écrit", path, f"({W}x{H})")


if __name__ == "__main__":
    # Auto-test
    render_terminal("_demo.png", [("$ echo hello", TERM_GREEN), "hello"])
    render_code("_democode.png", 'def f(x):\n    return x + 1  # commentaire')
