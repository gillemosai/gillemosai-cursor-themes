#!/usr/bin/env python3
"""Gera docs/resumo-behance.png: painel-resumo dos 5 temas (para Behance/portfólio).

Uso:  python3 src/make_behance.py [pasta_do_projeto]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_themes as mt  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

POPPINS_B = ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"] + mt.FONT_PATHS
POPPINS_M = ["/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"] + mt.FONT_PATHS
INTER = ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
INTER_B = ["/usr/share/fonts/opentype/inter/Inter-Bold.otf"] + mt.FONT_PATHS
MONO = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

CW, CH = 2800, 1900
ORANGE = (233, 84, 32)
INK = (240, 242, 248)
MUTED = (150, 158, 178)
CARD = (27, 31, 43)

SHOW = ["text", "pointer", "wait", "move", "help", "not-allowed", "grab", "zoom-in"]


def font(paths, px):
    return mt.load_font(px, paths)


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def cursor_img(cur, name, px, pixel, crop=False):
    im = cur[name][0][0]
    if crop:
        bb = im.getbbox()
        if bb:
            im = im.crop(bb)
    w, h = im.size
    s = px / max(w, h)
    return im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.NEAREST if pixel else Image.LANCZOS)


def gradient_bg():
    bg = Image.new("RGB", (CW, CH), (14, 16, 22))
    px = bg.load()
    for y in range(CH):
        t = y / CH
        c = (int(14 + 12 * t), int(16 + 12 * t), int(22 + 20 * t))
        for x in range(0, CW):
            px[x, y] = c
    d = ImageDraw.Draw(bg)
    for gx in range(60, CW, 60):          # grade de pontos sutil (clima "nerd")
        for gy in range(60, CH, 60):
            d.ellipse([gx - 1.5, gy - 1.5, gx + 1.5, gy + 1.5], fill=(34, 38, 52))
    return bg.convert("RGBA")


def rounded(img, box, r, fill):
    ImageDraw.Draw(img).rounded_rectangle(box, radius=r, fill=fill)


def main():
    allcur = mt.main()
    img = gradient_bg()
    d = ImageDraw.Draw(img)

    # ---------------------------------------------------------- cabeçalho
    d.text((110, 92), "GILLEMOSAI", font=font(INTER_B, 34), fill=ORANGE)
    d.text((110, 140), "Cursor Themes", font=font(POPPINS_B, 150), fill=INK)
    d.text((114, 330), "5 temas de cursor para Linux  ·  10 variantes  ·  22 cursores cada  ·  animações",
           font=font(INTER, 40), fill=MUTED)
    # selo 3x
    bx, by = CW - 800, 90
    rounded(img, (bx, by, CW - 110, by + 250), 34, (36, 22, 18))
    d.rounded_rectangle((bx, by, CW - 110, by + 250), radius=34, outline=ORANGE, width=4)
    d.text((bx + 60, by + 20), "3x", font=font(POPPINS_B, 150), fill=ORANGE)
    d.text((bx + 270, by + 62), "maior que o", font=font(INTER_B, 34), fill=INK)
    d.text((bx + 270, by + 106), "cursor tradicional", font=font(INTER_B, 34), fill=INK)
    d.text((bx + 270, by + 158), "72 px · até 128 px", font=font(INTER, 30), fill=MUTED)

    # ---------------------------------------------------------- cards
    n = len(mt.THEMES)
    gap, margin = 44, 110
    cw = (CW - 2 * margin - gap * (n - 1)) // n
    top, ch = 440, 1180
    for i, (key, cfg) in enumerate(mt.THEMES.items()):
        x0 = margin + i * (cw + gap)
        rounded(img, (x0, top, x0 + cw, top + ch), 36, CARD)
        vnames = list(cfg["variants"].keys())
        va, vb = cfg["variants"][vnames[0]], cfg["variants"][vnames[1]]
        acc = va["swatch"][1] if key != "base" else ORANGE
        d.rounded_rectangle((x0 + 36, top + 28, x0 + 36 + 90, top + 36), radius=4, fill=acc)

        # nome e descrição
        d.text((x0 + 36, top + 56), cfg["title"], font=font(POPPINS_B, 64), fill=INK)
        d.text((x0 + 36, top + 140), cfg["full"], font=font(INTER, 21), fill=MUTED)
        f = font(INTER, 28)
        ty = top + 186
        for ln in wrap(d, cfg["tagline"], f, cw - 72):
            d.text((x0 + 36, ty), ln, font=f, fill=(205, 210, 224))
            ty += 38

        # hero: seta nas duas variantes, lado a lado
        hy0, hh = top + 300, 330
        hw = (cw - 72) // 2
        for j, v in enumerate((va, vb)):
            hx0 = x0 + 36 + j * hw
            tile = Image.new("RGBA", (hw, hh), v["bg"] + (255,))
            cur = allcur[(key, vnames[j])]
            a = cursor_img(cur, "left_ptr", 168, cfg["pixel"], crop=True)
            if not cfg["pixel"] and v["style"].get("glow"):
                gl = Image.new("RGBA", tile.size, (0, 0, 0, 0))
                gl.alpha_composite(a, ((hw - a.width) // 2, (hh - a.height) // 2 - 10))
                tile.alpha_composite(gl.filter(ImageFilter.GaussianBlur(22)))
            tile.alpha_composite(a, ((hw - a.width) // 2, (hh - a.height) // 2 - 10))
            td = ImageDraw.Draw(tile)
            lum = 0.299 * v["bg"][0] + 0.587 * v["bg"][1] + 0.114 * v["bg"][2]
            td.text((hw // 2, hh - 30), vnames[j], font=font(INTER_B, 24),
                    fill=(40, 40, 44) if lum > 110 else (210, 214, 226), anchor="mm")
            mask = Image.new("L", tile.size, 0)
            r = 22
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, hw - 1, hh - 1), radius=r, fill=255)
            if j == 0:
                ImageDraw.Draw(mask).rectangle((hw // 2, 0, hw, hh), fill=255)
            else:
                ImageDraw.Draw(mask).rectangle((0, 0, hw // 2, hh), fill=255)
            img.paste(tile, (hx0, hy0), mask)

        # paleta
        sy = hy0 + hh + 28
        d.text((x0 + 36, sy + 4), "Paleta", font=font(INTER_B, 22), fill=MUTED)
        sx = x0 + 150
        for col in (va["swatch"] + [c for c in vb["swatch"] if c not in va["swatch"]]):
            d.ellipse((sx, sy, sx + 38, sy + 38), fill=tuple(col), outline=(90, 96, 116), width=2)
            sx += 50

        # grade de cursores (variante A)
        gy0 = sy + 78
        cols, cell = 4, (cw - 72) // 4
        d.rounded_rectangle((x0 + 36, gy0, x0 + cw - 36, gy0 + 2 * 128 + 12), radius=22, fill=va["bg"])
        cur = allcur[(key, vnames[0])]
        lum = 0.299 * va["bg"][0] + 0.587 * va["bg"][1] + 0.114 * va["bg"][2]
        for k, nm in enumerate(SHOW):
            cx = x0 + 36 + (k % cols) * cell + cell // 2
            cy = gy0 + 12 + (k // cols) * 128 + 50
            ci = cursor_img(cur, nm, 96, cfg["pixel"])
            img.alpha_composite(ci, (cx - ci.width // 2, cy - ci.height // 2))
            d.text((cx, cy + 62), nm, font=font(INTER, 16),
                   fill=(60, 60, 64) if lum > 110 else (170, 176, 194), anchor="mm")

        # variantes
        d.text((x0 + 36, top + ch - 62), "Variantes:  " + "  ·  ".join(vnames), font=font(INTER_B, 26), fill=INK)

    # ---------------------------------------------------------- rodapé
    fy = top + ch + 56
    rounded(img, (110, fy, CW - 110, fy + 170), 30, (24, 27, 38))
    d.text((160, fy + 28), "Instalação (Zorin OS, Ubuntu e GNOME)", font=font(INTER_B, 28), fill=MUTED)
    d.text((160, fy + 78), "./instalar.sh galaxy Blue 96", font=font(MONO, 48), fill=(120, 230, 160))
    d.text((CW - 160, fy + 38), "gillemosai.com", font=font(POPPINS_B, 74), fill=ORANGE, anchor="ra")
    d.text((CW - 160, fy + 136), "Download grátis no GitHub  ·  licença MIT", font=font(INTER, 28), fill=MUTED, anchor="ra")

    out = os.path.join(mt.DOCS, "resumo-behance.png")
    img.convert("RGB").save(out, optimize=True)
    print("ok", out, img.size)


if __name__ == "__main__":
    main()
