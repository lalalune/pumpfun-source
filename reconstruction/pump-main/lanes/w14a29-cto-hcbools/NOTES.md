# w14a29-cto-hcbools: holder/cashback as two bools across the sharing CPI (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a13-cto-sharingslots (#3257, #3285), first next idea: materialize holder and cashback as two independent
bools before the sharing CPI, so that 9 spilled intervals (not 10) cross the CPI and the accounts pointer moves back to colour 178.
Ledger approach `hcbools`, keys `0x22a10-w14-d2d1875-hcbools-*` and `0x22a10-w14-b2e90aa-hcbools-*`.

## Result

No gain. A spelling reaches 9 crossing intervals in four cases: cashback carried through the shared-tree arms,
cashback computed after `validate`, cashback passed into `validate`, or holder as `hopt.unwrap_or(false)`. The last
one also puts the accounts pointer back on colour 178. Every one of them reassigns the colours of the other argument
spills, and loses 0.05 to 0.18 ratio. Each spelling that keeps the main ratio folds back to main's IR.

## Mechanism (new findings)

- **Store labels.** The original stores `is_holder_reward` (curve +0xa5) from `[r10-0x950]` with no mask, and
  `is_cashback_coin` (+0xa3) from `[r10-0x958]` followed by `and 1`. So 0x950 is holder and 0x958 is cashback.
  The w14a13 note had the two labels swapped. Holder is an i8 phi of constants (1 at 0x23b38, 0 at 0x23848, r6 in the shared
  arms). Cashback is an i1 phi: `[curve.is_cashback_coin != 0]` is materialized at orig +0xd78, after the
  `t==sharing||t==holder_key` memcmp (validate line 314), and set to 0 in the holder arm. Only its zext (`and 1`) sinks to the store.
