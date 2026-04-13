# V1-V4 Tiered Testing Methodology

This document details the four testing tiers used by skill-tester. Each tier trades fidelity for cost — choose the tier that matches your diagnostic stage.

## Overview

```
            Fidelity ────────────────────────────── Cost
V1  ██████████████████████████████████████████  ~6-8K tokens/run
V2  █████████████████████████                   ~2-3K tokens/run
V3  ████████                                    ~0-2K tokens/run
V4                                              ~0 tokens/run
```

---

## V1: Full Agent Run (End-to-End)

### What it does
Spawns a complete agent session: the agent reads the skill's SKILL.md, autonomously fetches inputs (documents, URLs), and produces the full output following the skill's complete workflow.

### When to use
- **First-time diagnosis**: You need to verify the agent's true end-to-end behavior, including how it interprets the skill instructions, what tools it calls, and what reasoning path it takes.
- **Verifying agent exploration behavior**: When you suspect the problem is in how the agent *navigates* to the information, not in its *understanding* of it.

### Operating procedure
1. For each test case, start a fresh context (ideally a separate `codex exec` or new conversation)
2. Provide only the skill path and the user prompt — let the agent explore freely
3. Record: final verdict, evidence cited, reasoning chain, total tokens
4. Run each case 3 times minimum for stability measurement

### Cost model
- Skill instructions loading: ~3K tokens
- Document fetching + content: ~1-3K tokens  
- Model reasoning + output: ~2K tokens
- **Per-run total: ~6-8K tokens**
- **Important**: If running multiple cases in the same conversation, context accumulates. Case N carries the context of cases 1 through N-1. This inflates costs and can bias results (the model "learns" from earlier runs).

### Real-world benchmark
From the check-prd H1-H4 experiment:
- 14 test cases × 3 runs = 45 total runs
- Total consumption: **~86.7 万 tokens** (~867K tokens)
- Average per run: ~19K tokens (inflated by context accumulation)

### Pitfalls
- **Context leakage**: Running multiple cases in one conversation lets the model learn from earlier results. Mitigate by explicit "treat each run as independent" instructions, but this is imperfect.
- **Agent path variance**: The agent may take different exploration paths on each run, introducing variance unrelated to the factor under test.
- **High cost**: 45 runs at V1 costs ~87万 tokens. Reserve for initial diagnosis only.

---

## V2: Pre-fetched Input + Direct Model Judgment

### What it does
Separates the "fetch" step from the "judge" step:
1. **Pre-fetch**: Batch-download all documents/inputs before testing begins (using `lark-cli docs +fetch`, file reads, etc.)
2. **Judge**: Feed the pre-fetched content directly to the model with a minimal, focused prompt that asks only about the specific factor under test

### When to use
- **Model understanding is the bottleneck**: You know the agent can find the document — the question is whether the model can *understand* and *judge* it correctly.
- **Precision diagnosis**: When you want to isolate the model's judgment from the agent's exploration behavior.
- **Moderate sample sizes**: 10-30 test cases.

### Operating procedure
1. Batch-fetch all test documents upfront:
   ```bash
   lark-cli docs +fetch --url <url> --output <local-path>
   ```
2. For each case, construct a minimal prompt:
   ```
   Given this document content:
   <pre-fetched content>
   
   Does this document contain [specific evidence for dimension X]?
   Answer: { "verdict": "covered|partial|missing", "evidence_location": "...", "reasoning": "..." }
   ```
3. Do NOT load the full skill's 14-dimension framework — only the dimension under test
4. Run 3 times per case

### Cost model
- Pre-fetch: one-time CLI cost (negligible tokens)
- Per-run: document content (~1-2K) + focused prompt (~200) + response (~500) = **~2-3K tokens**
- **45 runs at V2: ~10-14 万 tokens** (54.5% reduction vs V1, confirmed by real measurement)

### When NOT to use
- When the problem might be in the agent's *exploration* behavior (e.g., it fetched the wrong URL, used the wrong tool). V2 bypasses exploration entirely.

