# 版式（layout）

`compose_plan.py` 内置 9 种通用版式，供 outline 快速出稿。风格识别度更强的逐页页型见 `styles/<风格>.md`「页型」表与对应样例脚本。

每种版式的坐标从风格的 `grid`（边距、页眉页脚位置）和字号阶梯推出，换风格不需要改内容。
表中"字段"是该版式的专有字段；通用字段见 plan-schema.md。

| layout | 用途 | 专有字段 | 推荐背景 |
|---|---|---|---|
| `cover` | 封面 | `kicker` `title` `subtitle` `english` `meta` `align`(left/center) | 满版图，左侧或中部平整 |
| `toc` | 目录 | `title` `index` `items[{title,en}]`（3-6 项） | 浅纹理或加 scrim |
| `statement` | 观点/金句/关于我 | `index` `title` `english` `body` `vertical`（竖排大字，2-4 字）`indent` | 纸张/平整背景 |
| `split-image` | 图文分栏 | `image` `image_w` `image_h` `image_y` `side`(文字在 left/right) `caption` `index` `title` `body` `points[]`（≤4） | 浅色平整背景 |
| `cards` | 并列要点 | `index` `title` `items[{title,body,no}]`（2-6 项，`cols` 可指定列数） | 平整背景；深色图需 scrim |
| `steps` | 流程/时间线 | `index` `title` `items[{title,body}]`（3-5 步） | 平整背景 |
| `stats` | 数据 | `index` `title` `items[{value,label}]`（3-4 项） | 平整背景 |
| `full-image` | 满版大图 + 角落标题 | `index` `title` `english` `body` `text_area`(bottom-left/top-left/bottom-right/top-right) | 主体在文字区对侧的照片 |
| `closing` | 结尾 | `index` `title` `english` `contact` | 与封面呼应 |

## 推荐页序（outline 快速出稿时）

- **个人介绍（F）**：cover → statement（关于我）→ toc → cards（能力）→ split-image（代表项目）× N → stats → steps（合作方式）→ closing
- **作品集（C）**：cover → toc → [full-image（项目大图）→ split-image（细节）] × N → cards（能力）→ stats（经历）→ closing
- **品牌汇报（D）**：cover → statement（品牌故事）→ cards（定位）→ full-image（场景）→ split-image（产品）→ stats → steps（传播）→ closing
- **数据汇报（B）**：cover → stats（核心指标）→ toc → cards → full-image（洞察）→ split-image → steps（计划）→ closing
- **演讲（A）**：cover → statement（问题）→ stats → full-image（转折）→ cards（方法）→ split-image（案例）→ steps（行动）→ closing
- 需要风格鲜明的成稿时，改用样例脚本逐页设计（见 SKILL.md 第 4 步）

## 版式之外

需要的版式不在列表中时：

1. 先用最接近的版式生成，再在 plan.json 中手动增删文本框/形状
2. 同一调整出现两次以上 → 在 `compose_plan.py` 中新增 layout 方法，并在本文件登记
