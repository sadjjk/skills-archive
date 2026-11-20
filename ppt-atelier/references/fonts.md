# 字体

plan 里的 `font` 写**角色名**（推荐）或商业字体名，`assets/fonts.json` 负责映射：

- HTML：按字体栈依次回退，用户装了商业字体就用商业字体
- PPTX：按 `--fonts` 方案写入一个确定的字体名（PPTX 不支持字体栈）

## 角色

| 角色 | 用途 | 商业字体（--fonts original） | macOS（--fonts mac） | Windows（--fonts win） | 免费替代（可商用） |
|---|---|---|---|---|---|
| serif-zh | 中文主标题 | 方正书宋简体 / 经典标宋简 / 方正明尚简体 | Songti SC | SimSun | 思源宋体 Noto Serif SC |
| sans-zh | 中文正文 | 方正兰亭细黑_GBK_M | PingFang SC | Microsoft YaHei UI Light | 思源黑体 Noto Sans SC |
| script-zh | 中文手写点缀 | 全新硬笔行书简 | Xingkai SC | STXingkai | 霞鹜文楷 LXGW WenKai |
| serif-en | 英文衬线/数字 | Times New Roman | Didot | Times New Roman | Playfair Display |
| script-en | 英文斜体副标 | 313-CAI978 | Baskerville（斜体） | Georgia（斜体） | Cormorant Garamond Italic |
| sans-en | 英文索引/瑞士风 | Microsoft YaHei UI | Helvetica Neue | Arial | Inter |
| mono | 编号/kicker | — | Menlo | Consolas | IBM Plex Mono |
| display-zh | A/B 粗宋展示字 | 方正大标宋 | Songti SC Black | SimSun | 思源宋体 Heavy |
| light-zh | C/F 细宋正文 | 方正书宋 | Songti SC Light | SimSun | 思源宋体 Light |
| bold-zh | B 中文粗黑标题 | 方正兰亭粗黑 | PingFang SC Semibold | Microsoft YaHei | 思源黑体 Bold |
| kai-zh | F 签名、金句；A/C 署名 | 方正楷体 | Kaiti SC | KaiTi | 霞鹜文楷 |
| wei-zh | F 人物大标题 | 方正魏碑 | Weibei SC | KaiTi | 站酷庆科黄油体（风格近似） |
| round-zh | D 品牌标题与正文 | 方正准圆 | Yuanti SC Light | Microsoft YaHei | 思源柔黑 / 得意黑 |
| didone-en | A 刊头、页码、大数字 | Bodoni 72 | Bodoni 72 | Bodoni MT | Bodoni Moda |
| didot-en | C 编号与斜体标题 | Didot | Didot | Bodoni MT | Playfair Display |
| geo-en | D 字标与英文 | Futura | Futura | Century Gothic | Jost |
| helv-black / helv-thin | B 细粗对比 | Helvetica Neue | Helvetica Neue Bold / UltraLight | Arial Black / Arial | Inter Black / Thin |
| condensed-en | A/C 窄体标签 | Avenir Next Condensed | Avenir Next Condensed | Arial Narrow | Barlow Condensed |

## 使用建议

- 交付给 Mac 用户：`--fonts mac`；交付给 Windows 用户或不确定：`--fonts win`
- 用户已安装方正等商业字体并有授权：`--fonts original`
- Windows 缺少魏碑、圆体、Futura 等时会回退，F/D 风格交付 Windows 用户前提醒安装免费替代字体
- 商业字体（方正、汉仪等）用于商业交付需要授权，交付说明中提醒
- 新增字体：在 `fonts.json` 的 `roles` 加角色或在 `aliases` 加别名，HTML 字体栈与三种 PPTX 方案都要填
- 检查报告的 `font` 提示列出了实际回退结果，交付说明中写清实际字体