---

## V3: Local Rules First + Model for Gray Zone

### What it does
Applies deterministic local rules (regex, keyword matching, structural analysis) as a first pass. Only sends "gray zone" cases — where rules are insufficient — to the model for judgment.

### When to use
- **Large-scale regression**: 30+ test cases where most are clear-cut
- **After initial diagnosis**: You've identified the root cause and need to verify the fix didn't break other cases
- **A/B testing at scale**: Comparing before/after across many samples

### Operating procedure
1. Pre-fetch all inputs (same as V2)
2. Write local rule scripts (Agent generates these on-the-fly based on the specific skill):
   ```python
   # Example: check if document contains "业务背景" section
   def rule_judge(content: str) -> str:
       """Returns 'covered', 'missing', or 'gray'"""
       keywords = ["业务背景", "项目背景", "背景介绍", "Background"]
       for kw in keywords:
           if kw in content:
               return "covered"
       # Check for semantic equivalents — can't be sure without model
       if any(w in content for w in ["为什么做", "痛点", "现状"]):
           return "gray"
       return "missing"
   ```
3. For "covered" and "missing" results → record directly (0 tokens)
4. For "gray" results → send to model with V2-style focused prompt

### Cost model
- Typically 60-80% of cases are clear-cut → 0 tokens
- Remaining 20-40% use V2 pricing → ~2-3K tokens each
- **45 runs at V3: ~2-6 万 tokens** (85-95% reduction vs V1)

### Limitations
- Rules can't handle semantic nuance. If 90% of your cases are semantically ambiguous, V3 degenerates to V2.
- Rule scripts are skill-specific — they must be written fresh for each skill being tested.

---

## V4: Pure Local Rules

### What it does
100% deterministic, script-based judgment. No model involvement at all.

### When to use
- **CI/CD smoke tests**: Fast, zero-cost, fully deterministic
- **Structural validation**: Checking that required sections exist, formatting is correct, links are valid
- **Known-pattern regression**: Re-checking cases where the expected pattern is unambiguous

### Operating procedure
1. Write comprehensive rule scripts
2. Run all cases through rules
3. Results are fully deterministic — no need for 3x runs

### Cost model
- **0 tokens**
- Execution time: milliseconds

### Limitations
- Cannot handle any semantic judgment
- False negatives on non-standard expressions (e.g., "业务背景" written as "我们为什么要做这个项目")
- Only useful after you've confirmed the pattern through V1/V2

---

## Tier Selection Decision Tree

```
                    ┌─────────────────────┐
                    │ What's the testing  │
                    │ objective?          │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        First-time      Regression      CI / Smoke
        diagnosis       after fix       test
              │               │               │
              ▼               ▼               ▼
     ┌────────────┐   ┌─────────────┐   ┌─────────┐
     │ Need E2E   │   │ Sample      │   │ V3 or   │
     │ agent      │   │ count?      │   │ V4      │
     │ behavior?  │   │             │   └─────────┘
     └──┬─────┬───┘   └──┬──────┬──┘
        │     │           │      │
       Yes    No        < 10   ≥ 10
        │     │           │      │
        ▼     ▼           ▼      ▼
      ┌──┐  ┌──┐       ┌──┐  ┌──┐
      │V1│  │V2│       │V2│  │V3│
      └──┘  └──┘       └──┘  └──┘
```

---

## Cost Comparison Summary

Based on check-prd 45-run experiment:

| Tier | Per-Run Tokens | 45-Run Total | vs V1 |
|:-----|:--------------|:-------------|:------|
| V1 | ~19K (avg, with context bloat) | ~87万 | baseline |
| V2 | ~2-3K | ~12万 | **-86%** |
| V3 | ~0-2K | ~4万 | **-95%** |
| V4 | 0 | 0 | **-100%** |

> **Recommendation**: Start with V1 for the first 3-5 cases to calibrate, then switch to V2 for the remaining diagnosis. Use V3 for regression after fixing.
