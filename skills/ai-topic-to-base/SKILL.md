---
name: ai-topic-to-base
version: 1.0.0
description: "将 ai-topic-fetcher 抓取的热点内容存入飞书多维表格。首次使用时引导用户配置飞书多维表格链接，支持自动建表、建字段、去重写入。当用户需要把抓取的选题存入飞书多维表格时使用。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "This is an agentic workflow skill, no custom CLI."
---

# ai-topic-to-base 工作流

> **前置条件：** 本 Skill 依赖 `lark-cli`（飞书 CLI），首次使用时会自动检测并引导安装。

## 首次使用引导流程

每次运行本 Skill 时，按以下顺序检查环境：

### Step 1: 检查 lark-cli 安装

```bash
which lark-cli
```

- **已安装** → 跳到 Step 2
- **未安装** → 告知用户：
  > "检测到您尚未安装飞书 CLI（lark-cli），这是将数据写入飞书多维表格的必要工具。
  > 是否同意从 GitHub 安装？（将执行 `npm install -g @larksuite/cli`）"
  
  用户同意后执行安装。安装完成后引导用户完成 `lark-cli config init` 和 `lark-cli auth login`。
  
  > ⚠️ **必须等待用户明确同意后才能执行安装命令。**

### Step 2: 检查 lark-cli 认证状态

```bash
lark-cli auth status
```

- **已认证** → 跳到 Step 3
- **未认证/过期** → 引导用户：
  > "您的飞书 CLI 认证已过期或尚未配置。请先完成以下步骤：
  > 1. `lark-cli config init`（配置应用 ID 和密钥）
  > 2. `lark-cli auth login`（OAuth 授权登录）"

### Step 3: 检查多维表格配置

读取本 Skill 目录下的 `config.json`：`~/.gemini/antigravity/skills/ai-topic-to-base/config.json`

- **存在且有效** → 使用已配置的 `base_token`，进入写入流程
- **不存在** → 引导用户：
  > "首次使用需要配置飞书多维表格的存储位置。请选择：
  > 1. 提供一个**已有的**飞书多维表格链接（如 `https://xxx.feishu.cn/base/xxxxx`）
  > 2. 让我在指定文件夹中**新建**一个多维表格"
  
  **选项 1：** 用户提供链接后，解析出 `base_token`（注意处理 `/wiki/` 链接需先用 `lark-cli wiki spaces get_node` 解析真实 token），保存到 `config.json`。
  
  **选项 2：** 用户提供 `folder_token` 或文件夹链接后：
  ```bash
  lark-cli base +base-create --name "AI 选题素材库" --folder-token <folder_token>
  ```
  拿到返回的 `base_token`，保存到 `config.json`。

#### config.json 格式

```json
{
  "base_token": "xxxxxxxxxxxxxxx",
  "base_url": "https://xxx.feishu.cn/base/xxxxxxxxxxxxxxx",
  "created_at": "2026-04-05"
}
```

---

## 写入流程

### Step 4: 读取待写入数据

读取工作区中 `ai-topic-fetcher` 输出的 `topic_results.json` 文件。根据其中的 `mode` 字段判断写入目标表：

| mode | 写入的表 |
|------|---------|
| `global` | 「全网热点汇总」表 |
| `platform` | 以平台名命名的独立表（如 `B站`、`YouTube`） |

### Step 5: 确保目标表存在

```bash
lark-cli base +table-list --base-token <base_token>
```

检查目标表是否已存在：

- **存在** → 跳到 Step 6
- **不存在** → 自动创建表和字段

#### 创建「全网热点汇总」表

```bash
# 建表
lark-cli base +table-create --base-token <base_token> --name "全网热点汇总"
```

然后逐个创建字段（使用 `+field-create`，严格遵循 lark-base skill 的字段 JSON 规范）：

