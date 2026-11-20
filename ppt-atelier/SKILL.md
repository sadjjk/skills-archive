---
name: ppt-atelier
description: >
  有审美的 PPT 设计 Skill：六种风格鲜明的视觉基调（A 人文时尚杂志 / B 瑞士国际主义海报 /
  C 画廊式黑盒作品集 / D 自然护理品牌手册 / E 新中式室内摄影 / F 人物专访式个人介绍），
  每种都有自己的字体、版式与商业摄影。先列大纲再逐页设计，交付可编辑 PPTX + 横向翻页 HTML + 逐页预览图，
  并自动检查断行、溢出、对齐与字体。
  当用户说「$ppt-atelier」「PPT 工作室」「做一份 PPT/演示文稿/幻灯片/deck」「个人介绍 PPT」「作品集 PPT」
  「品牌汇报」「新中式方案汇报」「用风格 A-F 做」「要高级感的 PPT」时使用。
  也用于：把自己喜欢的参考图沉淀成新风格、逐页校正已有 deck、把改稿经验写回规则。
---

# ppt-atelier

把做 PPT 时反复调整的字体、留白、图位和页面节奏，写成可重复执行的规则与模板。
核心原则：**先定风格，再列大纲，再逐页设计，最后逐页检查；有效的修改写回 Skill。**

## 目录结构

```
ppt-atelier/
├── SKILL.md                  本文件：什么时候用、怎么做、交付什么
├── references/
│   ├── design-rules.md       通用设计规则：字体层级、图位与留白、网格节奏（必读）
│   ├── quality-check.md      逐页检查清单与检查脚本的判定口径（必读）
│   ├── plan-schema.md        plan.json / outline.json 字段说明（含图片 mask、文字 rotate 等）
│   ├── layouts.md            outline 自动排版的 9 种通用版式
│   ├── fonts.md              字体角色、商业字体与免费替代
│   ├── iteration.md          迭代循环：参考 → 规则 → 小样 → 校正 → 回写；如何新增风格
│   └── styles/a-…f-*.md      六种风格：五个标志、配色、字体、逐页页型、选图与禁忌（必读所选风格）
├── assets/
│   ├── fonts.json            字体角色表（HTML 字体栈 + PPTX 字体名）
│   └── styles/<id>/          style.json + photos/（Unsplash 商用实拍，photos/CREDITS.md 记来源）
├── scripts/
│   ├── make_deck.py          一键：outline/plan → plan → HTML → PPTX → 检查
│   ├── page_kit.py           逐页设计构建器（Page/Deck），风格样例脚本共用
│   ├── make_{a,b,c,d,e,f}_example.py  六种风格的样例生成脚本（每页一段注释说明版式意图）
│   ├── compose_plan.py       outline（只写内容）→ plan（通用版式自动算坐标，快速出稿用）
│   ├── build_html.py         plan → 横向翻页 HTML
│   ├── build_pptx.py         plan → 可编辑 PPTX
│   ├── check_deck.mjs        逐页截图 + 溢出/越界/安全区/重叠/孤字/字体检查 + 总览图
│   ├── fetch_photos.py       从免费可商用图库（沙沙野/Burst）搜图、出候选联系表、挑选下载并写 CREDITS
│   └── photo_zones.py        照片明暗分区：判断哪个区域可放浅字/深字（换照片前先测）
└── examples/
    ├── <风格>.json           六种风格的完整样例 plan（10-12 页，逐页设计）
    └── quick-start.outline.json  outline 写法示例（任意风格都能自动排版）
```

## 依赖

- Python 3.9+：`python-pptx`、`Pillow`（缺失时 `pip3 install --user python-pptx Pillow`）
- Node 18+ 与 Playwright Chromium（检查与预览图用）：`npm i -g playwright && npx playwright install chromium`
- 下文 `$SKILL` 指本 Skill 目录（默认 `~/.agents/skills/ppt-atelier`）

