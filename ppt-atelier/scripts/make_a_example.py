#!/usr/bin/env python3
"""A 风格样例：「NOIR 墨刊 · 第 07 期｜慢阅读的复兴」10 页（人文时尚杂志）。

识别度来自：Bodoni 刊头大字压在黑白人像上、首字下沉、双栏正文、超大引号金句、期号/页码/栏目名的杂志页面系统。
黑白摄影 + 纸白底 + 单一朱红强调色。照片来自 Unsplash（assets/styles/a-editorial/photos/CREDITS.md）。
运行后生成 examples/a-editorial.json，再用 make_deck.py 渲染。
"""
from page_kit import Deck, Page

PAPER, INK, GREY, RULE, RED = "#F3F0EA", "#111111", "#6E6A63", "#C9C3B8", "#B3261E"
WHITE = "#F7F5F0"
ISSUE = "NOIR 墨刊 · ISSUE 07 · OCTOBER 2026"
PH = "photos/"


def folio(p: Page, section: str, dark=False):
    """杂志页眉页脚：左上栏目名，右上期号；页脚左页码、右刊名。全套同一基线。"""
    c = WHITE if dark else INK
    g = "#B9B4AA" if dark else GREY
    p.t("header-section", section.upper(), 64, 34, 400, 16, 9, "condensed-en", c, charSpacing=3)
    p.t("header-issue", ISSUE, 760, 34, 456, 16, 9, "condensed-en", g, "right", charSpacing=2)
    p.line(64, 58, 1216, 58, c, 0.75, 0.5)
    p.t("page", f"{p.no:03d}", 64, 676, 80, 18, 10, "didone-en", c, charSpacing=1)
    p.t("footer-title", "NOIR · 慢阅读的复兴", 900, 678, 316, 16, 9, "sans-zh", g, "right", charSpacing=2)


