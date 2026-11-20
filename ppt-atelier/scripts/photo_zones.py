#!/usr/bin/env python3
"""照片明暗分区：判断一张照片哪些区域适合放文字。

做法：按 16:9 cover 裁切到 1280×720，切 5 列 × 3 行网格，算每格平均亮度（0-255）和边缘强度
（Pillow FIND_EDGES 均值，越大纹理越复杂）。判定规则与 references/design-rules.md「照片与文字区」一致：
  亮度 < 70  且边缘 < 12 → 可放浅色文字（暗部）
  亮度 > 180 且边缘 < 12 → 可放深色文字（亮部）
  其余                   → 不宜直接放字（需遮罩 / 衬底 / 挪开照片）

用法：python3 photo_zones.py photo.jpg [more.jpg ...]
fetch_photos.py 也调用本模块给候选图生成放字建议。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

COLS, ROWS = 5, 3
DARK_MAX, LIGHT_MIN, EDGE_MAX = 70, 180, 12
COL_NAMES = ["左", "中左", "中", "中右", "右"]
ROW_NAMES = ["上", "中", "下"]


@dataclass
class Cell:
    row: int
    col: int
    luma: int
    edge: int

    @property
    def kind(self) -> str:
        """dark：可放浅字；light：可放深字；busy：不宜放字。"""
        if self.edge < EDGE_MAX and self.luma < DARK_MAX:
            return "dark"
        if self.edge < EDGE_MAX and self.luma > LIGHT_MIN:
            return "light"
        return "busy"


class PhotoZones:
    """一张照片的 5×3 明暗分区结果。"""

    def __init__(self, image: Image.Image):
        im = image.convert("L")
        w, h = im.size
        # 按 16:9 cover 居中裁切：与渲染器 object-fit:cover 的默认取景一致
        if w / h > 16 / 9:
            nw = int(h * 16 / 9)
            im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = int(w * 9 / 16)
            im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        im = im.resize((1280, 720))
        edges = im.filter(ImageFilter.FIND_EDGES)
        cw, ch = 1280 // COLS, 720 // ROWS
        self.cells = []
        for r in range(ROWS):
            for c in range(COLS):
                box = (c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)
                self.cells.append(Cell(r, c, int(ImageStat.Stat(im.crop(box)).mean[0]),
                                       int(ImageStat.Stat(edges.crop(box)).mean[0])))

    @classmethod
    def open(cls, path: str | Path) -> "PhotoZones":
        with Image.open(path) as im:
            return cls(im)

    def grid(self) -> str:
        """亮度/边缘 网格，每格标 ●（可放浅字）○（可放深字）·（不宜）。"""
        mark = {"dark": "●", "light": "○", "busy": "·"}
        lines = []
        for r in range(ROWS):
            row = [c for c in self.cells if c.row == r]
            lines.append("  ".join(f"{mark[c.kind]}{c.luma:3d}/{c.edge:2d}" for c in row))
        return "\n".join(lines)

    def _region(self, kind: str) -> str | None:
        """把同类格子归纳成一个方位描述，如「左」「上」「左上」。"""
        cells = [c for c in self.cells if c.kind == kind]
        if len(cells) < 2:
            return None
        cols = {c.col for c in cells}
        rows = {c.row for c in cells}
        horiz = "左" if max(cols) <= 1 else "右" if min(cols) >= 3 else "中" if cols <= {1, 2, 3} else ""
        vert = "上" if rows == {0} else "下" if rows == {2} else ""
        if not horiz and not vert:
            return "大面积" if len(cells) >= 8 else "多处"
        return (horiz + vert) or "多处"

    def summary(self) -> str:
        """一句话放字建议，如「左暗 · 浅字」「上亮 · 深字」「纹理多 · 需遮罩」。"""
        parts = []
        dark, light = self._region("dark"), self._region("light")
        if dark:
            parts.append(f"{dark}暗·浅字")
        if light:
            parts.append(f"{light}亮·深字")
        return " / ".join(parts) if parts else "纹理多·需遮罩"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for p in sys.argv[1:]:
        z = PhotoZones.open(p)
        print(f"{p}\n  建议：{z.summary()}\n  网格（●浅字 ○深字 ·不宜；亮度/边缘）：")
        print("\n".join("  " + line for line in z.grid().splitlines()))


if __name__ == "__main__":
    main()
