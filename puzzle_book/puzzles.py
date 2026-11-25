"""Puzzle generators for the large-print puzzle book.

Every generator is seeded (same seed -> same puzzle) and has a matching verify_* function that
re-checks the finished puzzle independently. make_book.py refuses to write a PDF if any check fails.
"""
from __future__ import annotations

import random
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- Sudoku


@dataclass
class Sudoku:
    n: int                 # 6 or 9
    br: int                # box height
    bc: int                # box width
    puzzle: list           # n x n, 0 = blank
    solution: list


def _peers(n, br, bc):
    peers = {}
    for r in range(n):
        for c in range(n):
            p = {(r, k) for k in range(n)} | {(k, c) for k in range(n)}
            r0, c0 = r - r % br, c - c % bc
            p |= {(r0 + i, c0 + j) for i in range(br) for j in range(bc)}
            p.discard((r, c))
            peers[r, c] = p
    return peers


def _units(n, br, bc):
    units = [[(r, c) for c in range(n)] for r in range(n)]
    units += [[(r, c) for r in range(n)] for c in range(n)]
    units += [[(r0 + i, c0 + j) for i in range(br) for j in range(bc)]
              for r0 in range(0, n, br) for c0 in range(0, n, bc)]
    return units


def count_solutions(grid, n, br, bc, limit=2) -> int:
    """Backtracking solution counter (stops at `limit`)."""
    g = [row[:] for row in grid]
    peers = _peers(n, br, bc)
    found = 0

    def cands(r, c):
        return set(range(1, n + 1)) - {g[pr][pc] for pr, pc in peers[r, c]}

    def solve():
        nonlocal found
        best, best_c = None, None
        for r in range(n):
            for c in range(n):
                if g[r][c] == 0:
                    cs = cands(r, c)
                    if not cs:
                        return
                    if best is None or len(cs) < len(best_c):
                        best, best_c = (r, c), cs
        if best is None:
            found += 1
            return
        r, c = best
        for v in best_c:
            g[r][c] = v
            solve()
            if found >= limit:
                break
        g[r][c] = 0

    solve()
    return found


def logic_solve(grid, n, br, bc):
    """Solve with naked and hidden singles only (no guessing). Returns the grid, or None if stuck."""
    g = [row[:] for row in grid]
    peers, units = _peers(n, br, bc), _units(n, br, bc)
    while True:
        changed = False
        for r in range(n):
            for c in range(n):
                if g[r][c] == 0:
                    cs = set(range(1, n + 1)) - {g[pr][pc] for pr, pc in peers[r, c]}
                    if len(cs) == 1:
                        g[r][c] = cs.pop(); changed = True
        for unit in units:
            for v in range(1, n + 1):
                if any(g[r][c] == v for r, c in unit):
                    continue
                spots = [(r, c) for r, c in unit if g[r][c] == 0
                         and all(g[pr][pc] != v for pr, pc in peers[r, c])]
                if len(spots) == 1:
                    r, c = spots[0]; g[r][c] = v; changed = True
        if all(all(row) for row in g):
            return g
        if not changed:
            return None


def _full_grid(n, br, bc, rng):
    g = [[0] * n for _ in range(n)]
    peers = _peers(n, br, bc)

    def fill(i):
        if i == n * n:
            return True
        r, c = divmod(i, n)
        vals = list(range(1, n + 1)); rng.shuffle(vals)
        for v in vals:
            if all(g[pr][pc] != v for pr, pc in peers[r, c]):
                g[r][c] = v
                if fill(i + 1):
                    return True
        g[r][c] = 0
        return False

    fill(0)
    return g


def make_sudoku(n: int, givens: int, seed: int) -> Sudoku:
    """Remove clues in symmetric pairs while the puzzle stays unique AND solvable by singles."""
    br, bc = (2, 3) if n == 6 else (3, 3)
    rng = random.Random(seed)
    sol = _full_grid(n, br, bc, rng)
    puz = [row[:] for row in sol]
    cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(cells)
    count = n * n
    for r, c in cells:
        if count <= givens or puz[r][c] == 0:
            continue
        pair = {(r, c), (n - 1 - r, n - 1 - c)}
        saved = {p: puz[p[0]][p[1]] for p in pair}
        for pr, pc in pair:
            puz[pr][pc] = 0
        if count_solutions(puz, n, br, bc) == 1 and logic_solve(puz, n, br, bc) is not None:
            count -= len(pair)
        else:
            for (pr, pc), v in saved.items():
                puz[pr][pc] = v
    return Sudoku(n, br, bc, puz, sol)


