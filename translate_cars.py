"""Upload manual translations (title, description, tags) for the car listings.

    python translate_cars.py check            # build every translation and validate it, no upload
    python translate_cars.py upload [lang..]  # create/update the translations on Etsy

Texts live in car_i18n/<lang>.py. The numbers (level, zones, colors) and the page list are read from the
English listing.json files, so translations always match the English listing.
"""
import importlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SINGLES = HERE / "output" / "car_singles"
BOOK_KEY, BOOK_DIR = "book", HERE / "output" / "books" / "car_classics_22"
BOOK_ID = 4621027114
BOOK_URL = f"https://www.etsy.com/listing/{BOOK_ID}"
LANGS = ["fr", "de", "es", "it", "nl", "pt", "pl", "ru", "sv", "ja"]
TAG_OK = re.compile(r"^[\w \-'™©®]+$")


def listings():
    """[(key, listing_id, english listing dict)] for the 10 singles and the book."""
    ids = json.loads((SINGLES / "uploaded.json").read_text())
    out = [(stem, lid, json.loads((SINGLES / stem / "listing.json").read_text(encoding="utf-8")))
           for stem, lid in ids.items()]
    out.append((BOOK_KEY, BOOK_ID, json.loads((BOOK_DIR / "listing.json").read_text(encoding="utf-8"))))
    return out


def tags_for(L, english_tags):
    tags = []
    for t in english_tags:
        local = L.TAGS[t].strip()
        if local not in tags:
            tags.append(local)
    return tags[:13]


def translate(lang, key, en):
    L = importlib.import_module(f"car_i18n.{lang}")
    d = en["description"]
    if key == BOOK_KEY:
        pages = re.findall(r"^(\d+)\. (.+) \((\w+)\)$", d, re.M)
        lines = "\n".join(f"{i}. {L.NAMES[name]} ({L.LEVELS[lv]})" for i, name, lv in pages)
        lo, hi = re.search(r"about (\d+) to (\d+) numbered zones", d).groups()
        desc = L.BOOK.format(blurb=L.BLURBS[key], pages=lines, lo=lo, hi=hi).strip()
    else:
        name = re.search(r"Paint this (.+?) design", d).group(1)
        lv, zones, colors = re.search(r"Level: (\w+), with about ([\d,]+) numbered zones and (\d+) colors", d).groups()
        desc = L.SINGLE.format(blurb=L.BLURBS[key], name=L.NAMES[name], level=L.LEVELS[lv], zones=zones,
                               colors=colors, url=BOOK_URL).strip()
    return dict(title=L.TITLES[key], description=desc, tags=tags_for(L, en["tags"]))


def validate(lang, key, t):
    errs = []
    if not 0 < len(t["title"]) <= 140:
        errs.append(f"title length {len(t['title'])}")
    for tag in t["tags"]:
        if len(tag) > 20 or not TAG_OK.match(tag):
            errs.append(f"bad tag {tag!r} ({len(tag)})")
    if len(t["tags"]) < 10:
        errs.append(f"only {len(t['tags'])} tags")
    if "{" in t["description"] or "}" in t["description"]:
        errs.append("unfilled placeholder")
    return [f"{lang}/{key}: {e}" for e in errs]


def check(langs):
    errs = []
    for lang in langs:
        for key, _, en in listings():
            errs += validate(lang, key, translate(lang, key, en))
    print("\n".join(errs) or f"all translations valid ({', '.join(langs)})")
    return not errs


def upload(langs):
    import etsy_api as e
    if not check(langs):
        sys.exit("fix the errors above first")
    sid = e.get_token()["shop_id"]
    for lang in langs:
        for key, lid, en in listings():
            t = translate(lang, key, en)
            path = f"/shops/{sid}/listings/{lid}/translations/{lang}"
            form = dict(title=t["title"], description=t["description"], tags=",".join(t["tags"]))
            have = e.request("GET", path)
            e.request("PUT" if have.get("title") else "POST", path, form=form)
        print(f"{lang}: {len(listings())} listings translated", flush=True)


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["check"]
    langs = rest or [l for l in LANGS if (HERE / "car_i18n" / f"{l}.py").exists()]
    {"check": check, "upload": upload}[cmd](langs)
