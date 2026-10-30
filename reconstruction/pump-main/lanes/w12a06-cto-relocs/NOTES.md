# Lane w12a06-cto-relocs (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the 2 extra `lddw` relocations (the only non-`.text` ELF difference, `.rel.dyn` 0x18050 vs 0x18030).
Base: main 20a1ae9c0 (admin_cto 0.43919), then b5975fa67 after #2749 (k4size, 0.45147).
Ledger approach `lddw-reloc-pairing`, keys `0x22a10-w12-20a1ae9-relocs-*`.

## 1. What the 2 extra lddw are

`tools/lddwpair.py <orig.so> <cand.so> 0x22a10 27400 --list` classifies every `lddw` target
(`.rodata` string/constant, `.data.rel.ro` Location or vtable, plain constant):

- 86 vs 88 `lddw` (84 vs 86 relocated; 2 are the constant `-0x7fffffffffffffe6`).
- The only multiset difference is `.data.rel.ro+0x128`, the `String as core::fmt::Write` vtable: 9 in the original, 11 in ours.
  Every panic `Location`, string, seed, program id and `&PumpError` constant pairs 1:1. No extra panic, unwrap or overflow site exists.

`tools/errsites.py <ann.txt> <so>` (after `tools/ann.py`) lists every `PumpError::name` site with its variant (read
from the `lddw r2` constant) and whether `<T as ToString>::to_string` is called (OUT) or inlined (INL, `Display::fmt` + vtable):

| variant (line) | 19 (312) | 30 (307) | 80 (330) | 78 (338) | 77 (334) | 93 (660, 719) | all others |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | OUT | OUT | OUT | OUT | OUT | OUT | INL |
| main | **INL** | **INL** | OUT | OUT | OUT | OUT | INL |

So the 2 extra relocations are the inlined `to_string` at 307 `CreatorShouldNotBeZero` and 312 `InvalidCreator`
(same finding as w9r1/w9r2-admincto-relocs, re-confirmed on 20a1ae9).

## 2. Why they are inlined: pre-inliner block frequencies (new)

Raw-IR oracle: `tools/capraw.py` captures the `-C no-prepopulate-passes` module (experiment copy only), and
`opt -O3` (SDK rustlib `opt`) + `llc` reproduces main's `execute` exactly (`tools/oracle.sh`, ratio 0.43919, identical insns).
`opt -O3 -print-before=inline -filter-print-funcs=<validate> -print-module-scope` gives the module at the moment the
CGSCC inliner looks at `validate`'s calls; `opt -passes='function(print<block-freq>)'` on that dump gives:

| block | role | freq (entry = 1) |
| --- | --- | ---: |
| bb5 | after mayhem test (`icmp eq mayhem,0`, zero heuristic) | 0.375 |
| bb12 | 296 check (`!hr && !he` select, 50/50) | 0.1875 |
| bb18 | 296 passed, **reached only with holder = true**, `br holder` | 0.09375 |
| bb20 | else arm = 0.070313 (real, via critedge) + 0.046875 (infeasible, from bb18) | 0.11719 |
| bb27 / bb28 | 306 / Some (the tag test is already 50/50 here: `icmp ult i1` switch-range form) | 0.0586 / 0.0586 |
| **bb29** | **307 error (`to_string`)** | **0.021973** |
| **bb36** | **312 error (`to_string`)** | **0.022316** |

`-pass-remarks=inline`: `to_string` (cost 130) is inlined into validate at threshold 325 at 7 sites and kept at
the cold-call-site threshold 45 (relative frequency < 2%) at 4 (330, 334, 338, 326; 326 is re-inlined later in execute).
307/312 sit just above 2% only because of the infeasible edge: bb12 has two holder-true predecessors (the 289
check's holder edge is threaded straight to it), so EarlyCSE cannot fold bb18's `br holder`, and BPI sends half of
bb18 into the else arm. Without that edge 307 = 0.0132 and 312 = 0.0134 (cold, outlined as in the original).

Consequences:
- An and-1 / `take()` form of the 306 tag test cannot cool 307/312: the test is already 50/50 at inliner time.
  Measured: `validate(mut new)` + `new.take()` only at 306 on main = 27,672 B, 0.41461, still 88 lddw.
- Any source that removes the infeasible edge (the 296 check inside the holder arm, #2370's form) makes the outline set
  and the lddw multiset equal to the original's.

## 3. Outlining alone costs ratio (oracle)

Marking only the 307/312 `to_string` calls `noinline` in the raw IR (everything else unchanged): 26,960 B, lddw 86 = original,
ratio 0.43919 -> **0.40918**. The two inlined bodies own String/Formatter slots; without them the frame shrinks another
8 B (arg spills at `-0x8e8`; main `-0x8f0`; original `-0x928`). The original's frame is 64 B larger than "main with
307/312 outlined", so the outline fix only pays together with a frame/size source of +64 B frame and about +440 B code.

## 4. Micro oracle: which spellings give the original's 306 `and 1`

Small `#![no_std]` crates compiled with the identity rustc (`hybrid144`, `--target sbpf-solana-solana -C opt-level=3`, about 0.05 s each)
show the original's pair of tag tests (298 `jeq tag,0`, 306 `ldxb; and64 1; jeq`) appears when the 306 let-else
matches a copy that was written, i.e. `let mut m=new; let Some(t)=m.take() else ..` or `new.xor(None)`.
Plain `let Some(t)=new`, `match`, `if let`, `is_none()`, `ok_or`, `filter`, `or` all give `jeq tag,0`.

## Trials (main 20a1ae9 unless noted; ledger keys `0x22a10-w12-20a1ae9-relocs-*`)

| trial | change | bytes | ratio | lddw |
| --- | --- | ---: | ---: | ---: |
| main | | 27,400 | 0.43919 | 88 |
| t01 | take() at 306 only | 27,672 | 0.41461 | 88 |
| oracle | 307/312 `noinline` only | 26,960 | 0.40918 | 86 |
| v2 | 296 in holder arm + validate keys by value | 26,944 | 0.38604 | 86 |
| v1 | v2 + take() at 306 | 27,080 | 0.43085 | 86 |