def verify_sudoku(s: Sudoku) -> int:
    n, br, bc = s.n, s.br, s.bc
    full = set(range(1, n + 1))
    for unit in _units(n, br, bc):
        assert {s.solution[r][c] for r, c in unit} == full, "solution breaks a rule"
    for r in range(n):
        for c in range(n):
            assert s.puzzle[r][c] in (0, s.solution[r][c]), "clue disagrees with solution"
    assert count_solutions(s.puzzle, n, br, bc) == 1, "puzzle does not have exactly one solution"
    assert logic_solve(s.puzzle, n, br, bc) == s.solution, "puzzle needs guessing"
    return sum(v != 0 for row in s.puzzle for v in row)


# ---------------------------------------------------------------- Word search

ALL_DIRS = [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]
# Never let random filler spell these, in any direction.
BLOCKED = ["SEX", "FUCK", "SHIT", "CUNT", "DICK", "COCK", "PISS", "TWAT", "SLUT", "WHORE", "FAG",
           "NAZI", "RAPE", "KILL", "DEAD", "ASS", "TIT", "CUM", "FART", "BUTT", "PORN", "KKK", "NIGG"]


@dataclass
class WordSearch:
    theme: str
    words: list
    grid: list                                     # list of strings
    places: dict = field(default_factory=dict)     # word -> (r, c, dr, dc)


def _occurrences(grid, word):
    n, m = len(grid), len(grid[0])
    hits = []
    for r in range(n):
        for c in range(m):
            for dr, dc in ALL_DIRS:
                rr, cc = r + dr * (len(word) - 1), c + dc * (len(word) - 1)
                if 0 <= rr < n and 0 <= cc < m and all(
                        grid[r + dr * i][c + dc * i] == ch for i, ch in enumerate(word)):
                    hits.append((r, c, dr, dc))
    return hits


def make_wordsearch(theme, words, size, dirs, seed) -> WordSearch:
    rng = random.Random(seed)
    for _ in range(500):
        g = [[""] * size for _ in range(size)]
        places = {}
        ok = True
        for w in sorted(words, key=len, reverse=True):
            spots = []
            for dr, dc in dirs:
                for r in range(size):
                    for c in range(size):
                        rr, cc = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
                        if not (0 <= rr < size and 0 <= cc < size):
                            continue
                        if all(g[r + dr * i][c + dc * i] in ("", ch) for i, ch in enumerate(w)):
                            spots.append((r, c, dr, dc))
            if not spots:
                ok = False; break
            r, c, dr, dc = rng.choice(spots)
            for i, ch in enumerate(w):
                g[r + dr * i][c + dc * i] = ch
            places[w] = (r, c, dr, dc)
        if not ok:
            continue
        # filler: half from the puzzle's own letters (so words do not stand out), half plain alphabet
        pool = "".join(words) + "ABCDEFGHIKLMNOPRSTUWY" * 2
        filler = [(r, c) for r in range(size) for c in range(size) if not g[r][c]]
        for r, c in filler:
            g[r][c] = rng.choice(pool)
        filler_set = set(filler)
        # repair: re-roll a filler letter inside any accidental extra copy / blocked word
        for _ in range(3000):
            grid = ["".join(row) for row in g]
            bad = []
            for w in list(words) + BLOCKED:
                for hit in _occurrences(grid, w):
                    if hit == places.get(w):
                        continue
                    cells = _cells(hit, len(w))
                    if w in BLOCKED and _inside_word(cells, places):
                        continue                      # e.g. ASS inside WASSAIL: part of a real word
                    free = [p for p in cells if p in filler_set]
                    bad += free if free else [None]   # None: made only of placed letters -> re-place
            if not bad:
                break
            if None in bad:
                break
            r, c = rng.choice(bad)
            g[r][c] = rng.choice(pool)
        ws = WordSearch(theme, list(words), ["".join(row) for row in g], places)
        try:
            verify_wordsearch(ws)
            return ws
        except AssertionError:
            continue
    raise RuntimeError(f"could not build word search {theme}")


def verify_wordsearch(ws: WordSearch):
    for w in ws.words:
        hits = _occurrences(ws.grid, w)
        assert len(hits) == 1, f"{w} found {len(hits)} times"
        assert hits[0] == ws.places[w], f"{w} not where the answer key says"
    for bad in BLOCKED:
        for hit in _occurrences(ws.grid, bad):
            assert _inside_word(_cells(hit, len(bad)), ws.places), f"filler spells {bad}"


def _cells(hit, length):
    r, c, dr, dc = hit
    return [(r + dr * i, c + dc * i) for i in range(length)]


def _inside_word(cells, places):
    """True if every cell lies within one placed word, in the same line."""
    return any(set(cells) <= set(_cells(p, len(w))) for w, p in places.items())


# ---------------------------------------------------------------- Maze


@dataclass
class Maze:
    w: int
    h: int
    open: set           # {((r, c), (r2, c2))} both orders
    path: list          # cells from start (0, 0) to finish (h-1, w-1)


