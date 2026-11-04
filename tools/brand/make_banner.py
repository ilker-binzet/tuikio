#!/usr/bin/env python3
"""Renders docs/images/banner.png (3:2, 1800x1200) and banner-16x9.png (1920x1080) in the style
of the Design Review's identity board (docs/design/boards/Main.png), from the app's own assets:
the Kio mascot and wordmark (app/src/main/res/drawable, converted to SVG) and its fonts. The
game count comes from catalog/games. Needs Playwright (Node) and Pillow.

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


NETHACK = """\
 <y>You see here a gold piece.</y>

   ---------           --------
   |.......|           |......|
   |...<b>@</b>...+###########+..<r>d</r>...|
   |..<y>$</y>....|     #     |....<m>&gt;</m>.|
   ----+----     #     --------
       #         #
       ##########<g>%</g>##########
"""


def page(W, H, L, d):
    """In the style of the Design Review's identity board: Tidepool palette, ink outlines with a
    hard drop, Unbounded/Figtree/JetBrains Mono, Kio."""
    nethack = (NETHACK.replace("<y>", '<span style="color:#FFC93C">').replace("</y>", "</span>")
               .replace("<b>", '<span style="color:#FFFFFF;background:#FF6B4A;border-radius:3px">').replace("</b>", "</span>")
               .replace("<r>", '<span style="color:#FF8A6E">').replace("</r>", "</span>")
               .replace("<m>", '<span style="color:#3BE3B0">').replace("</m>", "</span>")
               .replace("<g>", '<span style="color:#B9A6FF">').replace("</g>", "</span>"))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Unb;src:url(file://{FONTS}/Unbounded-Variable.ttf)}}
@font-face{{font-family:Fig;src:url(file://{FONTS}/Figtree-Variable.ttf)}}
@font-face{{font-family:Mono;src:url(file://{FONTS}/JetBrainsMono-Variable.ttf)}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#F6F3FB;position:relative;font-family:Fig;color:#1E1A3A}}
.dots{{position:absolute;inset:0;background-image:radial-gradient(rgba(30,26,58,.09) 1.6px,transparent 1.8px);background-size:32px 32px}}
.txt{{position:absolute;left:{L['tx']}px;top:{L['ty']}px;width:{L['tw']}px}}
.wm{{height:{L['wm']}px;display:block}}
.tag{{font:800 {L['fs']}px/1.06 Unb;letter-spacing:-.02em;margin:{L['fs']*0.55}px 0 {L['fs']*0.4}px}}
.tag em{{font-style:normal;color:#FF6B4A}}
.lede{{font:600 {L['fs']*0.4}px/1.4 Fig;color:#4A4566;max-width:{L['tw']}px}}
.chips{{display:flex;gap:14px;margin-top:{L['fs']*0.5}px}}
.chip{{display:inline-flex;align-items:center;gap:10px;height:{L['ch']}px;padding:0 {L['ch']*0.42}px;border-radius:999px;font:800 {L['ch']*0.42}px Fig;border:3px solid #1E1A3A;box-shadow:0 4px 0 #1E1A3A}}
.card{{position:absolute;background:#1B1838;border:4px solid #1E1A3A;border-radius:34px;box-shadow:0 12px 0 #1E1A3A;overflow:hidden}}
.bar{{height:56px;background:#2A2550;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:4px solid #1E1A3A}}
.bar i{{width:18px;height:18px;border-radius:50%;border:3px solid #1E1A3A}}
.bar b{{margin-left:auto;font:700 20px Mono;color:#C9C4E8}}
.scr{{font:600 {L['mono']}px/1.3 Mono;color:#E9E6FF;white-space:pre;padding:22px 28px}}
.stat{{font:700 {L['mono']*0.82}px Mono;color:#B9B3DA;padding:0 28px 22px;display:flex;justify-content:space-between}}
.cart{{position:absolute;border:4px solid #1E1A3A;border-radius:28px;box-shadow:0 10px 0 #1E1A3A;overflow:hidden;background:#FFFFFF}}
.cart .s{{background:#1B1838;font:700 {L['cm']}px/1.15 Mono;white-space:pre;padding:18px 22px;border-bottom:4px solid #1E1A3A}}
.cart .t{{padding:12px 20px 16px;font:800 {L['cm']*0.95}px Fig;display:flex;align-items:center;justify-content:space-between;gap:10px}}
.pill{{font:800 {L['cm']*0.6}px Fig;padding:5px 12px;border-radius:999px;border:3px solid #1E1A3A;background:#2BD9A0}}
.kio{{position:absolute;left:{L['kx']}px;top:{L['ky']}px;width:{L['ks']}px}}
</style></head><body><div class="dots"></div>
<div class="cart" style="left:{L['c1x']}px;top:{L['c1y']}px;transform:rotate(-7deg)"><div class="s" style="color:#3BE3B0">┌────┬────┬────┐
│  2 │  4 │  8 │
├────┼────┼────┤
│ 16 │ 32 │  2 │
├────┼────┼────┤
│128 │ 64 │  4 │
└────┴────┴────┘</div><div class="t">2048<span class="pill">Plays here</span></div></div>
<div class="cart" style="left:{L['c2x']}px;top:{L['c2y']}px;transform:rotate(6deg)"><div class="s" style="color:#B9A6FF">│      ▓▓      │
│     ▓▓       │
│              │
│ ░░       ▒▒  │
│░░░░▒▒▒▒▒▒▒▒░░│
└──────────────┘</div><div class="t">Tetris<span class="pill">Plays here</span></div></div>
<div class="card" style="left:{L['mx']}px;top:{L['my']}px;width:{L['mw']}px">
<div class="bar"><i style="background:#FF6B4A"></i><i style="background:#FFC93C"></i><i style="background:#2BD9A0"></i><b>nethack</b></div>
<div class="scr">{nethack}</div>
<div class="stat"><span>Dlvl:1  $:14  HP:12(12)</span><span>T:418</span></div></div>
<img class="kio" src="file://{d}/kio.svg">
<div class="txt"><img class="wm" src="file://{d}/wordmark.svg">
<div class="tag">Terminal games,<br><em>carried home.</em></div>
<div class="lede">{L['count']} real terminal games for Android: native ports with touch controls made for each one.</div>
<div class="chips"><span class="chip" style="background:#FFC93C">{L['count']} games</span><span class="chip" style="background:#2BD9A0">Plays offline</span><span class="chip" style="background:#FFFFFF">Open source</span></div></div>
</body></html>"""


def main():
    count = len([f for f in os.listdir(os.path.join(ROOT, "catalog/games")) if f.endswith(".json")])
    layouts = {
        "banner": (1800, 1200, dict(tx=120, ty=170, tw=760, wm=150, fs=70, ch=60, mono=24, cm=22,
                                    mx=960, my=400, mw=740, cw=0, c1x=1000, c1y=110, c2x=1350, c2y=80,
                                    kx=640, ky=780, ks=330)),
        "banner-16x9": (1920, 1080, dict(tx=130, ty=170, tw=800, wm=140, fs=70, ch=58, mono=23, cm=21,
                                         mx=1060, my=330, mw=720, cw=0, c1x=1080, c1y=70, c2x=1430, c2y=50,
                                         kx=720, ky=700, ks=310)),
    }
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "kio.svg"), "w").write(vector_to_svg("kio"))
        open(os.path.join(d, "wordmark.svg"), "w").write(vector_to_svg("wordmark_tuikio"))
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
