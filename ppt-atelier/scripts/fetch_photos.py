#!/usr/bin/env python3
"""从免费可商用图库搜图、出候选联系表、挑选下载，并自动写入 CREDITS.md。

两步走（中间由人或 Agent 看联系表挑选，不会自动把图塞进项目）：

  1) 搜索候选
     python3 fetch_photos.py search "茶室" "tea ceremony" --source all --count 24 --orientation landscape --out ./候选
     → 候选/candidates.json   每张：编号、图源、标题、作者、原图尺寸、可下载尺寸、许可、原图页、放字建议
     → 候选/candidates.jpg    带编号的缩略图联系表（格下标注图源、尺寸、放字建议）

  2) 挑选下载
     python3 fetch_photos.py pick --from ./候选 --ids 3,7,12 --dest ./photos
     python3 fetch_photos.py pick --from ./候选 --ids 3:cover,7:tea --dest ./photos    # 编号:文件名
     → photos/<名字>.jpg，并在 photos/CREDITS.md 追加「文件 / 摄影师 / 原图」行

图源（均免 Key、免浏览器）：
  ssyer  沙沙野 ssyer.com   全站 CC0（平台声明），中文关键词效果好、东方题材多；
                            免登录只能取 1200 宽预览图，适合局部用图（装裱小图、拼贴、圆形取景），不建议满版
  burst  Burst（Shopify）   逐张核对 CC0 许可，原图约 5000+ 宽，下载取 2400 宽；偏欧美商业与生活方式，英文关键词
依赖：Python 3.9+ 标准库 + Pillow。
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from photo_zones import PhotoZones  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
REQUEST_GAP = 0.3       # 两次请求之间的间隔（秒），不连续猛打
MIN_LONG_EDGE = 1000    # 可下载尺寸长边低于此值的图直接丢弃
FULL_BLEED_MIN = 1920   # 低于此宽度的图在联系表与下载时提示「仅宜局部用图」


@dataclass
class Photo:
    source: str
    id: str
    title: str
    author: str
    width: int              # 原图尺寸
    height: int
    dl_width: int           # 免登录可下载到的尺寸
    dl_height: int
    thumb_url: str
    download_url: str
    page_url: str
    license: str
    license_url: str
    no: int = 0
    zones: str = ""
    notes: list[str] = field(default_factory=list)


class Http:
    """带节流的最小 HTTP 客户端（标准库）。"""

    def __init__(self):
        self._last = 0.0

    def _wait(self):
        gap = time.time() - self._last
        if gap < REQUEST_GAP:
            time.sleep(REQUEST_GAP - gap)
        self._last = time.time()

    def get(self, url: str, timeout=30, referer: str | None = None) -> bytes:
        self._wait()
        headers = {"User-Agent": UA}
        if referer:
            headers["Referer"] = referer
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
            return r.read()

    def post_json(self, url: str, body: dict, referer: str, timeout=30) -> dict:
        self._wait()
        req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(), method="POST",
                                     headers={"User-Agent": UA, "Content-Type": "application/json", "Referer": referer})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))


class SsyerSource:
    """沙沙野：搜索接口 POST /apis/20001（cateId=1 摄影专区），详情 /apis/20002。
    参数取自其搜索页实际请求；多带默认字段会返回空列表。"""

    name = "ssyer"
    base = "https://www.ssyer.com"
    license, license_url = "CC0（沙沙野平台声明）", "https://www.ssyer.com/"

    def __init__(self, http: Http):
        self.http = http

    def search(self, query: str, count: int) -> list[Photo]:
        out, page = [], 1
        while len(out) < count:
            d = self.http.post_json(f"{self.base}/apis/20001", {
                "keywords": query, "cateId": 1, "order": 1,
                "page": {"showCount": 20, "currentPage": page}}, referer=self.base + "/")
            items = d.get("data") or []
            if d.get("code") != 200 or not items:
                break
            for x in items:
                w, h = int(x.get("width") or 0), int(x.get("height") or 0)
                if not (w and h and x.get("showUrl")):
                    continue
                # 免登录仅能取 showUrl 预览图：长边约 1200，按原图比例换算
                scale = 1200 / max(w, h)
                out.append(Photo(
                    source=self.name, id=str(x["id"]), title=(x.get("title") or "").split("_")[0],
                    author=x.get("authorName") or "ssyer", width=w, height=h,
                    dl_width=round(w * scale), dl_height=round(h * scale),
                    thumb_url=x.get("thumbUrl") or x["showUrl"], download_url=x["showUrl"],
                    page_url=f"{self.base}/detail/{x['id']}", license=self.license, license_url=self.license_url))
            page += 1
            if page > (d.get("page") or {}).get("totalPage", page):
                break
        return out[:count]

    def verify(self, p: Photo) -> bool:
        """详情接口确认作品仍存在、未下架。"""
        d = self.http.post_json(f"{self.base}/apis/20002", {"id": int(p.id)}, referer=self.base + "/")
        data = d.get("data") or {}
        return d.get("code") == 200 and str(data.get("id")) == p.id and not data.get("deleted")


class BurstSource:
    """Burst（Shopify）：解析搜索结果页（每页 30 张），逐张读详情页 JSON-LD 核对 CC0 许可与作者。"""

    name = "burst"
    base = "https://burst.shopify.com"
    cdn = "https://burst.shopifycdn.com/photos"
    cc0 = "licenses/creative-commons"
    # 卡片 HTML 的 <a> 与 <div> 之间有换行缩进，用 \s* 容忍
    tile = re.compile(r'href="/stock-photos/photos/([a-z0-9\-]+)\?q=[^"]*">\s*<div class="ratio-box"\s+'
                      r'style="padding-bottom:\s*([\d.]+)%;">\s*<img[^>]*?data-photo-title="([^"]*)"')

    def __init__(self, http: Http):
        self.http = http

    def search(self, query: str, count: int) -> list[Photo]:
        out, seen, page = [], set(), 1
        while len(out) < count and page <= 5:
            q = urllib.parse.urlencode({"q": query, "page": page})
            t = self.http.get(f"{self.base}/photos/search?{q}").decode("utf-8", "ignore")
            tiles = [m for m in self.tile.findall(t) if m[0] not in seen]
            if not tiles:
                break
            for slug, ratio, title in tiles:
                if len(out) >= count:
                    break
                seen.add(slug)
                meta = self._detail(slug)
                if not meta:
                    continue
                # 详情页 JSON-LD 的 contentUrl 才是真实文件名（页面 slug 偶尔与文件名不一致）
                file = meta["file"]
                w, h = meta["w"], meta["h"] or round(meta["w"] * float(ratio) / 100)
                dl_w = min(2400, w)
                out.append(Photo(
                    source=self.name, id=slug, title=html.unescape(title), author=meta["author"],
                    width=w, height=h, dl_width=dl_w, dl_height=round(dl_w * h / w),
                    thumb_url=f"{self.cdn}/{file}?width=373&format=pjpg&exif=0&iptc=0",
                    download_url=f"{self.cdn}/{file}?width={dl_w}&format=pjpg&exif=0&iptc=0",
                    page_url=f"{self.base}/stock-photos/photos/{slug}", license="CC0", license_url=meta["license"]))
            page += 1
        return out

    def _detail(self, slug: str) -> dict | None:
        """读详情页 JSON-LD：许可必须是 CC0；原图宽度从页面最大 width 参数或原图头部推断。"""
        p = self.http.get(f"{self.base}/stock-photos/photos/{slug}").decode("utf-8", "ignore")
        for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', p, re.S):
            try:
                d = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict) and d.get("@type") == "ImageObject":
                lic = d.get("license") or ""
                if self.cc0 not in lic:
                    return None  # 非 CC0（如 Some Rights Reserved）一律跳过
                author = (d.get("creator") or d.get("author") or {}).get("name") or "Burst"
                # contentUrl 形如 https://burst.shopifycdn.com/photos/<file>.jpg?exif=0&iptc=0
                m = re.search(r'/photos/([^?"]+)', d.get("contentUrl") or "")
                if not m:
                    return None
                w, h = self._orig_size(m.group(1))
                return {"author": author, "license": lic, "w": w, "h": h, "file": m.group(1)}
        return None

    def _orig_size(self, file: str) -> tuple[int, int]:
        """只读原图前 64KB 解析 JPEG 头拿尺寸，不下载整张。"""
        req = urllib.request.Request(f"{self.cdn}/{file}?exif=0&iptc=0", headers={"User-Agent": UA, "Range": "bytes=0-65535"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                im = Image.open(io.BytesIO(r.read()))
                return im.size
        except Exception:
            return 2400, 0

    def verify(self, p: Photo) -> bool:
        return self._detail(p.id) is not None





SOURCES = {"ssyer": SsyerSource, "burst": BurstSource}


class ContactSheet:
    """带编号的候选联系表：每格缩略图 + 编号 + 图源 + 可下载尺寸 + 放字建议。"""

    cell_w, thumb_h, caption_h, cols, gap = 300, 200, 44, 6, 10

    def __init__(self):
        self.font = self._font(13)
        self.font_big = self._font(20)

    @staticmethod
    def _font(size):
        for f in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
                  "/System/Library/Fonts/Hiragino Sans GB.ttc", "C:/Windows/Fonts/msyh.ttc"]:
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def render(self, photos: list[Photo], thumbs: dict[int, Image.Image], out: Path):
        rows = (len(photos) + self.cols - 1) // self.cols
        W = self.cols * (self.cell_w + self.gap) + self.gap
        H = rows * (self.thumb_h + self.caption_h + self.gap) + self.gap
        sheet = Image.new("RGB", (W, H), "#1b1b1b")
        d = ImageDraw.Draw(sheet)
        for i, p in enumerate(photos):
            x = self.gap + (i % self.cols) * (self.cell_w + self.gap)
            y = self.gap + (i // self.cols) * (self.thumb_h + self.caption_h + self.gap)
            im = thumbs.get(p.no)
            if im:
                t = im.copy()
                t.thumbnail((self.cell_w, self.thumb_h))
                sheet.paste(t, (x + (self.cell_w - t.width) // 2, y + (self.thumb_h - t.height) // 2))
            d.rectangle((x, y, x + 34, y + 26), fill="#002FA7")
            d.text((x + 6, y + 2), str(p.no), fill="white", font=self.font_big)
            warn = " ⚠局部" if p.dl_width < FULL_BLEED_MIN else ""
            d.text((x, y + self.thumb_h + 4), f"{p.source} · {p.dl_width}×{p.dl_height}{warn}", fill="#cfcfcf", font=self.font)
            d.text((x, y + self.thumb_h + 22), p.zones[:22], fill="#E2C99C", font=self.font)
        sheet.save(out, quality=88)


class PhotoFetcher:
    def __init__(self):
        self.http = Http()

    # ---------- search ----------
    def search(self, queries: list[str], sources: list[str], count: int, orientation: str, out: Path):
        out.mkdir(parents=True, exist_ok=True)
        found, seen = [], set()
        for src in sources:
            s = SOURCES[src](self.http)
            for q in queries:
                try:
                    batch = s.search(q, count)
                except Exception as e:  # 单个图源失败不影响其它图源
                    print(f"⚠ {src} 搜索「{q}」失败：{e}")
                    continue
                print(f"  {src:6s} 「{q}」→ {len(batch)} 张")
                for p in batch:
                    key = (p.source, p.id)
                    if key in seen or max(p.dl_width, p.dl_height) < MIN_LONG_EDGE:
                        continue
                    if orientation == "landscape" and p.width <= p.height:
                        continue
                    if orientation == "portrait" and p.height <= p.width:
                        continue
                    seen.add(key)
                    found.append(p)
        if not found:
            raise SystemExit("没有找到符合条件的图片：换关键词（ssyer 用中文、burst 用英文），或放宽 --orientation")
        thumbs = {}
        for i, p in enumerate(found, 1):
            p.no = i
            try:
                im = Image.open(io.BytesIO(self.http.get(p.thumb_url, referer=SOURCES[p.source].base + "/"))).convert("RGB")
                thumbs[i] = im
                p.zones = PhotoZones(im).summary()
            except Exception as e:
                p.zones = "缩略图失败"
                print(f"⚠ 缩略图 #{i} 失败：{e}")
            if p.dl_width < FULL_BLEED_MIN:
                p.notes.append(f"可下载 {p.dl_width} 宽，建议局部用图（装裱小图/拼贴/圆形取景），不宜满版")
        (out / "candidates.json").write_text(json.dumps([asdict(p) for p in found], ensure_ascii=False, indent=2), encoding="utf-8")
        ContactSheet().render(found, thumbs, out / "candidates.jpg")
        print(f"\n{'#':>3}  {'图源':6s} {'可下载尺寸':>11s}  {'放字建议':16s} 标题 / 作者")
        for p in found:
            print(f"{p.no:>3}  {p.source:6s} {p.dl_width:>5}×{p.dl_height:<5}  {p.zones:16s} {p.title[:24]} / {p.author}")
        print(f"\n候选：{out / 'candidates.jpg'}\n明细：{out / 'candidates.json'}")
        print(f"挑选后执行：python3 {Path(__file__).name} pick --from {out} --ids 1,2,3 --dest <项目>/photos")

    # ---------- pick ----------
    def pick(self, cand_dir: Path, ids: str, dest: Path):
        cands = {p["no"]: Photo(**p) for p in json.loads((cand_dir / "candidates.json").read_text(encoding="utf-8"))}
        dest.mkdir(parents=True, exist_ok=True)
        credits = dest / "CREDITS.md"
        for token in [t.strip() for t in ids.split(",") if t.strip()]:
            no_s, _, name = token.partition(":")
            p = cands.get(int(no_s))
            if not p:
                print(f"⚠ 编号 {no_s} 不在候选里，跳过")
                continue
            name = self._safe_name(name or f"{p.source}-{p.id}")
            target = dest / f"{name}.jpg"
            if target.exists():
                print(f"⚠ {target.name} 已存在，跳过（换个名字：--ids {no_s}:新名字）")
                continue
            src = SOURCES[p.source](self.http)
            try:
                if not src.verify(p):  # 下载前再核一次许可 / 是否下架
                    print(f"⚠ #{p.no} 许可核对未通过或已下架，跳过")
                    continue
                im = Image.open(io.BytesIO(self.http.get(p.download_url, timeout=90, referer=src.base + "/"))).convert("RGB")
            except Exception as e:
                print(f"⚠ #{p.no} 下载失败：{e}")
                continue
            # 先写临时文件再改名：失败不留半截文件，成功后才追加署名
            tmp = target.with_suffix(".part")
            im.save(tmp, "JPEG", quality=88, optimize=True)
            tmp.rename(target)
            self._append_credit(credits, target.name, p)
            warn = "  ⚠ " + p.notes[0] if p.notes else ""
            print(f"✓ #{p.no} → {target}  {im.width}×{im.height}  {PhotoZones(im).summary()}{warn}")

    @staticmethod
    def _safe_name(s: str) -> str:
        s = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", s).strip("-")
        return s[:60] or "photo"

    @staticmethod
    def _append_credit(credits: Path, filename: str, p: Photo):
        """沿用现有 CREDITS 的「文件 / 摄影师 / 原图」三列；不存在则建表头。"""
        if not credits.exists():
            credits.write_text("# 照片来源\n\n由 scripts/fetch_photos.py 获取。许可以各行图源为准："
                               "沙沙野为平台声明的 CC0，Burst 为逐张核对的 CC0；均可商用，署名非必需，此处保留以便追溯。\n\n"
                               "| 文件 | 摄影师 | 原图 |\n|---|---|---|\n", encoding="utf-8")
        line = f"| `{filename}` | {p.author} | {p.source} · [{p.license}]({p.page_url}) |\n"
        with credits.open("a", encoding="utf-8") as f:
            f.write(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="搜索候选并生成联系表")
    s.add_argument("queries", nargs="+", help="关键词，可多个（ssyer 用中文、burst 用英文效果最好）")
    s.add_argument("--source", choices=["ssyer", "burst", "all"], default="all")
    s.add_argument("--count", type=int, default=12, help="每个图源、每个关键词最多取多少张（默认 12）")
    s.add_argument("--orientation", choices=["landscape", "portrait", "any"], default="any")
    s.add_argument("--out", default="./photo-candidates", help="候选输出目录")
    k = sub.add_parser("pick", help="按编号下载选中的图片并写 CREDITS")
    k.add_argument("--from", dest="cand", required=True, help="search 的输出目录")
    k.add_argument("--ids", required=True, help="编号列表，如 3,7,12 或 3:cover,7:tea")
    k.add_argument("--dest", required=True, help="目标 photos 目录")
    a = ap.parse_args()
    f = PhotoFetcher()
    if a.cmd == "search":
        srcs = list(SOURCES) if a.source == "all" else [a.source]
        f.search(a.queries, srcs, a.count, a.orientation, Path(a.out).expanduser())
    else:
        f.pick(Path(a.cand).expanduser(), a.ids, Path(a.dest).expanduser())


if __name__ == "__main__":
    main()
