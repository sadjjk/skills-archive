#!/usr/bin/env python3
"""一键流水线：outline.json 或 plan.json → plan → HTML → PPTX → 逐页检查。

用法：python3 make_deck.py <outline.json|plan.json> [-o 输出目录] [--fonts mac|win|original] [--no-check]

输入是 outline（只写内容）时先调用 compose_plan 自动排版；输入已经是 plan（slides 里有 texts 坐标）时直接渲染。
输出目录结构：
  <name>.plan.json   最终坐标（逐页校正时改这个文件，再重跑本脚本）
  <name>.html        横向翻页演示（←/→ 翻页，ESC 总览）
  <name>.pptx        可编辑 PPTX
  check/             slide-NN.png 逐页截图、overview.png 总览、report.json 检查报告
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_html import HtmlDeckBuilder  # noqa: E402
from build_pptx import PptxDeckBuilder  # noqa: E402
from compose_plan import Composer  # noqa: E402
from deck_lib import Plan  # noqa: E402


class DeckPipeline:
    def __init__(self, src: Path, out_dir: Path, fonts: str, check: bool):
        self.src, self.out_dir, self.fonts, self.check = src.resolve(), out_dir.resolve(), fonts, check
        self.name = src.name.replace(".outline.json", "").replace(".plan.json", "").replace(".json", "")

    def _plan_path(self) -> Path:
        data = json.loads(self.src.read_text(encoding="utf-8"))
        is_plan = all("texts" in s for s in data.get("slides", [])) and data.get("slides")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        dst = self.out_dir / f"{self.name}.plan.json"
        if is_plan:
            if dst != self.src:
                plan = data
                # 原 plan 里的相对资源路径以原目录为基准；拷贝到输出目录后改写为绝对路径，避免断链
                tmp = Plan(self.src)
                for s in plan["slides"]:
                    for key in ("background",):
                        if s.get(key) and (p := tmp.resolve(s[key])):
                            s[key] = str(p)
                    for sh in s.get("shapes", []):
                        if sh.get("src") and (p := tmp.resolve(sh["src"])):
                            sh["src"] = str(p)
                dst.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"plan: {dst}（直接使用已有坐标）")
        else:
            plan = Composer(data).compose()
            dst.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"plan: {dst}（由 outline 自动排版，{len(plan['slides'])} 页）")
        return dst

    def run(self) -> int:
        plan = Plan(self._plan_path())
        h = HtmlDeckBuilder(plan, self.out_dir / f"{self.name}.html")
        print(f"HTML: {h.build()}")
        p = PptxDeckBuilder(plan, self.out_dir / f"{self.name}.pptx", self.fonts)
        print(f"PPTX: {p.build()}（字体方案 {self.fonts}）")
        missing = sorted(set(h.missing + p.missing))
        if missing:
            print("⚠ 找不到的资源：" + ", ".join(missing))
        if not self.check:
            return 0
        if not shutil.which("node"):
            print("⚠ 未安装 node，跳过逐页检查")
            return 0
        r = subprocess.run(["node", str(HERE / "check_deck.mjs"), str(self.out_dir / f"{self.name}.html"),
                            "--out", str(self.out_dir / "check")])
        return r.returncode or (1 if missing else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("-o", "--out-dir")
    ap.add_argument("--fonts", choices=["mac", "win", "original"], default="mac")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()
    src = Path(a.src)
    out = Path(a.out_dir) if a.out_dir else src.parent / "out" / src.name.split(".")[0]
    sys.exit(DeckPipeline(src, out, a.fonts, not a.no_check).run())


if __name__ == "__main__":
    main()
