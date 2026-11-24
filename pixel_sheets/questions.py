"""Math question generators (grades 2-4). Every answer is re-computed from the text in verify()."""
import random


def _pick(pool, n, seed, fmt):
    rng = random.Random(seed)
    pool = list(dict.fromkeys(pool))            # unique, stable order
    rng.shuffle(pool)
    if len(pool) < n:
        raise ValueError("not enough unique questions")
    return [fmt(*t) for t in pool[:n]]


def multiplication(n, seed=0):
    pool = [(min(a, b), max(a, b)) for a in range(2, 13) for b in range(2, 13)]
    rng = random.Random(seed + 99)
    return _pick(pool, n, seed, lambda a, b: ((f"{a} × {b} =", str(a * b)) if rng.random() < .5
                                              else (f"{b} × {a} =", str(a * b))))


def division(n, seed=0):
    pool = [(a, b) for a in range(2, 13) for b in range(2, 13)]
    return _pick(pool, n, seed, lambda a, b: (f"{a * b} ÷ {a} =", str(b)))


def addition(n, seed=0):
    pool = [(a, b) for a in range(11, 80) for b in range(11, 100 - a)]
    return _pick(pool, n, seed, lambda a, b: (f"{a} + {b} =", str(a + b)))


def subtraction(n, seed=0):
    pool = [(a, b) for a in range(25, 100) for b in range(11, a - 4)]
    return _pick(pool, n, seed, lambda a, b: (f"{a} − {b} =", str(a - b)))


GENERATORS = {"Multiplication": multiplication, "Division": division,
              "Addition": addition, "Subtraction": subtraction}


def verify(qs):
    """Independently recompute every answer from the question text."""
    for q, a in qs:
        expr = q.rstrip("= ").replace("×", "*").replace("÷", "/").replace("−", "-")
        val = eval(expr, {"__builtins__": {}})          # text we generated ourselves
        if isinstance(val, float):
            assert val.is_integer(), f"not a whole number: {q}"
            val = int(val)
        assert val >= 0, f"negative answer: {q}"
        assert str(val) == a, f"wrong answer: {q} {a} (should be {val})"
    assert len({q for q, _ in qs}) == len(qs), "duplicate question"
