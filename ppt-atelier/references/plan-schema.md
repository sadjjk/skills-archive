# plan.json / outline.json 字段说明

两种输入，`make_deck.py` 自动识别：

- **outline.json**：只写内容和版式名，坐标由 `compose_plan.py` 计算。日常使用首选。
- **plan.json**：每个文本框的精确坐标。逐页设计（六种风格样例都是 plan，由 `scripts/make_<x>_example.py` 用 `page_kit` 生成）与逐页校正时使用。outline 生成后得到的 `out/<name>/<name>.plan.json` 就是 plan，可以直接手改再重跑。

坐标单位 px（画布 1280×720），字号与字距单位 pt（PPTX 画布 960×540pt，1px = 0.75pt）。

## outline.json

```jsonc
{
  "style": "f-premium-texture",          // 必填：a-editorial | b-swiss | c-dark-portfolio | d-natural-brand | e-oriental-interior | f-premium-texture
  "project": "林知夏 · 个人介绍",          // deck 标题（HTML <title>）
  "subject": "品牌与空间设计师个人介绍",
  "header": {"left": "PERSONAL PROFILE", "right": "品牌 · 空间 · 叙事"},   // 每页页眉，可省略
  "footer": {"left": "林知夏 · 设计工作室", "right": "LIN ZHIXIA STUDIO"}, // 页脚左 + 页脚中，可省略
  "slides": [ { "layout": "cover", ... }, ... ]
}
```

### 每页通用字段

| 字段 | 说明 |
|---|---|
| `layout` | 必填，见 layouts.md：cover / toc / statement / split-image / cards / steps / stats / full-image / closing |
| `section` | 页面名称（总览与 PPTX 备注用） |
| `dark` | true 深色页 / false 浅色页；省略时取风格默认（C/D/E 深，A/B/F 浅） |
| `background` | 背景图，相对 outline 目录或风格目录（如 `photos/01-window-sill.jpg`） |
| `background_frame` | 背景图位置 `{x,y,w,h}`，省略为满版 |
| `flip` | true 时背景水平镜像 |
| `scrim` | 遮罩 `{x,y,w,h,color,opacity}`，省略项取满版 + 页面底色 + 0.55 |
| `chrome` | false 时不画页眉页脚页码（满版封面可用） |
| `title_size` / `title_spacing` / `y` | 覆盖版式默认的标题字号、字距、起始 y |
| `notes` | 演讲者备注，写入 PPTX |
| `extra_shapes` | 额外形状，格式同 plan 的 shapes |

各版式的专有字段（`kicker`、`items`、`points`、`image` 等）见 layouts.md。

## plan.json

```jsonc
{
  "schema_version": 1,
  "style": "e-oriental-interior",
  "project": "栖隐 · 东方静养空间",
  "canvas": {"width_px": 1280, "height_px": 720},
  "slides": [{
    "page": 1,
    "section": "封面",
    "background": "photos/01-courtyard-threshold.jpg",      // 相对 plan 目录或风格目录，也兼容 assets/ 前缀
    "background_frame": {"x": 0, "y": 0, "w": 1280, "h": 720},
    "background_color": "#34271B",                          // 可选：图片未铺满时的底色
    "image_horizontal_flip": false,
    "shapes": [                                             // 可选，按顺序叠在背景之上、文字之下
      {"type": "rect",  "x": 0, "y": 0, "w": 1280, "h": 720, "fill": "#000000", "opacity": 0.4},
      {"type": "rect",  "x": 640, "y": 120, "w": 520, "h": 480, "fill": "#FFFFFF", "opacity": 0.16,
       "radius": 6, "line": "#FFFFFF", "line_width": 0.75},  // 圆角 + 描边（毛玻璃卡片）
      {"type": "ellipse", "x": 760, "y": 520, "w": 120, "h": 120, "fill": "#C98B6B"},   // 圆/椭圆
      {"type": "line",  "x1": 80, "y1": 300, "x2": 160, "y2": 300, "color": "#E2C99C", "width": 1, "opacity": 1},
      {"type": "image", "src": "photos/a.jpg", "x": 640, "y": 110, "w": 560, "h": 500,
       "mask": "arch",          // 可选：circle 圆 | arch 上半圆拱（竖向框） | rounded 圆角（配 radius）
       "focus": "70% 40%",      // 可选：裁切焦点，同 CSS object-position
       "grayscale": true}       // 可选：转黑白（PPTX 端预先转换图片）
    ],
    "texts": [{
      "name": "cover-title-0",        // 唯一名，检查报告用；header/footer/page 开头的不做安全区检查
      "value": "静",                   // \n 为手动换行
      "x": 320, "y": 183, "w": 160, "h": 112,
      "size": 84,                      // pt
      "font": "serif-zh",               // 字体角色名（推荐）或商业字体名，见 fonts.md
      "color": "#392B20",
      "alignment": "center",           // left | center | right
      "charSpacing": 13,               // 字距 pt，可选
      "lineSpacing": 1.15,             // 行距倍数，可选；省略时按框高自适应
      "italic": false, "weight": 400,  // 可选，省略时取字体角色默认
      "rotate": -90,                   // 可选：绕文本框中心旋转（度），用于书脊字、侧标
      "underline": false, "uppercase": false,  // 可选
      "bleed": false                   // 可选：刻意出血/叠压的装饰大字，检查脚本跳过越界、安全区与重叠判定
    }],
    "notes": "演讲者备注"
  }]
}
```

### 资源路径解析顺序

绝对路径 → plan 所在目录 → 风格目录 `assets/styles/<style>/`（自动去掉 `assets/` 前缀）→ Skill 根目录。
`make_deck.py` 把 plan 复制到输出目录时会把相对路径改写为绝对路径。
