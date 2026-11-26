"""Large pixel-art murals (48 x 40) for the Class Mystery Mural, drawn square by square in code.

Each function returns a design dict like designs.py: {"title", "colors", "rows"}.
"""
import math

W, H = 48, 40


def _canvas(fill="."):
    return [[fill] * W for _ in range(H)]


def _put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def _rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            _put(g, x, y, c)


def _disc(g, cx, cy, r, c):
    for y in range(H):
        for x in range(W):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r * 0.6:
                g[y][x] = c


def _pine(g, cx, top, height):
    """Triangle pine with three notched tiers and snow on the left edges."""
    for k in range(height):
        tier_start = (k // 4) * 4
        half = 1 + (k - tier_start) + (k // 4)
        for x in range(cx - half, cx + half + 1):
            _put(g, x, top + k, "g" if x <= cx else "G")
        if (k - tier_start) == 3 or k == 0:
            _put(g, cx - half, top + k, "W")
            _put(g, cx - half + 1, top + k, "W")
    _rect(g, cx - 1, top + height, cx, top + height + 1, "N")


def _ring(g, cx, cy, r, c, fill):
    """Disc of `fill` with a one-square outline of colour c."""
    _disc(g, cx, cy, r + 1, c)
    _disc(g, cx, cy, r, fill)


def winter_cabin():
    g = _canvas(".")
    # sky bands (night)
    for y in range(H):
        for x in range(W):
            g[y][x] = "K" if y < 7 else ("k" if y < 14 else ".")
    # aurora ribbon
    for x in range(W):
        y = int(9 + 3 * math.sin(x / 5.0))
        for d in range(2):
            _put(g, x, y + d, "A" if (x // 3) % 2 == 0 else "a")
    # moon with craters
    _disc(g, 39, 5, 3, "M")
    for x, y in [(38, 4), (40, 6)]:
        _put(g, x, y, "m")
    # stars
    for x, y in [(3, 2), (9, 5), (15, 1), (21, 4), (27, 2), (33, 6), (45, 2), (6, 15), (30, 16), (44, 13), (18, 14)]:
        _put(g, x, y, "Y")
    # far snowy hills
    for x in range(W):
        top = int(21 + 2.5 * math.sin(x / 6.0 + 1) + 1.5 * math.sin(x / 2.7))
        for y in range(top, H):
            g[y][x] = "s"
    # near snow ground
    for x in range(W):
        top = int(31 + 1.2 * math.sin(x / 4.0))
        for y in range(top, H):
            g[y][x] = "W"
    # pine trees
    _pine(g, 5, 16, 15)
    _pine(g, 43, 15, 16)
    # fence on the left and right
    for x in range(0, 14):
        _put(g, x, 32, "n")
        if x % 3 == 0:
            _rect(g, x, 31, x, 33, "N")
    for x in range(31, 48):
        if 33 <= x <= 41:
            continue
        _put(g, x, 32, "n")
        if x % 3 == 0:
            _rect(g, x, 31, x, 33, "N")
    # cabin
    _rect(g, 16, 25, 29, 33, "N")                  # walls
    for y in range(26, 34, 2):                     # log lines
        _rect(g, 16, y, 29, y, "n")
    for k in range(7):                             # roof
        _rect(g, 14 + k, 24 - k, 31 - k, 24 - k, "R")
    for k in range(7):                             # snow on roof edge
        _put(g, 14 + k, 24 - k, "W"); _put(g, 31 - k, 24 - k, "W")
    _rect(g, 20, 18, 25, 18, "W")
    _rect(g, 26, 16, 27, 20, "c")                  # chimney
    _rect(g, 26, 15, 27, 15, "W")
    for x, y in [(27, 13), (28, 12), (28, 11), (29, 10), (29, 9)]:
        _put(g, x, y, "p")                         # smoke
    _rect(g, 18, 27, 20, 29, "L"); _put(g, 19, 28, "n")     # window left (warm light, cross bar)
    _rect(g, 25, 27, 27, 29, "L"); _put(g, 26, 28, "n")     # window right
    _rect(g, 22, 28, 23, 33, "D"); _put(g, 23, 31, "Y")      # door + knob
    # path from the door
    for y in range(34, H):
        w = (y - 33)
        _rect(g, 22 - w // 2, y, 23 + w // 2, y, "s")
    # snowman (blue outline so it shows on the snow)
    _ring(g, 37, 34, 3, "b", "W")
    _ring(g, 37, 28, 2, "b", "W")
    _rect(g, 35, 26, 39, 26, "K"); _rect(g, 36, 24, 38, 25, "K"); _rect(g, 36, 25, 38, 25, "R")
    _put(g, 36, 28, "K"); _put(g, 38, 28, "K"); _put(g, 37, 29, "O"); _put(g, 38, 29, "O")
    _rect(g, 35, 31, 39, 31, "R"); _put(g, 39, 32, "R")
    _put(g, 37, 33, "K"); _put(g, 37, 35, "K")
    for x, y in [(33, 30), (32, 29), (41, 30), (42, 29)]:
        _put(g, x, y, "n")
    # sled with a red seat
    _rect(g, 3, 35, 10, 35, "R"); _rect(g, 4, 34, 9, 34, "R")
    _rect(g, 2, 36, 11, 36, "n"); _put(g, 12, 35, "n"); _put(g, 1, 35, "n")
    # footprints in the snow
    for x, y in [(15, 37), (17, 38), (27, 37), (29, 38), (31, 37), (44, 36), (46, 37)]:
        _put(g, x, y, "s")
    # string of lights along the roof edge
    for k, x in enumerate(range(16, 30, 2)):
        _put(g, x, 25, ["Y", "R", "A", "L"][k % 4])
    return {
        "title": "Winter Cabin Night",
        "colors": {".": "3B5F9A", "K": "16213E", "k": "24386A", "A": "4FD1A5", "a": "8BE3C7",
                   "M": "F6E7A1", "m": "D9C77E", "Y": "FFE27A", "s": "CFE0F2", "W": "FFFFFF",
                   "g": "1D5C36", "G": "2E8B4E", "N": "8B5A2B", "n": "6B4220", "R": "B23A2E",
                   "c": "7A7F8C", "p": "B8C2D3", "b": "8FAED6", "L": "FFC94D", "D": "5A3418", "O": "F28C28"},
        "rows": ["".join(r) for r in g],
    }


def _ellipse(g, cx, cy, rx, ry, c):
    for y in range(H):
        for x in range(W):
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                g[y][x] = c


def _penguin(g, cx, base, size, scarf=None):
    """Penguin standing on `base` row. size ~ body half-width."""
    bh = int(size * 1.6)
    cy = base - bh
    _ellipse(g, cx, cy, size, bh, "K")                       # body
    _ellipse(g, cx, cy + 1, size - 2, bh - 2, "W")           # belly
    hy = cy - bh + 1
    _ellipse(g, cx, hy, size - 1, size - 1, "K")             # head
    _put(g, cx - 1, hy, "W"); _put(g, cx + 1, hy, "W")       # eye whites
    _put(g, cx - 1, hy, "E"); _put(g, cx + 1, hy, "E")
    _put(g, cx - 2, hy - 1, "W"); _put(g, cx + 2, hy - 1, "W")
    _rect(g, cx - 1, hy + 1, cx + 1, hy + 1, "O")            # beak
    _put(g, cx, hy + 2, "O")
    _rect(g, cx - size + 1, base, cx - 1, base, "O")         # feet
    _rect(g, cx + 1, base, cx + size - 1, base, "O")
    _put(g, cx - size - 1, cy, "K"); _put(g, cx + size + 1, cy, "K")   # flippers
    _put(g, cx - size - 1, cy + 1, "K"); _put(g, cx + size + 1, cy + 1, "K")
    if scarf:
        _rect(g, cx - size + 1, hy + size - 1, cx + size - 1, hy + size - 1, scarf)
        _rect(g, cx + size - 2, hy + size, cx + size - 2, hy + size + 2, scarf)


def x_shade(k):
    return k % 3 != 0


def penguin_party():
    g = _canvas(".")
    for y in range(H):                                       # day sky bands
        for x in range(W):
            g[y][x] = "S" if y < 6 else ("s" if y < 13 else ".")
    _disc(g, 7, 6, 3, "Y")                                   # sun
    for x, y in [(18, 3), (25, 7), (33, 2), (41, 9), (29, 12), (14, 11), (45, 4)]:
        _put(g, x, y, "W")                                   # snowflakes
    for cx, top, half in [(30, 12, 6), (42, 10, 7), (20, 15, 4)]:   # icebergs
        for k in range(18 - top):
            hw = min(half, 1 + k)
            _rect(g, cx - hw, top + k, cx + hw, top + k, "W" if x_shade(k) else "i")
    _rect(g, 0, 18, W - 1, 21, "B")                          # sea
    for x in range(0, W, 5):
        _put(g, x, 19, "b"); _put(g, x + 2, 20, "b")
    for x in range(W):                                       # ice floor
        top = int(22 + 1.0 * __import__("math").sin(x / 5.0))
        for y in range(top, H):
            g[y][x] = "W" if (y + x // 7) % 9 else "w"
    # igloo: blue-grey dome with block lines and a dark door
    _ellipse(g, 40, 31, 7, 6, "j")
    _ellipse(g, 40, 31, 6, 5, "q")
    for y in (28, 31, 34):
        for x in range(33, 48):
            if g[y][x] == "q":
                g[y][x] = "j"
    for x, y0 in [(37, 26), (43, 26), (35, 29), (40, 29), (45, 29), (37, 32), (43, 32)]:
        for y in range(y0, y0 + 2):
            if g[y][x] == "q":
                g[y][x] = "j"
    _ellipse(g, 40, 35, 2, 3, "D")
    _rect(g, 32, 37, 47, 37, "w")
    # penguins
    _penguin(g, 21, 35, 4, scarf="R")
    _penguin(g, 11, 36, 3)
    _penguin(g, 29, 36, 3, scarf="G")
    _penguin(g, 4, 38, 2)
    # fish and a little snow pile
    _rect(g, 15, 37, 17, 37, "F"); _put(g, 18, 36, "F"); _put(g, 18, 38, "F")
    return {
        "title": "Penguin Ice Party",
        "colors": {".": "BFE3F7", "S": "7EC3EB", "s": "9ED3F1", "Y": "FFD84D", "W": "FFFFFF", "w": "D6E6F2",
                   "I": "E9F4FB", "i": "BCD7EA", "q": "CFE3F3", "j": "8FB3D3", "B": "2C6FB2", "b": "5A95CF", "K": "1E2433", "E": "000000",
                   "O": "F59E1B", "R": "D7263D", "G": "2E9E4F", "D": "3E4A5E", "F": "7BA7C9"},
        "rows": ["".join(r) for r in g],
    }


def _fox(g, x0, base):
    """Sitting fox facing right, about 14 wide x 13 tall, bottom row = base."""
    _ellipse(g, x0 + 5, base - 4, 5, 4, "F")                 # body
    _ellipse(g, x0 + 9, base - 9, 3, 3, "F")                 # head
    _put(g, x0 + 7, base - 13, "F"); _put(g, x0 + 7, base - 12, "F")   # ears
    _put(g, x0 + 11, base - 13, "F"); _put(g, x0 + 11, base - 12, "F")
    _put(g, x0 + 7, base - 12, "f"); _put(g, x0 + 11, base - 12, "f")
    _rect(g, x0 + 10, base - 8, x0 + 13, base - 7, "W")      # snout
    _put(g, x0 + 13, base - 8, "K")                          # nose
    _put(g, x0 + 10, base - 10, "K")                         # eye
    _ellipse(g, x0 + 7, base - 4, 2, 3, "W")                 # chest
    for k in range(7):                                       # tail curling left
        _put(g, x0 - 1 - k // 2, base - 1 - k // 3, "F")
        _put(g, x0 - k // 2, base - k // 3, "F")
    _put(g, x0 - 4, base - 3, "W"); _put(g, x0 - 3, base - 3, "W")
    _rect(g, x0 + 3, base, x0 + 4, base, "f"); _rect(g, x0 + 7, base, x0 + 8, base, "f")


def _owl(g, cx, top):
    _ellipse(g, cx, top + 4, 3, 4, "N")                      # body
    _ellipse(g, cx, top + 5, 2, 2, "T")                      # belly
    _put(g, cx - 3, top, "N"); _put(g, cx + 3, top, "N")     # ear tufts
    _put(g, cx - 1, top + 2, "Y"); _put(g, cx + 1, top + 2, "Y")
    _put(g, cx - 1, top + 2, "Y"); _put(g, cx, top + 3, "O")
    _put(g, cx - 1, top + 2, "K"); _put(g, cx + 1, top + 2, "K")
    _put(g, cx - 2, top + 2, "Y"); _put(g, cx + 2, top + 2, "Y")


def _bunny(g, cx, base):
    _ellipse(g, cx, base - 2, 4, 3, "b")                     # outline so the white bunny shows on snow
    _ellipse(g, cx + 3, base - 4, 3, 3, "b")
    _rect(g, cx + 1, base - 9, cx + 5, base - 6, "b")
    _ellipse(g, cx, base - 2, 3, 2, "W")
    _ellipse(g, cx + 3, base - 4, 2, 2, "W")
    _rect(g, cx + 2, base - 8, cx + 2, base - 6, "W"); _rect(g, cx + 4, base - 8, cx + 4, base - 6, "W")
    _put(g, cx + 2, base - 7, "p"); _put(g, cx + 4, base - 7, "p")
    _put(g, cx + 4, base - 4, "K"); _put(g, cx + 5, base - 3, "p")
    _put(g, cx - 3, base - 3, "w")
    for x in range(cx - 4, cx + 5):
        if g[base][x] == "W":
            g[base][x] = "w"


def forest_friends():
    import math
    g = _canvas(".")
    for y in range(H):                                       # sunset bands
        for x in range(W):
            g[y][x] = "P" if y < 5 else ("p" if y < 10 else ("Y" if y < 14 else "."))
    _disc(g, 24, 15, 4, "Z")                                 # low sun
    for x in range(W):                                       # far snowy hills
        top = int(17 + 2 * math.sin(x / 7.0) + math.sin(x / 3.1))
        for y in range(top, H):
            g[y][x] = "s"
    for cx, top, h in [(3, 12, 14), (13, 15, 10), (36, 14, 11), (45, 10, 16)]:
        for k in range(h):
            tier = (k // 4)
            half = 1 + (k % 4) + tier
            for x in range(cx - half, cx + half + 1):
                _put(g, x, top + k, "g" if x <= cx else "G")
            if k % 4 == 3 or k == 0:
                _put(g, cx - half, top + k, "W"); _put(g, cx - half + 1, top + k, "W")
        _rect(g, cx - 1, top + h, cx, top + h + 1, "N")
    for x in range(W):                                       # snow ground
        top = int(30 + 1.2 * math.sin(x / 5.0 + 2))
        for y in range(top, H):
            g[y][x] = "W"
    for x in range(22, 34):                                  # branch for the owl
        _put(g, x, 22, "N")
    _put(g, 34, 21, "N"); _put(g, 21, 23, "N")
    _rect(g, 24, 21, 31, 21, "W")
    _owl(g, 28, 13)
    _fox(g, 12, 36)
    _bunny(g, 35, 36)
    for x, y in [(6, 4), (15, 7), (31, 3), (40, 6), (20, 25), (42, 24), (8, 22), (30, 28)]:
        _put(g, x, y, "W")                                   # falling snow
    for x, y in [(4, 37), (5, 38), (27, 38), (28, 37), (44, 38)]:
        _put(g, x, y, "w")
    return {
        "title": "Snowy Forest Friends",
        "colors": {".": "F3B7A0", "P": "6E4A8E", "p": "B0679A", "Y": "F5C27A", "Z": "FFE29A", "s": "E7D7E8",
                   "W": "FFFFFF", "w": "D9E1EE", "b": "A9B6CC", "g": "1D5C36", "G": "2E8B4E", "N": "6B4220", "F": "E0702A",
                   "f": "8A3A14", "K": "1E1E24", "T": "D9B183", "O": "F59E1B"},
        "rows": ["".join(r) for r in g],
    }


MURALS = {"winter_cabin": winter_cabin, "penguin_party": penguin_party, "forest_friends": forest_friends}
