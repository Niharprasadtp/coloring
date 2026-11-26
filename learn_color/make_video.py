"""Etsy listing video for the color-by-code bundle: 1920x1080, 30 fps, ~14 s, silent H.264.

Opens on the action (no title card): the penguin addition sheet gets colored in space by space, one crayon
color at a time, then the 4 levels, the 10 pictures and a short end card.

    ../.venv/Scripts/python.exe make_video.py            # build the mp4
    ../.venv/Scripts/python.exe make_video.py --upload   # build + replace the video on the Etsy draft
"""
from __future__ import annotations

import io
import json
import random
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import make_listing as L          # learn_color/make_listing.py (also loads the shared photo helpers as L.KL)

cbc, MB, KL = L.cbc, L.MB, L.KL
VW, VH, FPS, FADE = 1920, 1080, 30, 0.35
OUT = L.OUT / "video" / "color_by_code_math.mp4"
NAVY, RED, BLUE, YELLOW, WHITE, GREEN = KL.NAVY, KL.RED, KL.BLUE, KL.YELLOW, KL.WHITE, L.GREEN


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def background(seed):
    im = KL.wood_bg(seed)                                   # 2667x2000 -> crop 16:9 -> 1920x1080
    h = int(im.width * 9 / 16)
    top = (im.height - h) // 2
    return im.crop((0, top, im.width, top + h)).resize((VW, VH), Image.LANCZOS)


def shadow_paste(canvas_im, img, xy, blur=12):
    KL.put(canvas_im, KL.paper(img), xy)


# ---------- scene 1: the sheet gets colored in ----------