- **Why ours has 3 intervals for these two bools.** Post-opt IR computes `cashback = and i1 (cbyte!=0), !holder` once, in
  the entry block. ISel turns both i1 operands into PHI vregs. **MachineSink** then sinks `%14 = AND_rr %473,%472`
  and `%61 = AND_ri %14,1` from the entry into the curve-store block bb38 (checked with `-stop-before/after=machine-sink`).
  This leaves both operands live through the whole function (SS#184 w=1.5 and SS#185 w=1.09). Holder at the store is
  `icmp ne (holder & -3), 0`, sunk to its use by CodeGenPrepare, so its interval is the holder **argument** spill from
  slot 48 (SS#183 w=2.46). That heaviest interval takes colour 178, which pushes the accounts pointer to 179.
  The original's holder argument spill is a short interval at 0x918 (colour 186).
- `-disable-machine-sink` (oracle only) gives 9 crossings, with fee value on 189 and ctx on 190 as in the original, but
  0.52147 at 27,288 B, because sinking is global.

## Colour map per spelling (`tools/trial.sh`: raw-IR capture, rx opt/llc oracle, debug-llc stack-slot-coloring at the sharing CPI call)

Main b2e90aa (0.6444). Colour c sits at `r10-(0x8d0+8*(c-177))`. hArg = holder argument spill, hc = holder/cashback piece,
acct = accounts pointer (21+ sites), shTag = sharing tag, sw = swept. Labels are heuristic (first def and site count).

| spelling | bytes | ratio | n | crossing intervals (label:colour) |
| --- | ---: | ---: | ---: | --- |
| original | 27,400 | 1 | 8 | acct:178 feeT:180 sret:181 shTag:182 feeV:189 ctx:190 hold:192 cb:193 |
| main | 27,400 | 0.6444 | 10 | hArg:178 acct:179 shTag:180 sret:181 hc:182 hc:184 feeT:185 feeV:188 ctx:189 sw:196 |
| `st.cashback&!holder`, `!holder&st.cashback`, `match hopt{Some(true)=>false,_=>..}`, `if holder{false}else{..}`, `holder^true`, `st.cashback>holder` | 27,400 | = main | 10 | identical bytes |
| `st.cashback&&hopt!=Some(true)` (d2d1875) | 27,408 | 0.63951 | 10 | |
| n_e: cashback through the shared arms `(..,false)/(..,st.cashback)/(..,cashback)` | 27,296 | 0.5385 | 9 | hArg:178 acct:179 shTag:180 sret:181 cb:182 feeT:183 feeV:188 ctx:189 sw:195 |
| n_e, same on d2d1875 | 27,344 | 0.60429 (main 0.6417) | 9 | |
| n_e + holder in the arms too (`true/false/holder`) | = n_e | | 9 | folds back to holder |
| n_e6: n_e + holder-first curve stores | 27,296 | 0.53579 | 9 | = n_e |
| n_e2/e3/e5: no pre-computation, non-shared arm `!holder&&st.cashback` (3 spellings) | 27,312 | 0.56024 | 9 | sret:179 cb:180 hArg:182 .. feeT:184 feeV:186 ctx:187 |
| n_cbpost: `let cashback=..` after `validate()?` | 27,232 | 0.56228 | 9 | shTag:178 sret:179 acct:180 hArg:181 cb:182 feeT:184 feeV:186 ctx:187 |
| n_cbpost + holder-first stores | 27,232 | 0.56108 | 9 | |
| n_cbpost with `st.cashback&!holder` | 27,152 | 0.59443 | 10 | |
| p_c3: cashback in the block's result tuple / after the arms | 27,144 | 0.51927 | 9 | |
| q1/q2/q3: `validate(..,cashback:bool)` uses the caller's cashback at 330 (line 314 dropped) | 27,376 | 0.5239 | 9 | hArg:178 acct:179 shTag:180 sret:181 cb:182 feeT:184 feeV:187 ctx:188 |
| q4: same with `&bool` | 27,288 | 0.50405 | 9 | |
| n_okh: holder added to the `Ok::<_,Error>((..))?` carry | 27,512 | 0.46517 | 10 | |
| p_h1/p_h4: execute `holder=hopt.unwrap_or(false)` / `if let Some(h)` | 27,280 | 0.46239 | 9 | **acct:178** sh:179 sret:181 .. hArg:186 feeT:187 feeV:189 ctx:191 |
| p_h1 + n_e | 27,400 | 0.45896 | 9 | acct:178 .. feeV:189 ctx:191 |
| p_h1 + cbpost | 22,784 | 0.32508 | 9 | (frame collapses) |

Store-site and tail knobs on main 65df90f (0.6453):

| spelling | bytes | ratio | n |
| --- | ---: | ---: | ---: |
| `curve.is_cashback_coin=cashback&&!holder` / `cashback&!holder` | 27,400 | = main | 10 |
| `curve.is_cashback_coin=!holder&&cashback` (short-circuit at the store) | 27,208 | 0.55021 | 9 |
| holder-first curve stores | 27,408 | 0.64041 | 10 |
| event `is_cashback_coin:cashback` | 27,408 | 0.64161 | 10 |
| pool CPI `pargs=(target,holder,fee)` | 27,424 | 0.63932 | 10 |

p_h1 reaches the angle's target exactly: 9 crossings, the accounts pointer on 178, the holder argument spill on 186 as in the
original, and fee value on 189. It still loses 0.18, because the and-1 holder rebuilds the validate and shared tree
(this is w14a10's hxe/uxe row: −120 B, block order of orig 0x4000–0x5000 lost). Its 0x2800–0x3800 region matches 0 plain tokens
but 251/251 register+frame-masked tokens: a permutation of spill colours, not a code change.

## Conclusion

The holder/cashback interval count is not a separate lever. Making the two bools materialize requires a phi or an
early use. Either way the spill weights of the fee tag, ctx and fee value move, and so do the colours of every argument spill
(main 185/188/189 → 183..187/186..189/187..191). The positional ratio pays for this in the wallet/sweep region. Main's colour
assignment is a local optimum, and the remaining gap is the original's validate phi structure (w13a38 cbflagphi, w14a10
and1outline), which costs 150–370 B that no size repay found so far.

## Next ideas

- p_h1's colour map is the closest to the original's argument-spill colours seen so far. Combined with w14a10's e3+tu8 validate
  outline (also and-1 holder), the and-1 family may be worth a full size-repay screen with the #3137 knob catalog. The
  deficit to beat is about 0.18 here and about 0.03 for e3+tu8.
- An oracle that keeps the cashback `AND_rr` in the entry block (no MachineSink) would isolate the interval effect.
  A MIR round trip from `-stop-after=machine-sink` does not reproduce main (28,560 B), so it needs a later start point,
  for example w14a18's stack-slot-coloring pin.

## Tools

- `tools/trial.sh <name> <edits.py> <slot>`: w14a13 `capvar.sh` + `sscrun.sh` (debug llc `-print-before=stack-slot-coloring
  -debug-only=stack-slot-coloring`) + w14a13 `sscmap.py` at the `admin_cto_sharing_config` call. Prints the rx result and the crossing count.
- `tools/runq.sh <slot> names..`: runs trials one after another. `tools/rec2.py`: ledger records. `edits/*.py`: every spelling above.
