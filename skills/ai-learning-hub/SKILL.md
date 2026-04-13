---
name: ai-learning-hub
description: "AI 学习管理站核心业务流（Phase 2: 批量摄取配置化版）。用于按照配置表自动批量抓取全网资讯（Batch Ingest），以及将新知识沉淀到维基库（Wiki Merge）。"
---

# AI Learning Hub (V2: Dynamic & Batch)

## Setup & Pre-flight (首次使用向导/动态配置)

每次唤醒执行本技能时，请第一步务必阅读本地配置文件，切勿再使用硬编码的 Token。配置文件已封装在本技能内部：
```bash
cat ~/.gemini/antigravity/skills/ai-learning-hub/assets/config.json
```
*(如果没有这个文件，请先引导用户填入飞书的各项 Token 并创建好该 JSON。后续的 `base_token`, `table_id`, `user_id`, `wiki_id` 全局从该 JSON 文件中读取)*

---

## Workflow 1: Batch Ingest (批量多源摄取流)

当用户说：“执行今日巡查”或“抓取最新资讯”时，执行以下全自动扫街流程：

### Step 1: 读取「抓取表」清单 (Load Configs)
使用 `jq` 从本地配置文件中精准获取环境变量，然后拉取当前设定的所有活体任务（严禁你自己大脑主观脑补）：
```bash
BASE_TOKEN=$(jq -r '.base_token' ~/.gemini/antigravity/skills/ai-learning-hub/assets/config.json)
FETCH_TABLE=$(jq -r '.tables.fetch_config' ~/.gemini/antigravity/skills/ai-learning-hub/assets/config.json)
lark-cli base +record-list --base-token "$BASE_TOKEN" --table-id "$FETCH_TABLE"
```

### Step 2: 遍历深度提取 (Iterate & Extract)
遍历上述列表，针对每一个有效目标记录（抓取其对应的 `URL`、`平台` 或 `检索词`）：
调用对应的抓取命令（例如 `opencli web read <URL>` 去扫页面，或者 `opencli <平台>` 的专有命令）。
在你（大模型Agent）的内存上下文里，直接阅读抓取回来的长文本，并逐个浓缩成 100 词左右的“超纯净度”专业简报。

### Step 3: 落入「信息流」基地 (Upsert to Base)
针对分析完的资讯，务必将其 JSON 存入到 `/tmp/record.json` 中。
```bash
# JSON 格式参考: {"标题": "...", "简介": "...", "状态": "待处理", "扫描日期": 1712390400000, "信息层级": "🔴 每日速览", ...}
```
保存好由你生成的 `/tmp/record.json` 文件后，立刻执行以下官方封装脚本（防挂起专属）：
```bash
~/.gemini/antigravity/skills/ai-learning-hub/scripts/upsert_feed.sh /tmp/record.json
```

### Step 4: 汇总飞书推送报纸 (Batch IM Push)
全部入库后，将所有的抓取结果汇总成一篇多节点的 Markdown 清晨/晚间读物。为了避免终端里的隐形式换行破坏，**必须**先把内容安全写进 `/tmp/report.md` 中。

> 🚨 **极端避坑守则 (防御静默黑洞与保证直达) ：**
> 1. 飞书对异常 Markdown 链接（例如把一个纯命令 `from:karpathy` 放在括号里）会一律静默屏蔽。
> 2. 但为了保证极简阅读的“直达新闻”体验，**你绝对不能放弃链接！** 每条资讯都必须有一条可跳转的超链接。
> 3. 如果原始资讯本身有绝对 URL（如 `https://news.ycombinator...`），请直接使用它。
> 4. 如果任务目标只是一个非链接的暗号或查询词（如 `from:ylecun`），你必须把它 **动态补全组装成能用的真实网站搜索网址** 再填入。例如拼接成：`https://x.com/search?q=from%3Aylecun`。
> 5. **终极防脱落铁律**：飞书的解析引擎不支持**粗体嵌套链接**。绝不允许写成 `**[标题](URL)**`，必须写成 `**序号.** [标题](URL)`，让链接独立在粗体标记之外！

确认 `/tmp/report.md` 写入成功后，执行：
```bash
~/.gemini/antigravity/skills/ai-learning-hub/scripts/send_im.sh /tmp/report.md
```

---

## Workflow 2: Wiki Merge (知识库融合更新)

当用户说：“把刚才的讨论沉淀下来”，或者指令明确保留进某个 Wiki 节点。

### Step 1: 拉取历史文档 (Fetch Truth)
如果你知道目标文档的 DOC_TOKEN (可根据 `CONFIG.wiki_space_id` 搜查而得)：
```bash
lark-cli docs +fetch --doc <DOC_TOKEN> --as user
```
**阅读并沉浸式理解这篇返回的旧版 Markdown 内容。**

### Step 2: 知识融合与重新排版 (Agentic Fusion)
就像《文明》游戏的建筑升级一样，将新获取的高级知识卡片与这段历史 Markdown 进行化学融合：
- 不要只是堆砌尾部；寻找历史文档中对应的底层章节进行重构、增补。
- 开头加入 `> 系统最后融合迭代日志：YYYY-MM-DD` 追踪戳。

### Step 3: 原地覆写升级 (Overwrite)
把你处理好的最终篇 Markdown 存入本地缓存如 `/tmp/merged_doc.md`，然后覆写云端：
```bash
lark-cli docs +update --doc <DOC_TOKEN> --mode overwrite --markdown "$(cat /tmp/merged_doc.md)" --as user
```

---

## Workflow 3: Shadow Search (本地影子防爆检索)

如果用户询问某些既往飞书知识（如：“帮我找一下关于 AI Agent 记忆系统的理论”），禁止拉取飞书云端全集：
使用本地影子系统进行零 Token 开销极速碎片穿透：
```bash
python3 ~/.gemini/antigravity/skills/ai-learning-hub/scripts/shadow.py search "Agent 记忆"
```
*(如果没有找到，可能源文档发生了变动。此时可以执行 `python3 shadow.py sync <DOC_TOKEN>` 来强行从云端拉下最新版重新切片，再进行 Search)*
你（Agent）看到碎片回包后，给用户组织语言作答，并附带碎片标记的源 `DOC_TOKEN` 飞书链接。

---

## Workflow 4: Query as Ingest (对话即沉淀)

当你在长轮聊天中产生了一个包含表格、图册或者极好的思考结论时，且用户说：“把刚才的结论沉淀下来”。
你不需要去抓任何外部链接！
直接将你刚发过的那篇“好思考”，视为“新知识卡片”，无缝跳转回到 **Workflow 2: Wiki Merge** 流程的 `Step 1`，去主动加载用户飞书的维基主干文档，将这段聊天产物给覆写存进飞书中！这赋予了你拥有真正的【永久性群体记忆】的能力。
