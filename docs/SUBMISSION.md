# BACKSTOP v0.2 Portal revision handoff

The owner reviews and resubmits this contribution. The v0.2 source and new
Studionet demonstration address the two admission-capacity findings in the
steward request. The previous v0.1 deployment is historical evidence only.

**Contribution type:** Builder → Projects.

**Project name:** BACKSTOP

**Primary tag:** AI & Agents. Suggested focus tags: Model Evaluation and AI
Policy Enforcement.

**One-liner:** A GenLayer-native agent-policy regression registry that certifies
repairs only after they survive reproduced exploits and legitimate tasks.

**Description (under 1,000 characters):**

> BACKSTOP turns reproduced prompt-injection failures into an on-chain regression suite for agent policies. Builders freeze an agent prompt, allowed JSON actions, and two legitimate tasks. GenLayer validators independently simulate each attack and check its proposed action; a reproduced forbidden action increments the suite revision. Candidate repairs must hold every accepted exploit and complete both legitimate tasks before certification. Version 0.2 makes admission slots recoverable: rejected or expired attacks and failed, stale, or expired candidates release active capacity, while paginated on-chain history preserves every attempt. Seven outside repair proposals cannot exclude the builder. A 30-transaction Studionet demo shows saturation, a builder repair, failure recovery, and subsequent certification. This is a finite synthetic test, not a claim of general agent safety.

**Website:** [Public v0.2 registry, completed suite `bs-1`](https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry)

**GitHub:** [Dedicated BACKSTOP repository](https://github.com/Demigodd00/backstop-studionet)

**Contract:** [v0.2 Studionet explorer](https://explorer-studio.genlayer.com/address/0x6a5BAF4BE11aC207692a71993D6a40FB08c37400)

**Exact deployed source:** [Contract at deployment commit `7c0efc4`](https://github.com/Demigodd00/backstop-studionet/blob/7c0efc4db40a9af086a438f7f3b65464cf3b9a79/contracts/backstop.py)

**Proof and reviewer links:** [Deployment manifest](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/proof-v0.2.json), [30-transaction demo journal](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/demo-v0.2.json), [admission review and tests](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/ADMISSION_REVIEW.md), [code walkthrough](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/TUTORIAL.md), and [read-only proof verifier](https://github.com/Demigodd00/backstop-studionet/blob/main/scripts/verify_backstop_v02.py).

**Key transactions:** [seven outside slots filled](https://explorer-studio.genlayer.com/tx/0xc3853af6cb62e62ceac830e3f70be309c211233d1359f9aea0dbdcddf39d994b), [builder's eighth slot](https://explorer-studio.genlayer.com/tx/0xd389010fdcc75e6d8ecc059718597e8e5aa851330ae505cc4d147434e8a827b1), [failed legitimate task](https://explorer-studio.genlayer.com/tx/0x0c682bba0e4912ff21ed5ef777a84fa24c9a9c477b8ff40e8205e3712497b78b), [next builder repair](https://explorer-studio.genlayer.com/tx/0x67448a044783138ac3fcbc9cce280cca303532a0e1b04e16bd7cf61bf9d30cfc), and [final certification](https://explorer-studio.genlayer.com/tx/0x9763da94f9091b71c40c969dfe46c5232984db9310854f3ca2e1c7c891160177).

**Reviewer steps:** Open the public registry without a wallet and select
`Synthetic release-note agent` (`bs-1`). Confirm two `BROKEN` attacks and
revision 2. Inspect `cand-2` through `cand-8` as seven outside proposals, then
`cand-9` as the builder's eighth active proposal despite that saturation.
`cand-9` fails a legitimate task; `cand-10` enters the released slot, holds
both attacks, passes both legitimate tasks, and becomes the active certified
policy. The suite retains all ten candidates through
`list_candidate_history`; the UI can load older entries. Compare the source
commit and receipts through the proof links. Run
`python scripts/verify_backstop_v02.py` to recheck the chain without a private
key. The Direct Mode tests cover expiry and stale-revision recovery separately.

**Expected on-chain outcome:** `get_active_policy("bs-1")` reports
`usable: true`, `candidate_id: "cand-10"`, and `revision: 2`.
`get_suite("bs-1")` reports `candidate_total: 10` while its recent
`candidate_ids` list remains bounded at eight.

**Steward response to paste:**

> Thank you for identifying the two permanent slot-exhaustion paths. BACKSTOP v0.2 now admits attacks using only live pending slots plus accepted regressions, and admits candidates using only current-revision testing slots. Non-break and expired attacks release capacity; failed, stale, and expired candidates do likewise. Seven outsider proposals cannot occupy the builder's reserved eighth slot. Every attempt remains available by ID and through paginated history. Focused Direct Mode tests cover exhaustion, expiry, recovery, and later certification. The new source-identical Studionet deployment and 30 finalized successful transactions demonstrate seven outsider slots, builder admission as historical candidate nine, a failed builder check, admission of candidate ten, and final certification. The repository, deployment manifest, reviewer trail, and public registry are linked above.

**Project logo:** Upload [`apps/backstop-web/public/portal-logo.png`](../apps/backstop-web/public/portal-logo.png), a 512 × 512 PNG.

No Portal resubmission is performed by this repository. The owner submits after
reviewing the live site and form.
