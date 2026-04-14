# Skill Governance

- Managed skills live only under `/Users/scofy/.agents/skills`.
- Approved external bundles may only appear in `/Users/scofy/.agents/skills` as audited symlinks to `/Users/scofy/.agents/vendor/...`.
- Treat `/Users/scofy/.claude/skills`, `/Users/scofy/.codex/skills`, `/Users/scofy/.gemini/antigravity/skills`, and `/Users/scofy/.openclaw/skills` as publish-only directories for managed skills. Managed entries there must stay symlinks to `/Users/scofy/.agents/skills`.
- Never create, edit, rename, or delete a managed skill outside `/Users/scofy/.agents/skills`.
- Use `/Users/scofy/.agents/bin/skillsctl create`, `import`, and `publish` to manage the library.
- Before finishing any skill-library change, run `/Users/scofy/.agents/bin/skillsctl audit --strict`.
- If the audit fails, stop and report the drift. Do not patch consumer directories by hand.
