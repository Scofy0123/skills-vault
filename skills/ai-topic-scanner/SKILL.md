---
name: ai-topic-scanner
version: 1.0.0
description: "AI资讯自动化选题扫描器工作流。调用 opencli 和 gh 获取 HackerNews, ProductHunt, GitHub 等全网技术社区近期的热门 AI 话题，提炼具备“高热度、强可视展示性（可拍性）”的选题内容，并将 Markdown 报告一键发布到指定的飞书文件夹。"
metadata:
  requires:
    bins: ["opencli", "lark-cli", "gh"]
  cliHelp: "This is an agentic workflow skill, no custom CLI."
---

# ai-topic-scanner 工作流

**目标**：当用户请求执行本 skill，或者要求“搜集今日选题”时，作为一个 Agent 严格执行以下流程。

## Phase 1: 扫描全网最新趋势 (Data Gathering)
在后台静默运行以下命令（由于数据可能较多，可以将结果重定向到 `/tmp/` 目录中的文件，或是直接保存在你的上下文记忆中），以获取各渠道的最新热门数据：

1. **HackerNews (HN 高分)**
   ```bash
   opencli hackernews top --limit 30 --format plain
   ```
2. **ProductHunt (当日热门)**
   ```bash
   opencli producthunt hot --format plain
   ```
3. **GitHub (近期高星 AI 仓库)**
   ```bash
   gh search repos --stars ">1000" --sort updated --topic artificial-intelligence --json name,description,stargazerCount,url --limit 10
   ```

*(如果在闲聊中用户指定了包含 Bilibili 或知乎等国内站点，请查阅 opencli 手册替换命令，默认仅抓取上述 3 个平台以确保无需额外登录即可工作)。*

## Phase 2: 大模型提炼提取 (AI Synthesis)

基于搜集到的生肉数据，在你的内心（Thought 环节）进行选题评估。你需要挑选出 **Top 5 到 Top 8** 最有价值的内容。
**评判及筛选标准（必须同时满足）**：
1. **强相关**：与 AI 效率、Agent、最新大模型或能改变普通人生活的产品/相关技术强绑定。
2. **热度极高**：在各自榜单具有显著的分数（如 HN 100+ 分，GitHub 1000+ stars）。
3. **具“可拍性”**：能够演示、有视觉冲击力、适合讲故事，容易产出短视频爆款或图文爆款。

## Phase 3: 格式化与输出至飞书 (Export to Feishu)

1. 将筛选出的高质量提取物转组装成一篇赏心悦目的 **Lark-flavored Markdown** 格式。
   排版要求：
   - 必须使用飞书特有的 `<callout>` / `表格` 或 `高亮区` 等样式（具体参见 `lark-doc` 目录的参考手册）。
   - 每一个精读入选的选题需包括：**中文翻译的标题**、**热度与平台**、**一句话亮点/痛点/可拍性分析**，以及**原文直达链接**。
2. 将此 Markdown 文本写入一个临时文件，例如 `/tmp/ai_topic_report.md`。
3. 使用 `lark-cli` 创建飞书文档，写入到用户指定的选题库文件夹 (`MAcefnMWplIdMjdV64QcszrQnDg`)：
   ```bash
   lark-cli docs +create --title "🔥 每日 AI 爆款选题追踪 - $(date +'%Y-%m-%d')" --folder-token MAcefnMWplIdMjdV64QcszrQnDg --markdown "$(cat /tmp/ai_topic_report.md)"
   ```
4. 捕获上述命令创建成功的 `doc_url`。

## Phase 4: 回复用户 (Report)
最终仅回复用户该任务已完成，并提供直接跳转的飞书文档链接（不要在对话区把冗长的抓取源文再打印一遍，以节约屏幕空间）。
