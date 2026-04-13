#!/usr/bin/env python3
"""
Wiki Initializer — Creates the local wiki directory structure
following Karpathy's llm-wiki architecture.

Usage: python3 init_wiki.py [--wiki-root <path>]
Default root: ~/Documents/coding/wiki
"""

import os
import sys
from pathlib import Path
from datetime import datetime

DEFAULT_WIKI_ROOT = Path.home() / "Documents" / "coding" / "wiki"


def init_wiki(wiki_root: Path):
    """Initialize the wiki directory structure and core files."""

    if (wiki_root / "wiki" / "index.md").exists():
        print(f"⚠️  Wiki already initialized at {wiki_root}")
        print("   index.md exists. Skipping to avoid overwriting.")
        return

    # Create directory tree
    dirs = [
        "schema",
        "raw/assets",
        "wiki/team-sync",
        "wiki/personal/entities",
        "wiki/personal/concepts",
        "wiki/personal/sources",
        "wiki/comparisons",
    ]
    for d in dirs:
        (wiki_root / d).mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    # --- AGENTS.md (schema) ---
    (wiki_root / "schema" / "AGENTS.md").write_text(f"""\
# Wiki Schema & Conventions

> Last updated: {today}

## Directory Roles

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `raw/` | Human + Web Clipper | Immutable source materials. LLM reads only. |
| `wiki/team-sync/` | LLM (auto-sync) | Read-only mirror of Feishu team Wiki |
| `wiki/personal/` | LLM + Human | Personal synthesis, notes, analysis |
| `wiki/` (root files) | LLM | Cross-cutting: index, log, overview |
| `schema/` | Human + LLM co-evolve | This file. Conventions and workflows. |

## Page Format

Every wiki page uses YAML frontmatter:

```yaml
---
title: Page Title
date: YYYY-MM-DD
tags: [tag1, tag2]
type: entity | concept | source | comparison | sync
---
```

## Linking Convention

Use Obsidian-style `[[wiki-links]]` for cross-references.
Use relative paths within the wiki/ directory.

## Ingest Protocol

When ingesting a new source:
1. Save raw content to `raw/YYYY-MM-DD-<slug>.md`
2. Create source summary page in `wiki/personal/sources/`
3. Update or create relevant entity/concept pages
4. Add entry to `wiki/index.md`
5. Append entry to `wiki/log.md`
""")

    # --- index.md ---
    (wiki_root / "wiki" / "index.md").write_text(f"""\
# Wiki Index

> Auto-maintained by LLM. Last updated: {today}

## Team Sync (Feishu Mirror)

| Page | Title | Synced At |
|------|-------|-----------|
| _(empty — run Sync Down to populate)_ | | |

## Personal Sources

| Page | Summary | Date | Tags |
|------|---------|------|------|
| _(empty — ingest your first source)_ | | | |

## Entities

| Page | Type | Mentions |
|------|------|----------|
| | | |

## Concepts

| Page | Summary |
|------|---------|
| | |

## Comparisons

| Page | Items Compared |
|------|----------------|
| | |
""")

    # --- log.md ---
    (wiki_root / "wiki" / "log.md").write_text(f"""\
# Wiki Log

> Append-only chronological record. Parseable: `grep "^## \\[" log.md | tail -5`

## [{today}] init | Wiki Initialized
- Created directory structure at {wiki_root}
- Core files: index.md, log.md, overview.md, AGENTS.md
""")

    # --- overview.md ---
    (wiki_root / "wiki" / "overview.md").write_text(f"""\
# Wiki Overview

> Global synthesis page. Updated as knowledge accumulates.

This wiki follows the [Karpathy llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) architecture.

## Architecture: Dual-Wiki (双体共生)

- **Feishu Wiki** (cloud): Team-maintained Source of Truth
- **Local Wiki** (this): Personal compilation view + search cache + thinking workspace

## Statistics

- Total pages: 0
- Last ingest: —
- Last sync: —
""")

    # --- README.md ---
    (wiki_root / "README.md").write_text(f"""\
# Local Wiki

Personal knowledge base following Karpathy's llm-wiki pattern.

- Open this directory in **Obsidian** for graph visualization
- LLM maintains `wiki/` — human curates `raw/` sources
- Feishu team Wiki mirrors live in `wiki/team-sync/`

Initialized: {today}
""")

    # --- .gitignore ---
    (wiki_root / ".gitignore").write_text("""\
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.DS_Store
""")

    print(f"✅ Wiki initialized at {wiki_root}")
    print(f"   📂 Directories: {len(dirs)} created")
    print(f"   📄 Core files: AGENTS.md, index.md, log.md, overview.md, README.md")
    print(f"\n   Next: open {wiki_root} in Obsidian")


if __name__ == "__main__":
    root = DEFAULT_WIKI_ROOT
    if "--wiki-root" in sys.argv:
        idx = sys.argv.index("--wiki-root")
        root = Path(sys.argv[idx + 1]).expanduser()

    init_wiki(root)
