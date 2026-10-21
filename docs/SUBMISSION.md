# BACKSTOP Portal handoff draft

The owner submits this project. This text describes the verified Studionet build; it is not a promise of a Portal score.

**Contribution type:** Builder → Projects. BACKSTOP has a public registry and browser-wallet contract integration; use the Projects category when it is available in the Portal form.

**Project logo:** Upload [`apps/backstop-web/public/portal-logo.png`](../apps/backstop-web/public/portal-logo.png), a 512 × 512 PNG (13.5 KB) exported from the app's SVG mark. The form accepts PNG, JPEG, or WebP at 128–2048 px, at most 2 MB.

**Primary tag:** AI & Agents. Suggested focus tags: Model Evaluation and AI Policy Enforcement.

**Project name:** BACKSTOP

**One-liner:** A GenLayer-native agent-policy regression registry that certifies fixes only after they survive reproduced exploits and legitimate tasks.

**Description (under 1,000 characters):**

> BACKSTOP turns reproduced prompt-injection failures into an on-chain regression suite for agent policies. Builders freeze a bounded agent prompt, allowed JSON actions, and two legitimate tasks. For each attack, GenLayer validators independently simulate the agent and code-check its proposed action; a reproduced forbidden action increments the suite revision. Candidate repairs must hold every accepted exploit and complete both legitimate tasks before the contract certifies them. A later break invalidates the active certification. The public Studionet demo shows two breaks, invalidation of a partial repair, rejection of a repair that failed ordinary work, and certification of a revised candidate. Results are finite tests, not a claim of general agent safety; no external tool is executed.

**Project and proof links:**

- [Public frontend, completed suite `bs-1`](https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry)
- [Public frontend, certified browser-wallet suite `bs-3`](https://demigodd00.github.io/backstop-studionet/?suite=bs-3#registry)
- [Dedicated source repository](https://github.com/Demigodd00/backstop-studionet)
- [Contract explorer](https://explorer-studio.genlayer.com/address/0x85ea679b9f495196A2c229C925dA24Dfc10d3401)
- [Exact deployed contract source](https://github.com/Demigodd00/backstop-studionet/blob/2821da33549ef76ac7b4a548f128a320e99450ba/contracts/backstop.py)
- [Deployment proof](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/proof.json), [23-transaction regression demo](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/demo.json), and [eleven-transaction browser-wallet record](https://github.com/Demigodd00/backstop-studionet/blob/main/deploy/browser-flow-qa.json)
- [Regression reviewer trail](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/DEMO_SCRIPT.md), [browser-wallet reviewer trail](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/BROWSER_FLOW.md), and [code walkthrough](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/TUTORIAL.md)

**Project form links:** Website: `https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry`. GitHub: `https://github.com/Demigodd00/backstop-studionet`. Contract link: `https://explorer-studio.genlayer.com/address/0x85ea679b9f495196A2c229C925dA24Dfc10d3401`. Add the source repository, deployment proof, regression trail, browser-wallet trail, and key finalized transaction URLs above as supporting evidence. No demo video has been recorded.

**How-to steps for the Project form:**

1. Open the website without a wallet. It should select synthetic suite `bs-1`; if not, select it in the registry.
2. Read the two `BROKEN` attacks and compare the first and second judgment links in the review trail. The second break moves the suite to revision 2 and invalidates `cand-1`.
3. Inspect `cand-2`'s failed legitimate-task check, then `cand-3`'s two held exploits, two passed legitimate tasks, and active certification.
4. Open the final certification transaction and the exact deployed source link. Then open `bs-3` to see the browser-wallet path reach a separate certified revision 1 state. Optionally run `python scripts/verify_backstop.py` to recheck all recorded receipts and read-backs.

**Reviewer steps:** Open the public frontend without a wallet and select `Synthetic release-note agent` (`bs-1`). Confirm two `BROKEN` attacks, three candidate versions, and revision 2. Inspect `cand-1` as the earlier certification, `cand-2` as the failed legitimate-task check, and active `cand-3` with both exploit and legitimate-task checks `PASS`. Then open `bs-3`: it should show `atk-3 BROKEN` and active `cand-4` certified at revision 1. Compare both suites with their explorer-linked reviewer trails. Optionally run `python scripts/verify_backstop.py` from the repository root to recheck deployed source, finalized successful receipts, and on-chain read-backs without a wallet key.

**Expected outcome:** `get_active_policy("bs-1")` reports `usable: true`, `candidate_id: "cand-3"`, and `revision: 2`. The earlier `cand-1` certification is unusable after the second break. The browser-wallet suite `bs-3` reports `usable: true`, `candidate_id: "cand-4"`, and `revision: 1`.

**Browser-wallet proof:** [Full eleven-write proof trail](https://github.com/Demigodd00/backstop-studionet/blob/main/docs/BROWSER_FLOW.md), including [attack judgment](https://explorer-studio.genlayer.com/tx/0x82e566d72bb24d7236d5fe55881e9287393b42695f6c2e9fc1b21e9854224455) and [repair certification](https://explorer-studio.genlayer.com/tx/0x793509d0d92c2ec3e024e0139c36a0f42622bb9ca6c0852b495a4a54f26b5947). Expiry and failed branches were not individually browser-wallet tested.
