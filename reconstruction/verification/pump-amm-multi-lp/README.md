# PumpSwap multi-provider LP lifecycle

This package closes a specific runtime-verification gap: two distinct LP
authorities operate independently on one persistent PumpSwap pool.  Existing
pool-creation and liquidity packets exercise one signed liquidity owner per
fixture, and the retained multi-hop liquidity packets reuse one actor.  They
do not establish that LP shares, withdrawals, rollback, and authority checks
remain isolated across two providers over several transactions.

The producer uses local LiteSVM instances only.  It creates provider token
accounts through the captured Associated Token program, funds them through
the captured token program under a deterministic mint authority, and invokes
the captured PumpSwap `create_pool` instruction.  The pool PDA is never a
transaction signer; PumpSwap signs its own CPI calls with canonical seeds.
Provider A, provider B, and the fee payer are separate deterministic Ed25519
keypairs.

The same serialized, fully signed transactions are submitted to independent
original and candidate VMs.  Reports retain transaction bytes, signatures,
message/blockhash hashes, structured instruction errors, events, inner instructions,
return data, compute units, and fixed watched account snapshots. Executable account
data is represented by its length and hash; ordinary account bytes are retained.  `verify.py` derives
case membership, transaction identities, signatures, accounting, rollback,
and the differential result without trusting producer acceptance fields.

## Coverage boundary

The package is intentionally narrower than a claim of PumpSwap equivalence.
It covers only the listed deterministic lifecycle plans and their observed
captured-program outcomes.  An unsupported fixture or infrastructure failure
is never counted as an equivalent case.  PumpSwap's existing exact
meaningful-ELF checkpoint is independent of this runtime evidence; this
package does not change its bytecode completion percentage.

The discovery audit was refreshed at upstream commit
`747aae62864e490ac2142906c54fe039a8e9ae66`.  Relevant existing coverage:

- `scripts/pump_amm_create_differential.py`: real pool/LP/vault creation, one
  creator per reset fixture.
- `scripts/pump_amm_liquidity_differential.py`: one deposit or withdrawal per
  reset fixture with one synthetic LP owner.
- `research/amm-multi-hop-fee-table-split-liquidity-chains-20261029/`:
  persistent liquidity/trade chains, but one liquidity actor.
- `research/pump-amm-create-pool-initial-liquidity-20261030/` and
  `research/pump-amm-liquidity-rounding-boundaries-20261030/`: captured
  positive creation and arithmetic boundaries, still one LP authority.

No open upstream PR at the audit commit implemented a multi-provider LP
lifecycle package.

## Qualified lifecycle matrix

Each complete run executes 65 signed transactions against each image. The
captured original has 62 successful and three deliberately rejected transactions.
Only nine equal cases with no unsupported fixtures or infrastructure failures
qualify the supplied candidate on this finite corpus.

| case | captured result established |
| --- | --- |
| `two-provider-independent-withdrawals` | B deposits into A's pool; A and B withdraw their own shares |
| `deposit-trade-independent-withdraw` | B deposit, real `buy_v2`, then A withdrawal at changed reserves |
| `atomic-two-provider-deposits` | A and B deposit in one transaction signed by both providers and the fee payer |
| `atomic-valid-deposit-invalid-withdraw-rollback` | the second instruction fails and every non-fee account rolls back |
| `foreign-lp-authority-refused-then-owner-withdraws` | B cannot burn A's LP ATA; B can still withdraw its own shares |
| `over-withdraw-refused-then-partial-chain` | over-withdraw fails; two later partial withdrawals succeed |
| `tiny-deposits-and-rounding` | one- and two-unit LP deposits and one-unit withdrawals |
| `token2022-base-multi-provider` | Token-2022 base mint with classic wrapped-SOL quote and Token-2022 LP mint |
| `two-pool-provider-state-isolation` | operations on pool 2 leave pool 1, its mint, vaults, and provider positions unchanged |