## 工作流程

严格按顺序执行，每一步完成后再进入下一步。

### 1. 明确需求（缺什么问什么，一次一个问题）

必须确定：**主题、页数、风格（A-F）、交付物**。用户已给出的直接采用，不重复确认。

- 没指定风格 → 按用途推荐一种并说明理由（对照下表），用户同意后继续
- 没指定页数 → 个人介绍 / 作品集 8-12 页，汇报 10-15 页，演讲 12-20 页
- 默认交付：可编辑 PPTX + 逐页预览图（总览 overview.png）+ HTML 演示
- 用户要 CDR：说明本 Skill 输出 PPTX，CDR 需要在 CorelDRAW 中导入 PPTX/PDF 后分层整理，并确认页面尺寸与分层要求

| 代码 | 风格 | 一眼认出它 | 适合 |
|---|---|---|---|
| A | 人文时尚杂志 | Bodoni 刊头压人像、首字下沉、巨型朱红引号、黑白摄影 | 演讲、行业观察、方法论 |
| B | 瑞士国际主义海报 | 克莱因蓝色面、出血超大数字、Helvetica 细粗对比、12 列方块图 | 数据汇报、产品发布、季度复盘 |
| C | 画廊式黑盒作品集 | 黑墙挂画式装裱、极细 Didot 水印编号、展签小字 | 设计/摄影/产品作品集 |
| D | 自然护理品牌手册 | 拱形与圆形取景、三色拱门色块、Futura 字标、圆形印章 | 品牌手册、消费品牌汇报 |
| E | 新中式室内摄影 | 暖金光影实拍、竖排大字、行书点缀、照片明暗分区排字 | 新中式空间、茶/养生/文旅 |
| F | 人物专访式个人介绍 | 魏碑标题、楷体签名、Q/A 问答体、毛玻璃卡片压人像 | 个人介绍、讲师/设计师简介 |

### 2. 读规则

开始设计前必须读：`references/design-rules.md`、`references/styles/<所选风格>.md`。
风格文档里的「五个标志」是这套风格的识别度来源，每套 deck 至少用到其中四个。
需要改字体时读 `references/fonts.md`；写 plan 时读 `references/plan-schema.md`。

### 3. 先列大纲，给用户确认

按「封面 → 目录/引子 → 主体 → 结尾」组织，逐页写：页码、页型（风格文档「页型」表中的名字）、标题、要点、配图。
标题 ≤ 2 行、每行 ≤ 10 个汉字；正文每页 ≤ 3 行或 ≤ 4 个要点。**大纲经用户确认后再设计。**

### 4. 逐页设计并生成（首选）

以所选风格的样例脚本为起点，在用户项目目录写一个生成脚本：

1. 复制 `scripts/make_<x>_example.py` 到项目目录，保留文件顶部的颜色常量、页眉页脚函数（如 `folio` / `chrome` / `wall`）
2. 按确认的大纲逐页改写：从风格页型表中挑页型，复用样例里对应页的版式代码，替换文字与照片
3. 照片：用户提供的放项目目录；没有时用 `assets/styles/<风格>/photos/` 里的图；两者都不够时，用 `fetch_photos.py` 从免费图库搜新图（用法见下）。换照片前先测明暗分区（`python3 $SKILL/scripts/photo_zones.py 图.jpg`），文字只放在暗部或平整区
4. 运行脚本生成 plan，再渲染：

```bash
python3 my_deck.py                         # 生成 my-deck.json（脚本里用 Deck.save 或自定义输出路径）
python3 $SKILL/scripts/make_deck.py my-deck.json -o out/my-deck
# 字体方案：--fonts mac（默认，macOS 自带字体）| win（Windows 自带）| original（商业字体名）
```

脚本放在 `$SKILL/scripts/` 以外时，先把该目录加入导入路径：`sys.path.insert(0, "<SKILL>/scripts")`，再 `from page_kit import Deck, Page`。

