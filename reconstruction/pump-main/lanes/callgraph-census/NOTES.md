# Lane callgraph-census: call-graph and inlining-boundary census

## Round 2 (base origin/main 60bdd8a, 1020 normalized / 188 raw)

### Hidden call-target audit (`callid_audit.py`, `CALLID-AUDIT.json`)

score.py masks call immediates, so a window can match normalized while calling the wrong function.
`callid_audit.py` computes the greatest bisimulation over the call graph: start from score.py's
relation (same length, same normalized body), pin the 16 unmatched windows to their candidates, and
drop a pair (orig, ours) whenever some call site pairs callees that are not themselves related.
A normalized match with no surviving partner calls a wrong target somewhere and can never be raw.

On main 60bdd8a: 1015 of 1019 normalized matches are bisimilar. The 4 failures all trace to one
site (`entrypoint`, `entry` and `__global::set_reserved_fee_recipients` fail only through their callee):

| window | site | original calls | ours called | fix |
|---|---|---|---|---|
| 0x6fef8 set_reserved_fee_recipients | rent-exempt `format!` (line 65, pos 53) | outlined `alloc::fmt::format` | `format_inner` (format inlined, cost 185 vs hot threshold 325) | `#[cold]` on `rent_exempt_error`: BPI marks the block that calls a cold fn cold before the inliner considers `format`, so it stays outlined (cold threshold 45). Bytes unchanged. |
| 0x6cd78 process_cashback_inner (pinned) | pos 35, after transfer_native | `Account::<UserVolumeAccumulator>::try_from` | `try_from_unchecked` | `try_from`: both bodies are equal after masking; the original's calls `try_deserialize` (checked), not `try_deserialize_unchecked`. Reverts ledger row `0x6cd78-main-d2cb88d-try-from-unchecked-v1`, whose identification came from the normalized body alone. |

After both: 1019 / 1019 normalized matches bisimilar, census msdiff for 0x6cd78 2 -> 0 (58/58 aligned),
1020 / 188, no gains or losses. Ledger attempts cfbc2c9a, a5feccda.

Lesson for reconstruction lanes: when choosing between functions that differ only in which helper they
call (try_from / try_from_unchecked, `format` / `format_inner`, generic monomorphs), use the census
key (body + callee identities), not the normalized body, and re-run `callid_audit.py` before a PR.

### Census refresh on 60bdd8a

Other lanes merged since round 1. Remaining call-graph differences (CENSUS-TABLES.md): 0x22a10
admin_cto (msdiff 7; the admincto-reconstruction lane has an equal-multiset variant using the
hot/cold rule), 0x77940 claim_v2 (7), 0x5b3b0 swap_hop (1 extra clone), 0x72810 sweep (orig +1 memcmp).
All other unmatched windows now have an identical callee multiset.

Baseline: origin/main d2cb88d (`$BASE/unstripped.so`, sha256 04fdafc0..., 1019 normalized / 188 raw).
Tool: `census.py` in this directory (read-only; reuses the harness `score.py` masking, `win.py`, `coords.py`).
Outputs: `CENSUS.json` (full per-target data), `CENSUS-TABLES.md` (generated tables).

```bash
python3 reconstruction/pump-main/lanes/callgraph-census/census.py [--cand <unstripped.so>] \
  --json CENSUS.json --md CENSUS-TABLES.md [--only 0x5b3b0,...]
```

## Method

- Direct internal calls (`call` with src=1, imm != -1) in physical order; target = site + 8 + imm*8.
  Syscalls are counted separately.
- Callee identity = normalized body sha256 (exact score.py masking), refined 6 rounds Weisfeiler-Lehman
  style with the callees' identities (masking hides call targets, so e.g. `ToString::to_string<A>` and
  `<B>` would otherwise collide). The 16 unmatched windows are pinned to their README candidates.
  Every original callee of every target resolves (all are matched windows or one of the 16).
- Sequence alignment (difflib) of callee keys; multiset differences classified as:
  `orig-calls; we inline` (helper exists standalone in ours but this function does not call it),
  `we outline; no such function in original` (ours-only helper: the original inlined it everywhere),
  etc. Depth-2 evidence = the missing helper's own callees that show up as extra direct calls on the
  other side.
- Argument setup per aligned call: the last write to each of r1..r5 since the previous call,
  callee-saved registers folded to `rS`; `shape` also masks stack offsets.
