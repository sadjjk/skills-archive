# 迭代循环：把判断写回 Skill

先做出一版，再把判断写回去。分五步。

## 五步

1. **收集参考**：挑同一风格的 3-5 张参考，观察字体、比例和留白。记录：标题字号占画面高度的比例、正文行数、边距、图文比例、配色（取 5-7 个色值）。
2. **写成规则**：把"我觉得好看"改写成可执行要求。好规则可以被检查——"标题 ≤ 2 行、字距 2-6pt"是规则，"标题要大气"不是。
3. **跑一个主题**：用新规则做 4-6 页小样（封面、一页图文、一页卡片、结尾），检查规则能否迁移到不同内容。
4. **逐页校正**：看断行、图位、对齐与整套节奏（quality-check.md）。每处手动修改都记下"改了什么、为什么"。
5. **回写 Skill**：把有效修改写进规则、模板或脚本：

| 修改类型 | 写到哪里 |
|---|---|
| 通用排版规律（适用所有风格） | `references/design-rules.md`「改稿沉淀」 |
| 某风格的配色、字体、禁忌 | `references/styles/<风格>.md` + `assets/styles/<风格>/style.json` |
| 某风格的前景色组、字号阶梯 | `scripts/compose_plan.py` 的 `STYLE_TONES` |
| 版式坐标算法 | `scripts/compose_plan.py` 对应 layout 方法 |
| 新的检查项 | `scripts/check_deck.mjs` + `references/quality-check.md` |
| 风格专属页型 | `scripts/make_<x>_example.py` 对应页 + 风格文档「页型」表 |
| 一套可复用的成稿 | `examples/` 下新增 plan（逐页设计）或 outline |

回写后重跑全部样例，确认没有破坏其他风格：

```bash
cd $SKILL/examples
for x in a b c d e f; do python3 ../scripts/make_${x}_example.py; done
for f in *.json; do python3 ../scripts/make_deck.py "$f" || echo "FAIL $f"; done
```

## 新增风格（例：G 电子杂志）

1. 建目录 `assets/styles/g-xxx/`，写 `style.json`（字段参照现有风格：id、code、name、keywords、best_for、palette、fonts、grid）
2. 放照片到 `photos/`（2000px 宽以上，可商用来源，写 `photos/CREDITS.md`）。没有合适素材时用 `fetch_photos.py` 搜（见 SKILL.md「需要新照片时」）；先按 design-rules.md「照片与文字区」测分区再选图）
   定下「五个标志」：一种独有字体组合、一种取景形状、一种标志性页型、一种强调色用法、一种页眉页脚系统
3. 在 `compose_plan.py` 的 `STYLE_TONES` 加一组：`default_dark`、`cover_size`、`title_size`、`light`/`dark` 两组前景色（bg/ink/soft/muted/rule/accent）
4. 写 `references/styles/g-xxx.md`：五个标志、配色、字体、页型、选图、禁忌
5. 写 `scripts/make_g_example.py`（用 `page_kit`，参照现有样例脚本），生成 `examples/g-xxx.json`，跑通 make_deck，看截图校正
6. 在 SKILL.md 风格表中登记

## 从一张喜欢的参考图开始

用户只给一张参考图时：
1. 描述它：底色深浅、主色、标题字体类型（衬线/无衬线/手写）、字号对比、留白比例、图文关系
2. 找到最接近的已有风格作为起点，列出差异
3. 差异小（配色/字体） → 复制最接近风格的样例脚本，改颜色常量与字体角色
4. 差异大 → 按"新增风格"建立，先做 4 页小样给用户确认
