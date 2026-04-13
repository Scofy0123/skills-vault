#!/usr/bin/env python3
"""
Wiki Search — Recursive full-text search over local wiki.

Usage:
    wiki_search.py <keyword> [--wiki-root <path>] [--limit <n>]

Examples:
    wiki_search.py "Agent memory"
    wiki_search.py "RAG" --limit 5
"""

import os
import sys
import re
from pathlib import Path

DEFAULT_WIKI_ROOT = Path.home() / "Documents" / "coding" / "wiki" / "wiki"


def search_wiki(keyword: str, wiki_root: Path, limit: int = 15):
    """Search all .md files under wiki_root for keyword matches."""
    results = []

    for md_file in wiki_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if keyword.lower() in line.lower():
                rel = md_file.relative_to(wiki_root)
                results.append((str(rel), i, line.strip()))

        if len(results) >= limit:
            break

    if not results:
        print(f"❌ No matches found for: {keyword}")
        print(f"   Searched: {wiki_root}")
        return

    print(f"🔍 Found {len(results)} match(es) for \"{keyword}\":\n")
    for rel_path, line_num, line_content in results[:limit]:
        # Highlight the keyword in output
        highlighted = re.sub(
            re.escape(keyword),
            f"**{keyword}**",
            line_content,
            flags=re.IGNORECASE
        )
        print(f"  📄 {rel_path}:{line_num}")
        print(f"     {highlighted}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: wiki_search.py <keyword> [--wiki-root <path>] [--limit <n>]")
        sys.exit(1)

    keyword = sys.argv[1]
    wiki_root = DEFAULT_WIKI_ROOT
    limit = 15

    if "--wiki-root" in sys.argv:
        idx = sys.argv.index("--wiki-root")
        wiki_root = Path(sys.argv[idx + 1]).expanduser()

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])

    search_wiki(keyword, wiki_root, limit)
