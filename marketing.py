"""Marketing assets for the books: Pinterest pins, Etsy shop banner, About text, German/French listing translations.

    .venv/Scripts/python marketing.py pins        # output/marketing/pinterest/*.jpg + pins.txt
    .venv/Scripts/python marketing.py banner      # output/marketing/etsy_banner_3360x840.jpg
    .venv/Scripts/python marketing.py about       # output/marketing/about_section.txt
    .venv/Scripts/python marketing.py translate   # push de/fr translations (needs German + French shop languages)
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_books as B
from make_listing_images import cover_crop, font

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "marketing"
SHOP = "SpellbindinTreasures"
PLUM, CORAL, CREAM, INK = (75, 46, 90), (226, 82, 58), (253, 246, 236), (43, 43, 43)
ACCENT = {"christmas": (150, 32, 44), "wild": (40, 92, 62), "cozy": (156, 70, 42), "rose": (150, 70, 104),
          "teal": (22, 98, 110), "sunset": (96, 52, 124)}
BOARDS = {"christmas": "Christmas Paint by Number", "wild": "Animal Paint by Number", "cozy": "Cozy Paint by Number",
          "rose": "Cottagecore Coloring Pages", "teal": "Landscape Paint by Number", "sunset": "Travel Paint by Number"}


def collection(key):
    p = B.PRODUCTS[key]
    return p, B.BookCollection(B.ordered_dirs(p), B.OUT / key / "_meta")


def uploaded():
    return json.loads((B.OUT / "uploaded.json").read_text())


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    return Image.fromarray(((np.array(top) * (1 - t) + np.array(bottom) * t) * np.ones((h, w, 3))).astype(np.uint8))


def shadow_paste(canvas, img, xy, r=22, border=12):
    framed = Image.new("RGB", (img.width + 2 * border, img.height + 2 * border), "white")
    framed.paste(img, (border, border))
    mask = Image.new("L", framed.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, framed.width - 1, framed.height - 1], r, fill=255)
    sh = Image.new("RGBA", (framed.width + 80, framed.height + 80), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 90), (40, 52), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(sh, (xy[0] - 40, xy[1] - 40), sh)
    canvas.paste(framed, xy, mask)


def centered(d, text, y, f, fill, w):
    d.text(((w - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


# ---------- C) Pinterest ----------

def pins(keys=None):
    import make_cover as MC
    dest = OUT / "pinterest"
    dest.mkdir(parents=True, exist_ok=True)
    ids = uploaded()
    lines = []
    for key in keys or list(B.PRODUCTS):
        p, col = collection(key)
        theme = B.COVER_THEME.get(key, "cozy")
        acc = ACCENT[theme]
        ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
        hero = ranked[int(len(ranked) * 0.7)]
        W, H = 1000, 1500

        # pin 1: hero split (numbered -> painted) with headline
        img = gradient(W, H, (253, 244, 236), (240, 222, 210))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 250], fill=acc)
        centered(d, p["name"], 30, font("georgiab", 68 if len(p["name"]) < 20 else 54), (255, 255, 255), W)
        centered(d, "PAINT BY NUMBER", 140, font("segoeuib", 76), (255, 236, 200), W)
        split = MC.straight_split(col, hero, 760, 960)
        shadow_paste(img, split, (108, 300))
        d = ImageDraw.Draw(img)
        d.ellipse([20, 1140, 300, 1420], fill=CORAL)
        centered_x = 160
        f_big = font("impact", 120)
        n = str(col.count)
        d.text((centered_x - d.textlength(n, font=f_big) / 2, 1175), n, font=f_big, fill="white")
        d.text((centered_x - d.textlength("PAGES", font=font("segoeuib", 40)) / 2, 1320), "PAGES",
               font=font("segoeuib", 40), fill="white")
        for i, (t, f_, c) in enumerate([("Procreate iPad + Printable", font("segoeuib", 46), PLUM),
                                         ("Easy to challenging", font("segoeui", 42), INK),
                                         ("Instant download on Etsy", font("segoeui", 42), INK)]):
            d.text((340, 1300 + i * 62), t, font=f_, fill=c)
        a = dest / f"{key}_1.jpg"
        img.save(a, quality=88)

        # pin 2: grid of pages
        img = gradient(W, H, (253, 246, 236), (236, 226, 214))
        d = ImageDraw.Draw(img)
        centered(d, f"{col.count} pages to paint", 40, font("georgiab", 70), acc, W)
        centered(d, p["name"], 135, font("segoeuib", 50), PLUM, W)
        picks = [ranked[round(k * (len(ranked) - 1) / 8)] for k in range(9)]
        tw, th, gap = 280, 373, 20
        x0 = (W - 3 * tw - 2 * gap) // 2
        for i, nn in enumerate(picks):
            r_, c_ = divmod(i, 3)
            shadow_paste(img, cover_crop(col.art(nn), tw - 16, th - 16), (x0 + c_ * (tw + gap), 215 + r_ * (th + gap)),
                         r=14, border=8)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([60, 1410, W - 60, 1482], 36, fill=acc)
        centered(d, "Procreate + Printable  •  Instant download", 1420, font("segoeuib", 40), (255, 255, 255), W)
        b = dest / f"{key}_2.jpg"
        img.save(b, quality=88)

        url = f"https://www.etsy.com/listing/{ids[key]}" if key in ids else "(listing not uploaded)"
        desc = (f"{p['blurb']} {col.count} paint by number pages for adults: print at home or paint on your iPad "
                f"in Procreate. Every page has its own numbered color palette, from easy to challenging. "
                f"Instant download.")
        for img_path, title in ((a, f"{p['name']} Paint by Number for Adults | Procreate + Printable"),
                                (b, f"{col.count} {p['name']} Paint by Number Pages | Cozy Coloring for Adults")):
            lines += [f"IMAGE:  {img_path.name}", f"BOARD:  {BOARDS[theme]}", f"TITLE:  {title}",
                      f"LINK:   {url}", f"DESCRIPTION:\n{desc}", "-" * 70]
        print(f"pins {key}", flush=True)
    (dest / "pins.txt").write_text("\n".join(lines), encoding="utf-8")


# ---------- D) banner + about ----------

def banner(_=None):
    OUT.mkdir(parents=True, exist_ok=True)
    W, H = 3360, 840
    img = gradient(W, H, (253, 244, 236), (242, 220, 206))
    picks = []
    for key in ("hygge_christmas_winter", "woodland_furry_friends", "soft_cottagecore_dreams", "around_the_world_30"):
        p, col = collection(key)
        ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
        picks += [col.art(ranked[int(len(ranked) * 0.75)]), col.art(ranked[int(len(ranked) * 0.45)])]
    tw, th, gap = 330, 440, 34
    x = W - 110 - (4 * (tw + 24) + 3 * gap)
    for i, art in enumerate([picks[0], picks[2], picks[4], picks[6]]):
        shadow_paste(img, cover_crop(art, tw, th), (x + i * (tw + 24 + gap), (H - th) // 2 - 12), r=20, border=12)
    d = ImageDraw.Draw(img)
    d.text((140, 170), SHOP, font=font("georgiab", 104), fill=PLUM)
    d.text((140, 330), "Cozy paint by number for adults", font=font("segoeuib", 76), fill=CORAL)
    d.text((140, 450), "Procreate iPad  +  printable  •  easy to challenging", font=font("segoeui", 56), fill=INK)
    d.text((140, 560), "Christmas  •  Animals  •  Cottagecore  •  Travel", font=font("segoeui", 56), fill=INK)
    out = OUT / "etsy_banner_3360x840.jpg"
    img.save(out, quality=90)
    print(out)


ABOUT = f"""ETSY ABOUT SECTION  (Shop Manager > Settings > Info & Appearance > About)

