---
name: ai-topic-fetcher
version: 1.0.0
description: "全网 AI 热点抓取器。调用 opencli 和 gh 从 YouTube、X(Twitter)、GitHub、小红书、B站等全网平台抓取热门内容，经 AI 筛选提炼后输出结构化 JSON。支持「全网搜索」和「特定平台搜索」两种模式，以及可配置的搜索预设。当用户需要搜集热点选题、全网巡查、平台调研时使用。"
metadata:
  requires:
    bins: ["opencli"]
  cliHelp: "This is an agentic workflow skill, no custom CLI."
---

# ai-topic-fetcher 工作流

> **前置条件：** 本 Skill 依赖全局安装的 `opencli`（`npm install -g @jackwener/opencli`）和 Chrome 浏览器插件。YouTube、X、小红书、B站 等平台需要用户在 Chrome 中已登录。GitHub 和 HackerNews 不需要登录。

## 核心概念

### 两种工作模式

| 模式 | 触发示例 | 行为 |
|------|---------|------|
| **全网搜索** | "帮我搜一下全网热点" / "用默认配置跑一下" / "搜集今天的选题" | 按指定配置中**所有已启用渠道**逐个抓取，AI 筛选后输出结构化 JSON |
| **特定平台搜索** | "帮我在B站搜AI agent" / "YouTube上搜一下最新的AI视频" | 只在用户**指定的单一平台**上搜索，用户提供关键词 |

### 配置系统

配置文件存储在本 Skill 目录下的 `configs/` 文件夹中：

```
ai-topic-fetcher/
├── SKILL.md
└── configs/
    ├── _default.json       # 默认配置（可修改，不可删除）
    ├── <用户自定义>.json     # 用户创建的配置
    └── ...
```

每个配置文件包含：`name`（配置名）、`description`（简介）、`topic`（主题）以及 `channels` 对象（各渠道的搜索参数和热度阈值）。

---

## 执行流程

### Step 0: 确定模式与配置

**如果用户明确要求某个特定平台**（如"在B站搜XXX"）：
- 进入「特定平台搜索」模式，跳到 Step 2b

**如果用户要求全网搜索或未指明平台**：
- 进入「全网搜索」模式
- 如果用户未指定配置，**列出所有可用配置并带出简介**让用户选择：

```
请选择搜索配置：
1. 🔹 **默认配置** — AI agent 相关热点，覆盖 YouTube(10k+播放)、X(500+赞)、GitHub(1k+ stars)、小红书(500+赞)、B站(50k+播放)
2. 🔹 **[配置A名称]** — [配置A的 description]
3. 🔹 **[配置B名称]** — [配置B的 description]
4. ➕ 新建配置

请选择序号或配置名：
```

读取配置的方法：使用 `view_file` 工具读取 `configs/` 目录中的 JSON 文件。默认配置路径为 `~/.gemini/antigravity/skills/ai-topic-fetcher/configs/_default.json`。

### Step 1: 读取配置

从选定的配置 JSON 文件中读取各渠道的参数。

### Step 2a: 全网搜索模式 — 数据抓取

对配置中 `enabled: true` 的每个渠道，**逐个**执行 opencli 命令：

**YouTube：**
```bash
opencli youtube search "<query>" --limit <limit> <extra_args> --format json
```

**X (Twitter)：**
```bash
opencli twitter search "<query>" --limit <limit> <extra_args> --format json
```

**GitHub：**
```bash
gh search repos <extra_args> --json name,description,stargazerCount,url --limit <limit>
```

**小红书：**
```bash
opencli xiaohongshu search "<query>" --limit <limit> <extra_args> --format json
```

**B站：**
```bash
opencli bilibili search "<query>" --limit <limit> <extra_args> --format json
```

将每个渠道的 JSON 输出重定向到工作区临时文件（如 `<workspace>/temp_yt.json`），使用完毕后清理。

> ⚠️ **重要**：不要将临时文件写到 `/tmp/` 目录，必须写在当前工作区目录中。

### Step 2b: 特定平台搜索模式 — 数据抓取

根据用户指定的平台和关键词，执行对应的单个 opencli 命令。如果用户未指定阈值和参数，使用默认配置中该平台的参数。

### Step 3: AI 筛选与提炼

基于抓取到的原始数据，进行智能筛选：

1. **按热度阈值过滤**：根据配置中的 `threshold` 过滤掉不达标的内容
2. **AI 提炼**（全网搜索模式挑选 Top 5-8，特定平台模式保留所有达标内容）：
   - 为每条内容生成**中文标题**（如原文是英文）
   - 生成**一句话摘要**（核心亮点/痛点）
   - 生成**可拍性分析**（是否适合做视频/图文爆款）

### Step 4: 输出结构化 JSON

将筛选和提炼后的结果以 JSON 数组格式输出到工作区临时文件 `<workspace>/topic_results.json`。

**全网搜索模式的输出格式：**
```json
{
  "mode": "global",
  "config_name": "默认配置",
  "scan_date": "2026-04-05",
  "results": [
    {
      "title": "中文标题",
      "platform": "YouTube",
      "heat_indicator": "YouTube 12.3万播放",
      "url": "https://...",
      "summary": "一句话摘要",
      "shootability": "可拍性分析",
      "status": "待筛选"
    }
  ]
}
```

**特定平台搜索模式的输出格式：**
```json
{
  "mode": "platform",
  "platform": "bilibili",
  "query": "AI agent",
  "scan_date": "2026-04-05",
  "results": [
    {
      "title": "视频标题",
      "author": "UP主",
      "heat": 125385,
      "url": "https://...",
      "query": "AI agent",
      "summary": "一句话摘要",
      "shootability": "可拍性分析"
    }
  ]
}
```

### Step 5: 回复用户

告知用户抓取完成，展示精选结果的简要摘要（不要打印完整 JSON），并提示用户可以继续运行 `ai-topic-to-base` 将结果存入飞书多维表格。

---

## 配置管理

### 新建配置

当用户说"帮我新建一个配置"时：

1. **启动配置助手**：自动读取 opencli 各平台的帮助信息，向用户介绍各渠道支持的能力
   ```bash
   opencli <platform_name> --help
   ```
   向用户说明，例如：
   - "**YouTube** 支持：`search`（关键词搜索，可按播放量/日期排序）、`channel`（频道视频）"
   - "**B站** 支持：`search`（搜索）、`hot`（热门）、`ranking`（排行榜）"
   - "**X** 支持：`search`（搜索，可筛选热门/最新）、`trending`（热搜趋势）"
   - "**小红书** 支持：`search`（搜索）、`feed`（推荐流）"
   - "**GitHub** 支持：按 topic/stars/language 搜索仓库"

2. 引导用户选择渠道、关键词、热度阈值
3. 让用户为配置取一个名字
4. 生成 JSON 配置文件保存到 `configs/<名称>.json`

### 修改配置

使用 `view_file` 读取配置 → 展示给用户 → 用户确认修改 → 使用编辑工具更新 JSON。

> ⚠️ `_default.json` 可以修改内容，但**不能删除该文件**。

### 查看配置

列出 `configs/` 目录下所有 JSON 文件，读取每个文件的 `name` 和 `description` 展示给用户。

### 删除配置

用户确认后删除对应 JSON 文件。`_default.json` 不允许删除。
