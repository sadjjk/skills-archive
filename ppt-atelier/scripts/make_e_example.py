#!/usr/bin/env python3
"""E 风格样例 v2：「栖隐 · 东方静养空间」12 页（新照片、新版式）。

一次性生成 examples/e-oriental-interior.json。版式按每张照片的明暗分区设计：
文字只落在照片暗部/平整区（亮度与纹理测量见 references/styles/e-oriental-interior.md「照片与文字区」）。
改文字直接改生成后的 JSON 即可；只有想整体换版式时才需要改本脚本重跑。
"""
from __future__ import annotations

import json
from pathlib import Path

from page_kit import Page as BasePage

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "e-oriental-interior.json"

# 配色：沿用 E 风格色板（暖金 + 米白 + 深褐）
GOLD, PAPER, PAPER2, INK, INK2, DEEP = "#E2C99C", "#F4EDE0", "#E2D6C0", "#392B20", "#60472F", "#1E1712"
HEADER_EN, HEADER_CN = "QIYIN · ORIENTAL RETREAT", "栖隐 · 东方静养空间"


class Page(BasePage):
    """E 专用：照片名省略目录与扩展名，按深浅自动设底色，并带统一页眉页脚。"""

    def __init__(self, no: int, section: str, photo: str, dark: bool, **bg):
        super().__init__(no, section, f"photos/{photo}.jpg", DEEP if dark else PAPER,
                         frame=bg.get("frame"), flip=bg.get("flip", False))
        self.dark = dark

    def image(self, src, x, y, w, h, **kw):
        return super().image(f"photos/{src}.jpg", x, y, w, h, **kw)

    def chrome(self, light_text: bool, footer=True):
        """页眉页脚全套同一基线：页眉 y=44，页脚 y=668。light_text 指浅色文字（用于深底）。"""
        c = PAPER2 if light_text else INK2
        self.t("header-en", HEADER_EN, 80, 44, 360, 18, 10, "sans-en", c, charSpacing=2)
        self.t("header-cn", HEADER_CN, 840, 43, 360, 20, 11, "sans-zh", c, "right", charSpacing=2)
        if footer:
            self.line(80, 656, 1200, 656, c, 0.5, 0.35)
            self.t("footer-cn", "城市里的一处东方隐居", 80, 668, 300, 18, 10, "serif-zh", c, charSpacing=1.5)
            self.t("page", f"{self.no:02d}", 1140, 664, 60, 24, 15, "serif-en", c, "right")
        return self


