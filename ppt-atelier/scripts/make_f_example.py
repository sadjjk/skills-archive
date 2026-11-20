#!/usr/bin/env python3
"""F 风格样例：「林知夏 · 人物专访式个人介绍」10 页（人物杂志专访）。

识别度来自：魏碑大字标题的碑刻感、楷体签名与金句、问答体排版（Q/A 大字母）、竖排姓名、
半透明毛玻璃卡片压在人像上、纸张米白 + 墨黑 + 赭石三色、纵向时间轴。
照片来自 Unsplash（assets/styles/f-premium-texture/photos/CREDITS.md）。运行后生成 examples/f-premium-texture.json。
"""
from page_kit import Deck, Page

PAPER, INK, SOFT, MUTED, RULE, OCHRE, DARK, CREAM = "#EFEAE1", "#1F1B17", "#4E463D", "#8C8174", "#C9BFAE", "#A0612F", "#1C1915", "#F5F0E7"
PH = "photos/"


def mag(p: Page, section: str, dark=False):
    """专访页眉：左「PROFILE」+ 期刊名，右栏目；页脚左姓名楷体、右页码。"""
    c = CREAM if dark else INK
    g = "#BFB4A3" if dark else MUTED
    p.t("header-mag", "PROFILE · 人物", 64, 36, 300, 14, 9, "sans-en", c, charSpacing=4)
    p.t("header-section", section, 816, 36, 400, 16, 10, "light-zh", g, "right", charSpacing=3)
    p.t("footer-name", "林知夏", 64, 670, 200, 22, 14, "kai-zh", c, charSpacing=4)
    p.t("page", f"— {p.no:02d} —", 1096, 674, 120, 16, 10, "serif-en", g, "right", charSpacing=2)


