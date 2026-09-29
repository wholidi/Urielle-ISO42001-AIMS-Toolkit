# ADR-0005: Clause 05 deterministic assessment layer

- Status: Proposed implementation checkpoint for Toolkit Release 0.2 Step 4
- Baseline: `111cf69c74107c08933f9feaa9b1dc856fee3e8e`
- Scope: Clause 05 deterministic configuration, adapter, validation and aggregation only

## Decision

Clause 05 knowledge is represented as a version-controlled atomic question bank and explicit
source-artifact evidence map. The Clause 05 adapter translates that configuration into the frozen
clause-neutral v2 evidence-mapping contract and delegates linked-record validation and baseline
question evaluation to the P03 shared governed kernel.

P04 then applies only the Clause-05-specific evidence-combination semantics declared in the map:

- `ALL_OF`: every configured in-scope mapping requires explicit human acceptance; any explicit
  rejection is `UNSUPPORTED`; missing or unreviewed required evidence is `UNRESOLVED`.
- `ANY_OF`: one configured human-accepted mapping can support the question; the question is
  `UNSUPPORTED` only when all configured in-scope alternatives are explicitly rejected; otherwise
  it remains `UNRESOLVED`.
- `CONDITIONAL`: the question remains `UNRESOLVED` unless the conditional mapping is placed
  in scope and receives question-specific human acceptance/rejection. P04 does not infer
  applicability on behalf of a human reviewer.

Clause-level aggregation is fail-closed:
- all mandatory atomic questions SUPPORTED -> SUPPORTED;
- any mandatory atomic question UNSUPPORTED -> UNSUPPORTED;
- otherwise -> UNRESOLVED.

No numeric readiness score is introduced. No file presence, integrity result, policy existence,
role title, RACI entry, schedule, confidence value or model output can create authoritative support.
Human question-specific acceptance remains a prerequisite through the P03 kernel.

## Phase boundary

Step 4 adds no supervisor, runtime workflow, governance registration, permission expansion,
portfolio scenario, release tag, model-use authority, autonomous decision authority or certification
conclusion. Those remain outside P04.
