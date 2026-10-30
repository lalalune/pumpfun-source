# admin_cto: earlier argument copy and event flags

The borrowed `new` tuple is bound before the function-scope `CtoState` literal.
Both operations read plain values without side effects. The event reads the
holder and cashback flags from the local variables that were stored into the
curve earlier in the instruction. There is no intervening curve-field mutation
or reload, so the emitted values are unchanged. All 24 macro sites retain their
original line numbers.

## Verified measurements

The reviewed branch includes main `4d529362b74a2051a5a164b7e251cb90eb9cccf5`,
whose full Pump source inventory matches the verified #2921 build:
`acc7d171b7b95e86658ed1403884b354746028559b267e0ed9bf3d0cda57393e`.
A fresh identity build produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.50929 | 0.51228 |
| Differing normalized 8-byte slots | 3,325 | 3,334 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The sequence ratio improves while the positional mismatch count increases.
The official 1,035-window inventory has no missing or resized windows and no
lost raw or normalized matches. This partial-window change does not increase
the matched-window completion percentage or establish whole-ELF identity.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `6ec93b9004c2374f087c98d93a6d5bc3c211ef133999b84a0e995b8b080a3761`.
Unstripped ELF: `89dc0ae69faf3fd63f2691b76f35a6bcfe144988598454eff1bc0dc3a8fe088c`.
Runtime ELF: `2b3bc21e534a0180f6cb838c9cb087b4c7eda4a51da7a1f4d66c4bf613084853`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.

## Lane notes (w13a13-cto-region1of3, continued)

Angle: region 1 of 3 of the ORIGINAL window (orig +0x0000..+0x23ad: prologue, holder_key/shared/quote_locked,
CtoState, validate, prepare_bonding_curve, the 410 `require!`, first sweep blocks). Ledger keys
`0x22a10-w13-<sha7>-region1-*-v1` (about 90 rows).

Oracle (kept in `~/.cache/pumpfun-reconstruction/lanes/w13a13-cto-region1of3/tools/regcon.py`): recomputes
target_metric's admin_cto difflib ratio and splits the matched tokens by the original instruction's third of the
window (shares sum to the ratio); `--frame/--regs/--jumps` mask r10 offsets, registers, jump offsets.

| build | bytes | ratio | R1 /1085 | R2 /1137 | R3 /1117 |
| --- | ---: | ---: | ---: | ---: | ---: |
| main 9eb6c00 | 27,400 | 0.49131 | 532 | 377 | 731 |
| #2921 (pfclimb-3) | 27,400 | 0.50929 | 512 | 493 | 695 |
| #2927 (this lane) | 27,400 | 0.51228 | 516 | 505 | 689 |
| #2933 (stitch-5) | 27,400 | 0.51348 | 516 | 505 | 693 |

Every gain since 9eb6c00 is in region 2 (sweep CPI frame/regalloc); region 1 got worse (532 -> 516).

### Region-1 findings

- `hk_after_shared` (#2921) moves the 45-instruction `shared` block ahead of the holder_key PDA, against the
  original's order (the PDA is the original's first call). Restoring PDA-first gives R1 +24 and R3 +12 tokens but
  R2 -50 (the transfer_creator_fees_to_pump_v2 CPI register allocation) and +32 B: every size-compensated form
  loses (0.50839-0.50943). Declaration order (`let shared;` deferred) is irrelevant; only evaluation order matters.
- The entry copy `args=&(new,)` is best right before the CtoState literal: between shared and the PDA 0.48517,
  after the PDA 0.48847, after mint 0.42497, first statement 0.41571 (on #2933).
- `CtoState` sits at -0x688..-0x65b since the function-scope hoist (orig -0x38..-0xb, main 9eb6c00 too); the top
  slot now hosts the inlined to_string temporaries (orig -0x4b8). `let st;` deferred init, `let st=&CtoState{..}` and
  `let st=&st` are byte-identical.
- `let holder=matches!(holder,Some(true))` gives the original's `and64 rX,1` holder test and improves the masked
  region-1 structure (672 -> 695/699) but is -256 B and 0.46418; repaying with validate reading `args.0` (+224 B)
  only reaches 0.45024.
- `validate(..,holder_key:Pubkey,..)` (the original's holder_key copy at -0x518) is 0.47872-0.47992 alone, 0.47786
  with PDA-first.
- Byte-identical spellings: `let cashback=if holder{false}else{st.cashback}`, `args=&(fee,new)`, `args=&Some(new)`,
  `require!(0==creator_fee,..)`.

### Single-gene deltas (size companions) on #2927 and #2933

| gene | on #2927 | on #2933 |
| --- | --- | --- |
| holder_key PDA first | +32, 0.50808 | +32, 0.50898 |
| `st.cashback&&!holder` | +8, 0.51191 | +8, 0.51310 |
| `let rent=&Rent::get()?` | -16, 0.51094 | -16, 0.51214 |
| `let sk=a.sharing_config.key()` before validate | +24, 0.51056 | +24, 0.51175 |
| event `is_holder_reward` from curve | 0, 0.51049 | -8, 0.51356 |
| event `is_cashback_coin` from curve | -8, 0.51356 | |
| `reset` inline | +8, 0.51221 | |
| collect_old operands swapped | | -24 (27,376), 0.39916 |
| validate holder_key by value | -32, 0.47872 | -32, 0.47992 |

Zero-sum pairs at 27,400 (none beats #2933's 0.51348): cashback-curve+cbrev 0.51288 (3,274 slots),
sk+rent+cashback-curve 0.51168 (3,238 slots, fewest seen), cbrev+reset+rent 0.51019, hk+rent+hr-curve+reset-local 0.50839.
