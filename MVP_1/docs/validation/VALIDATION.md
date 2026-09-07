# Urielle–Evgraph Clause 4 Independent Validation

## Status

**Technically reproduced, validated, and complete**

Validation was performed independently against:

- Repository: `SVamseekar/evgraph`
- Branch: `experiment/urielle-clause04`
- Commit: `28b339d247207aafa2e0a606846dcc608ba84e71`
- Validation date: `2026-09-07`

## Purpose

The experiment evaluated whether Urielle Clause 4 evidence records could be
consumed by Evgraph while preserving a clear separation between:

1. structural evidence verification;
2. evidence relevance/sufficiency assessment; and
3. ISO/IEC 42001 assurance judgement.

## Reproduction results

| Check | Expected | Observed | Result |
|---|---:|---:|---|
| Harborline readiness score | 76.25 | 76.25 | Reproduced |
| Public AWS/Microsoft documentation readiness score | 85.0 | 85.0 | Reproduced |
| Full automated test suite | Pass | 92 passed | Pass |

## Harborline scenario

Urielle produced a readiness score of **76.25**.

For C4-Q04:

- Urielle: `REQUIRES_HUMAN_JUDGEMENT`
- Urielle evidence IDs: none
- Evgraph: `EXPECTATION_NOT_MET`
- Evgraph finding level: `STRUCTURAL`
- Evgraph statement: no structured evidence references were found.

This confirms that both systems independently surfaced the same underlying
structural evidence-reference gap while retaining separate decision logic.

### Q02 demonstrates the boundary

For C4-Q02:

- Evgraph reported that a structured evidence reference was present.
- Urielle still returned `REQUIRES_HUMAN_JUDGEMENT`.

This demonstrates that **evidence-reference presence is not the same as
evidence sufficiency**.

## Public-document scenario

Urielle produced a readiness score of **85.0**.

Observed Evgraph structural findings:

- C4-Q01: `EXPECTATION_MET`
- C4-Q02: `EXPECTATION_NOT_MET`
- C4-Q03: `EXPECTATION_MET`
- C4-Q04: `EXPECTATION_NOT_MET`

Observed Urielle decisions:

- C4-Q01: `EVIDENCED`
- C4-Q02: `NOT_EVIDENCED`
- C4-Q03: `EVIDENCED`
- C4-Q04: `REQUIRES_HUMAN_JUDGEMENT`

The scenario again confirms that Evgraph reports structural evidence state,
while Urielle independently determines evidence disposition and assurance
treatment.

## Architectural finding

The validated boundary is:

### Evgraph

Structural evidence verification.

Examples:
- structured evidence reference present;
- structured evidence reference absent;
- deterministic, traceable structural findings.

### Urielle

Evidence relevance and sufficiency assessment.

Responsibilities include:
- evidence sufficiency;
- readiness scoring;
- human-review requirements;
- ISO/IEC 42001 assurance interpretation.

### Human / Assurance Authority

Retains final assurance judgement where human review is required.

## Test result

The full Evgraph repository test suite completed successfully:

```text
92 passed in 0.57s
```

All four Evgraph packages were installed into the clean validation environment:

- `evgraph-core` 0.1.2
- `evgraph-rules` 0.1.2
- `evgraph` 0.1.2
- `evgraph-cli` 0.1.2

Urielle MVP_1 was installed separately as an editable dependency.

## Provenance

The clean validation clone was confirmed at:

```text
Branch: experiment/urielle-clause04
Commit: 28b339d247207aafa2e0a606846dcc608ba84e71
Working tree: clean
```

The upstream Evgraph source is intentionally excluded from this validation
record. The exact source snapshot can be retrieved from the upstream repository
using the branch and commit recorded above.

## Boundary / non-goals

This validation covers only the completed Clause 4 experiment.

It does not establish or imply:

- Clause 8 integration;
- Annex A integration;
- evidence-quality scoring by Evgraph;
- provenance verification;
- bias or fairness evaluation;
- EU AI Act regulatory-control-plane integration;
- a shared commercial product;
- partnership or joint ownership;
- certification of ISO/IEC 42001 compliance.

Any future work in those areas would constitute a separate phase.

## Conclusion

The Urielle–Evgraph Clause 4 interoperability experiment was independently
reproduced and technically validated.

The experiment confirms that Evgraph can provide a structural evidence layer
without replacing Urielle's evidence-sufficiency assessment, readiness scoring,
human-review process, or assurance authority.

**Clause 4 validation phase: COMPLETE.**
