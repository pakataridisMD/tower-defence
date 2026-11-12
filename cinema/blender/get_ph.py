"""Fetch CC0 Poly Haven assets for the story sets into cinema/blender/ph/ (run on the Mac: the cloud can't reach
polyhaven.com). Plain Python 3, no Blender needed.

    python3 get_ph.py              # the default shopping list below
    python3 get_ph.py --dry        # only print what it would fetch

Every asset is CC0 (polyhaven.com/license). ph/assets.json records each one with its source URL."""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("PH_OUT") or os.path.join(HERE, "ph")
API = "https://api.polyhaven.com"
UA = {"User-Agent": "cinema-set-fetch/1.0"}
RES = "1k"

# (kind, search words, how many). Words match the asset id, name, tags or categories; most-downloaded first.
WANT = [
    ("models", ["rock", "boulder", "cliff"], 8),
    ("models", ["dead tree", "tree trunk", "root"], 5),
    ("models", ["tree", "pine", "fir"], 5),
    ("models", ["ruin", "pillar", "column", "arch", "statue"], 6),
    ("models", ["barrel", "crate", "cart", "wagon"], 5),
    ("models", ["lantern", "lamp", "brazier", "candle"], 4),
    ("models", ["anvil", "hammer", "tool"], 3),
    ("models", ["shield", "sword", "spear"], 3),
    ("models", ["bench", "table", "chair", "stool"], 3),
    ("models", ["fern", "grass", "shrub", "bush", "plant"], 5),
    ("textures", ["lava", "volcanic", "basalt"], 3),
    ("textures", ["snow", "ice"], 3),
    ("textures", ["sand", "dirt", "gravel"], 3),
    ("textures", ["forest", "moss", "leaves"], 3),
    ("textures", ["cobble", "paving", "brick", "castle"], 4),
    ("textures", ["wood", "plank"], 2),
    ("textures", ["rock", "cliff"], 3),
    ("hdris", ["night", "moon"], 3),
    ("hdris", ["dusk", "sunset", "evening"], 3),
    ("hdris", ["overcast", "cloudy", "storm"], 3),
    ("hdris", ["sunrise", "morning"], 2),
]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def save(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url)
    with open(path + ".part", "wb") as f:
        f.write(data)
    os.replace(path + ".part", path)


def pick(kind, words, n, have):
    allx = json.loads(get("%s/assets?t=%s" % (API, kind)))
    def hit(aid, a):
        hay = " ".join([aid, a.get("name", "")] + a.get("tags", []) + a.get("categories", [])).lower()
        return any(w in hay for w in words)
    found = sorted(((a.get("download_count", 0), aid) for aid, a in allx.items() if hit(aid, a) and aid not in have), reverse=True)
    return [(aid, allx[aid]) for _, aid in found[:n]]


def fetch(kind, aid):
    files = json.loads(get("%s/files/%s" % (API, aid)))
    d = os.path.join(OUT, aid); got = []
    if kind == "models":
        g = files["gltf"][RES]["gltf"]
        save(g["url"], os.path.join(d, os.path.basename(g["url"]))); got.append(os.path.basename(g["url"]))
        for rel, inc in g.get("include", {}).items():
            save(inc["url"], os.path.join(d, rel)); got.append(rel)
    elif kind == "textures":
        for key, short in (("Diffuse", "diff"), ("nor_gl", "nor_gl"), ("Rough", "rough"), ("Displacement", "disp")):
            if key in files and RES in files[key]:
                u = files[key][RES]["jpg"]["url"] if "jpg" in files[key][RES] else files[key][RES]["png"]["url"]
                ext = os.path.splitext(u)[1]
                name = "%s_%s_%s%s" % (aid, short, RES, ext)
                save(u, os.path.join(d, name)); got.append(name)
    else:
        u = files["hdri"][RES]["hdr"]["url"]
        name = "%s_%s.hdr" % (aid, RES); save(u, os.path.join(d, name)); got.append(name)
    return got


def main():
    dry = "--dry" in sys.argv
    meta_path = os.path.join(OUT, "assets.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {"source": "Poly Haven (polyhaven.com), all CC0 1.0", "assets": []}
    have = {a["id"] for a in meta["assets"]}
    for kind, words, n in WANT:
        for aid, a in pick(kind, words, n, have):
            print(kind, aid, "-", a.get("name"), flush=True)
            if dry:
                continue
            try:
                got = fetch(kind, aid)
            except Exception as e:   # keep going: one broken asset should not stop the list
                print("  skipped:", e, flush=True)
                continue
            have.add(aid)
            meta["assets"].append({"id": aid, "type": kind[:-1], "role": "/".join(words), "files": got, "license": "CC0",
                                   "source": "https://polyhaven.com/a/%s" % aid})
            json.dump(meta, open(meta_path, "w"), indent=1)
    print("done:", len(meta["assets"]), "assets in", OUT)


if __name__ == "__main__":
    main()