def build() -> Deck:
    d = Deck("f-premium-texture", "林知夏 · 个人介绍", "品牌与空间设计师个人介绍（人物专访式）")

    # 01 封面：满版窗边人像（左暗右亮），竖排魏碑姓名在左侧暗部，楷体签名
    p = d.add(Page(1, "封面", PH + "01-window-sill.jpg", DARK))
    p.rect(0, 0, 520, 720, DARK, 0.45)
    p.t("cover-mag", "PROFILE", 64, 60, 300, 20, 12, "serif-en", CREAM, charSpacing=10)
    for i, ch in enumerate("林知夏"):
        p.t(f"cover-name-{i}", ch, 80, 140 + i * 128, 130, 120, 96, "wei-zh", CREAM, "center", lineSpacing=1.0)
    p.line(236, 160, 236, 520, OCHRE, 1.5)
    p.t("cover-role", "\n".join("品牌与空间设计师"), 262, 160, 40, 260, 15, "light-zh", "#D8CFC0", lineSpacing=1.45)
    p.t("cover-quote", "把感受，\n做成可以被看见的秩序。", 262, 430, 260, 64, 16, "kai-zh", CREAM, lineSpacing=1.7)
    p.t("cover-sign", "Lin Zhixia", 262, 520, 260, 34, 24, "script-en", OCHRE)

    # 02 开场金句：纸张底，超大楷体引号 + 魏碑金句，右侧窄条人像
    p = d.add(Page(2, "开场", None, PAPER))
    mag(p, "开 场")
    p.image(PH + "03-hand-chin.jpg", 900, 0, 380, 720, focus="50% 40%", grayscale=True)
    p.t("q-mark", "「", 64, 90, 160, 160, 120, "kai-zh", OCHRE, lineSpacing=1.0, bleed=True)
    p.t("q-text", "好的设计不靠堆叠，\n而是让每一处留白\n都有理由。", 120, 210, 740, 230, 50, "wei-zh", INK, lineSpacing=1.45, charSpacing=4)
    p.t("q-end", "」", 720, 456, 120, 120, 90, "kai-zh", OCHRE, lineSpacing=1.0, bleed=True)
    p.line(124, 580, 184, 580, INK, 1)
    p.t("q-by", "林知夏，于上海工作室", 124, 596, 500, 22, 13, "light-zh", MUTED, charSpacing=3)

    # 03 档案卡：毛玻璃卡片压在人像上，像杂志人物档案（基本信息表）
    p = d.add(Page(3, "档案", PH + "04-long-hair.jpg", DARK, flip=True))
    mag(p, "人 物 档 案", dark=True)
    p.rect(640, 120, 520, 480, "#FFFFFF", 0.16, radius=6)
    p.rect(640, 120, 520, 480, "transparent", line="#FFFFFF", line_width=0.75, radius=6)
    p.t("card-title", "人物档案", 680, 152, 440, 50, 36, "wei-zh", CREAM, charSpacing=8)
    p.t("card-en", "FACT FILE", 680, 210, 440, 14, 9, "sans-en", "#D8CFC0", charSpacing=5)
    facts = [("姓名", "林知夏"), ("职业", "品牌与空间设计师"), ("坐标", "上海 · 杭州"), ("从业", "十年 · 60+ 项目"), ("擅长", "品牌视觉 / 空间叙事 / 内容策划")]
    for i, (k, v) in enumerate(facts):
        y = 258 + i * 62
        p.line(680, y, 1120, y, "#FFFFFF", 0.5, 0.5)
        p.t(f"fact-{i}-k", k, 680, y + 18, 100, 22, 13, "kai-zh", "#D8CFC0", charSpacing=4)
        p.t(f"fact-{i}-v", v, 790, y + 16, 330, 24, 15, "light-zh", CREAM, charSpacing=1)

    # 04 问答一：Q/A 大字母 + 魏碑问题 + 细宋回答（专访体），左侧书桌照片
    p = d.add(Page(4, "问答一", None, PAPER))
    mag(p, "对 话 · 一")
    p.image(PH + "07-table-lamp.jpg", 0, 0, 440, 720, focus="40% 50%")
    p.t("q-letter", "Q", 504, 96, 100, 110, 96, "serif-en", OCHRE, lineSpacing=1.0, italic=True)
    p.t("q-1", "为什么选择\n同时做品牌和空间？", 610, 112, 600, 110, 32, "wei-zh", INK, lineSpacing=1.35, charSpacing=2)
    p.line(504, 250, 1216, 250, RULE, 0.75)
    p.t("a-letter", "A", 504, 272, 100, 110, 96, "serif-en", INK, lineSpacing=1.0, italic=True)
    p.t("a-1", "品牌是一个人说话的方式，空间是他待客的方式。只做一样，总觉得话没说完。\n\n我更关心的是「一致」——从一张名片到一间门店，人们感受到的应该是同一种气质。", 610, 286, 560, 200, 14, "light-zh", SOFT, lineSpacing=2.0)
    p.t("a-1-pull", "只做一样，\n总觉得话没说完。", 610, 520, 560, 70, 22, "kai-zh", OCHRE, lineSpacing=1.5)

    # 05 能力：三张竖向毛玻璃卡片压在暗调散景人像上
    p = d.add(Page(5, "能力", PH + "05-silhouette-window.jpg", DARK))
    p.rect(0, 0, 1280, 720, DARK, 0.35)
    mag(p, "三 件 事", dark=True)
    p.t("cap-title", "三件事，做到足够深", 64, 92, 800, 54, 38, "wei-zh", CREAM, charSpacing=6)
    caps = [("壹", "品牌视觉", "标志、字体、色彩与版式规范，从一张名片到一整套系统。"),
            ("贰", "空间叙事", "门店与展陈的动线和氛围，让品牌在现场被感受到。"),
            ("叁", "内容策划", "图片、文案与发布节奏，让每次露面都在同一语境里。")]
    for i, (no, t, b) in enumerate(caps):
        x = 64 + i * 392
        p.rect(x, 200, 360, 400, "#FFFFFF", 0.14, radius=6)
        p.rect(x, 200, 360, 400, "transparent", line="#FFFFFF", line_width=0.75, radius=6)
        p.t(f"cap-{i}-no", no, x + 30, 228, 120, 90, 64, "kai-zh", OCHRE, lineSpacing=1.0)
        p.t(f"cap-{i}-t", t, x + 30, 340, 300, 40, 28, "wei-zh", CREAM, charSpacing=6)
        p.line(x + 30, 396, x + 70, 396, OCHRE, 1.5)
        p.t(f"cap-{i}-b", b, x + 30, 418, 300, 100, 13, "light-zh", "#D8CFC0", lineSpacing=1.95)

    # 06 时间轴：纵向时间线 + 楷体年份，右侧铅笔静物
    p = d.add(Page(6, "履历", None, PAPER))
    mag(p, "十 年")
    p.image(PH + "09-pencil-book.jpg", 760, 80, 456, 560, focus="60% 50%")
    p.t("tl-title", "十年，一条线", 64, 92, 600, 54, 38, "wei-zh", INK, charSpacing=6)
    p.t("tl-en", "A DECADE IN DESIGN", 64, 152, 600, 14, 9, "sans-en", MUTED, charSpacing=5)
    tl = [("二〇一六", "中国美术学院 视觉传达 毕业"), ("二〇一八", "加入独立品牌事务所，主导 20+ 品牌项目"), ("二〇二一", "成立林知夏设计工作室"),
          ("二〇二三", "「一盏茶」品牌获金点设计奖"), ("二〇二六", "完成第 60 个品牌与空间项目")]
    p.line(160, 210, 160, 620, INK, 1)
    for i, (yr, ev) in enumerate(tl):
        y = 210 + i * 86
        p.ellipse(154, y + 8, 12, 12, OCHRE if i == len(tl) - 1 else INK)
        p.t(f"tl-{i}-yr", yr, 40, y, 104, 28, 15, "kai-zh", OCHRE if i == len(tl) - 1 else SOFT, "right", charSpacing=1)
        p.t(f"tl-{i}-ev", ev, 190, y + 2, 520, 26, 15, "light-zh", INK, charSpacing=1)

    # 07 代表作：全宽横幅照片 + 左下项目名魏碑 + 右侧三项数据
    p = d.add(Page(7, "代表作", None, PAPER))
    mag(p, "代 表 作")
    p.image(PH + "02-bay-window.jpg", 64, 76, 1152, 360, focus="50% 45%")
    p.rect(64, 76, 220, 46, INK)
    p.t("w-label", "SELECTED WORK", 64, 90, 220, 18, 10, "sans-en", CREAM, "center", charSpacing=4)
    p.t("w-title", "一盏茶 · 城市茶空间", 64, 466, 600, 50, 34, "wei-zh", INK, charSpacing=4)
    p.t("w-body", "为城市茶空间做的品牌与门店设计。\n用纸张肌理和暖光，替代复杂装饰。", 64, 530, 540, 56, 14, "light-zh", SOFT, lineSpacing=1.9)
    for i, (n, lab) in enumerate([("18", "城市门店"), ("3", "年合作"), ("金点", "设计奖")]):
        x = 720 + i * 170
        p.line(x, 470, x, 600, RULE, 0.75)
        p.t(f"w-{i}-n", n, x + 20, 470, 150, 70, 48, "kai-zh" if not n.isdigit() else "serif-en", OCHRE, lineSpacing=1.0)
        p.t(f"w-{i}-lab", lab, x + 20, 560, 150, 22, 13, "light-zh", MUTED, charSpacing=3)

    # 08 问答二：暗底对话页，Q/A 倒置配色，右侧剪影
    p = d.add(Page(8, "问答二", None, DARK))
    mag(p, "对 话 · 二", dark=True)
    p.image(PH + "06-silhouette-cloth.jpg", 820, 0, 460, 720, focus="45% 50%", grayscale=True)
    p.t("q-letter", "Q", 64, 96, 100, 110, 96, "serif-en", OCHRE, lineSpacing=1.0, italic=True)
    p.t("q-2", "和你合作，\n会是什么样？", 170, 112, 600, 110, 32, "wei-zh", CREAM, lineSpacing=1.35, charSpacing=2)
    p.line(64, 250, 760, 250, "#4A443C", 0.75)
    p.t("a-letter", "A", 64, 272, 100, 110, 96, "serif-en", CREAM, lineSpacing=1.0, italic=True)
    flow = [("一次深谈", "明确目标与预算"), ("两套方向", "选一套深入"), ("逐页校正", "直到可以交付"), ("三月陪伴", "交付后跟进反馈")]
    for i, (t, b) in enumerate(flow):
        y = 290 + i * 76
        p.t(f"flow-{i}-no", f"0{i + 1}", 170, y, 60, 24, 16, "serif-en", OCHRE)
        p.t(f"flow-{i}-t", t, 240, y - 2, 200, 30, 20, "wei-zh", CREAM, charSpacing=4)
        p.t(f"flow-{i}-b", b, 460, y + 2, 300, 24, 14, "light-zh", "#BFB4A3")

    # 09 寄语：纸张底，居中楷体长句 + 印章式红方块
    p = d.add(Page(9, "寄语", PH + "10-pencils-card.jpg", PAPER))
    p.rect(0, 0, 1280, 720, PAPER, 0.55)
    mag(p, "寄 语")
    p.t("note-title", "写给未来的合作者", 240, 150, 800, 40, 26, "wei-zh", INK, "center", charSpacing=10)
    p.t("note-body", "如果你也相信，\n安静的东西更有力量；\n如果你愿意，\n花一点时间把一件事做对——\n我们大概会合作得很愉快。", 240, 230, 800, 260, 24, "kai-zh", SOFT, "center", lineSpacing=1.8)
    p.rect(612, 540, 56, 56, OCHRE)
    p.t("seal", "知夏", 612, 548, 56, 40, 17, "kai-zh", CREAM, "center", lineSpacing=1.1)

    # 10 封底：暗调人像（侧脸）+ 联系方式毛玻璃条
    p = d.add(Page(10, "封底", PH + "03-hand-chin.jpg", DARK))
    p.rect(0, 0, 1280, 720, DARK, 0.55)
    p.t("end-sign", "林知夏", 340, 220, 600, 120, 88, "wei-zh", CREAM, "center", charSpacing=24, lineSpacing=1.0)
    p.t("end-en", "Let's make something quiet and lasting.", 240, 360, 800, 34, 24, "script-en", OCHRE, "center")
    p.rect(340, 470, 600, 64, "#FFFFFF", 0.14, radius=32)
    p.t("end-contact", "hello@linzhixia.studio　·　微信 linzhixia", 340, 490, 600, 24, 14, "light-zh", CREAM, "center", charSpacing=2)
    return d


if __name__ == "__main__":
    build().save("f-premium-texture")
