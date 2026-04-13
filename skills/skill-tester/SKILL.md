---
name: skill-tester
description: Diagnose and fix quality issues in existing skills through hypothesis-driven root cause analysis. Use when a skill produces incorrect, inconsistent, or degraded outputs and you need to figure out WHY — not just WHAT failed. Covers controlled-variable experiments, factor decomposition, tiered testing (V1-V4), and regression verification. Use this skill whenever the user reports a skill is "not working right", "giving wrong results", "sometimes fails", or wants to systematically test whether a specific factor causes failures. Also use when the user says "帮我测一下这个 skill"、"skill 效果不对"、"为什么误判了" or similar diagnostic requests.
---

# Skill Tester

A diagnostic tool for systematically finding and fixing quality problems in existing skills. While skill-creator helps you *build* a skill and verify it works, skill-tester helps you figure out *why* it's failing in specific scenarios and confirm your fix actually works.

Think of it this way: skill-creator is the test suite you run during development. skill-tester is the root cause analysis you do when production users report bugs.

## When to use this vs skill-creator

| Situation | Use |
|:----------|:----|
| "I want to build a new skill" | skill-creator |
| "My skill's output is wrong on certain inputs" | **skill-tester** |
| "I need to A/B compare two skill versions" | skill-creator (comparator) |
| "I need to find out *which factor* causes the failure" | **skill-tester** |
| "I fixed the skill, does it still break?" | **skill-tester** |
| "Run the eval suite" | skill-creator |

---

## The Diagnostic Workflow

```
User reports a problem (or proactively initiates testing)
     │
     ▼
Phase 1: Problem Modeling — turn vague complaints into testable hypotheses
     │
     ▼
Phase 2: Test Matrix — design controlled experiments with positive/negative samples
     │
     ▼
Phase 3: Tiered Execution — pick V1-V4 based on cost/fidelity tradeoff
     │
     ▼
Phase 4: Root Cause Analysis — locate the factor(s) causing failures
     │
     ▼
Phase 5: Fix & Regress — modify the skill, re-run, confirm the delta
```

### Phase 1: Problem Modeling

The goal is to convert "it doesn't work" into specific, testable hypotheses. Guide the user through:

1. **Identify the symptom**: Which dimension/metric/output is wrong? Get a concrete example — "the correct answer is X but it said Y".
2. **Assess reproducibility**: Does it fail every time, or intermittently? On which inputs?
3. **Generate hypotheses**: Based on the symptom, propose candidate causes. Check `references/hypothesis-catalog.md` for reusable templates. Common patterns:
   - **Structural**: Evidence is in an unusual location, format, or nesting depth
   - **Scale**: Document is too long, causing attention degradation
   - **Cognitive**: Too many dimensions evaluated simultaneously
   - **Semantic**: Evidence uses informal/ambiguous language
   - **Input**: Different input channels (URL vs paste vs file) behave differently

Output: A ranked list of hypotheses, each with:
- ID (e.g., H1, H2)
- Description ("Long documents cause attention degradation")
- The specific factor being tested ("document length")
- Expected behavior if hypothesis is correct

### Phase 2: Test Matrix Generation

For each hypothesis, design controlled-variable experiments following these principles:

**Core design rules:**
- **One variable at a time**: Each experiment changes exactly one factor
- **High-Fidelity Context**: NEVER use "Lorem Ipsum" or random generic filler to simulate long contexts. AI models easily filter out random noise. Stress tests must use **highly realistic domain noise** (e.g., dense API specs, detailed database tables, genuine business processes rules) to accurately simulate real-world cognitive load.
- **Multi-Scale Testing (S/M/L)**: When testing for attention degradation or multi-task interference, test across different volume tiers:
  - **S-Tier (~1.5K words)**: Comfortable baseline, mimics simple feature PRDs.
  - **M-Tier (~5K words)**: Elevated load, mimics module-level specs.
  - **L-Tier (~15K+ words)**: Extreme stress, mimics complex system specs.
- **Positive + negative samples**: Always include a known-failing negative sample as the gate test
- **Negative-first + early stop**: Run negative samples first. If the model correctly identifies the negative case (e.g., 2/3 correct), proceed to positive samples. If it fails the gate, the hypothesis is already informative.
- **Minimum 3 independent runs per case**: To measure stability (majority vote)

**Test case structure:**
```json
{
  "case_id": "TC-H1-01",
  "hypothesis": "H1",
  "type": "positive",
  "description": "Baseline: evidence in standard location",
  "input": "<document or reference>",
  "expected_verdict": "covered",
  "controlled_variable": "position=standard",
  "evaluation_criteria": "Model correctly identifies evidence and cites location"
}
```

**Compatibility with skill-creator**: Test cases follow the same `evals.json` schema where possible. If you already have eval files from skill-creator, you can reference them as baselines.

### Phase 3: Tiered Execution

Choose a testing tier based on the situation. The tiers trade fidelity for cost:

| Tier | Method | Token Cost | When to Use |
|:-----|:-------|:-----------|:------------|
| **V1** | Full agent run (end-to-end) | ~6-8K/run | First-time validation, verifying true agent behavior |
| **V2** | Pre-fetch input + direct model judgment | ~2-3K/run | Known model-understanding bottleneck, need precision |
| **V3** | Local rules first + model for gray zone | ~0-2K/run | Batch regression, large sample sizes |
| **V4** | Pure local rules | ~0/run | CI/smoke tests, structural checks |

