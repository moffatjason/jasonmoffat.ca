"""Generate the work pages for jasonmoffat.ca from _src/work.json.

Run from anywhere:  python site/_src/build.py
Writes: work/<group>.html, work/<project>.html, work/<role>.html,
        img/work/<project>/NN.jpg (web-sized copies of img/legacy), img/work-experiments.jpg
"""
import json, html as H, pathlib
from PIL import Image

SRC = pathlib.Path(__file__).parent
SITE = SRC.parent
DATA = json.loads((SRC / "work.json").read_text(encoding="utf-8"))
LEGACY = SITE / "img" / "legacy"
OUT = SITE / "work"; OUT.mkdir(exist_ok=True)

def e(s): return H.escape(s, quote=True)

def crumbbar(trail):
    """trail: list of (label, href or None); the last item is the current page."""
    parts = []
    for i, (label, href) in enumerate(trail):
        if i: parts.append('<span class="sep">/</span>')
        cls = ' class="home"' if i == 0 else ""
        parts.append(f'<a{cls} href="{href}">{e(label)}</a>' if href else f'<span class="here">{e(label)}</span>')
    return f'<div class="crumbbar"><div class="wrap">{"".join(parts)}</div></div>\n'

def links_row(items):
    if not items: return ""
    out = "".join(f'<a class="btn" href="{i["href"]}" target="_blank" rel="noopener">{e(i["label"])}</a>' for i in items)
    return f'<div class="btns">{out}</div>'

def head(title, desc, trail=()):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Jason Moffat</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" type="image/png" href="../img/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="../css/site.css">
</head>
<body>
<nav>
  <div class="wrap">
    <a class="brand" href="../index.html">Jason Moffat</a>
    <ul>
      <li><a href="../index.html#hyperflora">Hyperflora</a></li>
      <li><a href="../index.html#work">Work</a></li>
      <li><a href="../index.html#how">Approach</a></li>
      <li><a href="../index.html#connect">Connect</a></li>
      <li><a class="cta" href="../jason-moffat-resume.pdf">Resume</a></li>
    </ul>
  </div>
</nav>
""" + crumbbar(trail)

FOOT = """
<footer>
  <div class="wrap">
    <span>© 2026 Jason Moffat</span>
    <span><a href="../index.html#connect">Connect</a></span>
  </div>
</footer>
</body>
</html>
"""

def video_block(v):
    if "vimeo" in v:
        src = f"https://player.vimeo.com/video/{v['vimeo']}?dnt=1&title=0&byline=0&portrait=0"
    else:
        src = f"https://www.youtube-nocookie.com/embed/{v['yt']}?rel=0"
    cap = f'<div class="caption">{e(v["caption"])}</div>' if v.get("caption") else ""
    return f'<div><div class="video"><iframe src="{src}" loading="lazy" allow="fullscreen; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen title="Video"></iframe></div>{cap}</div>'

def prepare_images(slug):
    """Web-size every legacy image for a project; return list of (rel_path, is_square)."""
    src_dir = LEGACY / slug
    if not src_dir.exists(): return []
    out_dir = SITE / "img" / "work" / slug; out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for n, p in enumerate(sorted(x for x in src_dir.iterdir() if x.is_file() and "-thumb" not in x.name), 1):
        try: im = Image.open(p)
        except Exception: continue
        w, h = im.size; ratio = w / h
        cls = "sq" if ratio < 1.25 else "wide" if ratio > 2.2 else ""
        outp = out_dir / f"{n:02d}.jpg"
        if not outp.exists():
            im = im.convert("RGB")
            if im.width > 1600: im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
            im.save(outp, "JPEG", quality=80, optimize=True, progressive=True)
        items.append((f"../img/work/{slug}/{n:02d}.jpg", cls))
    return items

def project_page(slug, group_id, prev, nxt):
    p = DATA["projects"][slug]; g = DATA["groups"][group_id]
    meta = [f"<span><b>{e(g['employer'])}</b></span>"]
    if p.get("client"): meta.append(f"<span>{e(p['client'])}</span>")
    meta.append(f"<span>{e(p.get('year', g['years']))}</span>")
    meta.append(f"<span>{e(p['type'])}</span>")
    if p.get("format"): meta.append(f"<span>{e(p['format'])}</span>")
    videos = "".join(video_block(v) for v in p.get("videos", []))
    imgs = prepare_images(slug)
    gallery = "".join(f'<a href="{src}" target="_blank" class="{cls}"><img src="{src}" alt="{e(p["title"])}" loading="lazy"></a>' for src, cls in imgs)
    prose = "".join(f"<p>{e(t)}</p>" for t in p["text"])
    pager = []
    pager.append(f'<a href="{prev}.html">Previous: {e(DATA["projects"][prev]["title"])}</a>' if prev else "<span></span>")
    pager.append(f'<a href="{nxt}.html">Next: {e(DATA["projects"][nxt]["title"])}</a>' if nxt else "<span></span>")
    body = f"""
