# 质量检查

每一次改稿，都留下下一次的标准。检查分两层：脚本自动检查 + 亲眼逐页看。两层都通过才交付。

## 一、自动检查（scripts/check_deck.mjs）

`make_deck.py` 会自动调用；也可单独运行：`node scripts/check_deck.mjs out/deck/deck.html --out out/deck/check [--strict]`

| 类型 | 级别 | 判定口径 | 处理 |
|---|---|---|---|
| overflow | error | 实际行数 × 行高 > 框高，或横向长串超出框宽 | 调大 `h`、减小 `size`、改写或手动 `\n` 断行 |
| bounds | error | 文本框超出画布 | 移回画布内 |
| safe-area | warn | 文字进入安全边距（页眉/页脚/页码等 name 以 header/footer/page/top/bottom/section/index 开头的除外） | 移入；装饰性英文可保留并在交付说明注明 |
| overlap | warn | 两个文本框的行盒重叠 > 3px | 拉开间距；刻意叠字设计可保留 |
| orphan | warn | 中文段落末行只剩 1 个字 | 调整 `w` 或改写 |
| font | info | 首选字体未安装，回退到备选 | 交付说明中写清实际使用的字体 |

退出码：存在 error 时为 1；`--strict` 时 warn 也算失败。报告写入 `check/report.json`。

## 二、逐页人工检查（看 slide-NN.png 与 overview.png）

分四项：

### 01 标题与正文
- [ ] 层级清楚：一眼能分出主标题、副标题、正文、索引
- [ ] 中文自然断行：断在语义停顿处，无孤字，无标点落在行首
- [ ] 英文副标与中文标题有呼吸间距，不粘连

### 02 图位与文字
- [ ] 文字避开亮部和复杂纹理，正文对比度足够（暗底浅字 / 亮底深字）
- [ ] 图片主体完整，没有被文字或裁切切断（人脸、器物、窗框）
- [ ] 图片方向引导视线朝向文字

### 03 全套页面
- [ ] 边距、细线和页脚基线一致（总览图里横向扫一遍）
- [ ] 深浅页面、版式、对齐方式有交替，无连续 3 页同版式
- [ ] 页码连续，章节编号正确

### 04 导出成品
- [ ] 逐页渲染，确认内容与字体：PPTX 用 Keynote/PowerPoint/WPS 打开至少抽查封面、一页正文、结尾
- [ ] 文字全部可编辑（不是图片）
- [ ] 资源无缺失（make_deck 不再提示"找不到的资源"）

macOS 上可用 Keynote 批量导出 PPTX 预览，核对与 HTML 截图是否一致：

```bash
osascript -e 'tell application "Keynote"
  set d to open POSIX file "/abs/path/deck.pptx"
  export d to POSIX file "/abs/path/keynote-preview" as slide images with properties {image format:PNG}
  close d saving no
end tell'
```

## 三、交付说明模板

```
风格：F 肌理景深｜页数：12｜字体方案：mac（Songti SC / PingFang SC / Baskerville）
文件：deck.pptx（可编辑）、check/overview.png、check/slide-01..12.png、deck.html
检查：error 0，warn 1（P1 英文装饰行进入边距，有意保留）
图片：样例图库照片 8 张（Unsplash License，来源见 photos/CREDITS.md）；P3、P7 建议换成客户实拍
```
