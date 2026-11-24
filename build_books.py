"""Build every image in input_books/<folder>/ as its own paint-by-number design, with settings per level.

    .venv/Scripts/python build_books.py [folder ...]     # default: book1 book2 book3 scenery

Level comes from the file name: scenery files carry EASY/MEDIUM/HARD/EXPERT/EXTRA_HARD, book files are
numbered so that positions 1-3, 4-6, 7-8 and 9-10 of every 10 are easy, medium, hard and expert.
Output: output/books_build/<folder>/<image stem>/ (same layout as output/collection/Design_NN).
A summary with zone counts goes to output/books_build/summary.tsv. Already-built designs are skipped.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "input_books"
OUT = ROOT / "output" / "books_build"
PY = sys.executable

SETTINGS = {  # level -> build_collection.py arguments
    "EASY": ["--difficulty", "intermediate"],
    "MEDIUM": ["--difficulty", "expert"],
    "HARD": ["--difficulty", "expert"],
    "EXPERT": ["--difficulty", "expert", "-k", "28"],
    "EXTRA_HARD": ["--difficulty", "expert", "-k", "32", "--min-area", "3", "--min-radius", "1.8"],
}


# "Simple" series (anime books): few colors per page, similar shades merged, few extra detail colors.
MINIMAL = {
    "EASY": ["--difficulty", "intermediate", "-k", "8", "--merge-delta", "12", "--residual-delta", "40"],
    "MEDIUM": ["--difficulty", "intermediate", "-k", "10", "--merge-delta", "12", "--residual-delta", "40"],
    "HARD": ["--difficulty", "intermediate", "-k", "12", "--merge-delta", "12", "--residual-delta", "40"],
}


# Car book: 01-05 beginner, 06-10 easy, 11-15 medium, 16+ expert; light numbers on the printable page.
CARS = {
    # Fidelity first: the car must look like the original (wheels, rims, lights, trim), so similar shades
    # are kept apart (low merge-delta) and small parts survive (low min-area). Difficulty comes from the art.
    "BEGINNER": ["--difficulty", "intermediate", "-k", "14", "--merge-delta", "5", "--residual-delta", "12",
                 "--min-area", "12", "--min-radius", "3"],
    "EASY": ["--difficulty", "intermediate", "-k", "20", "--merge-delta", "5", "--residual-delta", "12",
             "--min-area", "8", "--min-radius", "2.6"],
    "MEDIUM": ["--difficulty", "expert", "-k", "28", "--merge-delta", "4", "--residual-delta", "10",
               "--min-area", "5", "--min-radius", "2"],
    "EXPERT": ["--difficulty", "expert", "-k", "32", "--merge-delta", "4", "--residual-delta", "10",
               "--min-area", "4", "--min-radius", "1.8"],
}
CARS = {k: v + ["--light-numbers"] for k, v in CARS.items()}


def settings(folder, path):
    """build_collection.py arguments for this image (anime books: 15 pages each, minimal colors)."""
    if folder == "cars":
        n = int(path.name[:2])
        return "BEGINNER" if n <= 5 else "EASY" if n <= 10 else "MEDIUM" if n <= 15 else "EXPERT", CARS
    if folder.startswith("anime"):
        pos = (int(path.name[:2]) - 1) % 15
        return "EASY" if pos < 5 else "MEDIUM" if pos < 11 else "HARD", MINIMAL
    return level(folder, path), SETTINGS


def level(folder, path):
    if folder == "scenery":
        m = re.search(r"_(EASY|MEDIUM|HARD|EXPERT|EXTRA_HARD)_", path.name)
        return m.group(1)
    n = int(path.name[:2])
    pos = (n - 1) % 10
    return "EASY" if pos < 3 else "MEDIUM" if pos < 6 else "HARD" if pos < 8 else "EXPERT"


def main():
    folders = sys.argv[1:] or ["book1", "book2", "book3", "scenery"]
    OUT.mkdir(parents=True, exist_ok=True)
    summary = OUT / "summary.tsv"
    if not summary.exists():
        summary.write_text("folder\tdesign\tlevel\tregions\tcolors\tpre_printed\tdetail_merged\n", encoding="utf-8")
    for folder in folders:
        for path in sorted((SRC / folder).glob("*.png")):
            dest = OUT / folder / path.stem
            if (dest / "report.txt").exists():
                continue
            lv, table = settings(folder, path)
            with tempfile.TemporaryDirectory() as tmp:
                src, out = Path(tmp) / "in", Path(tmp) / "out"
                src.mkdir()
                shutil.copy(path, src / path.name)
                subprocess.run([PY, str(ROOT / "build_collection.py"), "-i", str(src), "-o", str(out), "--no-sparkle"]
                               + table[lv], check=False, capture_output=True)
                built = out / "Design_01"
                if not (built / "report.txt").exists():
                    print(f"FAILED {folder}/{path.stem}", flush=True)
                    continue
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(built, dest)
            rep = (dest / "report.txt").read_text(encoding="utf-8")
            m = re.search(r"(\d+) regions, \d+ numbers, (\d+) colors, (\d+) pre-printed details.*detail merged (\d+)%", rep)
            row = [folder, path.stem, lv] + (list(m.groups()) if m else ["?"] * 4)
            with summary.open("a", encoding="utf-8") as f:
                f.write("\t".join(row) + "\n")
            print("\t".join(row), flush=True)


if __name__ == "__main__":
    main()
