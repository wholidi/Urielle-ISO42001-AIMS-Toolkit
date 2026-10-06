# Toolkit Release 0.2 — Phase 4 Clause 05 deterministic layer

Baseline: `111cf69c74107c08933f9feaa9b1dc856fee3e8e`

The implementation introduces 21 atomic Clause 05 questions:
- 6 under 5.1;
- 8 under 5.2;
- 7 under 5.3.

Evidence relationships are explicit and use the actual Section 5 artifact identities. The known
baseline mismatch around S5-02 through S5-05 is not silently reinterpreted. Evidence acceptance
remains question-specific and human-authoritative.

The adapter emits frozen P02 v2 evidence-mapping records, reuses P03 linked-record validation and
question evaluation, and then enforces the Clause-05-specific `ALL_OF`, `ANY_OF` and `CONDITIONAL`
combination rules declared by the approved evidence map. In particular, one accepted item cannot
satisfy an `ALL_OF` question such as formal policy approval. Conditional applicability is not
inferred in P04: conditional mappings are emitted as `PROPOSED` by default and require an
explicit caller decision to place them in scope. Without an in-scope mapping and explicit human
review, the result remains `UNRESOLVED`.

Actual AIMS performance reporting occurrence is distinct from a reporting schedule. Question
`Q-C05-5.3-006` therefore requires both the S5-14 route/cadence record and explicitly mapped
S5-05 occurrence evidence to receive question-specific human acceptance. A schedule alone remains
`UNRESOLVED`.

Clause-level aggregation is deterministic and input-order independent. `SUPPORTED` requires every
mandatory atomic question to be supported; any mandatory `UNSUPPORTED` question makes the clause
requirement unsupported; otherwise the aggregate remains unresolved. No numeric readiness score is
introduced. Aggregation validates the caller's expected questions against the complete configured
mandatory set for the requirement, and an existing `UNSUPPORTED` assessment takes precedence over
a different missing assessment.

Focused tests cover question-bank integrity, evidence-map relationships, broken references,
combination-rule validation, deterministic aggregation, stable identity, P03 kernel integration,
missing / unable-to-establish evidence, rejected evidence, non-human acceptance rejection,
unconfigured evidence rejection, and phase-boundary leakage.

The resource-decision mapping remains a documented limitation. S5-05 contains management-review
material about resource adequacy and may be considered only as corroborating evidence after human
content review; it is not silently reclassified as the missing dedicated resource-approval record.
Consequently, Clause 5.1 resource support remains `UNRESOLVED` until authoritative resource-decision
evidence is added through a separately reviewed future change.

Runtime mappings must match the configured assessment, question, requirement, canonical mapping,
and `EVD-S5` source tuple before an acceptance can contribute. The source catalog is fixed to the
approved S5-01 through S5-14 inventory; missing, additional, invented, or substituted identities
fail configuration validation.

Excluded: governed Clause 05 workflow, runtime supervisor, permissions, scenarios, release
packaging, version increment and certification statements.
