#!/usr/bin/env python3
"""plan.json → 横向翻页 HTML 演示（同时是逐页检查与预览图的渲染源）。

用法：python3 build_html.py plan.json [-o out/deck.html]
浏览：←/→/空格 翻页，ESC 或 O 切换总览，URL 加 ?mode=print 时全部页面纵向平铺（供截图检查）。
"""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path

from deck_lib import Plan, css_font_stack, font_role, line_spacing

PT_TO_PX = 4 / 3  # plan 字号/字距用 pt，画布用 px（960pt ↔ 1280px）


class HtmlDeckBuilder:
    def __init__(self, plan: Plan, out: Path):
        self.plan = plan
        self.out = out.resolve()
        self.missing: list[str] = []

    # 资源用相对 out 的路径引用，HTML 可以直接双击打开，也方便整个目录打包
    def _url(self, ref: str | None) -> str | None:
        p = self.plan.resolve(ref)
        if ref and p is None:
            self.missing.append(ref)
            return None
        return Path(os.path.relpath(p, self.out.parent)).as_posix() if p else None

    def _bg(self, s: dict) -> str:
        parts = []
        if s.get("background_color"):
            parts.append(f'<div class="bgc" style="background:{s["background_color"]}"></div>')
        url = self._url(s.get("background"))
        if url:
            f = {"x": 0, "y": 0, "w": self.plan.width, "h": self.plan.height, **s.get("background_frame", {})}
            flip = "transform:scaleX(-1);" if s.get("image_horizontal_flip") else ""
            parts.append(
                f'<img class="bg" src="{html.escape(url)}" style="left:{f["x"]}px;top:{f["y"]}px;'
                f'width:{f["w"]}px;height:{f["h"]}px;{flip}" alt="">'
            )
        return "".join(parts)

    def _shape(self, sh: dict) -> str:
        kind = sh.get("type", "rect")
        op = sh.get("opacity", 1)
        if kind == "line":
            # 统一转成细矩形，HTML 与 PPTX 的线宽和位置才能一一对应
            x1, y1, x2, y2 = sh["x1"], sh["y1"], sh["x2"], sh["y2"]
            wpx = sh.get("width", 1)
            if y1 == y2:
                box = (min(x1, x2), y1 - wpx / 2, abs(x2 - x1), wpx)
            else:
                box = (x1 - wpx / 2, min(y1, y2), wpx, abs(y2 - y1))
            return (f'<div class="sh" style="left:{box[0]}px;top:{box[1]}px;width:{box[2]}px;'
                    f'height:{box[3]}px;background:{sh.get("color", "#000")};opacity:{op}"></div>')
        style = f'left:{sh["x"]}px;top:{sh["y"]}px;width:{sh["w"]}px;height:{sh["h"]}px;opacity:{op};'
        if kind == "image":
            url = self._url(sh.get("src"))
            fit = sh.get("fit", "cover")
            # mask：circle 圆/椭圆、arch 上半圆拱、rounded 圆角；与 PPTX 端的几何形状一一对应
            mask = {"circle": "border-radius:50%;", "arch": f'border-radius:{sh["w"] / 2}px {sh["w"] / 2}px 0 0;',
                    "rounded": f'border-radius:{sh.get("radius", 16)}px;'}.get(sh.get("mask"), "")
            pos = f'object-position:{sh["focus"]};' if sh.get("focus") else ""
            gray = "filter:grayscale(1);" if sh.get("grayscale") else ""
            if not url:
                return f'<div class="sh ph" style="{style}{mask}">IMAGE · {html.escape(sh.get("src", ""))}</div>'
            return f'<img class="sh" src="{html.escape(url)}" style="{style}object-fit:{fit};{pos}{mask}{gray}" alt="">'
        border = f'border:{sh["line_width"]}px solid {sh["line"]};' if sh.get("line") else ""
        fill = sh.get("fill", "transparent")
        radius = "border-radius:50%;" if kind == "ellipse" else (f'border-radius:{sh["radius"]}px;' if sh.get("radius") else "")
        return f'<div class="sh" style="{style}background:{fill};{border}{radius}box-sizing:border-box"></div>'

    def _text(self, t: dict) -> str:
        role = font_role(t.get("font", "sans-zh"))
        size_px = t.get("size", 14) * PT_TO_PX
        ls = t.get("charSpacing", 0) * PT_TO_PX
        lh = line_spacing(t)
        italic = t.get("italic", role.get("italic", False))
        weight = t.get("weight", role.get("weight", 400))
        # rotate：绕文本框中心旋转（与 PPTX 的 rotation 语义一致），用于竖向书脊字、侧边标签
        rot = f'transform:rotate({t["rotate"]}deg);transform-origin:center;' if t.get("rotate") else ""
        deco = "text-decoration:underline;text-underline-offset:0.18em;" if t.get("underline") else ""
        upper = "text-transform:uppercase;" if t.get("uppercase") else ""
        style = (
            f'left:{t["x"]}px;top:{t["y"]}px;width:{t["w"]}px;height:{t["h"]}px;'
            f'font-family:{css_font_stack(t.get("font", "sans-zh"))};font-size:{size_px:.2f}px;'
            f'color:{t.get("color", "#222")};text-align:{t.get("alignment", "left")};'
            f'letter-spacing:{ls:.2f}px;line-height:{lh};font-weight:{weight};'
            f'{"font-style:italic;" if italic else ""}{rot}{deco}{upper}'
        )
        return (f'<div class="t" data-name="{html.escape(t.get("name", ""))}" '
                f'data-font="{html.escape(t.get("font", ""))}" data-rotate="{t.get("rotate", 0)}" '
                f'data-bleed="{1 if t.get("bleed") else 0}" '
                f'style="{style}">{html.escape(t["value"])}</div>')

    def build(self) -> Path:
        p = self.plan
        slides = []
        for i, s in enumerate(p.slides, 1):
            inner = self._bg(s) + "".join(self._shape(x) for x in s.get("shapes", [])) \
                + "".join(self._text(t) for t in s.get("texts", []))
            label = html.escape(f'{s.get("page", i):02d} {s.get("section", "")}')
            slides.append(f'<section class="slide" data-page="{s.get("page", i)}" data-label="{label}">{inner}</section>')
        meta = {"title": p.title, "style": p.style_id, "width": p.width, "height": p.height,
                "safe_margin": p.style.get("grid", {}).get("safe_margin", 40)}
        doc = TEMPLATE.replace("__TITLE__", html.escape(p.title)) \
            .replace("__W__", str(p.width)).replace("__H__", str(p.height)) \
            .replace("__META__", json.dumps(meta, ensure_ascii=False)) \
            .replace("__SLIDES__", "\n".join(slides))
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.out.write_text(doc, encoding="utf-8")
        return self.out


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
  html,body{margin:0;height:100%;background:#111;overflow:hidden}
  #stage{position:absolute;left:50%;top:50%;width:__W__px;height:__H__px;transform-origin:0 0}
  .slide{position:absolute;inset:0;width:__W__px;height:__H__px;overflow:hidden;background:#fff;
         opacity:0;pointer-events:none;transition:opacity .45s ease}
  .slide.on{opacity:1;pointer-events:auto}
  .bg,.bgc,.sh,.t{position:absolute}
  .bgc{inset:0}
  .bg{object-fit:cover}
  .t{white-space:pre-wrap;word-break:normal;overflow-wrap:break-word;line-break:strict;
     -webkit-font-smoothing:antialiased;font-kerning:normal;margin:0;padding:0}
  .ph{display:flex;align-items:center;justify-content:center;border:1px dashed rgba(128,128,128,.6);
      color:rgba(128,128,128,.9);font:12px/1.4 Menlo,monospace;box-sizing:border-box}
  #pager{position:fixed;right:18px;bottom:12px;color:#888;font:12px Menlo,monospace}
  /* 总览：所有页缩略平铺，点击跳转 */
  body.overview{overflow:auto}
  body.overview #stage{position:static;transform:none!important;width:auto;height:auto;display:grid;
      grid-template-columns:repeat(4,calc(__W__px * .25));gap:14px;padding:24px;justify-content:center}
  body.overview .slide{position:relative;opacity:1;pointer-events:auto;cursor:pointer;
      transform:scale(.25);transform-origin:0 0;margin-right:calc(__W__px * -.75);margin-bottom:calc(__H__px * -.75)}
  /* print：原尺寸纵向平铺，供 Playwright 逐页截图 */
  body.print{overflow:visible;background:#fff}
  body.print #stage{position:static;transform:none!important;height:auto}
  body.print .slide{position:relative;opacity:1;transition:none}
  body.print #pager{display:none}
</style></head>
<body>
<div id="stage">
__SLIDES__
</div>
<div id="pager"></div>
<script>
window.DECK_META = __META__;
(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const stage = document.getElementById('stage'), pager = document.getElementById('pager');
  const mode = new URLSearchParams(location.search).get('mode');
  let cur = Math.max(0, Math.min(slides.length - 1, (parseInt(location.hash.slice(1)) || 1) - 1));
  const fit = () => {
    if (document.body.classList.contains('overview') || mode === 'print') return;
    // 以左上角为原点缩放，再平移半个缩放后尺寸，实现等比居中
    const s = Math.min(innerWidth / __W__, innerHeight / __H__);
    stage.style.transform = `translate(${-__W__ * s / 2}px,${-__H__ * s / 2}px) scale(${s})`;
  };
  const show = i => {
    cur = (i + slides.length) % slides.length;
    slides.forEach((el, k) => el.classList.toggle('on', k === cur));
    pager.textContent = `${cur + 1} / ${slides.length}`;
    history.replaceState(null, '', '#' + (cur + 1));
  };
  const toggleOverview = () => { document.body.classList.toggle('overview'); fit(); };
  if (mode === 'print') document.body.classList.add('print');
  if (mode === 'overview') document.body.classList.add('overview');
  addEventListener('resize', fit);
  addEventListener('keydown', e => {
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) show(cur + 1);
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) show(cur - 1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
    else if (e.key === 'Escape' || e.key === 'o') toggleOverview();
  });
  slides.forEach((el, k) => el.addEventListener('click', e => {
    if (document.body.classList.contains('overview')) { toggleOverview(); show(k); }
    else if (mode !== 'print') show(e.clientX > innerWidth / 2 ? cur + 1 : cur - 1);
  }));
  fit(); show(cur);
})();
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("-o", "--out", help="输出 HTML，默认 <plan 目录>/out/<plan 名>.html")
    a = ap.parse_args()
    plan = Plan(a.plan)
    out = Path(a.out) if a.out else plan.dir / "out" / f"{plan.path.stem}.html"
    b = HtmlDeckBuilder(plan, out)
    path = b.build()
    print(f"HTML: {path}  ({len(plan.slides)} 页)")
    if b.missing:
        print("⚠ 找不到的资源：" + ", ".join(sorted(set(b.missing))))


if __name__ == "__main__":
    main()