<section class="page">
  <div class="wrap">
    <h1>{e(p['title'])}</h1>
    <div class="meta">{"".join(meta)}</div>
    {f'<div class="videos">{videos}</div>' if videos else ""}
    <div class="prose">{prose}</div>
    {links_row(p.get("links"))}
    {f'<div class="gallery">{gallery}</div>' if gallery else ""}
    <div class="pager">{"".join(pager)}</div>
  </div>
</section>"""
    trail = [("Home", "../index.html"), ("Work", "../index.html#work"), (g["title"], f"{group_id}.html"), (p["title"], None)]
    (OUT / f"{slug}.html").write_text(head(p["title"], p["text"][0][:150], trail) + body + FOOT, encoding="utf-8")

def group_page(gid):
    g = DATA["groups"][gid]
    tiles = "".join(
        f'<a class="tile" href="{s}.html"><img src="../img/thumbs/{s}.jpg" alt="{e(DATA["projects"][s]["title"])}" loading="lazy"><span class="t">{e(DATA["projects"][s]["title"])}</span><span class="k">{e(DATA["projects"][s]["type"])}</span></a>'
        for s in g["projects"])
    intro = "".join(f"<p>{e(t)}</p>" for t in g["intro"])
    body = f"""
<section class="page">
  <div class="wrap">
    <h1>{e(g['title'])}</h1>
    <div class="meta"><span><b>{e(g['employer'])}</b></span><span>{e(g['years'])}</span><span>{e(g['role'])}</span></div>
    {f'<div class="cover"><img src="../{g["cover"]}" alt="{e(g.get("cover_alt", g["title"]))}"></div>' if g.get("cover") else ""}
    <div class="prose">{intro}</div>
    {links_row(g.get("links"))}
    <div class="tiles">{tiles}</div>
    <div class="pager"><a href="../index.html#work">Back to all work</a><span></span></div>
  </div>
</section>"""
    trail = [("Home", "../index.html"), ("Work", "../index.html#work"), (g["title"], None)]
    (OUT / f"{gid}.html").write_text(head(g["title"], g["intro"][0][:150], trail) + body + FOOT, encoding="utf-8")

def role_page(rid):
    r = DATA["roles"][rid]
    prose = "".join(f"<p>{e(t)}</p>" for t in r["text"])
    body = f"""
<section class="page">
  <div class="wrap">
    <h1>{e(r['title'])}</h1>
    <div class="meta"><span><b>{e(r['employer'])}</b></span><span>{e(r['years'])}</span><span>{e(r['role'])}</span><span>{e(r['type'])}</span></div>
    <div class="prose">{prose}</div>
    {links_row(r.get("links"))}
    <div class="pager"><a href="../index.html#work">Back to all work</a><span></span></div>
  </div>
</section>"""
    trail = [("Home", "../index.html"), ("Work", "../index.html#work"), (r["title"], None)]
    (OUT / f"{rid}.html").write_text(head(r["title"], r["text"][0][:150], trail) + body + FOOT, encoding="utf-8")

def experiments_cover():
    """21:9 cover for the studio group, cropped from the Sound Table launchpad photo."""
    src = LEGACY / "sound-table" / "sound-table-04.jpg"
    if not src.exists(): return
    im = Image.open(src).convert("RGB")
    w, h = im.size; ch = round(w / (21 / 9))
    top = min(max(round(h * 0.60) - ch // 2, 0), h - ch)   # bias low: the lit pads sit below centre
    im = im.crop((0, top, w, top + ch)).resize((1600, round(1600 * ch / w)), Image.LANCZOS)
    im.save(SITE / "img" / "work-experiments.jpg", "JPEG", quality=82, optimize=True, progressive=True)

def main():
    for gid, g in DATA["groups"].items():
        group_page(gid)
        ps = g["projects"]
        for i, s in enumerate(ps):
            project_page(s, gid, ps[i - 1] if i > 0 else None, ps[i + 1] if i + 1 < len(ps) else None)
    for rid in DATA["roles"]: role_page(rid)
    experiments_cover()
    n = len(list(OUT.glob("*.html")))
    print(f"wrote {n} pages to {OUT}")

if __name__ == "__main__":
    main()