- Error-message form per Anchor error site: `fmt` = direct `<PumpError as Display>::fmt` call
  (ToString inlined), `to_string` = outlined `ToString::to_string` call, attached to the next
  `Source{file,line}` coordinate.

## Headline results

| target | fn | calls orig/ours | callee multiset | verdict |
|---|---|---:|---|---|
| 0x14f4e0 | buy_exact_sol_in | 101/101 | equal, order equal, args equal | not a call-graph problem (2 swapped loads) |
| 0x80df8 | v3_buy_costs | 17/17 | equal | one `expect_failed` site moved (orig pos 4, ours pos 16) |
| 0x6cd78 | process_cashback_inner | 58/58 | to_string vs fmt at sell.rs:85 | error site placement/frequency |
| 0x83c00 | v3_execute_buy | 22/22 | equal, order equal | not a call-graph problem |
| 0x13f630 | buy_exact_quote_in_handler | 130/130 | equal, order equal | not a call-graph problem |
| 0x13b9b8 | buy_handler | 90/90 | equal | two closure calls moved |
| 0x144508 | sell_v2::execute | 80/80 | equal | one Clock::get moved by one position |
| 0x4c158 | create_token_account_v2 | 10/10 | equal, order equal | not a call-graph problem |
| 0x147ba0 | trade::buy | 29/29 | equal | one memcmp moved (orig pos 4, ours pos 2) |
| 0x14a8a8 | trade::sell | 47/47 | equal, order equal | not a call-graph problem |
| 0x1489f8 | trade::buy_exact_quote | 66/66 | equal | 8 calls reordered |
| 0x72810 | sweep::execute | 37/36 | orig +1 memcmp | one extra key compare in original |
| 0x1e7c0 | create_v2::execute | 125/126 | fmt/to_string flips, memcpy +1 | error-site frequency + one memcpy |
| 0x77940 | cashback::claim_v2 | 68/62 | **inline boundary differs** | see below |
| 0x5b3b0 | swap_hop | 107/94 | **inline boundary differs a lot** | see below |
| 0x22a10 | admin_cto::execute | 154/178 | **21 AccountInfo::clone inlined in orig** | see below |

Key negative result: for 10 of the 16 windows (all except 0x77940, 0x5b3b0, 0x22a10, 0x1e7c0,
0x6cd78, 0x72810) the direct-callee multiset is identical (depth-6 identities), and for 5 of
them the physical order is identical too. Their residuals are intra-function (block layout,
register allocation, stack slots, expression shape), not helper/inlining boundaries; adding or
removing `#[inline]` helpers there is unlikely to help.

## Per target

### 0x5b3b0 multi_hop_curve::swap_hop (ratio 0.158)

The inlining boundary is clearly different. The original:

- **Inlines `emit!` + `emit_cpi!` three times** (TradeEvent, CompleteEvent, PostCompleteBuyEvent):
  it calls `<E as Event>::data` twice per event, `sol_log_data` x3, `Vec::from_iter` x3
  (the macro's `disc.into_iter().map(|b| *b).chain(inner).collect()`), `exchange_malloc` x3
  (`vec![AccountMeta]`), `Instruction::new_with_bytes` x3, `invoke_signed` x3 and
  `From<ProgramError>` +3 (the macro's `.map_err(Error::from)?`). Ours outlines the hand-written
  generic `route_event` (3 monomorphs, none exist in the original) with an `Instruction {..}` literal
  and `extend_from_slice`. Implication: replace `route_event(..)` by the literal `emit!`/`emit_cpi!`
  expansion (anchor-attribute-event 0.31.2), inline in swap_hop.
- Calls `trade::sub3` x2 where ours has `sub(sub(x,pf)?,cf)?` (multi_hop_curve.rs:580 and :679)
  through the ours-only helpers `multi_hop_curve::sub` (x5), `add` (x2), `div` (x2).
- Calls `buy_fee_market_cap` (ours: inline `div(supply*vqr, vtr)` at :572; note the original
  helper picks `token_total_supply` in mayhem mode).
- Calls `constant_product::tokens_for_quote` (ours: inline `div(effective*vtr, vqr+effective)` at :589).
- Calls `trade::post_complete_buy_event` (ours: struct literal with `sub`/`add` at :789-794).
- Calls `trade::quote_payments::transfer_native` once more (ours: the ours-only `move_lamports`
  at :762, last-hop native sell payout).
- `__multi3` x2 in ours disappears in the original (it lives inside `buy_fee_market_cap`).

### 0x77940 cashback::claim_v2 (ratio 0.167)

- Ours outlines `anchor_lang::Lamports::add_lamports` (single caller; no such function exists
  anywhere in the original). Its depth-2 callees (`lamports`, `try_borrow_mut_lamports`,
  `From<ProgramError>`) are exactly the original's surplus. Implication: the original either wrote the
  lamport credit by hand or `add_lamports` was inlined (e.g. called on a different receiver type).
- Original calls `AccountInfo::data_is_empty` once (before `try_borrow_data`, physical pos 9) where
  ours uses `data.is_empty()` on the borrowed slice.
- Original order: token-account branch (data_is_empty, try_borrow_data, deserialize) physically before
  the native `Rent::get`/`minimum_balance`/`lamports`; `AccountInfo::clone` +2.

### 0x22a10 admin_cto::execute (ratio 0.095, orig 27,400 B vs ours 18,464 B)

- The 21 surplus `AccountInfo::clone` calls in ours (54 vs 33) are exactly the clones the original
  **inlines**: 42 inline Rc strong-count increments in two call-free regions, 13 clones at
  0x26a8..0x33f8 (just before `pump_amm::cpi::transfer_creator_fees_to_pump_v2`, 12 accounts + program)
  and 8 clones at 0x3da8..0x45d0 (just before `pump_fees::cpi::admin_cto_sharing_config`, 7 accounts
  + program). These account for most of the 8.9 KB size gap. The third CPI (`admin_cto_pool`) keeps
  outlined clones in both builds.
- Physical order differs too: the original calls transfer_creator_fees_to_pump_v2 (pos 67) and
  admin_cto_sharing_config (pos 70) before admin_cto_pool (pos 82) and then the collect/create_idempotent
  path; ours places transfer_creator_fees_to_pump_v2 near the end (pos 157).
- Implication: the two CPIs with inlined clones were probably compiled in their own small function
  (LLVM inlines `Clone::clone` bottom-up into the small helper, then the helper into execute), or built
  through a path whose clone is MIR-inlined. Test: move each CPI into a separate non-`inline(never)` fn.

### Inline decisions are a per-site hot/cold bit (confirmed with inliner remarks)

`capture_inline.py` (experiment-only `-C remark=inline` on the root crate; same unstripped hash as the
source build) shows the two small callees that differ between the builds sit exactly between LLVM's
cold-callsite threshold and the inline-hint threshold:

| callee | cost | outlined at cold sites | inlined at normal sites |
|---|---:|---|---|
| `<AccountInfo as Clone>::clone` | 60 | threshold 45 | threshold 325 |
| `<T as ToString>::to_string` (inside `From<PumpError>`) | 130 | threshold 45 | threshold 325 |

Without profile data LLVM calls a site cold when its block frequency is below 2 % of the function's
entry frequency. So every original site where `clone` or `to_string` is **inlined** (no call; for
to_string a direct `<PumpError as Display>::fmt` call) is at >= 2 % entry frequency in the original CFG,
and every site where it is a call is below 2 %. This gives the reconstruction lanes a hotness bit per
site:

- admin_cto (0x22a10): the original's transfer_creator_fees_to_pump_v2 (13 accounts) and
  admin_cto_sharing_config (8) CPIs are hot; in ours every clone site in execute is cold. Something in
  our execute's control flow drops the frequency below 2 % much earlier than in the original.
- create_v2 (0x1e7c0): create_v2.rs:205, :210, :541 are hot in the original (fmt) but cold in ours
  (to_string); 11 vs 6 hot error sites overall.
- process_cashback_inner (0x6cd78): sell.rs:85 is cold in the original, hot in ours.
- claim_v2 (0x77940): the original's two clones at pos 26/55 and the to_string at :333.

**`#[inline(always)]` vs cost-model inlining.** An always-inline helper is inlined by the
AlwaysInliner before the CGSCC inliner looks at its small callees, so its `to_string`/`clone` sites
are judged at the caller's frequency (often cold). A normally inlined helper is optimized first on its
own (entry frequency 100 %, sites hot) and then inlined. So: original hot + ours cold inside an
always-inline helper -> the original helper was a plain fn (create_v2 t12); original cold + ours hot
inside a plain nested fn -> the original was always-inline or inline code (process_cashback_inner t15).
`HOTNESS.md` (from `hotness.py` over a `capture_inline.py --lines` build of this branch's swap_hop
source) lists every remark site per target.

Extracting a CPI into a small helper makes its clones inline (the helper's entry is hot), but the
helper is then not inlined back (t9/t11); `#[inline(always)]` inlines it before the clones (t10). The
fix has to be control flow (block frequency), not helper boundaries.

### 0x72810 sweep::execute

Same size (7,832 B) but ratio 0.298. Original has one more `memcmp` (pos 12, 0x6e0, near sweep_fees.rs:123)
and `format_inner`, `admit_associated_token_account`, `From<ProgramError>` at earlier positions.

### Equal-multiset targets

0x14f4e0, 0x83c00, 0x13f630, 0x4c158, 0x14a8a8: identical direct-call sequences.
0x80df8 (`expect_failed` placement), 0x13b9b8 (two closures), 0x144508 (Clock::get), 0x147ba0
(memcmp), 0x1489f8 (8 reordered calls): reorder only. Recurring argument-setup pattern in the buy/sell
v2 handlers: the original re-loads `ldxdw r3, [r3 + 0]` (a pointer read through a reference) at
`transfer_from_user*` call sites where ours passes a callee-saved register or `[rS + 0x1a0]`, and
uses frame offsets 0x20 lower (`-0x4c0` vs `-0x4a0`) for the shared admit/check locals.

## Trials

See the ledger (`--lane callgraph-census`) and the table below (filled as trials land).

| trial | target | mechanism | result |
|---|---|---|---|
| t1 | 0x5b3b0 | `route_event` -> `#[inline(always)]` literal emit!/emit_cpi! expansion | ratio 0.1575 -> 0.1690, calls 94 -> 121, all event-callee diffs gone (ledger 15443db7) |
| t2 | 0x5b3b0 | + sub3 x2, buy_fee_market_cap, tokens_for_quote, post_complete_buy_event, quote_payments::transfer_native | 0.2078, 113 calls, 20,264 B (ab955690) |
| t3 | 0x5b3b0 | + one hoisted fee_config data_len, buyback_fee = received_buyback | **0.2229, 108 calls (orig 107), 19,024 B (orig 18,584); kept in source** (1f217d1e) |
| t4 | 0x5b3b0 | + validate_buyback args without clones | 106 calls, ratio 0.127 (141c0f0f) |
| t5 | 0x5b3b0 | + one of the two validate clones removed | 107 calls, callee multiset identical, ratio 0.119 (a5064c2b) |
| t6 | 0x5b3b0 | t4 + `mint_key = h.base_mint.to_account_info().key` (orig seeds point into a temporary clone's key) | multiset identical, 18,552 B (32 B short), insn-jaccard 0.354 > t3 0.349, win.py ratio 0.127; `t6-call-multiset-exact.patch` (75e75861) |
| t7 | 0x77940 | manual lamport credit instead of `add_lamports` | add_lamports/lamports/try_borrow_mut/From counts equal orig, aligned 48 -> 52, ratio 0.167 -> 0.164 (8179d4d2) |
| t8 | 0x77940 | t7 + `data_is_empty()` before `try_borrow_data` | multiset diff down to fmt/to_string and clone 6 vs 8, ratio 0.163 (5aeb7a66) |
| t9-t11 | 0x22a10 | CPI or accounts-struct helper for transfer_creator_fees | clones inline inside helper, helper stays outlined; inline(always) undoes it (db8120b9) |
| t12 | 0x1e7c0 | drop `#[inline(always)]` from `initialize_quote_accounts` and `validate_create_metadata` (attribute lines blanked) | **0.2467 -> 0.2653, 126 calls unchanged, error hot/cold 11/6 = original (was 6/11), multiset diff only memcpy +1; kept in source** (7dcc3207). Only validate_create_metadata: 0.2760 (hot/cold 9/8); only initialize_quote_accounts: 0.2400 |
| t13 | 0x1e7c0 | also drop it from `create_quote_config` / CPI helpers | loses 0x18678 (and 0x1c880); rejected (b0401991) |
| t15 | 0x6cd78 | `#[inline(always)]` on nested `check_existing` | multiset identical, hot/cold equal orig, 8600 B, ratio 0.7354 -> 0.7321; same result already logged by cashback-inner-reconstruction (key collided), not re-recorded |

win.py's ratio is a difflib alignment and collapses when LLVM re-lays blocks (t4-t6 match the
original's callee multiset and size far better yet score lower). `blocksim.py` gives order-insensitive
block and instruction Jaccard as a second diagnostic.
