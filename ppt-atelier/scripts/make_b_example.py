#!/usr/bin/env python3
"""B 风格样例：「Q3 增长报告」10 页（瑞士国际主义平面海报）。

识别度来自：克莱因蓝整块色面、Helvetica 超细/超粗极致对比、出血超大数字、12 列网格方块裁图、
90° 旋转的侧边标签、发丝线 + 圆点编号。全部直角、无衬线、单一强调色。
照片来自 Unsplash（assets/styles/b-swiss/photos/CREDITS.md）。运行后生成 examples/b-swiss.json。
"""
from page_kit import Deck, Page

IKB, WHITE, PAPER, INK, GREY, LIGHT, RULE = "#002FA7", "#FFFFFF", "#F4F4F2", "#0A0A0A", "#6F6F6F", "#E6E6E3", "#CFCFCC"
PH = "photos/"
COL = 88  # 12 列网格：左边距 64，列宽 80 + 槽 8 → 列距 88


def gx(col: int) -> int:
    """第 col 列（0 起）的 x 坐标。"""
    return 64 + col * COL


def chrome(p: Page, label: str, dark=False):
    """顶部 meta 行：左报告名、中栏目、右页码；底部一根发丝线。所有页一致。"""
    c = WHITE if dark else INK
    g = "#AFC0EE" if dark else GREY
    p.t("header-report", "Q3 2026 GROWTH REPORT", gx(0), 32, 300, 14, 8.5, "helv-black", c, charSpacing=1.5)
    p.t("header-label", label.upper(), gx(4), 32, 300, 14, 8.5, "sans-en", g, charSpacing=1.5)
    p.t("header-page", f"{p.no:02d}/10", gx(10), 32, 168, 14, 8.5, "mono", c, "right")
    p.line(64, 54, 1216, 54, c, 0.5, 0.6)