**Selection logic:**
```
if first_time_diagnosing:
    if need_to_verify_agent_e2e_behavior: V1
    else: V2
elif regression_after_fix:
    if sample_count < 10: V2
    else: V3
elif ci_or_smoke_test: V4
```

For detailed tier descriptions, operating procedures, and cost models, read `references/methodology.md`.

**Running V1 tests:**
- Each run must be independent (fresh context, no carryover from previous runs)
- If running in the same conversation, explicitly instruct the model to treat each run as independent
- Record: verdict, evidence location, reasoning, token count

**Running V2 tests:**
- Pre-fetch all documents/inputs before testing begins (batch `lark-cli docs +fetch` or equivalent)
- Feed the pre-fetched content directly to the model with a minimal, focused prompt
- Only ask about the specific dimension/factor under test — don't load the full skill framework

### Phase 4: Root Cause Analysis

After all runs complete, build a results matrix:

```
┌──────────┬──────┬──────┬──────┬───────────┐
│ Case     │ Run1 │ Run2 │ Run3 │ Pass Rate │
├──────────┼──────┼──────┼──────┼───────────┤
│ TC-H1-01 │ ✅   │ ✅   │ ✅   │ 3/3 ✅    │
│ TC-H1-N1 │ ✅   │ ✅   │ ✅   │ 3/3 ✅    │
│ TC-H2-01 │ ❌   │ ❌   │ ✅   │ 1/3 ❌    │
│ TC-H2-N1 │ ✅   │ ✅   │ ✅   │ 3/3 ✅    │
└──────────┴──────┴──────┴──────┴───────────┘
```

**Analysis framework:**
1. **Factor isolation**: Which hypotheses show pass_rate < threshold (default: 2/3)?
2. **Primary vs secondary causes**: Rank by failure severity and frequency
3. **Interaction effects**: Do failures compound when multiple factors co-occur?
4. **Stability assessment**: High variance (e.g., 1/3) suggests the factor is at the model's boundary — intermittent failures are harder to fix than consistent ones

**Output: Root cause report** (use template from `references/test-report-template.md`):
- Confirmed root causes with evidence
- Rejected hypotheses with evidence
- Specific fix recommendations tied to each confirmed cause
- Predicted impact of each fix

### Phase 5: Fix & Regression

After the user applies fixes to the skill:

1. **Re-run the failing cases** using V2 or V3 (no need for V1 — the fix target is already identified)
2. **Also re-run passing cases** to check for regression (did the fix break something else?)
3. **Compare pass_rate delta**: before-fix vs after-fix
4. **Document the result** in the test report

If the fix doesn't fully resolve the issue, loop back to Phase 1 with updated hypotheses.

---

## Output Formats

### Per-case result (compatible with skill-creator's grading.json)
```json
{
  "case_id": "TC-H2-01",
  "hypothesis": "H2: Evidence position migration",
  "runs": [
    {"run": 1, "verdict": "covered", "evidence_location": "§1.2", "correct": true, "tokens": 6800},
    {"run": 2, "verdict": "missing", "evidence_location": null, "correct": false, "tokens": 7200},
    {"run": 3, "verdict": "covered", "evidence_location": "§1.2", "correct": true, "tokens": 6500}
  ],
  "pass_rate": 0.67,
  "conclusion": "Borderline pass — position migration causes intermittent failures"
}
```

### Aggregate summary (compatible with skill-creator's benchmark.json)
```json
{
  "metadata": {
    "skill_name": "check-prd",
    "test_type": "root_cause_analysis",
    "tier": "V2",
    "timestamp": "2026-04-08T10:00:00Z",
    "total_runs": 45,
    "total_tokens": 150000
  },
  "hypotheses": [
    {
      "id": "H1",
      "description": "Numbering format causes misidentification",
      "status": "rejected",
      "evidence": "0/9 failures across 3 cases × 3 runs"
    },
    {
      "id": "H2",
      "description": "Evidence position migration",
      "status": "confirmed_secondary",
      "evidence": "2/9 failures, intermittent pattern",
      "fix_recommendation": "Add position-agnostic scanning instruction"
    }
  ]
}
```

---

## Collaboration with skill-creator

skill-tester is independent but designed to play well with skill-creator's ecosystem:

| skill-creator asset | How skill-tester uses it |
|:-------------------|:------------------------|
| `evals/evals.json` | Import as baseline test cases |
| `grading.json` schema | Output results in compatible format |
| `timing.json` schema | Token tracking uses same format |
| `benchmark.json` schema | Aggregate results are compatible |
| `eval-viewer` | Results can be visualized in the same viewer |

What skill-tester does **not** use:
- `comparator.md` — we use controlled-variable analysis instead of blind A/B
- `run_loop.py` — description optimization is out of scope

---

## Reference Files

Read these when you need deeper guidance:

- `references/methodology.md` — V1-V4 tier details, cost models, operational procedures, real-world benchmarks
- `references/hypothesis-catalog.md` — Reusable hypothesis templates with example experiments
- `references/test-report-template.md` — Standard report format for documenting findings
