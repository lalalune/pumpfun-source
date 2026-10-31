# w14a27-cto-hvatalit: the sweep token arm's create_idempotent (holder vault ATA, line 719)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: per-account AccountInfo form / field-order screen for the one CPI no lane had touched, the sweep token arm's
`anchor_spl::associated_token::create_idempotent` into `holder_creator_vault_quote_token_account` (line 719).
Bases: main 7e6aa9c (0.6414), e87e001 (0.64709), 6db95a7 (0.65458). Ledger: approach `hvatalit`,
keys `0x22a10-w14-<main7>-hvatalit-<screen>-<variant>-v1` (about 290 rows).
Oracle: w14a23's raw-IR capture (`capvar.sh` -> `capraw.py`) + `rx.py` (opt -O3 + llc), with a call counter added.
On 7e6aa9c it reproduces main's ratio (0.6414 / 3,173 slots), and `eq_main` is true on e87e001 and 6db95a7.

## Result

- **Lead found: b9.** In the token arm, `transfer_vault_tokens(..)?;return Ok(amount);` inside `else if amount>0`
  (in place of falling through to the trailing `Ok(amount)`). On 7e6aa9c: 0.6414 -> 0.6434 at 27,408 B. With the
  `if let Some(f)=fee{curve.creator_fee_bps=f;}` repay it measured **0.6432 at 27,400 B, 1034/1034, zero losses,
  differential 363/0**, but main moved before I could land it (#3287 landed the same repay knob). On e87e001, b9
  was 0.64879 at 27,408 B; with the repay `nf`-drop + `wl_ts_clockvar` it measured **0.64919 at 27,400 B, zero losses**.
  Before I could land that, **w14a33-cto-nativejoin landed b9 (credited) inside #3315** (6db95a7, 0.65458).
  On the current main the lead is spent.
- **The per-account form angle is dead by inspection.** Every account in this CPI is already one out-of-line
  `AccountInfo::clone` call per field, in the original's order and at the original's offsets (program +0x28, payer +0x0,
  ATA +0x50, authority spill, mint +0x18->+0x58, system +0x30, token program +0x20, then the 0x120 memcpy). This is
  the same finding as w14a24 for the wallet CPIs. Literal and override forms inline the Rc clone, so they change the
  call count and add 256-680 B.

## 1. Map (orig 0x5e70-0x60f8 vs main 7e6aa9c 0x5e68-0x60f0)

Instruction for instruction, the tokens of the clone run are the same. The differences are register and slot choices:

| | original | main 7e6aa9c | b9 / main 6db95a7 |
| --- | --- | --- | --- |
| accounts pointer | r7 from [r10-0x8d8] | r9 from [r10-0x8e0] | r7 from [r10-0x8e0] |
| Create dest (r10-0x450) | r9, kept across calls | spilled to [r10-0x900] | r9 |
| &holder_creator_vault | [r10-0x8e0] | [r10-0x9b8] | [r10-0x9b8] |
| amount | r6 | r8 | r8 |
| TVT Ok exit | threaded past the swept tag test (orig 0x60d8 -> 0x3c68) | Ok/Err both to the shared join, which tests `jne r7,2` | same as main |

Cause: in 7e6aa9c the zero path and the TVT Ok exit both reach a block that tests `r7` (the constant tag 2). That keeps
r7 live across the whole create path, so the accounts pointer gets r9 and the dest pointer is spilled.
`return Ok(amount)` after TVT routes the Ok exit to the sweep's return, not to that block. That frees r7, and RA then
picks the original's r7/r9 for the clone run.

Splice bounds (byte-splice what-ifs, `tools/splice.py`): on 7e6aa9c the create block [0x5e70,0x60f8) is worth +0.0081
and the clone run alone +0.0036. On 6db95a7 the clone run is worth **+0.0006** and the whole block +0.0048. What
remains is the amount register (r6 vs r8), the 0x950/0x8e8 phi spill slots and the TVT Ok threading, all owned by
the swept-join / frame lanes (w14a06, w14a33).

## 2. Screens (raw-IR oracle)

| screen | base | variants | best | note |
| --- | --- | ---: | --- | --- |
| s1 per-account forms | 7e6aa9c | 56 | = main | 7 accounts x {C `let x;x.clone()`, cl `AccountInfo::clone(..)`, Kc/Oc/KOc/Rc `{key:x.key,..x.clone()}` overrides, KLDORSWE literal, aKLDORSWE read-through}. C and cl give main's tokens. Overrides cost +240..+304 B (0.34-0.38). Literals cost +384..+680 B and 156-162 calls (orig 157). |
| s2 token arm shapes | 7e6aa9c | 10 | **b8/b9 0.6434 @27,408** | b1 `.map(\|()\|amount)` 0.64031 @27,416, b2 and_then 0.63981, b6 `require!(!frozen)` in `amount>0` 0.62172, polarity / `!=` / `==0{}else` give main's tokens |
| s3 around b9 | 7e6aa9c | 9 | c5/c9 = b9 | native `?`/return forms 0.36 (+64..96 B). Frozen-arm `return Ok` forms 0.642 @27,448 |
| k1 catalog knobs on b9 | 7e6aa9c | 67 | none at 27,400 above b9 | |
| k2 new knobs on b9 | 7e6aa9c | 17 | **t1 fee if-let 0.6432 @27,400** (built: zero losses, diff 363/0) | `t5_nonf` 0.64189 @27,384 |
| r2 b9 re-check | e87e001 | 6 | b9 0.64879 @27,408 | |
| k3 knobs on b9 | e87e001 | 98 | ev_hr_curve / fee match 0.64829 @27,400 (built: zero losses) | `t5_nonf` 0.64969 @27,384 |
| p2 knob pairs on b9 | e87e001 | 16 | **nf + wl_ts_clockvar 0.64919 @27,400** (built: zero losses) | |
| s4 token arm shapes | 6db95a7 | 10 | = main | d4 `create.and_then(\|()\|TVT)?;return Ok(amount)` 0.65408 @27,368. Result<()> join forms (w14a33's native form, applied to the token arm) 0.6495-0.6506 |
| k4 knobs on d4 | 6db95a7 | 92 | **d4 + `s_frozen_first` 0.65528 @27,392** (above main, 8 B short) | `s_frozen_first`: `let frozen=token_frozen(..)?;` before `let amount=token_raw_amount(..)?;`. t41 fee match 0.65447 @27,360 |
| p3 +8 B repays on d4+ff | 6db95a7 | 6 | ff+ev_cb_local 0.65428 @27,400 (main 0.65458) | ff+cb+sh_fees_key 0.65389, ff+cb+destrev 0.65368, ff+cu_replace 0.65249, ff+fee match+wl clock 0.65309. All have 3,194 slots (main 3,279), but the ratio is lower |

Open lead for the next lane: **d4 + s_frozen_first is 0.65528 at 27,392 B on 6db95a7**. It needs a +8 B repay that
does not cost ratio. The +8 knobs in the catalogs (ev_cb_local, cu_replace) lose 0.001-0.003 on it.

## Tools (scratch copies under `~/.cache/pumpfun-reconstruction/lanes/w14a27-cto-hvatalit/tools/`)

`gen.py` (per-account forms at the last `create_idempotent`), `genarm*.py` (token-arm shapes), `genknob.py` (every
knobs13 + sizeknobs-cto.json knob on a base edit), `genknob2.py` + `newknobs.py` (lane knobs), `splice.py` (byte-splice
bound), `odis.sh` (oracle object -> function-relative listing), `rec.py` (bulk ledger record).
