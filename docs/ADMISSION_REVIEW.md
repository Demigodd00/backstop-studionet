# BACKSTOP v0.2 admission-capacity revision

The steward found two permanent denial-of-service paths in v0.1: every submitted
attack counted toward a lifetime twelve-attempt cap, and every proposed repair
counted toward a lifetime eight-candidate cap. Rejected, failed, stale, and
expired records still consumed those slots. This revision separates short-lived
admission capacity from permanent audit history.

## Rules now enforced by the contract

- Attack admission counts only accepted regressions plus pending judgments.
  The total cannot exceed four, so every pending attack can still become a
  regression. A `HELD`, `UNCLEAR`, or expired attempt releases its slot.
  Pending attempts expire after one day. A proven `BROKEN` attack remains a
  permanent regression and cannot be submitted again against the same prompt.
- Candidate admission counts only live `TESTING` candidates at the current
  suite revision. At most eight can be live, with no more than seven submitted
  by non-builders. This leaves one usable slot for the builder even if outside
  participants saturate their allowance. A failed exploit or legitimate-task
  check immediately marks the candidate `FAILED` and releases its slot. A new
  reproduced break marks previous-revision testing candidates `STALE` and
  releases them. Candidates expire after three days; the next proposal can
  reap expired slots without waiting for their authors.
- `attack_total` and `candidate_total` never decrease. Every record remains
  retrievable by ID. `list_attack_history` and `list_candidate_history` page
  through the full per-suite audit trail in batches of at most twenty. The
  suite's `attack_ids` and `candidate_ids` fields contain only the newest
  twelve and eight IDs, respectively, so a suite read remains bounded.

The four-accepted-regression ceiling is deliberate: a candidate must replay
every accepted break. After that ceiling is reached, the suite is complete and
new attacks require a new suite. Draft suite creation still has a lifetime
contract cap of 100; draft lifecycle management remains a separate follow-up.

## Focused local proof

`pytest -q tests/direct/test_backstop.py` exercises four adversarial pending
attacks, rejection of a fifth while they are live, resolution and expiry,
resubmission after a non-break, fourteen historical attacks despite the old
twelve-record limit, and a later accepted break. It also tests seven outside
candidates, the builder's eighth slot, failed-check recovery, revision-stale
recovery, expiry, complete history beyond eight candidates, and successful
certification after those events. Direct Mode uses mocked model outputs; live
validator agreement is recorded separately in the deployment demo.

## Deployment and live evidence

The v0.2 contract is [deployed on Studionet](https://explorer-studio.genlayer.com/address/0x6a5BAF4BE11aC207692a71993D6a40FB08c37400).
The [deployment manifest](../deploy/proof-v0.2.json) records the pushed source
commit, exact blob, runner, finalized successful deployment receipt, validator
votes, and deployed-source byte check. The previous v0.1 deployment and proof
remain in [`deploy/proof.json`](../deploy/proof.json) for historical review.

The [v0.2 demo journal](../deploy/demo-v0.2.json) is the live progression through
a reproduced break, seven outside repair proposals, a builder's reserved eighth
active slot, history beyond the old eight-record cap, further checks, and
certification. All 30 writes finalized with successful execution. Key receipts:

| Check | Explorer transaction | Finalized readback |
| --- | --- | --- |
| Seven outside slots filled | [seventh outsider proposal](https://explorer-studio.genlayer.com/tx/0xc3853af6cb62e62ceac830e3f70be309c211233d1359f9aea0dbdcddf39d994b) | Seven live outsider candidates. |
| Builder's reserved eighth slot | [builder proposal](https://explorer-studio.genlayer.com/tx/0xd389010fdcc75e6d8ecc059718597e8e5aa851330ae505cc4d147434e8a827b1) | Eight live candidates; nine historical candidates, all paginated. |
| Failed check releases slot | [first legitimate-task failure](https://explorer-studio.genlayer.com/tx/0x0c682bba0e4912ff21ed5ef777a84fa24c9a9c477b8ff40e8205e3712497b78b), [next builder proposal](https://explorer-studio.genlayer.com/tx/0x67448a044783138ac3fcbc9cce280cca303532a0e1b04e16bd7cf61bf9d30cfc) | `cand-9` becomes `FAILED`; `cand-10` enters testing as the tenth historical candidate. |
| Subsequent certification | [certify `cand-10`](https://explorer-studio.genlayer.com/tx/0x9763da94f9091b71c40c969dfe46c5232984db9310854f3ca2e1c7c891160177) | Revision 2 has a usable certified policy. |

The live sequence demonstrates outsider saturation, builder admission, failure
recovery, preserved history, and later certification. The attack-expiry,
candidate-expiry, and revision-stale recovery branches are covered by Direct
Mode tests, not separate live transactions. Run `python scripts/verify_backstop_v02.py`
to independently compare the pushed and deployed source, recorded receipts,
full candidate history, and current finalized policy state without a private
key.
