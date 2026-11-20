#!/usr/bin/env python3
"""feishu-group-notify — 飞书群通知 CLI（子命令分层，脚本不交互）。

用法:
  python3 scripts/feishu-notify.py init
  python3 scripts/feishu-notify.py init --from dsh|openclaw
  python3 scripts/feishu-notify.py list
  python3 scripts/feishu-notify.py bot add --name <名> --app-id <cli_xxx> --secret '<secret>'
  python3 scripts/feishu-notify.py check [--bot <app_id>]
  python3 scripts/feishu-notify.py chats [--bot <app_id>]  # 不传 --bot 列出全部 bot 的群
  python3 scripts/feishu-notify.py send --to <群名> --content '<纯文本或 JSON>' [--msg-type text|post] [--bot <app_id>]
  python3 scripts/feishu-notify.py create --name <群名> [--members ou_a,ou_b] [--bot <app_id>]

1 个 bot 时 send/chats/create/check 不用 --bot；≥2 个必须 --bot <app_id>。
绑定到单个 bot 的 OK/FAIL 带 bot=<name> app_id=<cli_…>。凭据加密写入 config.json，严禁打印。
成功 stdout 以 OK 开头（send 为 OK sent: ...；create 为 OK created: ...）；失败 FAIL: <原因> 并退出码 1。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import socket
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config.json"
LEGACY_ENV_PATH = SKILL_DIR / ".env"

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
SEND_BASE = "https://open.feishu.cn/open-apis/im/v1/messages"
CHATS_URL = "https://open.feishu.cn/open-apis/im/v1/chats"
CREATE_URL = "https://open.feishu.cn/open-apis/im/v1/chats"
SCOPES_URL = "https://open.feishu.cn/open-apis/application/v6/scopes"
BOT_INFO_URL = "https://open.feishu.cn/open-apis/bot/v3/info"

SCOPE_ROWS = (
    ("tenant_access_token", "获取应用身份令牌"),
    ("im:message:send_as_bot", "以应用的身份发消息"),
    ("im:chat:readonly", "获取群组信息"),
    ("im:chat:create", "创建群组"),
)

SCOPE_ALIASES = {
    "im:message:send_as_bot": ("im:message:send_as_bot", "im:message"),
    "im:chat:readonly": ("im:chat:readonly", "im:chat:read", "im:chat"),
    "im:chat:create": ("im:chat:create", "im:chat"),
}


class FeiShuNotifyError(Exception):
    """可预期错误，CLI 转为 FAIL。"""


class ConfigStore:
    PLACEHOLDER_NAME = "openclaw"

    @staticmethod
    def tag(bot: dict) -> str:
        return f"bot={bot.get('name') or '?'} app_id={bot.get('app_id') or '?'}"

    @staticmethod
    def first_ou(values) -> str:
        for item in values or []:
            if isinstance(item, str) and item.startswith("ou_"):
                return item
        return ""

    @staticmethod
    def available(bots: list[dict]) -> str:
        if not bots:
            return "available: （无）"
        rows = [f"- {b.get('name')}  app_id={b.get('app_id')}" for b in bots]
        return "available:\n" + "\n".join(rows)

    @staticmethod
    def encrypt(plain: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            f"{socket.gethostname()}:{os.getuid()}".encode(),
            salt,
            200000,
            dklen=32,
        )
        data = plain.encode("utf-8")
        stream = bytearray()
        counter = 0
        while len(stream) < len(data):
            stream.extend(
                hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha256).digest()
            )
            counter += 1
        cipher = bytes(a ^ b for a, b in zip(data, stream[: len(data)]))
        return base64.b64encode(salt + cipher).decode("ascii")

    @staticmethod
    def decrypt(blob: str) -> str:
        raw = base64.b64decode(blob)
        salt, cipher = raw[:16], raw[16:]
        key = hashlib.pbkdf2_hmac(
            "sha256",
            f"{socket.gethostname()}:{os.getuid()}".encode(),
            salt,
            200000,
            dklen=32,
        )
        stream = bytearray()
        counter = 0
        while len(stream) < len(cipher):
            stream.extend(
                hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha256).digest()
            )
            counter += 1
        return bytes(a ^ b for a, b in zip(cipher, stream[: len(cipher)])).decode(
            "utf-8"
        )

    @staticmethod
    def _legacy_env() -> dict[str, str]:
        if not LEGACY_ENV_PATH.exists():
            return {}
        out: dict[str, str] = {}
        for line in LEGACY_ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
        return out

    def get_secret(self, bot: dict) -> str:
        blob = bot.get("secret") or ""
        if not blob:
            raise FeiShuNotifyError(f"secret missing {self.tag(bot)}")
        try:
            return self.decrypt(blob)
        except Exception:
            raise FeiShuNotifyError(f"secret decrypt failed {self.tag(bot)}")

    def has_secret(self, bot: dict) -> bool:
        blob = bot.get("secret") or ""
        if not blob:
            return False
        try:
            return bool(self.decrypt(blob))
        except Exception:
            return False

    def set_secret(self, bot: dict, plain: str) -> None:
        bot["secret"] = self.encrypt(plain)

    def exists(self) -> bool:
        return CONFIG_PATH.exists()

    def load(self) -> dict:
        if not CONFIG_PATH.exists():
            raise FeiShuNotifyError("not initialized; run init")
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            raise FeiShuNotifyError(f"读取 config.json 失败 {e}")
        return self.migrate(cfg)

    def save(self, cfg: dict) -> None:
        cfg = dict(cfg)
        cfg.pop("default_bot", None)
        cfg.pop("default_app_id", None)
        cfg["version"] = 2
        CONFIG_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)

    def migrate(self, cfg: dict) -> dict:
        changed = False
        if cfg.get("default_bot") is not None or cfg.get("default_app_id") is not None:
            cfg.pop("default_bot", None)
            cfg.pop("default_app_id", None)
            changed = True
        bots = []
        for b in cfg.get("bots") or []:
            bot = dict(b)
            if "sources" not in bot:
                src = bot.pop("source", None)
                bot["sources"] = [src] if src else []
                changed = True
            else:
                bot.pop("source", None)
            if "owner_open_id" not in bot:
                ids = bot.pop("owner_open_ids", None) or []
                bot["owner_open_id"] = self.first_ou(ids)
                changed = True
            else:
                bot.pop("owner_open_ids", None)
            if not bot.get("status"):
                bot["status"] = "unknown"
                changed = True
            if not bot.get("secret"):
                env = self._legacy_env()
                app_id = bot.get("app_id") or ""
                name = bot.get("name") or ""
                blob = env.get(
                    "FEISHU_SECRET_" + re.sub(r"[^A-Za-z0-9_]", "_", app_id)
                ) or env.get("FEISHU_SECRET_" + re.sub(r"[^A-Za-z0-9_]", "_", name))
                if blob:
                    bot["secret"] = blob
                    changed = True
            bots.append(bot)
        cfg["bots"] = bots
        if cfg.get("version") != 2:
            cfg["version"] = 2
            changed = True
        if changed:
            self.save(cfg)
        # all([]) is True, so require at least one migrated bot before
        # removing the legacy credential source.
        if LEGACY_ENV_PATH.exists() and bots and all(b.get("secret") for b in bots):
            try:
                LEGACY_ENV_PATH.unlink()
            except OSError:
                pass
        return cfg

    def bots(self) -> list[dict]:
        return list(self.load().get("bots") or [])

    def resolve(self, app_id: str | None = None) -> dict:
        bots = self.bots()
        if not bots:
            raise FeiShuNotifyError("not initialized; run init")
        if app_id:
            for b in bots:
                if b.get("app_id") == app_id:
                    return b
            raise FeiShuNotifyError(f"unknown bot: {app_id}\n{self.available(bots)}")
        if len(bots) == 1:
            return bots[0]
        raise FeiShuNotifyError(
            "multiple bots; pass --bot <app_id>\n" + self.available(bots)
        )

    def upsert(self, entry: dict, secret: str | None, overwrite_secret: bool) -> str:
        """entry 不含 secret。返回 added|merged|unchanged。"""
        if self.exists():
            cfg = self.load()
        else:
            cfg = {"version": 2, "bots": []}
        bots = cfg.setdefault("bots", [])
        app_id = entry["app_id"]
        for i, old in enumerate(bots):
            if old.get("app_id") != app_id:
                continue
            sources = list(old.get("sources") or [])
            incoming = entry.get("sources") or []
            added_src = False
            for src in incoming:
                if src not in sources:
                    sources.append(src)
                    added_src = True
            name = old.get("name") or ""
            new_name = entry.get("name") or ""
            if (not name or name == self.PLACEHOLDER_NAME) and new_name:
                name = new_name
            merged = dict(old)
            merged.update(
                {
                    "name": name,
                    "app_id": app_id,
                    "sources": sources,
                    "bot_open_id": entry.get("bot_open_id")
                    or old.get("bot_open_id")
                    or "",
                    "owner_open_id": entry.get("owner_open_id")
                    or old.get("owner_open_id")
                    or "",
                }
            )
            if secret and (overwrite_secret or not self.has_secret(merged)):
                self.set_secret(merged, secret)
            bots[i] = merged
            self.save(cfg)
            return "merged" if added_src else "unchanged"
        new_bot = {
            "name": entry.get("name") or app_id,
            "app_id": app_id,
            "sources": list(entry.get("sources") or []),
            "status": entry.get("status") or "unknown",
            "bot_open_id": entry.get("bot_open_id") or "",
            "owner_open_id": entry.get("owner_open_id") or "",
        }
        if secret:
            self.set_secret(new_bot, secret)
        bots.append(new_bot)
        self.save(cfg)
        return "added"

    def update_bot(self, app_id: str, fields: dict) -> None:
        cfg = self.load()
        for b in cfg.get("bots") or []:
            if b.get("app_id") == app_id:
                for k, v in fields.items():
                    if v is None or v == "":
                        continue
                    b[k] = v
        self.save(cfg)

    def set_status(self, app_id: str, status: str) -> None:
        cfg = self.load()
        for b in cfg.get("bots") or []:
            if b.get("app_id") == app_id:
                b["status"] = status
                b["checked_at"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
        self.save(cfg)


class AdapterResult:
    def __init__(self, name: str):
        self.name = name
        self.records: list[dict] = []
        self.skip_reason: str | None = None

    @property
    def summary(self) -> str:
        if self.skip_reason:
            return f"{self.name}=skip ({self.skip_reason})"
        return f"{self.name}={len(self.records)}"


class DshAdapter:
    name = "dsh"
    CONFIG = Path.home() / ".dsh/integrations/dsh-feishu/config.json"
    CREDS = Path.home() / ".dsh/.credentials.yaml"

    def discover(self) -> AdapterResult:
        result = AdapterResult(self.name)
        if not self.CONFIG.exists():
            result.skip_reason = "no config"
            return result
        try:
            import yaml
        except ImportError as e:
            raise FeiShuNotifyError(f"需要 PyYAML: {e}")
        try:
            dsh = json.loads(self.CONFIG.read_text(encoding="utf-8"))
            creds = yaml.safe_load(self.CREDS.read_text(encoding="utf-8")) or {}
            refs = creds.get("refs") or {}
        except Exception as e:
            raise FeiShuNotifyError(f"读取 DSH 配置/凭据失败 {e}")
        raw = dsh.get("bots") or []
        if not raw:
            result.skip_reason = "no bots"
            return result
        for b in raw:
            name = b.get("botName") or ""
            app_id = b.get("appId") or ""
            secret_ref = b.get("secretRef")
            secret = refs.get(secret_ref) if secret_ref else None
            if not name or not app_id or not isinstance(secret, str) or not secret:
                raise FeiShuNotifyError(f"DSH bot 字段不完整 name={name or '(空)'}")
            result.records.append(
                {
                    "from": "dsh",
                    "name": name,
                    "app_id": app_id,
                    "secret": secret,
                    "bot_open_id": b.get("botOpenId") or "",
                    "owner_open_id": ConfigStore.first_ou(b.get("ownerOpenIds")),
                }
            )
        return result


class OpenClawAdapter:
    name = "openclaw"
    CONFIG = Path.home() / ".openclaw/openclaw.json"
    DEFAULT_NAME = "openclaw"

    def discover(self) -> AdapterResult:
        result = AdapterResult(self.name)
        if not self.CONFIG.exists():
            result.skip_reason = "no config"
            return result
        try:
            oc = json.loads(self.CONFIG.read_text(encoding="utf-8"))
        except Exception as e:
            raise FeiShuNotifyError(f"读取 OpenClaw 配置失败 {e}")
        feishu = (oc.get("channels") or {}).get("feishu")
        if not isinstance(feishu, dict):
            result.skip_reason = "no feishu channel"
            return result
        if feishu.get("enabled") is False:
            result.skip_reason = "disabled"
            return result
        app_id = feishu.get("appId") or ""
        if not app_id:
            result.skip_reason = "no appId"
            return result
        secret = self._read_secret(oc, feishu)
        if not secret:
            result.skip_reason = "no secret"
            return result
        result.records.append(
            {
                "from": "openclaw",
                "name": self.DEFAULT_NAME,
                "app_id": app_id,
                "secret": secret,
                "bot_open_id": "",
                "owner_open_id": ConfigStore.first_ou(feishu.get("allowFrom")),
            }
        )
        return result

    def _read_secret(self, oc: dict, feishu: dict) -> str | None:
        ref = feishu.get("appSecret")
        if isinstance(ref, str) and ref:
            return ref
        if not isinstance(ref, dict):
            return None
        provider = ref.get("provider") or "lark-secrets"
        secret_id = ref.get("id") or "/lark/appSecret"
        providers = (oc.get("secrets") or {}).get("providers") or {}
        spec = providers.get(provider) or {}
        raw_path = spec.get("path") or str(
            Path.home() / ".openclaw/credentials/lark.secrets.json"
        )
        path = Path(os.path.expanduser(raw_path))
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        keys = [k for k in secret_id.strip("/").split("/") if k]
        cur = data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur if isinstance(cur, str) and cur else None


class FeiShuClient:
    def __init__(self, bot: dict, config: ConfigStore):
        self.bot = bot
        self.config = config
        self._token = None

    def _request(self, url: str, payload=None, method: str | None = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            method = method or "POST"
        else:
            method = method or "GET"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Raw response bodies can contain request data or credentials.
            request_id = e.headers.get("X-Request-Id") if e.headers else None
            suffix = f" request_id={request_id}" if request_id else ""
            raise FeiShuNotifyError(f"HTTP {e.code}{suffix}")
        except (urllib.error.URLError, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            kind = type(reason).__name__
            raise FeiShuNotifyError(
                f"network outcome unknown ({kind}); do not retry automatically"
            )
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            raise FeiShuNotifyError("invalid response from Feishu API")
        if not isinstance(body, dict):
            raise FeiShuNotifyError("invalid response from Feishu API")
        if body.get("code") not in (0, None) and "tenant_access_token" not in body:
            raise FeiShuNotifyError(f"飞书返回 {body.get('code')} {body.get('msg')}")
        return body

    def ensure_token(self) -> str:
        if self._token:
            return self._token
        secret = self.config.get_secret(self.bot)
        resp = self._request(
            TOKEN_URL, {"app_id": self.bot["app_id"], "app_secret": secret}
        )
        token = resp.get("tenant_access_token")
        if not token:
            raise FeiShuNotifyError(
                f"获取 tenant_access_token 失败 {ConfigStore.tag(self.bot)}"
            )
        self._token = token
        return token

    def list_chats(self) -> list[dict]:
        self.ensure_token()
        chats: list[dict] = []
        page_token = ""
        while True:
            qs = {"page_size": "100"}
            if page_token:
                qs["page_token"] = page_token
            url = CHATS_URL + "?" + urllib.parse.urlencode(qs)
            try:
                resp = self._request(url)
            except FeiShuNotifyError as e:
                msg = str(e)
                if "HTTP 403" in msg or "99991672" in msg or "99991663" in msg:
                    raise FeiShuNotifyError(
                        f"im:chat:readonly missing (获取群组信息) {ConfigStore.tag(self.bot)}; run check"
                    )
                raise
            data = resp.get("data") or {}
            for item in data.get("items") or []:
                chats.append(
                    {
                        "name": item.get("name") or "",
                        "chat_id": item.get("chat_id") or "",
                    }
                )
            if not data.get("has_more"):
                break
            page_token = data.get("page_token") or ""
            if not page_token:
                break
        return chats

    def send(self, chat_id: str, msg_type: str, content: dict) -> dict:
        self.ensure_token()
        payload = {
            "receive_id": chat_id,
            "msg_type": msg_type,
            "content": json.dumps(content, ensure_ascii=False),
        }
        resp = self._request(f"{SEND_BASE}?receive_id_type=chat_id", payload)
        if resp.get("code") != 0:
            raise FeiShuNotifyError(
                f"飞书返回 {resp.get('code')} {resp.get('msg')} {ConfigStore.tag(self.bot)}"
            )
        data = resp.get("data")
        return data if isinstance(data, dict) else {}

    def create_chat(self, name: str, user_ids: list[str]) -> str:
        self.ensure_token()
        payload = {"name": name, "user_id_list": user_ids}
        url = CREATE_URL + "?" + urllib.parse.urlencode({"user_id_type": "open_id"})
        try:
            resp = self._request(url, payload)
        except FeiShuNotifyError as e:
            msg = str(e)
            if "HTTP 403" in msg or "99991672" in msg or "99991663" in msg:
                raise FeiShuNotifyError(
                    f"im:chat:create missing (创建群组) {ConfigStore.tag(self.bot)}; run check"
                )
            raise
        if resp.get("code") != 0:
            raise FeiShuNotifyError(
                f"飞书返回 {resp.get('code')} {resp.get('msg')} {ConfigStore.tag(self.bot)}"
            )
        return ((resp.get("data") or {}).get("chat_id")) or ""

    def fetch_bot_info(self) -> dict:
        """返回 {open_id, app_name}，接口失败则空 dict。"""
        self.ensure_token()
        try:
            resp = self._request(BOT_INFO_URL)
        except FeiShuNotifyError:
            return {}
        bot = resp.get("bot")
        if not isinstance(bot, dict):
            data = resp.get("data") or {}
            bot = data.get("bot") if isinstance(data, dict) else {}
        if not isinstance(bot, dict):
            bot = {}
        open_id = bot.get("open_id") or bot.get("bot_open_id") or ""
        app_name = bot.get("app_name") or bot.get("name") or ""
        out = {}
        if isinstance(open_id, str) and open_id.startswith("ou_"):
            out["open_id"] = open_id
        if isinstance(app_name, str) and app_name.strip():
            out["app_name"] = app_name.strip()
        return out

    def fetch_scopes(self) -> set[str] | None:
        self.ensure_token()
        try:
            resp = self._request(SCOPES_URL)
        except FeiShuNotifyError:
            return None
        scopes: set[str] = set()
        data = resp.get("data") or {}
        for item in data.get("scopes") or []:
            status = item.get("grant_status")
            granted = status in (1, "1", True, "granted", "GRANT_STATUS_GRANTED")
            if granted:
                name = item.get("scope_name") or item.get("scope") or ""
                if name:
                    scopes.add(name)
        return scopes

    @staticmethod
    def scope_granted(granted: set[str] | None, key: str) -> str:
        if granted is None:
            return "UNKNOWN"
        aliases = SCOPE_ALIASES.get(key, (key,))
        return "OK" if any(a in granted for a in aliases) else "MISSING"


class CLI:
    def __init__(self):
        self.config = ConfigStore()
        self.adapters = {"dsh": DshAdapter(), "openclaw": OpenClawAdapter()}

    def _client(self, bot: dict) -> FeiShuClient:
        return FeiShuClient(bot, self.config)

    def _fill_bot_identity(self, bot: dict, client: FeiShuClient) -> None:
        info = client.fetch_bot_info()
        patch = {}
        if info.get("open_id"):
            patch["bot_open_id"] = info["open_id"]
        if info.get("app_name") and (
            not bot.get("name") or bot.get("name") == ConfigStore.PLACEHOLDER_NAME
        ):
            patch["name"] = info["app_name"]
        if patch:
            self.config.update_bot(bot["app_id"], patch)

    def _mark_invalid(self, bot: dict) -> None:
        app_id = bot.get("app_id")
        if app_id:
            try:
                self.config.set_status(app_id, "invalid")
            except FeiShuNotifyError:
                pass

    def _print_bot_line(self, bot: dict) -> None:
        app_id = bot.get("app_id") or ""
        sources = ",".join(bot.get("sources") or []) or "-"
        prefix = (app_id[:8] + "…") if len(app_id) > 8 else (app_id or "(无)")
        print(
            f"- {bot.get('name')}  appId={prefix}  "
            f"sources={sources}  status={bot.get('status') or 'unknown'}"
        )

    def init(self, from_name: str | None) -> None:
        names = [from_name] if from_name else list(self.adapters)
        if from_name and from_name not in self.adapters:
            raise FeiShuNotifyError(f"unknown adapter: {from_name}")
        results: list[AdapterResult] = []
        for name in names:
            result = self.adapters[name].discover()
            if result.skip_reason and from_name:
                raise FeiShuNotifyError(
                    f"adapter {name} unavailable: {result.skip_reason}"
                )
            results.append(result)

        touched_ids: list[str] = []
        for result in results:
            for rec in result.records:
                secret = rec["secret"]
                src = rec["from"]
                entry = {
                    "name": rec["name"],
                    "app_id": rec["app_id"],
                    "sources": [src],
                    "bot_open_id": rec.get("bot_open_id") or "",
                    "owner_open_id": rec.get("owner_open_id") or "",
                }
                self.config.upsert(entry, secret, overwrite_secret=False)
                if rec["app_id"] not in touched_ids:
                    touched_ids.append(rec["app_id"])

        adapter_line = "adapters: " + ", ".join(r.summary for r in results)
        local_bots = self.config.bots() if self.config.exists() else []
        if not any(r.records for r in results) and not local_bots:
            raise FeiShuNotifyError(
                "no bots from any adapter\n"
                + adapter_line
                + "\n下一步: bot add --name <名> --app-id <cli_xxx> --secret '<secret>'"
            )

        print("OK init")
        print(adapter_line)
        by_id = {b["app_id"]: b for b in local_bots}
        ordered = list(touched_ids)
        for b in local_bots:
            if b["app_id"] not in ordered:
                ordered.append(b["app_id"])
        for app_id in ordered:
            bot = by_id.get(app_id)
            if not bot:
                continue
            try:
                client = self._client(bot)
                client.ensure_token()
                self._fill_bot_identity(bot, client)
                self.config.set_status(app_id, "ok")
            except FeiShuNotifyError:
                self.config.set_status(app_id, "invalid")
            bot = next(b for b in self.config.bots() if b["app_id"] == app_id)
            self._print_bot_line(bot)

    def list_bots(self) -> None:
        bots = self.config.bots()
        print(f"OK list {len(bots)} bots")
        for b in bots:
            self._print_bot_line(b)

    def bot_add(self, name: str, app_id: str, secret: str | None, secret_stdin: bool) -> None:
        if secret and secret_stdin:
            raise FeiShuNotifyError("--secret 与 --secret-stdin 不能同时使用")
        if secret_stdin:
            secret = sys.stdin.read().strip()
        if not name or not app_id or not secret:
            raise FeiShuNotifyError("bot add 需要 --name --app-id，并通过 --secret-stdin 或 --secret 提供 secret")
        if self.config.exists():
            for b in self.config.bots():
                if b.get("app_id") == app_id:
                    raise FeiShuNotifyError(f"bot exists: {app_id}")
                if b.get("name") == name:
                    raise FeiShuNotifyError(f"bot exists: {name}")
        self.config.upsert(
            {
                "name": name,
                "app_id": app_id,
                "sources": ["manual"],
                "bot_open_id": "",
                "owner_open_id": "",
            },
            secret,
            overwrite_secret=True,
        )
        print(f"OK added {ConfigStore.tag({'name': name, 'app_id': app_id})}")

    def check(self, app_id: str | None) -> None:
        bot = self.config.resolve(app_id)
        client = self._client(bot)
        status = {
            "tenant_access_token": "MISSING",
            "im:message:send_as_bot": "MISSING",
            "im:chat:readonly": "MISSING",
            "im:chat:create": "MISSING",
        }
        try:
            client.ensure_token()
            status["tenant_access_token"] = "OK"
            status["im:message:send_as_bot"] = "OK"
            self._fill_bot_identity(bot, client)
            self.config.set_status(bot["app_id"], "ok")
        except FeiShuNotifyError:
            status["tenant_access_token"] = "MISSING"
            status["im:message:send_as_bot"] = "MISSING"
            self.config.set_status(bot["app_id"], "invalid")

        if status["tenant_access_token"] == "OK":
            try:
                client.list_chats()
                status["im:chat:readonly"] = "OK"
            except FeiShuNotifyError:
                status["im:chat:readonly"] = "MISSING"
            granted = client.fetch_scopes()
            status["im:chat:create"] = FeiShuClient.scope_granted(
                granted, "im:chat:create"
            )
            send_st = FeiShuClient.scope_granted(granted, "im:message:send_as_bot")
            if send_st == "MISSING":
                status["im:message:send_as_bot"] = "MISSING"
            elif send_st == "OK":
                status["im:message:send_as_bot"] = "OK"

        missing = [k for k, v in status.items() if v == "MISSING"]
        unknown = [k for k, v in status.items() if v == "UNKNOWN"]
        tag = ConfigStore.tag(bot)
        if missing:
            print(f"FAIL: missing scopes {tag}")
        elif unknown:
            print(f"OK token and listed scopes {tag}")
        else:
            print(f"OK all scopes present {tag}")
        for key, zh in SCOPE_ROWS:
            print(f"- {key:<24} {zh:<12} {status[key]}")
        if missing:
            names = "、".join(zh for k, zh in SCOPE_ROWS if status[k] == "MISSING")
            print(
                f"下一步: 开放平台 → 权限管理勾选「{names}」→ 创建版本并发布 "
                f"→ 管理员审批后重跑 check --bot '{bot['app_id']}'"
            )
            raise SystemExit(1)
        if unknown:
            print("下一步: im:chat:create 以第一次 create 为准（探活不建群）")

    def chats(self, app_id: str | None) -> None:
        if app_id:
            bots = [self.config.resolve(app_id)]
        else:
            bots = self.config.bots()
            if not bots:
                raise FeiShuNotifyError("not initialized; run init")
        blocks = []
        total = 0
        failed = 0
        for bot in bots:
            try:
                chats = self._client(bot).list_chats()
                total += len(chats)
                blocks.append((bot, chats, None))
            except FeiShuNotifyError as e:
                self._mark_invalid(bot)
                failed += 1
                blocks.append((bot, [], str(e)))
        if failed == len(blocks):
            for _, _, err in blocks:
                print(f"FAIL: {err}")
            raise SystemExit(1)
        print(f"OK {total} chats")
        for bot, chats, err in blocks:
            print(f"[{ConfigStore.tag(bot)}]")
            if err:
                print(f"FAIL: {err}")
            elif not chats:
                print("- （无）")
            else:
                for c in chats:
                    print(f"- {c['name']}")
        if failed:
            raise SystemExit(1)

    @staticmethod
    def parse_content(
        content_raw: str | None, msg_type: str | None
    ) -> tuple[str, dict]:
        if content_raw is None or not str(content_raw).strip():
            raise FeiShuNotifyError("需要 --content")
        raw = str(content_raw).strip()
        parsed = None
        is_json = False
        try:
            parsed = json.loads(raw)
            is_json = True
        except json.JSONDecodeError:
            is_json = False

        inferred = None
        content: dict | None = None
        if not is_json:
            inferred = "text"
            content = {"text": raw}
        elif isinstance(parsed, dict):
            if "post" in parsed:
                inferred = "post"
                content = parsed
            elif list(parsed.keys()) == ["text"] and isinstance(parsed.get("text"), str):
                inferred = "text"
                content = parsed
            elif "zh_cn" in parsed or isinstance(parsed.get("content"), list):
                inferred = "post"
                content = {"post": parsed}
            else:
                raise FeiShuNotifyError(
                    '--content JSON 无法识别：用纯文本、{"text":"..."} 或完整 {"post":...}'
                )
        elif isinstance(parsed, str):
            inferred = "text"
            content = {"text": parsed}
        else:
            raise FeiShuNotifyError(
                '--content JSON 无法识别：用纯文本、{"text":"..."} 或完整 {"post":...}'
            )

        chosen = msg_type or inferred
        if chosen not in ("text", "post"):
            raise FeiShuNotifyError(f"不支持的 --msg-type {chosen}")
        if chosen == "post" and inferred == "text":
            raise FeiShuNotifyError(
                "--msg-type post 需要 JSON（{\"post\":...}），不要把纯文本当 post"
            )
        if chosen == "text" and inferred == "post":
            raise FeiShuNotifyError("--msg-type text 与 post JSON 不匹配")
        return chosen, content

    def send(
        self,
        app_id: str | None,
        to: str | None,
        msg_type: str | None,
        content_raw: str | None,
    ) -> None:
        msg_type, content = self.parse_content(content_raw, msg_type)
        if not to:
            raise FeiShuNotifyError("需要 --to <群名>")
        bot = self.config.resolve(app_id)
        client = self._client(bot)
        try:
            chats = client.list_chats()
        except FeiShuNotifyError:
            self._mark_invalid(bot)
            raise
        hits = [c for c in chats if c["name"] == to]
        if not hits:
            available = ", ".join(c["name"] for c in chats) or "（无）"
            raise FeiShuNotifyError(
                f"chat not found: {to} {ConfigStore.tag(bot)}\navailable: {available}"
            )
        if len(hits) > 1:
            lines = "\n".join(f"- {c['name']} {c['chat_id']}" for c in hits)
            raise FeiShuNotifyError(
                f"ambiguous chat: {to} ({len(hits)}) {ConfigStore.tag(bot)}\n{lines}"
            )
        try:
            data = client.send(hits[0]["chat_id"], msg_type, content)
        except FeiShuNotifyError:
            self._mark_invalid(bot)
            raise
        mid = data.get("message_id") or ""
        extra = f"  {mid}" if mid else ""
        print(f"OK sent: {to} {msg_type}{extra} {ConfigStore.tag(bot)}")

    def create(self, app_id: str | None, name: str | None, members: str | None) -> None:
        if not name:
            raise FeiShuNotifyError("需要 --name <群名>")
        bot = self.config.resolve(app_id)
        client = self._client(bot)
        try:
            chats = client.list_chats()
        except FeiShuNotifyError as e:
            if "im:chat:readonly missing" not in str(e):
                self._mark_invalid(bot)
            raise
        if any(c["name"] == name for c in chats):
            raise FeiShuNotifyError(f"chat exists: {name} {ConfigStore.tag(bot)}")
        user_ids = []
        owner = bot.get("owner_open_id") or ""
        if owner:
            user_ids.append(owner)
        if members:
            for x in [p.strip() for p in members.split(",") if p.strip()]:
                if x not in user_ids:
                    user_ids.append(x)
        if not user_ids:
            raise FeiShuNotifyError(
                f"create 需要成员：无 owner_open_id，请传 --members {ConfigStore.tag(bot)}"
            )
        try:
            chat_id = client.create_chat(name, user_ids)
        except FeiShuNotifyError as e:
            if "im:chat:create missing" not in str(e):
                self._mark_invalid(bot)
            raise
        extra = f"  {chat_id}" if chat_id else ""
        print(f"OK created: {name}{extra} {ConfigStore.tag(bot)}")

    def run(self, argv: list[str]) -> None:
        parser = self.build_parser()
        if not argv:
            print(__doc__)
            sys.exit(1)
        args = parser.parse_args(argv)
        try:
            if args.cmd == "init":
                self.init(args.from_name)
            elif args.cmd == "list":
                self.list_bots()
            elif args.cmd == "bot":
                if args.bot_cmd == "add":
                    self.bot_add(args.name, args.app_id, args.secret, args.secret_stdin)
                else:
                    raise FeiShuNotifyError("bot 需要 add")
            elif args.cmd == "check":
                self.check(args.bot)
            elif args.cmd == "chats":
                self.chats(args.bot)
            elif args.cmd == "send":
                self.send(args.bot, args.to, args.msg_type, args.content)
            elif args.cmd == "create":
                self.create(args.bot, args.name, args.members)
            else:
                raise FeiShuNotifyError(f"未知命令 {args.cmd}")
        except FeiShuNotifyError as e:
            print(f"FAIL: {e}")
            sys.exit(1)

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog="feishu-notify.py", description="飞书群通知 CLI")
        sub = p.add_subparsers(dest="cmd")

        init_p = sub.add_parser("init", help="从适配器导入 bot")
        init_p.add_argument("--from", dest="from_name", choices=("dsh", "openclaw"))

        sub.add_parser("list", help="列出已保存的 bot")

        bot_p = sub.add_parser("bot", help="手工添加 bot")
        bot_sub = bot_p.add_subparsers(dest="bot_cmd")
        add_p = bot_sub.add_parser("add")
        add_p.add_argument("--name", required=True)
        add_p.add_argument("--app-id", required=True)
        secret_group = add_p.add_mutually_exclusive_group(required=True)
        secret_group.add_argument("--secret", help="不推荐：secret 会出现在进程参数中")
        secret_group.add_argument(
            "--secret-stdin",
            action="store_true",
            help="从标准输入读取 secret（推荐）",
        )

        check_p = sub.add_parser("check", help="检查权限")
        check_p.add_argument("--bot")

        chats_p = sub.add_parser("chats", help="列出群")
        chats_p.add_argument("--bot")

        send_p = sub.add_parser("send", help="按群名发消息")
        send_p.add_argument("--bot")
        send_p.add_argument("--to")
        send_p.add_argument("--msg-type", choices=("text", "post"))
        send_p.add_argument("--content")

        create_p = sub.add_parser("create", help="建群")
        create_p.add_argument("--bot")
        create_p.add_argument("--name")
        create_p.add_argument("--members")
        return p


def main() -> None:
    CLI().run(sys.argv[1:])


if __name__ == "__main__":
    main()
