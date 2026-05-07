# Skills Vault

`skills-vault` 是这台机器上的统一 Agent Skill 管理仓库。它把自维护技能收束到一个可信来源，再通过可审计的 symlink 发布给 Claude、Codex、Gemini 和 OpenClaw，避免同一个技能在多个工具目录里各自漂移。

这个仓库的目标很简单：技能只维护一份，暴露可以有多份，所有变更都要能被审计。

## 它解决什么问题

多 Agent 环境里，技能通常会散落在不同工具自己的目录下：

- Claude 读 `/Users/scofy/.claude/skills`
- Codex 读 `/Users/scofy/.codex/skills`
- Gemini 读 `/Users/scofy/.gemini/antigravity/skills`
- OpenClaw 读 `/Users/scofy/.openclaw/skills`

如果直接在这些目录里复制和修改技能，很快就会出现版本不一致、别名失控、外部技能混入、启动时加载错版本等问题。`skills-vault` 用一个注册表和一套 CLI 把这些动作集中管理：

- 自维护技能只存在于 `/Users/scofy/.agents/skills`
- 消费端目录只放指向 canonical skill 的 symlink
- 外部 bundle 只能作为受控投影进入技能树
- 每次技能变更前后都可以用 `skillsctl audit --strict` 校验状态
- 各 Agent 启动包装器会在审计失败时拒绝启动

## 核心能力

- **Canonical skill library**：所有受管技能以真实目录形式保存在 `/Users/scofy/.agents/skills/<skill-name>`。
- **Cross-agent publishing**：通过 `skills-registry.yaml` 决定每个技能暴露给哪些工具，以及是否带 alias。
- **Audited symlink projections**：Claude、Codex、Gemini、OpenClaw 的技能入口只接受审计通过的 symlink。
- **External bundle governance**：外部技能包放在 `/Users/scofy/.agents/vendor`，只通过注册表声明的投影进入技能树。
- **Preflight wrappers**：`bin/claude`、`bin/codex`、`bin/gemini`、`bin/openclaw` 会在启动真实命令前执行严格审计。
- **Portable policy text**：`policies/` 提供可复用的技能治理说明和项目级 `AGENTS.md` 模板。

## 工作模型

```text
/Users/scofy/.agents/skills
  canonical managed skills
          |
          v
skills-registry.yaml
  exposure, aliases, external bundles
          |
          v
skillsctl publish
  rebuild audited symlinks
          |
          v
consumer roots
  Claude / Codex / Gemini / OpenClaw
```

GitHub 上的这个仓库是本机技能库的镜像，便于备份、审阅和版本追踪；本机的 `/Users/scofy/.agents` 才是运行时事实来源。

## 快速使用

进入 canonical repo：

```bash
cd /Users/scofy/.agents
```

检查技能库是否干净：

```bash
/Users/scofy/.agents/bin/skillsctl audit --strict
```

创建新技能：

```bash
/Users/scofy/.agents/bin/skillsctl create my-skill --expose codex gemini
```

导入旧技能：

```bash
/Users/scofy/.agents/bin/skillsctl import /path/to/legacy-skill --name my-skill --expose claude codex
```

重新发布所有消费端投影：

```bash
/Users/scofy/.agents/bin/skillsctl publish
```

查看库状态并运行严格审计：

```bash
/Users/scofy/.agents/bin/skillsctl doctor
```

## 日常变更流程

1. 只在 `/Users/scofy/.agents/skills/<skill-name>` 下编辑受管技能。
2. 如果新增、导入、改名、改 alias 或调整暴露范围，使用 `skillsctl` 完成，不手改消费端目录。
3. 如需更新外部 bundle，在 `/Users/scofy/.agents/vendor/<bundle>` 中更新源 clone，再重新审计。
4. 运行 `/Users/scofy/.agents/bin/skillsctl audit --strict`。
5. 审计通过后再提交和推送 `/Users/scofy/.agents`。

## 项目结构

| 路径 | 说明 |
| --- | --- |
| `skills/` | 受管技能的 canonical 目录 |
| `skills-registry.yaml` | YAML-compatible JSON 注册表，记录技能、暴露范围、alias 和外部 bundle |
| `bin/skillsctl` | 技能库管理 CLI，负责 create、import、publish、audit、doctor |
| `bin/claude` / `bin/codex` / `bin/gemini` / `bin/openclaw` | 启动前审计包装器 |
| `.githooks/` | 提交和推送前强制运行严格审计 |
| `policies/` | 技能治理政策与可复用 Agent 指令模板 |
| `EXPOSURE_MATRIX.md` | 技能暴露关系的一次性迁移快照 |

## 治理原则

- 不在消费端目录直接创建、修改、删除受管技能。
- 不把消费端 symlink 替换成真实目录。
- 不从投影路径手改外部 bundle。
- 不绕过 `skillsctl audit --strict` 的失败结果。
- 不把 GitHub 镜像当作运行时事实来源。

如果审计失败，先修复 canonical registry、技能目录或外部 bundle 的真实漂移，再重新发布。不要手动修补消费端目录来“让它看起来通过”。

## 当前覆盖

这个 vault 当前覆盖的技能类型包括：

- Feishu / Lark 文档、云盘、日历、任务、多维表格、会议纪要和 IM 工作流
- PRD 创建、PRD 审查和飞书 PRD 闭环评审
- AI 资讯抓取、学习中心、选题扫描和知识沉淀
- 本地 Wiki、PDF 翻译、技能创建、技能测试、自我改进和长期记忆
- 外部 `superpowers` bundle 的受控投影

具体技能清单、暴露目标和 alias 以 `skills-registry.yaml` 为准。