On every established pool state, the verifier observes
`pool.lp_supply - lp_mint.supply == 100` and the two provider LP balances sum
to the LP mint supply.  It recomputes base/quote/reserve deltas from serialized
account bytes.  The trade case includes the buyback recipient when checking
quote-token conservation.  Failed transactions must preserve all watched
non-fee state exactly.

The independent verifier reconstructs every complete Solana message from the
canonical fixture and immutable plan, checks its header and exact signer set,
and verifies every required Ed25519 signature. It binds the first prestate to
constructor state and each later prestate to the preceding poststate. All watched
addresses and executable records must remain present. It strictly decodes account
metadata and bytes, recomputes fees, accounting, rollback and outcome fields, and
compares both sides. The AMM executable account is checked against each side's own
image; its differing code identity is excluded from cross-image state equality.

The reader uses LiteSVM constructors to derive canonical fixture state, with zero
transactions unless `--replay` is requested. Saved receipts remain observations
from the producer; offline verification cannot independently prove that a VM ran
or that logs and snapshots were emitted by it. `--replay` performs a fresh bounded
execution and requires an identical report.

## Reproduce

Use normal Python with `solders==0.27.1` and the repository requirements in an
isolated environment. Supply an actual ELF candidate obtained separately; the
runtime packet does not authenticate build receipts. The maintained ordinary
source-build recipe is `scripts/amm_sell/native_build.py`; its SDK/workspace
requirements and public layout recipe are separate from this runtime admission.

```sh
python reconstruction/verification/pump-amm-multi-lp/lifecycle.py \
  --candidate /absolute/path/to/rebuilt-pump-amm.so \
  --output /tmp/pump-amm-multi-lp-report.json.gz
python reconstruction/verification/pump-amm-multi-lp/verify.py \
  --candidate /absolute/path/to/rebuilt-pump-amm.so \
  --report /tmp/pump-amm-multi-lp-report.json.gz --replay
python -m unittest discover \
  -s reconstruction/verification/pump-amm-multi-lp -p 'test_*.py' -v
```

Outputs must be outside the repository, and existing files and dangling symlinks
are refused before execution. Reports are published exclusively. Producer and
reader load local Python dependencies from captured source bytes, ignoring
bytecode caches, and verify their fixed code/data inventory before and after
operations. All original/dependency images are pinned to captured hashes. The
candidate and every executable are frozen for the duration of each run. Optimized
Python, duplicate JSON keys, nonfinite values, malformed or incomplete signatures,
and fabricated build receipts are rejected.

## Qualification and limitation

The `qualification/` directory preserves the author's historical v1 reports and
self-reported build context. Those files are not admitted by the repaired v2
reader and are not source-build proof. Fresh v2 results and exact code/input pins
are recorded separately in `results/`; final qualification identifies the actual
report bytes and their supplied candidate.

The repair was exercised with an actual ordinary AMM source build using the
maintained native recipe and official platform-tools v1.44. The actual candidate
SHA-256 is `51a5f6a7fb5a812de7686e593ce6159f6ee59b15771a3d5d37ab661c46d64586`.
Its separate retained build context includes the real compiler/linker invocations,
logs, source equality, image bytes and disclosed public layout/workspace recipe.
This runtime suite labels it `supplied_binary_only`; its source snapshot fields
are contextual and do not assert that an arbitrary supplied ELF was built from
that snapshot. No source-build receipt is accepted by this suite.

Finite signed execution does not establish broad semantic equivalence, compute
unit equality, or new whole-program byte identity. Token-2022 coverage uses the
plain mint/account layout in the named fixture and does not cover arbitrary
extensions. This packet does not change the repository completion percentage.

The repaired v2 selected report is `results/report.json.gz` (SHA-256
`5c30dc80f6588ae323d445b7a26f2503a68336bd797167949e41262fe24377a7`). Its separate original
control is `results/original-control.json.gz`; `results/qualification.json` records
exact input/code pins, 56 passing focused methods plus the final pure replay-context
regression, seven repaired false-admission controls, and the independent reader audit.
The selected run and fresh replay each observed nine equal cases and 65 genuine
signed transactions per image, with 122 required signatures verified per image.
