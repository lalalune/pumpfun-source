# w17a26-shim-assumeq: `llvm.assume` equality and range facts (notes, KILL)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 SHIM
track. Base: main 53ec7fb53 (0.68754, M 2,295, 3,096 slots, 1034/1034). Ledger: approach `assumeq`, keys
`0x22a10-w17-53ec7fb-assumeq-<item>-v1`.

**Result: notes only. The kill condition holds.** No single assume cell, no pair of assume cells, and no size-neutral
pair or triple of an assume cell with a passthrough partner reaches main's M at 27,400 B. The best at 27,400 B is
-2 M; the best off-size cell is -1 M at -8 B.

## 1. The construct

`fn assume(b:bool)` (`link_name="llvm.assume"`) is already declared on admin_cto.rs line 8 for `rcinc`, so no line and
no lib.rs change is needed. Source form, one line, condition bound first:

```rust
let c=<fact>;unsafe{assume(c)}/*shim: assume <fact> (<why it holds on every path>)*/;
```

In pre-opt IR it is `call void @llvm.assume(i1 noundef zeroext %c)`. It emits no instruction. In MIR it is an
opaque `Call` terminator, like `pt*`/`expect_p`.

## 2. Calibration (main 53ec7fb53)

| variant | slim oracle (capraw + preslim + fx) |
| --- | --- |
| m0: plain capture of the worktree | M 2,295 @27,400, ratio 0.68754, sig `61dcfe87f489`; **0 masked-token differences** from `current-baseline/unstripped.so` |
| cal1: line 761 `let c=nf==nf;unsafe{assume(c)}` | **byte-identical** (sig `61dcfe87f489`): a neutral assume and its MIR block split are free |
| hu2 (source, line 755) vs IR cell F4 (bb82) | same signature `436adad5596b`: a source assume reproduces its IR cell exactly |

## 3. Fold table (`probe/aq.rs`, `probe/probe.sh`: identity rustc, sbpf-solana-solana, opt-level 3, about 1 s)

| probe | without | with assume | effect |
| --- | --- | --- | --- |
| e0/e1 `assume(y==x)`, y reloaded after a call that may write | `ldxdw r7,[r6+8]; call; ldxdw r6,[r6+8]` | x kept in r6 across the call, reload deleted | GVN substitutes the **earlier** value (lower value number) for the later one; it extends x's live range |
| r0/r1 `assume(b<=1)` on a raw byte | `and64 r6,1; jeq r6,0` | `jeq r6,0` | known bits drop the and-1 mask |
| c0/c1 `assume(y==0)` on a reload after a call | reload + pointer kept in r6 | `mov64 r1,0`, no reload, no pointer spill | constant substitution: the only form that does not extend a live range |
| b0/b1 `assume(h.unwrap_or(false)==(h==Some(true)))` | `and64 r1,1; stxb` | **identical** | an i1 equality is canonicalised to `xor`; GVN does not substitute either side |
| n0/n1 `assume(x==x)` | | identical | a known fact is dropped by InstCombine |

Beam observations that the probe does not show:
- **Polarity flip (F4 mechanism).** An assume whose condition uses the *other* polarity of a compare (here the positive
  `holder` form, where execute only had `holder.not`) makes InstCombine re-express the existing uses through a `xor`
  and then flip the `br`: `br i1 %holder.not, %bb24, %bb30` becomes `br i1 %holder, %bb30, %bb24`. ISel then emits one
  inverted `jne` instead of `jeq +1; ja far` (-8 B). This is a size knob, not a gain (section 5).
- An assume that is false on some path is not usable even for screening; every range cell on a non-bool byte
  (bumps, `Option<bool>` tags) was either neutral or a collapse.

## 4. IR beam on main 53ec7fb (slim pre-opt oracle, about 2 s per cell)

Generators (`tools/`): `asgen.py` (kinds `eq`, `rg`, `st`, `cc`, `r64`), `semgen.py` (hand-written semantic facts),
`postkeys.py`/`rereads.py` (same-address load groups that survive as two or more loads post-opt), `polflip.py`
(llc-only polarity flips). Screens use w17a15's `screen.py` (combos with de-duplicated declarations).

