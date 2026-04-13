# Unified Skill Vault

This workspace is the canonical home for every self-managed skill on this machine.

## Rules

- Canonical skill content lives only in `/Users/scofy/.agents/skills`.
- Consumer roots publish managed skills as symlinks only:
  - `/Users/scofy/.claude/skills`
  - `/Users/scofy/.codex/skills`
  - `/Users/scofy/.gemini/antigravity/skills`
  - `/Users/scofy/.openclaw/skills`
- Use `/Users/scofy/.agents/bin/skillsctl` for creation, import, publish, audit, and diagnostics.
- Before finishing any skill change, run `skillsctl audit --strict`.

## Layout

- `skills/`: canonical managed skill directories
- `skills-registry.yaml`: YAML-compatible JSON registry for managed skills and exposure rules
- `bin/skillsctl`: library management CLI
- `bin/{claude,codex,gemini,openclaw}`: preflight wrappers that block startup when the library drifts
- `.githooks/`: Git hooks that enforce `skillsctl audit --strict`
- `policies/`: shared governance text and Claude project template
- `EXPOSURE_MATRIX.md`: one-time recorded exposure snapshot for managed skills

## Workflow

1. Edit a managed skill only under `/Users/scofy/.agents/skills/<name>`.
2. Run `skillsctl publish` when exposure changes or after importing a legacy skill.
3. Run `skillsctl audit --strict`.
4. Commit and push from `/Users/scofy/.agents`.

## Notes

- `skills-registry.yaml` uses JSON syntax inside a `.yaml` file so the registry stays YAML-compatible without extra parser dependencies.
- The canonical repo owner is the local machine. GitHub mirrors this workspace; it is not the source of truth.
