# Toolkit Release 0.2 — Phase 5A/5B baseline and staged governance

## Verified source baseline
- Git main commit: `a561e7d9f73cecb0ccd7d0823dfc481bc5a7ea37`
- Python package version: `0.4.0` (no change).
- Existing Clause 04 compatibility characterization: `tests/test_clause04_release02_characterization.py`.
- Frozen Clause 04 normalized-result digest: `76c36e453f29b650f8cce0e41d99d71a09c87ab47592bf2244e089d79cc6984d`.
- Clause 04 sequential workflow has seven fixed stages; leave unchanged.
- Existing Clause 05 config: 21 mandatory questions, 46 evidence mappings, S5-01 to S5-15.
- Prior PR #22 records 402 passing local tests; this document does not assert tests have been rerun.

## Phase 5A safeguards
- `tests/test_clause04_release02_characterization.py` remains authoritative.
- No changes to `clause_04_context`, `supervisor.py`, existing Clause 04 runtime, v2 schemas or shared kernel.
- Run baseline tests before making changes, and full tests after applying the staging patch.

## Phase 5B governance decision
- Add `agentic.clause05_workflow` to `agent_registry.yaml` as **disabled**.
- Its type uses existing `SEQUENTIAL_SUPERVISOR` schema enum, avoiding frozen schema changes.
- Its implementation path is reserved for later P05-C; this module is NOT created here.
- Its single declared action is NOT permission to execute: component is disabled and no matching permission-matrix entry exists.
- The permission matrix, human approval rules and model-use record are unchanged.
- No runtime or human-acceptance permission is granted. The actor cannot run.
- P05-C must separately approve adding the module, enabling actor and granting least-privilege permissions.

## Preflight and acceptance
1. Verify branch `main`, clean Git working tree, `HEAD` equals baseline.
2. Run `python -m pytest tests -q -p no:cacheprovider` before patch; record results.
3. Apply this patch locally only after review.
4. Run `python -m pytest tests/test_clause04_release02_characterization.py tests/test_p05_ab_governance.py -q -p no:cacheprovider`.
5. Run `python -m pytest tests -q -p no:cacheprovider` and check `git diff --check`.
6. Python 3.11 / 3.12 / 3.13 CI remains a later approval gate; this package does not modify CI.

This checkpoint does not close audit findings, execute a Clause 05 assessment, or authorize commits, pushes, merges, tags or releases.
