"""Etsy listing video (1920x1080, 30 fps, 14.5 s, silent H.264) built from the listing photos and one design.

    python make_listing_video.py -i input -c output/collection -l output/listing -o output/listing_video
"""

import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from make_listing_images import (CORAL, PLUM, TEAL, Collection, background, cover_crop, font, shadowed,
                                 text_c)

VW, VH, FPS = 1920, 1080, 30
FADE = 0.35


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def photo_scene(path, zoom_from, zoom_to, duration):
    """A listing photo, letterboxed over a blurred copy of itself, with a slow zoom."""
    photo = Image.open(path).convert("RGB")
    bg = np.asarray(cover_crop(photo, VW, VH))
    bg = cv2.GaussianBlur(bg, (0, 0), 35)
    bg = (bg * 0.78).astype(np.uint8)
    fg_h = round(VH * 1.0)
    fg = np.asarray(photo.resize((round(photo.width * fg_h / photo.height), fg_h), Image.LANCZOS))

    def render(t):
        z = zoom_from + (zoom_to - zoom_from) * ease(t / duration)
        h, w = round(fg.shape[0] * z), round(fg.shape[1] * z)
        scaled = cv2.resize(fg, (w, h), interpolation=cv2.INTER_LINEAR)
        frame = bg.copy()
        x, y = (VW - w) // 2, (VH - h) // 2
        sx0, sy0 = max(0, -x), max(0, -y)
        dx0, dy0 = max(0, x), max(0, y)
        cw, ch = min(w - sx0, VW - dx0), min(h - sy0, VH - dy0)
        frame[dy0:dy0 + ch, dx0:dx0 + cw] = scaled[sy0:sy0 + ch, sx0:sx0 + cw]
        return frame

    return render


def reveal_scene(col, n, duration):
    """Numbered page turns into the finished painting with a diagonal brush-like wipe."""
    base = background(50).resize((VW, VH), Image.LANCZOS)
    cw, ch = 645, 860
    rect = col.rect(n)
    line = cover_crop(col.style_img(n, "Dark_Numbered", rect), cw, ch)
    color = cover_crop(col.art(n), cw, ch)
    cx, cy = (VW - cw) // 2 - 14, 150
    shadowed(base, line, (cx, cy), border=14)
    base_np = np.asarray(base).copy()
    d = ImageDraw.Draw(base)
    text_c(base, "FROM NUMBERS TO MASTERPIECE", VW / 2, 28, font("georgiab", 82), PLUM)
    text_c(base, "NUMBERED PAGE", cx / 2 + 20, 520, font("segoeuib", 50), TEAL)
    text_c(base, "FINISHED PAINTING", VW - (VW - cx - cw - 28) / 2 + 20, 520, font("segoeuib", 50), TEAL)
    titled = np.asarray(base).copy()
    line_np, color_np = np.asarray(line), np.asarray(color)
    yy, xx = np.mgrid[0:ch, 0:cw]
    skew = xx + 0.45 * yy            # diagonal wipe front
    span = cw + 0.45 * ch + 120

    def render(t):
        p = ease((t - 0.6) / (duration - 1.6))
        front = p * span - 60
        m = np.clip((front - skew) / 90.0 + 0.5, 0, 1)[:, :, None]
        card = (line_np * (1 - m) + color_np * m).astype(np.uint8)
        frame = titled.copy()
        frame[cy + 14:cy + 14 + ch, cx + 14:cx + 14 + cw] = card
        return frame

    return render


def build(col, listing, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes = [
        (2.7, photo_scene(listing / "01_cover.jpg", 1.0, 1.06, 2.7)),
        (5.6, reveal_scene(col, 1, 5.6)),
        (2.4, photo_scene(listing / "04_detail_eyes.jpg", 1.0, 1.06, 2.4)),
        (2.3, photo_scene(listing / "06_ipad.jpg", 1.0, 1.06, 2.3)),
        (1.5 + FADE, photo_scene(listing / "01_cover.jpg", 1.06, 1.0, 1.5 + FADE)),
    ]
    starts, t0 = [], 0.0
    for dur, _ in scenes:
        starts.append(t0)
        t0 += dur - FADE if len(starts) < len(scenes) else dur
    total = starts[-1] + scenes[-1][0]
    n_frames = round(total * FPS)
    print(f"{total:.1f} s, {n_frames} frames")

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = out_dir / "paint_by_number_listing_video.mp4"
    proc = subprocess.Popen([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS),
                             "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                             "-preset", "medium", "-movflags", "+faststart", str(out)],
                            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for f in range(n_frames):
        T = f / FPS
        i = max(k for k, s in enumerate(starts) if s <= T)
        dur, render = scenes[i]
        frame = render(min(T - starts[i], dur))
        if i > 0 and T - starts[i] < FADE:
            pdur, prender = scenes[i - 1]
            prev = prender(min(T - starts[i - 1], pdur))
            a = ease((T - starts[i]) / FADE)
            frame = (prev * (1 - a) + frame * a).astype(np.uint8)
        proc.stdin.write(np.ascontiguousarray(frame).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-l", "--listing", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    a = p.parse_args()
    build(Collection(a.input, a.collection), a.listing, a.output)


if __name__ == "__main__":
    sys.exit(main())
