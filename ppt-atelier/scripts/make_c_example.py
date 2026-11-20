#!/usr/bin/env python3
"""C 风格样例：「OBJECTS & SPACES · 器物与空间作品集」10 页（画廊式黑盒子）。

识别度来自：近黑画廊墙面、作品居中带细框留白（像挂在墙上）、超大极细 Didot 编号、
展签式小字信息（年份/材质/尺寸/客户）、胶片式横排缩略、一根暖金细线贯穿全套。
照片来自 Unsplash（assets/styles/c-dark-portfolio/photos/CREDITS.md）。运行后生成 examples/c-dark-portfolio.json。
"""
from page_kit import Deck, Page

BLACK, WALL, IVORY, SOFT, MUTED, RULE, GOLD = "#0A0A0A", "#111110", "#EEEAE2", "#B5AFA4", "#6E6960", "#2C2A27", "#C8A978"
PH = "photos/"
NAME = "LIN · OBJECTS & SPACES"


def label(p: Page, x, y, w, rows, align="left"):
    """展签：一组「键 — 值」小字，像画廊作品标签。"""
    for i, (k, v) in enumerate(rows):
        p.t(f"label-{i}-k", k.upper(), x, y + i * 30, 96, 14, 8, "condensed-en", MUTED, align, charSpacing=2)
        p.t(f"label-{i}-v", v, x + (0 if align == "right" else 96), y + i * 30 - 2, w - 96, 18, 11, "light-zh", SOFT, align)


def wall(p: Page, section: str):
    """画廊墙面页眉页脚：左上作者名，右上栏目，底部暖金细线 + 页码。"""
    p.t("header-name", NAME, 64, 36, 400, 14, 8.5, "condensed-en", SOFT, charSpacing=3)
    p.t("header-section", section.upper(), 816, 36, 400, 14, 8.5, "condensed-en", MUTED, "right", charSpacing=3)
    p.line(64, 668, 1216, 668, RULE, 0.75)
    p.line(64, 668, 124, 668, GOLD, 1)
    p.t("page", f"{p.no:02d}", 1156, 678, 60, 16, 10, "didot-en", SOFT, "right")


