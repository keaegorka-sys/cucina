"""Поиск и загрузка фотографий блюд с Wikimedia Commons (только свободные лицензии).

Шаг 1 — найти кандидатов:   python tools/photos.py search <файл-кандидатов.json>
Шаг 2 — скачать выбранные:  python tools/photos.py download <файл-кандидатов.json> [выбор.json]
   выбор.json — {"id блюда": номер кандидата}, по умолчанию берётся первый (0).
Результат: картинки img/<id>.jpg и файл photos.js с авторами и лицензиями.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://commons.wikimedia.org/w/api.php"
UA = "CucinaRecipeApp/1.0 (personal meal-planner; github.com/keaegorka-sys/cucina)"
WIDTH = 640

QUERIES = {
 "frittata": ["frittata zucchine", "frittata"],
 "purgatorio": ["uova in purgatorio", "shakshuka"],
 "ricotta_toast": ["crostini ricotta miele", "ricotta toast"],
 "bruschetta": ["bruschetta pomodoro", "bruschetta"],
 "piadina": ["piadina romagnola", "piadina"],
 "polenta_egg": ["polenta poached egg", "polenta"],
 "crostone_caprese": ["bruschetta mozzarella tomato", "caprese toast"],
 "pomodoro": ["spaghetti al pomodoro", "spaghetti tomato sauce"],
 "aglio_olio": ["spaghetti aglio olio peperoncino", "aglio e olio"],
 "cacio_pepe": ["cacio e pepe", "tonnarelli"],
 "carbonara": ["spaghetti alla carbonara", "carbonara"],
 "amatriciana": ["bucatini amatriciana", "amatriciana"],
 "norma": ["pasta alla norma"],
 "pesto": ["trofie al pesto", "pasta pesto genovese"],
 "bolognese": ["tagliatelle al ragù", "tagliatelle bolognese"],
 "lasagne": ["lasagne alla bolognese", "lasagna"],
 "pasta_fagioli": ["pasta e fagioli"],
 "vongole": ["spaghetti alle vongole"],
 "tonno": ["pasta al tonno", "penne tuna"],
 "tagliatelle_salvia": ["tagliatelle burro salvia", "tagliatelle"],
 "gnocchi": ["gnocchi al pomodoro", "gnocchi"],
 "risotto_funghi": ["risotto ai funghi", "mushroom risotto"],
 "risotto_milanese": ["risotto alla milanese"],
 "risotto_limone": ["risotto gamberi", "shrimp risotto"],
 "arancini": ["arancini"],
 "minestrone": ["minestrone"],
 "ribollita": ["ribollita"],
 "cacciatora": ["pollo alla cacciatora", "chicken cacciatore"],
 "piccata": ["chicken piccata", "piccata"],
 "saltimbocca": ["saltimbocca alla romana", "saltimbocca"],
 "polpette": ["polpette al sugo", "meatballs tomato sauce"],
 "parmigiana": ["parmigiana di melanzane"],
 "acqua_pazza": ["acqua pazza", "pesce acqua pazza"],
 "orata_forno": ["orata al forno", "baked sea bream"],
 "pizza": ["pizza margherita"],
 "caprese": ["insalata caprese", "caprese salad"],
 "panzanella": ["panzanella"],
 "caponata": ["caponata"],
 "tiramisu": ["tiramisu"],
 "panna_cotta": ["panna cotta"],
 "focaccia": ["focaccia genovese", "focaccia rosmarino"],
 "ciambellone": ["ciambellone", "ciambella cake"],
 "cantucci": ["cantucci", "cantuccini"],
 "eggs_toast": ["fried egg on toast", "egg toast"],
 "frittata_potato": ["frittata di patate", "potato frittata"],
 "frittata_asparagus": ["frittata asparagi", "asparagus frittata"],
 "nutella_toast": ["pane e nutella", "nutella bread"],
 "panino_margherita": ["caprese sandwich", "panino mozzarella pomodoro"],
 "tuna_bean_salad": ["insalata tonno fagioli", "tuna bean salad"],
 "lemon_spaghetti": ["spaghetti al limone", "lemon pasta"],
 "orecchiette_crumbs": ["orecchiette pangrattato", "orecchiette"],
 "tortellini_brodo": ["tortellini in brodo"],
 "penne_vodka": ["penne alla vodka"],
 "alfredo": ["fettuccine alfredo"],
 "primavera": ["pasta primavera"],
 "farfalle_sausage": ["farfalle salsiccia funghi", "farfalle sausage"],
 "turkey_meatballs": ["turkey meatballs", "meatballs in tomato sauce"],
 "chicken_parm": ["chicken parmigiana", "chicken parmesan"],
 "marsala": ["chicken marsala", "veal marsala"],
 "milanese": ["cotoletta alla milanese"],
 "salmon_foil": ["salmon en papillote", "salmone al cartoccio"],
 "fra_diavolo": ["shrimp fra diavolo", "gamberi pomodoro piccante"],
 "spezzatino": ["spezzatino", "chicken stew"],
 "osso_buco": ["ossobuco"],
 "tuna_steak": ["seared tuna steak", "tuna steak"],
 "steak_salad": ["tagliata rucola", "steak salad"],
 "scampi_couscous": ["shrimp couscous", "couscous prawns"],
 "calamari": ["calamari fritti", "fried calamari"],
 "pepper_salad": ["peperoni arrostiti", "roasted peppers salad"],
 "stuffed_tomatoes": ["pomodori ripieni", "stuffed tomatoes"],
 "farro_salad": ["insalata di farro", "farro salad"],
 "marinara": ["marinara sauce", "tomato sauce pot"],
 "affogato": ["affogato"],
 "grilled_peaches": ["grilled peaches", "pesche grigliate"],
 "cannoli_fruit": ["macedonia di frutta", "fruit salad"],
 "kd_ricotta": ["ricotta cheese", "ricotta"],
 "kd_focaccia24": ["focaccia bread", "focaccia"],
 "kd_pesto_roasted": ["linguine al pesto", "pesto pasta"],
 "kd_gnocchi_yolk": ["gnocchi burro salvia", "pan fried gnocchi"],
 "kd_ravioli": ["ravioli burro e salvia", "ricotta ravioli"],
 "kd_scampi": ["shrimp scampi", "linguine shrimp"],
 "kd_sungold": ["spaghetti cherry tomatoes", "spaghetti pomodorini"],
 "kd_caciofredo": ["fettuccine parmigiano", "fettuccine"],
 "kd_pizza_pan": ["pan pizza", "cast iron pizza"],
 "kd_peaches_burrata": ["burrata peaches", "burrata"],
 "kd_broccoli": ["roasted broccoli parmesan", "roasted broccoli"],
 "kd_risotto_asparagus": ["risotto agli asparagi", "asparagus risotto"],
 "kd_sausage_patties": ["sausage patties eggs", "breakfast sausage"],
 "kd_jammy_toast": ["soft boiled egg toast", "jammy egg"],
}

QUERIES.update({
 "kd_artichokes": ["fried artichokes", "artichoke hearts fried"], "kd_dates": ["bacon wrapped dates", "devils on horseback"],
 "kd_chickpeas": ["roasted chickpeas", "crispy chickpeas"], "kd_crab_dip": ["crab dip", "artichoke dip"],
 "kd_watermelon": ["watermelon halloumi", "halloumi skewers"], "kd_onion_dip": ["french onion dip", "onion dip"],
 "kd_hummus": ["hummus", "hummus pine nuts"], "kd_pasta_chips": ["pasta chips", "fried pasta snack"],
 "kd_pancakes": ["pancakes chocolate", "pancakes stack"], "kd_chicken_eggs": ["scrambled eggs", "scrambled eggs plate"],
 "kd_bagels": ["everything bagel", "bagels"], "kd_bacon": ["candied bacon", "bacon strips"],
 "kd_benedict": ["eggs benedict", "eggs benedict smoked salmon"], "kd_hashbrowns": ["hash browns waffle", "hash browns"],
 "kd_burrito": ["breakfast burrito", "burrito"], "kd_pattymelt": ["patty melt", "patty melt sandwich"],
 "kd_grilled_cheese_blueberry": ["grilled cheese sandwich", "brie sandwich"], "kd_blt": ["BLT sandwich", "bacon lettuce tomato sandwich"],
 "kd_chicken_sandwich": ["fried chicken sandwich", "chicken sandwich"], "kd_tuna_melt": ["tuna melt", "tuna melt sandwich"],
 "kd_gc_tomato_soup": ["grilled cheese tomato soup", "tomato soup"], "kd_quesadilla": ["chicken quesadilla", "quesadilla"],
 "kd_smash_burger": ["smash burger", "cheeseburger"], "kd_confit": ["chicken confit", "confit chicken leg"],
 "kd_fried_chicken": ["fried chicken", "buttermilk fried chicken"], "kd_chicken_skins": ["chicken skin crispy", "fried chicken skin"],
 "kd_butter_chicken": ["butter chicken", "butter chicken rice"], "kd_dino_nuggets": ["chicken nuggets", "dinosaur chicken nuggets"],
 "kd_chicken_salad": ["chicken salad", "chicken salad sandwich"], "kd_buffalo_rolls": ["egg rolls", "buffalo chicken egg rolls"],
 "kd_thai_soup": ["thai chicken soup", "tom kha gai"], "kd_ribeye": ["ribeye steak", "cast iron steak"],
 "kd_ribs": ["pork ribs oven", "baby back ribs"], "kd_lamb": ["lamb chops", "lamb lollipops"],
 "kd_chili": ["beef chili", "chili con carne"], "kd_steak_tips": ["steak tips", "garlic butter steak bites"],
 "kd_shepherd": ["shepherd's pie", "cottage pie"], "kd_swedish_meatballs": ["swedish meatballs", "köttbullar"],
 "kd_khao_soi": ["khao soi", "khao soi pork"], "kd_lobster_roll": ["lobster roll", "lobster roll sandwich"],
 "kd_scallops": ["baked scallops", "scallops gratin"], "kd_fish_chips": ["fish and chips", "fish and chips plate"],
 "kd_calamari2": ["fried calamari", "calamari fritti"], "kd_salmon_air": ["baked salmon fillet", "salmon fillet"],
 "kd_tuna_rice": ["crispy rice tuna", "spicy tuna crispy rice"], "kd_ceviche": ["shrimp ceviche", "ceviche"],
 "kd_fish_curry": ["thai fish curry", "fish curry coconut"], "kd_mezcal": ["rigatoni vodka sauce", "rigatoni pasta"],
 "kd_lasagna": ["lasagne bechamel", "lasagna slice"], "kd_ramen_carbonara": ["ramen carbonara", "carbonara noodles"],
 "kd_pizza_grill": ["grilled pizza", "pizza on grill"], "kd_roast_potatoes": ["roasted potatoes crispy", "roast potatoes"],
 "kd_crispy_rice": ["tahdig", "persian crispy rice"], "kd_naan": ["naan bread", "naan"],
 "kd_mash": ["mashed potatoes", "mashed potatoes plate"], "kd_cheese_balls": ["pão de queijo", "brazilian cheese bread"],
 "kd_tortillas": ["flour tortillas", "tortillas"], "kd_wedge": ["wedge salad", "iceberg wedge salad"],
 "kd_miso_eggplant": ["miso eggplant", "nasu dengaku"], "kd_brussels": ["roasted brussels sprouts", "brussels sprouts"],
 "kd_corn": ["grilled corn on the cob", "elote"], "kd_cucumbers": ["cucumber salad", "cucumber dill salad"],
 "kd_caesar": ["caesar salad", "caesar salad croutons"], "kd_cupcakes": ["chocolate cupcakes", "devils food cupcake"],
 "kd_toffee_bars": ["toffee bars", "blondie bars"], "kd_cookies": ["chocolate chip cookies", "chocolate chip cookie"],
 "kd_fruit_leather": ["fruit leather", "fruit roll"], "kd_horchata": ["horchata", "horchata glass"],
 "kd_tanghulu": ["tanghulu", "candied strawberries"], "kd_ice_cream": ["chocolate hazelnut ice cream", "ice cream scoop"],
 "kd_frosting": ["buttercream frosting", "frosted cupcake"], "kd_wings": ["chicken wings lemon pepper", "chicken wings"],
 "kd_compost_cookies": ["cookies with potato chips", "big cookies"], "kd_pretzels": ["soft pretzel", "soft pretzels"],
 "kd_borscht": ["borscht", "borscht beef"], "kd_salt": ["flaky salt", "sea salt flakes"],
 "kd_brown_sugar": ["brown sugar", "brown sugar bowl"], "kd_pickling": ["quick pickled vegetables", "pickled cucumbers jar"],
 "kd_butter": ["homemade butter", "butter block"], "kd_stock": ["chicken stock", "chicken broth pot"],
 "kd_onions": ["caramelized onions", "caramelised onions pan"], "kd_browned_butter": ["brown butter", "browned butter"],
 "kd_pasta_dough": ["fresh pasta dough", "homemade pasta"], "kd_croutons": ["croutons", "garlic croutons"],
 "kd_ranch": ["ranch dressing", "ranch dressing bowl"], "kd_honey_bbq": ["honey mustard sauce", "dipping sauce"],
 "kd_special_sauce": ["burger sauce", "special sauce burger"], "kd_buffalo": ["buffalo sauce", "buffalo wings sauce"],
 "kd_bbq": ["barbecue sauce", "bbq sauce"],
 "straccetti": ["straccetti di manzo", "beef strips arugula"], "pollo_limone": ["roast chicken lemon rosemary", "chicken thighs potatoes"],
 "salsicce_fagioli": ["sausages and beans", "salsiccia e fagioli"], "tagliata": ["tagliata di manzo", "sliced steak arugula"],
 "agnello": ["lamb ribs", "lamb chops rosemary"], "arista": ["arista di maiale", "roast pork loin"],
 "spiedini_pollo": ["chicken skewers", "spiedini"], "uova_pancetta": ["scrambled eggs bacon", "eggs and pancetta"],
})

OK_LICENSE = re.compile(r"^(CC0|CC BY(-SA)? \d|Public domain|PD)", re.I)


def fetch(url, binary=False):
    """GET с паузой и повторами при 429/5xx — Wikimedia просит не спешить."""
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read() if binary else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1)
            print("  жду", wait, "с", file=sys.stderr)
            time.sleep(wait)


def api(params):
    return fetch(API + "?" + urllib.parse.urlencode(params))


def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()


def search(q):
    data = api({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                "gsrsearch": "filetype:bitmap " + q, "gsrlimit": 8, "prop": "imageinfo",
                "iiprop": "url|extmetadata|size", "iiurlwidth": WIDTH})
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata") or {}
        lic = clean((md.get("LicenseShortName") or {}).get("value"))
        if not OK_LICENSE.match(lic) or ii.get("width", 0) < 400:
            continue
        if not re.search(r"\.(jpe?g|png|webp)$", p["title"], re.I):
            continue
        out.append({"title": p["title"], "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
                    "author": clean((md.get("Artist") or {}).get("value")) or "неизвестен",
                    "license": lic, "licenseUrl": clean((md.get("LicenseUrl") or {}).get("value"))})
    return out


def cmd_search(path):
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for rid, qs in QUERIES.items():
        if res.get(rid):
            continue                                   # уже найдено в прошлый запуск
        cands, seen = [], set()
        for q in qs:
            for c in search(q):
                if c["title"] not in seen:
                    seen.add(c["title"]); cands.append(c)
            time.sleep(1.5)
            if len(cands) >= 6:
                break
        res[rid] = cands[:6]
        print(rid, len(res[rid]))
        json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def cmd_download(path, choice_path=None):
    cands = json.load(open(path, encoding="utf-8"))
    choice = json.load(open(choice_path, encoding="utf-8")) if choice_path else {}
    os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
    meta = {}
    for rid, lst in cands.items():
        k = choice.get(rid, 0)
        if k is None or k < 0 or not lst or k >= len(lst):
            continue
        c = lst[k]
        dest = os.path.join(ROOT, "img", rid + ".jpg")
        if not os.path.exists(dest) or choice_path:
            with open(dest, "wb") as f:
                f.write(fetch(c["thumb"], binary=True))
            time.sleep(1.0)
        meta[rid] = {"f": "img/" + rid + ".jpg", "a": c["author"], "l": c["license"], "u": c["page"]}
    with open(os.path.join(ROOT, "photos.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* Фотографии блюд с Wikimedia Commons (свободные лицензии). Собрано tools/photos.py.\n"
                "   f — файл, a — автор, l — лицензия, u — страница фото. */\n")
        f.write("window.PHOTOS = " + json.dumps(meta, ensure_ascii=False, indent=0) + ";\n")
    print("downloaded", len(meta))


def short_author(a):
    """Короткая подпись автора: без текста лицензии, почты и пояснений Commons."""
    a = re.sub(r"^No machine-readable author provided\.\s*", "", a or "")
    a = re.sub(r"\s+assumed \(based on copyright claims\)\.?$", "", a)
    a = re.sub(r"\S+@\S+", "", a)
    a = re.split(r"\s+(?:I'd|This file|Own work|©|Photo by|Photograph)|\.\s|\n", a)[0]
    a = re.sub(r"(\S+) \(\1\)", r"\1", a).strip(" ,;-")
    if len(a) > 60:
        a = a[:57].rsplit(" ", 1)[0] + "…"
    return a or "автор указан на странице файла"


def cmd_build(path, choice_path, cache_dir):
    """Собирает img/ и photos.js из уже скачанных кандидатов (cache_dir/<id>__<n>.jpg):
    сжимает до 600 px по ширине, JPEG качество 80 — чтобы репозиторий и сайт оставались лёгкими."""
    from PIL import Image
    cands = json.load(open(path, encoding="utf-8"))
    choice = json.load(open(choice_path, encoding="utf-8"))
    out = os.path.join(ROOT, "img")
    os.makedirs(out, exist_ok=True)
    meta = {}
    for rid, k in choice.items():
        lst = cands.get(rid) or []
        if k is None or not lst or k >= len(lst):
            continue
        c = lst[k]
        im = Image.open(os.path.join(cache_dir, f"{rid}__{k}.jpg")).convert("RGB")
        if im.width > 600:
            im = im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS)
        im.save(os.path.join(out, rid + ".jpg"), "JPEG", quality=80, optimize=True, progressive=True)
        meta[rid] = {"f": "img/" + rid + ".jpg", "a": short_author(c["author"]), "l": c["license"], "u": c["page"]}
    with open(os.path.join(ROOT, "photos.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* Фотографии блюд с Wikimedia Commons (свободные лицензии). Собрано tools/photos.py.\n"
                "   f — файл, a — автор, l — лицензия, u — страница фото. */\n")
        f.write("window.PHOTOS = " + json.dumps(meta, ensure_ascii=False, indent=0) + ";\n")
    print("built", len(meta))


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "build":
        cmd_build(sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) >= 3 and sys.argv[1] == "search":
        cmd_search(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "download":
        cmd_download(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        sys.exit(__doc__)
