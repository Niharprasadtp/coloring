"""Color by Code: a color-by-number page where every space holds a math problem instead of a number.
The answer tells the child which color to use, so the picture only comes out right when the math is right.

    ../.venv/Scripts/python.exe color_by_code.py ../input_books/book1/01_snowman.png --skill add10

Skills: add10 (addition to 10), sub10 (subtraction within 10), mult (times tables), div (division).
Writes <out>/<stem>_<skill>.pdf (worksheet + answer key) and a PNG preview, then re-checks every
problem against its color.

Reuses the color-by-number engine in ../cbn as a library; nothing in cbn is changed.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from cbn import quantize, regions                      # noqa: E402
from cbn.layout import MM2_PER_PT2                      # noqa: E402

FONT = "Helvetica-Bold"
MIN_FONT, MAX_FONT = 6.5, 11.0
MIN_AREA, MIN_RADIUS = 12.0, 3.0      # mm2 / pt: smaller spaces merge away; spaces too small for a problem come pre-colored
SKILLS = {
    "add10": "Addition to 10",
    "sub10": "Subtraction within 10",
    "mult": "Multiplication",
    "div": "Division",
}
MINUS, TIMES, DIVIDE = "−", "×", "÷"


# ---------- math ----------

def answer_set(skill: str, n: int, rng: random.Random) -> list[int]:
    """n different answers, one per color."""
    pool = {"add10": range(2, 11), "sub10": range(1, 10), "div": range(2, 11),
            "mult": [6, 8, 10, 12, 14, 15, 16, 18, 20, 21, 24, 27, 28, 30, 32, 35, 36, 40, 42, 45, 48]}[skill]
    pool = list(pool)
    if skill == "add10" and n <= 7:
        pool = [v for v in pool if v >= 4]          # 2 and 3 only allow 1+1, 1+2: boring
    if n > len(pool):
        raise SystemExit(f"{n} colors but only {len(pool)} different answers for {skill}; use fewer --colors")
    return sorted(rng.sample(pool, n))


def problem(skill: str, ans: int, rng: random.Random) -> str:
    if skill == "add10":
        a = rng.randint(1, ans - 1) if ans > 1 else 0
        return f"{a}+{ans - a}"
    if skill == "sub10":
        b = rng.randint(ans + 1, 10)
        return f"{b}{MINUS}{b - ans}"
    if skill == "mult":
        pairs = [(a, ans // a) for a in range(2, 10) if ans % a == 0 and 2 <= ans // a <= 10]
        a, b = rng.choice(pairs)
        return f"{a}{TIMES}{b}"
    if skill == "div":
        d = rng.randint(2, 9)
        return f"{ans * d}{DIVIDE}{d}"
    raise ValueError(skill)


def solve(text: str) -> float:
    expr = text.replace(MINUS, "-").replace(TIMES, "*").replace(DIVIDE, "/")
    assert set(expr) <= set("0123456789+-*/"), text
    return eval(expr)  # digits and one operator only (checked above)


# ---------- picture ----------

# A standard kids' crayon box. Every picture color is snapped to the nearest crayon, so the key can say
# "7 = ORANGE" and two shades of brown never ask a child to tell them apart.
CRAYONS = [("WHITE", (255, 255, 255)), ("BLACK", (35, 35, 35)), ("GRAY", (150, 150, 150)),
           ("RED", (215, 40, 45)), ("ORANGE", (245, 130, 35)), ("YELLOW", (250, 215, 50)),
           ("LIGHT GREEN", (130, 200, 80)), ("GREEN", (35, 140, 65)), ("LIGHT BLUE", (120, 195, 240)),
           ("BLUE", (35, 90, 200)), ("PURPLE", (125, 70, 175)), ("PINK", (245, 150, 190)),
           ("BROWN", (125, 75, 40)), ("TAN", (215, 175, 125))]
WHITE_IDX = 0


def paper_color(rgb: np.ndarray) -> np.ndarray:
    corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
                              rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
    return np.median(corners, axis=0)


def crop_to_art(rgb: np.ndarray, pad: int = 12) -> np.ndarray:
    """Cut away the plain margin around the drawing (color of the corners)."""
    corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
                              rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    ys, xs = np.nonzero(np.abs(rgb.astype(int) - bg).sum(axis=2) > 40)
    if len(xs) == 0:
        return rgb
    h, w = rgb.shape[:2]
    return rgb[max(0, ys.min() - pad):min(h, ys.max() + pad), max(0, xs.min() - pad):min(w, xs.max() + pad)]


def analyse(path: Path, k: int, scale_hint: float, min_area_mm2: float, min_radius_pt: float, seed: int):
    """Regions, outlines and problem spots from the cbn engine, at the printed scale."""
    rgb = quantize.smooth(crop_to_art(quantize.load_image(path, 1800)))
    lab = quantize.to_lab(rgb)
    rng = np.random.default_rng(seed)
    pic_lab = quantize.fit_palette(quantize.sample_pixels(lab, 60_000, rng), k, 6.0, seed)
    base, _ = quantize.assign(lab, pic_lab)
    palette_lab = quantize.to_lab(np.array([[c for _, c in CRAYONS]], np.uint8))[0]
    to_crayon, _ = quantize.assign(pic_lab[None, :, :], palette_lab)
    base = to_crayon[0][base]                      # picture colors -> crayon indices
    # the plain paper around the drawing stays white, whatever crayon it is closest to
    paper = paper_color(rgb)
    near = np.abs(rgb.astype(int) - paper).sum(axis=2) < 40
    count, comp = cv2.connectedComponents(near.astype(np.uint8), connectivity=4)
    edge = set(np.unique(np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]]))) - {0}
    base[np.isin(comp, list(edge))] = WHITE_IDX
    h, w = base.shape
    scale = scale_hint(w, h)                       # pt per image pixel
    labels, region_ids, n, dist, _, detail_map = regions.cleanup(
        base, palette_lab, min_area_mm2 / MM2_PER_PT2 / scale ** 2, min_radius_pt / scale,
        0.2 / MM2_PER_PT2 / scale ** 2, 4.5 / MM2_PER_PT2 / scale ** 2, max(2.0, 0.5 / scale),
        detail_delta=25.0)                         # tiny high-contrast specks (eyes) come pre-printed
    markers = regions.place_numbers(labels, region_ids, n, dist, 120 / scale, max_per_region=4)
    outlines = regions.trace_outlines(labels)
    details = regions.trace_details(detail_map)
    palette = np.array([c for _, c in CRAYONS], np.uint8)
    return dict(labels=labels, n=n, markers=markers, outlines=outlines, palette=palette, scale=scale,
                w=w, h=h, region_ids=region_ids, palette_lab=palette_lab, details=details)


# ---------- PDF ----------

def rgb(c):
    return Color(c[0] / 255, c[1] / 255, c[2] / 255)


def _png_reader(arr):
    import io
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    buf = io.BytesIO()
    Image.fromarray(arr.astype(np.uint8)).save(buf, "PNG")
    buf.seek(0)
    return ImageReader(buf)


def _poly_path(c, poly, ox, oy, s, path=None):
    p = path or c.beginPath()
    p.moveTo(ox + poly[0][0] * s, oy - poly[0][1] * s)
    for x, y in poly[1:]:
        p.lineTo(ox + x * s, oy - y * s)
    return p


def draw_details(c, pic, ox, oy, s):
    for color, polys in pic["details"]:
        c.setFillColor(rgb(pic["palette"][color]))
        p = c.beginPath()
        for poly in polys:                       # holes are separate polygons: even-odd fill
            _poly_path(c, poly, ox, oy, s, p)
            p.close()
        c.drawPath(p, stroke=0, fill=1, fillMode=0)


def draw_outlines(c, pic, ox, oy, s, width=0.7):
    c.setStrokeColor(black)
    c.setLineWidth(width)
    c.setLineJoin(1)
    for line in pic["outlines"]:
        c.drawPath(_poly_path(c, line, ox, oy, s), stroke=1, fill=0)


_CACHE: dict = {}


def prepare(image: Path, W: float, H: float, k: int = 12, seed: int = 1) -> dict:
    """Analyse a picture once for this page size (cached; the same for every skill)."""
    key = (str(image), W, H, k, seed)
    if key not in _CACHE:
        box = (36, 150, W - 72, H - 150 - 132)          # x, y, w, h of the picture area
        pic = analyse(image, k, lambda w, h: min(box[2] / w, box[3] / h), MIN_AREA, MIN_RADIUS, seed)
        s = pic["scale"]
        pic["dw"], pic["dh"] = pic["w"] * s, pic["h"] * s
        pic["ox"] = box[0] + (box[2] - pic["dw"]) / 2
        pic["oy"] = box[1] + box[3] - (box[3] - pic["dh"]) / 2      # top-left corner of the picture
        rid = pic["region_ids"]
        pic["used"] = sorted({m.color for m in pic["markers"]})
        pic["marker_rid"] = [int(rid[int(m.y), int(m.x)]) for m in pic["markers"]]
        _CACHE[key] = pic
    return _CACHE[key]


def header(c, W, H, head, sub, page_label=None):
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", fit_font(head, "Helvetica-Bold", W - 72 - 210, 26))
    c.drawString(36, H - 60, head)
    c.setFont("Helvetica", 12)
    c.drawString(36, H - 112, sub)
    c.setFont("Helvetica", 11)
    c.drawRightString(W - 36, H - 56, "Name: ______________________")
    c.drawRightString(W - 36, H - 78, "Date: ______________________")
    c.setLineWidth(0.8)
    c.line(36, H - 92, W - 36, H - 92)
    if page_label:
        c.setFont("Helvetica", 9)
        c.setFillColor(Color(0.45, 0.45, 0.45))
        c.drawCentredString(W / 2, 22, page_label)
        c.setFillColor(black)


def fit_font(text, font, max_w, max_size):
    return min(max_size, max_w / pdfmetrics.stringWidth(text, font, 1))


def worksheet(c, pic, skill: str, seed: int, W: float, H: float, head: str, page_label=None) -> dict:
    """Draw one worksheet page and verify it. Returns the answers for the answer key."""
    s, ox, oy = pic["scale"], pic["ox"], pic["oy"]
    rng = random.Random(f"{seed}-{skill}")
    pal, used, markers, mrid = pic["palette"], pic["used"], pic["markers"], pic["marker_rid"]
    blank = {WHITE_IDX} & set(used)
    coded = [ci for ci in used if ci not in blank]
    answers = dict(zip(coded, rng.sample(answer_set(skill, len(coded), rng), len(coded))))

    header(c, W, H, head, "Solve each problem. Find the answer in the color key and color the space with that color.",
           page_label)
    texts = {i: problem(skill, answers[m.color], rng) for i, m in enumerate(markers) if m.color not in blank}
    best = {}
    for i, m in enumerate(markers):
        if mrid[i] not in best or m.radius > markers[best[mrid[i]]].radius:
            best[mrid[i]] = i
    # a space whose best spot cannot hold a readable problem comes pre-colored
    prefill = {r for r, i in best.items()
               if i in texts and 2 * markers[i].radius * s * 0.92 / pdfmetrics.stringWidth(texts[i], FONT, 1) < MIN_FONT}
    layer = np.zeros((pic["h"], pic["w"], 4), np.uint8)
    mask = np.isin(pic["region_ids"], list(prefill))
    layer[mask, :3] = pal[pic["labels"][mask]]
    layer[mask, 3] = 255
    c.drawImage(_png_reader(layer), ox, oy - pic["dh"], pic["dw"], pic["dh"], mask="auto")
    draw_details(c, pic, ox, oy, s)
    draw_outlines(c, pic, ox, oy, s)
    problems = []
    for i, m in enumerate(markers):
        if i not in texts or mrid[i] in prefill:
            continue
        size = min(MAX_FONT, 2 * m.radius * s * 0.92 / pdfmetrics.stringWidth(texts[i], FONT, 1))
        if size < MIN_FONT:          # extra copy in a cramped corner: skip, the space has a bigger one
            continue
        c.setFillColor(black)
        c.setFont(FONT, size)
        c.drawCentredString(ox + m.x * s, oy - m.y * s - size * 0.35, texts[i])
        problems.append((texts[i], m.color, mrid[i]))
    # color key
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, 128, "COLOR KEY")
    cw = (W - 72) / 5
    for i, ci in enumerate(sorted(coded, key=lambda ci: answers[ci])):
        r, col = divmod(i, 5)
        x, y = 36 + col * cw, 98 - r * 34
        c.setFillColor(rgb(pal[ci]))
        c.setStrokeColor(black)
        c.setLineWidth(1)
        c.roundRect(x, y - 6, 40, 24, 5, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x + 48, y + 3, f"= {answers[ci]}")
        c.setFont("Helvetica", 8)
        c.drawString(x + 48, y - 7, CRAYONS[ci][0])
    if blank:
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 36, 128, "Spaces with no problem: leave white.")

    # verify: every problem solves to its color's answer; every coded space has a problem or comes pre-colored
    bad = [t for t, ci, _ in problems if solve(t) != answers[ci]]
    coded_regions = {mrid[i] for i, m in enumerate(markers) if m.color not in blank}
    missing = coded_regions - {r for _, _, r in problems} - prefill
    if bad or missing:
        raise SystemExit(f"VERIFY FAILED ({head}): wrong {bad[:5]}, {len(missing)} spaces without a problem")
    return dict(answers=answers, coded=coded, blank=blank, problems=len(problems),
                spaces=len(coded_regions), prefill=len(prefill))


def answer_picture(c, pic, x, y, w, h):
    """The finished picture fitted into the box (x, y bottom-left)."""
    f = min(w / pic["dw"], h / pic["dh"])
    s = pic["scale"] * f
    dw, dh = pic["dw"] * f, pic["dh"] * f
    ox, oy = x + (w - dw) / 2, y + h - (h - dh) / 2
    ref = pic["palette"][pic["labels"]].copy()
    ref[pic["labels"] == WHITE_IDX] = 255
    c.drawImage(_png_reader(ref), ox, oy - dh, dw, dh)
    draw_details(c, pic, ox, oy, s)
    draw_outlines(c, pic, ox, oy, s, width=0.7 * max(f, 0.5))


def build(image: Path, skill: str, out_dir: Path, k: int, seed: int, title: str | None) -> Path:
    W, H = letter
    pic = prepare(image, W, H, k, seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"{image.stem}_{skill}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=letter)
    head = title or f"Color by Code: {SKILLS[skill]}"
    st = worksheet(c, pic, skill, seed, W, H, head)
    c.showPage()
    header(c, W, H, head, "Answer key: the finished picture.")
    answer_picture(c, pic, 36, 150, W - 72, H - 282)
    c.showPage()
    c.save()
    print(f"{pdf.name}: {st['problems']} problems in {st['spaces']} spaces ({st['prefill']} small spaces "
          f"pre-colored), {len(st['coded'])} colors; verified")
    return pdf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--skill", choices=SKILLS, default="add10")
    ap.add_argument("--colors", type=int, default=12)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--title")
    ap.add_argument("-o", "--out", type=Path, default=HERE.parent / "output" / "learn_color")
    a = ap.parse_args()
    pdf = build(a.image, a.skill, a.out, a.colors, a.seed, a.title)
    import pymupdf
    doc = pymupdf.open(pdf)
    for i, p in enumerate(doc):
        p.get_pixmap(dpi=110).save(str(pdf.with_name(f"{pdf.stem}_p{i + 1}.png")))


if __name__ == "__main__":
    main()