def build() -> Deck:
    d = Deck("c-dark-portfolio", "器物与空间 · 作品集", "产品与空间设计师作品集（画廊式）")

    # 01 封面：满版暗调曲面，中央极细大字「Objects」，下方中文与年份
    p = d.add(Page(1, "封面", PH + "01-dark-curves.jpg", BLACK))
    p.t("cover-kicker", "PORTFOLIO  2020 — 2026", 340, 188, 600, 16, 9, "condensed-en", GOLD, "center", charSpacing=6)
    p.t("cover-title", "Objects", 140, 214, 1000, 180, 150, "didot-en", IVORY, "center", lineSpacing=1.0, italic=True)
    p.t("cover-amp", "&  Spaces", 340, 414, 600, 60, 40, "didot-en", SOFT, "center", charSpacing=4)
    p.line(610, 494, 670, 494, GOLD, 1)
    p.t("cover-zh", "器物与空间　设计作品集", 340, 514, 600, 26, 16, "light-zh", IVORY, "center", charSpacing=10)
    p.t("cover-name", "林 默　LIN MO", 340, 600, 600, 16, 10, "condensed-en", SOFT, "center", charSpacing=6)

    # 02 自述：左侧超大引号式开场，右侧一列细宋正文；没有照片，留白即画廊墙
    p = d.add(Page(2, "自述", None, WALL))
    wall(p, "Statement")
    p.t("st-no", "00", 64, 96, 300, 200, 180, "didot-en", RULE, lineSpacing=1.0, bleed=True)
    p.t("st-kicker", "ARTIST STATEMENT", 64, 330, 400, 16, 9, "condensed-en", GOLD, charSpacing=4)
    p.t("st-title", "以克制的秩序，\n整理复杂的生活。", 64, 360, 520, 110, 34, "serif-zh", IVORY, lineSpacing=1.4, charSpacing=3)
    p.t("st-body", "我做器物，也做空间。\n\n相信一件好的东西不需要解释——它的比例、材质与光线，会替它说话。\n\n这份作品集收录 2020—2026 年间的四个项目：一套茶器、一把椅子、一盏灯，以及一间书店。", 720, 150, 440, 320, 13, "light-zh", SOFT, lineSpacing=2.0)
    p.t("st-sign", "林 默", 720, 520, 440, 30, 20, "kai-zh", IVORY)

    # 03 目录：四个项目编号 + 胶片式横排缩略图
    p = d.add(Page(3, "目录", None, WALL))
    wall(p, "Index")
    p.t("idx-title", "Index", 64, 80, 500, 100, 80, "didot-en", IVORY, italic=True, lineSpacing=1.0)
    p.t("idx-zh", "作品索引 · 四个项目", 64, 190, 500, 20, 12, "light-zh", SOFT, charSpacing=4)
    films = [("02-white-tea-set", "I", "素瓷茶器", "TEA WARE · 2024"), ("03-orange-chair", "II", "橘色单椅", "LOUNGE CHAIR · 2023"),
             ("06-lamp-shadows", "III", "影灯", "TABLE LAMP · 2022"), ("10-chairs-shelves", "IV", "椅子书店", "RETAIL SPACE · 2021")]
    for i, (img, no, cn, en) in enumerate(films):
        x = 64 + i * 292
        p.image(PH + img + ".jpg", x, 280, 268, 200, focus="50% 50%")
        p.t(f"film-{i}-no", no, x, 496, 80, 40, 30, "didot-en", GOLD, lineSpacing=1.0)
        p.t(f"film-{i}-cn", cn, x + 70, 500, 198, 26, 17, "serif-zh", IVORY, charSpacing=3)
        p.t(f"film-{i}-en", en, x + 70, 532, 198, 14, 8, "condensed-en", MUTED, charSpacing=2)

    # 04 项目 I 开篇：作品挂墙式——居中照片带 1px 细框，左侧超大极细罗马数字，右侧展签
    p = d.add(Page(4, "项目 I", None, WALL))
    wall(p, "Project I — Tea Ware")
    p.t("proj-no", "I", 60, 100, 280, 400, 380, "didot-en", RULE, lineSpacing=1.0, bleed=True)
    p.rect(359, 99, 562, 422, "transparent", line=RULE, line_width=1)
    p.image(PH + "02-white-tea-set.jpg", 360, 100, 560, 420, focus="50% 55%")
    p.t("proj-title", "素瓷茶器", 360, 548, 400, 40, 28, "serif-zh", IVORY, charSpacing=8)
    p.t("proj-en", "White Porcelain Tea Ware", 360, 596, 400, 24, 15, "didot-en", SOFT, italic=True)
    label(p, 968, 360, 248, [("Year", "2024"), ("Material", "高白瓷、竹"), ("Pieces", "壶、公道杯、杯四只"), ("Client", "白露茶事")])

    # 05 项目 I 细节：满版大图 + 左下极小展签（作品本身成为整页）
    p = d.add(Page(5, "项目 I 细节", PH + "04-ranunculus-vases.jpg", BLACK))
    p.rect(0, 520, 1280, 200, BLACK, 0.55)
    p.t("detail-kicker", "I — DETAIL", 64, 560, 300, 14, 9, "condensed-en", GOLD, charSpacing=4)
    p.t("detail-title", "器以载花", 64, 584, 400, 40, 28, "serif-zh", IVORY, charSpacing=8)
    p.t("detail-body", "同一套釉色延伸到花器，让茶席与花席成为一个画面。", 500, 594, 600, 22, 13, "light-zh", SOFT)
    p.t("page", "05", 1156, 678, 60, 16, 10, "didot-en", SOFT, "right")

    # 06 项目 II：左图右文分屏，橘色单椅照片占左 60%，右侧大段留白 + 竖排作品名
    p = d.add(Page(6, "项目 II", None, WALL))
    wall(p, "Project II — Lounge Chair")
    p.image(PH + "03-orange-chair.jpg", 0, 0, 760, 720, focus="45% 50%")
    p.t("proj-no", "II", 820, 80, 400, 240, 210, "didot-en", RULE, lineSpacing=1.0, bleed=True)
    p.t("proj-title", "橘色单椅", 820, 330, 396, 44, 30, "serif-zh", IVORY, charSpacing=8)
    p.t("proj-en", "Amber Lounge Chair", 820, 382, 396, 26, 16, "didot-en", SOFT, italic=True)
    p.line(820, 428, 880, 428, GOLD, 1)
    p.t("proj-body", "一块完整的曲面包裹身体。\n颜色取自傍晚六点的窗光。", 820, 448, 396, 50, 13, "light-zh", SOFT, lineSpacing=1.9)
    label(p, 820, 540, 396, [("Year", "2023"), ("Material", "羊毛毡、胡桃木"), ("Size", "W72 × D80 × H74 cm")])

    # 07 项目 III：极暗灯光照片满版，超大细体标题压在暗部，几乎无其它元素
    p = d.add(Page(7, "项目 III", PH + "06-lamp-shadows.jpg", BLACK))
    p.t("header-name", NAME, 64, 36, 400, 14, 8.5, "condensed-en", SOFT, charSpacing=3)
    p.t("proj-no", "III", 64, 340, 400, 200, 180, "didot-en", "#2A2723", lineSpacing=1.0, bleed=True)
    p.t("proj-title", "影灯", 64, 520, 300, 56, 40, "serif-zh", IVORY, charSpacing=14)
    p.t("proj-en", "A lamp that draws with shadow", 64, 584, 400, 24, 15, "didot-en", SOFT, italic=True)
    label(p, 968, 540, 248, [("Year", "2022"), ("Material", "黄铜、和纸"), ("Edition", "限量 30 盏")])
    p.t("page", "07", 1156, 678, 60, 16, 10, "didot-en", SOFT, "right")

    # 08 过程：三张细节图等宽排列 + 编号步骤（工作方法），统一画框
    p = d.add(Page(8, "过程", None, WALL))
    wall(p, "Process")
    p.t("proc-title", "Process", 64, 80, 500, 90, 72, "didot-en", IVORY, italic=True, lineSpacing=1.0)
    p.t("proc-zh", "从一个形状开始", 64, 176, 500, 26, 16, "light-zh", SOFT, charSpacing=6)
    steps = [("09-speckled-egg", "形", "Form", "先找一个让人想触摸的形状。"), ("08-camera-red", "光", "Light", "在暗房里看它如何被光照亮。"),
             ("05-wood-chandelier", "材", "Material", "最后才选材料，让它服务于形与光。")]
    for i, (img, zh, en, b) in enumerate(steps):
        x = 64 + i * 392
        p.rect(x - 1, 239, 362, 242, "transparent", line=RULE, line_width=1)
        p.image(PH + img + ".jpg", x, 240, 360, 240, focus="50% 50%")
        p.t(f"step-{i}-zh", zh, x, 500, 60, 50, 36, "serif-zh", GOLD, lineSpacing=1.0)
        p.t(f"step-{i}-en", en.upper(), x + 64, 508, 200, 14, 9, "condensed-en", MUTED, charSpacing=3)
        p.t(f"step-{i}-b", b, x + 64, 530, 290, 20, 12, "light-zh", SOFT)

    # 09 项目 IV + 履历：亮色空间照片放右上，左侧年表（年份 Didot 大字）
    p = d.add(Page(9, "履历", None, WALL))
    wall(p, "Project IV & CV")
    p.image(PH + "10-chairs-shelves.jpg", 720, 80, 496, 372, focus="50% 50%")
    p.t("iv-label", "IV — 椅子书店　RETAIL SPACE · 2021", 720, 468, 496, 16, 9, "condensed-en", MUTED, charSpacing=2)
    p.t("cv-title", "Chronology", 64, 80, 600, 70, 52, "didot-en", IVORY, italic=True, lineSpacing=1.0)
    cv = [("2026", "米兰设计周 · 卫星展参展"), ("2024", "「素瓷茶器」获金点设计奖"), ("2023", "成立 LIN MO STUDIO"), ("2021", "「椅子书店」空间设计落地"), ("2020", "毕业于中国美术学院 工业设计")]
    for i, (yr, ev) in enumerate(cv):
        y = 186 + i * 82
        p.t(f"cv-{i}-yr", yr, 64, y, 160, 50, 38, "didot-en", GOLD if i == 0 else SOFT, lineSpacing=1.0)
        p.t(f"cv-{i}-ev", ev, 240, y + 12, 420, 24, 15, "light-zh", IVORY, charSpacing=1)
        p.line(64, y + 64, 660, y + 64, RULE, 0.75)

    # 10 封底：吊灯照片（亮）反转成浅色页，联系信息极简居中
    p = d.add(Page(10, "封底", None, IVORY))
    p.image(PH + "07-pendant-lamp.jpg", 0, 0, 1280, 400, focus="50% 40%", grayscale=True)
    p.t("end-title", "Thank you", 340, 440, 600, 80, 60, "didot-en", BLACK, "center", italic=True, lineSpacing=1.0)
    p.t("end-zh", "作品，成为视觉中心。", 340, 532, 600, 26, 16, "light-zh", "#4A463F", "center", charSpacing=8)
    p.line(610, 580, 670, 580, GOLD, 1)
    p.t("end-contact", "MO@LINMO.STUDIO  ·  +86 138 0000 0000  ·  SHANGHAI", 240, 600, 800, 14, 9, "condensed-en", "#6E6960", "center", charSpacing=3)
    return d


if __name__ == "__main__":
    build().save("c-dark-portfolio")
