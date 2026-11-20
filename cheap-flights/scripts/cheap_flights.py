#!/usr/bin/env python3
"""查询指定出发地在日期范围内的国内特价机票，多来源比价后输出 Markdown 表格。

数据来源（均为各平台网页使用的非公开接口，无需登录）：
- 携程 fuzzySearch：全国目的地的最低价作为主列表；也用于返程反查和往返套票
- 飞猪 rule/domestic：热门航线特价，最多约覆盖 1 个月，仅用于去程比价
- 去哪儿 lowFlightInterface：首页各分类热门低价单程（需游客 cookie），仅用于去程比价
- 同程 getpricecalendar：单航线价格日历，去程与返程逐条比价

默认输出往返表：每个目的地只给往返总价最低的一种买法——携程往返套票（1 行）或
两张单程（2 行，去程、返程日期一起选，平台可不同），按总价从低到高排序；
--no-return 时输出单程表，一个目的地一行，按单程价从低到高排序。
任一来源失败不影响其他来源，失败状态写在表格下方。仅依赖 Python 3.9+ 标准库。
"""
import argparse
import calendar
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
WEEKDAYS = "一二三四五六日"
CN_NUM = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


class Http:
    """统一的 HTTP 请求封装，固定超时与 UA，返回文本。"""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def request(self, url: str, body: Optional[dict] = None,
                headers: Optional[dict] = None) -> str:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        h = {"user-agent": UA}
        if body is not None:
            h["content-type"] = "application/json"
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=h)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8")

    def json(self, url: str, body: Optional[dict] = None,
             headers: Optional[dict] = None) -> dict:
        return json.loads(self.request(url, body, headers))


@dataclass
class Fare:
    """某来源给出的一条最低价。discount 为"几折"，来源不提供时为 None。"""
    source: str
    price: int
    date: str
    discount: Optional[float] = None
    flight: str = ""
    link: str = ""
    dtime: str = ""   # 起飞时间 YYYY-MM-DD HH:MM，来源不提供时为空（飞猪）
    atime: str = ""   # 到达时间 YYYY-MM-DD HH:MM


@dataclass
class Plan:
    """一种往返买法。kind="combo" 为携程往返套票（go/back 的 price 无意义，只看 total）；
    kind="two" 为两张单程，go、back 各自来自最便宜的平台。"""
    kind: str
    total: int
    go: Fare
    back: Fare
    go_remark: str
    back_remark: str
    link: str = ""   # 套票购票链接；两张单程用各自 Fare.link


@dataclass
class Route:
    """一个航段（去程：出发地→目的地；返程：目的地→出发地），汇总各来源报价。
    航班结构信息（中转/经停、机场）来自携程。"""
    dest_code: str
    dest_name: str
    province: str = ""
    depart_label: str = ""
    ctrip_flights: List[str] = field(default_factory=list)
    transfer_city: str = ""      # 需换乘的中转城市
    stop_city: str = ""          # 同一航班的经停城市
    fares: List[Fare] = field(default_factory=list)
    back: Optional["Route"] = None   # 携程反查的返程航段，仅去程 Route 使用
    plan: Optional[Plan] = None      # 往返总价最低的买法
    alt: Optional[Plan] = None       # 另一种买法，用于对比

    @property
    def ctrip_direct(self) -> bool:
        return bool(self.ctrip_flights) and not self.transfer_city

    def best(self) -> Optional[Fare]:
        # 同价时日期早的优先，再同价时携程优先（携程有完整航班结构）
        if not self.fares:
            return None
        return sorted(self.fares, key=lambda f: (f.price, f.date, f.source != "携程"))[0]


class DateRange:
    """把"近一个月""近两周""2026-11-01~2026-12-15"等解析为起止日期。"""

    @staticmethod
    def add_months(d: date, n: int) -> date:
        m = d.month - 1 + n
        y, m = d.year + m // 12, m % 12 + 1
        return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))

    @classmethod
    def parse(cls, text: str, today: date) -> Tuple[date, date]:
        t = text.strip().replace(" ", "")
        m = re.fullmatch(r"(\d{4}-\d{1,2}-\d{1,2})[~～至到,](\d{4}-\d{1,2}-\d{1,2})", t)
        if m:
            b, e = (datetime.strptime(x, "%Y-%m-%d").date() for x in m.groups())
            b = max(b, today)
            if e < b:
                raise ValueError(f"日期范围无效或已过期：{text}")
            return b, e
        m = re.fullmatch(r"(?:近|最近|未来)?(\d+|[一两二三四五六])个?(月|周|星期|天|日)(?:内)?", t)
        if not m:
            raise ValueError(f"无法识别的日期范围：{text}（示例：近一个月、近两周、2026-11-01~2026-12-15）")
        num = int(m.group(1)) if m.group(1).isdigit() else CN_NUM[m.group(1)]
        unit = m.group(2)
        if unit == "月":
            end = cls.add_months(today, num) - timedelta(days=1)
        elif unit in ("周", "星期"):
            end = today + timedelta(days=7 * num - 1)
        else:
            end = today + timedelta(days=num - 1)
        return today, end

    @staticmethod
    def parse_stay(text: str) -> Tuple[int, int]:
        """"2-5" → (2, 5)，"3" → (3, 3)：返程日期减去程日期的天数范围。"""
        m = re.fullmatch(r"(\d+)(?:[-~～](\d+))?", text.strip())
        if not m:
            raise ValueError(f"无法识别的停留天数：{text}（示例：2-5、3）")
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if hi < lo or hi > 30:
            raise ValueError(f"停留天数无效：{text}（需要 最少≤最多≤30）")
        return lo, hi


