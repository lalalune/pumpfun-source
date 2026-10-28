# recovered from the transcript of lane create-a (create-a.md); entries in order

# create-a findings (incremental: inline Event::data first, then region-by-region alignment of 163920)
Baseline w582: 163920 ratio 0.3225, candidate 11112 B / 1323 insns (orig 13800 / 1641), + extra Event::data 648 B.


## 12:00-12:35 Event::data inlining mechanics (native remarks, -Cremark=inline; does not change codegen, sha identical)
- w582 `create`: `DonationFeePdaCreated::data` NOT inlined: cost=100 vs threshold=45 = LLVM *cold call-site* threshold
  (call site block freq < 2% of caller entry). Same reason for AccountInfo::clone (60/45), exchange_malloc (45/45),
  SpecFromIter::from_iter (495/45; would get the 15000 last-call-to-static bonus if not cold). So the whole emit!/emit_cpi!
  inline difference is ONE fact: the emit call sites must be non-cold *in the function where the inliner evaluates them*.
- Frequency model that fits all builds so far: disabled `&4` 50%, `version!=0` 62.5% taken (zero heuristic), memcmp key
  checks 62.5% to the error side, Result `?` after an inlined helper ~50% (helper's early returns MERGE at its return
  block, so they do not dilute the caller), all-inline early returns DO dilute.
- Same mechanism decides ToString-vs-Display at the 10 error sites (to_string cost 130: thr 325 non-cold / 45 cold).
  Original pattern: Display at 148,152,192,221; ToString at 156,174,197,204,213,214.
