"""逐页设计用的页面构建器（E 及 A/B/C/D/F 样例生成脚本共用）。

每个风格样例脚本按照片明暗分区手工排版：脚本只负责「写坐标」，渲染、导出、检查仍走 make_deck.py。
Page.t() 会按「行数 × 字号 × 行距」兜底框高，避免手算高度不足导致溢出。
"""
from __future__ import annotations

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


class Page:
    """单页：背景 + 形状 + 文本。所有方法返回 self，便于链式书写。"""

    def __init__(self, no: int, section: str, background: str | None = None, bg_color: str | None = None,
                 frame: dict | None = None, flip: bool = False):
        self.no = no
        self.slide: dict = {"page": no, "section": section, "shapes": [], "texts": []}
        if background:
            self.slide["background"] = background
        if bg_color:
            self.slide["background_color"] = bg_color
        if frame:
            self.slide["background_frame"] = frame
        if flip:
            self.slide["image_horizontal_flip"] = True

    def t(self, name, value, x, y, w, h, size, font, color, align="left", **kw):
        d = {"name": name, "value": value, "x": x, "y": y, "w": w, "h": h, "size": size,
             "font": font, "color": color, "alignment": align}
        d.update(kw)
        # 框高兜底：显式行距优先，单行默认 1.15、多行默认 1.25；旋转文字的 h 是旋转前的框高，同样适用。
        # 行数同时考虑自动换行：按「框宽 ÷ 字宽」估算每段折成几行（中文按 1em、西文按 0.55em，含字距），
        # 否则长段正文只按 \n 计行会低估高度，PPT 里撑出框外压住下方文字
        size_px = size * 4 / 3
        spacing_px = kw.get("charSpacing", 0) * 4 / 3
        lines = 0
        for para in value.split("\n"):
            width = sum((size_px if ord(c) > 0x2E80 else size_px * 0.55) + spacing_px for c in para)
            lines += max(1, -(-int(width) // max(1, int(w))))
        need = lines * size_px * kw.get("lineSpacing", 1.15 if lines == 1 else 1.25) + 2
        d["h"] = max(h, round(need))
        if not kw.get("rotate") and not kw.get("bleed"):
            self._check_stack(d)
        self.slide["texts"].append(d)
        return self

    def _check_stack(self, d: dict):
        """同一栏内上下两个文本框，上方框按估算高度压到下方框就报错——在生成阶段拦住叠字。
        双向检查：新框可能在已有框的上方，也可能在下方。"""
        for u in self.slide["texts"]:
            if u.get("bleed") or u.get("rotate"):
                continue
            overlap_x = min(d["x"] + d["w"], u["x"] + u["w"]) - max(d["x"], u["x"])
            if overlap_x <= 20:
                continue
            upper, lower = (d, u) if d["y"] < u["y"] else (u, d)
            if upper["y"] < lower["y"] < upper["y"] + upper["h"] - 2:
                raise ValueError(f"P{self.no} 「{upper['name']}」估算需要到 y={upper['y'] + upper['h']}，会压住下方"
                                 f"「{lower['name']}」(y={lower['y']})：加宽 w、缩小字号、减少文字，或把下方元素下移")

    def rect(self, x, y, w, h, fill, opacity=1.0, **kw):
        self.slide["shapes"].append({"type": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "opacity": opacity, **kw})
        return self

    def ellipse(self, x, y, w, h, fill="transparent", opacity=1.0, **kw):
        self.slide["shapes"].append({"type": "ellipse", "x": x, "y": y, "w": w, "h": h, "fill": fill, "opacity": opacity, **kw})
        return self

    def line(self, x1, y1, x2, y2, color, width=1, opacity=1.0):
        self.slide["shapes"].append({"type": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                                     "color": color, "width": width, "opacity": opacity})
        return self

    def image(self, src, x, y, w, h, **kw):
        """kw：mask=circle|arch|rounded、focus="30% 50%"（裁切焦点）、grayscale=True。"""
        self.slide["shapes"].append({"type": "image", "src": src, "x": x, "y": y, "w": w, "h": h, **kw})
        return self


class Deck:
    def __init__(self, style: str, project: str, subject: str):
        self.meta = {"schema_version": 1, "style": style, "project": project, "subject": subject,
                     "canvas": {"width_px": 1280, "height_px": 720, "aspect_ratio": "16:9"}}
        self.pages: list[Page] = []

    def add(self, page: Page) -> Page:
        self.pages.append(page)
        return page

    def save(self, name: str, out_dir: str | Path | None = None) -> Path:
        """写出 plan：默认 <skill>/examples/<name>.json；用户项目传 out_dir（相对路径的照片以 plan 所在目录为基准）。"""
        out = Path(out_dir or SKILL_ROOT / "examples") / f"{name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {**self.meta, "slides": [p.slide for p in self.pages]}
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"plan: {out}  ({len(self.pages)} 页)")
        return out
