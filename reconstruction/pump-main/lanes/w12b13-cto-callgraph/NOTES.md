# w12b13-cto-callgraph: admin_cto::execute call-sequence alignment

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `20a1ae9c0` (landed baseline `8cd7695c…`): 0.43919, 3,352 slots, 27,400 B, 1033/1033.

## Tool

`callseq.py` (this directory) lists every call in layout order for the original window and a
candidate function, names internal callees with a same-layout unstripped build (address-based
labels are an analysis aid, not proof of original source identity;
`--orig-names` defaults to the landed baseline, so candidates of another size still resolve),
names syscalls through `.rel.dyn`, and labels error sites:

- `vNNNN`: the PumpError variant whose rodata constant is in r1/r2 at a `name`/`fmt`/`to_string` call;
- `ENNNN Lnnn`: the error code and `line!()` immediates stored before a `From<AnchorError>` call.

```bash
python3 callseq.py                      # summary of differing runs (callee names)
python3 callseq.py --table --by-site    # full table aligned on callee + error-site identity
python3 callseq.py --cand <unstripped.so> --json out.json
```

`TABLE-main-20a1ae9.txt` is the `--table --by-site` output for the pinned
main `20a1ae9c0` build. It reproduces byte-for-byte from the retained pass-7
unstripped ELF (`8cd7695c3fc638fc8ccfaba49a55b7615421e6f1c4c02f623124d9cc67a8ebf2`).
Unretained intermediate k4 and j3 tables are omitted.

## Findings (main 20a1ae9)

1. 157 calls each (154 internal + 3 syscalls). The callee multisets are equal except the known
   ToString split: original 7 `to_string` / 8 inlined `PumpError::fmt`, ours 5 / 10 (307 and 312
   inlined in ours).