| family | what | cells | identical | changed @27,400 | best @27,400 | best off-size |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| eq (nearest/earliest) | `assume(y==x)`, y a load, x a dominating load of the same type and symbolic address that post-opt keeps as a separate load (`ctx+8` excluded: `ctx` is noalias readonly) | 111 | 18 | 10 | -5 | -5 @+8 (wallet `current_creator`/`quote_token_program` reuse) |
| eq (all dominators) | the same with every dominating x (not only nearest/earliest) | 145 more | 21 | 2 | -23 | -11 @-8 (curve Box pointer at the curve store) |
| rg | `assume(b<=1)`/`<=2` on i8 loads without `!range` | 24 | 20 | 0 | - | -7 @-8 (false fact on `hopt`) |
| st | `assume(reload==stored value)` after the curve store (event reads) | 2 | 0 | 1 | -2 (`is_holder_reward` reload := stored value) | |
| cc | `assume(reload==C)` under a dominating branch on the same address | 0 | | | | (no such pair inside one pre-opt function: the re-reads live in inlined callees) |
| prg | `assume(pt8 result<=1)` on the two landed `pt8` sites | 2 | 1 | 0 | - | -4 @+48 (578 do_coin) |
| tg | parameter range facts at the execute / validate entry: `new` tag <= 1, hopt <= 2, fee tag <= 1, all three | 8 | 3 | 0 | - | -8 @-8 (fee tag); execute entry `new` tag -259 @-128, hopt -263 @-48 |
| sem | facts after validate's Ok (section 4a) | 18 | 13 | 0 | - | **-1 @-8 (F4, A26hr)** |
| pt (size partners) | w17a15 `ptgen.py` re-screened on this main | 1,009 | 726 | 62 | 0 (no gain) | -1 @+8 (execute 28792/28794), -1 @-8 (validate 27954) |
| polflip (llc only) | every `br i1` of post-opt execute inverted | 146 | 48 | 67 | 0 (validate holder br, @+8) | |

Long-range reuse cells are the worst: the mint key pointer, the sharing_config AccountInfo, the curve Box pointer and
the accounts fields across the CPIs cost 160 to 600 M each (`eqf:*:28695`, `eqn:execute:29660/29686/28930`).

### 4a. Semantic cells (inserted at the head of bb82, validate's Ok edge, unless named by arm)

| cell | fact | result |
| --- | --- | --- |
| F12 / F1 / F2 | `new` tag == !holder; holder => None; !holder => Some | identical |
| F3 | !mayhem | identical |
| **F4** | holder_reward => holder | **-1 @-8 B** (sig `436adad5596b`) |
| F5 | holder => holder_reward or holder_enabled | identical |
| F6a-d | fee Some => !quote_locked, fee_configurable, f!=0, f<=max | identical |
| F6e | fee Some => !cashback | -367 @-144 |
| F7 | fee tag <= 1 | -8 @-8 |
| F8 | hopt <= 2 | identical |
| A23tag0 / A24tag1 | holder arm tag==0 / non-holder shared arm tag==1 | identical / -309 @-48 (the sharing tag becomes a phi of constants) |
| A24hr0, A26tag | !hr in the non-holder shared arm; non-shared arm tag fact | identical |
| A26hr | holder_reward => holder in the non-shared arm | -1 @-8 B (= F4) |

### 4b. Source checks (real captures)

| variant | line | M @ bytes | note |
| --- | --- | --- | --- |
| hu2 | 755 `curve.is_holder_reward={let u=holder.unwrap_or(false);let c=u==_holder;assume(c);u}` | 2,294 @27,392 | = F4. The `and64 r2,1` at the store stays (b0/b1); only the J1 holder br flips |
| hu1 | 755 `curve.is_holder_reward=_holder` (ordinary) | 2,257 @27,416 | |
| su1 | 339 `sharing_update=Some(args.0)` in the holder arm (ordinary; `new` is None there) | 2,102 @27,208 | |

### 4c. Combinations

