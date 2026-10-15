"""PNG previews for checking results by eye before opening the PDFs."""

import cv2
import numpy as np


def render_lineart(shape, outlines, markers, details=(), detail_style="outline", scale=1.0):
    """Line art with numbers and pre-printed details, as an RGB image."""
    h, w = shape
    canvas = np.full((round(h * scale), round(w * scale), 3), 255, np.uint8)
    pts = [np.round(o * scale * 16).astype(np.int32) for o in outlines]  # 4-bit subpixel
    cv2.polylines(canvas, pts, False, (110, 110, 110), 1, cv2.LINE_AA, shift=4)
    for rgb, polys in details:
        pts = [np.round(p * scale * 16).astype(np.int32) for p in polys]
        if detail_style == "outline":
            cv2.polylines(canvas, pts, True, (110, 110, 110), 1, cv2.LINE_AA, shift=4)
        else:
            cv2.fillPoly(canvas, pts, tuple(int(v) for v in rgb), cv2.LINE_AA, shift=4)
    for m in markers:
        text = str(m.color + 1)
        font_scale = float(np.clip(m.radius * scale / (14 if len(text) > 1 else 10), 0.25, 0.9))
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        org = (round(m.x * scale - tw / 2), round(m.y * scale + th / 2))
        cv2.putText(canvas, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (90, 90, 90), 1, cv2.LINE_AA)
    return canvas


def save_png(path, image):
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", image)
    if not ok:
        raise IOError(f"cannot encode {path}")
    buf.tofile(str(path))
