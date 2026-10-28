# recovered from the transcript of lane create-c (create-c.md); entries in order

# create-c findings (sibling-analogy strategy for 163920 CreateDonationFeePda)
Baseline w582: 163920 ratio 0.3225, candidate 11112 B / 1323 insns (orig 13800 / 1641), + extra Event::data 648 B.


## 12:20 KEY MECHANISM (BFI cold-callsite) + v1 result
- LLVM inliner (no profile) treats a call site as COLD when its block freq < 2% of the caller's entry (BFI computed
  BEFORE the caller's inline batch; inlined callee blocks are scaled, original blocks keep pre-inline freq). Cold sites get
  threshold 45 (no bonuses) instead of 250/325. Writing all validation inline in `create` (w582) makes the emission and the
  pool error sites cold -> Event::data, Vec::from_iter, AccountInfo::clone, exchange_malloc and the pool to_string are NOT
  inlined. Original pattern (Display inlined = warm): L148,L152 (pool), L192 (sharing owner), L221 (payer==creator);
  ToString outlined (cold): L156,L174,L197,L204,L213,L214. Model with zero-heuristic (x!=0 likely 62.5%): pool entry
  P must be in [0.34,0.91) and the creator/sharing merge freq M in [0.085,0.285) relative to the function that owns the
  require! sites -> validation lives in a separate function/closure whose curve/pool split is ~50/50 (bool / folded
  test) and whose curve path has one `?` (curve_quote_mint) before the merge; emission stays in the handler
  (handler path: disabled 0.375 * exists 0.375 * closure? 0.5 * Clock? 0.375 = 2.6% -> warm, data() inlined).
- v1 = sibling form of create_sharing: `let graduated = 4 reserve tests; let accounts=&*ctx.accounts;
  let (creator, quote_mint) = (move || -> Result<(Pubkey,Pubkey)> { curve/pool; sharing/else -> Ok((..)) })()?;`
  then state writes + event + emit!/emit_cpi! in `create`. RESULT: 13752 B / 1635 insns, ratio 0.5824 (w582 0.3225,
  Codex continue13 port 0.4887), 585 candidate windows (extra Event::data GONE), call multiset == original exactly,
  Display/ToString per line == original. No normalized loss (578 native).
- Residual: reserves test layout (original = 4 consecutive tests, curve fallthrough, no bool trampolines; suggests
  the tests were folded to one `or` branch = curve ptr dereferenceable, i.e. a function PARAMETER), and the original
  loads sharing_config/base_mint/payer AccountInfo ptrs up-front (call-site args), not at use sites.


## 12:45-13:20 helper-fn experiments on w583 (farm1; all: 579 native, lost [], 585 windows, extra Event::data gone)
- BACKEND FACT: SBF/BPF `BPFInstrInfo::analyzeBranch` returns "cannot analyze" for ANY conditional branch, so
  MachineBlockPlacement pre-merges every cond-branch block with its layout successor and BranchFolding cannot remove
  `ja` trampolines. => final block order ~= LLVM IR block order (MBP only reorders whole chains by frequency).
  The original's layout is thus a fingerprint of IR block order + BPI only at chain boundaries.
