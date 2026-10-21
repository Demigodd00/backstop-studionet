# BACKSTOP Portal handoff draft

The owner submits this project. This text describes the verified Studionet build; it is not a promise of a Portal score.

**Contribution type:** Project / deployed Intelligent Contract (use the closest current Portal label).

**Project name:** BACKSTOP

**One-liner:** A GenLayer-native agent-policy regression registry that certifies fixes only after they survive reproduced exploits and legitimate tasks.

**Description (under 1,000 characters):**

> BACKSTOP turns reproduced prompt-injection failures into an on-chain regression suite for agent policies. Builders freeze a bounded agent prompt, allowed JSON actions, and two legitimate tasks. For each attack, GenLayer validators independently simulate the agent and code-check its proposed action; a reproduced forbidden action increments the suite revision. Candidate repairs must hold every accepted exploit and complete both legitimate tasks before the contract certifies them. A later break invalidates the active certification. The public Studionet demo shows two breaks, invalidation of a partial repair, rejection of a repair that failed ordinary work, and certification of a revised candidate. Results are finite tests, not a claim of general agent safety; no external tool is executed.

**Project and proof links:**

- [Public frontend, completed suite `bs-1`](https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry)
- [Dedicated source repository](https://github.com/Demigodd00/backstop-studionet)
- [Contract explorer](https://explorer-studio.genlayer.com/address/0x85ea679b9f495196A2c229C925dA24Dfc10d3401)
- [Exact deployed contract source](https://github.com/Demigodd00/backstop-studionet/blob/2821da33549ef76ac7b4a548f128a320e99450ba/contracts/backstop.py)
- [Deployment proof](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/proof.json), [23-transaction demo record](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/demo.json), and [browser-wallet QA record](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/browser-qa.json)
- [Detailed reviewer trail](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/DEMO_SCRIPT.md) and [code walkthrough](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/TUTORIAL.md)

**Reviewer steps:** Open the public frontend without a wallet and select `Synthetic release-note agent` (`bs-1`). Confirm two `BROKEN` attacks, three candidate versions, and revision 2. Inspect `cand-1` as the earlier certification, `cand-2` as the failed legitimate-task check, and active `cand-3` with both exploit and legitimate-task checks `PASS`. Compare those states with the key explorer transactions in the reviewer trail. Optionally run `python scripts/verify_backstop.py` from the repository root to recheck deployed source, finalized successful receipts, and on-chain read-backs without a wallet key.

**Expected outcome:** `get_active_policy("bs-1")` reports `usable: true`, `candidate_id: "cand-3"`, and `revision: 2`. The earlier `cand-1` certification is unusable after the second break. The separate browser-wallet transaction created public draft `bs-2`; it is QA evidence, not a certified demo.

**Browser-wallet proof:** [Finalized `create_suite` transaction](https://explorer-studio.genlayer.com/tx/0x8507c90f9af4bedf7f9a26bac2bcff698f660abfa83ed8555ee415567191d1b2). The remaining frontend write buttons have not each been exercised through a browser wallet.
