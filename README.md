# BACKSTOP

BACKSTOP is a versioned agent-policy regression registry built for GenLayer. When validators reproduce a forbidden JSON action from a frozen attack, that attack joins the suite. Every later candidate prompt must hold **all** accepted attacks and still complete two legitimate tasks before the contract exposes it as certified. A new reproduced break increments the suite revision and immediately makes the old certification unusable.

**Current state:** the contract is [deployed on Studionet](https://explorer-studio.genlayer.com/address/0x85ea679b9f495196A2c229C925dA24Dfc10d3401), and the public frontend shows the finalized [`bs-1` regression demo](https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry) and a completed [`bs-3` browser-wallet flow](https://demigodd00.github.io/backstop-studionet/?suite=bs-3#registry). The 23-transaction `bs-1` demo shows two reproduced breaks, invalidation, a rejected repair, and a certified revision 2 repair. Eleven user-approved browser-wallet writes took `bs-3` from creation through certification at revision 1. Every recorded write finalized with successful execution. See the [regression review trail](docs/DEMO_SCRIPT.md), [browser proof](docs/BROWSER_FLOW.md), and [read-only proof verifier](scripts/verify_backstop.py).

## Why GenLayer

A deterministic parser can tell whether a proposed JSON action uses a forbidden tool or exceeds an amount cap. It cannot decide how an agent will respond to a hostile message across independent models, nor whether a patched agent meaningfully completed a legitimate writing task. BACKSTOP puts those bounded evaluations inside GenLayer's validator consensus. Ordinary code controls the suite revision, test matrix, deadlines, and certification.

```mermaid
flowchart LR
  B[Builder freezes policy and two legitimate tasks] --> S[BACKSTOP suite]
  H[Hunter freezes attack message] --> S
  S --> V[Each validator runs bounded agent prompt]
  V --> C[Code checks JSON tool and amount]
  C --> R[Reproduced exploit joins regression suite]
  R --> P[Candidate patch is tested per case]
  P --> G[Validators judge legitimate task completion]
  G --> A[Code certifies only if every case passes at current revision]
  A --> N[New break invalidates active certification]
```

The defender is a **bounded simulation**: one frozen system prompt, one user message, a JSON `answer`, and a proposed JSON `action`. No external agent tool is executed. Prompts, tasks, rubrics, attacks, and candidate versions are public on-chain. Certification means only that a version passed this finite suite at a specific revision; it is not a general safety guarantee.

## Repository

- [`contracts/backstop.py`](contracts/backstop.py) — Intelligent Contract, independently rerun model checks, versioned suite, and read methods.
- [`tests/direct/test_backstop.py`](tests/direct/test_backstop.py) — direct-mode state, safety, replay, and validator disagreement tests.
- [`apps/backstop-web`](apps/backstop-web) — no-wallet registry and wallet transaction interface.
- [`docs/DESIGN.md`](docs/DESIGN.md) — mechanism, roles, comparison, evidence plan, and limitations.
- [`docs/TUTORIAL.md`](docs/TUTORIAL.md) — code-based walkthrough.
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — completed live demonstration and reviewer links.
- [`docs/BROWSER_FLOW.md`](docs/BROWSER_FLOW.md) and [`deploy/browser-flow-qa.json`](deploy/browser-flow-qa.json) — full browser-wallet flow and receipt record.
- [`docs/SUBMISSION.md`](docs/SUBMISSION.md) — copyable Portal handoff draft and public evidence links.
- [`apps/backstop-web/public/portal-logo.png`](apps/backstop-web/public/portal-logo.png) — 512 × 512 PNG accepted by the current Portal Project logo field.
- [`scripts/deploy_backstop.py`](scripts/deploy_backstop.py) and [`deploy/proof.json`](deploy/proof.json) — resumable deployment and verified source record.
- [`scripts/demo_backstop.py`](scripts/demo_backstop.py) — resumable synthetic live regression demonstration.
- [`deploy/browser-qa.json`](deploy/browser-qa.json) — earlier standalone browser-wallet creation check.
- [`scripts/verify_backstop.py`](scripts/verify_backstop.py) — read-only verification of deployed source, finalized receipts, and current state.

## Contract flow

1. `create_suite` freezes a base prompt, allowlisted tools, amount cap, and exactly two legitimate task/rubric pairs. It starts as `DRAFT`.
2. Permissionless `validate_golden` asks validators whether each rubric is observable. The builder calls `open_suite` after both return `VALID`; the attack deadline starts then.
3. Anyone calls `submit_attack`, then permissionless `judge_attack`. Each validator runs the agent on its own model and code-derives `HELD`, `BROKEN`, or `UNCLEAR`. Only `BROKEN` joins the regression suite and increments its revision.
4. Anyone proposes a replacement prompt. `check_exploit` evaluates one accepted attack; `check_golden` evaluates one legitimate task. Each validator independently reruns and compares the exact normalized result. Invalid model output cannot pass.
5. `certify_candidate` succeeds only when all current exploit and legitimate-task checks are `PASS`, at the captured suite revision. `get_active_policy` returns `usable: true` only while that certification remains current.
6. An unjudged attack or unfinished candidate can be expired after its deadline. New attacks close at the builder's frozen attack deadline. Finalized results should be used for subsequent operations and displayed to reviewers.

No native funds move in this version. The deterministic consequence is activation or invalidation of an on-chain certified policy. This keeps the distinct regression mechanism reviewable before adding a repair reward pool.

## Local development

Use Python 3.12 and Node 22 or newer. Pin the versions from `requirements-dev.txt` and `apps/backstop-web/package.json`.

```powershell
python -m pip install -r requirements-dev.txt
genvm-lint check contracts/backstop.py
python scripts/prepare_gltest_runner.py
pytest -q tests/direct
cd apps/backstop-web
corepack pnpm install --frozen-lockfile
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
```

For the local frontend, copy `.env.example` to `.env.local` and run `corepack pnpm dev`. The example points to the verified Studionet contract. The [hosted no-wallet registry](https://demigodd00.github.io/backstop-studionet/?suite=bs-1#registry) was checked in a logged-out browser: it displayed revision 2, two reproduced attacks, three candidates, and active `cand-3` directly from finalized state. The [Pages workflow](https://github.com/Demigodd00/backstop-studionet/actions/workflows/pages.yml) publishes this view. Wallet writes are journaled locally and checked for **finalized successful execution** before the UI reports success. The [eleven-step browser flow](docs/BROWSER_FLOW.md) exercised creation, validation, opening, attack submission and judgment, repair proposal and checks, and certification; the UI read the resulting `bs-3` state. Never put a private key in the frontend or repository. Run `python -m pip install -r requirements-deploy.txt` and `python scripts/verify_backstop.py` to recheck the public chain proof without a wallet key.

## Limits and evidence status

The two legitimate tasks are public, so candidate authors can overfit them. The demo policy and attacks are synthetic and intentionally flawed; they are not evidence about a production agent. Independent models can disagree on a marginal attack or task; the failed `cand-2` golden check had two disagreeing validator votes and still finalized as `FAIL`. The read-only verifier checks the deployed source, every recorded finalized receipt, and current on-chain state. The dedicated repository and frontend are publicly accessible. The successful core browser-wallet path is evidenced; expiry and failed branches were not individually browser-wallet tested.

BACKSTOP differs from a one-prompt break bounty by making every accepted exploit alter future certification obligations. It also differs from evidence-backed claim settlement: the contract's changing registry and legitimate-use check are the mechanism, rather than one verdict and payout.