class CtripSource:
    """携程：城市代码解析 + 全国目的地最低价（主列表）。"""
    BASE = "https://m.ctrip.com/restapi/soa2/19728/"
    HEADERS = {"origin": "https://flights.ctrip.com", "referer": "https://flights.ctrip.com/"}
    HEAD = {"cid": "", "ctok": "", "cver": "1.0", "lang": "01", "sid": "8888",
            "syscode": "999", "auth": "", "xsid": "", "extension": []}

    def __init__(self, http: Http):
        self.http = http
        self.cities: Dict[str, str] = {}  # 城市名 → 三字码，resolve_city 时加载
        # 航空公司两字码 → 简称，每次查询顺带记录；同程、去哪儿只给航班号，靠它换算
        self.airlines: Dict[str, str] = {}

    def code_of(self, city_name: str) -> Optional[str]:
        return self.cities.get(city_name)

    @staticmethod
    def short_airline(name: str) -> str:
        # 海航系简称带集团前缀（"新海航|首都航空"），只留后半段并缩成"首都航"
        return name.split("|")[-1].replace("航空", "航") if "|" in name else name

    def airline_of(self, flight: str) -> str:
        """"NS3276+NS3303" → "河北航"；多段不同公司用 + 连接，查不到时显示两字码。"""
        out: List[str] = []
        for no in filter(None, flight.split("+")):
            n = self.airlines.get(no[:2], no[:2])
            if n not in out:
                out.append(n)
        return "+".join(out) or "—"

    def resolve_city(self, text: str) -> Tuple[str, str]:
        """城市名或三字码 → (三字码, 城市名)。名称取自携程城市配置。"""
        t = text.strip()
        res = self.http.json(self.BASE + "getConfig",
                             {"keys": ["OnlineDomesticDestination"], "head": self.HEAD},
                             self.HEADERS)
        groups = json.loads(res["map"]["OnlineDomesticDestination"])
        cities = self.cities
        for g in groups:
            for c in g.get("cityList", []):
                parts = c["data"].split("|")
                cities[c["value"]] = parts[3]
        if t in cities:
            return cities[t], t
        if re.fullmatch(r"[A-Za-z]{3}", t):
            code = t.upper()
            name = next((n for n, c in cities.items() if c == code), code)
            return code, name
        fuzzy = [n for n in cities if t in n or n in t]
        if len(fuzzy) == 1:
            return cities[fuzzy[0]], fuzzy[0]
        hint = f"，候选：{'、'.join(fuzzy[:8])}" if fuzzy else ""
        raise ValueError(f"无法识别出发城市：{text}{hint}")

    def _query(self, dcs: List[dict], acs: List[dict], begin: date, end: date,
               tt: int = 1, sr: Optional[dict] = None) -> List[dict]:
        body = {"tt": tt, "source": "online_theme", "st": 18,
                "segments": [{"dcs": dcs, "acs": acs, "dow": [], "sr": sr,
                              "drl": [{"begin": begin.isoformat(), "end": end.isoformat()}],
                              "ddate": None}],
                "filters": None, "head": self.HEAD}
        res = self.http.json(self.BASE + "fuzzySearch", body, self.HEADERS)
        rows = [r for r in res.get("routes") or [] if r.get("pl") and r.get("flights")]
        for r in rows:
            for f in r["flights"]:
                al = f.get("airline") or {}
                if al.get("code") and (al.get("shortName") or al.get("name")):
                    self.airlines[al["code"]] = self.short_airline(al.get("shortName") or al["name"])
        return rows

    @staticmethod
    def port_label(port: dict) -> str:
        # 机场名常以城市名开头（"揭阳潮汕"），去掉重复部分显示为"揭阳 潮汕"
        city, name = port["cityName"], port["name"]
        if name.startswith(city) and len(name) > len(city):
            name = name[len(city):]
        return f"{city} {name}{port.get('terminal', '')}"

    def _route(self, r: dict, city: dict) -> Route:
        p, fl = r["pl"][0], r["flights"]
        route = Route(dest_code=city["code"], dest_name=city["name"],
                      province=city.get("provinceName", ""),
                      depart_label=self.port_label(fl[0]["dport"]),
                      ctrip_flights=[f["flightNo"] for f in fl])
        if len(fl) > 1:
            route.transfer_city = "、".join(f["aport"]["cityName"] for f in fl[:-1])
        route.stop_city = "、".join(s["name"] for f in fl for s in (f.get("stops") or []))
        # 去掉携程链接里的埋点参数，保留日期与价格排序
        link = p.get("jumpUrl", "").split("&lowprice")[0]
        route.fares.append(Fare("携程", int(p["price"]), p["departDate"], None,
                                "+".join(route.ctrip_flights), link,
                                fl[0]["dtime"][:16], fl[-1]["atime"][:16]))
        return route

    def search(self, code: str, name: str, begin: date, end: date) -> List[Route]:
        rows = self._query([{"ct": 1, "code": code, "name": name}],
                           [{"ct": 3, "code": "DOMESTIC_ALL", "name": "全中国"}], begin, end)
        return [self._route(r, r["arriveCity"]) for r in rows]

    def reverse(self, home: str, home_name: str, codes: List[str],
                begin: date, end: date) -> Dict[str, Route]:
        """多个城市 → 出发地的单程最低价，一次请求；返回 {城市三字码: 返程 Route}。
        Route.dest_* 填出发地本身，表示返程目的地。"""
        rows = self._query([{"ct": 1, "code": c, "name": c} for c in codes],
                           [{"ct": 1, "code": home, "name": home_name}], begin, end)
        return {r["departCity"]["code"]: self._route(r, r["arriveCity"]) for r in rows}

    @staticmethod
    def remark_of(fl: List[dict]) -> str:
        """一段行程的航班结构：直飞 / 直飞，经停X / 经X中转。"""
        if len(fl) > 1:
            return f"经{'、'.join(f['aport']['cityName'] for f in fl[:-1])}中转"
        stops = [s["name"] for s in (fl[0].get("stops") or [])]
        return f"直飞，经停{'、'.join(stops)}" if stops else "直飞"

    def combos(self, code: str, name: str, begin: date, end: date,
               stay: Tuple[int, int], direct_only: bool = False) -> Dict[str, Plan]:
        """全国目的地的往返套票最低价。接口的 sr 按"含首尾天数"计，比停留天数多 1；
        返回结果再按实际停留天数过滤一遍，防止接口口径变化导致错位。"""
        rows = self._query([{"ct": 1, "code": code, "name": name}],
                           [{"ct": 3, "code": "DOMESTIC_ALL", "name": "全中国"}], begin, end,
                           tt=2, sr={"min": stay[0] + 1, "max": stay[1] + 1})
        out = {}
        for r in rows:
            p = r["pl"][0]
            if not p.get("returnDate"):
                continue
            days = (date.fromisoformat(p["returnDate"]) - date.fromisoformat(p["departDate"])).days
            if not stay[0] <= days <= stay[1]:
                continue
            go = [f for f in r["flights"] if f.get("segment") == 1]
            back = [f for f in r["flights"] if f.get("segment") == 2]
            if not go or not back:
                continue
            # 直飞模式：去、回两段各只有一个航班（经停仍算同一航班）
            if direct_only and (len(go) > 1 or len(back) > 1):
                continue

            def leg(fl: List[dict], d: str) -> Fare:
                return Fare("携程", 0, d, None, "+".join(f["flightNo"] for f in fl), "",
                            fl[0]["dtime"][:16], fl[-1]["atime"][:16])

            out[r["arriveCity"]["code"]] = Plan(
                "combo", int(p["price"]), leg(go, p["departDate"]), leg(back, p["returnDate"]),
                self.remark_of(go), self.remark_of(back), p.get("jumpUrl", "").split("&lowprice")[0])
        return out


