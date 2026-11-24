"""Manual translations (title, description, tags) for the shop's non-car listings.

    python translate_listings.py fetch            # cache listings + write the English phrase list (i18n/en_segments.txt)
    python translate_listings.py check [lang..]   # build every translation and validate it, no upload
    python translate_listings.py upload [lang..]  # create/update the translations on Etsy

Descriptions are split into lines. Each line is either kept as is (URLs, blank), built from a pattern
(page list items, file list items, "Paint this X design" lines) or looked up as a phrase. Numbers in a
phrase become {0}, {1}... so translations can reorder them. Texts live in i18n/<lang>.py:
    SEG    {segment id: translated phrase}
    NAMES  {English design name: translated name}
    LEVELS {English level: translated level}
    TITLES {listing id: translated title}
    TAGS   {English tag: translated tag (max 20 chars)}
    FILES  {"Download Full Pack": ..., "Printable Book": ..., "Color Guide": ..., "Procreate Kit": ..., "Part": ...}
"""
import html
import importlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = HERE / "i18n"
CACHE = DIR / "listings.json"
SEGS = DIR / "en_segments.json"
LANGS = ["fr", "de", "es", "it", "nl", "pt", "pl", "ru", "sv", "ja"]
CAR_IDS = {4621027114, 4621094293, 4621106459, 4621117266, 4621118248, 4621114285, 4621120740, 4621121594,
           4621122436, 4621123006, 4621118499}
SKIP = {4593014726}                                  # inactive Halloween PLR listing
TAG_OK = re.compile(r"^[\w \-'™©®]+$")
NUM = re.compile(r"\d+(?:[.,]\d+)*")

PAGE = re.compile(r"^(\d+)\. (.+) \((Easy|Medium|Challenging|Expert|Relaxing|Beginner)\)$")
FILE = re.compile(r"^- (.+?) (Download Full Pack|Printable Book|Color Guide|Procreate Kit)(?: Part (\d+))? \((PDF|ZIP)\)$")
PAINT = re.compile(r"^Paint this (.+?) design on your iPad in Procreate, or print it at home and paint with markers, "
                   r"colored pencils or paint\. Level: (\w+), with about ([\d,]+) numbered zones and (\d+) colors\.$")


def kind(line):
    """('keep'|'page'|'file'|'paint'|'seg', match or template, numbers)"""
    if not line.strip() or re.match(r"^https?://\S+$", line.strip()):
        return "keep", line, []
    for k, rx in (("page", PAGE), ("file", FILE), ("paint", PAINT)):
        m = rx.match(line)
        if m:
            return k, m, []
    nums = NUM.findall(line)
    i = iter(range(len(nums)))
    return "seg", NUM.sub(lambda _: "{%d}" % next(i), line.replace("{", "(").replace("}", ")")), nums


def fetch():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    out = []
    for state in ("active", "draft"):
        off = 0
        while True:
            r = e.request("GET", f"/shops/{sid}/listings", params={"state": state, "limit": 100, "offset": off})
            for l in r["results"]:
                if l["listing_id"] in CAR_IDS | SKIP:
                    continue
                out.append(dict(id=l["listing_id"], state=state, title=html.unescape(l["title"]),
                                tags=[html.unescape(t) for t in l["tags"]],
                                description=html.unescape(l["description"])))
            off += 100
            if off >= r["count"]:
                break
    DIR.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    segs, names, levels, tags = {}, set(), set(), set()
    for l in out:
        tags |= set(l["tags"])
        for line in l["description"].split("\n"):
            k, m, _ = kind(line)
            if k == "seg" and m not in segs.values():
                segs[f"s{len(segs) + 1:03d}"] = m
            elif k == "page":
                names.add(m.group(2)); levels.add(m.group(3))
            elif k == "paint":
                names.add(m.group(1)); levels.add(m.group(2))
    SEGS.write_text(json.dumps(dict(seg=segs, names=sorted(names), levels=sorted(levels), tags=sorted(tags),
                                    titles={l["id"]: l["title"] for l in out}), indent=1, ensure_ascii=False),
                    encoding="utf-8")
    print(f"{len(out)} listings, {len(segs)} phrases, {len(names)} names, {len(tags)} tags -> {SEGS}")


def translate(L, listing):
    en = json.loads(SEGS.read_text(encoding="utf-8"))
    by_text = {v: k for k, v in en["seg"].items()}
    lines = []
    for line in listing["description"].split("\n"):
        k, m, nums = kind(line)
        if k == "keep":
            lines.append(line)
        elif k == "page":
            lines.append(f"{m.group(1)}. {L.NAMES[m.group(2)]} ({L.LEVELS[m.group(3)]})")
        elif k == "file":
            part = f" {L.FILES['Part']} {m.group(3)}" if m.group(3) else ""
            lines.append(f"- {m.group(1)}, {L.FILES[m.group(2)]}{part} ({m.group(4)})")
        elif k == "paint":
            lines.append(L.PAINT.format(name=L.NAMES[m.group(1)], level=L.LEVELS[m.group(2)], zones=m.group(3),
                                        colors=m.group(4)))
        else:
            lines.append(L.SEG[by_text[m]].format(*nums))
    tags = []
    for t in listing["tags"]:
        local = L.TAGS[t].strip()
        if local not in tags:
            tags.append(local)
    return dict(title=L.TITLES[listing["id"]], description="\n".join(lines).strip(), tags=tags[:13])


def check(langs):
    listings = json.loads(CACHE.read_text(encoding="utf-8"))
    errs = []
    for lang in langs:
        L = importlib.import_module(f"i18n.{lang}")
        for l in listings:
            try:
                t = translate(L, l)
            except (KeyError, IndexError) as x:
                errs.append(f"{lang}/{l['id']}: missing {x!r}")
                continue
            if not 0 < len(t["title"]) <= 140:
                errs.append(f"{lang}/{l['id']}: title length {len(t['title'])}")
            errs += [f"{lang}/{l['id']}: bad tag {g!r}" for g in t["tags"] if len(g) > 20 or not TAG_OK.match(g)]
    print("\n".join(errs) or f"all translations valid ({', '.join(langs)}; {len(listings)} listings)")
    return not errs


def upload(langs):
    import etsy_api as e
    if not check(langs):
        sys.exit("fix the errors above first")
    sid = e.get_token()["shop_id"]
    listings = json.loads(CACHE.read_text(encoding="utf-8"))
    for lang in langs:
        L = importlib.import_module(f"i18n.{lang}")
        for l in listings:
            t = translate(L, l)
            path = f"/shops/{sid}/listings/{l['id']}/translations/{lang}"
            form = dict(title=t["title"], description=t["description"], tags=",".join(t["tags"]))
            have = e.request("GET", path)
            e.request("PUT" if have.get("title") else "POST", path, form=form)
        print(f"{lang}: {len(listings)} listings translated", flush=True)


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["check"]
    langs = rest or [l for l in LANGS if (DIR / f"{l}.py").exists()]
    {"fetch": fetch, "check": check, "upload": upload}[cmd](*(() if cmd == "fetch" else (langs,)))
