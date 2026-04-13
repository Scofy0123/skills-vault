---
name: local-wiki
description: "Karpathy llm-wiki 风格的本地 Markdown 知识库管理。当用户需要：(1) 将学习资料、文章、论文沉淀为结构化 Wiki 知识页；(2) 在本地知识库中搜索已有知识；(3) 从飞书团队 Wiki 同步内容到本地镜像；(4) 将个人思考/对话洞察存入知识库；(5) 对知识库进行健康检查(lint)时使用。触发词：沉淀、记笔记、知识库、wiki、本地搜索、sync。"
---

# Local Wiki — Karpathy llm-wiki 架构

基于 Karpathy llm-wiki 方法论的本地 Markdown 知识库。采用**双体共生架构**：飞书 Wiki 为团队共建 Source of Truth，本地 Wiki 为个人编译视图 + 检索镜像 + 思考工作台。

## Pre-flight

每次唤醒时，先确认 Wiki 根目录存在：
```bash
ls ~/Documents/coding/wiki/wiki/index.md
```
若不存在，执行初始化脚本：
```bash
python3 ~/.gemini/antigravity/skills/local-wiki/scripts/init_wiki.py
```

读取飞书配置（如果需要 sync）：
```bash
cat ~/.gemini/antigravity/skills/ai-learning-hub/assets/config.json
```

## Architecture

```
~/Documents/coding/wiki/              ← Obsidian Vault 根目录
├── schema/AGENTS.md                  ← LLM 行为约定
├── raw/                              ← 不可变原始素材
│   └── assets/                       ← 附件
├── wiki/                             ← LLM 维护的知识图谱
│   ├── index.md                      ← 全局导航（每次更新时维护）
│   ├── log.md                        ← 时间线（append-only）
│   ├── overview.md                   ← 综述页
│   ├── team-sync/                    ← 飞书团队 Wiki 本地镜像（只读）
│   ├── personal/                     ← 个人独有思考
│   │   ├── entities/                 ← 人物/公司
│   │   ├── concepts/                 ← 概念
│   │   └── sources/                  ← 源文章分析
│   └── comparisons/                  ← 对比分析
└── README.md
```

### 双体共生规则

| 方向 | 场景 | 写入位置 |
|------|------|----------|
| 外部文章 → 本地 | Ingest 学习资料 | `raw/` → `wiki/personal/sources/` |
| 对话洞察 → 本地 | 沉淀思考结论 | `wiki/personal/` |
| 飞书 → 本地 | 团队知识同步 | `wiki/team-sync/` |
| 本地 → 飞书 | 成果发布 | 使用 ai-learning-hub 的 Wiki Merge |

## Workflow 1: Ingest（知识摄入）

当用户提供文章 URL 或说"帮我沉淀这篇"时：

1. **获取原始内容**
   ```bash
   # 抓取网页内容
   read_url_content <URL>
   ```
   将原始 Markdown 存入 `raw/`：
   ```
   raw/YYYY-MM-DD-<slug>.md
   ```

2. **生成 Wiki 页面**
   阅读原始内容后，在 `wiki/personal/sources/` 生成摘要页，格式：
   ```markdown
   ---
   title: <标题>
   source: <URL>
   date: YYYY-MM-DD
   tags: [tag1, tag2]
   ---
   # <标题>
   ## 核心观点
   ...
   ## 关键引用
   ...
   ## 与现有知识的关联
   - 参见 [[concept-page]]
   ```

3. **更新交叉引用**
   - 检查 `wiki/personal/entities/` 和 `concepts/` 目录，更新或创建被提及的实体/概念页
   - 在相关页面添加 `[[wiki-link]]` 反向引用

4. **更新 index.md**
   在 index.md 的对应分类表中追加新条目。

5. **追加 log.md**
   ```markdown
   ## [YYYY-MM-DD] ingest | <标题>
   - Source: raw/<filename>
   - Pages created: <list>
   - Pages updated: <list>
   ```

## Workflow 2: Search（本地检索）

当用户询问已有知识时：

1. **先读 index.md** 定位相关页面
   ```bash
   cat ~/Documents/coding/wiki/wiki/index.md
   ```

2. **如果 index 不够精确，用 grep 穿透搜索**
   ```bash
   grep -rni "<关键词>" ~/Documents/coding/wiki/wiki/ --include="*.md" | head -20
   ```

3. **读取命中页面** 合成回答，引用来源页面链接。

## Workflow 3: Sync Down（飞书 → 本地镜像）

当用户说"同步飞书知识库"时：

1. **获取飞书 Wiki Space 节点列表**
   ```bash
   WIKI_SPACE=$(jq -r '.wiki_space_id' ~/.gemini/antigravity/skills/ai-learning-hub/assets/config.json)
   lark-cli wiki +node-list --space-id "$WIKI_SPACE" --as user
   ```

2. **遍历节点，拉取内容**
   针对每个节点：
   ```bash
   lark-cli docs +fetch --doc <DOC_TOKEN> --as user
   ```

3. **写入 team-sync/**
   每个文档存为 `wiki/team-sync/<slug>.md`，frontmatter 标注：
   ```yaml
   ---
   doc_token: <token>
   synced_at: YYYY-MM-DDTHH:MM:SS
   title: <原标题>
   ---
   ```

4. **更新 index.md** 中的 Team Sync 分区。
5. **追加 log.md**。

## Workflow 4: Capture（对话即沉淀）

当用户说"把刚才的结论沉淀下来"时：

1. 不抓外部链接，直接将对话中的洞察视为"新知识卡片"
2. 写入 `wiki/personal/` 下的合适子目录（entities/concepts/sources）
3. 更新交叉引用、index.md、log.md

## Workflow 5: Lint（健康检查）

当用户说"检查知识库"时，扫描并报告：
- 孤儿页（没有被 index.md 或其他页引用）
- 断链（引用了不存在的 `[[page]]`）
- 过期内容（team-sync 超过 7 天未同步的页面）
- 缺失概念页（被多次提及但无独立页面的概念）

统计信息：总页数、总字数、最近更新、按分类分布。
