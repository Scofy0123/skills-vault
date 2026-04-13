# Hypothesis Catalog

Reusable hypothesis templates for diagnosing skill quality issues. Each template describes a common failure pattern, the controlled variable to test, and sample design guidance.

These templates were distilled from the check-prd H1-H8 root cause analysis experiments (45 runs, 14 test cases, 4 hypotheses validated in first round).

---

## How to Use This Catalog

1. When a user reports a skill quality problem, scan this catalog for matching patterns
2. Select 2-4 hypotheses that best explain the symptom
3. Adapt the templates to the specific skill under test
4. Design test cases following the sample design guidance

Not every hypothesis will be relevant — pick the ones that match the failure pattern. If none match, create a new hypothesis and consider adding it to this catalog after the investigation.

---

## Category 1: Structural Hypotheses

### H-STRUCT-01: Evidence Position Migration

**Pattern**: The model fails to identify information when it appears in a non-standard location within the document.

**Controlled variable**: Position of the target information (beginning / middle / end / nested subsection)

**Sample design**:
- Positive baseline: Target info in the standard/expected position
- Experiment group: Same info moved to an unexpected position (e.g., appendix, footnote, middle of an unrelated section)
- Negative sample: Document with no target info at all (gate test)

**Origin**: check-prd H2 — tested whether moving "业务背景" from §1 to §3 caused misidentification. Result: **not confirmed** (model was position-agnostic).

---

### H-STRUCT-02: Carrier Type Substitution

**Pattern**: The model fails when information is presented in a different format (table vs paragraph vs bullet list vs diagram description).

**Controlled variable**: Content carrier format

**Sample design**:
- Positive baseline: Info as a standard paragraph
- Experiment variants: Same info as a table, as a numbered list, as nested bullets, as a key-value pair
- Negative sample: Document with no relevant info in any format

**Origin**: check-prd H3 — tested paragraph vs table vs list carriers. Result: **not confirmed** (model handled all carriers correctly).

---

### H-STRUCT-03: Nesting Depth

**Pattern**: Deeply nested content (e.g., a bullet point inside a subsection inside a collapsed section) is missed.

**Controlled variable**: Nesting level (1-level / 3-level / 5-level)

**Sample design**:
- Positive baseline: Info at top level
- Experiment group: Same info nested 3+ levels deep
- Negative sample: Equally nested document without the target info

---

## Category 2: Scale Hypotheses

### H-SCALE-01: Long Document Attention Degradation

**Pattern**: The model's accuracy drops when the document is very long, especially for information located far from the beginning.

**Controlled variable**: Document length (tokens) and target info position relative to length

**Sample design**:
- Positive baseline: S-Tier (~1.5K words) document with target info (known to work)
- Experiment group 1 (M-Tier): ~5K words of *highly realistic domain noise* (real API specs, schemas, diagrams, rules) embedding the target info
- Experiment group 2 (L-Tier): ~15K words of extreme realistic stress noise
- Variant: Target info at beginning vs end of the long document
- Negative sample: Long document without target info
- **CRITICAL IMPERATIVE**: Never use "Lorem Ipsum". Models easily bypass random noise. Use domain-specific jargon and structured data relevant to the task to create genuine cognitive load.

---

### H-SCALE-02: Multi-Dimension Cognitive Load

**Pattern**: When the skill requires evaluating many dimensions simultaneously, accuracy drops on individual dimensions due to attention splitting.

**Controlled variable**: Number of dimensions evaluated concurrently

**Sample design**:
- Positive baseline: Evaluate only the target dimension (e.g., just "业务背景")
- Experiment group: Evaluate 7 dimensions simultaneously, then 14 dimensions
- Compare: Accuracy on the target dimension across conditions

**Origin**: check-prd H7 — hypothesized that evaluating 14 dimensions at once dilutes attention per dimension.

---

## Category 3: Encoding Hypotheses

### H-ENCODE-01: Numbering System Decoupling

