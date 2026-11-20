#!/usr/bin/env python3
"""D 风格样例：「NATURA 植萃 · 品牌手册」10 页（自然护理品牌手册）。

识别度来自：拱形与圆形取景框、Futura 全大写几何字 + 圆体中文、鼠尾草绿/燕麦米/陶土三色块面分割、
包装标签式信息框（细框 + 成分 + 容量）、圆形印章（品牌认证感）。
照片来自 Unsplash（assets/styles/d-natural-brand/photos/CREDITS.md）。运行后生成 examples/d-natural-brand.json。
"""
from page_kit import Deck, Page

SAGE, OAT, CLAY, FOREST, CREAM, INK, MUTED = "#8A9A7B", "#EDE6D8", "#C98B6B", "#2F3B2B", "#F7F3EA", "#2A3326", "#7B8270"
PH = "photos/"


def brand_chrome(p: Page, label: str, dark=False):
    """品牌手册页眉：左上品牌字标（Futura 宽字距），右上章节，底部章节色点 + 页码。"""
    c = CREAM if dark else INK
    p.t("header-brand", "NATURA", 64, 34, 200, 18, 11, "geo-en", c, charSpacing=8)
    p.t("header-label", label.upper(), 816, 36, 400, 14, 8.5, "geo-en", MUTED if not dark else "#C9CDB4", "right", charSpacing=3)
    p.ellipse(64, 672, 10, 10, CLAY)
    p.t("page", f"{p.no:02d}", 82, 668, 60, 18, 10, "geo-en", c, charSpacing=2)
    p.t("footer", "BRAND BOOK 2026", 1016, 668, 200, 16, 8.5, "geo-en", MUTED if not dark else "#C9CDB4", "right", charSpacing=3)


def seal(p: Page, x, y, size, color, text_top="NATURAL", text_mid="100%", text_bot="PLANT BASED"):
    """圆形印章：双环 + 三行文字（品牌认证标）。"""
    p.ellipse(x, y, size, size, "transparent", line=color, line_width=1.5)
    p.ellipse(x + 8, y + 8, size - 16, size - 16, "transparent", line=color, line_width=0.75)
    p.t("seal-top", text_top, x, y + size * 0.24, size, 14, 8, "geo-en", color, "center", charSpacing=3)
    p.t("seal-mid", text_mid, x, y + size * 0.38, size, 34, 24, "geo-en", color, "center", lineSpacing=1.0)
    p.t("seal-bot", text_bot, x, y + size * 0.68, size, 14, 7, "geo-en", color, "center", charSpacing=2)


