"""Winter Class Mystery Mural bundle: 3 murals x 4 skills = 12 shared class workbooks, all verified."""
from pathlib import Path

import mural as M
import mural_designs as MD
import questions as Q

OUT = Path(__file__).parent / "output" / "winter_class_mural"
DESIGNS = ["winter_cabin", "penguin_party", "forest_friends"]


def murals():
    """{(design, topic): Mural}"""
    out = {}
    for di, name in enumerate(DESIGNS):
        d = MD.MURALS[name]()
        for ti, topic in enumerate(Q.GENERATORS):
            m = M.make(d, topic, seed_base=di * 50000 + ti * 5000)
            m.title = f"{d['title']}: Class Mystery Mural ({topic})"
            m.seed = 5 + di * 100
            out[(name, topic)] = m
    return out


def path(name, topic):
    title = MD.MURALS[name]()["title"].replace(" ", "_")
    return OUT / topic / f"Class_Mural_{title}_{topic}.xlsx"


def main():
    for (name, topic), m in murals().items():
        x = M.build(m, path(name, topic))
        for line in M.verify(x, m):
            print(line, flush=True)


if __name__ == "__main__":
    main()