def build() -> dict:
    pages = []

    # 01 封面：庭院门洞。左右两侧暗墙，中间亮庭院——标题竖排放左侧暗墙，英文放右侧暗墙
    p = Page(1, "封面", "01-courtyard-threshold", True)
    p.rect(0, 0, 1280, 720, "#000000", 0.18).chrome(True, footer=False)
    for i, ch in enumerate("栖隐"):
        p.t(f"cover-title-{i}", ch, 96, 168 + i * 132, 130, 120, 92, "serif-zh", PAPER, "center", lineSpacing=1.0)
    p.line(250, 190, 250, 410, GOLD, 1)
    p.t("cover-subject", "东方静养空间\n品牌与空间提案", 276, 186, 260, 70, 17, "sans-zh", PAPER2, charSpacing=4, lineSpacing=1.6)
    p.t("cover-english", "A Retreat\nBeyond the Threshold", 276, 300, 300, 96, 26, "script-en", GOLD, lineSpacing=1.15)
    p.t("cover-line", "跨过一道门，\n把城市留在身后。", 1000, 488, 200, 64, 15, "sans-zh", PAPER2, "right", lineSpacing=1.7, charSpacing=1)
    p.t("cover-meta", "2026 · PROPOSAL", 1000, 600, 200, 18, 10, "sans-en", GOLD, "right", charSpacing=3)
    pages.append(p)

    # 02 序：一束光穿过门。全画面极暗，中下方一条亮光——文字放左上暗区
    p = Page(2, "序章", "02-light-doorway", True)
    p.chrome(True)
    p.t("index", "PROLOGUE · 序", 80, 150, 300, 18, 10, "sans-en", GOLD, charSpacing=3)
    p.t("heading-1", "门内一束光", 80, 186, 520, 80, 54, "serif-zh", PAPER, charSpacing=6)
    p.t("heading-2", "照见安静的开始", 82, 278, 520, 50, 30, "sans-zh", PAPER2, charSpacing=8)
    p.t("english-heading", "Where stillness begins", 84, 352, 520, 44, 26, "script-en", GOLD)
    p.line(84, 424, 144, 424, GOLD)
    p.t("body-cn", "推门之前，人还在城市的速度里；\n跨过门槛，光替你放慢了脚步。", 84, 448, 440, 64, 15, "sans-zh", PAPER2, lineSpacing=1.75)
    pages.append(p)

    # 03 目录：亚麻肌理浅底 + 右侧格窗竖图
    p = Page(3, "目录", "alt-linen", False)
    p.rect(0, 0, 1280, 720, PAPER, 0.55).image("alt-lattice-shelf", 760, 0, 520, 720).chrome(False)
    p.t("index", "CONTENTS", 80, 150, 300, 18, 10, "sans-en", INK2, charSpacing=3)
    p.t("heading-1", "目录", 80, 182, 300, 80, 56, "serif-zh", INK, charSpacing=12)
    p.t("english-heading", "Five rooms of stillness", 82, 270, 400, 40, 22, "script-en", INK2)
    items = [("壹", "入境", "THRESHOLD"), ("贰", "茶叙", "TEA"), ("叁", "器物", "OBJECTS"), ("肆", "光影", "LIGHT"), ("伍", "园林", "GARDEN")]
    for i, (no, cn, en) in enumerate(items):
        y = 352 + i * 56
        p.line(80, y, 640, y, INK2, 0.5, 0.4)
        p.t(f"toc-{i}-no", no, 80, y + 12, 50, 32, 20, "serif-zh", INK2)
        p.t(f"toc-{i}-cn", cn, 150, y + 12, 200, 32, 20, "serif-zh", INK, charSpacing=6)
        p.t(f"toc-{i}-en", en, 440, y + 18, 200, 18, 10, "sans-en", INK2, "right", charSpacing=2)
    pages.append(p)

    # 04 入境：日光茶室。上部极暗、右侧墙面平整——文字放右上
    p = Page(4, "入境", "04-sunlit-room", True)
    p.chrome(True)
    p.t("index", "01 · THRESHOLD", 760, 150, 440, 18, 10, "sans-en", GOLD, "right", charSpacing=3)
    p.t("heading-1", "一室天光", 760, 182, 440, 80, 56, "serif-zh", PAPER, "right", charSpacing=8)
    p.t("heading-2", "慢慢落在木与纸上", 760, 272, 440, 44, 26, "sans-zh", PAPER2, "right", charSpacing=5)
    p.t("english-heading", "Light, settling slowly", 760, 334, 440, 40, 24, "script-en", GOLD, "right")
    p.line(1140, 398, 1200, 398, GOLD)
    p.t("body-cn", "低窗、矮几、素墙。\n空间不说话，只让光替它说。", 820, 420, 380, 56, 15, "sans-zh", PAPER2, "right", lineSpacing=1.75)
    pages.append(p)

    # 05 茶叙：窗边茶席（中间亮、左侧暗）——左侧深色色带承载文字，照片右移
    p = Page(5, "茶叙", "03-tea-window", True, frame={"x": 440, "y": 0, "w": 840, "h": 720})
    p.chrome(True)
    p.t("index", "02 · TEA", 80, 150, 320, 18, 10, "sans-en", GOLD, charSpacing=3)
    p.t("heading-1", "一席茶叙", 74, 176, 400, 100, 66, "script-zh", PAPER)
    p.t("heading-2", "坐下来，时间就慢了", 80, 296, 340, 36, 20, "sans-zh", PAPER2, charSpacing=4)
    p.t("english-heading", "A cup of tea,\na slower hour", 82, 356, 340, 80, 24, "script-en", GOLD, lineSpacing=1.15)
    p.line(82, 462, 142, 462, GOLD)
    p.t("body-cn", "窗光落在茶席上，\n水声、杯响与呼吸，\n是这里唯一的节奏。", 82, 486, 320, 84, 14, "sans-zh", PAPER2, lineSpacing=1.75)
    pages.append(p)

    # 06 器物：陶器静物（整体极亮）——浅色页，深色文字，上方大片留白
    p = Page(6, "器物", "06-ceramic-vessels", False)
    p.chrome(False)
    p.t("index", "03 · OBJECTS", 80, 120, 320, 18, 10, "sans-en", INK2, charSpacing=3)
    p.t("heading-1", "器以载境", 80, 150, 480, 80, 56, "serif-zh", INK, charSpacing=10)
    p.t("english-heading", "Objects that hold a mood", 82, 240, 480, 36, 22, "script-en", INK2)
    p.t("body-cn", "粗陶、素釉、手作的不完美——\n让日常器物成为空间的注脚。", 700, 140, 500, 56, 15, "sans-zh", INK2, "right", lineSpacing=1.75)
    pages.append(p)

    # 07 材质：三张小图 + 标签（拼贴页，节奏变化）
    p = Page(7, "材质", "alt-linen", False)
    p.rect(0, 0, 1280, 720, PAPER, 0.62).chrome(False)
    p.t("index", "MATERIALS", 80, 120, 320, 18, 10, "sans-en", INK2, charSpacing=3)
    p.t("heading-1", "木石有温，触手知静", 80, 150, 700, 60, 40, "serif-zh", INK, charSpacing=4)
    p.t("english-heading", "The texture of tranquility", 82, 220, 520, 36, 20, "script-en", INK2)
    tiles = [("alt-lattice-shelf", "木作  TIMBER", "格窗与博古架，\n留住手作的温度。"),
             ("07-leaf-shadow", "石墙  STONE", "素石墙面，\n叶影是唯一的装饰。"),
             ("alt-linen", "织物  LINEN", "亚麻与棉麻，\n柔化光线与声音。")]
    for i, (img, label, body) in enumerate(tiles):
        x = 80 + i * 380
        p.image(img, x, 290, 360, 250)
        p.t(f"material-{i}-label", label, x, 556, 360, 22, 13, "sans-zh", INK, charSpacing=2)
        p.t(f"material-{i}-body", body, x, 586, 360, 44, 12, "sans-zh", INK2, lineSpacing=1.6)
    pages.append(p)

    # 08 香：焚香（整体暗、中右侧有烟）——文字放左侧
    p = Page(8, "闻香", "08-incense", True)
    p.chrome(True)
    p.t("index", "SCENT · 闻香", 80, 170, 320, 18, 10, "sans-en", GOLD, charSpacing=3)
    p.t("heading-lead", "一缕", 80, 214, 120, 50, 34, "sans-zh", PAPER2, charSpacing=6)
    p.t("heading-main", "香", 186, 186, 140, 120, 96, "serif-zh", PAPER)
    p.t("heading-2", "让呼吸先安静下来", 82, 338, 460, 40, 24, "sans-zh", PAPER2, charSpacing=6)
    p.t("english-heading", "Breathe in, slow down", 84, 396, 460, 40, 24, "script-en", GOLD)
    p.line(84, 462, 144, 462, GOLD)
    p.t("body-cn", "沉香、檀木与雨后的草木气，\n气味是最先抵达记忆的感官。", 84, 486, 440, 56, 15, "sans-zh", PAPER2, lineSpacing=1.75)
    pages.append(p)

    # 09 光影：叶影石墙（左右两侧偏暗、纹理弱）——全画面压暗后，居中排大字
    p = Page(9, "光影", "07-leaf-shadow", True)
    p.rect(0, 0, 1280, 720, "#2A2018", 0.45).chrome(True)
    p.t("index", "04 · LIGHT", 340, 170, 600, 18, 10, "sans-en", GOLD, "center", charSpacing=3)
    for i, ch in enumerate("光影有序"):
        p.t(f"heading-char-{i}", ch, 280 + i * 180, 206, 180, 120, 88, "serif-zh", PAPER, "center", lineSpacing=1.0)
    p.t("heading-2", "心有余地", 340, 340, 600, 44, 28, "sans-zh", PAPER2, "center", charSpacing=14)
    p.t("english-heading", "Shadows, gently arranged", 340, 400, 600, 40, 24, "script-en", GOLD, "center")
    p.t("body-cn", "不靠装饰，只让阳光与叶影在墙上变化。", 340, 470, 600, 26, 15, "sans-zh", PAPER2, "center", charSpacing=1)
    pages.append(p)

    # 10 园林：圆窗（左侧暗竹墙、右侧亮白墙）——左右分栏：左图右文，右侧浅底
    p = Page(10, "园林", "05-round-window", False)
    p.rect(640, 0, 640, 720, PAPER, 0.9).chrome(False)
    p.t("index", "05 · GARDEN", 720, 170, 480, 18, 10, "sans-en", INK2, charSpacing=3)
    p.t("heading-1", "一方圆窗", 720, 202, 480, 80, 56, "serif-zh", INK, charSpacing=8)
    p.t("heading-2", "借来满庭清意", 722, 292, 480, 44, 26, "sans-zh", INK2, charSpacing=6)
    p.t("english-heading", "A garden, borrowed by a window", 724, 354, 480, 40, 22, "script-en", INK2)
    p.line(724, 418, 784, 418, INK2)
    p.t("body-cn", "园林不必大。一扇圆窗、几竿竹影，\n就是一年四季的风景。", 724, 442, 460, 56, 15, "sans-zh", INK2, lineSpacing=1.75)
    pages.append(p)

    # 11 静坐：矮几与蒲团（上部极暗、下部亮地面）——文字放上半，左对齐
    p = Page(11, "静坐", "10-low-table", True)
    p.chrome(True)
    p.t("index", "REPOSE · 静坐", 80, 120, 320, 18, 10, "sans-en", GOLD, charSpacing=3)
    p.t("heading-1", "坐享清闲", 76, 150, 520, 100, 76, "script-zh", PAPER)
    p.t("heading-2", "一处安坐，半日无事", 82, 276, 520, 40, 24, "sans-zh", PAPER2, charSpacing=6)
    p.t("english-heading", "A little time at ease", 760, 150, 440, 40, 24, "script-en", GOLD, "right")
    p.t("body-cn", "蒲团、矮几、一盏灯。\n把手机放进木匣，\n留一段只属于自己的时间。", 760, 204, 440, 84, 15, "sans-zh", PAPER2, "right", lineSpacing=1.75)
    pages.append(p)

    # 12 结尾：暗调盆景（全暗、纹理弱）——居中行书大字
    p = Page(12, "结尾", "11-bonsai-dark", True)
    p.chrome(True)
    p.t("index", "AN INVITATION", 340, 182, 600, 18, 10, "sans-en", GOLD, "center", charSpacing=3)
    p.t("heading-1", "静候相逢", 340, 214, 600, 44, 28, "sans-zh", PAPER2, "center", charSpacing=16)
    p.t("heading-2", "栖于东方", 240, 270, 800, 130, 100, "script-zh", PAPER, "center")
    p.t("english-heading", "Your quiet moment awaits", 340, 430, 600, 40, 26, "script-en", GOLD, "center")
    p.line(610, 494, 670, 494, GOLD)
    p.t("body-cn", "暂别繁忙，来这里与安静相坐。", 340, 514, 600, 26, 15, "sans-zh", PAPER2, "center", charSpacing=2)
    p.t("contact", "QIYIN RETREAT · 预约 hello@qiyin.space", 340, 560, 600, 18, 10, "sans-en", GOLD, "center", charSpacing=2)
    pages.append(p)

    return {"schema_version": 1, "style": "e-oriental-interior", "project": "栖隐 · 东方静养空间",
            "subject": "新中式静养空间品牌与空间提案",
            "canvas": {"width_px": 1280, "height_px": 720, "aspect_ratio": "16:9"},
            "slides": [p.slide for p in pages]}


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"plan: {OUT}")
