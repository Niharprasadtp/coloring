"""Puzzle book: every generated puzzle must pass its independent checks."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "puzzle_book"))
import puzzles as P  # noqa: E402


@pytest.mark.parametrize("n,givens", [(6, 14), (9, 32)])
def test_sudoku_unique_and_no_guessing(n, givens):
    s = P.make_sudoku(n, givens, seed=3)
    P.verify_sudoku(s)


def test_sudoku_counter_detects_two_solutions():
    empty = [[0] * 6 for _ in range(6)]
    assert P.count_solutions(empty, 6, 2, 3) == 2


def test_wordsearch_each_word_once():
    ws = P.make_wordsearch("t", ["SNOW", "STAR", "BELLS", "PIE", "WASSAIL"], 9, P.ALL_DIRS[:4], seed=1)
    P.verify_wordsearch(ws)
    grid = [row for row in ws.grid]
    grid[0] = "SEX" + grid[0][3:]                    # plant a blocked word in filler
    with pytest.raises(AssertionError):
        P.verify_wordsearch(P.WordSearch("t", ws.words, grid, ws.places))


def test_maze_single_route():
    m = P.make_maze(10, 12, seed=2)
    P.verify_maze(m)
    extra = set(m.open)                              # knock down one more wall -> a loop
    for r in range(m.h):
        for c in range(m.w - 1):
            if ((r, c), (r, c + 1)) not in extra:
                extra |= {((r, c), (r, c + 1)), ((r, c + 1), (r, c))}
                break
        else:
            continue
        break
    with pytest.raises(AssertionError):
        P.verify_maze(P.Maze(m.w, m.h, extra, m.path))


def test_cryptogram_fair_hints():
    cg = P.make_cryptogram("SILENT NIGHT, HOLY NIGHT", "Silent Night", 6, seed=1)
    P.verify_cryptogram(cg)
    for word in ("SILENT", "NIGHT", "HOLY"):
        assert sum(ch in cg.hints for ch in word) <= len(word) // 2


def test_patterns_have_one_answer():
    assert P.fitting_answers([2, 3, 5, 8, 13]) == {21}
    assert P.fitting_answers([1, 2, 4, 8, 16]) == {32}
    for p in P.make_patterns(2, 8, seed=5):
        P.verify_pattern(p)


def test_scramble_rejects_words_with_other_anagrams():
    d = {"TINSEL", "LISTEN", "SILENT", "HOLLY"}
    assert not P.scramble_ok("TINSEL", d)
    assert P.scramble_ok("HOLLY", d)
