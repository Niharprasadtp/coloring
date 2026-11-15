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
            lv = level(folder, path)
            with tempfile.TemporaryDirectory() as tmp:
                src, out = Path(tmp) / "in", Path(tmp) / "out"
                src.mkdir()
                shutil.copy(path, src / path.name)
                subprocess.run([PY, str(ROOT / "build_collection.py"), "-i", str(src), "-o", str(out), "--no-sparkle"]
                               + SETTINGS[lv], check=False, capture_output=True)
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
