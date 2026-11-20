"""ppt-atelier 公共模块：读取 plan.json、解析资源路径与字体角色。

plan.json 的坐标单位是 px（基于 canvas，默认 1280×720），字号与字距单位是 pt，
PPTX 画布 960×540pt，所以 1px = 0.75pt。
"""
from __future__ import annotations

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets"
STYLES_DIR = ASSETS / "styles"
FONTS = json.loads((ASSETS / "fonts.json").read_text(encoding="utf-8"))

DEFAULT_CANVAS = {"width_px": 1280, "height_px": 720}


class Plan:
    """plan.json 的薄封装：补默认值、解析相对路径，供 HTML/PPTX/检查脚本共用。"""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.dir = self.path.parent
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.canvas = {**DEFAULT_CANVAS, **self.data.get("canvas", {})}
        self.width = int(self.canvas["width_px"])
        self.height = int(self.canvas["height_px"])
        self.style_id = self.data.get("style", "")
        self.style = load_style(self.style_id) if self.style_id else {}
        self.slides = self.data.get("slides", [])

    @property
    def title(self) -> str:
        return self.data.get("project") or self.data.get("title") or "Untitled Deck"

    def resolve(self, ref: str | None) -> Path | None:
        """资源查找顺序：绝对路径 → plan 所在目录 → 风格目录 → skill 根目录。
        也兼容 `assets/xx` 前缀写法。"""
        if not ref:
            return None
        p = Path(ref).expanduser()
        if p.is_absolute():
            return p if p.exists() else None
        candidates = [self.dir / p]
        if self.style_id:
            sd = STYLES_DIR / self.style_id
            candidates += [sd / p, sd / Path(*p.parts[1:]) if p.parts[0] == "assets" else sd / p]
        candidates.append(SKILL_ROOT / p)
        for c in candidates:
            if c.exists():
                return c
        return None


def load_style(style_id: str) -> dict:
    f = STYLES_DIR / style_id / "style.json"
    if not f.exists():
        raise SystemExit(f"未知风格 {style_id!r}，可选：{', '.join(list_styles())}")
    return json.loads(f.read_text(encoding="utf-8"))


def list_styles() -> list[str]:
    return sorted(p.parent.name for p in STYLES_DIR.glob("*/style.json"))


def font_role(name: str) -> dict:
    """把 plan 里的 font（角色名或商业字体名）解析成角色定义；未知字体原样作为首选。"""
    role = name if name in FONTS["roles"] else FONTS["aliases"].get(name)
    if role:
        return {"role": role, **FONTS["roles"][role]}
    return {"role": None, "css": [name, "sans-serif"], "pptx": {"mac": name, "win": name, "original": name}}


def css_font_stack(name: str) -> str:
    stack = font_role(name)["css"]
    generic = {"serif", "sans-serif", "monospace", "cursive"}
    # 用单引号：结果会嵌进 HTML 的 style="..." 属性，双引号会提前截断属性值
    return ", ".join(f if f in generic else f"'{f}'" for f in stack)


def pptx_font(name: str, profile: str) -> str:
    return font_role(name)["pptx"].get(profile) or name


def is_cjk(text: str) -> bool:
    return any("\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff" for ch in text)


def line_spacing(t: dict) -> float:
    """行距倍数。未显式指定 lineSpacing 时按「框高 ÷ (行数 × 字号)」自适应，上限 1.25：
    文本框常按字高贴身画（多行约 1.15、单行大字约 0.95），固定 1.25 会整体溢出。
    下限：多行 1.05 保证可读，单行 0.9 允许展示大字贴框。HTML 与 PPTX 共用此值。"""
    if "lineSpacing" in t:
        return float(t["lineSpacing"])
    lines = t["value"].count("\n") + 1
    size_px = t.get("size", 14) * 4 / 3
    floor = 1.05 if lines > 1 else 0.9
    return round(max(floor, min(1.25, t["h"] / (lines * size_px))), 3)