STORY HEADLINE:
Cozy paint by number pages to paint on your iPad or on paper

STORY:
Welcome to {SHOP}! This shop is all about slow, cozy evenings with a paint by number page.

Every design here starts as an original illustration and is turned into a paint by number page by hand-tuned software: the colors are grouped into a numbered palette made just for that page, the numbers are placed so they stay readable, and tiny details like eyes and ornaments come pre-colored so you only paint the parts that are fun to paint.

You can print the pages at home on A4 or US Letter paper, or paint them digitally in Procreate with the matching .swatches palette. The books go from easy to challenging, so they suit beginners and experienced painters alike.

Themes include cozy Christmas and winter scenes, woodland animals, cats and dogs, soft cottagecore gardens, and beautiful places from around the world. New books are added regularly.

If anything isn't right with a download, send me a message and I'll fix it quickly. Happy painting!
"""


def about(_=None):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "about_section.txt").write_text(ABOUT, encoding="utf-8")
    print(OUT / "about_section.txt")


# ---------- E) translations ----------

CAT = {"christmas_magic": "xmas", "winter_wonderland": "xmas", "hygge_christmas_winter": "xmas",
       "woodland_wildlife": "animals", "cats_and_dogs": "animals", "woodland_furry_friends": "animals",
       "cottage_garden": "cottage", "cozy_hideaways": "cottage", "soft_cottagecore_dreams": "cottage",
       "cozy_collection_60": "mixed", "mountains_nature": "travel", "seas_shores": "travel",
       "villages_cities": "travel", "around_the_world_30": "travel"}

NAMES = {  # key: (German theme, French theme)
    "christmas_magic": ("Weihnachten", "Noël"),
    "winter_wonderland": ("Winter", "Hiver"),
    "hygge_christmas_winter": ("Hygge Weihnachten und Winter", "Noël et Hiver Hygge"),
    "woodland_wildlife": ("Waldtiere", "Animaux de la Forêt"),
    "cats_and_dogs": ("Katzen und Hunde", "Chats et Chiens"),
    "woodland_furry_friends": ("Waldtiere, Katzen und Hunde", "Animaux de la Forêt, Chats et Chiens"),
    "cottage_garden": ("Cottagecore Garten", "Jardin Cottagecore"),
    "cozy_hideaways": ("Gemütliche Rückzugsorte", "Refuges Cosy"),
    "soft_cottagecore_dreams": ("Cottagecore Träume", "Rêves Cottagecore"),
    "cozy_collection_60": ("Weihnachten, Tiere und Cottagecore", "Noël, Animaux et Cottagecore"),
    "mountains_nature": ("Berge und Natur", "Montagnes et Nature"),
    "seas_shores": ("Strand und Meer", "Plage et Mer"),
    "villages_cities": ("Dörfer und Städte", "Villages et Villes"),
    "around_the_world_30": ("Reise um die Welt", "Tour du Monde"),
}

TAGS = {
    "de": dict(core=["malen nach zahlen", "malbuch erwachsene", "procreate malen", "ausmalbilder pdf",
                     "ipad malvorlagen", "digitales malbuch", "druckbare vorlagen"],
               xmas=["weihnachten malen", "weihnachtsgeschenk", "winter ausmalbilder", "weihnachtsmalbuch",
                     "gemütlich malen", "geschenk für sie"],
               animals=["tiere ausmalen", "waldtiere", "hund ausmalbild", "katze ausmalbild", "tierliebhaber",
                        "geschenk für sie"],
               cottage=["cottagecore", "blumen ausmalen", "garten malbuch", "gemütlich malen", "frühling malen",
                        "geschenk für sie"],
               travel=["landschaft malen", "reise malbuch", "berge ausmalen", "meer ausmalbilder", "städte ausmalen",
                       "reisegeschenk"],
               mixed=["weihnachten malen", "tiere ausmalen", "cottagecore", "gemütlich malen", "malbuch bundle",
                      "geschenk für sie"]),
    "fr": dict(core=["peinture par numéro", "coloriage adulte", "procreate coloriage", "coloriage pdf",
                     "coloriage ipad", "coloriage numéroté", "art thérapie"],
               xmas=["coloriage noël", "cadeau noël", "coloriage hiver", "noël cosy", "petit cadeau noël",
                     "cadeau pour elle"],
               animals=["coloriage animaux", "animaux forêt", "coloriage chien", "coloriage chat", "amoureux animaux",
                        "cadeau pour elle"],
               cottage=["cottagecore", "coloriage fleurs", "coloriage jardin", "ambiance cosy", "coloriage printemps",
                        "cadeau pour elle"],
               travel=["coloriage paysage", "coloriage voyage", "coloriage montagne", "coloriage mer", "coloriage ville",
                       "cadeau voyageur"],
               mixed=["coloriage noël", "coloriage animaux", "cottagecore", "ambiance cosy", "lot coloriages",
                      "cadeau pour elle"]),
}

DESC = {
    "de": """{n} Malen-nach-Zahlen-Seiten zum Thema {theme}: zum Ausdrucken oder zum Malen auf dem iPad in Procreate. Die Seiten gehen von leicht bis anspruchsvoll, und jede Seite hat ihre eigene nummerierte Farbpalette. Kleine Details wie Augen und Verzierungen sind schon farbig gedruckt, du malst nur die nummerierten Flächen.

