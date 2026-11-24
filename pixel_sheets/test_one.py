"""Build + verify one test puzzle (Christmas tree, multiplication)."""
from pathlib import Path

import designs as D
import pixelsheet as P
import questions as Q

OUT = Path(__file__).parent / "output" / "test"

p = P.Puzzle("Tree", D.DESIGNS["tree"], Q.multiplication(20, seed=7))
x = P.build([p], OUT / "test_tree.xlsx", "Christmas Multiplication Mystery Picture")
for line in P.verify(x, [p]):
    print(line)
# copy with every answer typed in (to test in Google Sheets / Excel)
filled = P.build([p], OUT / "test_tree_ALL_ANSWERED.xlsx", "Christmas Multiplication Mystery Picture",
                 answers={"Tree": [int(a) for _, a in p.questions]})
half = P.build([p], OUT / "test_tree_HALF.xlsx", "Christmas Multiplication Mystery Picture",
               answers={"Tree": [int(a) if i % 2 == 0 else int(a) + 1 for i, (_, a) in enumerate(p.questions)]})
P.preview(p, OUT / "preview_full.png", 1.0)
P.preview(p, OUT / "preview_half.png", 0.5)
print("written to", OUT)
