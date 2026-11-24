"""Christmas Math Mystery Pictures bundle: 10 pictures x 4 topics, each topic one workbook."""
from pathlib import Path

import designs as D
import pixelsheet as P
import questions as Q

OUT = Path(__file__).parent / "output" / "christmas_math_bundle"
ORDER = ["tree", "snowman", "present", "gingerbread", "santa_hat",
         "reindeer", "candy_cane", "stocking", "ornament", "cocoa"]
N_QUESTIONS = 20


def puzzles_for(topic: str) -> list[P.Puzzle]:
    t = list(Q.GENERATORS).index(topic)
    gen = Q.GENERATORS[topic]
    return [P.Puzzle(f"Picture {i + 1}", D.DESIGNS[name], gen(N_QUESTIONS, seed=t * 100 + i), seed=i + 11)
            for i, name in enumerate(ORDER)]


def workbook_path(topic: str) -> Path:
    return OUT / f"Christmas_{topic}_Mystery_Pictures.xlsx"


def main():
    for topic in Q.GENERATORS:
        pz = puzzles_for(topic)
        x = P.build(pz, workbook_path(topic), f"Christmas {topic} Mystery Picture")
        print(f"\n{x.name}")
        for line in P.verify(x, pz):
            print("  ", line)
        for p in pz:
            P.preview(p, OUT / "previews" / f"{topic}_{p.name.replace(' ', '_')}_full.png", 1.0)
            P.preview(p, OUT / "previews" / f"{topic}_{p.name.replace(' ', '_')}_half.png", 0.5)


if __name__ == "__main__":
    main()