def build() -> Deck:
    d = Deck("a-editorial", "NOIR 墨刊 · 慢阅读的复兴", "人文杂志式演讲：注意力与慢阅读")

    # 01 封面：满版黑白人像，Bodoni 刊头「NOIR」占据上部，封面要目沿左侧排开
    p = d.add(Page(1, "封面", PH + "01-portrait-necklace.jpg", "#1A1A1A"))
    p.rect(0, 380, 1280, 340, "#000000", 0.35)
    p.t("masthead", "NOIR", 40, 24, 1200, 230, 190, "didone-en", WHITE, "center", charSpacing=40, lineSpacing=1.0, bleed=True)
    p.t("masthead-cn", "墨 刊", 560, 238, 160, 24, 14, "display-zh", WHITE, "center", charSpacing=12)
    p.t("issue", "ISSUE 07 · OCT 2026 · ¥48", 900, 246, 316, 16, 9, "condensed-en", WHITE, "right", charSpacing=3)
    p.t("cover-kicker", "COVER STORY", 64, 400, 300, 18, 10, "condensed-en", RED, charSpacing=4)
    p.t("cover-title", "慢阅读\n的复兴", 64, 426, 420, 140, 50, "display-zh", WHITE, lineSpacing=1.12, charSpacing=4)
    p.t("cover-sub", "在信息过载的时代，\n重新学会读完一篇文章", 64, 576, 360, 52, 14, "sans-zh", "#D8D4CC", lineSpacing=1.6)
    p.t("cover-line-1", "The Slow\nReading Revival", 900, 470, 316, 90, 30, "didone-en", WHITE, "right", italic=True, lineSpacing=1.05)
    p.line(1156, 580, 1216, 580, RED, 2)
    p.t("cover-line-2", "主讲 · 周明远\n内容产品负责人", 900, 596, 316, 44, 12, "sans-zh", "#D8D4CC", "right", lineSpacing=1.6)

    # 02 编者按：左栏超大首字下沉 + 双栏正文，右侧竖幅人像
    p = d.add(Page(2, "编者按", None, PAPER))
    folio(p, "Editor's Letter")
    p.image(PH + "09-window-reader.jpg", 812, 84, 404, 560, focus="70% 50%", grayscale=True)
    p.t("caption", "图｜窗边的读者。阅读，是一种主动选择的安静。", 812, 650, 404, 16, 9, "sans-zh", GREY)
    p.t("kicker", "EDITOR'S LETTER · 编者按", 64, 92, 500, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "我们读得更多，\n却记得更少。", 64, 118, 700, 120, 44, "display-zh", INK, lineSpacing=1.18, charSpacing=2)
    p.line(64, 262, 744, 262, INK, 1)
    p.t("dropcap", "每", 60, 276, 104, 100, 72, "display-zh", RED, lineSpacing=1.0)
    p.t("col-1", "天平均接触三万四千字，能复述出来的不到百分之五。问题不在内容太少，而在注意力太碎——我们滑过了大部分文字，却很少真正读完一篇。", 170, 284, 246, 160, 12.5, "light-zh", INK, lineSpacing=1.85)
    p.t("col-1b", "这一期，我们想谈谈那些逆潮流而上的人：长读播客、纸质周刊、只发六篇文章的数字刊。", 64, 444, 352, 90, 12.5, "light-zh", INK, lineSpacing=1.85)
    p.t("col-2", "他们证明了同一件事：当阅读被重新设计，人们愿意为「读完」付费。注意力不是越来越短，而是越来越贵。\n\n本期 30 页，预计阅读时间 18 分钟。", 448, 284, 296, 250, 12.5, "light-zh", INK, lineSpacing=1.85)
    p.t("sign", "—— 主编  周明远", 448, 560, 296, 20, 12, "kai-zh", GREY, "right")

    # 03 目录：左侧超大「07」期号，右侧编号目录 + 页码，杂志式点线
    p = d.add(Page(3, "目录", None, PAPER))
    folio(p, "Contents")
    p.t("issue-no", "07", 40, 70, 520, 380, 300, "didone-en", INK, lineSpacing=1.0, bleed=True)
    p.t("contents", "CONTENTS", 70, 460, 400, 30, 22, "didone-en", INK, charSpacing=8)
    p.t("contents-cn", "本期目录 · 共五章", 70, 500, 400, 20, 12, "sans-zh", GREY, charSpacing=3)
    items = [("008", "注意力的价格", "THE PRICE OF ATTENTION"), ("016", "为「读完」付费", "PAYING TO FINISH"),
             ("024", "让人读完的四个设计", "FOUR DESIGNS"), ("032", "一次改版，完读率翻倍", "CASE STUDY"),
             ("040", "从明天开始", "WHAT TO DO")]
    for i, (pg, cn, en) in enumerate(items):
        y = 120 + i * 96
        p.t(f"toc-{i}-page", pg, 620, y, 90, 34, 26, "didone-en", RED)
        p.t(f"toc-{i}-cn", cn, 720, y + 2, 400, 32, 22, "display-zh", INK, charSpacing=2)
        p.t(f"toc-{i}-en", en, 720, y + 40, 400, 16, 9, "condensed-en", GREY, charSpacing=3)
        p.line(620, y + 72, 1216, y + 72, RULE, 0.75)

    # 04 数据：黑底大字数据跨页，Bodoni 超大数字 + 细线脚注
    p = d.add(Page(4, "数据", None, INK))
    folio(p, "In Numbers", dark=True)
    p.t("kicker", "008 · THE PRICE OF ATTENTION", 64, 92, 600, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "注意力，正在被重新定价", 64, 118, 900, 60, 36, "display-zh", WHITE, charSpacing=3)
    stats = [("8", "s", "单条内容平均停留"), ("34", "K", "每日接触字数"), ("4.7", "%", "长文完读率"), ("+62", "%", "付费长读订阅增长")]
    for i, (num, unit, label) in enumerate(stats):
        x = 64 + i * 292
        p.line(x, 250, x + 260, 250, WHITE, 0.75, 0.6)
        p.t(f"stat-{i}-num", num, x, 268, 270, 150, 118 if len(num) <= 2 else 96, "didone-en", RED if i == 3 else WHITE, lineSpacing=1.0)
        p.t(f"stat-{i}-unit", unit, x + 4, 432, 120, 40, 28, "didone-en", "#9A958C", italic=True)
        p.t(f"stat-{i}-label", label, x + 4, 482, 250, 22, 14, "sans-zh", "#D8D4CC", charSpacing=2)
    p.t("source", "数据来源：2026 中文数字阅读行为报告（样本 12,000 人）。仅为示例数据。", 64, 600, 700, 16, 9, "sans-zh", "#8A857C")

    # 05 专题跨页：左半满版黑白人像，右半标题与引言，书脊式竖排栏目名
    p = d.add(Page(5, "专题", None, PAPER))
    folio(p, "Feature")
    p.image(PH + "03-portrait-woman.jpg", 0, 0, 600, 720, focus="55% 30%", grayscale=True)
    p.t("spine", "FEATURE · 专题报道", 548, 330, 300, 22, 10, "condensed-en", WHITE, "center", charSpacing=6, rotate=-90)
    p.t("kicker", "016 · PAYING TO FINISH", 664, 120, 500, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "人们开始\n为「读完」付费", 664, 146, 552, 130, 46, "display-zh", INK, lineSpacing=1.18, charSpacing=2)
    p.t("title-en", "Finishing is the new luxury.", 664, 294, 552, 34, 22, "didone-en", GREY, italic=True)
    p.line(664, 350, 724, 350, RED, 2)
    p.t("lead", "长读播客、纸质周刊、深度订阅——\n过去三年，「慢内容」的付费用户增长了 62%。\n他们买的不是信息，而是一段不被打断的时间。", 664, 372, 520, 96, 14, "light-zh", INK, lineSpacing=1.9)
    p.t("byline", "文｜林一舟　摄影｜Unsplash", 664, 600, 520, 16, 10, "sans-zh", GREY, charSpacing=1)

    # 06 金句页：纸白底，巨型朱红引号 + 宋体大字引语（杂志 pull quote）
    p = d.add(Page(6, "金句", None, PAPER))
    folio(p, "Pull Quote")
    p.t("quote-mark", "“", 70, 70, 300, 320, 300, "didone-en", RED, lineSpacing=1.0, bleed=True)
    p.t("quote", "注意力不是越来越短，\n而是越来越贵。", 180, 236, 920, 170, 54, "display-zh", INK, lineSpacing=1.3, charSpacing=4)
    p.line(184, 460, 264, 460, INK, 1)
    p.t("quote-by", "周明远　《NOIR》第 07 期主编", 184, 480, 600, 22, 14, "kai-zh", GREY, charSpacing=2)
    p.t("quote-en", "Attention isn't getting shorter. It's getting more expensive.", 184, 520, 900, 28, 18, "didone-en", GREY, italic=True)

    # 07 方法：四栏编号，每栏顶部粗线 + Bodoni 罗马数字，像杂志「指南」栏目
    p = d.add(Page(7, "方法", None, PAPER))
    folio(p, "The Guide")
    p.t("kicker", "024 · FOUR DESIGNS", 64, 92, 500, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "让人读完的四个设计", 64, 118, 900, 60, 40, "display-zh", INK, charSpacing=3)
    guide = [("I", "可预期的长度", "开篇写明阅读时间。读者知道要花多久，才愿意开始。"),
             ("II", "清楚的结构", "小标题即目录。跳读也能抓住主线，读到一半不迷路。"),
             ("III", "节奏化的版面", "图片、引文与留白交替出现，让眼睛有地方休息。"),
             ("IV", "读完的回报", "结尾给出一句可以带走的结论，让完读本身成为收获。")]
    for i, (no, t, b) in enumerate(guide):
        x = 64 + i * 292
        p.line(x, 236, x + 264, 236, INK, 3)
        p.t(f"guide-{i}-no", no, x, 254, 200, 90, 70, "didone-en", RED, lineSpacing=1.0)
        p.t(f"guide-{i}-title", t, x, 360, 264, 30, 20, "display-zh", INK, charSpacing=2)
        p.t(f"guide-{i}-body", b, x, 404, 250, 90, 12.5, "light-zh", INK, lineSpacing=1.85)
    p.image(PH + "08-reading-magazine.jpg", 64, 520, 1152, 130, focus="50% 40%", grayscale=True)

    # 08 案例：上方横幅建筑大片，下方三栏数据 + 正文（杂志案例页）
    p = d.add(Page(8, "案例", None, PAPER))
    folio(p, "Case Study")
    p.image(PH + "07-highrise-bw.jpg", 64, 76, 1152, 300, focus="50% 30%", grayscale=True)
    p.t("img-label", "CASE STUDY", 88, 96, 300, 16, 10, "condensed-en", WHITE, charSpacing=4)
    p.t("kicker", "032 · 某周刊数字版改版", 64, 400, 500, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "一次改版，\n完读率翻倍", 64, 426, 360, 110, 38, "display-zh", INK, lineSpacing=1.2, charSpacing=2)
    p.t("body", "把信息流改回「期刊」形态：每期只发六篇，每篇标注阅读时间，结尾留一句结论。", 64, 556, 360, 70, 12.5, "light-zh", INK, lineSpacing=1.85)
    for i, (num, lab) in enumerate([("11.2%", "完读率\n改版前 4.7%"), ("×2.6", "平均阅读时长"), ("81%", "订阅续费率")]):
        x = 480 + i * 248
        p.line(x, 420, x, 620, RULE, 0.75)
        p.t(f"case-{i}-num", num, x + 24, 430, 220, 80, 56, "didone-en", RED if i == 0 else INK, lineSpacing=1.0)
        p.t(f"case-{i}-label", lab, x + 24, 530, 200, 46, 12.5, "sans-zh", GREY, lineSpacing=1.6)

    # 09 行动清单：黑白人像右侧出血 + 左侧编号清单，像杂志「三件事」
    p = d.add(Page(9, "行动", None, PAPER))
    folio(p, "What To Do")
    p.image(PH + "04-portrait-hands.jpg", 760, 0, 520, 720, focus="40% 40%", grayscale=True)
    p.t("kicker", "040 · WHAT TO DO", 64, 92, 500, 16, 10, "condensed-en", RED, charSpacing=3)
    p.t("title", "从明天开始，\n可以做的三件事", 64, 118, 640, 120, 40, "display-zh", INK, lineSpacing=1.2, charSpacing=2)
    todo = [("砍掉一半", "把更新频率降一半，把篇幅留给最好的内容。"), ("标注时长", "每篇写明阅读时间，让读者主动选择。"),
            ("设计结尾", "每篇结尾留一句值得被转述的话。")]
    for i, (t, b) in enumerate(todo):
        y = 290 + i * 112
        p.t(f"todo-{i}-no", f"0{i + 1}", 64, y, 90, 60, 46, "didone-en", RED, lineSpacing=1.0)
        p.t(f"todo-{i}-title", t, 170, y + 2, 400, 32, 22, "display-zh", INK, charSpacing=2)
        p.t(f"todo-{i}-body", b, 170, y + 44, 520, 22, 13, "light-zh", GREY)
        p.line(64, y + 88, 700, y + 88, RULE, 0.75)

    # 10 封底：满版暗调人像，刊名缩小居中，结语 + 下期预告
    p = d.add(Page(10, "封底", PH + "10-black-dress-chair.jpg", "#0B0B0B"))
    p.rect(0, 0, 1280, 720, "#000000", 0.25)
    p.t("end-mark", "NOIR", 340, 92, 600, 70, 54, "didone-en", WHITE, "center", charSpacing=24)
    p.t("end-title", "慢一点，才能读进心里。", 240, 470, 800, 60, 36, "display-zh", WHITE, "center", charSpacing=6)
    p.t("end-en", "Read slowly. Remember more.", 240, 540, 800, 30, 20, "didone-en", "#CFCAC1", "center", italic=True)
    p.line(610, 594, 670, 594, RED, 2)
    p.t("next", "NEXT ISSUE 08 ·「留白」  ·  zhou@noir-mag.cn", 240, 612, 800, 16, 10, "condensed-en", "#CFCAC1", "center", charSpacing=3)
    return d


if __name__ == "__main__":
    build().save("a-editorial")
