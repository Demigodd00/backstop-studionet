# BACKSTOP design

BACKSTOP is a versioned agent-policy regression registry. A reproduced exploit becomes an immutable test that every later policy version must survive. A candidate is certified only when it holds every accepted exploit in the current suite and still completes the frozen legitimate tasks. A new exploit against a certified version invalidates that certification and increments the suite revision.

## Consensus boundary

The contract stores a bounded system prompt, a deterministic JSON-action policy, two legitimate task/rubric pairs, attack messages, candidate prompts, and normalized case outcomes. For an exploit, each validator runs the same bounded defender prompt on its own model and derives `HELD` or `BROKEN` from the JSON action using code. For a legitimate task, each validator runs the defender and then judges the reply against a narrow frozen rubric, returning `PASS` or `FAIL`. Validators compare the exact normalized outcome. No raw model prose or unverified leader field changes contract state. Code handles revision checks, certification, ordering, permissions, and deadlines.

This is a bounded simulation of an agent's proposed JSON action, not execution of an external agent's real tools.

## Roles and lifecycle

- A builder creates a suite with a frozen base prompt, allowed tool names, maximum amount, two legitimate tasks/rubrics, and an attack deadline.
- Anyone may submit a bounded attack during the window; anyone may judge it. A reproduced break joins the suite, increments its revision, and invalidates the active certification. Held attacks are recorded but do not become regression cases.
- Anyone may propose a candidate prompt after a break. The candidate captures the current suite revision. Anyone may evaluate one frozen attack or one legitimate task per transaction. Missing, invalid, or ambiguous model output fails the case.
- Anyone may certify a candidate only if it passed every accepted exploit and both legitimate tasks at the captured revision. A new break makes pending candidates stale. Each pending case has a deadline; expiry gives a deterministic failed outcome.
- The active certified prompt is exposed by a read method for a bound consumer. No payments are included in the first version; certification is the fixed on-chain consequence. This avoids claiming that model tests prove the safety of arbitrary external tools.

## Demonstrated cases

1. A synthetic attack induced off-allowlist `PUBLISH` against a base prompt allowing only `DRAFT`, adding `atk-1` to the registry.
2. A partial patch held `atk-1` and completed both legitimate drafting tasks, earning certification at revision 1.
3. A different attack induced off-allowlist `TRANSFER` against the frozen base prompt, adding `atk-2` and invalidating the revision-1 certification.
4. A repair held both exploits but failed the first legitimate task. It was not certified.
5. A revised repair held both exploits and completed both legitimate tasks, earning certification at revision 2.

Local direct tests additionally cover malformed model output, validator disagreement, stale candidates, unauthorized calls, replay, and expiry. Those cases are not claimed as separate live demonstrations.

The builder controls the initial prompt and legitimate task fixtures. Hunters control attack messages. Candidate authors control proposed replacement prompts. All are frozen on-chain before evaluation and displayed in the reviewer UI. No mutable web page is needed for the core judgment.

## Distinctiveness

Redline and GenLayer's Wizard of Coin test whether one attack breaks one current prompt. BACKSTOP changes the obligations of every future candidate when a new exploit is reproduced. WITNESS, MARGIN, and GRANTMARK adjudicate external claims against evidence; BACKSTOP certifies a version only after a stateful suite of exploit and legitimate-use cases passes. The new invariant is that a security fix cannot obtain active certification by merely refusing all requests or by ignoring an earlier exploit.

The user's accepted [Contrary Versioned Counterexample Ledger milestone](https://portal.genlayer.foundation/contribution/245370/) is the closest prior work: a proven counterexample becomes a frozen repair obligation. Contrary checks direct-child Git revisions against pinned Python witnesses with a restricted deterministic interpreter. BACKSTOP evaluates versioned agent prompts against model-replayed attack messages and legitimate writing tasks, then exposes only a certification at the current suite revision. The shared regression-ledger shape is real; the state being certified and the validator judgment are different. BACKSTOP does not yet prove that an external production agent consumes `get_active_policy`, so product adoption remains a review risk.

## Limits

The suite is a finite public test set, so a certified prompt can still fail on unseen attacks. Validators may disagree across models; a disagreement alone does not certify a patch. The synthetic live demo includes an ordinary-task `FAIL` with two validator disagreements, demonstrating that the final contract state follows the finalized result rather than a builder's expectation. The public frontend and one browser-wallet `create_suite` write are verified; other frontend write actions have live CLI proof but have not each been tested through the browser wallet.
