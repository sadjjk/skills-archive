#!/usr/bin/env python3
"""plan.json → 可编辑 PPTX（背景图 + 形状 + 独立文本框，文字保持可编辑）。

用法：python3 build_pptx.py plan.json [-o out/deck.pptx] [--fonts mac|win|original]
  --fonts mac       写入 macOS 自带字体（Songti SC / PingFang SC / Xingkai SC，默认）
  --fonts win       写入 Windows 自带字体（SimSun / 微软雅黑 / 华文行楷）
  --fonts original  写入商业字体名（方正书宋、兰亭细黑等，需要本机已安装且有授权）
依赖：python-pptx、Pillow（pip install --user python-pptx Pillow）
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from deck_lib import Plan, font_role, is_cjk, line_spacing, pptx_font

try:
    from PIL import Image
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Pt
except ImportError as e:  # 依赖缺失时给出可执行的安装命令，而不是堆栈
    raise SystemExit(f"缺少依赖 {e.name}：pip3 install --user python-pptx Pillow")

EMU_PER_PX = 9525  # 1px = 0.75pt = 9525 EMU
ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}


def px(v: float) -> Emu:
    return Emu(int(round(v * EMU_PER_PX)))


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#")[:6].upper())


class PptxDeckBuilder:
    def __init__(self, plan: Plan, out: Path, profile: str):
        self.plan, self.out, self.profile = plan, out, profile
        self.tmp = Path(tempfile.mkdtemp(prefix="ppt-atelier-"))
        self.missing: list[str] = []
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = px(plan.width), px(plan.height)
        self.layout = self.prs.slide_layouts[6]  # 空白版式

    def _prepared_image(self, path: Path, flip: bool, gray: bool = False) -> Path:
        """PPTX 不支持直接镜像/灰度图片填充，处理后另存；webp 也统一转成兼容格式。"""
        if not flip and not gray and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            return path
        im = Image.open(path)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if gray:
            im = im.convert("L").convert("RGB")
        tag = ("-flip" if flip else "") + ("-gray" if gray else "")
        dst = self.tmp / f"{path.stem}{tag}.jpg"
        im.convert("RGB").save(dst, quality=90)
        return dst

    def _add_picture_cover(self, slide, path: Path, x, y, w, h, flip=False, focus=None, mask=None, gray=False):
        """按 object-fit:cover 语义裁剪：等比铺满目标框，按 focus 位置裁掉多余部分。
        focus 与 CSS object-position 一致，如 "30% 50%"；mask 为 circle/arch/rounded 时替换图片几何形状。"""
        path = self._prepared_image(path, flip, gray)
        iw, ih = Image.open(path).size
        pic = slide.shapes.add_picture(str(path), px(x), px(y), px(w), px(h))
        fx, fy = 0.5, 0.5
        if focus:
            parts = [float(v.rstrip("%")) / 100 for v in focus.split()]
            fx, fy = parts[0], parts[1] if len(parts) > 1 else 0.5
        box_r, img_r = w / h, iw / ih
        if img_r > box_r:  # 图更宽，裁左右
            c = 1 - box_r / img_r
            pic.crop_left, pic.crop_right = c * fx, c * (1 - fx)
        elif img_r < box_r:  # 图更高，裁上下
            c = 1 - img_r / box_r
            pic.crop_top, pic.crop_bottom = c * fy, c * (1 - fy)
        if mask:
            self._mask_picture(pic, mask, w, h)
        return pic

    @staticmethod
    def _mask_picture(pic, mask: str, w: float, h: float):
        """把图片的 prstGeom 换成椭圆/圆角矩形/上半圆拱（round2SameRect 上两角半径 = 50%）。"""
        geom = pic._element.spPr.find(qn("a:prstGeom"))
        # round2SameRect 的 adj1 以短边为基准（50000 = 短边一半）。拱形要求圆角半径 = 宽/2，
        # 竖向拱（h ≥ w）时短边就是宽，取 50000 正好是上半圆
        prst, adj = {"circle": ("ellipse", None), "rounded": ("roundRect", 12000),
                     "arch": ("round2SameRect", 50000)}[mask]
        geom.set("prst", prst)
        av = geom.find(qn("a:avLst"))
        if av is None:
            av = geom.makeelement(qn("a:avLst"), {})
            geom.append(av)
        for g in list(av):
            av.remove(g)
        if adj is not None:
            av.append(av.makeelement(qn("a:gd"), {"name": "adj1", "fmla": f"val {int(adj)}"}))

    def _background(self, slide, s: dict):
        if s.get("background_color"):
            fill = slide.background.fill
            fill.solid()
            fill.fore_color.rgb = rgb(s["background_color"])
        ref = s.get("background")
        if not ref:
            return
        p = self.plan.resolve(ref)
        if p is None:
            self.missing.append(ref)
            return
        f = {"x": 0, "y": 0, "w": self.plan.width, "h": self.plan.height, **s.get("background_frame", {})}
        pic = self._add_picture_cover(slide, p, f["x"], f["y"], f["w"], f["h"], s.get("image_horizontal_flip", False))
        pic.name = "background"

    def _shape(self, slide, sh: dict):
        kind = sh.get("type", "rect")
        if kind == "image":
            p = self.plan.resolve(sh.get("src"))
            if p is None:
                self.missing.append(sh.get("src", ""))
                return
            self._add_picture_cover(slide, p, sh["x"], sh["y"], sh["w"], sh["h"], focus=sh.get("focus"),
                                    mask=sh.get("mask"), gray=sh.get("grayscale", False))
            return
        if kind == "line":
            # 与 HTML 一致：细线按细矩形绘制，保证两端对齐像素级一致
            x1, y1, x2, y2, wpx = sh["x1"], sh["y1"], sh["x2"], sh["y2"], sh.get("width", 1)
            box = (min(x1, x2), y1 - wpx / 2, abs(x2 - x1), wpx) if y1 == y2 \
                else (x1 - wpx / 2, min(y1, y2), wpx, abs(y2 - y1))
            sh = {**sh, "x": box[0], "y": box[1], "w": max(box[2], 0.5), "h": max(box[3], 0.5),
                  "fill": sh.get("color", "#000000")}
        shape_type = MSO_SHAPE.OVAL if kind == "ellipse" else \
            MSO_SHAPE.ROUNDED_RECTANGLE if sh.get("radius") else MSO_SHAPE.RECTANGLE
        shp = slide.shapes.add_shape(shape_type, px(sh["x"]), px(sh["y"]), px(sh["w"]), px(sh["h"]))
        if sh.get("fill") and sh["fill"] != "transparent":
            shp.fill.solid()
            shp.fill.fore_color.rgb = rgb(sh["fill"])
            if sh.get("opacity", 1) < 1:
                self._set_alpha(shp.fill._xPr.find(qn("a:solidFill")), sh["opacity"])
        else:
            shp.fill.background()
        if sh.get("line"):
            shp.line.color.rgb = rgb(sh["line"])
            shp.line.width = Pt(sh.get("line_width", 1) * 0.75)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False

    @staticmethod
    def _set_alpha(solid_fill, opacity: float):
        if solid_fill is None:
            return
        clr = solid_fill[0]
        a = clr.makeelement(qn("a:alpha"), {"val": str(int(opacity * 100000))})
        clr.append(a)

    def _text(self, slide, t: dict):
        role = font_role(t.get("font", "sans-zh"))
        font_name = pptx_font(t.get("font", "sans-zh"), self.profile)
        tb = slide.shapes.add_textbox(px(t["x"]), px(t["y"]), px(t["w"]), px(t["h"]))
        tb.name = t.get("name", "text")
        if t.get("rotate"):
            tb.rotation = float(t["rotate"])  # 绕中心旋转，与 HTML transform-origin:center 一致
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = MSO_ANCHOR.TOP
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        value = t["value"].upper() if t.get("uppercase") else t["value"]
        size_pt = t.get("size", 14)
        # 行距用固定磅值（spcPts）而不是百分比：PowerPoint/WPS/Keynote 的百分比行距乘的是字体自身的单倍行高
        # （宋体约 1.4em、苹方约 1.3em），与 CSS line-height 乘字号的口径不同，多行时会撑出框外压住下方文字
        line_pt = Pt(size_pt * line_spacing(t))
        for i, line in enumerate(value.split("\n")):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.alignment = ALIGN.get(t.get("alignment", "left"), PP_ALIGN.LEFT)
            para.line_spacing = line_pt
            run = para.add_run()
            run.text = line
            f = run.font
            f.size = Pt(t.get("size", 14))
            f.color.rgb = rgb(t.get("color", "#222222"))
            f.name = font_name
            f.italic = bool(t.get("italic", role.get("italic", False)))
            f.bold = t.get("weight", role.get("weight", 400)) >= 600
            f.underline = bool(t.get("underline"))
            rPr = run._r.get_or_add_rPr()
            # 中文必须写 ea（东亚）字体，否则 PowerPoint/WPS 会回退到默认中文字体
            for tag in ("a:latin", "a:ea", "a:cs"):
                el = rPr.find(qn(tag))
                if el is None:
                    el = rPr.makeelement(qn(tag), {})
                    rPr.append(el)
                el.set("typeface", font_name)
            if t.get("charSpacing"):
                rPr.set("spc", str(int(t["charSpacing"] * 100)))  # 单位 1/100 pt
            if is_cjk(line):
                rPr.set("lang", "zh-CN")

    def build(self) -> Path:
        for s in self.plan.slides:
            slide = self.prs.slides.add_slide(self.layout)
            self._background(slide, s)
            for sh in s.get("shapes", []):
                self._shape(slide, sh)
            for t in s.get("texts", []):
                self._text(slide, t)
            if s.get("notes"):
                slide.notes_slide.notes_text_frame.text = s["notes"]
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(self.out)
        return self.out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("-o", "--out")
    ap.add_argument("--fonts", choices=["mac", "win", "original"], default="mac")
    a = ap.parse_args()
    plan = Plan(a.plan)
    out = Path(a.out) if a.out else plan.dir / "out" / f"{plan.path.stem}.pptx"
    b = PptxDeckBuilder(plan, out.resolve(), a.fonts)
    print(f"PPTX: {b.build()}  ({len(plan.slides)} 页, 字体方案 {a.fonts})")
    if b.missing:
        print("⚠ 找不到的资源：" + ", ".join(sorted(set(b.missing))))


if __name__ == "__main__":
    main()
