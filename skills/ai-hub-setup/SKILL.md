---
name: ai-hub-setup
version: 2.0.0
description: "AI Learning Hub V2 的配置中枢与管家。当用户需要首次初始化 AI 学习枢纽（建表、配置抓取源字典、设定知识库空间 ID）、或修改基础配置信息时使用。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# AI Hub Setup (配置中枢)

这是 AI Learning Hub V2 架构的基础配置管家。
负责维护核心配置文件：`~/.gemini/antigravity/configs/ai-learning-hub.json`。

> **前置条件：** 依赖 `lark-cli` 和 `lark-base` 技能。

## 执行流程：首次引导或修复配置

当用户触发初始化，或其他核心子系统（ingest/wiki/shadow）报错缺配置时，执行本流程。

### Step 1: 检查配置文件
读取 `~/.gemini/antigravity/configs/ai-learning-hub.json`。
如果不存在，通过终端交互向用户索要以下信息：
1. **飞书多维表格（Base）URL 或 Token**（用于存储流与收藏索引）
2. **飞书知识库（Wiki）的空间 ID 或 URL**（用于存放深度文章体系）

### Step 2: 验证和补全 Base 表结构
连接到指定的飞书多维表格通过 `lark-cli base +table-list` 检查是否包含以下四张表：
1. `信息流` (主字段：标题)
2. `精选收藏` (主字段：标题)
3. `深度学习` (主字段：标题)
4. `📡 抓取源配置` (主字段：配置名称)

如果缺失任何一张表，使用 `lark-cli base +table-create` 建表，并根据以下 Schema 补充所需字段：

**📡 抓取源配置**
必须包含以下字段：
- `配置名称` (Text - 主字段)
- `平台` (Text) 
- `目标标识` (Text)
- `抓取频率` (Text)
- `备注` (Text)

如果这是新创建的从零开始的 Base，**必须删除飞书自动默认创建的 5 条空行** (通过 `lark-cli base +record-list` 发现全 null 记录后执行 `+record-delete`)。

### Step 3: 获取 User ID (用于 IM 简报)
运行 `lark-cli contact +me` 获取当前用户的 `open_id`。

### Step 4: 将配置落盘
将收集到的所有配置信息，整理并存储至共享配置文件 `~/.gemini/antigravity/configs/ai-learning-hub.json`，格式如下：

```json
{
  "base_token": "xxx",
  "wiki_space_id": "xxx",
  "user_open_id": "ou_xxx",
  "tables": {
    "feed": "tbl_xxx",
    "favorites": "tbl_xxx",
    "deep_learning": "tbl_xxx",
    "fetch_config": "tbl_xxx"
  }
}
```

## 执行流程：管理抓取源配置表

当用户要求“给我看看现在的抓取源”、“帮我加一个推特的抓取源”时。

1. **查源**：读取 shared `config.json` 获取 `base_token` 和 `fetch_config` table ID，运行 `lark-cli base +record-list`，将当前配置罗列给用户看。
2. **加源/改源**：根据用户指令，通过 `lark-cli base +record-upsert` 对抓取源配置表进行增删改查。

**支持的平台类型字典**：
- `推特`
- `油管`
- `B站`
- `播客`
- `博客`

## 编排与协作
- 在完成初始化后，提醒用户：系统已经打好底座，可以使用 `ai-hub-ingest` 进行信息摄取了。
- 其他子技能（ingest, wiki, shadow）在运行时，第一步必须是静默读取上述共享的 json 配置文件。
