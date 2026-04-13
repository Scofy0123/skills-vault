# Test Report Template

Use this template to document skill-tester diagnostic findings. Copy and fill in the sections relevant to your investigation.

---

## [Skill Name] Diagnostic Report

**Date**: YYYY-MM-DD  
**Skill under test**: [skill name + version/path]  
**Reported symptom**: [Brief description of the quality problem]  
**Test tier used**: V1 / V2 / V3 / V4  
**Total runs**: [N]  
**Total token consumption**: [estimated]

---

### Hypotheses Tested

| ID | Description | Controlled Variable | Status | Evidence |
|:---|:-----------|:-------------------|:-------|:---------|
| H1 | [description] | [variable] | ✅ Confirmed / ❌ Rejected / ⚠️ Inconclusive | [pass_rate or key finding] |
| H2 | [description] | [variable] | ... | ... |

---

### Test Cases & Results

#### Hypothesis H1: [Description]

| Case ID | Type | Description | Run 1 | Run 2 | Run 3 | Pass Rate |
|:--------|:-----|:-----------|:------|:------|:------|:----------|
| TC-H1-N1 | Negative | [Gate test] | ✅ | ✅ | ✅ | 3/3 |
| TC-H1-01 | Positive | [Baseline] | ✅ | ✅ | ✅ | 3/3 |
| TC-H1-02 | Positive | [Variant] | ❌ | ❌ | ✅ | 1/3 |

**Conclusion for H1**: [Summary of findings — confirmed/rejected, primary/secondary cause, boundary behavior]

*(Repeat for each hypothesis)*

---

### Root Cause Analysis

**Primary cause(s)**:
1. [Root cause with evidence and confidence level]

**Secondary cause(s)**:
1. [Contributing factor, if any]

**Rejected hypotheses**:
1. [What was tested and why it was ruled out]

**Interaction effects**:
- [Do any confirmed factors compound each other?]

---

### Fix Recommendations

| Priority | Recommendation | Expected Impact | Affected Area |
|:---------|:--------------|:---------------|:-------------|
| High | [Specific change to make] | [Predicted improvement] | [File/section to modify] |
| Medium | [Change] | [Impact] | [Area] |

---

### Regression Verification (Post-Fix)

**Fix applied**: [Description of the change made]  
**Re-test tier**: V2 / V3  
**Results**:

| Case ID | Before Fix | After Fix | Delta |
|:--------|:----------|:----------|:------|
| TC-H1-02 | 1/3 (33%) | 3/3 (100%) | +67% ✅ |
| TC-H1-01 | 3/3 (100%) | 3/3 (100%) | 0% (no regression) |

**Conclusion**: [Fix effective? Any side effects?]

---

### Token Consumption Breakdown

| Phase | Tier | Runs | Tokens |
|:------|:-----|:-----|:-------|
| Initial diagnosis | V1 | [N] | [tokens] |
| Factor isolation | V2 | [N] | [tokens] |
| Regression test | V3 | [N] | [tokens] |
| **Total** | | **[N]** | **[tokens]** |

---

### Appendix: Raw Data

*(Link to or embed the full result JSON files)*

- `results/hypothesis-H1.json`
- `results/hypothesis-H2.json`
- `results/aggregate-benchmark.json`