def build() -> Deck:
    d = Deck("d-natural-brand", "NATURA 植萃 · 品牌手册", "自然护理品牌手册")

    # 01 封面：左侧燕麦米底 + 巨大 Futura 字标；右侧竖向拱形取景框装产品图；陶土色圆形点缀
    p = d.add(Page(1, "封面", None, OAT))
    p.rect(780, 0, 500, 720, SAGE)
    p.image(PH + "02-bottle-leaves.jpg", 840, 90, 380, 540, mask="arch", focus="50% 50%")
    p.ellipse(760, 520, 120, 120, CLAY)
    p.t("cover-kicker", "BRAND BOOK  ·  VOL. 01", 64, 150, 500, 16, 10, "geo-en", MUTED, charSpacing=5)
    p.t("cover-brand", "NATURA", 50, 180, 760, 170, 128, "geo-en", FOREST, lineSpacing=1.0, charSpacing=6)
    p.t("cover-zh", "植萃　自然护理", 64, 360, 500, 44, 30, "round-zh", FOREST, charSpacing=14)
    p.line(64, 430, 124, 430, CLAY, 2)
    p.t("cover-tagline", "生于森林，立于原野。", 64, 452, 500, 26, 16, "round-zh", INK, charSpacing=4)
    p.t("cover-en", "Born in the forest, rooted in the wild.", 64, 486, 500, 20, 12, "geo-en", MUTED, charSpacing=1)
    p.t("cover-meta", "BRAND TEAM  ·  2026.10", 64, 620, 400, 14, 9, "geo-en", MUTED, charSpacing=4)

    # 02 品牌故事：大圆形取景框（植物）+ 右侧故事；左下印章
    p = d.add(Page(2, "品牌故事", None, CREAM))
    brand_chrome(p, "01 — Our Story")
    p.ellipse(40, 90, 540, 540, OAT)
    p.image(PH + "05-monstera-vase.jpg", 80, 130, 460, 460, mask="circle", focus="40% 40%")
    seal(p, 470, 470, 130, CLAY)
    p.t("story-kicker", "OUR STORY", 680, 140, 500, 16, 10, "geo-en", CLAY, charSpacing=5)
    p.t("story-title", "生于森林，\n立于原野。", 680, 170, 520, 130, 46, "round-zh", FOREST, lineSpacing=1.25, charSpacing=4)
    p.t("story-body", "我们只用可追溯的植物成分。\n从种植、萃取到包装，\n每一步都尽量少打扰自然。", 680, 330, 460, 90, 15, "round-zh", INK, lineSpacing=1.9)
    p.t("story-en", "A brand that grows like a tree —\nslowly, honestly, from the root.", 680, 450, 460, 44, 13, "geo-en", MUTED, lineSpacing=1.6)

    # 03 品牌价值：三个拱形色块并排，每块一个关键词（植物 / 温和 / 可持续）
    p = d.add(Page(3, "品牌价值", None, OAT))
    brand_chrome(p, "02 — Values")
    p.t("val-title", "三个关键词", 64, 90, 600, 50, 36, "round-zh", FOREST, charSpacing=6)
    p.t("val-en", "WHAT WE STAND FOR", 64, 150, 600, 16, 10, "geo-en", MUTED, charSpacing=5)
    vals = [(SAGE, "PLANT", "植物", "核心成分 100% 植物来源，\n全部公开产地。"), (CLAY, "GENTLE", "温和", "无香精、无酒精，\n敏感肌也能安心使用。"),
            (FOREST, "CIRCULAR", "可持续", "可回收铝管与纸盒，\n空瓶回收计划。")]
    for i, (col, en, zh, b) in enumerate(vals):
        x = 64 + i * 392
        p.rect(x, 300, 360, 340, col)
        p.ellipse(x, 120, 360, 360, col)
        p.t(f"val-{i}-en", en, x, 250, 360, 20, 13, "geo-en", CREAM, "center", charSpacing=6)
        p.t(f"val-{i}-zh", zh, x, 296, 360, 70, 52, "round-zh", CREAM, "center", charSpacing=10)
        p.line(x + 160, 392, x + 200, 392, CREAM, 1)
        p.t(f"val-{i}-b", b, x + 30, 416, 300, 50, 13, "round-zh", CREAM, "center", lineSpacing=1.8)

    # 04 产品线：三个圆形产品窗 + 包装标签式信息框
    p = d.add(Page(4, "产品线", None, CREAM))
    brand_chrome(p, "03 — Product Line")
    p.t("pl-title", "三条产品线", 64, 90, 600, 50, 36, "round-zh", FOREST, charSpacing=6)
    p.t("pl-en", "PRODUCT SYSTEM", 64, 150, 600, 16, 10, "geo-en", MUTED, charSpacing=5)
    prods = [("03-amber-leaves", "01", "CLEANSE", "洁净系列", "洁面 · 卸妆油", "120 ml"),
             ("01-cream-eucalyptus", "02", "REPAIR", "修护系列", "精华 · 面霜", "50 ml"),
             ("09-oil-cloth", "03", "BODY", "身体系列", "沐浴 · 身体乳", "250 ml")]
    for i, (img, no, en, zh, items, vol) in enumerate(prods):
        x = 64 + i * 392
        p.image(PH + img + ".jpg", x + 60, 196, 240, 240, mask="circle", focus="50% 50%")
        p.rect(x, 460, 360, 170, "transparent", line=INK, line_width=1)
        p.line(x, 500, x + 360, 500, INK, 0.75)
        p.t(f"pl-{i}-no", no, x + 16, 470, 60, 20, 13, "geo-en", CLAY, charSpacing=2)
        p.t(f"pl-{i}-en", en, x + 80, 472, 264, 18, 11, "geo-en", INK, "right", charSpacing=6)
        p.t(f"pl-{i}-zh", zh, x + 16, 516, 328, 36, 24, "round-zh", FOREST, charSpacing=6)
        p.t(f"pl-{i}-items", items, x + 16, 562, 240, 20, 12, "round-zh", MUTED)
        p.t(f"pl-{i}-vol", vol, x + 240, 596, 104, 18, 11, "geo-en", INK, "right", charSpacing=2)

    # 05 场景：满版产品大片，左侧鼠尾草绿半透明竖条承托文字
    p = d.add(Page(5, "使用场景", PH + "07-skincare-stones.jpg", OAT))
    p.rect(0, 0, 460, 720, FOREST, 0.88)
    brand_chrome(p, "04 — Ritual", dark=True)
    p.t("rit-kicker", "MORNING RITUAL", 64, 190, 360, 16, 10, "geo-en", "#C9CDB4", charSpacing=5)
    p.t("rit-title", "清晨的\n三分钟", 64, 220, 360, 140, 52, "round-zh", CREAM, lineSpacing=1.2, charSpacing=6)
    p.line(64, 380, 124, 380, CLAY, 2)
    steps = [("01", "洁面", "温水 + 洁面乳"), ("02", "精华", "两滴，按压吸收"), ("03", "面霜", "薄涂，锁住水分")]
    for i, (no, t, b) in enumerate(steps):
        y = 410 + i * 64
        p.t(f"rit-{i}-no", no, 64, y, 50, 22, 14, "geo-en", CLAY, charSpacing=1)
        p.t(f"rit-{i}-t", t, 120, y - 2, 100, 26, 17, "round-zh", CREAM, charSpacing=4)
        p.t(f"rit-{i}-b", b, 220, y, 200, 22, 12, "round-zh", "#C9CDB4")

    # 06 成分：半屏植物照片 + 成分表（像包装背标），右下印章
    p = d.add(Page(6, "成分", None, OAT))
    brand_chrome(p, "05 — Ingredients")
    p.image(PH + "06-monstera-beige.jpg", 0, 0, 560, 720, focus="70% 50%")
    p.t("ing-kicker", "INGREDIENTS", 640, 100, 500, 16, 10, "geo-en", CLAY, charSpacing=5)
    p.t("ing-title", "看得懂的成分表", 640, 128, 560, 50, 36, "round-zh", FOREST, charSpacing=4)
    ings = [("龟背竹叶提取物", "MONSTERA LEAF", "舒缓"), ("尤加利精油", "EUCALYPTUS OIL", "清新"), ("燕麦 β-葡聚糖", "OAT BETA-GLUCAN", "保湿"), ("积雪草提取物", "CENTELLA ASIATICA", "修护")]
    for i, (zh, en, fn) in enumerate(ings):
        y = 220 + i * 84
        p.line(640, y, 1216, y, INK, 0.75)
        p.t(f"ing-{i}-zh", zh, 640, y + 16, 320, 28, 18, "round-zh", INK, charSpacing=2)
        p.t(f"ing-{i}-en", en, 640, y + 50, 320, 14, 9, "geo-en", MUTED, charSpacing=3)
        p.rect(1116, y + 20, 100, 34, SAGE, radius=17)
        p.t(f"ing-{i}-fn", fn, 1116, y + 26, 100, 22, 13, "round-zh", CREAM, "center", charSpacing=4)
    p.line(640, 556, 1216, 556, INK, 0.75)
    seal(p, 1086, 570, 120, FOREST, "FREE FROM", "0%", "ALCOHOL")

    # 07 数据：三个圆形色块大数字（圆是品牌符号）
    p = d.add(Page(7, "市场表现", None, CREAM))
    brand_chrome(p, "06 — Performance")
    p.t("perf-title", "上市一年", 64, 90, 600, 50, 36, "round-zh", FOREST, charSpacing=6)
    p.t("perf-en", "FIRST YEAR IN NUMBERS", 64, 150, 600, 16, 10, "geo-en", MUTED, charSpacing=5)
    nums = [(SAGE, "36", "万", "累计用户"), (CLAY, "48", "%", "复购率"), (FOREST, "4.9", "", "平均评分")]
    for i, (col, n, u, lab) in enumerate(nums):
        x = 100 + i * 380
        p.ellipse(x, 210, 320, 320, col)
        p.t(f"perf-{i}-n", n, x, 290, 320, 120, 100, "geo-en", CREAM, "center", lineSpacing=1.0)
        p.t(f"perf-{i}-u", u, x, 428, 320, 30, 20, "round-zh", CREAM, "center")
        p.t(f"perf-{i}-lab", lab, x, 556, 320, 26, 17, "round-zh", INK, "center", charSpacing=6)

    # 08 包装：横向产品大片 + 下方三栏包装规范（色卡）
    p = d.add(Page(8, "视觉系统", None, OAT))
    brand_chrome(p, "07 — Visual System")
    p.image(PH + "04-perfume-satin.jpg", 64, 80, 1152, 330, mask="rounded", radius=24, focus="50% 50%")
    p.t("vs-title", "品牌色", 64, 440, 300, 40, 28, "round-zh", FOREST, charSpacing=6)
    p.t("vs-en", "COLOR PALETTE", 64, 484, 300, 14, 9, "geo-en", MUTED, charSpacing=4)
    sw = [(SAGE, "鼠尾草绿", "SAGE  #8A9A7B"), (OAT, "燕麦米", "OAT  #EDE6D8"), (CLAY, "陶土", "CLAY  #C98B6B"), (FOREST, "森林", "FOREST  #2F3B2B")]
    for i, (c, zh, code) in enumerate(sw):
        x = 360 + i * 214
        # 燕麦米与页面底色接近，加细描边才看得出色卡边界
        extra = {"line": INK, "line_width": 0.75} if c == OAT else {}
        p.ellipse(x, 440, 90, 90, c, **extra)
        p.t(f"sw-{i}-zh", zh, x + 100, 458, 110, 22, 14, "round-zh", INK, charSpacing=2)
        p.t(f"sw-{i}-code", code, x + 100, 488, 110, 14, 8, "geo-en", MUTED, charSpacing=1)
    p.t("vs-font", "字体　Futura（英文）＋ 圆体（中文）", 64, 590, 600, 22, 13, "round-zh", INK, charSpacing=2)

    # 09 传播节奏：三个半圆拱门时间线
    p = d.add(Page(9, "传播计划", None, CREAM))
    brand_chrome(p, "08 — Campaign")
    p.t("cp-title", "下半年传播节奏", 64, 90, 600, 50, 36, "round-zh", FOREST, charSpacing=6)
    p.t("cp-en", "H2 CAMPAIGN PLAN", 64, 150, 600, 16, 10, "geo-en", MUTED, charSpacing=5)
    phases = [("JUL — AUG", "种草期", "垂类博主试用\n真实使用记录", SAGE), ("SEP — OCT", "上新期", "秋冬修护系列\n城市快闪店", CLAY), ("NOV — DEC", "沉淀期", "会员体系上线\n空瓶回收计划", FOREST)]
    for i, (m, t, b, col) in enumerate(phases):
        x = 64 + i * 392
        p.rect(x, 380, 360, 250, col)
        p.ellipse(x, 200, 360, 360, col)
        p.t(f"cp-{i}-m", m, x, 280, 360, 18, 11, "geo-en", CREAM, "center", charSpacing=4)
        p.t(f"cp-{i}-t", t, x, 320, 360, 56, 40, "round-zh", CREAM, "center", charSpacing=10)
        p.line(x + 160, 410, x + 200, 410, CREAM, 1)
        p.t(f"cp-{i}-b", b, x + 30, 436, 300, 56, 14, "round-zh", CREAM, "center", lineSpacing=1.8)

    # 10 封底：森林绿满版，大拱形产品图居中，字标与联系方式
    p = d.add(Page(10, "封底", None, FOREST))
    p.image(PH + "08-skincare-light.jpg", 470, 70, 340, 420, mask="arch", focus="40% 50%")
    p.t("end-brand", "NATURA", 340, 520, 600, 60, 44, "geo-en", CREAM, "center", charSpacing=14)
    p.t("end-zh", "一起，把森林带回家。", 340, 590, 600, 26, 16, "round-zh", "#C9CDB4", "center", charSpacing=6)
    p.t("end-contact", "BRAND@NATURA.CN", 340, 640, 600, 14, 9, "geo-en", CLAY, "center", charSpacing=5)
    return d


if __name__ == "__main__":
    build().save("d-natural-brand")