def build() -> Deck:
    d = Deck("b-swiss", "Q3 增长报告", "季度数据汇报（瑞士国际主义）")

    # 01 封面：左 2/3 克莱因蓝满版色面 + 超大「Q3」出血；右 1/3 竖幅建筑照片；旋转侧标
    p = d.add(Page(1, "封面", None, IKB))
    p.image(PH + "04-blue-tower.jpg", 856, 0, 424, 720, focus="60% 50%")
    p.t("cover-q", "Q3", -20, 40, 900, 560, 470, "helv-black", WHITE, lineSpacing=0.9, charSpacing=-20, bleed=True)
    p.t("cover-title", "增长报告", gx(0), 520, 600, 70, 52, "bold-zh", WHITE, charSpacing=4)
    p.t("cover-sub", "用户、留存与收入的季度复盘", gx(0), 604, 600, 24, 15, "sans-zh", "#D6DEF5", charSpacing=2)
    p.t("cover-meta", "PRODUCT GROWTH TEAM  ·  2026.10", gx(0), 656, 600, 14, 9, "mono", "#AFC0EE", charSpacing=1)
    p.t("side-label", "QUARTERLY REVIEW — 2026", 650, 340, 400, 18, 10, "helv-black", WHITE, "center", charSpacing=6, rotate=90)
    p.ellipse(gx(8) + 30, 640, 16, 16, WHITE)

    # 02 核心指标：超大细体数字矩阵，第一个数字蓝色色块反白
    p = d.add(Page(2, "核心指标", None, PAPER))
    chrome(p, "01 — Key Metrics")
    p.t("title-thin", "Key", gx(0), 76, 500, 110, 92, "helv-thin", INK, lineSpacing=1.0, charSpacing=-2)
    p.t("title-bold", "Metrics", gx(0), 200, 600, 110, 92, "helv-black", INK, lineSpacing=1.0, charSpacing=-2)
    p.t("title-zh", "本季度四个核心数字", gx(7), 104, 432, 30, 20, "bold-zh", INK, "right", charSpacing=2)
    p.t("title-note", "数据截至 2026.09.30 · 环比口径", gx(7), 140, 432, 16, 10, "sans-zh", GREY, "right")
    kpi = [("128", "万", "月活跃用户", "+18% QoQ"), ("42", "%", "次月留存", "+6pt QoQ"), ("3.2", "M", "季度收入（¥）", "+71% YoY"), ("4.8", "★", "应用商店评分", "历史最高")]
    for i, (n, u, lab, delta) in enumerate(kpi):
        x = gx(i * 3)
        if i == 0:
            p.rect(x, 316, 3 * COL - 8, 340, IKB)
        c = WHITE if i == 0 else INK
        p.line(x, 316, x + 3 * COL - 8, 316, INK, 2) if i else None
        p.t(f"kpi-{i}-value", n, x + 12, 330, 3 * COL - 30, 150, 112 if len(n) <= 2 else 96, "helv-thin", c, lineSpacing=1.0, charSpacing=-4)
        p.t(f"kpi-{i}-unit", u, x + 14, 486, 120, 40, 28, "helv-black", c)
        p.t(f"kpi-{i}-label", lab, x + 14, 556, 3 * COL - 40, 24, 15, "bold-zh", c, charSpacing=1)
        p.t(f"kpi-{i}-delta", delta, x + 14, 592, 3 * COL - 40, 16, 10, "mono", "#D6DEF5" if i == 0 else IKB)

    # 03 目录：超大编号竖列，越大越细；右侧 12 列网格里放方形建筑图
    p = d.add(Page(3, "目录", None, WHITE))
    chrome(p, "Contents")
    toc = [("01", "核心指标", "Key Metrics"), ("02", "增长来源", "Growth Drivers"), ("03", "关键洞察", "Insight"),
           ("04", "留存分析", "Retention"), ("05", "下季度计划", "Q4 Plan")]
    for i, (no, cn, en) in enumerate(toc):
        y = 84 + i * 118
        p.line(gx(0), y, gx(8) - 8, y, INK, 1 if i else 2)
        p.t(f"toc-{i}-no", no, gx(0), y + 8, 160, 100, 80, "helv-thin", IKB if i == 0 else INK, lineSpacing=1.0, charSpacing=-3)
        p.t(f"toc-{i}-cn", cn, gx(2) + 20, y + 30, 300, 36, 26, "bold-zh", INK, charSpacing=2)
        p.t(f"toc-{i}-en", en.upper(), gx(2) + 20, y + 74, 300, 14, 9, "sans-en", GREY, charSpacing=2)
    p.image(PH + "01-geometric-facade.jpg", gx(8), 84, 4 * COL - 8, 4 * COL - 8, focus="50% 50%")
    p.rect(gx(8), 84 + 4 * COL, 4 * COL - 8, 586 - 4 * COL, IKB)
    p.t("toc-note", "5\nSECTIONS", gx(8) + 20, 84 + 4 * COL + 24, 300, 120, 44, "helv-black", WHITE, lineSpacing=1.0)

    # 04 增长来源：横向比例条（扁平几何图表）+ 超大百分比
    p = d.add(Page(4, "增长来源", None, PAPER))
    chrome(p, "02 — Growth Drivers")
    p.t("title", "增长来自\n三个渠道", gx(0), 76, 520, 150, 52, "bold-zh", INK, lineSpacing=1.15, charSpacing=2)
    p.t("title-en", "Where the new users came from.", gx(0), 248, 520, 24, 16, "helv-thin", GREY)
    bars = [("41", "自然搜索", "SEO 改版后搜索新增占比", IKB), ("33", "老带新", "邀请奖励上线后的推荐用户", INK), ("26", "内容合作", "12 个垂类博主合作带来", "#8A8A88")]
    y = 320
    for i, (pct, cn, note, color) in enumerate(bars):
        w = int(1152 * 0.62 * int(pct) / 41)  # 最大值 41% 对应内容区 62%，其余等比
        p.rect(gx(0), y, w, 92, color)
        p.t(f"bar-{i}-pct", pct + "%", gx(0) + 18, y + 8, 260, 80, 64, "helv-black", WHITE, lineSpacing=1.0, charSpacing=-2)
        p.t(f"bar-{i}-cn", cn, gx(0) + w + 24, y + 18, 320, 30, 22, "bold-zh", INK, charSpacing=2)
        p.t(f"bar-{i}-note", note, gx(0) + w + 24, y + 56, 320, 18, 11, "sans-zh", GREY)
        y += 108

    # 05 洞察：满版蓝 + 巨型「7」出血，右侧结论；左下方块裁图
    # 单字符 bleed 让笔画集中在中部；多字符长串（"+0.07"）会铺满页面盖住左上标题
    p = d.add(Page(5, "关键洞察", None, IKB))
    chrome(p, "03 — Insight", dark=True)
    p.t("big-7", "7", 300, -60, 640, 820, 760, "helv-black", WHITE, lineSpacing=1.0, bleed=True)
    p.t("insight-kicker", "DAY 7 IS THE MOMENT OF TRUTH", gx(0), 92, 360, 32, 11, "helv-black", WHITE, charSpacing=2, lineSpacing=1.4)
    p.t("insight-title", "第 7 天\n决定留存", gx(0), 150, 300, 150, 48, "bold-zh", WHITE, lineSpacing=1.2, charSpacing=2)
    p.image(PH + "06-concrete-corner.jpg", gx(0), 440, 3 * COL - 8, 3 * COL - 8 - 40, focus="50% 50%")
    p.t("insight-num", "3.4×", gx(9), 380, 3 * COL - 8, 100, 80, "helv-thin", WHITE, "right", lineSpacing=1.0)
    p.line(gx(9), 500, gx(12) - 8, 500, WHITE, 1)
    p.t("insight-body", "第 7 天仍活跃的用户，\n90 天留存是其他用户的 3.4 倍。", gx(9) - 40, 516, 3 * COL + 32, 50, 13, "sans-zh", "#D6DEF5", "right", lineSpacing=1.7)

    # 06 留存漏斗：阶梯式递减方块（几何漏斗），单色 + 一个蓝色缺口
    p = d.add(Page(6, "留存分析", None, WHITE))
    chrome(p, "04 — Retention")
    p.t("title", "新手引导是最大缺口", gx(0), 84, 900, 56, 40, "bold-zh", INK, charSpacing=2)
    p.t("title-en", "From sign-up to first task, 38% of users drop.", gx(0), 152, 900, 22, 15, "helv-thin", GREY)
    funnel = [("注册", 100), ("完成引导", 62), ("首次任务", 51), ("第 7 天活跃", 39), ("第 30 天活跃", 31)]
    for i, (lab, v) in enumerate(funnel):
        x = gx(i * 2 + 1) - 40
        h = int(360 * v / 100)  # 最高柱顶部数值需落在副标题下方
        top = 620 - h
        p.rect(x, top, 2 * COL - 16, h, IKB if i == 1 else (INK if i == 0 else LIGHT))
        p.t(f"f-{i}-v", f"{v}", x, top - 66, 2 * COL - 16, 60, 44, "helv-thin", IKB if i == 1 else INK, lineSpacing=1.0)
        p.t(f"f-{i}-lab", lab, x, 632, 2 * COL - 16, 20, 12, "bold-zh", INK)
    # 「−38%」标注第 1→2 柱的落差：放在第 2 柱数字上方，与第 1 柱数字不在同一栏
    top2 = 620 - int(360 * funnel[1][1] / 100)
    p.t("gap-note", "−38%", gx(3) - 40, top2 - 116, 2 * COL - 16, 40, 26, "helv-black", IKB)
    p.line(gx(0), 620, 1216, 620, INK, 1)

    # 07 对策：三张建筑方图 + 编号对策（12 列 3×4）
    p = d.add(Page(7, "对策", None, PAPER))
    chrome(p, "04 — Actions")
    p.t("title-thin", "Three", gx(0), 76, 400, 90, 72, "helv-thin", INK, lineSpacing=1.0)
    p.t("title-bold", "Fixes", gx(0), 174, 400, 90, 72, "helv-black", IKB, lineSpacing=1.0)
    p.t("title-zh", "针对新手引导的三项改动", gx(6), 120, 6 * COL - 8, 30, 20, "bold-zh", INK, "right", charSpacing=2)
    fixes = [("03-white-lowangle", "步骤减半", "引导从 6 步减到 3 步，\n去掉所有非必填项。"),
             ("08-white-stairs", "行为触发", "首日推送改为按行为触发，\n不再定时群发。"),
             ("09-round-rooftop", "进度提醒", "第 3 天加入进度提醒，\n展示还差几步完成。")]
    for i, (img, t, b) in enumerate(fixes):
        x = gx(i * 4)
        p.image(PH + img + ".jpg", x, 270, 4 * COL - 8, 230, focus="50% 50%", grayscale=(i != 1))
        p.rect(x, 270, 56, 56, IKB)
        p.t(f"fix-{i}-no", f"{i + 1}", x, 276, 56, 44, 30, "helv-black", WHITE, "center", lineSpacing=1.0)
        p.t(f"fix-{i}-title", t, x, 520, 4 * COL - 8, 30, 20, "bold-zh", INK, charSpacing=2)
        p.t(f"fix-{i}-body", b, x, 560, 4 * COL - 20, 46, 12, "sans-zh", GREY, lineSpacing=1.7)

    # 08 路线图：时间轴 + 圆点 + 月份超大细字；目标月份蓝色实心块
    p = d.add(Page(8, "Q4 计划", None, WHITE))
    chrome(p, "05 — Q4 Plan")
    p.t("title", "下季度路线图", gx(0), 84, 600, 56, 40, "bold-zh", INK, charSpacing=2)
    p.t("title-en", "Q4 2026 Roadmap", gx(0), 152, 600, 22, 15, "helv-thin", GREY)
    p.line(gx(0), 380, 1216, 380, INK, 1)
    road = [("10", "新手引导改版", "上线 A/B 实验"), ("11", "会员体系 2.0", "推出年付方案"), ("12", "海外版内测", "首批 3 个市场")]
    for i, (m, t, b) in enumerate(road):
        x = gx(i * 3)
        p.ellipse(x - 6, 374, 12, 12, INK)
        p.t(f"road-{i}-m", m, x, 230, 200, 130, 110, "helv-thin", INK, lineSpacing=1.0, charSpacing=-4)
        p.t(f"road-{i}-mlabel", "MONTH", x + 4, 214, 120, 12, 8, "mono", GREY, charSpacing=2)
        p.t(f"road-{i}-t", t, x, 404, 3 * COL - 16, 28, 18, "bold-zh", INK, charSpacing=1)
        p.t(f"road-{i}-b", b, x, 440, 3 * COL - 16, 20, 12, "sans-zh", GREY)
    p.rect(gx(9), 200, 3 * COL - 8, 440, IKB)
    p.t("goal-label", "Q4 TARGET", gx(9) + 20, 220, 200, 14, 9, "helv-black", WHITE, charSpacing=2)
    p.t("goal-1", "160万", gx(9) + 20, 260, 3 * COL - 48, 70, 54, "helv-black", WHITE, lineSpacing=1.0)
    p.t("goal-1l", "MAU 目标", gx(9) + 20, 334, 200, 20, 12, "sans-zh", "#D6DEF5")
    p.line(gx(9) + 20, 380, gx(12) - 28, 380, WHITE, 1)
    p.t("goal-2", "46%", gx(9) + 20, 400, 3 * COL - 48, 70, 54, "helv-black", WHITE, lineSpacing=1.0)
    p.t("goal-2l", "次月留存目标", gx(9) + 20, 474, 200, 20, 12, "sans-zh", "#D6DEF5")

    # 09 原则：黑底，三条原则用超大数字 + 一行陈述（海报式排列）
    p = d.add(Page(9, "原则", None, INK))
    chrome(p, "Principles", dark=True)
    p.image(PH + "07-wavy-facade.jpg", gx(8), 0, 4 * COL + 64 - 8, 720, focus="50% 50%", grayscale=True)
    rules = [("少", "Less steps", "每减少一步，转化率提升 9%"), ("早", "Earlier value", "第一分钟内让用户完成一件事"), ("准", "Right moment", "在用户需要时提醒，而不是定时")]
    for i, (zh, en, b) in enumerate(rules):
        y = 96 + i * 196
        p.t(f"rule-{i}-zh", zh, gx(0), y, 180, 170, 130, "bold-zh", IKB if i == 0 else WHITE, lineSpacing=1.0)
        p.t(f"rule-{i}-en", en.upper(), gx(2) + 20, y + 40, 400, 20, 13, "helv-black", WHITE, charSpacing=2)
        p.t(f"rule-{i}-b", b, gx(2) + 20, y + 76, 420, 22, 14, "sans-zh", "#BDBDBD")
        if i < 2:
            p.line(gx(0), y + 180, gx(7), y + 180, "#3A3A3A", 1)

    # 10 封底：满版蓝，超大「Q&A」细粗对比，联系信息左下
    p = d.add(Page(10, "结尾", None, IKB))
    p.t("end-thin", "Q&", gx(0) - 8, 120, 700, 330, 280, "helv-thin", WHITE, lineSpacing=1.0, charSpacing=-10)
    p.t("end-bold", "A", gx(6) + 10, 120, 400, 330, 280, "helv-black", WHITE, lineSpacing=1.0)
    p.line(gx(0), 500, 1216, 500, WHITE, 1)
    p.t("end-zh", "谢谢。欢迎讨论。", gx(0), 524, 600, 40, 28, "bold-zh", WHITE, charSpacing=4)
    p.t("end-contact", "GROWTH@COMPANY.COM  ·  PRODUCT GROWTH TEAM", gx(0), 590, 700, 14, 9, "mono", "#AFC0EE", charSpacing=1)
    p.t("end-page", "10/10", gx(10), 590, 168, 14, 9, "mono", WHITE, "right")
    return d


if __name__ == "__main__":
    build().save("b-swiss")
