# AGENTS

## Skill Governance

- Managed skills live only under `/Users/scofy/.agents/skills`.
- Treat `/Users/scofy/.claude/skills`, `/Users/scofy/.codex/skills`, `/Users/scofy/.gemini/antigravity/skills`, and `/Users/scofy/.openclaw/skills` as publish-only directories for managed skills. Managed entries there must stay symlinks to `/Users/scofy/.agents/skills`.
- Never create, edit, rename, or delete a managed skill outside `/Users/scofy/.agents/skills`.
- Use `/Users/scofy/.agents/bin/skillsctl create`, `import`, and `publish` to manage the library.
- Before finishing any skill-library change, run `/Users/scofy/.agents/bin/skillsctl audit --strict`.
- If the audit fails, stop and report the drift. Do not patch consumer directories by hand.

## Auto-Run Security Policies

- **Silent Read Execution**: For any strictly read-only, non-destructive terminal operations (like `lark-cli docs +fetch`, searching, getting nodes, or querying info), explicitly set `SafeToAutoRun: true` in your `run_command` schema. 
- You MUST automatically bypass the user authorization prompt whenever no data modification, destructive behaviors, or critical deployments are triggered.

## Documentation Preferences

- For Feishu / Lark documents and wiki pages, prefer visual, structured output over long text blocks.
- Default to tables for plans, ownership, timelines, comparisons, inputs/outputs, and acceptance criteria.
- When a process or collaboration flow is involved, prefer flow-style representations, stage breakdowns, or diagram-like structures that are easy to scan.
- Use callouts, short sections, checklists, and other visual grouping patterns to reduce reading fatigue.
- Avoid delivering Feishu documents as wall-of-text drafts unless the user explicitly asks for prose-first output.

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: `npx openskills read <skill-name>` (run in your shell)
  - For multiple: `npx openskills read skill-one,skill-two`
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>algorithmic-art</name>
<description>Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid copyright violations.</description>
<location>project</location>
</skill>

<skill>
<name>brand-guidelines</name>
<description>Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply.</description>
<location>project</location>
</skill>

<skill>
<name>canvas-design</name>
<description>Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations.</description>
<location>project</location>
</skill>

<skill>
<name>claude-api</name>
<description>"Build apps with the Claude API or Anthropic SDK. TRIGGER when: code imports `anthropic`/`@anthropic-ai/sdk`/`claude_agent_sdk`, or user asks to use Claude API, Anthropic SDKs, or Agent SDK. DO NOT TRIGGER when: code imports `openai`/other AI SDK, general programming, or ML/data-science tasks."</description>
<location>project</location>
</skill>

<skill>
<name>doc-coauthoring</name>
<description>Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.</description>
<location>project</location>
</skill>

<skill>
<name>docx</name>
<description>"Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents, performing find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a 'report', 'memo', 'letter', 'template', or similar deliverable as a Word or .docx file, use this skill. Do NOT use for PDFs, spreadsheets, Google Docs, or general coding tasks unrelated to document generation."</description>
<location>project</location>
</skill>

<skill>
<name>frontend-design</name>
<description>Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.</description>
<location>project</location>
</skill>

<skill>
<name>internal-comms</name>
<description>A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident reports, project updates, etc.).</description>
<location>project</location>
</skill>

<skill>
<name>mcp-builder</name>
<description>Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).</description>
<location>project</location>
</skill>

<skill>
<name>pdf</name>
<description>Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.</description>
<location>project</location>
</skill>

<skill>
<name>pptx</name>
<description>"Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."</description>
<location>project</location>
</skill>

<skill>
<name>skill-creator</name>
<description>Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.</description>
<location>project</location>
</skill>

<skill>
<name>slack-gif-creator</name>
<description>Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack."</description>
<location>project</location>
</skill>

<skill>
<name>template</name>
<description>Replace with description of the skill and when Claude should use it.</description>
<location>project</location>
</skill>

<skill>
<name>theme-factory</name>
<description>Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.</description>
<location>project</location>
</skill>

<skill>
<name>web-artifacts-builder</name>
<description>Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.</description>
<location>project</location>
</skill>

<skill>
<name>webapp-testing</name>
<description>Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.</description>
<location>project</location>
</skill>

<skill>
<name>xlsx</name>
<description>"Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved."</description>
<location>project</location>
</skill>

<skill>
<name>apple-buying-advisor</name>
<description>帮助比较近 5 年内的 Apple 产品，并给出最值得买的选择。适用于 iPad、Mac、iPhone、Watch、AirPods 以及相邻产品线对比；适用于跨代比较、同代新品与二手对比、相邻产品线错位对比；当用户希望基于分层价格、代际价值、甜点配置、预算匹配和结构化二手市场字段得到 Top 3 推荐时使用。最终推荐必须有明确的飞书表格作为数据依据，并且该表格需创建在用户指定文档目录下。</description>
<location>global</location>
</skill>

<skill>
<name>feishu-research-indexer</name>
<description>"建立和维护基于飞书的研究捕获工作流。当用户要求将文章提取/抓取到飞书、建立或更新飞书 Bitable（多维表格）、为每篇文章创建一个飞书文档、或将文章列表转换为结构化的飞书研究资产时，TRIGGER THIS SKILL（触发此技能）。关键信号：'抓取网页...并建飞书索引', '整理到飞书 Research Bitable', '建逐篇整理文档'。如果是简单的 PDF 总结、基础翻译、代码生成或一般性的飞书使用问题，DO NOT trigger（请勿触发）。"</description>
<location>global</location>
</skill>

<skill>
<name>find-skills</name>
<description>Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.</description>
<location>global</location>
</skill>

<skill>
<name>todo-reminder</name>
<description>"记录和管理每日重要 TODO，通过飞书主动催办提醒。当用户提到待办、TODO、要做的事、任务清单、记一下、提醒我、今天要做什么、完成了XX 等表达时触发此 skill。也会在 Heartbeat 时自动检查未完成和逾期的 TODO 并主动催促用户。"</description>
<location>global</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
