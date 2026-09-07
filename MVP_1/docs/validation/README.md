# Evgraph Clause 4 Interoperability Validation

This folder contains Urielle's independent validation record for the public
Urielle–Evgraph Clause 4 interoperability experiment.

## External project

- Evgraph repository: https://github.com/SVamseekar/evgraph
- Branch: `experiment/urielle-clause04`
- Validated commit: `28b339d247207aafa2e0a606846dcc608ba84e71`

The Evgraph source repository itself is intentionally **not included** in this
validation record. It remains available from the upstream public repository.

## Validation summary

- Harborline scenario readiness score: **76.25**
- Public AWS/Microsoft documentation scenario readiness score: **85.0**
- Automated tests: **92 passed**
- Structural evidence boundary: **confirmed**
- Validation status: **Complete**

See [VALIDATION.md](VALIDATION.md) for the detailed findings.

## Collaboration boundary

The experiment confirmed the following separation:

**Evgraph**
- Performs structural evidence-reference verification.
- Produces evidence-state findings such as whether a structured reference exists.
- Does not issue the Urielle readiness score or ISO/IEC 42001 assurance conclusion.

**Urielle**
- Evaluates evidence relevance and sufficiency.
- Produces readiness scoring.
- Retains human-review logic and ISO/IEC 42001 assurance interpretation.

**Human / Assurance Authority**
- Retains final assurance judgement where human review is required.

## Scope

This record covers only the completed Clause 4 experiment. It does not imply
an ongoing integration, commercial partnership, certification claim, or
automatic extension into Clause 8, Annex A, provenance, bias/fairness,
regulatory-control-plane integration, or other future phases.