```bash
# 标题
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"text","name":"标题"}'

# 来源平台（单选）
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"select","name":"来源平台","multiple":false,"options":[{"name":"YouTube","hue":"Red"},{"name":"Twitter","hue":"Blue"},{"name":"GitHub","hue":"Gray"},{"name":"小红书","hue":"Carmine"},{"name":"B站","hue":"Wathet"},{"name":"HackerNews","hue":"Orange"},{"name":"ProductHunt","hue":"Green"},{"name":"Reddit","hue":"Purple"}]}'

# 热度指标
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"text","name":"热度指标"}'

# 原文链接
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"text","name":"原文链接","style":{"type":"url"}}'

# 一句话摘要
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"text","name":"一句话摘要"}'

# 可拍性分析
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"text","name":"可拍性分析"}'

# 扫描日期
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"datetime","name":"扫描日期","style":{"format":"yyyy-MM-dd"}}'

# 状态（单选）
lark-cli base +field-create --base-token <base_token> --table-id <table_id> --json '{"type":"select","name":"状态","multiple":false,"options":[{"name":"待筛选","hue":"Blue","lightness":"Lighter"},{"name":"已采纳","hue":"Green","lightness":"Light"},{"name":"已放弃","hue":"Gray","lightness":"Lighter"}]}'
```

#### 创建特定平台表

表名使用平台中文名（如 `B站`、`YouTube`）。字段根据该平台 opencli 返回的列动态确定，但至少包含：

| 字段 | 类型 | 所有平台通用 |
|------|------|------------|
| 标题 | text | ✅ |
| 作者 | text | ✅ |
| 热度 | number | ✅ |
| 链接 | text (url) | ✅ |
| 搜索关键词 | text | ✅ |
| 一句话摘要 | text | ✅ |
| 可拍性分析 | text | ✅ |
| 扫描日期 | datetime | ✅ |

各平台可能追加的特殊字段：
- **YouTube**：`频道`(text)、`时长`(text)、`发布时间`(text)
- **Twitter**：`点赞数`(number)、`浏览量`(number)、`发布时间`(text)
- **小红书**：`发布时间`(text)

### Step 6: 去重检查

在写入前，先检查该条记录的链接是否已存在。使用已有的视图筛选或逐条比对：

```bash
# 获取已有记录的链接字段
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --limit 200
```

从返回结果中提取所有已有的「原文链接」/「链接」值，与待写入数据比对。已存在的链接跳过，避免重复写入。

### Step 7: 写入记录

对每条不重复的记录，使用 `+record-upsert` 写入：

```bash
# 全网热点汇总表示例
lark-cli base +record-upsert --base-token <base_token> --table-id <table_id> --json '{
  "标题": "Claude Code 发现隐藏 23 年的 Linux 漏洞",
  "来源平台": "HackerNews",
  "热度指标": "HN 653分 / 542评论",
  "原文链接": "https://mtlynch.io/claude-code-found-linux-vulnerability/",
  "一句话摘要": "AI 编程助手在常规代码审查中揪出了潜伏 23 年的内核安全漏洞",
  "可拍性分析": "极强！人类找了23年的bug被AI秒杀，天然爆款叙事",
  "扫描日期": "2026-04-05 00:00:00",
  "状态": "待筛选"
}'
```

> ⚠️ **批量写入上限 500 条/次**，串行写入，批次间延迟 0.5 秒。

### Step 8: 回复用户

告知用户写入完成，报告：
- 写入了多少条新记录
- 跳过了多少条重复记录
- 提供飞书多维表格的直达链接（从 `config.json` 中的 `base_url` 获取）

---

## 注意事项

- 所有 `base` 命令必须遵循 `lark-base` skill 的规范（先读字段结构再写记录、字段类型匹配等）
- Wiki 链接（`/wiki/xxx`）必须先用 `lark-cli wiki spaces get_node` 解析出真实的 `obj_token` 再使用
- 不要将 wiki_token 直接作为 base_token
- `+table-list / +field-list / +record-list` 只能串行执行，不能并发
