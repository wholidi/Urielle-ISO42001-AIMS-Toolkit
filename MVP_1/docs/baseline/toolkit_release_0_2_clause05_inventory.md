# Toolkit Release 0.2 — Clause 05 Baseline Inventory

## Purpose

This inventory establishes the source baseline for extending the governed
assessment pattern to ISO/IEC 42001 Clause 05 Leadership. It records what is
present at the start of Toolkit Release 0.2 and prevents filenames, references,
or templates from being treated as evidence of content sufficiency.

Baseline repository commit: `6a22ed8db5d512cdea503fb2c3326e2dba980eae`.

The source locations below remain read-only during an assessment run:

- `05_Leadership/`
- `Evidence_Repository/Section_5/`

## Clause workbook

| Path | Current purpose | Executable status |
|---|---|---|
| `05_Leadership/5_Leadership_Clause_Register.xlsx` | Human-oriented questions and evidence requests for 5.1, 5.2, and 5.3 | Source material only; not an executable question bank or assessment contract |

## Section 5 artifact inventory

| ID | File | Primary relationship to Clause 05 | Baseline limitation |
|---|---|---|---|
| S5-01 | `S5-01_AI_Policy_Template.docx` | Primary candidate for 5.2 policy content | A policy cannot establish leadership commitment, approval, communication, or implementation by itself |
| S5-02 | `S5-02_AI_Risk_Register_Template.xlsx` | Indirect implementation context; principally related to planning and risk | Not an AIMS objectives register |
| S5-03 | `S5-03_Impact_Assessment_DPIA_Template.docx` | Indirect implementation context | Not a dedicated management-review record |
| S5-04 | `S5-04_Third_Party_Model_Risk_Assessment_Template.docx` | Indirect third-party governance context | Not an AIMS resource-approval record |
| S5-05 | `S5-05_Internal_Audit_Review_Record_Template.docx` | Contains review material that may corroborate 5.1 | Not a dedicated leadership-communication record; mixes internal-audit and management-review material |
| S5-06 | `S5-06_AI_Policy_Approval_Record_Template.docx` | Primary candidate for 5.2 approval | Approval must be explicitly content-reviewed and accepted; blank signature fields do not prove approval |
| S5-07 | `S5-07_AI_Policy_Communication_Record_Template.docx` | Primary candidate for 5.2 communication | Log entries and referenced receipts must be reviewed separately |
| S5-08 | `S5-08_AI_Policy_Training_Acknowledgement_Record_Template.xlsx` | Primary candidate for policy acknowledgement | A stated completion status or formula does not prove individual understanding |
| S5-09 | `S5-09_External_AI_Policy_Publication_Record_Template.docx` | Conditional candidate for external availability | Applicability and the referenced publication must be established explicitly |
| S5-10 | `S5-10_AIMS_RACI_Matrix_Template.xlsx` | Primary candidate for 5.3 responsibility assignment | RACI codes do not prove authority, appointment, acceptance, or understanding |
| S5-11 | `S5-11_AIMS_Role_and_Accountability_Register_Template.xlsx` | Primary candidate for named roles and reporting lines | Role titles and named entries require corroboration |
| S5-12 | `S5-12_AIMS_Appointment_Letter_Template.docx` | Primary candidate for formal appointment and acceptance | Unsigned template fields do not prove appointment or acceptance |
| S5-13 | `S5-13_AIMS_Organisation_Chart_Template.pptx` | Supporting candidate for reporting relationships | A chart alone cannot prove assigned responsibilities or authorities |
| S5-14 | `S5-14_AIMS_Reporting_and_Delegation_Record_Template.docx` | Primary candidate for reporting and delegation arrangements | A schedule does not prove that reporting occurred; blank attestations remain unexecuted |

## Confirmed traceability mismatch

The Clause 05 register currently refers to S5-02 through S5-05 as an AIMS
objectives register, management-review minutes, resource-approval record, and
leadership-communication record. Those identifiers do not match the actual
files listed above.

Toolkit Release 0.2 must use an explicit evidence map based on the actual
artifact identity. Existing source templates must not be renamed or silently
reinterpreted as part of assessment execution.

## Missing or unestablished supporting evidence

Several templates refer to external supporting records, such as email receipts,
acknowledgement files, publication screenshots, URLs, minutes, and signed
attestations. A reference to such a record is not proof that it is present,
authentic, applicable, or sufficient. Each submitted item must pass the
governed evidence lifecycle independently.

## Baseline assessment

The repository has substantial Clause 05 template coverage but no executable
Clause 05 question set, assessment result, evidence map, scenario suite,
governed report, or tests. The templates are suitable source examples for a
professional portfolio review of an existing AI-enabled SaaS system. They are
not automatically accepted evidence and do not constitute a certification
conclusion.