class FliggySource:
    """飞猪：热门航线特价（JSONP）。链接会跳登录页，因此只用于比价不给链接。"""
    URL = ("https://r.fliggy.com/rule/domestic?routes={code}-&startDate={b}"
           "&endDate={e}&flag=1&ruleId=99&callback=cb")

    def __init__(self, http: Http):
        self.http = http
        self.names: Dict[str, str] = {}  # 三字码 → 城市名，供飞猪独有目的地展示

    def search(self, code: str, begin: date, end: date) -> Dict[str, Fare]:
        text = self.http.request(self.URL.format(code=code, b=begin, e=end),
                                 headers={"referer": "https://www.fliggy.com/jipiao/"})
        data = json.loads(re.sub(r"\);?\s*$", "", re.sub(r"^[^(]*\(", "", text, count=1)))
        items = self._find_items(data) or []
        fares = {}
        for x in items:
            d = x.get("depDate", "")
            if not x.get("price") or x.get("soldOut") or not (begin.isoformat() <= d <= end.isoformat()):
                continue
            fares[x["arrCode"]] = Fare("飞猪", int(x["price"]), d, x.get("discount"))
            self.names[x["arrCode"]] = x.get("arrName") or x["arrCode"]
        return fares

    def _find_items(self, o):
        # 响应结构嵌套层级不固定，递归找到含 arrCode 的列表
        if isinstance(o, list) and o and isinstance(o[0], dict) and "arrCode" in o[0]:
            return o
        if isinstance(o, dict):
            o = list(o.values())
        if isinstance(o, list):
            for v in o:
                r = self._find_items(v)
                if r:
                    return r
        return None


