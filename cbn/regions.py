"""Region cleanup, outline tracing, and number placement.

Works on the quantized label map (HxW array of palette indices). A "region"
is one 4-connected patch of a single color; each one gets an outline and at
least one number.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from scipy import ndimage
from skimage import measure


@dataclass
class Marker:
    x: float        # image pixel coordinates of the number's center
    y: float
    radius: float   # clear space around the point, in pixels
    color: int      # 0-based palette index


def region_map(labels):
    """Split the label map into 4-connected regions numbered 1..n."""
    regions = np.zeros(labels.shape, np.int32)
    n = 0
    for c in np.unique(labels):
        count, comp = cv2.connectedComponents((labels == c).astype(np.uint8), connectivity=4)
        inside = comp > 0
        regions[inside] = comp[inside] + n
        n += count - 1
    return regions, n


def boundary_distance(regions, obstacles=None):
    """Distance (px) from each pixel to the nearest region boundary or image edge.

    Pixels in `obstacles` (pre-printed details) count as boundary, so numbers
    are never placed on top of them.
    """
    edge = np.zeros(regions.shape, bool)
    dx = regions[:, 1:] != regions[:, :-1]
    dy = regions[1:, :] != regions[:-1, :]
    edge[:, 1:] |= dx
    edge[:, :-1] |= dx
    edge[1:, :] |= dy
    edge[:-1, :] |= dy
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    if obstacles is not None:
        edge |= obstacles
    return cv2.distanceTransform((~edge).astype(np.uint8), cv2.DIST_L2, 5)


def _inner_radius(dist, regions, n):
    """Radius of the largest circle that fits in each region (index 0 unused)."""
    r = np.zeros(n + 1, np.float32)
    r[1:] = ndimage.maximum(dist, regions, np.arange(1, n + 1)) + 0.5
    return r


def cleanup(labels, palette_lab, min_area_px, min_radius_px,
            detail_area_px, detail_max_area_px, detail_radius_px, detail_delta=25.0, max_iter=8):
    """Remove regions too small or too thin to hold a number.

    Their pixels are handed to the nearest surviving region, so a thin stroke
    between two shapes is split down the middle instead of turning into a
    tendril of one color.

    Small regions that stand out strongly from what would replace them (an
    eye, a pupil, stripes on a face) are kept as pre-printed details instead
    of disappearing: they are recorded in `details` with their palette index
    and printed already colored, with no number.

    Returns (labels, regions, n, dist, changed_fraction, details) where
    `details` is an HxW array of palette indices, -1 where there is none.
    """
    original = labels
    details = np.full(labels.shape, -1, np.int32)
    color_delta = np.linalg.norm(palette_lab[:, None] - palette_lab[None], axis=2)
    for _ in range(max_iter):
        regions, n = region_map(labels)
        if n <= 1:
            break
        dist = boundary_distance(regions)
        area = np.bincount(regions.ravel(), minlength=n + 1)
        radius = _inner_radius(dist, regions, n)
        bad = (area < min_area_px) | (radius < min_radius_px)
        bad[0] = False
        if not bad[1:].any():
            break
        if bad[1:].all():  # everything is tiny: keep the largest region
            bad[np.argmax(area[1:]) + 1] = False
        bad_px = bad[regions]
        _, (iy, ix) = ndimage.distance_transform_edt(bad_px, return_indices=True)
        merged = labels[iy, ix]

        # Mean color jump each removed region would suffer when merged away.
        jump = np.bincount(regions[bad_px], weights=color_delta[labels[bad_px], merged[bad_px]],
                           minlength=n + 1) / np.maximum(area, 1)
        # Only compact specks qualify: long thin strips (leaf veins, feather
        # edges) are too big to count as a detail and are merged as before.
        keep = (bad & (area < detail_max_area_px) & (jump >= detail_delta)
                & (area >= detail_area_px) & (radius >= detail_radius_px))
        keep_px = keep[regions] & (details < 0)
        details[keep_px] = labels[keep_px]
        labels = merged
    regions, n = region_map(labels)
    dist = boundary_distance(regions, details >= 0)
    return labels, regions, n, dist, float(np.mean(labels != original)), details


def trace_details(details, sigma=0.7, tolerance=0.3):
    """Closed outlines of the pre-printed details, grouped by palette index.

    Returns a list of (palette_index, [polygons]) where each polygon is an
    (N, 2) array of (x, y) image coordinates. Holes are separate polygons, so
    fill them with the even-odd rule.
    """
    out = []
    for c in np.unique(details[details >= 0]):
        mask = np.pad((details == c).astype(np.float32), 1)
        mask = cv2.GaussianBlur(mask, (0, 0), sigma)
        polys = [measure.approximate_polygon(line, tolerance)[:, ::-1] - 0.5
                 for line in measure.find_contours(mask, 0.5)]
        polys = [p for p in polys if len(p) >= 3]
        if polys:
            out.append((int(c), polys))
    return out


def trace_outlines(labels, sigma=1.0, tolerance=0.3):
    """Smooth vector outlines for every color boundary.

    Each color's mask is blurred and traced at the 0.5 iso-level. Where two
    colors meet, their blurred masks sum to 1, so both colors trace the same
    curve and shared edges coincide instead of doubling up. The blur also
    removes the pixel staircase.

    Returns a list of (N, 2) float arrays of (x, y) image coordinates.
    """
    outlines = []
    for c in np.unique(labels):
        mask = cv2.GaussianBlur((labels == c).astype(np.float32), (0, 0), sigma)
        for line in measure.find_contours(mask, 0.5):
            line = measure.approximate_polygon(line, tolerance)
            if len(line) >= 2:
                outlines.append(line[:, ::-1] + 0.5)  # (row, col) -> (x, y) pixel centers
    return outlines


def _contains(sub, cx, cy, need):
    """cv2.pointPolygonTest on the region's outer contour: inside with `need` px to spare."""
    contours, _ = cv2.findContours(sub.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False
    outer = max(contours, key=cv2.contourArea)
    return cv2.pointPolygonTest(outer, (float(cx), float(cy)), True) >= need


def place_numbers(labels, regions, n, dist, spacing_px, max_per_region=6):
    """Pick where each region's number goes.

    Primary spot is the centroid from the image moments (m10/m00, m01/m00),
    accepted when cv2.pointPolygonTest says it is inside the shape and the
    distance map says it is not in a hole or squeezed against an edge. Otherwise
    the number goes at the region's widest point (distance-transform maximum).
    Large regions get extra copies of the number about `spacing_px` apart.
    """
    h, w = regions.shape
    yy, xx = np.mgrid[0:h, 0:w]
    flat = regions.ravel()
    m00 = np.bincount(flat, minlength=n + 1).astype(np.float64)
    m10 = np.bincount(flat, weights=xx.ravel(), minlength=n + 1)
    m01 = np.bincount(flat, weights=yy.ravel(), minlength=n + 1)
    region_color = np.zeros(n + 1, np.int32)
    region_color[flat] = labels.ravel()

    markers = []
    for rid, sl in enumerate(ndimage.find_objects(regions), start=1):
        if sl is None:
            continue
        sub = regions[sl] == rid
        clear = np.where(sub, dist[sl], 0)
        oy, ox = sl[0].start, sl[1].start
        best = float(clear.max())
        by, bx = np.unravel_index(np.argmax(clear), clear.shape)
        color = int(region_color[rid])

        cx, cy = m10[rid] / m00[rid], m01[rid] / m00[rid]
        px, py = int(cx) - ox, int(cy) - oy
        if (0 <= py < sub.shape[0] and 0 <= px < sub.shape[1] and sub[py, px]
                and clear[py, px] >= 0.7 * best
                and _contains(sub, cx - ox, cy - oy, clear[py, px])):
            spot = (cx, cy, float(clear[py, px]))
        else:
            spot = (bx + ox + 0.5, by + oy + 0.5, best)
        markers.append(Marker(spot[0], spot[1], spot[2] + 0.5, color))

        if max(sub.shape) < spacing_px:
            continue
        placed = [(spot[0] - ox, spot[1] - oy)]
        gy, gx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
        open_space = clear.copy()
        floor = max(best * 0.5, 3.0)
        while len(placed) < max_per_region:
            px, py = placed[-1]
            open_space[(gx - px) ** 2 + (gy - py) ** 2 < spacing_px ** 2] = 0
            ny, nx = np.unravel_index(np.argmax(open_space), open_space.shape)
            if open_space[ny, nx] < floor:
                break
            placed.append((nx + 0.5, ny + 0.5))
            markers.append(Marker(nx + ox + 0.5, ny + oy + 0.5, float(open_space[ny, nx]) + 0.5, color))
    return markers
