---
name: feishu-group-notify
description: 可靠地通过飞书自建机器人查找群、发送群通知或在确认后创建群。用户提到“发飞书”“通知某个飞书群”“把结果同步到群”“建群后通知”、需要把任务结果或异常推送到飞书，或无人值守任务要求飞书告警时，都应使用本 skill；即使用户没有说出 skill 名也要触发。只讨论飞书开放平台 API、编写普通飞书消息文案、私聊个人或操作非飞书渠道时不要触发。
---

# 飞书群通知

在本 skill 目录运行 `scripts/feishu-notify.py`。脚本非交互；以**退出码为主**，再根据 stdout 的整行 `OK ...` 或 `FAIL: ...` 决定下一步。非零退出码即未完整成功，即使之前出现过部分 `OK` 也不能声称操作完成。`--bot` 始终使用完整 `app_id`。

## 先判断授权边界

把用户意图归为以下一种，再执行命令。这样既避免重复确认，也避免把“帮我看看”误当成发送授权。

| 情况 | 行为 |
|---|---|
| 用户明确要求发送，并给出**现有群名和最终正文** | 可查询群并直接发送，无需再问一次 |
| 群是根据任务主题推断的，或正文由你实质改写/补全 | 展示“目标群 + 正文预览”，确认后发送 |
| 用户明确要求创建群（并说明 bot；若多 bot） | 可创建；如果还要求通知，创建成功后再发送 |
| 只是询问能力、配置、可用群、起草文案或演练 | 只查询/回答，不发送、不建群 |
| cron、自动化或其他无人值守任务 | 只允许向用户预先指定的已有群发送；不得猜群、建群、索取凭据 |

`send` 和 `create` 都会产生真实外部副作用。没有满足上表条件时先确认。不要把读取 `chats`、`list` 或 `check` 当成发送授权。

## 安全与结果规则

- 不在回复、日志或评估产物中展示 app secret、tenant token、access token 或 `config.json` 内容；只显示 bot 名和必要的 `app_id`。
- 不把用户提供的 secret 重复回显。添加 bot 时**明确使用 `--secret-stdin`** 从标准输入传入，避免 secret 留在命令历史或进程参数中；不要只笼统地说“安全传入”。
- 只有脚本返回 `OK sent ...` 才能说“已发送”；只有 `OK created ...` 才能说“已创建”。执行前只能说“准备发送/创建”。
- `FAIL:` 后如网络结果不确定，不要盲目重试 `send`，以免重复通知；先说明可能未确认送达并让用户决定。
- 不因群名相似就自动选择。精确匹配不唯一、bot 不唯一或没有明确相关群时，列出最少必要候选并询问。

## 1. 初始化与选择 Bot

仅在 `config.json` 缺失或脚本返回 `FAIL: not initialized` 时初始化；不要每次发送都重跑。

```bash
python3 scripts/feishu-notify.py init
```

`FAIL: adapter ... unavailable` 表示单个来源不可用，不等于所有来源都为空；改用无参 `init` 或选择可用的 `--from`。

没有发现 bot 时，向用户收集 bot 名、完整 `app_id` 和 secret。把 secret 通过 stdin 传入，不在命令文本或回复中出现：

```bash
printf '%s' "$FEISHU_APP_SECRET" | python3 scripts/feishu-notify.py bot add --name '<名称>' --app-id '<cli_xxx>' --secret-stdin
```

已有配置时，按需查看或检查；正常发送不必例行 `check`：

```bash
python3 scripts/feishu-notify.py list
python3 scripts/feishu-notify.py check [--bot <app_id>]
```

- `FAIL: multiple bots`：列出 available 中的 bot 名与 `app_id`，让用户选；不要猜。
- `FAIL: unknown bot`：重新 `list`，使用返回的完整 `app_id`。
- `invalid`、`unknown`、缺权限或 secret 错误：运行 `check`，照其“下一步”处理。

## 2. 解析目标群

发送前运行 `chats` 获取当场可见群，避免依赖记忆中的旧群名：

```bash
python3 scripts/feishu-notify.py chats [--bot <app_id>]
```

- 用户给了群名：用当场结果解析。精确且唯一时，若正文也最终确定，可直接发送；否则确认差异。
- 用户没给群名：只在任务主题与某一群明显、唯一对应时建议该群，并等待确认。
- 没有明显对应群：按 bot 分组给出少量候选，或建议一个新群名；等待用户选择。无人值守任务到此停止。
- `FAIL: ambiguous chat`：展示重名候选并询问。
- `FAIL: chat not found`：使用 available 中的当场候选询问；不要擅自新建。

建议确认格式：

```text
准备发送到：<bot 名> / <群名>
正文预览：
<最终正文>

回复“发送”继续，或指出要修改的群/正文。
```

## 3. 发送

尽量使用用户给出的最终正文；不要添加“由 AI 生成”等未要求内容。纯文本直接传入；`{"text":"..."}` 仍按 text；完整 `{"post":...}` 才按富文本 post。

```bash
python3 scripts/feishu-notify.py send --to '<群名>' --content '<正文>' [--bot <app_id>]
```

成功后简洁报告 bot、群名和消息类型，不回显敏感配置。失败时引用 `FAIL:` 的可操作部分并说明下一步，不能声称已送达。

## 4. 创建群

只有用户已明确要求或在看到建议后确认，且不是无人值守任务时，才创建：

```bash
python3 scripts/feishu-notify.py create --name '<群名>' [--bot <app_id>] [--members '<ou_1,ou_2>']
```

默认不加 `--members`，即只邀请 owner。要邀请其他人，先告知这一默认值并向用户收集对应的 `ou_...`；没有 open_id 就不要猜。

- `FAIL: chat exists`：不要重复创建，改为询问是否发送到已有群。
- `FAIL: create 需要成员`：收集明确的 `ou_...`。
- 创建成功且用户同时授权发送时，再运行 `send`；创建失败则不要发送。
