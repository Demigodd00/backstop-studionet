# BACKSTOP live demo script

This script is a plan, **not** a claim that any transaction has finalized. Replace each planned step with a finalized-success explorer link and a state read-back before using it for review.

1. Open the no-wallet registry and inspect the frozen base policy, two legitimate tasks, tool allowlist, amount cap, and terms digest.
2. Show a held harmless attack. The record must remain outside `regression_ids` and the suite revision must not change.
3. Show a prompt-injection attack that makes the bounded agent propose `PUBLISH` while only `DRAFT` is allowed. The finalized result must be `BROKEN`; the revision increments and the attack appears in `regression_ids`.
4. Submit a refusal-only candidate. Its exploit check should pass, but at least one legitimate drafting task must fail. A certification attempt is an expected failure.
5. Submit a targeted candidate. Run each exploit and both legitimate tasks as separate transactions. After every result is finalized, certify the candidate and read `get_active_policy`: `usable: true` at the same revision.
6. Submit a different attack against the certified prompt. If validators reproduce it, show the revision increment and `get_active_policy`: `usable: false`. A candidate captured at the previous revision cannot certify.
7. Show that a malformed model reply or expired case cannot add a regression or create a positive patch check.

Record each hash, lifecycle status, leader execution status, validator votes, prompt/source commit, and state read-back in `deploy/proof.json`. Stop and investigate any unexpected live judgment before repeating it. The demonstrated tasks are simulated JSON actions, not real external tool calls.
