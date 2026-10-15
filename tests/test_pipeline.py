import re

import cv2
import numpy as np

from cbn.cli import main


def make_image(path, seed):
    """Flat-color illustration: overlapping shapes, a black stroke, a little noise."""
    rng = np.random.default_rng(seed)
    img = np.full((1000, 800, 3), (235, 225, 200), np.uint8)
    colors = [(200, 80, 60), (60, 120, 180), (90, 160, 90), (240, 190, 60), (150, 90, 160), (40, 60, 90)]
    for _ in range(25):
        color = colors[rng.integers(len(colors))]
        center = tuple(int(v) for v in rng.integers(0, 800, 2))
        if rng.random() < 0.5:
            cv2.circle(img, center, int(rng.integers(30, 160)), color, -1)
        else:
            axes = tuple(int(v) for v in rng.integers(20, 200, 2))
            cv2.ellipse(img, center, axes, float(rng.integers(180)), 0, 360, color, -1)
    cv2.line(img, (0, 500), (800, 450), (20, 20, 20), 4)
    img = np.clip(img.astype(int) + rng.integers(-6, 7, img.shape), 0, 255).astype(np.uint8)
    cv2.imwrite(str(path), img)


def count_pages(pdf):
    return len(re.findall(rb"/Type /Page\b(?!s)", pdf.read_bytes()))


def test_end_to_end(tmp_path):
    src, out = tmp_path / "in", tmp_path / "out"
    src.mkdir()
    for i in range(2):
        make_image(src / f"img{i}.png", i)

    assert main(["-i", str(src), "-o", str(out), "--title", "Test Book", "--work-size", "800"]) == 0

    for size in ("letter", "a4", "16x20"):
        pdf = out / f"test-book_{size}.pdf"
        assert pdf.read_bytes().startswith(b"%PDF")
        # 2 templates + 2 blank backs + 1 gallery page + 1 master key
        assert count_pages(pdf) == 6
    assert list((out / "previews").glob("img0_*_lineart.png"))
    assert "Palette:" in (out / "report.txt").read_text()
