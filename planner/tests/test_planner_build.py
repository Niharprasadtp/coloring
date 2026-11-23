import pytest

from eink_planner import DEVICES, Options, Planner, build
from eink_planner.cli import batch_variants
from eink_planner.geometry import Rect
from eink_planner.ink import LayoutError
from verify_and_preview import audit, export_previews


@pytest.mark.parametrize("opts", [
    Options(DEVICES["remarkable_move"], "portrait", "mon", "right", "eink_color", "adhd"),
    Options(DEVICES["remarkable_move"], "landscape", "sun", "left", "bw", "minimal"),
    Options(DEVICES["kindle_scribe"], "landscape", "mon", "left", "eink_color", "adhd"),
], ids=lambda o: o.file_stem())
def test_build_passes_audit(tmp_path, opts):
    info = build(opts, tmp_path / "p.pdf")
    rep = audit(info["path"])
    assert rep.ok, rep.summary()
    assert rep.links == info["links"]


def test_page_inventory():
    p = Planner(Options(DEVICES["remarkable_pro"]))
    keys = [s.key for s in p.specs]
    assert len(keys) == len(set(keys))
    assert sum(k.startswith("d-") for k in keys) == 396
    assert sum(k.startswith("w-") for k in keys) == 57
    assert sum(k.startswith("m-") and not k.endswith("-h") for k in keys) == 13
    assert sum(k.startswith("bd-") for k in keys) == 5
    assert sum(k.startswith("p") and k[1].isdigit() for k in keys) == 30
    assert sum(k.startswith("t-") for k in keys) >= 20
    assert {"cover", "home", "projects", "templates", "q1", "q4-goals"} <= set(keys)


def test_rail_follows_handedness():
    for hand, side in (("right", "left"), ("left", "right")):
        p = Planner(Options(DEVICES["remarkable_pro"], handedness=hand))
        rail = [t.rect for t in p.chrome.tabs if t.kind == "month"]
        on_left = all(r.right < p.content.x for r in rail)
        assert on_left == (side == "left")


def test_link_guard_rejects_small_or_overlapping(tmp_path):
    p = Planner(Options(DEVICES["remarkable_pro"]))
    from reportlab.pdfgen import canvas
    from eink_planner.ink import Ink
    ink = Ink(canvas.Canvas(str(tmp_path / "x.pdf")), p.m, p.t, p.keys)
    big = p.m.mm(10)
    ink.link(Rect(0, 0, big, big), "home")
    with pytest.raises(LayoutError):
        ink.link(Rect(big / 2, 0, big, big), "home")          # overlaps
    with pytest.raises(LayoutError):
        ink.link(Rect(5 * big, 0, p.m.mm(5), big), "home")    # too narrow
    with pytest.raises(LayoutError):
        ink.link(Rect(9 * big, 0, big, big), "nowhere")       # unknown page


def test_batch_variants():
    assert len(batch_variants(Options(DEVICES["remarkable_pro"]))) == 8
    # Kindle Scribe is grayscale-only, so only the B&W palette is produced.
    assert len(batch_variants(Options(DEVICES["kindle_scribe"]))) == 4


def test_previews(tmp_path):
    info = build(Options(DEVICES["remarkable_move"]), tmp_path / "p.pdf")
    files = export_previews(info["path"], tmp_path / "prev", dpi=100)
    names = {f.stem for f in files}
    assert {"01_cover", "02_home", "03_year_at_a_glance", "04_monthly", "05_weekly",
            "06_daily_minimal", "07_project_hub", "08_template_index"} == names
