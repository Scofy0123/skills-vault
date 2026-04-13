# Skill Governance Policy

## Canonical Location

- Every self-managed skill must live under `/Users/scofy/.agents/skills/<skill-name>`.
- Canonical managed skills must be real directories, never symlinks.

## Consumer Roots

Treat these directories as publish-only entrypoints for managed skills:

- `/Users/scofy/.claude/skills`
- `/Users/scofy/.codex/skills`
- `/Users/scofy/.gemini/antigravity/skills`
- `/Users/scofy/.openclaw/skills`

Managed entries in consumer roots must stay symlinks to the canonical path in `/Users/scofy/.agents/skills`.

## Required Commands

- Create a new managed skill with `/Users/scofy/.agents/bin/skillsctl create`.
- Import a legacy skill into the vault with `/Users/scofy/.agents/bin/skillsctl import`.
- Rebuild consumer-root projections with `/Users/scofy/.agents/bin/skillsctl publish`.
- Validate the library with `/Users/scofy/.agents/bin/skillsctl audit --strict`.

## Prohibited Actions

- Do not create, edit, rename, or delete managed skills directly inside consumer roots.
- Do not replace a managed symlink with a real directory.
- Do not hand-edit the registry for routine moves when `skillsctl` can perform the operation.

## Failure Handling

- If `skillsctl audit --strict` fails, stop and report the drift.
- Do not patch around consumer roots by hand to “make it work”.
- Consumer tool startup wrappers must refuse to launch while the audit fails.