class QunarSource:
    """去哪儿：H5 首页"超值低价"各分类的热门低价单程。接口校验游客 cookie，
    先依次访问首页与机票页拿到 QN1/QN99 等 cookie（缺一步都返回空），再逐个分类查询。
    返回字段标 priceIncludeTax=True 但 tax=0，实测与携程不含税票面价一致，按不含税处理。"""
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"
    WARMUP = ["https://touch.qunar.com/", "https://touch.qunar.com/h5/flight/"]
    API = "https://touch.qunar.com/lowFlightInterface/api/getAirLine"
    TABS = ["国内热门", "国内降价榜", "国内低价榜", "海边浪一浪", "拥抱自然",
            "文艺古镇", "草原风光", "人文历史", "随机旅游", ""]
    LINK = "https://touch.qunar.com/lowFlight/flightList?dep={d}&arr={a}&flightType=1&startDate={date}"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def search(self, city: str, begin: date, end: date) -> Dict[str, Fare]:
        """{到达城市名: 最低价}。按城市名合并：去哪儿用机场码（PEK），携程用城市码（BJS）。"""
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        for u in self.WARMUP:
            op.open(urllib.request.Request(u, headers={"user-agent": self.UA}), timeout=self.timeout).read()
        out: Dict[str, Fare] = {}
        for tab in self.TABS:
            body = {"b": {"locationAirCity": city, "locationCity": city, "timeout": 5000,
                          "holiday": "default", "simpleData": "yes", "t": "f_urInfo_superLow_data",
                          "cat": "touch_flight_home", "tabName": tab}, "c": {}}
            req = urllib.request.Request(self.API, data=json.dumps(body).encode("utf-8"),
                                         headers={"user-agent": self.UA, "content-type": "application/json",
                                                  "referer": self.WARMUP[1]})
            with op.open(req, timeout=self.timeout) as resp:
                items = (json.loads(resp.read()).get("data") or {}).get("domList") or []
            for x in items:
                # 只要国内单程；列表里混有往返（flightType=2）和周边机场出发（如义乌）的条目
                if x.get("inter") or not x.get("price") or x.get("flightType") != 1:
                    continue
                if x.get("depCity") != city or not (begin.isoformat() <= x.get("date", "") <= end.isoformat()):
                    continue
                m = re.match(r"([\d.]+)折", x.get("discount") or "")
                f = Fare("去哪儿", int(x["price"]), x["date"], float(m.group(1)) if m else None,
                         x.get("flightNo", ""),
                         self.LINK.format(d=urllib.parse.quote(city), a=urllib.parse.quote(x["arrCity"]),
                                          date=x["date"]),
                         (x.get("depTime") or "")[:16], (x.get("arrTime") or "")[:16])
                k = x["arrCity"]
                if k not in out or (f.price, f.date) < (out[k].price, out[k].date):
                    out[k] = f
        return out