**Pattern**: The model relies on section numbering (e.g., "1.1", "第一章") for identification, so changing numbering formats causes failures.

**Controlled variable**: Numbering format (1.1 / 一.1 / I.A / unnumbered)

**Sample design**:
- Positive baseline: Standard "1.1 业务背景" format
- Experiment variants: "一、业务背景", "Part I: Background", no numbering at all
- Negative sample: Numbered sections without the target content

**Origin**: check-prd H1 — tested 4 numbering formats. Result: **not confirmed** (model was format-agnostic).

---

## Category 4: Input Channel Hypotheses

### H-INPUT-01: URL vs Direct Content

**Pattern**: The skill behaves differently depending on whether the input is a URL (requiring agent to fetch) vs directly pasted content.

**Controlled variable**: Input delivery method

**Sample design**:
- Positive baseline: Provide content via URL (agent fetches via lark-cli)
- Experiment group: Same content pasted directly into the prompt
- Negative sample: Invalid URL / empty document

**Origin**: check-prd H4 — tested URL vs paste vs file. Result: **not confirmed** (no behavioral difference).

---

### H-INPUT-02: Content Extraction Fidelity

**Pattern**: The document fetching tool (e.g., lark-cli docs +fetch) loses formatting, tables, or nested structures during extraction.

**Controlled variable**: Fetching tool / extraction method

**Sample design**:
- Positive baseline: Hand-verified clean extraction
- Experiment group: Tool-extracted content (compare with baseline to identify information loss)
- Check: Does the skill's failure correlate with extraction artifacts?

---

## Category 5: Semantic Hypotheses

### H-SEMANTIC-01: Informal / Non-Standard Expression

**Pattern**: The model looks for canonical phrases (e.g., "业务背景") and fails when the same concept is expressed colloquially (e.g., "我们为什么要做这个项目").

**Controlled variable**: Expression formality level

**Sample design**:
- Positive baseline: "1.1 业务背景：本项目旨在解决..."
- Experiment group: "先说说为什么我们要搞这个事儿吧..." (same substance, informal phrasing)
- Negative sample: Colloquial text that superficially resembles background discussion but doesn't contain actual business context

**Origin**: check-prd H8 — designed but not yet executed. High-risk hypothesis given the keyword-matching tendencies of prompts.

---

### H-SEMANTIC-02: Distributed Evidence

**Pattern**: The answer to a dimension is not in one place — it requires synthesizing information scattered across multiple sections.

**Controlled variable**: Evidence distribution (concentrated vs scattered)

**Sample design**:
- Positive baseline: All evidence for dimension X in a single section
- Experiment group: Same evidence split across 3-4 different sections
- Negative sample: Fragments that look relevant but don't actually constitute complete evidence

---

## Category 6: Interaction Hypotheses

### H-INTERACT-01: Conversation Context Pollution

**Pattern**: Earlier messages in the conversation influence the model's judgment on later inputs (carryover effects).

**Controlled variable**: Conversation history

**Sample design**:
- Positive baseline: Fresh conversation, single test case
- Experiment group: Same test case after 5+ other test cases in the same conversation
- Compare: Does accuracy degrade with conversation length?

---

### H-INTERACT-02: Prompt Priming

**Pattern**: The way the user phrases the request biases the model toward a particular answer.

**Controlled variable**: User prompt framing

**Sample design**:
- Neutral: "Review this PRD"
- Leading negative: "I think this PRD is missing the business background, please check"
- Leading positive: "This PRD should be complete, please verify"
- Compare: Does framing change the verdict?

---

## Template for New Hypotheses

When creating a new hypothesis during an investigation, use this template:

```markdown
### H-[CATEGORY]-[NN]: [Descriptive Name]

**Pattern**: [What failure behavior is observed]

**Controlled variable**: [The single factor being varied]

**Sample design**:
- Positive baseline: [Known-good case]
- Experiment group: [Variation to test]
- Negative sample: [Known-bad case for gate testing]

**Origin**: [Which skill/experiment this came from]
```