| set | screened | best @27,400 |
| --- | ---: | --- |
| pairs of the 25 best assume cells (dM >= -24) | 299 | -2 (`st:30334` + `eqn:30331`) |
| size-neutral pairs/triples of assume cells (incl. F4, A26hr) with pt partners, predicted dM >= -4 | 450 | -2 (F4 + pt 28792/28794 = 2,293; st:30334 + any 0 B pt) |
| llc-only pairs/triples of the 20 best polarity flips with cancelling sizes (`tools/polpair.py`) | 329 | 0 (pf1191 + pf1360: the validate holder-arm fee None br + the J1 holder br = F4's flip) |

Greedy forward selection has nothing to start from: no single is above main.

## 5. Why the family fails here

- GVN keeps the earlier value as the leader, so an equality can only lengthen an earlier live range or substitute a
  constant. In this function every lengthened range costs a register or a spill somewhere else; the RA ripple is
  larger than the one deleted load (-5 at best, -600 at worst).
- The residuals the angle aimed at are not GVN merges:
  - C1's sharing tag in main is `phi [new tag, 2, 2, 0]` (`0` from the holder arm's `Some(None)`). An assume can only
    turn the `new` tag into a constant inside an arm (A24tag1, -309); it cannot turn the holder arm's constant into
    the `new` tag. The C1 payload difference is SROA slice shape (`[1,5) [5,8) [8,16) [16,24) [24,32) [32,33)` pieces
    in the original vs aligned 8 B words in main), which facts do not touch.
  - The curve-store `and64` is `holder.unwrap_or(false)` = `hopt & 1` of the parameter byte, not a spilled cashback
    byte (+0xa5 is `is_holder_reward`; +0xa3 is `is_cashback_coin`, stored from r4 without a mask in both programs).
    `hopt` can be 2 (None), so `assume(hopt<=1)` is false. The original stores a precomputed holder bool
    ([r10-0x950], w17a23); the bool equality that would say so is dropped by InstCombine (b0/b1).
  - The account-field re-reads that the original avoids are register/spill decisions (w17a23: the original spills the
    `&creator_vault_quote_token_account` GEP at its definition), not missing value facts.
- Constant facts (`cc`) that do hold, such as anchor's `Signer`/`mut`/`Program` flags or wallet's `!executable` and
  `is_writable`, would turn `ldxb`/`stxb` flag copies into `stb` constants. The original keeps the loads (for example
  orig 0x3e90 copies the three flag bytes of a clone as one 3 B load), so these move away from it. Main already has
  more constant stack stores than the original (`stdw [r10-x],0` 92 vs 84, `stb ..,3` 11 vs 9; `ldxb` 98 vs 96,
  `stxb` 90 vs 91), so there is no constant-fold gap for `cc` cells to close.

## 6. For other lanes

- **F4 / A26hr / hu2 is a -8 B knob at -1 M** (validate's holder br in J1, `jeq+ja` -> `jne`). Source form:
  `curve.is_holder_reward={let u=holder.unwrap_or(false);let c=u==_holder;unsafe{assume(c)}/*shim: ..*/;u};` on line 755.
  It pairs with a +8 B cell that is worth at least +2 M on the same base; none exists on 53ec7fb (pt partners give -2).
- The polarity table (`data/polflip-53ec7fb.tsv`) prices every post-opt `br` flip on this main: no flip gains, pf:770
  (validate holder br) is 0 M at +8 B.
- The passthrough family is still locally exhausted on 53ec7fb (`data/pt-singles-53ec7fb.tsv`: 1,009 singles, best 0).
- `tools/asgen.py` + `tools/postkeys.py` give every same-address re-read pair that survives post-opt, with its
  dominance-checked earlier load; re-run them after each landing (the cells are base-specific).

## Tools and data

- `tools/cap.sh`, `tools/capq.sh`, `tools/mk.py`, `tools/variants.py`: source variants (line-asserted) captured into
  the slim oracle (w17a06 `capraw.py`/`preslim.py`/`fx.py`, survivor list `surv-1647da0.txt`, still exact on 53ec7fb).
- `tools/asgen.py <slim.ll> <out.jsonl> eq,rg,st,cc,r64`, `tools/semgen.py`, `tools/polflip.py <m.ll> <out.jsonl>`,
  `tools/rereads.py`, `tools/postkeys.py`, `tools/cdiff.py` (candidate-vs-candidate diff with jump targets masked),
  `tools/opdiff.py` (orig-vs-candidate difflib opcodes).
- `probe/aq.rs` + `probe/probe.sh`: the fold-table probe.
- `data/assume-singles-53ec7fb.tsv`, `data/assume-combos-53ec7fb.tsv`, `data/pt-singles-53ec7fb.tsv`,
  `data/polflip-53ec7fb.tsv`: every screened cell with dM, dB and output signature (sig `61dcfe87f489` = main).