def make_maze(w, h, seed) -> Maze:
    rng = random.Random(seed)
    seen = {(0, 0)}
    stack = [(0, 0)]
    opened = set()
    while stack:
        r, c = stack[-1]
        nb = [(r + dr, c + dc) for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
              if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in seen]
        if not nb:
            stack.pop(); continue
        nxt = rng.choice(nb)
        opened |= {((r, c), nxt), (nxt, (r, c))}
        seen.add(nxt)
        stack.append(nxt)
    return Maze(w, h, opened, _maze_path(w, h, opened))


def _maze_path(w, h, opened):
    start, goal = (0, 0), (h - 1, w - 1)
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        r, c = cur
        for nxt in ((r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c)):
            if (cur, nxt) in opened and nxt not in prev:
                prev[nxt] = cur; q.append(nxt)
    path, cur = [], goal
    while cur is not None:
        path.append(cur); cur = prev[cur]
    return path[::-1]


def verify_maze(m: Maze):
    cells = m.w * m.h
    assert len(m.open) // 2 == cells - 1, "maze has loops (more than one route)"
    path = _maze_path(m.w, m.h, m.open)
    assert path[0] == (0, 0) and path[-1] == (m.h - 1, m.w - 1), "finish not reachable"
    assert path == m.path
    # connected + (cells - 1) passages -> a tree -> exactly one route
    reach, q = {(0, 0)}, deque([(0, 0)])
    while q:
        r, c = q.popleft()
        for nxt in ((r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c)):
            if ((r, c), nxt) in m.open and nxt not in reach:
                reach.add(nxt); q.append(nxt)
    assert len(reach) == cells, "some parts of the maze are walled off"


# ---------------------------------------------------------------- Cryptogram

ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class Cryptogram:
    text: str            # plain text, upper case
    source: str          # song title shown in the answer key
    key: dict            # plain letter -> code letter
    hints: list          # plain letters given away

    @property
    def coded(self):
        return "".join(self.key.get(ch, ch) for ch in self.text)


def make_cryptogram(text, source, n_hints, seed) -> Cryptogram:
    rng = random.Random(seed)
    while True:
        perm = list(ABC); rng.shuffle(perm)
        if all(a != b for a, b in zip(ABC, perm)):
            break
    key = dict(zip(ABC, perm))
    # hints: most common letters first (most helpful), but never more than half of any word
    letters = sorted({ch for ch in text if ch in ABC}, key=lambda ch: (-text.count(ch), ch))
    hints = []
    for ch in letters:
        if len(hints) < n_hints and _hints_fair(text, hints + [ch]):
            hints.append(ch)
    return Cryptogram(text, source, key, hints)


def _words(text):
    return [w for w in re.split(r"[^A-Z]+", text) if w]


