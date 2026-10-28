# recovered from the transcript of lane create-b (create-b.md); entries in order

# create-b findings (163920 create_donation_fee_pda::create, re-derive from original)

## Original structure (from R/base/evidence/original/pump_fees/deployed.so @163920)
- emit!/emit_cpi! are fully inlined in the original: two inline bump allocations of 256 B (event data written with
  fixed offsets: disc 0xebe14d23ef89145e, ts@8, created_by@16, donation_fee_pda@48, config_id@80, base_mint@112,
  quote@144, creator@176, len 208), sol_log_data, inline AccountInfo clone of event_authority (Rc++ x2), 216-byte
  ix_data alloc + byte loop (collect of EVENT_IX_TAG_LE chain data), 34-byte AccountMeta alloc, new_with_bytes, invoke_signed.
- Event fields in the original come from ACCOUNT keys (payer [r7+272], donation_fee_pda info [r7+632], config_id [r7+856],
  base_mint [r7+88]), not from the written pda fields. quote/creator from the resolved pair.
- State is written BEFORE Clock::get (bump, version=1, config_id, base_mint, creator, quote, reserved=0, total/last=0).
- (creator, quote) flows through a tagged Result<(Pubkey,Pubkey), Error> (72 B: tag@0, Ok@1..65, Err@8..24):
  SROA pieces [1,8) [8,16) [16,24) [24,65) -> the 41-byte memcpys (-512 -> -920 in each arm, -920 -> -968 after merge).
- Why data() is inlined in the original but not in w582: in w582 the emit call sites are in `create` behind ~6 static
  37.5% branches (zero heuristic on memcmp/version/Clock tag) => block freq ~1.6% < 2% => cold callsite (threshold 45,
  no bonuses). In the original the emit block must have been >=2% when the inliner visited the function containing it
  => the creator/quote resolution (with its branches) was in a separate (later-inlined) function.

## Experiments

Scores below: score.py ratio = fndiff masked SequenceMatcher ratio for 163920 (w582 baseline 0.3225, Codex best
donation578-continue13-standard-pool-require measured with the same tool 0.4887). All builds keep 578 native normalized.
- v01_helper: split curve/pool/sharing resolution into `fn creator_and_quote_mint(ctx:&Context<..>) -> Result<(Pubkey,Pubkey)>`
  (error lines unchanged), `create` = checks + `let (creator, quote_mint) = helper(&ctx)?` + state + event(account keys) + emit.
  => DonationFeePdaCreated::data helper DISAPPEARS (inlined), 13512 B/1606 insns, ratio 0.5611. measure: 578 native, lost=[].
- v02_params (helper takes &AccountInfo derefs at call site): 13888 B, 0.6025; hoists AccountInfo ptr loads (good) but also
  key ptr loads (orig does not).
- v03 (helper(&Context) + explicit `let x:&AccountInfo=&ctx.accounts.x` locals): 0.5921.
- v04_wrapperparams (helper(curve:&Account<BondingCurve>, pool:&UncheckedAccount, base_mint:&InterfaceAccount<Mint>,
  sharing_config:&UncheckedAccount, payer:&Signer)): 0.6086; hoists exactly the 3 AccountInfo ptr loads like the original.
- v05 (helper(accounts:&CreateDonationFeePda)): 0.6567 but no hoisting. v06 (#[inline(always)] v02): 0.6603.
- Reserve-check layout (SBF analyzeBranch cannot analyze conditional branches => cond fallthroughs are fixed by IR block
  order; MachineBlockPlacement only orders chains, by frequency). Original: check4 falls into curve-head, abort, then
  POOL head (=> pool freq >= curve freq, i.e. 4 checks merged into one 50/50 select condition) and curve continuation later.
  `if a!=0||..{curve}else{pool}` and `if a==0&&..{pool}` / `!(..)` variants (c1,c2,c4) give identical code (pool first in IR).
  `let use_pool = a==0&&..; let (creator,quote_mint) = if use_pool {pool} else {curve}` (c3, pool code first, lines kept):
  curve-head after check4 (good) but last && operand stays a separate ZH branch (lifetime.start of the tuple temp on the
  threaded edges blocks FoldBranchToCommonDest) => curve cont after abort. 0.6989.
- v04_c3m: `let creator; let quote_mint; let use_pool = a==0&&b==0&&c==0&&d==0; if use_pool {...; creator=pool.coin_creator;
  quote_mint=pool.quote_mint;} else {...; creator=curve.creator; quote_mint=quote;}` => all 4 checks merged, pool head after
  abort exactly like the original. 13824 B/1644 insns, ratio 0.7574 (best so far).

- m4 (v04_c3m + struct-order params + `creator = curve.creator; quote_mint = if ..` same line): 0.8210, IDENTICAL callee
  order to the original, 585 windows. Harvested as near-miss create-b-n01 (w582).

## 12:55 CREATE 163920 NORMALIZED MATCH (native) — harvested create-b-g01 (w583)
Rebased on create-c-n01 (w583, 0.9287/span 118). farm1/farm2 under lanes/create-b:
- d1 = n01 + helper params in accounts-struct order (payer, base_mint, bonding_curve, pool, sharing_config): 0.9293/116.
  (load order [r7+872],[r7+88],[r7+272] + registers now == original.)
- e3 = d1 + tuple form `let (creator, quote_mint) = if is_graduated(curve) {..(pool.coin_creator, pool.quote_mint)} else
  {..(curve.creator, quote)};` : 0.9781/span 36 — LLVM SROA splits the 64-B pair => creator slot r10-96 next to quote -128
  (original frame). e1 (`let pair=..; let (c,q)=pair`) 0.9271, e2 (pair.0/pair.1 + Ok(pair)) 0.9225, e4 0.9264: worse.
- f1 = e3 + `let mut data: &[u8] = &info.try_borrow_data()?; let pool=Pool::try_deserialize(&mut data)?;` :
  0.9982/span 3 (naming/preview noise only), measure: normalized 580, gained [163920], lost []. f2 (`let data=..?;
  let mut slice:&[u8]=&data;`) byte-identical. f3 (`&mut data.as_ref()`) / f4 (`&mut &**data`) = e3 (0.9781).
  Mechanism: the named slice local spans the pool arm => not stack-colored into the -64 slot => own slot at -784.
Next for create-b: robustness (Linux recipe is the coordinator's), then help Crank 147944 if Create is confirmed.