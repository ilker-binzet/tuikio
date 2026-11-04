#!/usr/bin/env python3
"""Renders docs/images/banner.png (3:2, 1800x1200) and banner-16x9.png (1920x1080) from the
app's own assets: the Kio mascot and light wordmark (app/src/main/res/drawable, converted to
SVG), its fonts, and real game screens from RenderShotsTest (app/build/shots: run
`./gradlew :app:test --tests '*RenderShotsTest.portrait' --tests '*RenderShotsTest.landscape'
-Pshots=lantern-tide,doom-ascii,solvitaire` first). Needs Playwright (Node) and Pillow.

    python3 tools/brand/make_banner.py
"""
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RES = os.path.join(ROOT, "app/src/main/res/drawable")
FONTS = os.path.join(ROOT, "app/src/main/assets/fonts")
SHOTS = os.path.join(ROOT, "app/build/shots")
A = "{http://schemas.android.com/apk/res/android}"


def vector_to_svg(name):
    """Android vector drawable -> SVG (paths, groups with translate/rotate, fill and stroke)."""
    def color(c):
        if not c:
            return None, 1
        c = c.lstrip("#")
        return ("#" + c[2:], int(c[:2], 16) / 255) if len(c) == 8 else ("#" + c, 1)

    def conv(el):
        out = []
        for ch in el:
            if ch.tag == "group":
                t = []
                if ch.get(A + "translateX") or ch.get(A + "translateY"):
                    t.append(f"translate({ch.get(A + 'translateX', '0')} {ch.get(A + 'translateY', '0')})")
                if ch.get(A + "rotation"):
                    t.append(f"rotate({ch.get(A + 'rotation')} {ch.get(A + 'pivotX', '0')} {ch.get(A + 'pivotY', '0')})")
                out.append(f'<g transform="{" ".join(t)}">' + conv(ch) + "</g>")
            elif ch.tag == "path":
                f, fo = color(ch.get(A + "fillColor"))
                s, _ = color(ch.get(A + "strokeColor"))
                a = [f'd="{ch.get(A + "pathData")}"', f'fill="{f or "none"}"']
                if fo < 1:
                    a.append(f'fill-opacity="{fo:.3f}"')
                if s:
                    a += [f'stroke="{s}"', f'stroke-width="{ch.get(A + "strokeWidth", "1")}"']
                for k, v in (("strokeLineCap", "stroke-linecap"), ("strokeLineJoin", "stroke-linejoin")):
                    if ch.get(A + k):
                        a.append(f'{v}="{ch.get(A + k)}"')
                out.append("<path " + " ".join(a) + "/>")
        return "".join(out)

    r = ET.parse(os.path.join(RES, name + ".xml")).getroot()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {r.get(A + "viewportWidth")} '
            f'{r.get(A + "viewportHeight")}">' + conv(r) + "</svg>")


def page(W, H, L, d):
    s = lambda n: f"file://{SHOTS}/{n}.png"  # noqa: E731
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Fig;src:url(file://{FONTS}/Figtree-Variable.ttf)}}
@font-face{{font-family:Mono;src:url(file://{FONTS}/JetBrainsMono-Variable.ttf)}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#1E1A3A;position:relative;font-family:Fig;color:#F3F0FF}}
.glow{{position:absolute;inset:0;background:radial-gradient(circle at {L['gx']}% 55%,rgba(255,107,74,.28),transparent 42%),radial-gradient(circle at 18% 12%,rgba(59,227,176,.16),transparent 38%)}}
.grid{{position:absolute;inset:0;background-image:radial-gradient(rgba(243,240,255,.10) 1.4px,transparent 1.6px);background-size:28px 28px}}
.txt{{position:absolute;left:{L['tx']}px;top:{L['ty']}px}}
.wm{{height:150px;display:block}}
.tag{{font-size:74px;font-weight:700;line-height:1.12;margin:40px 0 30px;letter-spacing:-.01em}}
.tag b{{color:#3BE3B0;font-weight:700}}
.sub{{font-family:Mono;font-size:27px;color:#DCD6EA;font-weight:500;line-height:1.5;white-space:nowrap}}
.sub i{{font-style:normal;color:#FFC93C}} .p{{color:#3BE3B0;font-weight:700}}
.phone{{position:absolute;background:#0E0B22;border-radius:34px;padding:12px;box-shadow:0 30px 80px rgba(0,0,0,.55),0 0 0 3px rgba(243,240,255,.14)}}
.phone img{{display:block;border-radius:22px}}
.kio{{position:absolute;left:{L['kx']}px;top:{L['ky']}px;width:{L['ks']}px}}
</style></head><body><div class="glow"></div><div class="grid"></div>
<div class="txt"><img class="wm" src="file://{d}/wordmark.svg">
<div class="tag">Real terminal games,<br><b>on your phone.</b></div>
<div class="sub"><span class="p">$</span> {L['count']} games: <i>NetHack</i>, <i>Brogue</i>, <i>Doom</i>, <i>Pokete</i>…<br>&nbsp;&nbsp;native ports · touch controls · open source</div></div>
<div class="phone" style="left:{L['lx']}px;top:{L['ly']}px;transform:rotate(-4deg)"><img src="{s('doom-ascii-land')}" style="width:{L['lw']}px"></div>
<div class="phone" style="left:{L['l2x']}px;top:{L['l2y']}px;transform:rotate(3deg)"><img src="{s('solvitaire-land')}" style="width:{L['lw']}px"></div>
<div class="phone" style="left:{L['px']}px;top:{L['py']}px"><img src="{s('lantern-tide-port')}" style="height:{L['ph']}px"></div>
<img class="kio" src="file://{d}/kio.svg"></body></html>'''


def main():
    count = len([f for f in os.listdir(os.path.join(ROOT, "catalog/games")) if f.endswith(".json")])
    layouts = {
        "banner": (1800, 1200, dict(gx=70, tx=110, ty=120, lx=930, ly=470, l2x=870, l2y=820, lw=760, px=1310, py=140, ph=920, kx=90, ky=820, ks=330)),
        "banner-16x9": (1920, 1080, dict(gx=72, tx=120, ty=150, lx=930, ly=120, l2x=880, l2y=560, lw=740, px=1430, py=110, ph=860, kx=110, ky=700, ks=320)),
    }
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "kio.svg"), "w").write(vector_to_svg("kio"))
        open(os.path.join(d, "wordmark.svg"), "w").write(vector_to_svg("wordmark_tuikio").replace('fill="#1E1A3A"', 'fill="#F3F0FF"'))
        jobs = []
        for name, (W, H, L) in layouts.items():
            L["count"] = count
            open(os.path.join(d, name + ".html"), "w").write(page(W, H, L, d))
            jobs.append([name, W, H])
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
              f"for(const [n,w,h] of {jobs!r}){{const p=await b.newPage({{viewport:{{width:w,height:h}},deviceScaleFactor:1}});"
              f"await p.goto('file://{d}/'+n+'.html');await p.waitForTimeout(500);"
              f"await p.screenshot({{path:'{d}/'+n+'.png'}});}}await b.close();}})();")
        subprocess.run(["node", "-e", js], check=True)
        for name in layouts:
            # Full colour: a 256-colour palette shifts the accent colours.
            Image.open(os.path.join(d, name + ".png")).convert("RGB").save(
                os.path.join(ROOT, "docs/images", name + ".png"), optimize=True)
            print("wrote docs/images/" + name + ".png")


if __name__ == "__main__":
    main()
