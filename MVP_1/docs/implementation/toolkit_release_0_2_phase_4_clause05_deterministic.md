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
`Q-C05-5.3-006` therefore requires the complete S5-14 route/cadence, S5-11 assigned reporting-role,
and S5-05 submitted engagement occurrence-content combination to receive explicit, question-specific
human acceptance under `ALL_OF`. A schedule, role title, file, matching hash, policy, blank template,
or acceptance attached to another question cannot establish that reporting occurred. S5-05 contributes
only when a human explicitly accepts its submitted engagement content for this reporting claim.

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

The resource-decision mapping remains a documented evidence blocker. Inspection of every approved
S5-01 through S5-14 source found no authoritative leadership resource-allocation approval record.
S5-05, Section 3(d), states that pilot-stage resource adequacy was assessed as sufficient and lists
future production needs, but it does not record a specific leadership allocation or approval decision.
S5-10's “Allocate and approve AIMS resources (S5-04)” activity and S5-12 section 2 responsibility 6
only assign responsibility and retain the known mismatched S5-04 reference; S5-04 is actually a
third-party model risk assessment. None can be reclassified as the missing decision record. S5-05
therefore remains corroborating-only and Q-C05-5.1-004 remains `UNRESOLVED`. Resolution requires a
separately authorized, claim-specific record identifying the approving leader, resources allocated
(people, budget, tools or infrastructure), scope, decision and date, followed by explicit human
acceptance. Adding that real evidence would affect the protected source/inventory boundary and is
outside Phase 04 remediation authority.

Runtime mappings must match the configured assessment, question, requirement, canonical mapping,
and `EVD-S5` source tuple before an acceptance can contribute. The source catalog is fixed to the
approved S5-01 through S5-14 inventory; missing, additional, invented, or substituted identities
fail configuration validation.

Excluded: governed Clause 05 workflow, runtime supervisor, permissions, scenarios, release
packaging, version increment and certification statements.