- Variants on w582 (helpers nested in `create`, emit stays in `create`):
  A pool-only helper fn: helper NOT inlined (separate 4376 B fn) + data still separate -> negative.
  B helper(reserves+curve+pool)->Result<(Pubkey,Pubkey)>: data still separate (emit freq ~1.1% cold), 11216 B.
  C = B + sharing helper fn -> data/clone/from_iter/exchange_malloc ALL inlined, 585 windows, create 13392 B/1591 insns,
    ratio 0.4889; but pool 148/152 ToString (cold inside B's helper since the 4 zero checks give pool ~2%) and 197 Display.
  D = A + sharing helper: pool helper separate -> negative.
  v1 = Codex standard-pool-require form ported to w582: 13768 B/1637, ratio 0.4887, error-site pattern == original.
- Layout insight: BPF analyzeBranch cannot analyze conditional branches, so MachineBlockPlacement pre-merges every
  conditional fallthrough and, with the many-predecessor return block, mostly falls back to the ISel/IR block order.
  => the target layout ~= original final IR block order. Tool: lanes/create-a/work/chains.py (chain summary).


## 12:40-13:05 sibling-style closure form (big step)
Pattern borrowed from the MATCHED sibling create_fee_sharing_config::create_sharing (bool `graduated` + immediately
invoked `move` closure returning Result, early `&AccountInfo` locals). Create body stays in `create` (same fn name/file).
- E1/E2/E3 (w583): `let graduated = a==0&&b==0&&c==0&&d==0;` + `(move || -> Result<(Pubkey,Pubkey)> {curve/pool; sharing; Ok((creator,quote))})()?`
  + event built from ctx keys after Clock. Event::data/clone/from_iter/exchange_malloc all inlined, 585 windows.
  E1 (no info locals) 0.5577, E2 (+ base_mint/payer/sharing `&AccountInfo` locals before graduated) 0.5610,
  E3 (= E2 with pool branch first) 0.5812. Error-site Display/ToString pattern == original in E3.
  The info locals reproduce the original's early pointer loads ([r7+872],[r7+88],[r7+272] before the reserve checks).
- E8 = E3 + `Ok((config.admin, quote_mint))` / `Ok((creator, quote_mint))` built INSIDE each sharing branch (closure tail
  = the sharing if/else): ratio 0.6052, 13768 B/1637 insns, callee multiset == original incl. 5 memcpy (41,41,236,72,41).
  E9 (graduated = !(a!=0||...)) is byte-identical to E8. E10/E11 (`has_reserves` || form) worse (0.5995/0.5795, +1 Display).
- Remaining big differences: (1) reserve checks keep an empty trampoline (`ja`) where original branches straight to curve1;
  (2) original places pool chains early/interleaved (pool1 after curve1+abort), E8 puts the whole pool path at the end
  (MBP picks hottest ready chain => original pool path must be warmer); (3) 32 B short.


## 13:25 coordination note
create-b (v04_c3m) and create-c (p3) both reached 0.7574 with the natural helper form
`get_creator_and_quote_mint(&Account<BC>,&UncheckedAccount,&InterfaceAccount<Mint>,&UncheckedAccount,&Signer)` +
`is_graduated` + deferred init. My E-series (closure, 0.6052) is superseded; my E15/E16 (`&` non-short-circuit test) are
redundant with their is_graduated fix. create-a now REBASES ON create-c p3 and takes the regions the other two did not
list: (1) curve tail / quote-default / creator merge chain (orig 1704-2360 n=76 vs p3 n=83; curve2 n=10 vs 9),
(2) post-Clock event + state-write ordering (orig 3048-4000 n=120 vs 121) and emit chains, (3) pool 148a/148b error
chain placement (p3 puts them before the write path; orig after pool-deserialized 4784). I will NOT work on the pool
deserialize OK/Err dispatch (create-b/create-c both listed it) unless they report it done.

- 13:45 on p3 (create-c): q1 `quote_mint = if quote == default {..} else {quote};` (drop the `let quote=if..; quote_mint=quote` hop):
  byte-identical to p3 (0.7574) -> NOT the cause of the extra curve-tail copy.
  **q2: write `pda.creator=creator;` BEFORE `pda.quote_mint=quote_mint;` -> 0.7671 (span 600->576)**; the state-write
  block (orig 3048-4000) is now structurally identical to the original except register allocation (orig keeps
  creator[7..15] in r8 and uses r6=r7+640; q2 spills it). Spec: lanes/create-a/work/pv/q2.py (line 247/248 swap of p3).

- **14:00 r2 = 0.8351 (span 336, 13800->1640 insns vs orig 1641), ALL 47 MBP chains now in the ORIGINAL ORDER**
  (chaindiff: cand chain order == orig chain order 0..46; pool deser dispatch `ja ->4784` + pool-deserialized chain,
  148a/148b after it, all in place). Source = p3 (create-c) + two edits:
    (a) write `pda.creator=creator;` before `pda.quote_mint=quote_mint;` (q2),
    (b) curve arm: `let quote = crate::common::curve_quote_mint(&curve.to_account_info())?; creator = curve.creator;`
        then `if quote == Pubkey::default() { quote_mint = native_mint::ID; } else { quote_mint = quote; }`
        (branch-local deferred assignments, creator BEFORE the default test). r1 (same but creator after) = 0.7690,
        r3 (`quote_mint = match ..`) = 0.7671, q1 (`quote_mint = if ..`) == p3.
  Full file: lanes/create-a/src-r2/programs/pump-fees/src/instructions/fee_sharing/create_donation_fee_pda.rs (w583 tree).
  Remaining: in-chain diffs (curve read/quote chains 1160-2360 split 78/66 vs 68/76, sharing deser-err 9464 n=6 vs 2,
  sharing success 13320 n=28 vs 32, 11560/11936 chains, register allocation).

- 14:20 rebased on create-c-n01 (s0 reproduces 0.9287). My curve-arm edits on top of n01 are NEGATIVE:
  s1 (r2 arm) 0.9111, s2 (branch-local only) 0.9281, s3 (creator before test only) 0.9117. Keep n01's curve arm.
- Frame-layout residual (n01): pool success writes coin_creator -> -768 (helper's `creator.i` alloca, colored into the
  big -768 union slot) and quote_mint -> -96 (create's `quote_mint` alloca); original: creator -96, quote -128, i.e. the
  original keeps a separate 32-B creator object right above quote (FI order creator,quote near the frame top), and a
  separate 16-B pool-deserialize slice at -784 (n01 colors pool slice `_34.i` with sharing slice `_160.i` at -64).
  Working on it with -print-after=stack-coloring/prologepilog (frame object names) to see exactly which allocas merge.