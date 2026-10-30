#!/usr/bin/env python3
"""
Gillemosai Cursor Themes - gerador
https://gillemosai.com

Gera temas de cursor X11 (formato Xcursor) a partir de desenhos vetoriais
e empacota cada tema em dist/<Tema>.tar.gz, além das prévias em docs/.

Uso:  python3 src/make_themes.py [pasta_do_projeto]
"""
import math
import os
import shutil
import struct
import sys
import tarfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
DOCS = os.path.join(ROOT, "docs")

S = 8                 # supersampling: 64 unidades -> 512 px
W = 64 * S
SIZES_STD = [24, 48, 72, 96, 128]   # 72 = 3x o cursor tradicional (24 px)
SIZES_PIX = [24, 48, 72, 96, 120]   # múltiplos de 24 (pixels perfeitos)

FONT_PATHS = [
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def load_font(px, paths=None):
    for p in (paths or FONT_PATHS):
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


# ============================================================ geometria
def bez(p0, p1, p2, p3, n=28):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def rot(pts, deg, c=(32, 32)):
    t = math.radians(deg)
    out = []
    for x, y in pts:
        x -= c[0]
        y -= c[1]
        out.append((c[0] + x * math.cos(t) - y * math.sin(t),
                    c[1] + x * math.sin(t) + y * math.cos(t)))
    return out


# ============================================================ render
_stripes = None


def stripes():
    global _stripes
    if _stripes is None:
        m = Image.new("L", (W, W), 255)
        d = ImageDraw.Draw(m)
        y = 0.0
        while y < 64:
            d.rectangle([0, y * S, W, (y + 1.0) * S], fill=150)
            y += 2.6
        _stripes = m
    return _stripes


def solid(c):
    return Image.new("RGBA", (W, W), tuple(c) if len(c) == 4 else tuple(c) + (255,))


def quantize(lo, palette, athr=100):
    px = lo.load()
    for y in range(lo.height):
        for x in range(lo.width):
            r, g, b, a = px[x, y]
            if a < athr:
                px[x, y] = (0, 0, 0, 0)
                continue
            best = min(palette, key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2)
            px[x, y] = tuple(best[:3]) + (255,)
    return lo


def render(prims, st, details=(), arcs=(), glyph=None, bitmap=None):
    """Desenha as primitivas com contorno unificado, preenchimento e efeitos do estilo."""
    O = st["o"]
    pix = st.get("pixel")
    om, fm, am, dm, cm = (Image.new("L", (W, W), 0) for _ in range(5))
    do, df, da, dd, dc = (ImageDraw.Draw(m) for m in (om, fm, am, dm, cm))

    def P(pts):
        return [(x * S, y * S) for x, y in pts]

    def disc(d, cx, cy, r, v=255):
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=v)

    for p in prims:
        k = p[0]
        if k == "poly":
            pts = P(p[1])
            do.polygon(pts, fill=255)
            do.line(pts + [pts[0]], fill=255, width=int(2 * O * S), joint="curve")
            df.polygon(pts, fill=255)
        elif k == "line":
            pts, w = P(p[1]), (max(p[2], 4.4) if pix else p[2])
            do.line(pts, fill=255, width=int((w + 2 * O) * S), joint="curve")
            df.line(pts, fill=255, width=int(w * S), joint="curve")
            for (x, y) in p[1][:1] + p[1][-1:]:
                disc(do, x, y, w / 2 + O)
                disc(df, x, y, w / 2)
        elif k == "rrect":
            x0, y0, x1, y1, r = p[1:]
            do.rounded_rectangle([(x0 - O) * S, (y0 - O) * S, (x1 + O) * S, (y1 + O) * S],
                                 radius=(r + O) * S, fill=255)
            df.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=255)
        elif k == "ring":
            cx, cy, ro, ri = p[1:]
            disc(do, cx, cy, ro + O)
            disc(do, cx, cy, ri - O, 0)
            disc(df, cx, cy, ro)
            disc(df, cx, cy, ri, 0)
        elif k == "circle":
            cx, cy, r = p[1:]
            disc(do, cx, cy, r + O)
            disc(df, cx, cy, r)
        elif k == "aellipse":      # elipse preenchida com a cor de destaque
            cx, cy, rx, ry = p[1:]
            do.ellipse([(cx - rx - O) * S, (cy - ry - O) * S, (cx + rx + O) * S, (cy + ry + O) * S], fill=255)
            dc.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
        elif k == "acircle":       # círculo na cor de destaque (por cima do preenchimento)
            cx, cy, r = p[1:]
            disc(do, cx, cy, r + O)
            disc(dc, cx, cy, r)
    for d in details:              # linhas finas na cor de detalhe
        wd = max(d[1], 3.2) if pix else d[1]
        dd.line(P(d[0]), fill=255, width=int(wd * S), joint="curve")
        for (x, y) in d[0][:1] + d[0][-1:]:
            disc(dd, x, y, wd / 2)
    for a in arcs:                 # setores de anel (spinners), com transparência opcional
        cx, cy, ro, ri, a0, a1 = a[:6]
        alpha = a[6] if len(a) > 6 else 255
        tmp = Image.new("L", (W, W), 0)
        dt = ImageDraw.Draw(tmp)
        dt.pieslice([(cx - ro) * S, (cy - ro) * S, (cx + ro) * S, (cy + ro) * S], a0, a1, fill=255)
        dt.ellipse([(cx - ri) * S, (cy - ri) * S, (cx + ri) * S, (cy + ri) * S], fill=0)
        if alpha < 255:
            tmp = tmp.point(lambda v, al=alpha: v * al // 255)
        am = ImageChops.lighter(am, tmp)

    if pix:      # pixel art: cada camada vira pixels duros e a cor vem da camada (sem misturar cores)
        g = pix

        def lo(m, thr):
            return m.resize((g, g), Image.BOX).point(lambda v: 255 if v >= thr * 255 else 0)

        out = Image.new("RGBA", (g, g), (0, 0, 0, 0))

        def put(m, color):
            out.paste(Image.new("RGBA", (g, g), tuple(color[:3]) + (255,)), (0, 0), m)

        put(lo(om, 0.25), st["outline"])
        put(lo(fm, 0.5), st["fill"])
        put(ImageChops.lighter(lo(cm, 0.5), lo(am, 0.5)), st["accent"])
        put(lo(dm, 0.45), st.get("detail", st["accent"]))
        if glyph:
            text, cx, cy, size = glyph
            font = load_font(int(size * S))
            gf = Image.new("L", (W, W), 0)
            go = Image.new("L", (W, W), 0)
            ImageDraw.Draw(gf).text((cx * S, cy * S), text, font=font, fill=255, anchor="mm")
            ImageDraw.Draw(go).text((cx * S, cy * S), text, font=font, fill=255, anchor="mm",
                                    stroke_width=int(2.2 * S), stroke_fill=255)
            put(lo(go, 0.3), st["outline"])
            put(lo(gf, 0.5), st["fill"])
        if bitmap:
            rows, bx, by = bitmap
            px = out.load()
            colors = {"#": st["outline"], "o": st["fill"], "a": st["accent"]}
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch in colors and 0 <= bx + x < g and 0 <= by + y < g:
                        px[bx + x, by + y] = tuple(colors[ch][:3]) + (255,)
        return out

    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    if st.get("glow"):
        gc, gr, gs = st["glow"]
        g = om.filter(ImageFilter.GaussianBlur(gr * S)).point(lambda v: min(255, int(v * gs)))
        img.paste(solid(gc), (0, 0), g)
    img.paste(solid(st["outline"]), (0, 0), ImageChops.subtract(om, fm))
    fmm = ImageChops.multiply(fm, stripes()) if st.get("scan") else fm
    fa = st["fill"][3] if len(st["fill"]) == 4 else 255
    if fa < 255:
        fmm = fmm.point(lambda v: v * fa // 255)
    img.paste(solid(st["fill"][:3]), (0, 0), fmm)
    img.paste(solid(st["accent"]), (0, 0), cm)
    img.paste(solid(st.get("detail", st["accent"])), (0, 0), dm)
    img.paste(solid(st["accent"]), (0, 0), am)
    if glyph:
        text, cx, cy, size = glyph
        ImageDraw.Draw(img).text((cx * S, cy * S), text, font=load_font(int(size * S)),
                                 fill=st.get("glyph", st["fill"][:3]),
                                 stroke_width=int(1.5 * S), stroke_fill=st["outline"], anchor="mm")

    return img


# ============================================================ cursores comuns
def double_arrow(deg):
    return [("line", rot([(32, 16), (32, 48)], deg), 2.6),
            ("poly", rot([(32, 5), (24, 17), (40, 17)], deg)),
            ("poly", rot([(32, 59), (24, 47), (40, 47)], deg))]


def hand_point():
    return ([("rrect", 24, 5, 33, 36, 4.5), ("rrect", 15, 28, 49, 55, 8), ("rrect", 9, 33, 20, 47, 4.5)],
            [([(33.5, 30), (33.5, 38)], 1.3), ([(41, 32), (41, 40)], 1.3)])


def hand_open():
    return ([("rrect", 16, 26, 48, 54, 8), ("rrect", 16, 10, 24.5, 32, 4), ("rrect", 25, 6, 33.5, 32, 4),
             ("rrect", 34, 8, 42.5, 32, 4), ("rrect", 43, 13, 51, 34, 4), ("rrect", 9, 34, 20, 47, 4.5)],
            [([(24.7, 16), (24.7, 28)], 1.3), ([(33.7, 12), (33.7, 28)], 1.3), ([(42.7, 15), (42.7, 29)], 1.3)])


def hand_closed():
    return ([("rrect", 16, 24, 50, 54, 9), ("rrect", 16, 19, 26, 32, 5), ("rrect", 26, 17, 36, 30, 5),
             ("rrect", 36, 18, 46, 31, 5), ("rrect", 45, 21, 52, 34, 4.5), ("rrect", 9, 34, 20, 47, 4.5)],
            [([(26.2, 24), (26.2, 32)], 1.3), ([(36.2, 22), (36.2, 31)], 1.3), ([(45.5, 25), (45.5, 33)], 1.3)])


# ============================================================ setas por tema
def arrow_base():
    A, BL, R = (14, 6), (12, 48), (41, 38)
    # borda de baixo côncava (curva para dentro), como no conceito
    return dict(prims=[("poly", [A, R] + bez(R, (30, 39.5), (19, 43.5), BL)[1:])], hot=A, details=[])


# --- frota original do tema Galaxy (silhuetas minhas; nariz na origem, corpo para +y)
SHIPS = {
    "fighter": dict(L=36, cock=(0, 15), eng=[(-1.8, 37.2), (1.8, 37.2)],
                    body=[(0, 0), (2.4, 7), (3.4, 15), (13, 27), (13.5, 31), (5, 28), (3, 36), (-3, 36), (-5, 28),
                          (-13.5, 31), (-13, 27), (-3.4, 15), (-2.4, 7)]),
    "hauler": dict(L=30, cock=(0, 7), eng=[(-3, 29.8), (0, 29.8), (3, 29.8)],
                   body=[(-4, 0), (4, 0), (6.5, 6), (7, 22), (5, 28), (-5, 28), (-7, 22), (-6.5, 6)]),
    "scout": dict(L=34, cock=(0, 13), eng=[(-1.2, 35), (1.2, 35)],
                  body=[(0, 0), (3, 8), (3.4, 18), (9, 28), (9, 31), (2.6, 27), (2.2, 34), (-2.2, 34), (-2.6, 27),
                        (-9, 31), (-9, 28), (-3.4, 18), (-3, 8)]),
}


def ship_prims(kind, origin, deg, k, centered):
    s = SHIPS[kind]
    sh = (0, s["L"] / 2) if centered else (0, 0)

    def T(pts):
        r = rot([((x - sh[0]) * k, (y - sh[1]) * k) for x, y in pts], deg, (0, 0))
        return [(origin[0] + x, origin[1] + y) for x, y in r]

    prims = [("poly", T(s["body"]))]
    for e in s["eng"]:                           # chamas das turbinas
        ex, ey = T([e])[0]
        prims.append(("acircle", ex, ey, max(0.9, 1.5 * k)))
    cx, cy = T([s["cock"]])[0]                   # cabine
    prims.append(("acircle", cx, cy, max(0.9, 1.7 * k)))
    return prims


def robot_head(cx, cy, s):
    """Robozinho original: cabeça arredondada, antena, olhos e boca."""
    prims = [("line", [(cx, cy - 8.5 * s), (cx, cy - 12.5 * s)], 1.5 * s + 0.4),
             ("acircle", cx, cy - 13.8 * s, 1.9 * s),
             ("rrect", cx - 13.2 * s, cy - 3.2 * s, cx - 9 * s, cy + 3.2 * s, 1.4 * s),
             ("rrect", cx + 9 * s, cy - 3.2 * s, cx + 13.2 * s, cy + 3.2 * s, 1.4 * s),
             ("rrect", cx - 10.5 * s, cy - 8.5 * s, cx + 10.5 * s, cy + 8.5 * s, 4.2 * s),
             ("acircle", cx - 4.3 * s, cy - 1.2 * s, 2.1 * s),
             ("acircle", cx + 4.3 * s, cy - 1.2 * s, 2.1 * s)]
    details = [([(cx - 4 * s, cy + 4.6 * s), (cx + 4 * s, cy + 4.6 * s)], max(1.1, 1.3 * s))]
    return prims, details


def arrow_galaxy():
    """O ponteiro é um caça estelar original: o nariz é a ponta (hotspot)."""
    tip, k, deg = (8, 6), 1.05, -45
    prims = ship_prims("fighter", tip, deg, k, False)

    def T(pts):
        return [(tip[0] + x, tip[1] + y) for x, y in rot([(a * k, b * k) for a, b in pts], deg, (0, 0))]

    flames = [(T([(ex, 38.4), (ex, 46)]), 1.3) for ex in (-1.8, 1.8)]
    return dict(prims=prims, hot=tip, details=flames)


def arrow_hologram():
    A = (14, 6)
    inner = [(19.5, 17), (19.5, 39), (32.5, 33), (19.5, 17)]
    return dict(prims=[("poly", [A, (14, 51), (41, 36)])], hot=A, details=[(inner, 1.1)])


def arrow_ninja():
    tip, k = (7, 5), 1.2

    def T(pts):
        return [(tip[0] + x, tip[1] + y) for x, y in rot([(a * k, b * k) for a, b in pts], -45, (0, 0))]

    # lâmina em folha (larga), guarda, cabo com fitas e anel
    blade = [(0, 0), (4.2, 8), (6.4, 15), (5.4, 21), (3.0, 26), (-3.0, 26), (-5.4, 21), (-6.4, 15), (-4.2, 8)]
    handle = [(2.7, 25), (2.7, 34.5), (-2.7, 34.5), (-2.7, 25)]
    guard = [(-5.8, 25), (5.8, 25), (5.8, 28.4), (-5.8, 28.4)]
    cx, cy = T([(0, 39)])[0]
    wraps = [(T([(-2.7, y), (2.7, y)]), 1.5) for y in (30.5, 33.3)]
    spine = [(T([(0, 6), (0, 22)]), 1.0)]
    return dict(prims=[("ring", cx, cy, 4.7 * k, 2.3 * k), ("poly", T(blade)), ("poly", T(handle)),
                       ("poly", T(guard))], hot=tip, details=wraps + spine)


PIX_ARROW = [
    "#...........",
    "##..........",
    "#o#.........",
    "#oo#........",
    "#ooo#.......",
    "#oooo#......",
    "#ooooo#.....",
    "#oooooo#....",
    "#ooooooo#...",
    "#oooooooo#..",
    "#ooooooooo#.",
    "#ooooo######",
    "#oo#oo#.....",
    "#o#.#aa#....",
    "##..#aa#....",
    "#....#aa#...",
    ".....#aa#...",
    "......##....",
]


def arrow_pixel():
    bx, by = 2, 1
    return dict(prims=[], hot=(bx * 64 / 24, by * 64 / 24), details=[], bitmap=(PIX_ARROW, bx, by))


# ============================================================ loaders por tema
def star(cx, cy, ro, ri, deg, n=4):
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = math.radians(deg + i * 180 / n - 90)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def orbit_ship(kind, cx, cy, R, th, k):
    """Nave da frota orbitando (cx,cy), com o nariz apontado no sentido do movimento."""
    px, py = cx + R * math.cos(math.radians(th)), cy + R * math.sin(math.radians(th))
    return ship_prims(kind, (px, py), th + 180, k, True)


def trail(cx, cy, R, th, half, w=2.2):
    """Rastro de propulsão que some atrás da nave (começa depois da cauda dela)."""
    gap = (half + 1.0) / R * 57.3
    step = 12 * 19.5 / R
    arcs = []
    for j in range(6):
        a1 = th - gap - step * j
        arcs.append((cx, cy, R + w, R - w, a1 - step, a1, int(235 * (0.7 ** j))))
    return arcs


def loader_frames(theme, st, arrow, nf):
    """Retorna (frames_wait, frames_progress)."""
    theme = theme.lower()
    wait, prog = [], []
    A = arrow
    for i in range(nf):
        t = i / nf
        if theme == "base":
            a0 = t * 360
            wait.append(render([("ring", 32, 32, 22, 12)], st, arcs=[(32, 32, 22, 12, a0, a0 + 110)]))
            prog.append(render(A["prims"] + [("ring", 49, 49, 11.5, 6)], st, A["details"],
                               arcs=[(49, 49, 11.5, 6, a0, a0 + 110)]))
        elif theme == "galaxy":
            a0 = t * 360
            # robô no centro, frota de 3 naves originais em órbita (com rastro) e estrelas
            rp, rd = robot_head(32, 34, 0.8)
            prims = list(rp) + [("acircle", x, y, r) for x, y, r in
                                [(6.5, 7, 1.2), (57.5, 8, 1.0), (7, 57, 1.0), (57, 57.5, 1.3)]]
            arcs = []
            for j, (kind, k) in enumerate([("fighter", 0.6), ("hauler", 0.66), ("scout", 0.62)]):
                th = a0 + 120 * j
                prims += orbit_ship(kind, 32, 32, 22, th, k)
                arcs += trail(32, 32, 22, th, SHIPS[kind]["L"] / 2 * k, 1.7)
            wait.append(render(prims, st, rd, arcs=arcs))
            prog.append(render(A["prims"] + [("circle", 49.5, 49.5, 2.8)] + orbit_ship("scout", 49.5, 49.5, 8, a0, 0.36),
                               st, A["details"], arcs=trail(49.5, 49.5, 8, a0, 17 * 0.36, 1.3)))
        elif theme == "hologram":
            a0 = t * 360
            sweep = [(32, 32, 23, 3, a0 - 18 * (j + 1), a0 - 18 * j, int(255 * (0.85 ** j) * (1 - j * 0.16)))
                     for j in range(5)]
            cross = [([(32, 9), (32, 55)], 0.9), ([(9, 32), (55, 32)], 0.9)]
            wait.append(render([("ring", 32, 32, 24, 21.5), ("ring", 32, 32, 12, 10)], st, cross, arcs=sweep))
            small = [(49, 49, 11.5, 2, a0 - 20 * (j + 1), a0 - 20 * j, int(255 * (0.8 ** j))) for j in range(4)]
            prog.append(render(A["prims"] + [("ring", 49, 49, 11.5, 9.5)], st, A["details"], arcs=small))
        elif theme == "ninja":
            deg = t * 90
            wait.append(render([("poly", star(32, 32, 25, 8, deg)), ("acircle", 32, 32, 4.4)], st))
            prog.append(render(A["prims"] + [("poly", star(51, 51, 12, 4, deg)), ("acircle", 51, 51, 2.4)],
                               st, A["details"]))
        elif theme == "pixel8":
            ang = t * 2 * math.pi
            rx = max(2.2, 17 * abs(math.cos(ang)))
            slot = [([(32, 24), (32, 40)], 3.4)] if rx > 9 else []
            wait.append(render([("aellipse", 32, 32, rx, 21)], st, slot))
            rs = max(1.4, 8.5 * abs(math.cos(ang)))
            prog.append(render([("aellipse", 51, 51, rs, 10)], st, [], bitmap=A["bitmap"]))
    return wait, prog


# ============================================================ construção do tema
def build(theme, cfg, st):
    c = {}
    A = cfg["arrow"]()
    bm = A.get("bitmap")
    ap, ad, hot = A["prims"], A["details"], A["hot"]

    def R(prims, details=(), **kw):          # cursores sem a seta
        return render(prims, st, details, **kw)

    def RA(extra=(), details=(), **kw):      # cursores que levam a seta
        return render(ap + list(extra), st, list(ad) + list(details), bitmap=bm, **kw)

    c["left_ptr"] = ([RA()], hot)
    c["text"] = ([R([("line", [(32, 10), (32, 54)], 3.0), ("line", [(25, 10), (39, 10)], 3.0),
                     ("line", [(25, 54), (39, 54)], 3.0)])], (32, 32))
    c["vertical-text"] = ([R([("line", rot([(32, 10), (32, 54)], 90), 3.0),
                              ("line", rot([(25, 10), (39, 10)], 90), 3.0),
                              ("line", rot([(25, 54), (39, 54)], 90), 3.0)])], (32, 32))
    if cfg.get("beams"):          # feixes de energia com pontas arredondadas
        c["text"] = ([R([("line", [(32, 9), (32, 55)], 3.4), ("circle", 32, 9, 3.8), ("circle", 32, 55, 3.8)])],
                     (32, 32))
        c["vertical-text"] = ([R([("line", [(9, 32), (55, 32)], 3.4), ("circle", 9, 32, 3.8),
                                  ("circle", 55, 32, 3.8)])], (32, 32))
    pr, det = hand_point()
    c["pointer"] = ([R(pr, det)], (28.5, 5))
    pr, det = hand_open()
    c["grab"] = ([R(pr, det)], (32, 32))
    pr, det = hand_closed()
    c["grabbing"] = ([R(pr, det)], (32, 32))
    c["crosshair"] = ([R([("line", [(32, 8), (32, 27)], 2.6), ("line", [(32, 37), (32, 56)], 2.6),
                          ("line", [(8, 32), (27, 32)], 2.6), ("line", [(37, 32), (56, 32)], 2.6)])], (32, 32))
    c["cell"] = ([R([("line", [(32, 10), (32, 54)], 5.5), ("line", [(10, 32), (54, 32)], 5.5)])], (32, 32))
    c["move"] = ([R([("line", [(32, 12), (32, 52)], 2.6), ("line", [(12, 32), (52, 32)], 2.6),
                     ("poly", [(32, 4), (24, 15), (40, 15)]), ("poly", [(32, 60), (24, 49), (40, 49)]),
                     ("poly", [(4, 32), (15, 24), (15, 40)]), ("poly", [(60, 32), (49, 24), (49, 40)])])], (32, 32))
    c["ns-resize"] = ([R(double_arrow(0))], (32, 32))
    c["ew-resize"] = ([R(double_arrow(90))], (32, 32))
    c["nesw-resize"] = ([R(double_arrow(45))], (32, 32))
    c["nwse-resize"] = ([R(double_arrow(-45))], (32, 32))
    c["not-allowed"] = ([R([("ring", 32, 32, 23, 16), ("line", [(19, 45), (45, 19)], 5.0)])], (32, 32))
    if cfg.get("robot_help"):
        rb, rdt = robot_head(51.5, 52, 0.78)
        c["help"] = ([RA(rb, rdt)], hot)
    else:
        c["help"] = ([RA(glyph=("?", 52, 51, 24))], hot)
    c["copy"] = ([RA([("line", [(51, 44), (51, 58)], 4.4), ("line", [(44, 51), (58, 51)], 4.4)])], hot)
    c["alias"] = ([RA([("line", [(43, 58), (43, 50), (50, 50)], 3.4), ("poly", [(58, 50), (50, 43), (50, 57)])])], hot)
    c["context-menu"] = ([RA([("rrect", 43, 43, 61, 61, 3.5)],
                             [([(47.5, 49), (56.5, 49)], 1.4), ([(47.5, 53), (56.5, 53)], 1.4),
                              ([(47.5, 57), (56.5, 57)], 1.4)])], hot)
    zi = [("ring", 27, 27, 18, 11), ("line", [(41, 41), (56, 56)], 6.0)]
    c["zoom-in"] = ([R(zi, [([(27, 21), (27, 33)], 2.2), ([(21, 27), (33, 27)], 2.2)])], (27, 27))
    c["zoom-out"] = ([R(zi, [([(21, 27), (33, 27)], 2.2)])], (27, 27))

    wait, prog = loader_frames(theme, st, A, cfg["frames"])
    c["wait"] = (wait, (32, 32))
    c["progress"] = (prog, hot)
    return c


# ============================================================ Xcursor
def write_xcursor(path, frames, hot, sizes, delay, pixel):
    chunks = []
    for size in sizes:
        hx = min(size - 1, max(0, round(hot[0] * size / 64)))
        hy = min(size - 1, max(0, round(hot[1] * size / 64)))
        for fr in frames:
            im = fr.resize((size, size), Image.NEAREST if pixel else Image.LANCZOS).convert("RGBa")
            r, g, b, a = im.split()
            raw = Image.merge("RGBA", (b, g, r, a)).tobytes()   # ARGB little-endian, pré-multiplicado
            hdr = struct.pack("<9I", 36, 0xFFFD0002, size, 1, size, size, hx, hy,
                              delay if len(frames) > 1 else 0)
            chunks.append((size, hdr + raw))
    n = len(chunks)
    pos = 16 + 12 * n
    toc, body = b"", b""
    for size, data in chunks:
        toc += struct.pack("<3I", 0xFFFD0002, size, pos + len(body))
        body += data
    with open(path, "wb") as f:
        f.write(struct.pack("<4s3I", b"Xcur", 16, 0x10000, n) + toc + body)


ALIASES = {
    "left_ptr": ["default", "arrow", "top_left_arrow", "right_ptr", "dnd-none", "draft_large", "draft_small"],
    "text": ["xterm", "ibeam"],
    "pointer": ["hand1", "hand2", "pointing_hand", "e29285e634086352946a0e7090d73106",
                "9d800788f1b08800ae810202380a0822"],
    "wait": ["watch"],
    "progress": ["left_ptr_watch", "half-busy", "00000000000000020006000e7e9ffc3f",
                 "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross"],
    "cell": ["plus"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "d9ce0ab605698f320427677b458ad60b",
             "5c6cd98b3f3ebcb1f9c7f1c204630408"],
    "not-allowed": ["crossed_circle", "forbidden", "no-drop", "dnd-no-drop", "circle",
                    "03b6e0fcb3499374a867c041f52298f0"],
    "move": ["fleur", "all-scroll", "size_all", "9081237383d90e509aa00f00170e968f",
             "4498f0e0c1937ffe01fd06f973665830"],
    "grab": ["openhand"],
    "grabbing": ["closedhand", "dnd-move"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872"],
    "alias": ["link", "dnd-link", "a2a266d0498c3104214a47bd64ab0fc8", "640fb0e74195791501fd1ed57b41487f"],
    "zoom-in": ["zoom_in"],
    "zoom-out": ["zoom_out"],
    "ns-resize": ["size_ver", "v_double_arrow", "sb_v_double_arrow", "row-resize", "split_v", "n-resize",
                  "s-resize", "top_side", "bottom_side", "00008160000006810000408080010102",
                  "2870a09082c103050810ffdffffe0204"],
    "ew-resize": ["size_hor", "h_double_arrow", "sb_h_double_arrow", "col-resize", "split_h", "e-resize",
                  "w-resize", "left_side", "right_side", "14fef782d02440884392942c11205230",
                  "028006030e0e7ebffc7f7070c0600140"],
    "nesw-resize": ["size_bdiag", "fd_double_arrow", "ne-resize", "sw-resize", "top_right_corner",
                    "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "nwse-resize": ["size_fdiag", "bd_double_arrow", "nw-resize", "se-resize", "top_left_corner",
                    "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
}


def write_theme(dirname, comment, cur, sizes, delay, pixel):
    root = os.path.join(BUILD, dirname)
    cdir = os.path.join(root, "cursors")
    os.makedirs(cdir, exist_ok=True)
    for base, (frames, hot) in cur.items():
        write_xcursor(os.path.join(cdir, base), frames, hot, sizes, delay, pixel)
        for al in ALIASES.get(base, []):
            dst = os.path.join(cdir, al)
            if os.path.lexists(dst):
                os.remove(dst)
            os.symlink(base, dst)
    with open(os.path.join(root, "index.theme"), "w") as f:
        f.write(f"[Icon Theme]\nName={dirname}\nComment={comment} - https://gillemosai.com\nInherits=Adwaita\n")


# ============================================================ estilos e catálogo
def st(fill, outline, accent, o=1.6, **kw):
    d = dict(fill=fill, outline=outline, accent=accent, o=o)
    d.update(kw)
    return d


ORANGE = (233, 84, 32)

THEMES = {
    "base": dict(
        full="Gillemosai_Cursor_base",
        title="Base", tagline="Seta delta com contorno laranja",
        arrow=arrow_base, sizes=SIZES_STD, frames=12, delay=70, pixel=False,
        variants={
            "Dark": dict(style=st((255, 255, 255, 255), ORANGE, ORANGE), bg=(36, 36, 38), swatch=[(255, 255, 255), ORANGE]),
            "Light": dict(style=st((28, 28, 30, 255), ORANGE, ORANGE), bg=(226, 226, 228), swatch=[(28, 28, 30), ORANGE]),
        }),
    "Pixel8": dict(
        full="Gillemosai_Cursor_Pixel8",
        title="Pixel8", tagline="Clima de plataforma retrô em 8 bits",
        arrow=arrow_pixel, sizes=SIZES_PIX, frames=8, delay=90, pixel=True,
        variants={
            "White": dict(style=st((255, 255, 255, 255), (20, 20, 30), (252, 196, 25), o=2.4, pixel=24, detail=(20, 20, 30)),
                          bg=(88, 140, 230), swatch=[(255, 255, 255), (252, 196, 25), (20, 20, 30)]),
            "Mint": dict(style=st((120, 255, 170, 255), (20, 20, 30), (252, 196, 25), o=2.4, pixel=24, detail=(20, 20, 30)),
                         bg=(40, 36, 64), swatch=[(120, 255, 170), (252, 196, 25), (20, 20, 30)]),
        }),
    "Galaxy": dict(
        full="Gillemosai_Cursor_Galaxy",
        title="Galaxy", tagline="Caça estelar de ponteiro, robô e frota original",
        arrow=arrow_galaxy, sizes=SIZES_STD, frames=24, delay=40, pixel=False, beams=True, robot_help=True,
        variants={
            "Blue": dict(style=st((236, 248, 255, 255), (70, 165, 255), (140, 210, 255), o=1.5,
                                  glow=((50, 140, 255), 2.4, 1.5), detail=(70, 165, 255)),
                         bg=(10, 12, 28), swatch=[(70, 165, 255), (236, 248, 255), (10, 12, 28)]),
            "Red": dict(style=st((255, 240, 240, 255), (255, 70, 70), (255, 140, 120), o=1.5,
                                 glow=((255, 40, 40), 2.4, 1.5), detail=(255, 70, 70)),
                        bg=(22, 8, 12), swatch=[(255, 70, 70), (255, 240, 240), (22, 8, 12)]),
        }),
    "Hologram": dict(
        full="Gillemosai_Cursor_Hologram",
        title="Hologram", tagline="Painel holográfico de exploração espacial",
        arrow=arrow_hologram, sizes=SIZES_STD, frames=24, delay=45, pixel=False,
        variants={
            "Cyan": dict(style=st((0, 215, 245, 105), (60, 240, 255), (150, 255, 255), o=1.4, scan=True,
                                  glow=((0, 210, 255), 2.2, 1.3), detail=(150, 255, 255), glyph=(150, 255, 255)),
                         bg=(6, 18, 30), swatch=[(60, 240, 255), (150, 255, 255), (6, 18, 30)]),
            "Amber": dict(style=st((255, 175, 0, 105), (255, 200, 70), (255, 230, 150), o=1.4, scan=True,
                                   glow=((255, 170, 0), 2.2, 1.3), detail=(255, 230, 150), glyph=(255, 230, 150)),
                          bg=(26, 16, 6), swatch=[(255, 200, 70), (255, 230, 150), (26, 16, 6)]),
        }),
    "Ninja": dict(
        full="Gillemosai_Cursor_Ninja",
        title="Ninja", tagline="Kunai e shuriken em aço e laranja",
        arrow=arrow_ninja, sizes=SIZES_STD, frames=8, delay=55, pixel=False,
        variants={
            "Orange": dict(style=st((214, 221, 232, 255), (22, 26, 38), (255, 122, 26), o=1.7, detail=(255, 122, 26)),
                           bg=(60, 66, 82), swatch=[(214, 221, 232), (255, 122, 26), (22, 26, 38)]),
            "Blue": dict(style=st((214, 221, 232, 255), (22, 26, 38), (46, 140, 255), o=1.7, detail=(46, 140, 255)),
                         bg=(60, 66, 82), swatch=[(214, 221, 232), (46, 140, 255), (22, 26, 38)]),
        }),
}

PREVIEW_ORDER = ["left_ptr", "text", "pointer", "progress", "wait", "help", "not-allowed", "move", "ns-resize",
                 "ew-resize", "nesw-resize", "nwse-resize", "grab", "grabbing", "copy", "alias", "crosshair",
                 "zoom-in"]


def preview_sheet(items, path, cols=9, cell=96):
    """items: lista de (rótulo, cursores, cor_de_fundo, é_pixel)."""
    rows = math.ceil(len(PREVIEW_ORDER) / cols)
    block = rows * cell + 28
    sheet = Image.new("RGB", (cols * cell, block * len(items)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    f = load_font(11)
    fb = load_font(13)
    for bi, (label, cur, bg, pix) in enumerate(items):
        y0 = bi * block
        d.rectangle([0, y0, cols * cell, y0 + block], fill=bg)
        lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
        tc = (40, 40, 40) if lum > 140 else (205, 205, 205)
        d.text((10, y0 + 8), label, font=fb, fill=tc)
        for i, name in enumerate(PREVIEW_ORDER):
            x, y = (i % cols) * cell, y0 + 24 + (i // cols) * cell
            im = cur[name][0][0].resize((64, 64), Image.NEAREST if pix else Image.LANCZOS)
            tile = Image.new("RGBA", (64, 64), bg + (255,))
            tile.alpha_composite(im)
            sheet.paste(tile.convert("RGB"), (x + 16, y + 6))
            d.text((x + cell // 2, y + 82), name, font=f, fill=tc, anchor="mm")
    sheet.save(path)


def main(only=None):
    shutil.rmtree(BUILD, ignore_errors=True)
    os.makedirs(BUILD)
    os.makedirs(DIST, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    allcur = {}
    for key, cfg in THEMES.items():
        if only and key not in only:
            continue
        items, dirs = [], []
        for vname, v in cfg["variants"].items():
            cur = build(key, cfg, v["style"])
            dirname = f"{cfg['full']}-{vname}"
            write_theme(dirname, f"{cfg['title']} ({vname}): {cfg['tagline']}", cur, cfg["sizes"], cfg["delay"],
                        cfg["pixel"])
            dirs.append(dirname)
            allcur[(key, vname)] = cur
            items.append((f"{cfg['full']}-{vname}", cur, v["bg"], cfg["pixel"]))
        preview_sheet(items, os.path.join(DOCS, f"preview-{key}.png"))
        tar = os.path.join(DIST, f"{cfg['full']}.tar.gz")
        with tarfile.open(tar, "w:gz") as t:
            for dn in dirs:
                t.add(os.path.join(BUILD, dn), arcname=dn)
        print("ok", key, os.path.getsize(tar) // 1024, "KB")
    return allcur


if __name__ == "__main__":
    main(only=sys.argv[2].split(",") if len(sys.argv) > 2 else None)