DAS BEKOMMST DU (SOFORTIGER DOWNLOAD)
- Druckbares Buch: A4-Seiten mit 300 DPI, jede mit eigener Farbpalette, die leichtesten zuerst
- Farbübersicht: jede Seite fertig ausgemalt, zum Nachschauen
- Komplettpaket (Link im PDF): für jedes Motiv ein A4-PDF, 6 PNG-Stile mit 600 DPI, SVG-Dateien, Procreate-.swatches-Paletten, Palettenblätter und Hex-Codes

SO MALST DU IN PROCREATE
- Nummeriertes PNG importieren
- Die .swatches-Datei antippen, um die Farben zu laden
- Die Linienebene auf "Multiplizieren" stellen und darunter malen

DRUCKEN
Auf A4 drucken. Für US-Letter-Papier "An Seite anpassen" wählen.

BITTE BEACHTEN
- Digitaler Download, es wird nichts verschickt.
- Farben können auf Bildschirm und Drucker leicht abweichen.
- Nur für den privaten Gebrauch. Bitte die Dateien nicht teilen oder weiterverkaufen.

Fragen? Schreib mir jederzeit eine Nachricht.""",
    "fr": """{n} pages de peinture par numéros sur le thème {theme} : à imprimer ou à peindre sur iPad dans Procreate. Les pages vont de facile à difficile, et chaque page a sa propre palette de couleurs numérotée. Les petits détails comme les yeux et les décorations sont déjà imprimés en couleur : vous ne peignez que les zones numérotées.

