"""Etsy listing video: 1920x1080, 30 fps, ~14.5 s, silent H.264.

Scenes: title card -> answers typed in the sheet and the tree appears -> all 10 pictures -> end card.
Every sheet frame is drawn by render.py, so it matches the real sheet.
"""
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

import designs as D
import make_bundle as B
import make_listing as L
import render as R

VW, VH, FPS, FADE = 1920, 1080, 30, 0.35
OUT = L.OUT / "video" / "christmas_math_mystery_pictures.mp4"
f = R.font


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def base(seed=0):
    return L.bg(seed).resize((VW, VH), Image.LANCZOS)


def title_card(duration):
    bgimg = base(1)
    names = B.ORDER
    thumbs = []
    for n in names:
        p = B.P.Puzzle("x", D.DESIGNS[n], [("1 + 1 =", "2")])
        thumbs.append(L.fit(R.picture(p, {0}, cell=16, gap=1), 150, 170))

    def render(t):
        im = bgimg.copy()
        d = ImageDraw.Draw(im)
        a = ease(t / 0.5)
        d.text((VW // 2, 150 - 30 * (1 - a)), "CHRISTMAS MATH", font=f("bl", 120), fill=L.RED, anchor="mt")
        d.text((VW // 2, 300), "Mystery Pictures", font=f("b", 96), fill=L.INK, anchor="mt")
        d.text((VW // 2, 440), "40 self-checking pixel art activities", font=f("sb", 50), fill=L.GREEN, anchor="mt")
        tw, gap = 150, 22
        x0 = (VW - (10 * tw + 9 * gap)) // 2
        for i, th in enumerate(thumbs):
            k = ease((t - 0.3 - i * 0.1) / 0.3)
            if k <= 0:
                continue
            x, y = x0 + i * (tw + gap), int(650 + 60 * (1 - k))
            card = Image.new("RGB", (tw, 200), "white")
            card.paste(th, ((tw - th.width) // 2, (200 - th.height) // 2))
            im.paste(card, (x, y))
        return np.asarray(im)
    return render


def typing_scene(duration):
    p = B.puzzles_for("Multiplication")[0]
    title = "Christmas Multiplication Mystery Picture"
    # answer sequence: one mistake on question 4, fixed right away
    steps = []
    for i in range(20):
        if i == 3:
            steps.append({3: "27"})          # wrong first
        steps.append({})
    states, typed = [], [None] * 20
    k = 0
    for i in range(20):
        if i == 3:
            typed[3] = "27"
            states.append((list(typed), 3))
        typed[i] = p.questions[i][1]
        states.append((list(typed), min(i + 1, 19)))
    cache = {}
    bgimg = base(2)
    lap_w = 1500

    def frame_for(idx):
        if idx not in cache:
            t, cur = states[idx] if idx >= 0 else ([None] * 20, 0)
            s = R.sheet(p, t, title, cursor=cur)
            lap = R.laptop(R.sheets_window(s, "Christmas Multiplication Mystery Pictures"), lap_w)
            im = bgimg.copy()
            R.shadow(im, lap, ((VW - lap.width) // 2, 140), blur=22, offset=(0, 20), alpha=0.3)
            cache[idx] = im
        return cache[idx]

    start, end = 0.25, duration - 1.0
    per = (end - start) / len(states)

    def render(t):
        idx = int((t - start) / per) if t >= start else -1
        idx = min(idx, len(states) - 1)
        im = frame_for(idx).copy()
        d = ImageDraw.Draw(im)
        msg = "Type the answer..." if idx < 3 else ("Wrong answers reveal nothing" if idx in (3, 4) else
                                                   "...and the mystery picture appears!")
        if idx >= len(states) - 1:
            msg = "20 / 20  Math practice they actually enjoy!"
        tw = d.textlength(msg, font=f("b", 54))
        d.rounded_rectangle([(VW - tw) / 2 - 40, 30, (VW + tw) / 2 + 40, 118], 44, fill=L.RED)
        d.text((VW // 2, 74), msg, font=f("b", 54), fill="white", anchor="mm")
        return np.asarray(im)
    return render


def pictures_scene(duration):
    bgimg = base(3)
    cards = []
    for n in B.ORDER:
        p = B.P.Puzzle("x", D.DESIGNS[n], [("1 + 1 =", "2")])
        c = Image.new("RGB", (300, 360), "white")
        pic = L.fit(R.picture(p, {0}, cell=20, gap=1), 260, 280)
        c.paste(pic, ((300 - pic.width) // 2, 20 + (280 - pic.height) // 2))
        ImageDraw.Draw(c).text((150, 330), D.DESIGNS[n]["title"], font=f("sb", 26), fill=L.INK, anchor="mm")
        cards.append(c)

    def render(t):
        im = bgimg.copy()
        d = ImageDraw.Draw(im)
        d.text((VW // 2, 50), "10 pictures x 4 skills = 40 activities", font=f("b", 70), fill=L.RED, anchor="mt")
        d.text((VW // 2, 145), "Multiplication  •  Division  •  Addition  •  Subtraction", font=f("sb", 44),
               fill=L.INK, anchor="mt")
        x0 = (VW - (5 * 300 + 4 * 40)) // 2
        for i, c in enumerate(cards):
            k = ease((t - i * 0.12) / 0.3)
            if k <= 0:
                continue
            x, y = x0 + (i % 5) * 340, 250 + (i // 5) * 400 + int(40 * (1 - k))
            im.paste(c, (x, y))
        return np.asarray(im)
    return render


def end_card(duration):
    bgimg = base(4)

    def render(t):
        im = bgimg.copy()
        d = ImageDraw.Draw(im)
        d.text((VW // 2, 200), "Christmas Math", font=f("bl", 120), fill=L.RED, anchor="mt")
        d.text((VW // 2, 330), "Mystery Pictures", font=f("b", 100), fill=L.INK, anchor="mt")
        d.text((VW // 2, 480), "Be the teacher they remember!", font=f("pr", 64), fill=L.RED, anchor="mt")
        y = 640
        for line in ["Google Sheets + Excel  •  Google Classroom ready",
                     "Instant feedback  •  Answer keys included", "Grades 2-4  •  Instant download"]:
            d.text((VW // 2, y), line, font=f("sb", 50), fill=L.GREEN if y == 640 else L.INK, anchor="mt")
            y += 95
        return np.asarray(im)
    return render


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scenes = [(7.4, typing_scene(7.4)), (2.8, pictures_scene(2.8)), (2.2, end_card(2.2))]   # start on the reveal
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
    print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
