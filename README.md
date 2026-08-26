# Urielle ISO/IEC 42001 AIMS Toolkit

Open-source ISO/IEC 42001:2023 Artificial Intelligence Management System (AIMS) toolkit built using the Urielle-NCAOS governance architecture as a practical implementation and audit-readiness case study.

---

## Overview

Many ISO 42001 resources explain the standard.

This repository focuses on something different:

**How to translate ISO 42001 requirements into auditable governance artifacts.**

The toolkit combines:

- ISO 42001 implementation templates
- Auditor-oriented workbooks
- Evidence mapping
- Governance documentation examples
- Practical implementation guidance
- A governed, executable Agentic Clause 04 assessment MVP

The objective is to help practitioners understand not only **what documents to create**, but also **how an auditor evaluates them**.

---

## Current Release

### Clause 4 — Context of the Organization

Included templates:

| Template | Purpose |
|-----------|----------|
| 4.1_Context_Register.xlsx | Internal and external issues affecting the AIMS |
| 4.2_Stakeholder_Register.xlsx | Interested parties and their requirements |
| 4.3_Scope_Statement.xlsx | AIMS boundaries and applicability |
| 4.4_AIMS_Process_Map.xlsx | Key AIMS processes and interactions |

Each workbook contains:

- Plain-English interpretation of ISO requirements
- Audit questions
- Evidence requests
- Evidence mapping guidance
- Improvement recommendations

---

## Methodology

The toolkit follows an auditor-oriented approach:

```text
Requirement
    ↓
Audit Question
    ↓
Evidence Request
    ↓
Evidence Mapping
    ↓
Assessment
```

The goal is not simply to create documentation.

The goal is to demonstrate evidence that an auditor can verify.

---

## Urielle Evidence Reference Toolkit (ERT)

This toolkit references the Urielle Evidence Reference Toolkit (ERT), a structured evidence architecture used to organize governance artifacts.

### ERT Structure

| Section | Focus Area |
|----------|----------|
| S1 | System Identity & Accountability |
| S2 | Training & Validation |
| S3 | Runtime Monitoring |
| S4 | Incident & Change Management |
| S5 | Governance & Accountability |
| S6 | Transparency & Explainability |

The ERT provides traceability between:

- ISO 42001 requirements
- Audit questions
- Governance controls
- Evidence artifacts

---

## Repository Structure

```text
04_Context/
05_Leadership/
06_Planning/
07_Support/
08_Operation/
09_Performance_Evaluation/
10_Improvement/

Annex_A/
Annex_B/
Annex_C/
Annex_D/

Reference/

MVP_1/
├── agentic_assessment/
├── clause_04_context/
├── governance/
├── reports/
│   └── evidence/
├── scripts/
└── tests/
```

`04_Context/` through `Reference/` are the manual, template-based AIMS framework described above. `MVP_1/` is a separate, executable agentic assessment pilot — see the next section.

---

## MVP_1 — Governed Agentic Clause 04 MVP

Alongside the template-based AIMS framework above, `MVP_1/` is a separate, executable pilot showing how a governed agentic assessment workflow can be layered on top of the frozen deterministic ISO/IEC 42001 Clause 04 implementation without replacing its scoring authority.

Scope: ISO/IEC 42001 Clause 4 only.

The design principle is:

> **Deterministic control first, agentic assistance second, human accountability always.**

### End-to-End Workflow

```text
SequentialSupervisor
        ↓
Clause04Adapter
        ↓
EvidenceAssessor
        ↓
EvidenceDecision
        ↓
FindingGenerator
        ↓
Human Review
        ↓
ReportGenerator
        ↓
Auditable Clause 04 Report
```

| Phase | Status | Delivers |
|---|---|---|
| Phase 0 | Complete | Frozen deterministic Clause 04 baseline (`clause_04_context/`): rule-based scoring, gap detection, readiness calculation, evidence records, and report generation. |
| Phase 1 | Complete | Schema-validated governed data contracts for assessment plans, evidence decisions, findings, and execution events. |
| Phase 2 | Complete | Deterministic, fail-closed governance enforcement (`governance/`): component registry, default-deny permission matrix, human-approval rules, startup validation, and model-use controls. |
| Phase 3 | **Complete** | Governed runtime orchestration: schema validation, sequential supervisor, Clause 04 adapter, evidence assessment, finding generation, explicit human-review integration, report generation, end-to-end workflow integration, and acceptance evidence generation. |