CE QUE VOUS RECEVEZ (TÉLÉCHARGEMENT IMMÉDIAT)
- Livre imprimable : pages A4 en 300 DPI, chacune avec sa palette, les plus faciles d'abord
- Guide des couleurs : chaque page entièrement colorée, pour vérifier un numéro
- Pack complet (lien dans le PDF) : pour chaque motif un PDF A4, 6 styles PNG en 600 DPI, fichiers SVG, palettes Procreate .swatches, fiches de palette et codes hexadécimaux

PEINDRE DANS PROCREATE
- Importez le PNG numéroté
- Touchez le fichier .swatches pour charger les couleurs
- Mettez le calque des lignes en mode "Produit" et peignez sur un calque en dessous

IMPRESSION
Imprimez sur du papier A4. Pour le format US Letter, choisissez "Ajuster à la page".

À SAVOIR
- Produit numérique, rien n'est expédié.
- Les couleurs peuvent varier légèrement selon l'écran et l'imprimante.
- Usage personnel uniquement. Merci de ne pas partager ni revendre les fichiers.

Une question ? Envoyez-moi un message à tout moment.""",
}

TITLE = {
    "de": "{theme} Malen nach Zahlen Buch, {n} Seiten für Erwachsene, Procreate iPad und Druckbare PDF Malvorlagen",
    "fr": "Peinture par Numéros {theme}, Livre de {n} Coloriages pour Adultes, Procreate iPad et PDF Imprimable",
}


def translations():
    data = {}
    for key, cat in CAT.items():
        n = len(B.PRODUCTS[key]["items"])
        for li, lang in enumerate(("de", "fr")):
            theme = NAMES[key][li]
            tags = TAGS[lang]["core"] + TAGS[lang][cat]
            title = TITLE[lang].format(theme=theme, n=n)
            assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), (lang, cat, tags)
            assert len(title) <= 140, (key, lang, len(title))
            data.setdefault(key, {})[lang] = dict(title=title, tags=tags,
                                                  description=DESC[lang].format(n=n, theme=theme))
    return data


def translate(keys=None):
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    ids = uploaded()
    data = translations()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "translations.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    for key in keys or list(data):
        if key not in ids:
            continue
        for lang, t in data[key].items():
            form = {"title": t["title"], "description": t["description"], "tags": ",".join(t["tags"])}
            path = f"/shops/{sid}/listings/{ids[key]}/translations/{lang}"
            try:
                e.request("PUT", path, form=form)
            except RuntimeError as ex:
                if "404" in str(ex) or "not found" in str(ex).lower():
                    e.request("POST", path, form=form)
                else:
                    raise
            print(f"translated {key} -> {lang}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pins"
    args = sys.argv[2:] or None
    {"pins": pins, "banner": banner, "about": about, "translate": translate}[cmd](args)
