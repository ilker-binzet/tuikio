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
    """The Design Review's identity board (Tidepool palette, sticker outlines, Unbounded/Figtree)."""
    s = lambda n: f"file://{SHOTS}/{n}.png"  # noqa: E731
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Unb;src:url(file://{FONTS}/Unbounded-Variable.ttf)}}
@font-face{{font-family:Fig;src:url(file://{FONTS}/Figtree-Variable.ttf)}}
@font-face{{font-family:Mono;src:url(file://{FONTS}/JetBrainsMono-Variable.ttf)}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#F6F3FB;position:relative;font-family:Fig;color:#1E1A3A}}
.grid{{position:absolute;inset:0;background-image:radial-gradient(rgba(30,26,58,.10) 1.6px,transparent 1.8px);background-size:30px 30px}}
.blob{{position:absolute;border-radius:50%}}
.txt{{position:absolute;left:{L['tx']}px;top:{L['ty']}px;display:flex;flex-direction:column;gap:26px}}
.wm{{height:{L['wm']}px;align-self:flex-start}}
.tag{{font-size:{L['fs']}px;font-weight:800;line-height:1.08;letter-spacing:-.01em}}
.tag b{{background:#2BD9A0;padding:0 14px;border-radius:18px;border:3px solid #1E1A3A;box-shadow:0 5px 0 #1E1A3A;display:inline-block;margin-top:8px}}
.chips{{display:flex;gap:14px;flex-wrap:wrap}}
.chip{{display:inline-flex;align-items:center;height:52px;padding:0 22px;border-radius:999px;font-weight:800;font-size:23px;border:3px solid #1E1A3A;box-shadow:0 4px 0 #1E1A3A}}
.term{{font-family:Mono;font-size:24px;background:#1B1838;color:#E9E6FF;border-radius:16px;padding:14px 20px;border:3px solid #1E1A3A;box-shadow:0 6px 0 #1E1A3A;align-self:flex-start}}
.term i{{font-style:normal;color:#3BE3B0}} .term u{{text-decoration:none;color:#FF6B4A}}
.phone{{position:absolute;background:#1E1A3A;border-radius:38px;padding:12px;border:3px solid #1E1A3A;box-shadow:0 10px 0 #1E1A3A}}
.phone img{{display:block;border-radius:26px}}
.peb{{position:absolute;left:{L['kx']}px;top:{L['ky']}px;width:{L['ks']}px;height:{L['ks']}px;background:#DDF8EE;border:3px solid #1E1A3A;border-radius:44px;box-shadow:0 8px 0 #1E1A3A;display:flex;align-items:center;justify-content:center;transform:rotate(-4deg)}}
.peb img{{width:84%}}
</style></head><body><div class="grid"></div>
<div class="blob" style="left:{L['b1x']}px;top:{L['b1y']}px;width:{L['b1s']}px;height:{L['b1s']}px;background:#FFE6DF"></div>
<div class="blob" style="left:{L['b2x']}px;top:{L['b2y']}px;width:{L['b2s']}px;height:{L['b2s']}px;background:#E6E3FF"></div>
<div class="txt"><img class="wm" src="file://{d}/wordmark.svg">
<div class="tag">Terminal games,<br><b>carried home.</b></div>
<div class="chips"><span class="chip" style="background:#FFC93C">{L['count']} games</span><span class="chip" style="background:#2BD9A0">Plays offline</span><span class="chip" style="background:#FFFFFF">Open source</span></div>
<div class="term"><i>&gt;</i> nethack · brogue · doom · pokete<u>▌</u></div></div>
<div class="phone" style="left:{L['lx']}px;top:{L['ly']}px;transform:rotate(-4deg)"><img src="{s('doom-ascii-land')}" style="width:{L['lw']}px"></div>
<div class="phone" style="left:{L['l2x']}px;top:{L['l2y']}px;transform:rotate(3deg)"><img src="{s('solvitaire-land')}" style="width:{L['lw']}px"></div>
<div class="phone" style="left:{L['px']}px;top:{L['py']}px"><img src="{s('lantern-tide-port')}" style="height:{L['ph']}px"></div>
<div class="peb"><img src="file://{d}/kio.svg"></div></body></html>'''


def main():
    count = len([f for f in os.listdir(os.path.join(ROOT, "catalog/games")) if f.endswith(".json")])
    layouts = {
        "banner": (1800, 1200, dict(tx=110, ty=110, wm=130, fs=70, lx=960, ly=470, l2x=900, l2y=830, lw=720, px=1330, py=120, ph=900,
                                    kx=200, ky=730, ks=300, b1x=1100, b1y=-200, b1s=760, b2x=-200, b2y=780, b2s=620)),
        "banner-16x9": (1920, 1080, dict(tx=120, ty=120, wm=130, fs=70, lx=960, ly=110, l2x=900, l2y=560, lw=720, px=1450, py=100, ph=860,
                                         kx=210, ky=660, ks=290, b1x=1250, b1y=-260, b1s=760, b2x=-220, b2y=700, b2s=600)),
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