2. Callee-name sequence ratio 0.8726 (site-aware 0.8662). Only three regions differ:
   - **validate** (o7..o47): error-site layout order. Original (first block of each site):
     `289 306 [F289] 298 326 [3 memcmp] [F306] 296 [F326] 312ts 307ts 330ts 338ts 334ts | prep 410 memcmp sol_log`.
     Ours: `289 296 298 [F289] 330ts [3 memcmp] 312 [F296] 326 306 [F312] 307 338ts | prep 410 memcmp 334ts sol_log`.
     (`ts` = outlined `to_string`; `[Fnnn]` = the site's From call placed apart from its name/fmt.)
   - **334 placement**: the CreatorFeeNotConfigurable block has the same code and the same single
     predecessor (`jeq fee_configurable,0`) in both, but the original places it right after the 338
     block; ours places it after the wallet "Creator is a program" msg block (between its
     `ja` and the second msg literal). This is a pure block-placement difference (no size change).
   - **wallet / sweep tail** (o109..o157): original order is
     `[wallet flags] [wallet ATA create] [sweep ATA create] transfer_vault_tokens collect Clock::get From<PE> token_frozen(coin) [event] [collect_coin_creator_fee] From<PE>`;
     main has `[wallet flags] [sweep ATA create] transfer_vault_tokens token_frozen(coin) [wallet ATA create] collect …` and one extra trailing From<PE>.
## Follow-up on main b5975fa (after #2749)

`callseq.py --obj <m.o>` reads a relocatable object from an `llc -function-sections` oracle run:
callees are named through `.rel` entries and lddw constants are resolved through their relocation, so
the same site-aware table works for IR experiments (3 s per llc run, no build slot).

On main b5975fa (0.45147 / 3,308 slots / 27,400 B) the tail o47..o157 (110 calls) is identical to the
original; every remaining call-sequence difference is inside validate (o7..o47): the error-site order,
the 307/312 `to_string` inline split, and the 334 block placed after the 410 code.

Wallet hybrids on 20a1ae9 (ledger `...-callgraph-wallet-docollect-only-v1`, `...-docoin-only-v1`):
only both halves of #2518 together align the wallet/sweep tail. The source half alone carries all of
the -88 B (27,312 B, 0.44801) but keeps main's tail order; the coin half alone is +24 B (0.44378).

334 placement (`llc -debug-only=block-placement`, debug llc): when the 338 chain ends, the 334 block
(freq .0039) loses to `bb40.i`, the non-holder `target = t` copy (.0080). In the original `bb40.i` is
already placed because the fee checks are duplicated per arm (the holder arm tests fee tag and
quote_locked itself and jumps straight to the fee_configurable test, skipping 330), so the
fee_configurable block is not ready early. Branch weights on the 334 test alone never move it
(1:1, 3:1, 1:8 all keep the call order; ledger `...-callgraph-334-branch-weight-oracle-v1`).

`to_string` boundary (307/312): nesting the holder-reward checks as in the original's post-opt tree
(`if st.holder_reward{if !holder{289}} else if holder&&!st.holder_enabled{296}`, lines kept) makes the
callee multiset equal to the original (7 `to_string`, 8 inlined fmt) and raises the callee-sequence
ratio to 0.8854, but the function shrinks to 27,016 B (-384) and the ratio drops to 0.41569
(ledger `...-callgraph-nest-289-296-hr-first-v1`). Masking frame offsets and registers, main and this
variant are equally close to the original (0.803 vs 0.804), so the to_string fix needs ~380 B of
compensating structure (the original's per-arm fee checks and phi-of-constants exit) to be landable.

### Call-result slots follow ISel RPO (frame fingerprint of the original's branch polarity)

Every `{i64, ptr}`-returning call (all `From<AnchorError>`/`From<ProgramError>`, the CPI wrappers,
`prepare_bonding_curve`, `with_pubkeys`, `create_idempotent`, ...: 33 calls) gets its own 16-byte
result slot (`mov r1,r10; add r1,-X` before the call). The slots are created during instruction
selection, which walks the IR in reverse post-order, so sorting the calls by slot gives the RPO of the
final IR. `ir/rpo.py`-style RPO over the post-opt IR of main reproduces main's slot order exactly:

- original: `284 289 298 296 330 338 334 326 | prepare 410 ... CPIs ... | 312 307 wp 306`
- main b5975fa: `284 289 312 307 wp 306 298 330 338 | prepare 410 ... CPIs ... | 334 326 296`

(`slots.py` / `rposlots.py` in the lane scratch print these from any build.) RPO lists the second
successor's subtree before the first's, so the original's tail `312 307 306` means the first-successor
DFS path enters the non-holder arm and its None/zero/key errors first, and `334 326` early means the
fee test's first successor is the `fee == None` continuation. On main's post-opt IR (llc oracle):

| IR edit | bytes | ratio | RPO |
| --- | ---: | ---: | --- |
| none (main 20a1ae9 IR) | 27,400 | 0.43919 | main order |
| f2: fee tag test `None` successor first | 27,400 | 0.45956 | `... 338 334 326 | ... | 296` |
| f1: hr==0 holder test, non-holder successor first | 27,408 | 0.44032 | `... | 334 326 312 307 wp 306` |
| f1+f2 | 27,408 | 0.45829 | identical to the original |

(f2 is the mechanism w12a09-cto-cleanroom found at the same time: `match fee{None=>{},Some(f)=>..}`.)

### 298 check hoisted out of the target `if` (largest single gain found here)

`if holder&&new.is_some(){return Err(..298..)}let target=if holder{*holder_key}else{..}` (line 298
kept) on main b5975fa: 27,368 B (-32), ratio 0.45147 -> 0.48381, callee-sequence ratio
0.8854 -> 0.9236 (ledger `0x22a10-w12-b5975fa-callgraph-298-hoisted-before-target-v1`). The
`to_string` split is unchanged (5 calls); the gain is error-site layout. It needs +32 B of
compensation to land.

### 298 hoist + fee None-first (c2) and what does not compensate it

On main 70f2704 (swap_hop matched): `if holder&&new.is_some(){..298..}let target=if holder{*holder_key}else{..}`
plus `match fee{None=>{},Some(f)=>{..326..338..}}` gives 27,384 B (-16) at ratio 0.48487 (callee-sequence
0.9236; ledger `0x22a10-w12-70f2704-callgraph-298-hoist-plus-fee-none-first-v1`). Its post-opt IR has the
original's holder-threaded fee checks (holder arm: fee tag, quote_locked, then straight to the
fee_configurable test; 330 only on the non-holder arm). Same metrics for the spellings
`if holder{if new.is_some(){..}}` and `if holder&&!new.is_none(){..}`; `if new.is_some()&&holder{..}`
breaks the threading (27,008 B, 0.42359). Not compensators: curve bools read before `global_quote`
(-72 B, 0.46962), inverted wallet flags (byte-identical).

### Same mechanism as the per-arm cashback of #2831

w12a14-cto-hillclimb's 27,400 B candidate (PR #2831, 0.48652: `let cashback=if holder{false}else{st.cashback};`
before the fee checks, `if cashback{..330..}`, `match fee{Some(f)=>..,None=>{}}`, curve/event locals)
reaches the same holder-threaded validate: its callee sequence (0.9236) and result-slot order
(`284 289 330 312 307 306 298 338 334 326 | ... | 296`) equal those of the 298 hoist. Adding the 298
hoist on top of it is neutral (same ratio 0.4865188735769922 and 3,278 slots; only two overlapping u32
copies at +0xa30 swap; ledger `0x22a10-w12-4f24fbc-callgraph-298-hoist-on-hillclimb-d7acbb3-v1`).

