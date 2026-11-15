"""One printable PDF per set with every design's Light_Numbered page (A4, 300 DPI).

    python make_combined_pdf.py

Each page is reduced to 300 DPI and stored as an indexed-color PNG whose compressed data goes into the PDF
unchanged (Flate + PNG predictor), so files stay small without JPEG artifacts around the lines.
"""

import io
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

A4_PT = (595.276, 841.89)
PX = (2480, 3508)              # A4 at 300 DPI

FOLDERS = {
    Path("output/sets/Set1_Cozy_Cottage_Winter/Files"): "Cozy Cottage - Paint by Number",
    Path("output/sets/Set2_Wildlife_Scenic_Nature/Files"): "Wildlife & Nature - Paint by Number",
    Path("output/sets/Set3_Sunsets_Travel/Files"): "Sunsets & Travel - Paint by Number",
    Path("output/collection"): "Paint by Number Collection",
}


def png_parts(img):
    """Indexed PNG -> (palette bytes, bit depth, concatenated IDAT data)."""
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    data = buf.getvalue()
    pos, idat, plte, depth = 8, [], b"", 8
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            depth, ctype = body[8], body[9]
            assert ctype == 3, "expected an indexed PNG"
        elif kind == b"PLTE":
            plte = body
        elif kind == b"IDAT":
            idat.append(body)
        pos += 12 + n
    return plte, depth, b"".join(idat)


def design_palette(design_dir):
    """Gray ramp for lines and numbers plus the design's own colors for the pre-printed details."""
    cols = [(g, g, g) for g in range(0, 256, 2)] + [(255, 255, 255)]
    hexes = (design_dir / "Hex_Codes.txt").read_text(encoding="utf-8")
    cols += [tuple(int(h.split("#")[1][i:i + 2], 16) for i in (0, 2, 4)) for h in hexes.splitlines() if "#" in h]
    return np.array(cols[:256], np.int32)


def page_image(path):
    img = Image.open(path).convert("RGB")
    if img.size != PX:
        img = img.reduce(2) if img.width >= 2 * PX[0] else img
        img = img.crop((0, 0, *PX)) if img.size != PX and img.width >= PX[0] else img.resize(PX, Image.LANCZOS)
    pal = design_palette(path.parent.parent)
    a = np.asarray(img, np.int32)
    key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    uniq, inv = np.unique(key, return_inverse=True)
    rgb = np.stack([uniq >> 16, (uniq >> 8) & 255, uniq & 255], 1)
    nearest = np.empty(len(uniq), np.uint8)
    for i in range(0, len(uniq), 4096):              # exact nearest palette color for every distinct pixel color
        d = ((rgb[i:i + 4096, None, :] - pal[None]) ** 2).sum(2)
        nearest[i:i + 4096] = d.argmin(1)
    out = Image.fromarray(nearest[inv].reshape(key.shape), "P")
    flat = pal.astype(np.uint8).ravel().tolist()
    out.putpalette(flat)
    return out


def write_pdf(pages, out, title):
    objs = []                                            # index i -> object number i + 1

    def add(body):
        objs.append(body)
        return len(objs)

    catalog = add(None)
    pages_obj = add(None)
    kids = []
    w, h = A4_PT
    for img in pages:
        plte, depth, idat = png_parts(img)
        ncol = len(plte) // 3
        im = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /BitsPerComponent %d "
                 b"/ColorSpace [/Indexed /DeviceRGB %d <%s>] /Filter /FlateDecode "
                 b"/DecodeParms << /Predictor 15 /Colors 1 /BitsPerComponent %d /Columns %d >> /Length %d >>\n"
                 b"stream\n" % (img.width, img.height, depth, ncol - 1, plte.hex().encode(), depth, img.width, len(idat))
                 + idat + b"\nendstream")
        content = zlib.compress(b"q %.3f 0 0 %.3f 0 0 cm /Im0 Do Q" % (w, h))
        cs = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(content) + content + b"\nendstream")
        kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.3f %.3f] /Resources << /XObject << /Im0 %d 0 R >> >> "
                        b"/Contents %d 0 R >>" % (pages_obj, w, h, im, cs)))
    objs[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj
    objs[pages_obj - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    info = add(b"<< /Title (%s) /Producer (make_combined_pdf) >>" % title.encode("latin-1"))

    with open(out, "wb") as f:
        f.write(b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, 1):
            offsets.append(f.tell())
            f.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
        xref = f.tell()
        f.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
        for o in offsets:
            f.write(b"%010d 00000 n \n" % o)
        f.write(b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objs) + 1, catalog, info, xref))


def build(folder, title):
    designs = sorted(d for d in folder.glob("Design_*") if (d / "PNG" / "Light_Numbered.png").exists())
    out = folder / f"All_{len(designs)}_Designs_Light_Numbered.pdf"
    write_pdf((page_image(d / "PNG" / "Light_Numbered.png") for d in designs), out, title)
    return out, len(designs)


def main():
    only = sys.argv[1:]
    for folder, title in FOLDERS.items():
        if only and not any(o in str(folder) for o in only):
            continue
        out, n = build(folder, title)
        print(f"{out}: {n} pages, {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