def coloring_scene(duration):
    n, skill = 1, "add10"
    Wl, Hl = letter
    pic = cbc.prepare(MB.PICTURES[n - 1], Wl, Hl)
    st = cbc.worksheet(canvas.Canvas(io.BytesIO(), pagesize=letter), pic, skill, n, Wl, Hl, "x")  # same answers
    ph = 1000
    z = ph / Hl
    plain = np.asarray(L.page_img(L.LEVEL_PDF[skill], n, ph)).astype(np.uint8)
    done = np.asarray(L.colored(skill, n, ph)).astype(np.uint8)
    pw = plain.shape[1]
    # region id map at page resolution
    rmap = Image.fromarray(pic["region_ids"].astype(np.int32)).resize(
        (round(pic["dw"] * z), round(pic["dh"] * z)), Image.NEAREST)
    rid = np.zeros(plain.shape[:2], np.int32)
    x0, y0 = round(pic["ox"] * z), round((Hl - pic["oy"]) * z)
    r = np.asarray(rmap)
    rid[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r[:plain.shape[0] - y0, :plain.shape[1] - x0]
    # reveal order: one crayon color at a time (in answer order), top to bottom inside a color
    color_of = {}
    for m, rr in zip(pic["markers"], pic["marker_rid"]):
        color_of[rr] = m.color
    ys = {rr: m.y for m, rr in zip(pic["markers"], pic["marker_rid"])}
    groups = sorted(st["coded"], key=lambda ci: st["answers"][ci])
    t_start, t_end = 0.3, duration - 1.4
    span = (t_end - t_start) / len(groups)
    reveal = np.full(rid.max() + 1, np.inf)
    windows = []
    for g, ci in enumerate(groups):
        regs = sorted((rr for rr, c in color_of.items() if c == ci), key=lambda rr: ys[rr])
        g0 = t_start + g * span
        windows.append((g0, g0 + span, ci))
        for k, rr in enumerate(regs):
            reveal[rr] = g0 + span * 0.85 * k / max(1, len(regs))
    tmap = reveal[rid]
    bg = background(41)
    px, py = 150, (VH - ph) // 2
    rng = random.Random(7)
    examples = {ci: cbc.problem(skill, st["answers"][ci], rng) for ci in groups}

    def render(t):
        page = np.where((tmap <= t)[..., None], done, plain)
        im = bg.copy()
        shadow_paste(im, Image.fromarray(page), (px, py))
        d = ImageDraw.Draw(im)
        rx = px + pw + 120
        cx = (rx + VW - 60) // 2
        f = KL.lucky(110)
        for k, line in enumerate(["SOLVE IT.", "COLOR IT!"]):
            w = d.textlength(line, font=f)
            d.text((cx - w / 2, 70 + k * 120), line, font=f, fill=(YELLOW, WHITE)[k], stroke_width=10, stroke_fill=NAVY)
        cur = next((w for w in windows if w[0] <= t < w[1]), None)
        if cur and t < t_end:
            ci = cur[2]
            a = ease((t - cur[0]) / 0.25)
            card_y = 420 + int(30 * (1 - a))
            d.rounded_rectangle([rx, card_y, VW - 60, card_y + 330], 36, fill=WHITE, outline=NAVY, width=6)
            prob = f"{examples[ci]} = {st['answers'][ci]}"
            fp = KL.lucky(96)
            d.text((cx - d.textlength(prob, font=fp) / 2, card_y + 40), prob, font=fp, fill=NAVY)
            col = tuple(int(v) for v in pic["palette"][ci])
            name = cbc.CRAYONS[ci][0]
            fn = KL.lucky(64)
            sw = 150
            tw = d.textlength(name, font=fn)
            sx = cx - (sw + 30 + tw) / 2
            d.rounded_rectangle([sx, card_y + 190, sx + sw, card_y + 280], 18, fill=col, outline=NAVY, width=5)
            d.text((sx + sw + 30, card_y + 200), name, font=fn, fill=NAVY)
        elif t >= t_end:
            a = ease((t - t_end) / 0.3)
            KL.pill(im, "MYSTERY SOLVED!", cx, 470 + int(40 * (1 - a)), fill=RED, size=64)
            fb = KL.body(46)
            for k, line in enumerate(["The picture only comes out", "right when the math is right"]):
                d.text((cx - d.textlength(line, font=fb) / 2, 640 + k * 64), line, font=fb, fill=NAVY)
        return np.asarray(im)
    return render


# ---------- scene 2: 4 levels ----------

def levels_scene(duration):
    bg = background(42)
    labels = [("add10", "ADDITION", RED), ("sub10", "SUBTRACTION", BLUE), ("mult", "MULTIPLICATION", GREEN),
              ("div", "DIVISION", (131, 56, 236))]
    pages = [KL.paper(L.page_img(L.LEVEL_PDF[s], 2, 640)) for s, _, _ in labels]

    def render(t):
        im = bg.copy()
        d = ImageDraw.Draw(im)
        f = KL.lucky(96)
        txt = "4 LEVELS, SAME PICTURE"
        d.text((VW / 2 - d.textlength(txt, font=f) / 2, 50), txt, font=f, fill=YELLOW, stroke_width=9, stroke_fill=NAVY)
        for k, (pg, (_, lab, col)) in enumerate(zip(pages, labels)):
            a = ease((t - 0.1 - k * 0.22) / 0.4)
            if a <= 0:
                continue
            x = 90 + k * 450
            y = 210 + int(80 * (1 - a))
            KL.put(im, pg, (x, y), angle=(-2, 1.5, -1.5, 2)[k])
            KL.pill(im, lab, x + pg.width / 2, 900, fill=col, size=40)
        return np.asarray(im)
    return render


# ---------- scene 3: 10 pictures ----------

def pictures_scene(duration):
    bg = background(43)
    thumbs = []
    for k in range(10):
        c = L.colored("add10", k + 1, 640)
        c = c.crop((0, int(c.height * 0.14), c.width, int(c.height * 0.84))).resize((300, 300 * 448 // 494))
        thumbs.append(KL.paper(c))

    def render(t):
        im = bg.copy()
        d = ImageDraw.Draw(im)
        f = KL.lucky(96)
        txt = "10 MYSTERY PICTURES"
        d.text((VW / 2 - d.textlength(txt, font=f) / 2, 50), txt, font=f, fill=YELLOW, stroke_width=9, stroke_fill=NAVY)
        for k, th in enumerate(thumbs):
            a = ease((t - 0.05 - k * 0.12) / 0.3)
            if a <= 0:
                continue
            col, row = k % 5, k // 5
            x = 150 + col * 330
            y = 250 + row * 380 + int(50 * (1 - a))
            KL.put(im, th, (x, y), angle=((k % 3) - 1) * 2, shadow=a > 0.5)
        return np.asarray(im)
    return render


# ---------- scene 4: end card ----------

def end_card(duration):
    bg = background(44)

    def render(t):
        im = bg.copy()
        d = ImageDraw.Draw(im)
        a = ease(t / 0.4)
        f = KL.lucky(130)
        for k, (line, col) in enumerate([("COLOR BY CODE", YELLOW), ("MATH", WHITE)]):
            d.text((VW / 2 - d.textlength(line, font=f) / 2, 150 + k * 150 - int(30 * (1 - a))), line, font=f,
                   fill=col, stroke_width=11, stroke_fill=NAVY)
        fb = KL.body(58)
        for k, line in enumerate(["40 self-checking worksheets  ·  4 levels",
                                  "Addition · Subtraction · Multiplication · Division",
                                  "Answer keys  ·  US Letter + A4  ·  instant download"]):
            if t > 0.25 + k * 0.2:
                d.text((VW / 2 - d.textlength(line, font=fb) / 2, 520 + k * 95), line, font=fb, fill=NAVY)
        return np.asarray(im)
    return render


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scenes = [(7.2, coloring_scene(7.2)), (2.8, levels_scene(2.8)), (2.6, pictures_scene(2.6)), (2.2, end_card(2.2))]
    starts, t0 = [], 0.0
    for dur, _ in scenes:
        starts.append(t0)
        t0 += dur - FADE
    total = starts[-1] + scenes[-1][0]
    n = round(total * FPS)
    print(f"{total:.1f} s, {n} frames", flush=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS),
                             "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                             "-preset", "medium", "-movflags", "+faststart", str(OUT)],
                            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for fr in range(n):
        T = fr / FPS
        i = max(k for k, s in enumerate(starts) if s <= T)
        dur, rend = scenes[i]
        frame = rend(min(T - starts[i], dur)).astype(np.float32)
        if i > 0 and T - starts[i] < FADE:
            pd, pr = scenes[i - 1]
            a = ease((T - starts[i]) / FADE)
            frame = pr(min(T - starts[i - 1], pd)) * (1 - a) + frame * a
        proc.stdin.write(np.ascontiguousarray(frame.astype(np.uint8)).tobytes())
    proc.stdin.close()
    proc.wait()
    print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB", flush=True)


def upload():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    lid = json.loads((L.OUT / "uploaded.json").read_text())["listing_id"]
    for v in e.request("GET", f"/listings/{lid}/videos")["results"]:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/videos/{v['video_id']}")
    e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": "color by code math"},
              files={"video": OUT})
    print(f"video uploaded to draft {lid}", flush=True)


if __name__ == "__main__":
    build()
    if "--upload" in sys.argv:
        upload()