Remaining call-sequence differences after #2831: the RPO places 330 and 312/307/306 early and 296 last
(original: `298 296 330 338 334 326 | ... | 312 307 306`), the 334 block sits after the 410 code, and
`to_string` is inlined at 307/312. On the 298-hoist IR, flipping the hr==0 holder test (non-holder
arm first) reproduces the original's full slot order but costs ratio (27,384 B, 0.47678 vs 0.48381);
the IR flips that gain ratio at +0 B (`!holder_enabled` 296 test +0.008, 306 None test +0.003) are
single-use `icmp eq x,0` branches whose successor order InstCombine fixes, so plain source
spellings cannot reach them.

### Polarity scan on the #2831 IR and the and-1 tag test

Single-branch polarity scan of all 146 conditional branches of execute on the #2831-equivalent
post-opt IR (27,400 B, 0.48652; llc oracle, IR only):

| flip | branch | bytes | ratio |
| --- | --- | ---: | ---: |
| #33 | 410 `require!(creator_fee==0)`: error successor first | 27,400 | 0.49191 |
| #13 | 306 `new` None test: Some successor first | 27,400 | 0.48981 |
| #20 | holder-arm fee tag test | 27,400 | 0.48772 |
| #10 | 296 `!holder_enabled` test | 27,400 | 0.48742 |
| #43 | wallet `collection_native` memcmp | 27,400 | 0.48742 |
| 33+20 | | 27,400 | 0.49221 |
| 33+13 | | 27,392 | 0.49558 |

All of these are single-use `icmp eq x,0` branches: InstCombine canonicalizes their successor
order, so no plain spelling of the same test reaches them. #13 has a mechanism, though: the original
tests the 306 tag as `(tag & 1) == 0` (`and64 r1,1; jeq r1,0` at +0x738) because its tag is read from
the entry copy of `new` (an SROA-split memcpy drops `!range`), and BranchProbabilityInfo treats a
single-bit-mask compare as 50/50, so the E306 block becomes the fallthrough. Replacing the 306 test
with `icmp eq (and tag,1),0` in the IR gives exactly the #13 result (0.48981 at 27,400 B; on the
298-hoist IR 0.48381 -> 0.48711). The source route is a copy of `new` that memcpyopt cannot forward,
e.g. `validate(.., mut new, ..)` with `new.take()` at 306 (w12a06 measured +272 B on 20a1ae9).

## Scope

These are instruction and call-layout observations for the named baseline.
They do not establish equivalent source scopes or whole-program identity.
Use the same-layout `--orig-names` input when examining a differently laid-out
candidate. Reports require a fresh output path and never replace an existing file.
