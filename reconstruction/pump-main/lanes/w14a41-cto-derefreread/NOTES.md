# w14a41-cto-derefreread: source forms for the re-read leads of admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: find source forms for the post-opt IR re-read leads of w14a03-cto-liverange (#3228). The mechanism is the one behind #3241
(qlin2): when a deref sits behind `||`, or a helper is written out inline, the dominating load disappears and LLVM re-loads the
value instead of keeping it live.
Bases: main faf996242 (0.65129, M 2,174) and then main 6db95a764 (#3315, 0.65458, M 2,185, 3,279 slots). Both oracles were
checked against the baseline build (`eq_main` true on the empty edit).
Ledger approach `ir-reread-bound` / `deref-reread`, keys `0x22a10-w14-{faf9962,6db95a7}-derefreread-*-v1`.

**Result: no zero-loss gain and no source change.** All three leads are gone on current main:
- the oracles have no source-expressible re-read, hold or remat edit that gains at the pin;
- 27 source spellings either fold to main's tokens, byte for byte, or lose;
- the faithful size knobs cost 4 to 23 M each, so they cannot pay for a lead that shrinks the function.

Read the M values with w14a14's note: `ratio = 2M / (3339 + n)`. At the pin, only a change in M counts.

## 1. The leads, re-measured (w14a03 `irre.py --sub`, post-opt IR, llc, score)

| lead | 53abf28 (w14a03) | faf9962 | 6db95a7 |
| --- | --- | --- | --- |
| (a) holder_enabled `%33` (global+1087) re-read at the validate holder test | +0.0043 @ -184 B | **+1 M @ -40 B** (0.65208 @ 27,360) | **0 M @ -40 B** |
| (b) `ctx.accounts` (`%_266`) re-read per block, including the pool_updated test | +0.0023 @ +32 B | best -2 M @ +8 (bb88.i) | best 0 M @ +16 (bb25.i) |
| (c) global box pointer in the global_quote users | +0.0006 @ 27,400 | none (qlin2 #3241 already took it) | none |
| sharing_config pointer `%_382` re-read in bb1 (owner test) | | +1 M @ +8 | +1 M @ +8 |
| clone-run x pointer `%_232.i130` (accounts+128) after inc_strong | | | +1 M @ +8 |
| collect payload piece `%_196.1.i` after Clock::get | | +5 M @ -160 **(invalid IR)** | |

- **Treat `%_196.1.i` as an oracle artifact.** The edit re-reads the `collect` sret buffer `%_58.i` after its `lifetime.end`
  (bb82.i), so stack coloring may hand that slot to another value. `irre.py` does not check lifetimes. Lanes reusing it should
  drop variants whose pointer is an alloca ended before the new load.
- `%_382@bb1` has no source form. The owner test follows the key memcmp in the same `&&` chain. memcmp is
  argmem-readonly, so GVN folds every re-read of `accounts+144`.
- Full tables: `data/irre-faf9962.tsv`, `data/irre-6db95a7.tsv` (dM, dbytes, ratio, variant, IR line).

## 2. Lead (a) with faithful fill: no pair reaches the pin (faf9962, raw-IR capture oracle)

w14a31's +8/+16 knobs, alone and combined, each with and without the (a) re-read (an IR edit on the knob base's post-opt module):

| base | bytes | M | + (a) re-read: bytes | M |
| --- | ---: | ---: | ---: | ---: |
| main | 27,400 | 2,174 | 27,360 | 2,175 |
| n_ensiflet | 27,408 | 2,170 | 27,368 | 2,171 |
| k3 / wl_writ_eq | 27,408 | 2,169 | 27,368 | 2,169 |
| s_rent_get | 27,416 | 2,162 | 27,376 | 2,162 |
| K24 = s_rent_get+k3 | 27,424 | 2,165 | 27,384 | 2,166 |
| K32a = s_rent_get+k3+wl_writ_eq | 27,432 | 2,163 | 27,392 | 2,163 |
| K32b = s_rent_get+k3+n_ensiflet | 27,408 | 2,155 | 27,368 | 2,156 |
| K40 = all four | 27,416 (not additive) | 2,151 | 27,376 | 2,151 |

Every knob costs more M than the lead gives (at most +1). On 6db95a7 the lead is worth 0 M. k3 and wl_writ_eq are now on main
(#3315 used them as fill), and nativejoin rewrote the native arm, so the s_rent_get and n_ensiflet texts no longer apply there.

## 3. Source spellings (raw-IR capture + opt + llc, `tools/capvar.sh`; `data/source-screens.jsonl`)

On 6db95a7 (main M 2,185 @ 27,400):

| name | form | result |
| --- | --- | --- |
| h_g | validate gets `g:&Global`; holder test `!g.is_holder_reward_enabled` (st field kept) | byte-identical (GVN forwards the st-literal load) |
| h_gor / h_gand | `!(st.holder_enabled\|\|g.is_holder_reward_enabled)` / `&&`: a deref behind a short-circuit | byte-identical |
| h_gacct | `g:&Account<Global>` and an extra `&&!g.is_holder_reward_enabled` | 0.64243, M 2,138 @ 27,232 |
| h_acc | `#[inline(always)] fn he(g:&Global)->bool` accessor | 0.41547, M 1,386 @ 27,368 |
| p_ctx / p_ctxown | pool gate through a fresh `ctx.accounts` (both operands, or only the owner) | byte-identical |
| p_ai | pool gate `a.pool.to_account_info().owner==&AMM` | 0.65183, M 2,182 @ 27,552 |
| q_ctx / q_derefg | contains via `ctx.accounts.global` / `(&**a.global)` | byte-identical |
| st_ctxg | st `max_fee` via `ctx.accounts.global` | byte-identical |
| evhr | event `is_holder_reward:a.bonding_curve.is_holder_reward` (the original reads curve+0xa5 here) | 0.65169, M 2,175 @ 27,392 |
| hv_ctxarm / hv_clone | sweep token-arm `authority:` via `ctx.accounts` / `.clone()` | byte-identical |
| hv_destne | sweep PDA check `dest!=a.holder_creator_vault.key()` | 0.65398, M 2,183 @ 27,400 |
| hv_ctxhead / hv_refne / hv_ctxboth | PDA check `*ctx.accounts.holder_creator_vault.key!=dest` / `key!=&dest` | 0.65197, M 2,173 @ 27,320 (in-place compare drops the `key()` copy) |

On faf9962 (main M 2,174), with the curve flags read into locals before `quote_locked` (orig 0x290 order: w14a04's flaghoist
re-tested):

| name | form | bytes | M |
| --- | --- | ---: | ---: |
| F1/F2/F3/F10 | flags as a tuple, separate lets, 3 orders, or through a `c:&BondingCurve` binding | 27,304 | 2,029 (all equal) |
| F4 | same plus `let g=&a.global` for contains and st | 27,304 | 2,029 |
| F5/F6/F7 | `let g:&Global=&a.global` plus flags | 27,296 | 2,021 |
| F8/F9 | g binding only (undoes qlin2's reload) | 27,368 | 2,142 |

Why every fresh-deref spelling folds: `ctx` is `noalias readonly dereferenceable(48)`, so the accounts pointer is one SSA value.
The Box and Account pointers behind it are loaded with no intervening clobber, because every call between the two reads is
memcmp (argmem-readonly) or an error path that returns. A re-read survives only where the dominating load disappears (qlin2:
the only load was on the `contains` path) or where a call or an Rc `inc_strong` store sits between the two reads (the
clone-run literals that w14a17/w14a23/w14a30 landed).

## 4. Hold and pure-value remat oracles on 6db95a7 (`data/irhold-6db95a7.tsv`, `data/irremat-6db95a7.tsv`)

- Hold (83 variants): best `%_59.i128<-%x.i`, +1 M @ -8 B.
- Remat (112, `--sub`): **`%327@bb44.i117` +2 M @ 27,400 (0.65518, 3,275 slots)**, the only at-pin gain in any of the
  three oracles.
  - `%327` is the gep `accounts+264` (`&a.holder_creator_vault`, inline AccountInfo, `0x108`).
  - Main computes it at the sweep PDA check (main 0x24930 `mov r6,r8; add64 r6,0x108`) and holds it in r6 until the token-arm
    create_idempotent `authority:` clone, spilling it late (0x24ac8 `-0x9b8`).
  - The original computes it there too, but spills it at once (orig 0x24948-0x24958 `[r10-0x8e0]`) and reloads it.
  - Recomputing it in bb44 frees r6 across the sweep.
  - No source form: every spelling of the arm's AccountInfo address is the same constant gep off the same accounts SSA value,
    so GVN merges it into the head's gep (hv_ctxarm and hv_clone are byte-identical). The head's key load folds the gep
    into its address, and ISel materializes the cross-block use where the value is defined.
  - Giving the arm its own gep needs an accounts pointer that is not CSE'd, and `ctx` is readonly noalias.

## Tools (experiment only, `tools/`)

- `capvar.sh <name> <edits.py> <slot>`: w14a03/w14a31 raw-IR capture plus `rx.py`, which prints M, repointed at this lane.
- `q.sh <slot> name...`: queue over `e/<name>.py`. It deletes the crate copy and the IR after each row.
- `irre.py`, `irre_lib.py`, `irremat.py`, `irhold.py`: the w14a03 oracles, patched to report `M` per variant.
- `e/*.py`: every edit list above.

Next ideas (not this angle): the remat lead needs an RA-level change, not a load change. It is the same accounts+0x108
hold that splicemap (#3319) found in the PDA-first p1 swap. A partner that makes greedy split `&holder_creator_vault`
early, so it is spilled at its definition as in the original, would take it. That would need a use-count change in the sweep head
and does not change the call count.