class TongchengSource:
    """同程：单航线价格日历，取区间内最低价。"""
    URL = "https://www.ly.com/flights/api/query/getpricecalendar"
    HEADERS = {"referer": "https://www.ly.com/flights/home", "tcsessionid": "nologin-1",
               "refid": "0", "tcsectoken": ""}
    LINK = "https://www.ly.com/flights/itinerary/oneway/{d}-{a}?date={date}"

    def __init__(self, http: Http):
        self.http = http

    def calendar(self, dep: str, arr: str, begin: date, end: date) -> List[Fare]:
        """区间内每天的最低价；同一次请求供本地按任意日期窗口筛选。"""
        body = {"IsFromPhoenix": 1, "StartPort": dep, "EndPort": arr,
                "QueryBegDate": begin.isoformat(), "QueryEndDate": end.isoformat(),
                "QueryType": 1, "travelTypes": [1], "flat": 1, "plat": 1,
                "isFromKylin": 1, "refid": "0"}
        res = self.http.json(self.URL, body, self.HEADERS)
        out = []
        for x in (res.get("body") or {}).get("fzpriceinfos") or []:
            if x.get("price", 0) <= 0:
                continue
            disc = x.get("discount")
            out.append(Fare("同程", int(x["price"]), x["flydate"],
                            round(disc / 10, 1) if disc else None, x.get("flightno", ""),
                            self.LINK.format(d=dep, a=arr, date=x["flydate"]),
                            x.get("flytime", "")[:16], x.get("arrtime", "")[:16]))
        return out

    @staticmethod
    def lowest(fares: List[Fare], begin: date, end: date) -> Optional[Fare]:
        inside = [f for f in fares if begin.isoformat() <= f.date <= end.isoformat()]
        return min(inside, key=lambda f: (f.price, f.date)) if inside else None