### Phase 3 Validation

Phase 3 has been validated at both regression and end-to-end levels:

- **232 full regression tests passed**
- **9 end-to-end Agentic Clause 04 tests passed**
- **7/7 declared workflow stages completed**
- **16 execution events recorded in the acceptance run**
- Deterministic Clause 04 readiness score preserved at **100.0%**
- **4 governed evidence decisions** generated
- **0 findings** and **0 pending findings** for the validated evidence set
- Final report status: **FINAL**
- No LLM or external model is used in the governed assessment path

The acceptance run demonstrated:

```text
Assessment: CLAUSE04-DEMO-001
Run: RUN-CLAUSE04-DEMO-001
Workflow State: COMPLETED
Report Status: FINAL
Readiness Score: 100.0%
Evidence Decisions: 4
Findings: 0
Pending Findings: 0
```

### Acceptance Evidence

The demo runner can persist human-readable and machine-readable evidence under:

```text
MVP_1/reports/evidence/agentic_clause04/
├── CLAUSE04-DEMO-001_FINAL.md
├── CLAUSE04-DEMO-001_execution_events.json
└── CLAUSE04-DEMO-001_acceptance_summary.json
```

The Markdown report records the assessment outcome. The execution-event JSON preserves the governed workflow trace. The acceptance summary provides a compact machine-readable closure record.

The readiness score remains owned by the frozen deterministic Clause 04 engine. The agentic layer does not recalculate the score, make certification decisions, invent human approval, or give an LLM enforcement authority.

Architecture decisions and phase-by-phase implementation records are documented under `MVP_1/docs/`:

- `docs/architecture/ADR-0001-sequential-supervisor.md`
- `docs/architecture/ADR-0002-deterministic-governance-layer.md`
- `docs/implementation/`
- `MVP_1/CHANGELOG.md` and `MVP_1/VERSION.md`

---

## Roadmap

### Agentic Assessment MVP

- [x] Governed data contracts
- [x] Deterministic governance enforcement
- [x] Sequential supervisor
- [x] Clause 04 adapter
- [x] Evidence assessor
- [x] Finding generator
- [x] Human-review integration
- [x] Report generator
- [x] End-to-end Clause 04 workflow
- [x] Acceptance evidence generation

Next:
- Extend the governed assessment pattern beyond Clause 04
- Add additional acceptance scenarios for incomplete and review-required evidence
- Continue strengthening human-review and audit-trace boundaries

### Version 0.1
- Clause 4 Context Toolkit

### Version 0.2
- Clause 5 Leadership
- AI Policy
- Roles & Responsibilities

### Version 0.3
- Clause 6 Planning
- AI Risk Register
- AI Impact Assessment
- Statement of Applicability

### Version 0.4
- Clause 7 Support
- Resource Register
- Competency Matrix
- Communication Plan

### Version 0.5
- Clause 8 Operation
- AI Lifecycle Management
- Third-Party Governance

### Version 1.0
- Complete ISO/IEC 42001 Readiness Toolkit
- ERT Mapping Matrix
- Auditor Workbook
- Governance Implementation Guide

---

## Intended Audience

This repository is intended for:

- AI Governance Professionals
- ISO 42001 Implementers
- Internal Auditors
- AI Risk Managers
- Responsible AI Teams
- AI Assurance Practitioners
- Consultants supporting AI governance programs

---

## Case Study

The examples in this repository are based on lessons learned while mapping the **Urielle-NCAOS Governance Architecture** to ISO/IEC 42001 requirements.

The purpose of the case study is educational and focuses on demonstrating:

- Governance traceability
- Evidence mapping
- Audit readiness
- Responsible AI practices

No confidential customer information is included.

---

## Contributing

Suggestions, feedback, and improvements are welcome.

If you identify gaps, ambiguities, or opportunities to improve the toolkit, please open an Issue or Pull Request.

---

## Disclaimer

This repository is provided for educational, implementation, and readiness assessment purposes only.

It is not an official interpretation of ISO/IEC 42001 and does not replace:

- The official ISO standard
- Accredited certification body guidance
- Professional legal or regulatory advice

Users should validate all content against their own organizational requirements and applicable regulations.

---

## About Urielle AI

Urielle AI focuses on:

- Responsible AI
- AI Governance
- AI Assurance
- AI Auditability
- ISO/IEC 42001 Readiness

Our vision is to help organizations build trustworthy, transparent, and auditable AI systems.
