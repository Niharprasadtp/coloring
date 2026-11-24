"""Device presets, chrome layout rules, buyer guide and the Etsy download set."""

import zipfile

import pymupdf
import pytest

from eink_planner import DEVICES, Options, Planner, build
from eink_planner.cli import ETSY_MAX_BYTES, ETSY_MAX_FILES, etsy_package
from eink_planner.devices import ORIENTATIONS
from eink_planner.pages.guide import build_start_here
from verify_and_preview import audit

ALL = [(d, o) for d in DEVICES for o in ORIENTATIONS]


@pytest.mark.parametrize("dev,orient", ALL, ids=[f"{d}-{o}" for d, o in ALL])
def test_chrome_layout_rules(dev, orient):
    """Every tab is full size, inside the page, clear of the content and of each
    other, and (on reMarkable) below the toolbar button corner."""
    for hand in ("right", "left"):
        p = Planner(Options(DEVICES[dev], orient, handedness=hand))
        m, c = p.m, p.content
        rects = [t.rect for t in p.chrome.tabs]
        for r in rects:
            assert r.w >= m.tap_min - 0.01 and r.h >= m.tap_min - 0.01
            assert r.x >= m.edge - 0.01 and r.right <= m.W - m.edge + 0.01
            assert r.y >= m.edge - 0.01 and r.top <= m.H - m.edge + 0.01
            assert r.overlap_area(c) == 0
        for i, a in enumerate(rects):
            assert all(a.overlap_area(b) == 0 for b in rects[i + 1:])
        rail = [t.rect for t in p.chrome.tabs if t.kind == "month"]
        assert max(r.top for r in rail) <= m.H - m.edge - m.toolbar_corner + 0.01
        assert len(rail) == 13


def test_toolbar_corner_only_on_remarkable():
    for d in DEVICES.values():
        assert (d.toolbar_corner_mm > 0) == (d.family == "remarkable")


def test_tall_narrow_screens_keep_a_single_rail_column():
    p = Planner(Options(DEVICES["remarkable_move"]))
    xs = {round(t.rect.x) for t in p.chrome.tabs if t.kind == "month"}
    assert len(xs) == 1
    assert not p.chrome.quarters_in_rail


@pytest.mark.parametrize("opts", [
    Options(DEVICES["remarkable_2"], "portrait", "sun", "left", "bw", "adhd"),
    Options(DEVICES["kindle_scribe_colorsoft"], "landscape", "mon", "right", "eink_color", "minimal"),
    Options(DEVICES["supernote_nomad"], "portrait", "mon", "right", "bw", "adhd"),
    Options(DEVICES["supernote_manta"], "landscape", "sun", "right", "bw", "minimal"),
], ids=lambda o: o.file_stem())
def test_new_devices_pass_audit(tmp_path, opts):
    info = build(opts, tmp_path / "p.pdf")
    rep = audit(info["path"])
    assert rep.ok, rep.summary()


def test_home_tells_the_two_decembers_apart(tmp_path):
    """W49-W52 exist in Dec 2026 and Dec 2027; Home must label which is which."""
    for dev in ("remarkable_pro", "remarkable_2"):
        info = build(Options(DEVICES[dev]), tmp_path / f"{dev}.pdf")
        doc = pymupdf.open(info["path"])
        toc = {t[1]: t[2] for t in doc.get_toc()}
        text = doc[toc["Home"] - 1].get_text()
        assert text.count("W49") == 2
        assert "DEC 2026" in text or text.count("'26") >= 6   # group label or per-cell tags


def test_guide_page_is_linked_from_home():
    p = Planner(Options(DEVICES["remarkable_pro"]))
    assert "guide" in p.keys


def test_repeated_content_is_shared(tmp_path):
    """Nav chrome and grids are form XObjects, keeping files small for older tablets."""
    info = build(Options(DEVICES["remarkable_pro"], daily_style="adhd"), tmp_path / "p.pdf")
    assert (tmp_path / "p.pdf").stat().st_size < 7_000_000
    assert info["links"] > 15000


@pytest.mark.parametrize("dev", ["remarkable_pro", "kindle_scribe", "supernote_nomad"])
def test_start_here(tmp_path, dev):
    d = DEVICES[dev]
    path = build_start_here(Options(d), tmp_path / "s.pdf")
    doc = pymupdf.open(path)
    assert doc.page_count == 1
    text = doc[0].get_text()
    assert d.label in text
    assert ("Color / BW" in text) == (not d.grayscale_only)
    assert {"remarkable": "custom template", "kindle": "sendtokindle",
            "supernote": "Document folder"}[d.family] in text


def test_etsy_package_fits_etsy_limits(tmp_path):
    assert etsy_package(Options(DEVICES["supernote_nomad"]), tmp_path, None) == 0
    root = tmp_path / "Etsy_Supernote-Nomad"
    files = sorted(root.iterdir())
    assert len(files) <= ETSY_MAX_FILES
    assert all(f.stat().st_size <= ETSY_MAX_BYTES for f in files)
    zips = [f for f in files if f.suffix == ".zip"]
    assert len(zips) == 4
    for z in zips:
        assert len(zipfile.ZipFile(z).namelist()) == 4          # grayscale: 2 x 2 variants