def _hints_fair(text, hints):
    return all(sum(ch in hints for ch in w) <= len(w) // 2 for w in _words(text))


def verify_cryptogram(cg: Cryptogram):
    assert len(set(cg.key.values())) == 26, "two letters share a code"
    assert all(a != b for a, b in cg.key.items()), "a letter stands for itself"
    back = {v: k for k, v in cg.key.items()}
    assert "".join(back.get(ch, ch) for ch in cg.coded) == cg.text, "does not decode"
    assert _hints_fair(cg.text, cg.hints), "hints give away too much of a word"


# ---------------------------------------------------------------- Number patterns


@dataclass
class Pattern:
    shown: list
    answer: int
    rule: str


def make_patterns(level, count, seed, used=None) -> list[Pattern]:
    """`used` is shared across pages so no sequence repeats in the book. Kinds are spread evenly over the page."""
    rng = random.Random(seed)
    out, used = [], (set() if used is None else used)
    kinds = {}
    while len(out) < count:
        kind_list = ["add", "sub", "double"] if level == 1 else ["grow", "alt", "double", "add_big", "triple"]
        cap = -(-count // len(kind_list))
        kind = rng.choice(kind_list)
        if kind == "add":
            a, d = rng.randint(1, 20), rng.choice([2, 3, 4, 5, 10]); seq = [a + d * i for i in range(6)]
            rule = f"add {d} each time"
        elif kind == "add_big":
            a, d = rng.randint(5, 40), rng.choice([6, 7, 8, 9, 11, 12, 15, 25]); seq = [a + d * i for i in range(6)]
            rule = f"add {d} each time"
        elif kind == "sub":
            d = rng.choice([2, 3, 5, 10]); a = d * 5 + rng.randint(1, 30); seq = [a - d * i for i in range(6)]
            rule = f"take away {d} each time"
        elif kind == "double":
            a = rng.randint(1, 6); seq = [a * 2 ** i for i in range(6)]
            rule = "double each time"
        elif kind == "triple":
            a = rng.randint(1, 3); seq = [a * 3 ** i for i in range(6)]
            rule = "multiply by 3 each time"
        elif kind == "grow":
            a, s = rng.randint(1, 10), rng.randint(1, 3); seq = [a]
            for i in range(5):
                seq.append(seq[-1] + s + i)
            rule = f"add {s}, then {s + 1}, then {s + 2}... (one more each time)"
        else:  # alt
            a, p, q = rng.randint(1, 20), rng.randint(2, 9), rng.randint(2, 9)
            if p == q:
                continue
            seq = [a]
            for i in range(5):
                seq.append(seq[-1] + (p if i % 2 == 0 else q))
            rule = f"add {p}, then add {q}, and repeat"
        if tuple(seq) in used or min(seq) < 0 or max(seq) > 999 or kinds.get(kind, 0) >= cap:
            continue
        if fitting_answers(seq[:5]) != {seq[5]}:
            continue                                  # another common rule gives a different answer
        used.add(tuple(seq)); kinds[kind] = kinds.get(kind, 0) + 1
        out.append(Pattern(seq[:5], seq[5], rule))
    return out


def fitting_answers(shown) -> set:
    """Next term predicted by every common rule that fits all shown numbers."""
    d = [b - a for a, b in zip(shown, shown[1:])]
    dd = [b - a for a, b in zip(d, d[1:])]
    out = set()
    if len(set(d)) == 1:                                        # add the same amount
        out.add(shown[-1] + d[0])
    if all(a and b % a == 0 for a, b in zip(shown, shown[1:])) and len({b // a for a, b in zip(shown, shown[1:])}) == 1:
        out.add(shown[-1] * (shown[1] // shown[0]))             # multiply by the same amount
    if len(set(dd)) == 1:                                       # gaps grow by the same amount
        out.add(shown[-1] + d[-1] + dd[0])
    if d[0::2] == [d[0]] * len(d[0::2]) and d[1::2] == [d[1]] * len(d[1::2]):
        out.add(shown[-1] + d[len(d) % 2])                      # two gaps that alternate
    if all(shown[i] == shown[i - 1] + shown[i - 2] for i in range(2, len(shown))):
        out.add(shown[-1] + shown[-2])                          # add the two before
    return out


def verify_pattern(p: Pattern):
    assert fitting_answers(p.shown) == {p.answer}, f"{p.shown} has more than one sensible answer"
    seq = p.shown + [p.answer]
    rule = p.rule
    if rule.startswith("add") and "then" not in rule:
        d = int(rule.split()[1]); assert all(b - a == d for a, b in zip(seq, seq[1:]))
    elif rule.startswith("take away"):
        d = int(rule.split()[2]); assert all(a - b == d for a, b in zip(seq, seq[1:]))
    elif rule == "double each time":
        assert all(b == 2 * a for a, b in zip(seq, seq[1:]))
    elif rule == "multiply by 3 each time":
        assert all(b == 3 * a for a, b in zip(seq, seq[1:]))
    elif "one more each time" in rule:
        diffs = [b - a for a, b in zip(seq, seq[1:])]
        assert all(y - x == 1 for x, y in zip(diffs, diffs[1:]))
    else:
        p_, q_ = map(int, re.findall(r"add (\d+)", rule))
        diffs = [b - a for a, b in zip(seq, seq[1:])]
        assert diffs == [p_, q_, p_, q_, p_]


# ---------------------------------------------------------------- Word scramble

DICT_FILE = Path("/usr/share/dict/words")


def _dictionary():
    words = set()
    if DICT_FILE.exists():
        for w in DICT_FILE.read_text(encoding="utf-8", errors="ignore").split():
            if w.isalpha() and w.isascii():
                words.add(w.upper())
    return words


def scramble_ok(word, dictionary) -> bool:
    """True if no other dictionary word uses exactly the same letters."""
    key = sorted(word)
    return not any(sorted(w) == key for w in dictionary if len(w) == len(word) and w != word)


def make_scrambles(words, seed, dictionary):
    rng = random.Random(seed)
    out = []
    for w in words:
        assert scramble_ok(w, dictionary), f"{w} has another anagram"
        for _ in range(200):
            s = list(w); rng.shuffle(s); s = "".join(s)
            # must look different: not the word, not a real word, first two letters moved
            if s != w and s not in dictionary and s[:2] != w[:2] and s[-2:] != w[-2:]:
                break
        out.append((s, w))
    return out


def verify_scramble(pair, dictionary):
    s, w = pair
    assert sorted(s) == sorted(w) and s != w
    assert s not in dictionary, f"scramble {s} is itself a word"
    assert scramble_ok(w, dictionary), f"{w} has another anagram"
