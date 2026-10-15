"""Image loading, pre-smoothing, and K-Means color quantization in CIELAB."""

import warnings

import cv2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.exceptions import ConvergenceWarning

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def load_image(path, work_size):
    """Read an image as RGB uint8, resized so its long side is `work_size`."""
    data = np.fromfile(str(path), dtype=np.uint8)  # imdecode handles non-ASCII paths
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot decode image: {path}")
    if img.dtype == np.uint16:
        img = (img / 257).astype(np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:  # composite transparency onto white paper
        alpha = img[:, :, 3:4].astype(np.float32) / 255
        img = (img[:, :, :3] * alpha + 255 * (1 - alpha)).astype(np.uint8)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    h, w = rgb.shape[:2]
    f = work_size / max(h, w)
    if abs(f - 1) > 0.01:
        interp = cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC
        rgb = cv2.resize(rgb, (round(w * f), round(h * f)), interpolation=interp)
    return rgb


def smooth(rgb):
    """Flatten noise and soft gradients while keeping shape edges sharp."""
    out = cv2.bilateralFilter(rgb, 7, 30, 7)
    return cv2.medianBlur(out, 3)


def to_lab(rgb):
    """RGB uint8 image -> float32 CIELAB (L in 0..100)."""
    return cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2Lab)


def lab_to_rgb(lab):
    """(N, 3) CIELAB -> (N, 3) RGB uint8."""
    rgb = cv2.cvtColor(np.asarray(lab, np.float32).reshape(-1, 1, 3), cv2.COLOR_Lab2RGB)
    return np.clip(np.rint(rgb.reshape(-1, 3) * 255), 0, 255).astype(np.uint8)


def sample_pixels(lab, n, rng):
    flat = lab.reshape(-1, 3)
    if len(flat) <= n:
        return flat
    return flat[rng.choice(len(flat), n, replace=False)]


def _merge_close(centers, weights, min_delta):
    """Merge clusters whose colors are too close to tell apart on paper."""
    centers, weights = list(centers), list(weights)
    while len(centers) > 1:
        c = np.array(centers)
        d = np.linalg.norm(c[:, None] - c[None], axis=2)
        np.fill_diagonal(d, np.inf)
        i, j = np.unravel_index(np.argmin(d), d.shape)
        if d[i, j] >= min_delta:
            break
        wi, wj = weights[i], weights[j]
        centers[i] = (c[i] * wi + c[j] * wj) / (wi + wj)
        weights[i] = wi + wj
        del centers[j], weights[j]
    return np.array(centers), np.array(weights)


def fit_palette(samples, k, merge_delta, seed):
    """Fit one shared K-color palette (CIELAB) on pixels pooled from the batch.

    Returns centers sorted lightest first, so color 1 is the lightest.
    """
    k = min(k, len(np.unique(samples.round(1), axis=0)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        km = KMeans(n_clusters=k, n_init=4, random_state=seed).fit(samples)
    weights = np.bincount(km.labels_, minlength=k).astype(np.float64)
    centers = km.cluster_centers_.astype(np.float64)
    if merge_delta > 0:
        centers, weights = _merge_close(centers, weights, merge_delta)
    return centers[np.argsort(-centers[:, 0])].astype(np.float32)


def add_detail_colors(palette, pixels, min_pixels, min_delta, max_new=6, seed=0):
    """Add palette colors for small but distinct details K-Means overlooked.

    `pixels` are CIELAB values the current palette represents badly (an eye,
    a beak marking). They are clustered, and clusters with at least
    `min_pixels` members that differ from every palette color by `min_delta`
    are added. Returns the palette sorted lightest first.
    """
    if len(pixels) < min_pixels:
        return palette
    k = int(min(max_new, len(pixels) // min_pixels))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        km = KMeans(n_clusters=k, n_init=4, random_state=seed).fit(pixels)
    counts = np.bincount(km.labels_, minlength=k).astype(np.float64)
    centers = km.cluster_centers_.astype(np.float64)
    far = np.linalg.norm(centers[:, None] - palette[None], axis=2).min(1) >= min_delta
    keep = (counts >= min_pixels) & far
    if not keep.any():
        return palette
    new, _ = _merge_close(centers[keep], counts[keep], min_delta)
    combined = np.vstack([palette, new.astype(np.float32)])
    return combined[np.argsort(-combined[:, 0])]


def assign(lab, palette, chunk=1 << 20):
    """Label every pixel with its nearest palette color.

    Returns (labels int32 HxW, color error HxW as CIE76 delta E).
    """
    flat = lab.reshape(-1, 3)
    labels = np.empty(len(flat), np.int32)
    err = np.empty(len(flat), np.float32)
    for s in range(0, len(flat), chunk):
        d = np.linalg.norm(flat[s:s + chunk, None, :] - palette[None], axis=2)
        labels[s:s + chunk] = d.argmin(1)
        err[s:s + chunk] = d.min(1)
    return labels.reshape(lab.shape[:2]), err.reshape(lab.shape[:2])
