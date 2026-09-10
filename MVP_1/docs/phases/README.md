# MVP_1 Phase Understanding Guide

## Toolkit Release 0.2 extension

- Step 1 freezes and characterizes the Clause 04 baseline.
- Step 2 adds clause-neutral v2 contracts and controlled vocabulary without
  changing the Clause 04 v1 contracts.
- Steps 3–7 remain outside the Step 2 change set.

This directory explains the development of the governed ISO/IEC 42001 Clause
04 assessment MVP one phase at a time and introduces the bounded Clause 05
extension planned for Toolkit Release 0.2.

The documents are written as reader guides. Historical implementation records
remain in `docs/baseline/` and `docs/implementation/`, while architectural
decisions remain in `docs/architecture/`.

## Phase map

| Phase | Main question | Principal result |
|---|---|---|
| [Phase 0](phase_0_overview.md) | What must remain unchanged? | Frozen deterministic Clause 04 baseline |
| [Phase 1](phase_1_contracts.md) | What structured information may components exchange? | Schema-bound assessment contracts |
| [Phase 2](phase_2_governance.md) | What is each component permitted to do? | Deterministic, fail-closed governance layer |
| [Phase 3](phase_3_workflow.md) | Can the governed components complete an assessment? | End-to-end sequential workflow |
| [Phase 3.1](phase_3_1_reproducibility.md) | Can someone else install and validate it? | Reproducible package and CI |
| [Phase 3.2](phase_3_2_portfolio_scenarios.md) | Does it behave correctly outside the successful case? | Complete, incomplete, and reviewed scenarios |
| [Phase 4](phase_4_evidence_integrity.md) | Can evidence identity and integrity be established without claiming content sufficiency? | Fail-closed provenance lifecycle and human acceptance boundary |

Toolkit Release 0.2 starts from the
[Clause 05 baseline inventory](../baseline/toolkit_release_0_2_clause05_inventory.md)
and the compatibility decision in
[ADR-0003](../architecture/ADR-0003-clause-neutral-governed-assessment.md).

## How the phases build on each other

```mermaid
flowchart TD
    P0["Phase 0: Freeze baseline"] --> P1["Phase 1: Define contracts"]
    P1 --> P2["Phase 2: Enforce permissions"]
    P2 --> P3["Phase 3: Integrate workflow"]
    P3 --> P31["Phase 3.1: Make reproducible"]
    P31 --> P32["Phase 3.2: Prove scenarios"]
    P32 --> P4["Phase 4: Verify integrity"]
```

The phases are cumulative. A later phase adds evidence about the system without
removing the controls established by an earlier phase.

## Overall boundary

The MVP:

- covers ISO/IEC 42001 Clause 04 only;
- supports audit readiness and professional portfolio demonstration;
- keeps the original deterministic readiness score authoritative;
- requires explicit external input for human dispositions;
- uses no LLM or external model in the governed acceptance path;
- does not provide certification or accredited conformity assessment.

## Recommended reading order

Read the phase guides in sequence. For a short portfolio walkthrough, focus on
Phase 0, Phase 2, Phase 3, Phase 3.2, and Phase 4: these explain the trusted
baseline, governance controls, workflow, scenarios, and evidence boundary.
