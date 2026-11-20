#!/usr/bin/env python3
"""大纲 outline.json → 完整 plan.json（自动排版：按风格的网格、字号阶梯和页型算出每个文本框坐标）。

用法：python3 compose_plan.py outline.json [-o plan.json]

outline.json 只写内容，不写坐标：
{
  "style": "f-premium-texture",
  "project": "林知夏 · 个人介绍",
  "header": {"left": "PERSONAL PROFILE", "right": "设计 · 品牌 · 空间"},   # 每页页眉（可省略）
  "footer": {"left": "林知夏", "right": "LIN ZHIXIA"},                    # 每页页脚（可省略）
  "slides": [
    {"layout": "cover", "kicker": "...", "title": "...", "subtitle": "...", "english": "...", "background": "photos/01-window-sill.jpg"},
    {"layout": "statement", ...}, {"layout": "split-image", ...}, ...
  ]
}
可用 layout 见 LAYOUTS（与 references/layouts.md 一一对应）。生成后可以直接手改 plan.json 微调坐标。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from deck_lib import load_style

W, H = 1280, 720


class Composer:
    """把一页内容拆成「页眉 + 主体版式 + 页脚」三段，主体按 layout 分派到对应方法。
    所有坐标都从 style.grid 推出，换风格只需换 style.json，不改代码。"""

    def __init__(self, outline: dict):
        self.o = outline
        self.style_id = outline["style"]
        self.s = load_style(self.style_id)
        self.pal = self.s["palette"]
        self.fonts = self.s["fonts"]
        g = self.s["grid"]
        self.mx, self.mt, self.fy = g["margin_x"], g["margin_top"], g["footer_y"]
        self.cw = W - 2 * self.mx  # 内容区宽度
        self.tone = STYLE_TONES[self.style_id]

    # ---------- 颜色：每页按 dark/light 取一组前景色 ----------
    def colors(self, dark: bool) -> dict:
        return self.tone["dark" if dark else "light"]

    def T(self, name, value, x, y, w, h, size, font, color, align="left", **kw) -> dict:
        t = {"name": name, "value": value, "x": round(x), "y": round(y), "w": round(w), "h": round(h),
             "size": size, "font": font, "color": color, "alignment": align}
        t.update({k: v for k, v in kw.items() if v is not None})
        return t

    # ---------- 页眉页脚：所有页同一基线，这是「整套页面统一」的第一条规则 ----------
    def chrome(self, slide: dict, page: int, total: int, c: dict) -> list[dict]:
        out = []
        hd, ft = self.o.get("header", {}), self.o.get("footer", {})
        f_idx = self.fonts.get("index", "sans-en")
        if slide.get("chrome", True):
            if hd.get("left"):
                out.append(self.T("header-left", hd["left"], self.mx, self.mt, 420, 18, 10, f_idx, c["muted"], charSpacing=1.5))
            if hd.get("right"):
                out.append(self.T("header-right", hd["right"], W - self.mx - 420, self.mt, 420, 18, 10, self.fonts.get("body", "sans-zh"), c["muted"], "right", charSpacing=1.5))
            if ft.get("left"):
                out.append(self.T("footer-left", ft["left"], self.mx, self.fy, 360, 18, 10, self.fonts.get("body", "sans-zh"), c["muted"], charSpacing=1))
            if ft.get("right"):
                out.append(self.T("footer-center", ft["right"], W / 2 - 180, self.fy, 360, 18, 9, f_idx, c["muted"], "center", charSpacing=1.5))
            out.append(self.T("page", f"{page:02d} / {total:02d}", W - self.mx - 120, self.fy - 1, 120, 20, 10, f_idx, c["muted"], "right", charSpacing=1))
        return out

    def rule(self, x1, y, x2, color, width=1) -> dict:
        return {"type": "line", "x1": x1, "y1": y, "x2": x2, "y2": y, "color": color, "width": width}

    def vrule(self, x, y1, y2, color, width=1) -> dict:
        return {"type": "line", "x1": x, "y1": y1, "x2": x, "y2": y2, "color": color, "width": width}

    # ======================= 版式 =======================
    def cover(self, s, c):
        """封面：大标题 + 细线 + 副标 + 英文，左对齐或居中（s.align）。"""
        center = s.get("align") == "center"
        x, w = (self.mx + 120, self.cw - 240) if center else (self.mx, 640)
        al = "center" if center else "left"
        y = s.get("y", 196)
        texts, shapes = [], []
        if s.get("kicker"):
            texts.append(self.T("kicker", s["kicker"], x, y, w, 20, 11, self.fonts.get("index", "sans-en"), c["accent"], al, charSpacing=3))
            y += 44
        title = s["title"]
        lines = title.count("\n") + 1
        size = s.get("title_size", self.tone["cover_size"])
        th = lines * size * 4 / 3 * 1.12
        texts.append(self.T("title", title, x, y, w, th, size, self.fonts["heading"], c["ink"], al, charSpacing=s.get("title_spacing", 4), lineSpacing=1.12))
        y += th + 26
        rx = x + w / 2 - 40 if center else x
        shapes.append(self.rule(rx, y, rx + 80, c["accent"], 1))
        y += 28
        if s.get("subtitle"):
            texts.append(self.T("subtitle", s["subtitle"], x, y, w, 30, 18, self.fonts.get("body", "sans-zh"), c["ink"], al, charSpacing=2))
            y += 44
        if s.get("english"):
            texts.append(self.T("english", s["english"], x, y, w, 26, 15, self.fonts.get("english", "serif-en"), c["soft"], al, italic=self.tone.get("english_italic")))
            y += 40
        if s.get("meta"):
            texts.append(self.T("meta", s["meta"], x, max(y + 30, 560), w, 20, 11, self.fonts.get("body", "sans-zh"), c["muted"], al, charSpacing=1.5))
        return texts, shapes

    def statement(self, s, c):
        """金句/观点页：英文索引 + 2 行大标题 + 正文，可选右侧竖排关键词（F 风格「身心入静」）。"""
        x = self.mx + s.get("indent", 0)
        y = s.get("y", 150)
        texts, shapes = [], []
        if s.get("index"):
            texts.append(self.T("index", s["index"], x, y, 520, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=2.5))
            y += 40
        size = s.get("title_size", self.tone["title_size"])
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.18
        texts.append(self.T("title", s["title"], x, y, 680, th, size, self.fonts["heading"], c["ink"], charSpacing=2, lineSpacing=1.18))
        y += th + 24
        if s.get("english"):
            texts.append(self.T("english", s["english"], x, y, 600, 28, 16, self.fonts.get("english", "serif-en"), c["soft"], italic=self.tone.get("english_italic")))
            y += 46
        if s.get("body"):
            bl = s["body"].count("\n") + 1
            texts.append(self.T("body", s["body"], x, y, 560, bl * 16 * 4 / 3 * 1.7, 16, self.fonts.get("body", "sans-zh"), c["soft"], lineSpacing=1.7))
        if s.get("vertical"):  # 竖排大字：每个字单独一个框，保证 PPTX 里也是真竖排
            chars = list(s["vertical"])
            vx, vy, vs = W - self.mx - 90, s.get("vertical_y", 150), 52
            for i, ch in enumerate(chars):
                texts.append(self.T(f"vertical-{i}", ch, vx, vy + i * vs * 4 / 3 * 1.15, 90, vs * 4 / 3 * 1.1, vs, self.fonts["heading"], c["ink"], "center", lineSpacing=1.0))
            shapes.append(self.vrule(vx - 24, vy + 10, vy + len(chars) * vs * 4 / 3 * 1.15 - 10, c["rule"]))
        return texts, shapes

    def split_image(self, s, c):
        """图文分栏：一侧大图（image），一侧标题+正文+要点。side=left|right 指文字所在侧。"""
        texts, shapes = [], []
        right_text = s.get("side", "left") == "right"
        img_w = s.get("image_w", 600)
        gap = 72
        if right_text:
            ix, tx = self.mx, self.mx + img_w + gap
        else:
            tx, ix = self.mx, W - self.mx - img_w
        tw = self.cw - img_w - gap
        iy, ih = s.get("image_y", 110), s.get("image_h", 500)
        shapes.append({"type": "image", "src": s.get("image", ""), "x": ix, "y": iy, "w": img_w, "h": ih})
        if s.get("caption"):
            texts.append(self.T("caption", s["caption"], ix, iy + ih + 12, img_w, 18, 10, self.fonts.get("index", "sans-en"), c["muted"], charSpacing=1.5))
        y = s.get("y", 150)
        if s.get("index"):
            texts.append(self.T("index", s["index"], tx, y, tw, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=2.5))
            y += 38
        size = s.get("title_size", self.tone["title_size"] - 6)
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.18
        texts.append(self.T("title", s["title"], tx, y, tw, th, size, self.fonts["heading"], c["ink"], charSpacing=2, lineSpacing=1.18))
        y += th + 20
        shapes.append(self.rule(tx, y, tx + 48, c["accent"]))
        y += 24
        if s.get("body"):
            bl = s["body"].count("\n") + 1
            bh = bl * 15 * 4 / 3 * 1.7
            texts.append(self.T("body", s["body"], tx, y, tw, bh, 15, self.fonts.get("body", "sans-zh"), c["soft"], lineSpacing=1.7))
            y += bh + 26
        for i, item in enumerate(s.get("points", [])):
            texts.append(self.T(f"point-{i}-no", f"{i + 1:02d}", tx, y, 40, 20, 11, self.fonts.get("index", "sans-en"), c["accent"]))
            texts.append(self.T(f"point-{i}", item, tx + 44, y - 1, tw - 44, 22, 14, self.fonts.get("body", "sans-zh"), c["ink"]))
            shapes.append(self.rule(tx, y + 32, tx + tw, c["rule"]))
            y += 46
        return texts, shapes

    def cards(self, s, c):
        """编号卡片：2-6 张，自动按 3 列/2 列排布。用于「四条规则」「六种风格」这类并列信息。"""
        texts, shapes = [], []
        y = s.get("y", 110)
        if s.get("index"):
            texts.append(self.T("index", s["index"], self.mx, y, 600, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=2.5))
            y += 36
        size = s.get("title_size", self.tone["title_size"] - 8)
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.18
        texts.append(self.T("title", s["title"], self.mx, y, 760, th, size, self.fonts["heading"], c["ink"], charSpacing=2, lineSpacing=1.18))
        y += th + 40
        items = s["items"]
        cols = s.get("cols") or (3 if len(items) in (3, 6) else 2 if len(items) in (2, 4) else min(len(items), 5))
        rows = -(-len(items) // cols)
        gap = 24
        cw = (self.cw - gap * (cols - 1)) / cols
        ch = min(170, (self.fy - 36 - y - gap * (rows - 1)) / rows)
        for i, it in enumerate(items):
            cx = self.mx + (i % cols) * (cw + gap)
            cy = y + (i // cols) * (ch + gap)
            if self.tone.get("card_fill"):
                shapes.append({"type": "rect", "x": cx, "y": cy, "w": cw, "h": ch, "fill": c.get("card", self.tone["card_fill"]), "opacity": self.tone.get("card_opacity", 1)})
            else:
                shapes.append(self.rule(cx, cy, cx + cw, c["rule"]))
            pad = 18 if self.tone.get("card_fill") else 0
            no = it.get("no", f"{i + 1:02d}")
            texts.append(self.T(f"card-{i}-no", no, cx + pad, cy + 16, 80, 34 if len(no) == 1 else 22, 24 if len(no) == 1 else 12, self.fonts.get("english", "serif-en") if len(no) == 1 else self.fonts.get("index", "sans-en"), c["accent"]))
            texts.append(self.T(f"card-{i}-title", it["title"], cx + pad, cy + 56, cw - 2 * pad, 30, 19, self.fonts["heading"], c["ink"], charSpacing=1))
            if it.get("body"):
                texts.append(self.T(f"card-{i}-body", it["body"], cx + pad, cy + 96, cw - 2 * pad, max(24, ch - 106), 12.5, self.fonts.get("body", "sans-zh"), c["soft"], lineSpacing=1.6))
        return texts, shapes

    def steps(self, s, c):
        """流程：横向 3-5 步，细线串联，编号在线上。"""
        texts, shapes = [], []
        y = s.get("y", 120)
        if s.get("index"):
            texts.append(self.T("index", s["index"], self.mx, y, 600, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=2.5))
            y += 36
        size = s.get("title_size", self.tone["title_size"] - 8)
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.18
        texts.append(self.T("title", s["title"], self.mx, y, 760, th, size, self.fonts["heading"], c["ink"], charSpacing=2, lineSpacing=1.18))
        ly = max(y + th + 90, 400)
        items = s["items"]
        n = len(items)
        sw = self.cw / n
        shapes.append(self.rule(self.mx, ly, W - self.mx, c["rule"]))
        for i, it in enumerate(items):
            sx = self.mx + i * sw
            shapes.append({"type": "rect", "x": sx, "y": ly - 4, "w": 8, "h": 8, "fill": c["accent"]})
            texts.append(self.T(f"step-{i}-no", f"{i + 1:02d}", sx, ly - 64, 80, 36, 26, self.fonts.get("english", "serif-en"), c["accent"], lineSpacing=1.0))
            texts.append(self.T(f"step-{i}-title", it["title"], sx, ly + 24, sw - 28, 30, 19, self.fonts["heading"], c["ink"], charSpacing=1))
            if it.get("body"):
                texts.append(self.T(f"step-{i}-body", it["body"], sx, ly + 64, sw - 32, 64, 12.5, self.fonts.get("body", "sans-zh"), c["soft"], lineSpacing=1.6))
        return texts, shapes

    def stats(self, s, c):
        """数据页：3-4 个大数字 + 说明，顶部 hairline（瑞士风 KPI 行）。"""
        texts, shapes = [], []
        y = s.get("y", 120)
        if s.get("index"):
            texts.append(self.T("index", s["index"], self.mx, y, 600, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=2.5))
            y += 36
        size = s.get("title_size", self.tone["title_size"] - 8)
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.18
        texts.append(self.T("title", s["title"], self.mx, y, 820, th, size, self.fonts["heading"], c["ink"], charSpacing=2, lineSpacing=1.18))
        ky = max(y + th + 80, 360)
        items = s["items"]
        kw_ = self.cw / len(items)
        shapes.append(self.rule(self.mx, ky, W - self.mx, c["ink"], 1))
        for i, it in enumerate(items):
            kx = self.mx + i * kw_
            texts.append(self.T(f"kpi-{i}-value", it["value"], kx, ky + 24, kw_ - 24, 96, self.tone.get("kpi_size", 64), self.fonts.get("kpi", self.fonts.get("english", "serif-en")), c["accent"] if i == 0 else c["ink"], lineSpacing=1.0, weight=self.tone.get("kpi_weight")))
            label_lines = it["label"].count("\n") + 1
            texts.append(self.T(f"kpi-{i}-label", it["label"], kx, ky + 130, kw_ - 32, label_lines * 13 * 4 / 3 * 1.5 + 4, 13, self.fonts.get("body", "sans-zh"), c["soft"], lineSpacing=1.5))
        return texts, shapes

    def full_image(self, s, c):
        """满版大图 + 角落标题：项目页/空间页。文字只放在 text_area 指定的暗部（默认左下）。"""
        texts, shapes = [], []
        area = s.get("text_area", "bottom-left")
        x = self.mx if "left" in area else W - self.mx - 560
        al = "left" if "left" in area else "right"
        size = s.get("title_size", self.tone["title_size"])
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.15
        body_h = (s.get("body", "").count("\n") + 1) * 15 * 4 / 3 * 1.6 if s.get("body") else 0
        block = (24 if s.get("index") else 0) + th + (40 if s.get("english") else 0) + (body_h + 16 if body_h else 0)
        y = (self.fy - 44 - block) if "bottom" in area else 150
        if s.get("index"):
            texts.append(self.T("index", s["index"], x, y, 560, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], al, charSpacing=2.5))
            y += 28
        texts.append(self.T("title", s["title"], x, y, 560, th, size, self.fonts["heading"], c["ink"], al, charSpacing=3, lineSpacing=1.15))
        y += th + 8
        if s.get("english"):
            texts.append(self.T("english", s["english"], x, y, 560, 28, 15, self.fonts.get("english", "serif-en"), c["soft"], al, italic=self.tone.get("english_italic")))
            y += 40
        if s.get("body"):
            texts.append(self.T("body", s["body"], x, y + 8, 520 if al == "left" else 560, body_h, 15, self.fonts.get("body", "sans-zh"), c["soft"], al, lineSpacing=1.6))
        return texts, shapes

    def toc(self, s, c):
        """目录：左侧大标题，右侧编号条目 + 细线，编号用英文衬线/等宽。"""
        texts, shapes = [], []
        texts.append(self.T("index", s.get("index", "CONTENTS"), self.mx, 150, 400, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], charSpacing=3))
        size = s.get("title_size", self.tone["title_size"])
        texts.append(self.T("title", s.get("title", "目录"), self.mx, 186, 400, size * 4 / 3 * 1.2, size, self.fonts["heading"], c["ink"], charSpacing=6))
        x0 = self.mx + 480
        items = s["items"]
        rh = min(78, (self.fy - 60 - 150) / len(items))
        for i, it in enumerate(items):
            y = 150 + i * rh
            shapes.append(self.rule(x0, y, W - self.mx, c["rule"]))
            texts.append(self.T(f"toc-{i}-no", f"{i + 1:02d}", x0, y + 18, 60, 28, 20, self.fonts.get("english", "serif-en"), c["accent"]))
            texts.append(self.T(f"toc-{i}-title", it["title"], x0 + 80, y + 18, 380, 30, 20, self.fonts["heading"], c["ink"], charSpacing=2))
            if it.get("en"):
                texts.append(self.T(f"toc-{i}-en", it["en"], W - self.mx - 300, y + 24, 300, 20, 10, self.fonts.get("index", "sans-en"), c["muted"], "right", charSpacing=1.5))
        return texts, shapes

    def closing(self, s, c):
        """封底：居中金句 + 联系方式。"""
        texts, shapes = [], []
        size = s.get("title_size", self.tone["title_size"])
        lines = s["title"].count("\n") + 1
        th = lines * size * 4 / 3 * 1.2
        y = (H - th) / 2 - 50
        if s.get("index"):
            texts.append(self.T("index", s["index"], W / 2 - 300, y - 46, 600, 18, 10, self.fonts.get("index", "sans-en"), c["accent"], "center", charSpacing=3))
        texts.append(self.T("title", s["title"], W / 2 - 400, y, 800, th, size, self.fonts["heading"], c["ink"], "center", charSpacing=4, lineSpacing=1.2))
        y += th + 26
        shapes.append(self.rule(W / 2 - 30, y, W / 2 + 30, c["accent"]))
        y += 28
        if s.get("english"):
            texts.append(self.T("english", s["english"], W / 2 - 400, y, 800, 28, 16, self.fonts.get("english", "serif-en"), c["soft"], "center", italic=self.tone.get("english_italic")))
            y += 48
        if s.get("contact"):
            texts.append(self.T("contact", s["contact"], W / 2 - 400, y, 800, 20, 12, self.fonts.get("body", "sans-zh"), c["muted"], "center", charSpacing=2))
        return texts, shapes

    # ======================= 组装 =======================
    def compose(self) -> dict:
        slides_in = self.o["slides"]
        total = len(slides_in)
        out = []
        for i, s in enumerate(slides_in, 1):
            layout = s["layout"]
            if layout not in LAYOUTS:
                raise SystemExit(f"第 {i} 页 layout={layout!r} 不存在，可选：{', '.join(LAYOUTS)}")
            dark = s.get("dark", self.tone["default_dark"])
            c = self.colors(dark)
            texts, shapes = getattr(self, LAYOUTS[layout])(s, c)
            slide = {"page": i, "section": s.get("section", s.get("title", "").split("\n")[0][:12]), "layout": layout,
                     "dark": dark, "background_color": c["bg"]}
            if s.get("background"):
                slide["background"] = s["background"]
            if s.get("background_frame"):
                slide["background_frame"] = s["background_frame"]
            if s.get("flip"):
                slide["image_horizontal_flip"] = True
            # 遮罩：在背景与文字之间加一层半透明色，保证文字区对比度（规则：文字避开亮部和复杂纹理）
            if s.get("scrim"):
                sc = s["scrim"]
                shapes.insert(0, {"type": "rect", "x": sc.get("x", 0), "y": sc.get("y", 0), "w": sc.get("w", W), "h": sc.get("h", H),
                                  "fill": sc.get("color", c["bg"]), "opacity": sc.get("opacity", 0.55)})
            slide["shapes"] = s.get("extra_shapes", []) + shapes
            slide["texts"] = self.chrome(s, i, total, c) + texts
            if s.get("notes"):
                slide["notes"] = s["notes"]
            out.append(slide)
        return {"schema_version": 1, "style": self.style_id, "project": self.o.get("project", ""),
                "subject": self.o.get("subject", ""), "canvas": {"width_px": W, "height_px": H, "aspect_ratio": "16:9"},
                "slides": out}


LAYOUTS = {"cover": "cover", "statement": "statement", "split-image": "split_image", "cards": "cards",
           "steps": "steps", "stats": "stats", "full-image": "full_image", "toc": "toc", "closing": "closing"}

# 每种风格的前景色组与字号阶梯。dark/light 两组色让同一风格能做深浅页面交替（规则：深浅页面有变化）
STYLE_TONES = {
    "a-editorial": {
        "default_dark": False, "cover_size": 66, "title_size": 44, "english_italic": True, "kpi_size": 60,
        "light": {"bg": "#F1EFEA", "ink": "#0A0A0B", "soft": "#3A3A3C", "muted": "#7A7670", "rule": "#C9C4BA", "accent": "#8C2F1E"},
        "dark": {"bg": "#0E0E0F", "ink": "#F1EFEA", "soft": "#C9C5BD", "muted": "#8A867F", "rule": "#3A3936", "accent": "#D9B89A"},
    },
    "b-swiss": {
        "default_dark": False, "cover_size": 72, "title_size": 44, "english_italic": False, "kpi_size": 60, "kpi_weight": 300,
        "card_fill": "#F0F0EE",
        "light": {"bg": "#FAFAF8", "ink": "#0A0A0A", "soft": "#525252", "muted": "#737373", "rule": "#D4D4D2", "accent": "#002FA7", "card": "#F0F0EE"},
        "dark": {"bg": "#002FA7", "ink": "#FFFFFF", "soft": "#D6DEF5", "muted": "#AFC0EE", "rule": "#5B7BFF", "accent": "#FFFFFF", "card": "#0B3DBA"},
    },
    "c-dark-portfolio": {
        "default_dark": True, "cover_size": 64, "title_size": 42, "english_italic": True, "kpi_size": 60,
        "dark": {"bg": "#0B0B0B", "ink": "#F2EEE7", "soft": "#BDB6AA", "muted": "#7D776E", "rule": "#3A3631", "accent": "#C8A978"},
        "light": {"bg": "#EEEBE5", "ink": "#151412", "soft": "#4A4640", "muted": "#8A847A", "rule": "#CFC9BE", "accent": "#8C6A3E"},
    },
    "d-natural-brand": {
        "default_dark": True, "cover_size": 62, "title_size": 42, "english_italic": True, "kpi_size": 60,
        "card_fill": "#E4DECF",
        "dark": {"bg": "#2F3A2A", "ink": "#F1EDE2", "soft": "#C9CDB4", "muted": "#9EA58A", "rule": "#55634A", "accent": "#C9CFA8", "card": "#3A4733"},
        "light": {"bg": "#EDE8DC", "ink": "#24301F", "soft": "#55604A", "muted": "#8A9077", "rule": "#CFC8B5", "accent": "#5E7045", "card": "#E4DECF"},
    },
    "e-oriental-interior": {
        "default_dark": True, "cover_size": 64, "title_size": 44, "english_italic": True, "kpi_size": 60,
        "dark": {"bg": "#34271B", "ink": "#F4EDE0", "soft": "#E2D6C0", "muted": "#C2AE8C", "rule": "#6A563F", "accent": "#E2C99C"},
        "light": {"bg": "#F4EDE0", "ink": "#392B20", "soft": "#514331", "muted": "#8B7458", "rule": "#D9CBB2", "accent": "#9A7646"},
    },
    "f-premium-texture": {
        "default_dark": False, "cover_size": 64, "title_size": 42, "english_italic": True, "kpi_size": 60,
        "card_fill": "#FFFFFF", "card_opacity": 0.35,
        "light": {"bg": "#E9E3D8", "ink": "#2E2721", "soft": "#5E5346", "muted": "#8E8172", "rule": "#B9AD9B", "accent": "#9C7A48", "card": "#FFFFFF"},
        "dark": {"bg": "#2A2622", "ink": "#F3EDE3", "soft": "#CFC3B1", "muted": "#A39683", "rule": "#5A5048", "accent": "#C8A978", "card": "#FFFFFF"},
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outline")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    src = Path(a.outline)
    plan = Composer(json.loads(src.read_text(encoding="utf-8"))).compose()
    out = Path(a.out) if a.out else src.with_name(src.stem.replace(".outline", "") + ".plan.json")
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"plan: {out}  ({len(plan['slides'])} 页, 风格 {plan['style']})")


if __name__ == "__main__":
    main()