- v2 helper fn(&Account<BC>, &AccountInfo x4) 0.6025; v4 helper fn with WRAPPER params (&UncheckedAccount,
  &InterfaceAccount<Mint>, &UncheckedAccount, &Signer) 0.6086 (argpromotion loads the wrapper ptrs at the call site =
  original's up-front [r7+872]/[r7+88]/[r7+272] loads; key ptrs stay at use sites like the original).
- Reserve-test forms (inside helper): inline `if a!=0||..` / `if a==0&&..` / `if !(..)` -> all 4 tests fold to one
  select chain (pool warm, exact pattern) BUT pool arm first in IR (pool = fallthrough of test4, orig = curve).
  `let graduated = ..; if/match graduated` (v6,r2,r4,r5,r6,r10) -> 4th test NOT folded (lifetime marker in its block)
  -> zero heuristic makes pool cold: pattern 152C/197W (wrong) though layout curve-first (0.6788-0.6989).
  r3 `let has_liquidity = ||` 0.6436 (wrong pattern).
- FIX: predicate fn `fn is_graduated(curve: &BondingCurve) -> bool { 4 x ==0 && }` (dereferenceable param -> folds
  inside) and `if is_graduated(curve) {pool} else {curve}` (r7) or `if !is_graduated(curve)` (r8): EXACT original test
  chain (3x jne ->curve, jeq ->pool@416, pool path starts at 416 as in the original) + exact warm/cold pattern. 0.6159
  (extra 64-byte pair copy at the merge: tuple temp + destructure).
- Pair forms: p2 `let pair = if..; pair.0/pair.1` 0.7363; p4 same + Ok((pair.0,pair.1)) 0.7373;
  p1 deferred init `let creator; let quote_mint; if !is_graduated {..} else {..}` 0.7373;
  **p3 deferred init + `if is_graduated(curve) { pool } else { curve }` 0.7574 / span 600 (best so far)**.


## 13:40 BIG STEP — create-c-n01 harvested (ratio 0.9287, span 118, 1641/1641 insns) — create-a/b: rebase on it
Source: R/shared/harvest/create-c-n01/src (overlay of w583) ; generator lanes/create-c/gen/gen4.py (options).
- s1 = p3 + `return Ok((config.admin, quote_mint));` (explicit return inside the sharing `bytes` scope) -> 0.9177 / span 146.
  (s3 = rebinding `let creator = if .. {config.admin} else {creator}; Ok((creator, quote_mint))` -> 0.7602, worse.)
  Mechanism: the explicit return joins the return drop-tree, so sharing success + errors share one Ref drop + flag
  dispatch (orig 12304/12312: `jne r1,0,->3240`); tail-expression Ok got its own scope-exit drop and was jump-threaded.
- t1 = s1 + L213 `require!(payer.key() == config.admin, ..)` (orig memcmp(payer_copy -512, &config.admin -712): payer first)
  + `pda.creator=creator;` before `pda.quote_mint=quote_mint;` -> 0.9287 / span 118. (t3 only writes-order 0.9275,
  t2 only payer-first 0.9190.) decl order / curve assign order: no effect; pool assign order quote-first: worse (0.9025).
- Verified the 2 remaining call-name diffs are fndiff equal-body naming noise (orig targets 783752 = 2nd of
  start/end/order 8-B trampolines = slice_end_index_len_fail; 767672 = 2nd 152-B = panic_already_mutably_borrowed,
  same as the candidate). Program IDs: t1 uses public statics crate::pump_amm::ID / crate::pump::ID (original's).
- RESIDUAL = frame layout + 1 schedule: orig `creator` slot r10-96 (t1 -768 => +32 shift for [-576,-96], +16 for
  [-1456,-784]); Pool deser input slice orig -784 (t1 -64); orig early loads order 872,88,272 (t1 272 first).


## 14:00 0.9976 / span 5 — only the early-load order remains
- f-tuple = t1 with `let (creator, quote_mint) = if is_graduated(curve) { ..; (pool.coin_creator, pool.quote_mint) }
  else { ..; (curve.creator, quote) };` (tuple temp is SROA-split into creator/quote slots placed right after the top
  64-B slot = original frame order [64B][creator -96][quote -128]) -> 0.9775 / span 38 (f-tupleassign identical;
  `let pair` forms 0.92-0.93).
- pd-letslice = f-tuple + pool deserialize via a NAMED slice: `let data=info.try_borrow_data()?; let mut slice: &[u8] =
  &data; let pool=Pool::try_deserialize(&mut slice)?;` (identical binaries: `let mut slice = &data[..]` and Anchor-style
  `let mut data: &[u8] = &info.try_borrow_data()?;`) -> 0.9976 / span 5. The original keeps the Pool input slice in its
  own slot (-784) while the SharingConfig one stays a short temp merged into the top slot (-64): they were written
  differently. `&mut &**data` / `&mut data.as_ref()` = same as `&mut &data[..]` (0.9775).
- Remaining (raw diff): only `ldxdw r9,[r7+272]` scheduled first (orig: [r7+872],[r7+88],[r7+272]); everything else is
  lddw pointer values (masked) and equal-body call naming.


## 14:10 WINDOW 163920 CLOSED NATIVELY — harvested create-c-g01 (580 native, gained [163920], lost [])
- pp3 = pd-letslice + helper param order (curve, pool, payer, base_mint, sharing_config): early loads now
  [r7+872],[r7+88],[r7+272] like the original -> measure gained [163920], lost [], 585 windows (Event::data gone).
  fndiff 0.9982/span 3 = display-only (2 equal-body call names verified as the original's group members + native rodata
  preview of the __event_authority seed pointer). Param-order sweep: pp1 (sharing,base,payer) 0.9970, pp2 (base,payer,
  sharing) 0.9976, pp4 (payer,sharing,base) 0.9976, pp5 (sharing,payer,base) 0.9970, pp6 (pool last) 0.9970,
  pp7 (pool first) 0.9976, pp8 (base,pool,..) 0.9976; pp3 (payer,base,sharing after pool) = exact.
- create-b-g01 (same minute) = BYTE-IDENTICAL native ELF (sha 31fe7777...) from param order (curve,payer,base_mint,pool,
  sharing_config) + Anchor-style `let mut data: &[u8] = &info.try_borrow_data()?;`. Equivalent packets.


## 13:00 PIVOT to CRANK 147944 (per DIRECTIVES 12:56)
Taking: IR-level (llc loop, crank-c tools) probes of WHY greedy RA keeps the rent AccountInfo ptr in r6 / heap ptr in r8 in
the original vs crank-b v08 (heap r6, rent reloaded per use): block-frequency / use-position / live-range-shape hypotheses,
to hand crank-b a concrete IR delta to map back to source. Not duplicating crank-b's source batches (v09/v10).