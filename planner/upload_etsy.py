#!/usr/bin/env python3
"""Upload planner listings to Etsy as DRAFTS (you publish them in Shop Manager).

    ../.venv/Scripts/python.exe upload_etsy.py remarkable_pro remarkable_move ...
    ../.venv/Scripts/python.exe upload_etsy.py --price 799 kindle_scribe_colorsoft

Uses etsy/<slug>/ (listing.md + *.jpg from etsy_assets.py) and output/Etsy_<slug>/
(START-HERE.pdf + 4 ZIPs from make_planner.py --etsy). Re-running resumes: drafts
already created get any missing photos or files added instead of a new listing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import etsy_api as e  # noqa: E402

from eink_planner.devices import DEVICES  # noqa: E402

TAXONOMY = 354                 # Paper & Party Supplies > Paper > Calendars & Planners
SECTION = "Digital Planners"
STATE = HERE / "etsy" / "uploaded.json"


def parse_listing(md: str) -> dict:
    def section(name: str) -> str:
        m = re.search(rf"^## {name}[^\n]*\n(.*?)(?=^## |\Z)", md, re.S | re.M)
        return m.group(1).strip()
    return {"title": section("Title"),
            "tags": [t.strip() for t in section("Tags").split(",")],
            "description": section("Description")}


def files_for(slug: str) -> list[Path]:
    d = HERE / "output" / f"Etsy_{slug}"
    files = [d / "START-HERE.pdf"] + sorted(d.glob("*.zip"))
    assert len(files) <= 5 and all(f.stat().st_size <= 20_000_000 for f in files), files
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("devices", nargs="+", choices=sorted(DEVICES))
    ap.add_argument("--price", type=float, default=799, help="in the shop currency (INR)")
    a = ap.parse_args(argv)

    sid = e.get_token()["shop_id"]
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    sections = {s["title"]: s["shop_section_id"]
                for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    if SECTION not in sections:
        sections[SECTION] = e.request("POST", f"/shops/{sid}/sections",
                                      form={"title": SECTION})["shop_section_id"]

    for key in a.devices:
        slug = DEVICES[key].slug
        photos = sorted((HERE / "etsy" / slug).glob("*.jpg"))
        files = files_for(slug)
        text = parse_listing((HERE / "etsy" / slug / "listing.md").read_text(encoding="utf-8"))
        assert len(text["title"]) <= 140 and len(text["tags"]) <= 13, text["title"]

        lid = state.get(key)
        if lid is None:
            lid = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
                "quantity": 999, "title": text["title"], "description": text["description"],
                "price": a.price, "who_made": "i_did", "when_made": "2020_2026",
                "taxonomy_id": TAXONOMY, "type": "download", "is_supply": "false",
                "should_auto_renew": "true", "tags": ",".join(text["tags"]),
                "shop_section_id": sections[SECTION],
            })["listing_id"]
            state[key] = lid
            STATE.write_text(json.dumps(state, indent=2))
            print(f"{key}: created draft {lid}", flush=True)

        have = len(e.request("GET", f"/listings/{lid}/images")["results"])
        for rank, f in enumerate(photos, 1):
            if rank > have:
                e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank},
                          files={"image": f})
                print(f"  photo {rank}/{len(photos)}", flush=True)
        have_files = {f["filename"] for f in
                      e.request("GET", f"/shops/{sid}/listings/{lid}/files")["results"]}
        for rank, f in enumerate(files, 1):
            if f.name not in have_files:
                e.request("POST", f"/shops/{sid}/listings/{lid}/files",
                          form={"rank": rank, "name": f.name}, files={"file": f})
                print(f"  file {f.name} ({f.stat().st_size / 1e6:.1f} MB)", flush=True)
        print(f"{key}: draft {lid} ready - https://www.etsy.com/your/shops/me/listing-editor/"
              f"edit/{lid}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
