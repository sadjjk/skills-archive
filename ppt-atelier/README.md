# ppt-atelier

一个有审美的 PPT 设计 Skill。内置六种风格，每一种都有自己的字体组合、版式和配图，用户一眼就能分辨。工作方式是先列大纲，再逐页设计，最后逐页检查。交付物包括可编辑的 PPTX、横向翻页的 HTML 演示和逐页预览图，并会自动检查断行、文字溢出、对齐和字体。

## 六种风格

| | 风格 | 一眼认出它 | 字体 | 适合 |
|---|---|---|---|---|
| A | 人文时尚杂志 | Bodoni 刊头压在人像上、首字下沉、巨型朱红引号、黑白摄影 | Bodoni + 粗宋 / 细宋 | 演讲、行业观察、方法论 |
| B | 瑞士国际主义海报 | 克莱因蓝色面、超大数字出血、Helvetica 极细与极粗对比、12 列方块图 | Helvetica + 苹方 | 数据汇报、产品发布、季度复盘 |
| C | 画廊式黑盒作品集 | 黑墙装裱、极细 Didot 水印编号、展签小字 | Didot + 宋体 | 设计 / 摄影 / 产品作品集 |
| D | 自然护理品牌手册 | 拱形与圆形取景、三色拱门色块、Futura 字标、圆形印章 | Futura + 圆体 | 品牌手册、消费品牌汇报 |
| E | 新中式室内摄影 | 暖金光影实拍、竖排大字、行书点缀 | 宋体 + 行书 + 斜体衬线 | 新中式空间、茶 / 养生 / 文旅 |
| F | 人物专访式个人介绍 | 魏碑标题、楷体签名、Q/A 问答体、毛玻璃卡片压在人像上 | 魏碑 + 楷体 + 细宋 | 个人介绍、讲师 / 设计师简介 |

每种风格都附一套 10-12 页的完整样例（`examples/<风格>.json`），设计规则写在 `references/styles/<风格>.md`。样例照片全部来自 Unsplash，可免费商用，来源记录在各风格的 `photos/CREDITS.md`。

## 快速开始

```bash
pip3 install --user python-pptx Pillow
npm i -g playwright && npx playwright install chromium

cd ~/.agents/skills/ppt-atelier/examples
python3 ../scripts/make_deck.py f-premium-texture.json      # 渲染任一风格样例
# → out/f-premium-texture/{f-premium-texture.pptx, .html, .plan.json, check/overview.png}
python3 ../scripts/make_deck.py quick-start.outline.json    # 只写内容，自动排版
```

在 Agent 中调用：

```text
$ppt-atelier
做一份 10 页的个人介绍 PPT，使用风格 F：人物专访。
先列大纲，再逐页设计。
逐页检查断行、对齐和可读性。
交付可编辑 PPTX 与预览图。
```

## 两种出稿方式

- **逐页设计（首选）**：复制 `scripts/make_<x>_example.py`，按大纲逐页改写文字和照片。这种方式能完整保留风格的标志性版式。
- **自动排版（快速）**：写 `outline.json`，只填内容，由 `compose_plan.py` 套用 9 种通用版式排好。会自动用上所选风格的配色和字体，但页面变化较少。

```
make_<x>_example.py（逐页设计）──┐
                                 ├──▶ plan.json ──build_html──▶ deck.html ──check_deck──▶ check/*.png + report.json
outline.json（自动排版）─────────┘              └─build_pptx──▶ deck.pptx（可编辑）
```

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | Agent 工作流程：问清需求 → 读规则 → 列大纲 → 逐页设计 → 检查 → 交付 → 把有效修改写回 Skill |
| `references/` | 通用设计规则、质检清单、plan 字段说明、通用版式、字体说明、迭代方法、六份风格文档 |
| `assets/` | 字体角色表 `fonts.json`、各风格的 `style.json` 与照片 |
| `scripts/` | 渲染（HTML / PPTX）、检查、自动排版、逐页设计构建器与六个样例脚本 |
| `examples/` | 六套风格样例与一份 outline 示例；渲染结果输出到 `examples/out/`（已被 git 忽略） |

详见 [SKILL.md](SKILL.md)。
