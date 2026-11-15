"""Time-lapse video of one numbered page being painted color by color (1920x1080, 30 fps, silent H.264).

    python make_coloring_video.py -i input -c output/collection -o output/listing_video -n 1
"""

import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from make_listing_images import (CORAL, INK, MUSTARD, PLUM, TEAL, Collection, NAMES, background, cover_crop,
                                 font, shadowed, text_c)

VW, VH, FPS = 1920, 1080, 30
CW, CH = 645, 860                 # painted card
CX, CY = 640, 110                 # card position (inside its white border)
INTRO, PAINT, NUMBERS, HOLD = 1.3, 10.0, 1.0, 2.2
LINE_THRESHOLD = 0.80             # darker than this (0..1) counts as outline or number


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def hex_palette(path):
    rows = [line.split("#")[1].strip() for line in path.read_text().splitlines() if "#" in line]
    return np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for h in rows], np.uint8)


def prepare(col, n):
    """Line layer (0..1), flat color layer, label map and per-pixel reveal times for design n."""
    rect = col.rect(n)
    x0, y0, x1, y1 = rect
    dark = cv2.cvtColor(col.render(n, "Dark_Numbered")[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    line = cv2.resize(dark, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    nav = cv2.cvtColor(col.render(n, "Navigation_Map")[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
    nav = cv2.resize(nav, (CW, CH), interpolation=cv2.INTER_NEAREST)
    invalid = cv2.dilate((line < LINE_THRESHOLD).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    _, (iy, ix) = ndimage.distance_transform_edt(invalid, return_indices=True)
    flat = nav[iy, ix]
    palette = hex_palette(col.root / f"Design_{n:02d}" / "Hex_Codes.txt")
    dist = np.linalg.norm(flat[:, :, None, :].astype(np.float32) - palette[None, None].astype(np.float32), axis=3)
    labels = dist.argmin(axis=2)
    color_layer = palette[labels]

    count = len(palette)
    slot = PAINT / count
    reveal = np.full((CH, CW), INTRO + PAINT, np.float32)
    for c in range(count):
        mask = (labels == c).astype(np.uint8)
        k, comp, _, cent = cv2.connectedComponentsWithStats(mask, connectivity=4)
        if k <= 1:
            continue
        order = np.argsort(cent[1:, 1] + 0.001 * cent[1:, 0])        # top to bottom
        rank = np.empty(k - 1, np.float32)
        rank[order] = np.arange(k - 1)
        t0 = INTRO + c * slot
        times = np.concatenate([[0], t0 + rank / max(k - 1, 1) * slot * 0.8]).astype(np.float32)
        reveal[mask > 0] = times[comp[mask > 0]]
    return line, color_layer, labels, reveal, palette, slot


def build(col, n, out_dir, pages=46, out_name="paint_by_number_coloring_video.mp4"):
    out_dir.mkdir(parents=True, exist_ok=True)
    line, color_layer, labels, reveal, palette, slot = prepare(col, n)
    count = len(palette)
    clean = np.asarray(cover_crop(col.art(n), CW, CH))
    white = np.full_like(color_layer, 255)

    # static background with the empty card frame and the palette ring layout
    base = background(60).resize((VW, VH), Image.LANCZOS)
    blank = (white * line[:, :, None]).astype(np.uint8)
    shadowed(base, Image.fromarray(blank), (CX - 14, CY - 14), border=14)
    text_c(base, "WATCH IT COME TO LIFE", VW / 2, 24, font("georgiab", 60), PLUM)
    name = NAMES.get(n, f"Design {n}")
    cols, step, gx, gy, r = (4, 104, 1390, 190, 36) if count <= 32 else (5, 100, 1385, 190, 35)

    def swatch_xy(i):
        return gx + (i % cols) * step + r, gy + (i // cols) * step + r

    total = INTRO + PAINT + NUMBERS + HOLD
    n_frames = round(total * FPS)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = out_dir / out_name
    proc = subprocess.Popen([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS),
                             "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                             "-preset", "medium", "-movflags", "+faststart", str(out)],
                            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    f_small, f_mid, f_big = font("segoeuib", 34), font("segoeuib", 52), font("georgiab", 70)
    for f in range(n_frames):
        T = f / FPS
        alpha = np.clip((T - reveal) / 0.18, 0, 1)[:, :, None]
        layer = color_layer * alpha + white * (1 - alpha)
        card = layer * line[:, :, None]
        k = ease((T - (INTRO + PAINT)) / NUMBERS)                 # numbers/outlines fade into the finished art
        if k > 0:
            card = card * (1 - k) + clean.astype(np.float32) * k
        frame = base.copy()
        frame.paste(Image.fromarray(card.astype(np.uint8)), (CX, CY))
        d = ImageDraw.Draw(frame)

        cur = int(np.clip((T - INTRO) / slot, 0, count - 1)) if T >= INTRO else -1
        painting = INTRO <= T < INTRO + PAINT
        done = count if T >= INTRO + PAINT else max(cur, 0)
        for i in range(count):
            sx, sy = swatch_xy(i)
            filled = i < done or (i == cur and painting)
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=tuple(int(v) for v in palette[i]) if filled else (245, 240, 232),
                      outline=(150, 140, 130), width=3)
            lum = 0.299 * palette[i][0] + 0.587 * palette[i][1] + 0.114 * palette[i][2]
            ink = (255, 255, 255) if filled and lum < 140 else (60, 60, 60)
            tw = d.textlength(str(i + 1), font=f_small)
            d.text((sx - tw / 2, sy - 20), str(i + 1), font=f_small, fill=ink)
            if i == cur and painting:
                d.ellipse([sx - r - 9, sy - r - 9, sx + r + 9, sy + r + 9], outline=CORAL, width=7)

        # left panel
        if painting:
            c = palette[cur]
            d.ellipse([140, 330, 420, 610], fill=tuple(int(v) for v in c), outline=(255, 255, 255), width=10)
            lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            tw = d.textlength(str(cur + 1), font=f_big)
            d.text((280 - tw / 2, 440), str(cur + 1), font=f_big, fill=(255, 255, 255) if lum < 140 else INK)
            text_c(frame, "Painting color", 280, 270, f_mid, TEAL)
            pct = int(100 * (T - INTRO) / PAINT)
            d.rounded_rectangle([90, 700, 470, 740], 20, fill=(235, 226, 214))
            d.rounded_rectangle([90, 700, 90 + int(380 * pct / 100), 740], 20, fill=CORAL)
            text_c(frame, f"{pct}% painted", 280, 755, f_mid, PLUM)
        elif T < INTRO:
            text_c(frame, "Match each number", 280, 380, f_mid, PLUM)
            text_c(frame, "to its color", 280, 450, f_mid, PLUM)
        else:
            text_c(frame, "Your finished", 280, 330, f_mid, PLUM)
            text_c(frame, "painting", 280, 400, f_mid, PLUM)
            text_c(frame, name, 280, 500, f_small, TEAL)
            text_c(frame, f"{pages} pages included", 280, 640, f_mid, CORAL)
            text_c(frame, "Instant download", 280, 710, f_small, INK)
        proc.stdin.write(np.ascontiguousarray(np.asarray(frame)).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB, {total:.1f} s, {count} colors)")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    p.add_argument("-n", "--design", type=int, default=1)
    p.add_argument("--pages", type=int, default=46, help="page count shown at the end")
    p.add_argument("--name", default="paint_by_number_coloring_video.mp4")
    a = p.parse_args()
    build(Collection(a.input, a.collection), a.design, a.output, a.pages, a.name)


if __name__ == "__main__":
    sys.exit(main())