class CheapFlights:
    """编排四个来源：携程出主列表，飞猪/去哪儿/同程补充去程比价。
    开启返程时，用携程反查 + 同程返程价格日历拿返程报价，与去程报价一起挑出总价最低的
    两张单程（日期一起选，平台可不同），再与携程往返套票比，留下总价最低的一种买法。"""
    WORKERS = 6

    def __init__(self, city: str, range_text: str, top: int, direct_only: bool,
                 with_return: bool = True, stay: str = "2-5", today: Optional[date] = None):
        self.http = Http()
        self.ctrip = CtripSource(self.http)
        self.fliggy = FliggySource(self.http)
        self.qunar = QunarSource()
        self.tongcheng = TongchengSource(self.http)
        self.city, self.top, self.direct_only, self.with_return = city, top, direct_only, with_return
        self.stay = DateRange.parse_stay(stay)
        self.today = today or date.today()
        self.begin, self.end = DateRange.parse(range_text, self.today)
        self.status: Dict[str, str] = {}

    def run(self) -> Tuple[str, str, List[Route]]:
        code, name = self.ctrip.resolve_city(self.city)
        try:
            routes = self.ctrip.search(code, name, self.begin, self.end)
            self.status["携程"] = f"✅ {len(routes)} 条航线"
        except Exception as e:  # 主来源失败也继续用其他来源
            routes, self.status["携程"] = [], f"❌ {type(e).__name__}"
        by_code = {r.dest_code: r for r in routes}

        try:
            fz = self.fliggy.search(code, self.begin, self.end)
            self.status["飞猪"] = f"✅ {len(fz)} 条热门航线（仅去程）"
        except Exception as e:
            fz, self.status["飞猪"] = {}, f"❌ {type(e).__name__}"
        if not self.direct_only:  # 飞猪无航班号，直飞模式下无法确认，不参与
            for c, f in fz.items():
                if c not in by_code:
                    by_code[c] = Route(dest_code=c, dest_name=self.fliggy.names.get(c, c))
                by_code[c].fares.append(f)

        try:
            qn = self.qunar.search(name, self.begin, self.end)
            self.status["去哪儿"] = f"✅ {len(qn)} 条热门航线（仅去程）"
        except Exception as e:
            qn, self.status["去哪儿"] = {}, f"❌ {type(e).__name__}"
        by_name = {r.dest_name: r for r in by_code.values()}
        for city_name, f in qn.items():
            r = by_name.get(city_name)
            if r is None:
                # 携程主列表没有的目的地：用携程城市配置换成三字码，换不到就无法比价和查返程
                c = self.ctrip.code_of(city_name)
                if not c or self.direct_only:
                    continue
                r = by_code.setdefault(c, Route(dest_code=c, dest_name=city_name))
                by_name[city_name] = r
            # 直飞模式只接受与携程直飞同航班号的报价
            if self.direct_only and f.flight not in r.ctrip_flights:
                continue
            r.fares.append(f)

        cands = [r for r in by_code.values() if r.fares]
        if self.direct_only:
            cands = [r for r in cands if r.ctrip_direct]
        go_key = lambda r: (r.best().price, r.best().date)
        # 同程逐条请求成本高：只对当前最便宜的 2N 个目的地比价；往返按总价重排也在这 2N 内
        cands.sort(key=go_key)
        cands = cands[: self.top * 2]
        go_cals = self._compare_tongcheng(code, cands)
        for r in cands:
            if not r.depart_label:
                r.depart_label = name

        if not self.with_return:
            cands.sort(key=go_key)
            return code, name, cands[: self.top]
        self._plan_round_trips(code, name, cands, go_cals)
        priced = [r for r in cands if r.plan]
        if not priced:
            # 返程来源全部失败：退回单程表，至少给出去程结果
            self.with_return = False
            self.status["往返"] = "❌ 没有返程报价，已改为单程表"
            cands.sort(key=go_key)
            return code, name, cands[: self.top]
        if len(priced) < len(cands):
            self.status["无往返报价"] = f"{len(cands) - len(priced)} 个目的地"
        priced.sort(key=lambda r: (r.plan.total, r.plan.go.date))
        return code, name, priced[: self.top]

    def _compare_tongcheng(self, dep: str, routes: List[Route]) -> Dict[str, List[Fare]]:
        """同程去程比价；返回每个目的地的整段价格日历，供往返挑日期复用。"""
        def job(r: Route):
            return r, self.tongcheng.calendar(dep, r.dest_code, self.begin, self.end)

        cals: Dict[str, List[Fare]] = {}
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=self.WORKERS) as pool:
            for fut in [pool.submit(job, r) for r in routes]:
                try:
                    r, cal = fut.result()
                    ok += 1
                except Exception:
                    fail += 1
                    continue
                # 直飞模式只接受与携程直飞同航班号的同程报价
                if self.direct_only:
                    cal = [f for f in cal if f.flight in r.ctrip_flights]
                cals[r.dest_code] = cal
                fare = self.tongcheng.lowest(cal, self.begin, self.end)
                if fare:
                    r.fares.append(fare)
        if ok == 0 and fail:
            self.status["同程"] = "❌ 全部请求失败"
        else:
            self.status["同程"] = f"✅ 比价 {ok} 条" + (f"，失败 {fail} 条" if fail else "")
        return cals

    def _window(self, r: Route) -> Tuple[date, date]:
        """返程日期窗口：去程日期 + 停留天数，允许超出查询区间。"""
        g = date.fromisoformat(r.best().date)
        return g + timedelta(days=self.stay[0]), g + timedelta(days=self.stay[1])

    @staticmethod
    def _daily(fares: List[Fare]) -> Dict[str, Fare]:
        """同一天多家报价只留最便宜的；同价时携程优先。"""
        out: Dict[str, Fare] = {}
        for f in sorted(fares, key=lambda f: (f.price, f.source != "携程")):
            out.setdefault(f.date, f)
        return out

    def _plan_round_trips(self, home: str, home_name: str, routes: List[Route],
                          go_cals: Dict[str, List[Fare]]) -> None:
        lo, hi = self.stay
        # 携程反查按去程最低价日期分组：同一天出发的目的地共用一个返程窗口，一次请求查完
        groups: Dict[str, List[Route]] = {}
        for r in routes:
            groups.setdefault(r.best().date, []).append(r)

        def ctrip_job(rs: List[Route]):
            b, e = self._window(rs[0])
            return self.ctrip.reverse(home, home_name, [r.dest_code for r in rs], b, e)

        def tc_job(r: Route):
            # 返程日历覆盖所有可能的返程日期，供去程、返程日期一起挑
            return self.tongcheng.calendar(r.dest_code, home, self.begin + timedelta(days=lo),
                                           self.end + timedelta(days=hi))

        with ThreadPoolExecutor(max_workers=self.WORKERS) as pool:
            combo_fut = pool.submit(self.ctrip.combos, home, home_name, self.begin, self.end,
                                    self.stay, self.direct_only)
            ctrip_futs = [pool.submit(ctrip_job, rs) for rs in groups.values()]
            tc_futs = [(r, pool.submit(tc_job, r)) for r in routes]
            ctrip_back: Dict[str, Route] = {}
            cfail = 0
            for f in ctrip_futs:
                try:
                    ctrip_back.update(f.result())
                except Exception:
                    cfail += 1
            tc_back: Dict[str, List[Fare]] = {}
            tfail = 0
            for r, f in tc_futs:
                try:
                    tc_back[r.dest_code] = f.result()
                except Exception:
                    tfail += 1
            try:
                combos = combo_fut.result()
                self.status["携程往返"] = f"✅ {len(combos)} 条"
            except Exception as e:
                combos, self.status["携程往返"] = {}, f"❌ {type(e).__name__}"

        c_hit = t_hit = 0
        for r in routes:
            back = ctrip_back.get(r.dest_code)
            if back and self.direct_only and not back.ctrip_direct:
                back = None
            if back:
                c_hit += 1
            else:
                back = Route(dest_code=home, dest_name=home_name)
            tcal = tc_back.get(r.dest_code) or []
            if tcal:
                t_hit += 1
            if self.direct_only:
                tcal = [f for f in tcal if f.flight in back.ctrip_flights]
            back.fares.extend(tcal)

            # 两张单程：去程每天最低 × 返程每天最低，在停留天数内挑总价最低的组合
            go_by_day = self._daily(go_cals.get(r.dest_code, []) + [f for f in r.fares if f.source != "同程"])
            back_by_day = self._daily(back.fares)
            two = None
            for d, gf in sorted(go_by_day.items()):
                for k in range(lo, hi + 1):
                    bf = back_by_day.get((date.fromisoformat(d) + timedelta(days=k)).isoformat())
                    if bf and (two is None or gf.price + bf.price < two.total):
                        two = Plan("two", gf.price + bf.price, gf, bf,
                                   Renderer.remark(r, gf), Renderer.remark(back, bf))
            plans = [p for p in (combos.get(r.dest_code), two) if p]
            # 同价时优先往返套票：一个链接就能买完
            plans.sort(key=lambda p: (p.total, p.kind != "combo"))
            r.plan = plans[0] if plans else None
            r.alt = plans[1] if len(plans) > 1 else None

        n = len(routes)
        self.status["返程"] = (f"携程 {'❌' if groups and cfail == len(groups) else '✅'} {c_hit}/{n}"
                             + (f"（失败 {cfail} 组）" if cfail else "")
                             + f"、同程 {'❌' if n and tfail == n else '✅'} {t_hit}/{n}"
                             + (f"（失败 {tfail} 条）" if tfail else ""))


