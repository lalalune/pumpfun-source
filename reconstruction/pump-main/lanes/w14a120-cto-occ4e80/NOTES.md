# w14a120-cto-occ4e80: why pool_updated keeps r6 at the event, and what the n1 form changes (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main `ebe5387e1` (0.67316 / 3,123).
Angle: the event accounts-pointer piece at orig 0x4e80 (w14a105's `1687=r6`, w14a91's H1 lead).
Oracle: raw-IR capture + opt/llc (`rx.py`, `eq_main` true on the unedited capture) and the w14a84 private RAPRIO llc
(colmap / screen / climb). Ledger: approach `occ4e80`, keys `0x22a10-w14-ebe5387-occ4e80-*`.

**Result: notes only, no gain at 27,400 B.** Best zero-loss candidate at the pinned size is main itself.

## 1. Vreg ids on ebe5387

| value | vreg | ours | orig |
| --- | --- | --- | --- |
| pool_updated (MOV 0 / MOV 1 phi) | %1649 | r6 | r8 |
| event accounts piece (0x4e48-0x50e8 ours) | %1684 | r8 | r2 at 0x4e80, then r6 from 0x4f38 |
| curve-block accounts piece | %1682 | r6 | r3 (reloaded) |
| pool-arm accounts piece | %1678 | r6 | r6 |
| old_fee | %288 | spilled (evicted by 1649) | spilled at def |
| nf (`let nf` before the pool gate) | - | r9 across the pool CPI | no such value: orig reads [curve+112] at 0x4fd8 |
| swept | %1624 | spilled | r9 |
| sharing tag | %59 | spilled, reloaded into r3 | r6 to 0x4f28 |

Single force `1684=r6` on main: **0.67585 @27,400** (+0.0027). pool_updated goes to r9 and evicts nf.

## 2. Why pool_updated holds r6 (greedy trace, `-debug-only=regalloc`)

- Step 589: %1649 finds r6..r9 all busy over its range. It evicts old_fee %288 (the cheapest at w=1.37e-6) from r6.
- Step 1172: %1684 is a split product of %0. Its hint is r2, which it misses because the range spans calls. It takes the
  first free callee-saved register, r8. r6 is never free for it.
- The original avoids this because r6 holds the sharing tag up to 0x4f28. Greedy then splits the accounts value around the
  tag: r2 for the authority read, r6 after the tag dies. r8 holds pool_updated and r9 holds swept.

## 3. Source forms (raw-IR oracle, ebe5387)

| key | form | bytes | ratio |
| --- | --- | ---: | ---: |
| a1 / a3 / a4 | pool_updated as the value of the pool-CPI `if` / `match` (`{cpi?;true}` / `{msg;false}`) | 27,400 | = main (byte-identical) |
| a2 | the same with pargs before the gate | 27,456 | 0.63085 |
| e1 / e2 / e3 | event reads `ctx.accounts` (rebinding `a`, authority only, whole literal) | 27,400 | = main |
| **n1** | no `nf` local: event `new_creator_fee_bps:a.bonding_curve.creator_fee_bps` (the original's read at 0x4fd8) | 27,376 | 0.67106 |
| n1 + e1/e2/e3/sr/p_pool/pu_neg/cs_old_fee_first/cu_replace | | 27,376 | = n1 |
| n1 + ph (`holder.unwrap_or(false)` pool arg) | | 27,408 | 0.63262 |
| n1 + pu_own (owner first) | | 27,416 | 0.63402 |
| n1 + ev_nf_unw / cu_match / cu_fee_first / ev_ts_clockvar | | 27,400 / 27,368 / 27,376 / 27,376 | 0.66477 / 0.67056 / 0.66837 / 0.66807 |
| of1 / of2 | old_fee (and old_creator) read before the sharing match | 27,496 | 0.48295 / 0.44169 |
| n1 + 24 B repays (c1-c8) | p_colnat, rP_back, wl_writ_eq, cu_unwrapcur, wl_ts_clockvar, g_w_clock_local | 27,400 | best **0.67076** (c4 = p_colnat+rP_back+wl_writ_eq, c8 = p_colnat+rP_back+cu_unwrapcur) |

n1 singles (+repay sizes on n1): rP_back +8 (.67006), p_colnat +8 (.67096), wl_writ_eq +8 (.67006), cu_unwrapcur +8
(.66976), n_mapamt +8 (.66946), wl_ts_clockvar / g_w_clock_local +16 (.66996), ev_mint_key +16 (.66187), hkmut +32
(.66677), nf_blk +24 (= main).

## 4. n1 is the original's event form and has a higher RA ceiling, but old_fee then keeps r6

- On n1, r9 is free over the pool region because nf is gone. pool_updated %1648 takes r9 without evicting anything, so
  old_fee %288 keeps r6 from the curve block to the event. The event piece %1682 again misses its r2 hint and takes the
  free r8.
- `1682=r6` on n1 evicts old_fee, which is then spilled at its definition as in the original: **0.67676 @27,376**
  (+0.0057 over n1). On c4 at 27,400 the same force gives **0.67645 @27,400**, above main's own single-force 0.67585.
- n1 climb ceiling (11 forces): **0.68485 @27,376**. Main's is 0.68035 @27,400 (w14a105). Log: `climb-n1-ebe5387.log`.
- Forces that do not help on n1: tag pieces 1707-1716 -> r6 (best = n1 + 1682 force); old_fee spill at first dequeue
  (0.596); old_fee -> r7/r8/r9 (0.611/0.665/= n1); swept's post-sweep piece 1730 -> r9 (0.498) or r8 (0.653);
  pool_updated -> r8 (0.662, -128 B).

So the missing decision on n1 is "old_fee loses r6 to the event accounts piece". For greedy to make it without a force,
r7, r8 and r9 must all be busy across the event when %1682 is dequeued (in the original they hold the clock tag,
pool_updated and swept). Every way of filling them that was tried (swept or tag in a register, pool_updated in r8)
cascades.

## 5. Next ideas

- n1 + a 24 B repay that leaves the tail alone is worth +0.0057 if any source form spills old_fee. Look for a value the
  original keeps live in r8/r9 across the event (swept in r9) that only needs a local change. On n1 the swept force is
  catastrophic because of the sweep/wallet region, not the tail.
- Untested repay triples are listed in `results-ebe5387.jsonl` (k00-k16 were queued, but the machine stalled,
  load average > 100). They are cheap with `tools/cg.sh` + `tools/q.sh` (gene names from w14a109's `genes.py`, `@edit` for local
  edits).
- pr1 (pool_updated recomputed at the event, gate kept for the if) was written but not built.