**快速出稿（次选）**：内容为主、对版式要求不高时，写 `outline.json`（参照 `examples/quick-start.outline.json`，字段见 plan-schema.md），`make_deck.py` 用 9 种通用版式自动排版。各风格的配色和字体会自动套用，但页型变化比逐页设计少。

### 5. 逐页检查与校正（不可跳过）

1. 看检查报告：`error` 必须清零；`warn` 逐条判断（装饰性越界可保留，需在交付说明中注明）
2. **打开 `check/overview.png` 和每张 `slide-NN.png` 亲眼看**，对照 `references/quality-check.md` 逐项核对：断行是否自然、文字是否压在亮部或复杂纹理上、深浅页面节奏、页眉页脚基线是否一致、风格标志是否到位
3. 发现问题 → 改生成脚本中对应元素的坐标/字号/文字 → 重新生成并渲染
4. 文字压在亮部 → 加半透明色块、换 `focus` 裁切焦点、`flip` 镜像背景或换照片
5. 刻意出血或叠压的装饰大字（水印编号、巨型引号、出血数字）加 `bleed=True`，检查脚本会跳过越界与重叠判定

### 6. 交付

交付清单：`deck.pptx`（可编辑）、`check/overview.png`（总览）、`check/slide-NN.png`（逐页预览）、`deck.html`（双击打开，←/→ 翻页，ESC 总览）。
说明中写清：使用的风格、字体方案（以及在用户电脑上缺失时的替代字体）、使用了哪些图库照片（附 CREDITS.md 来源）。

### 7. 回写 Skill（用户认可某处调整时）

把这次有效的修改沉淀下来，见 `references/iteration.md`：
- 通用规律 → `references/design-rules.md`
- 风格专属 → `references/styles/<风格>.md`、`assets/styles/<风格>/style.json`、`scripts/make_<x>_example.py`
- 通用版式算法 → `scripts/compose_plan.py` 中对应 layout 方法
- 新风格 → 按 iteration.md「新增风格」一节建目录

## 硬性规则

- 每种风格使用其风格文档规定的字体组合，不跨风格混用（例：魏碑只属于 F，Bodoni 刊头只属于 A）
- 每套 deck 页眉、页脚、页码使用同一基线与字号，不逐页变化
- 文字只放在图片的暗部或平整区域；亮部、复杂纹理上必须加遮罩或移开
- 一页只讲一件事；标题不超过 2 行
- 不交付未经检查的 deck；检查报告存在 error 时不交付
- 所有文字保持可编辑（文本框），不把文字烙进图片
- 只使用可商用来源的图片（Unsplash License、CC0 或用户自有），并在 CREDITS.md 记录来源

## 需要新照片时（fetch_photos.py）

```bash
# 1) 搜候选：ssyer 用中文、burst 用英文效果最好
python3 $SKILL/scripts/fetch_photos.py search "茶室" "tea" --source all --count 12 --orientation landscape --out ./候选
#    → 候选/candidates.jpg（带编号的联系表）+ candidates.json（明细）

# 2) 看联系表，挑出编号下载到项目 photos/（自动写 CREDITS.md）
python3 $SKILL/scripts/fetch_photos.py pick --from ./候选 --ids 3,7,12 --dest ./photos
python3 $SKILL/scripts/fetch_photos.py pick --from ./候选 --ids 3:cover,7:tea --dest ./photos   # 编号:文件名
```

- **沙沙野**：CC0，中文关键词效果好、东方题材多；免登录只能取 1200 宽预览图，适合局部用图（装裱小图/拼贴/圆形取景），不宜满版
- **Burst**：逐张核对 CC0，原图约 5000+ 宽（下载取 2400 宽）；偏欧美商业与生活方式
- 下载后跑 `photo_zones.py` 确认文字区，再改生成脚本中的 `focus`/`flip` 或文字位置