class Renderer:
    """把结果渲染为 Markdown。"""
    KIND = {"combo": "往返套票", "two": "两张单程"}

    @staticmethod
    def day(d: str) -> str:
        dt = datetime.strptime(d, "%Y-%m-%d").date()
        return f"{dt:%m-%d} 周{WEEKDAYS[dt.weekday()]}"

    @classmethod
    def when(cls, f: Fare) -> str:
        """"10-25 周日 22:15→00:20(+1)"；来源不给时间时注明。"""
        if not f.dtime:
            return f"{cls.day(f.date)}（时间未知）"
        s = f"{cls.day(f.dtime[:10])} {f.dtime[11:16]}"
        if f.atime:
            span = (date.fromisoformat(f.atime[:10]) - date.fromisoformat(f.dtime[:10])).days
            s += f"→{f.atime[11:16]}" + (f"(+{span})" if span > 0 else "")
        return s

    @staticmethod
    def remark(r: Route, best: Fare) -> str:
        # 中转/经停信息来自携程，只有展示的航班与携程一致时才可确认
        same = best.source == "携程" or (best.flight and best.flight in r.ctrip_flights)
        if not r.ctrip_flights or not same:
            return "直飞/中转未知"
        if r.transfer_city:
            return f"经{r.transfer_city}中转"
        if r.stop_city:
            return f"直飞，经停{r.stop_city}"
        return "直飞"

    @staticmethod
    def place(name: str, province: str) -> str:
        return f"{name}（{province}）" if province else name

    @staticmethod
    def stay_days(p: Plan) -> int:
        return (date.fromisoformat(p.back.date) - date.fromisoformat(p.go.date)).days

    @classmethod
    def leg(cls, app: "CheapFlights", tag: str, f: Fare, remark: str) -> str:
        """"去 11-05 周四 21:55→00:05(+1) 春秋 9C6354 直飞"；飞猪无航班号时航空公司、航班都写"—"。"""
        airline = app.ctrip.airline_of(f.flight) if f.flight else "—"
        return f"{tag} {cls.when(f)} {airline} {f.flight or '—'} {remark}"

    @staticmethod
    def link(tag: str, f: Fare) -> str:
        # 飞猪链接会跳淘宝登录，不提供
        return f"[{tag}·{f.source}]({f.link})" if f.link else f"{tag}·{f.source}无链接"

    @classmethod
    def one_way(cls, app: "CheapFlights", name: str, routes: List[Route]) -> List[str]:
        direct = "，仅直飞" if app.direct_only else ""
        # 列与往返表一一对应：去 / 回 → 去，往返总价 → 价格，另一种买法 → 其他来源比价
        lines = [f"**{name}出发特价机票（{app.begin:%Y-%m-%d}～{app.end:%m-%d}，单程，不含税，"
                 f"按价格从低到高{direct}）**", "",
                 "| # | 目的地 | 买法 | 去 | 价格 | 平台 | 其他来源比价 | 链接 |",
                 "|" + "---|" * 8]
        for i, r in enumerate(routes, 1):
            b = r.best()
            others = sorted((f for f in r.fares if f is not b), key=lambda f: f.price)
            cmp_ = "、".join(f"{f.source} ¥{f.price}" + ("" if f.date == b.date else f"（{f.date[5:]}）")
                             for f in others) or "—"
            # 折扣只有部分来源给，跟在平台后面，不单独占列
            platform = f"{b.source} {b.discount:g}折" if b.discount else b.source
            # 飞猪最低时没有可用链接，借用同日期优先的其他来源链接
            link = cls.link("去", b) if b.link else next(
                (cls.link("去", f) for f in others if f.link), cls.link("去", b))
            lines.append(f"| {i} | {cls.place(r.dest_name, r.province)} | 单程 | "
                         f"{cls.leg(app, '去', b, cls.remark(r, b))} | **¥{b.price}** | {platform} | "
                         f"{cmp_} | {link} |")
        return lines

    @classmethod
    def round_trip(cls, app: "CheapFlights", name: str, routes: List[Route]) -> List[str]:
        lo, hi = app.stay
        stay = f"{lo}–{hi}" if lo != hi else f"{lo}"
        direct = "，仅直飞" if app.direct_only else ""
        lines = [f"**{name}往返特价机票（去程 {app.begin:%Y-%m-%d}～{app.end:%m-%d}，停留 {stay} 天，"
                 f"不含税，按往返总价从低到高{direct}）**", "",
                 "| # | 目的地 | 买法 | 去 / 回 | 往返总价 | 平台 | 另一种买法 | 链接 |",
                 "|" + "---|" * 8]
        for i, r in enumerate(routes, 1):
            p = r.plan
            # 玩几天 = 返程日期 − 去程日期，按实际选中的日期算
            dest = f"{cls.place(r.dest_name, r.province)} 玩{cls.stay_days(p)}天"
            alt = f"{cls.KIND[r.alt.kind]} ¥{r.alt.total}" if r.alt else "—"
            go, back = cls.leg(app, "去", p.go, p.go_remark), cls.leg(app, "回", p.back, p.back_remark)
            if p.kind == "combo":
                # 套票也拆成去、回两行（与两张单程同一格式）；一张票一个链接，回程行写"同上"
                lines.append(f"| {i} | {dest} | 往返套票 | {go} | **¥{p.total}** | 携程 | {alt} | "
                             f"[携程往返]({p.link}) |")
                lines.append(f"| {i} | {dest} | ↳ | {back} | | | | 同上 |")
                continue
            lines.append(f"| {i} | {dest} | 两张单程 | {go} | **¥{p.total}** | "
                         f"{cls.platform(p.go)} | {alt} | {cls.link('去', p.go)} |")
            lines.append(f"| {i} | {dest} | ↳ | {back} | | "
                         f"{cls.platform(p.back)} | | {cls.link('回', p.back)} |")
        return lines

    @staticmethod
    def platform(f: Fare) -> str:
        """两张单程的"平台"格：来源 + 单价，有折扣时附上，如"同程 ¥278 2.4折"。"""
        return f"{f.source} ¥{f.price}" + (f" {f.discount:g}折" if f.discount else "")

    @classmethod
    def markdown(cls, app: "CheapFlights", name: str, routes: List[Route]) -> str:
        lines = (cls.round_trip if app.with_return else cls.one_way)(app, name, routes)
        status = " · ".join(f"返程：{v}" if k == "返程" else f"{k} {v}" for k, v in app.status.items())
        lines += ["", f"> 已查来源：{status}；价格为不含税起价，以下单页为准。"]
        return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="国内特价机票多来源比价")
    ap.add_argument("city", help="出发城市名或三字码，如 杭州 / HGH")
    ap.add_argument("range", nargs="?", default="近一个月",
                    help="去程日期范围：近一个月 / 近两个月 / 近两周 / 2026-11-01~2026-12-15")
    ap.add_argument("--top", type=int, default=20, help="输出目的地个数，默认 20")
    ap.add_argument("--direct", action="store_true", help="只看直飞（去程、返程都要求直飞）")
    ap.add_argument("--no-return", action="store_true", help="只查单程，一个目的地一行")
    ap.add_argument("--stay", default="2-5", help="往返停留天数，默认 2-5")
    ap.add_argument("--today", help="调试用：指定今天日期 YYYY-MM-DD")
    args = ap.parse_args()
    try:
        today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else None
        app = CheapFlights(args.city, args.range, max(1, args.top), args.direct,
                           not args.no_return, args.stay, today)
        _, name, routes = app.run()
    except ValueError as e:
        print(f"FAIL: {e}")
        return 2
    if not routes:
        print(f"FAIL: 没有查到结果；来源状态：{app.status}")
        return 1
    print(Renderer.markdown(app, name, routes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
