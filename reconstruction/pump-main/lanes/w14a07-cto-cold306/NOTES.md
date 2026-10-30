# w14a07-cto-cold306: a source form for the cold 306 `Some` edge

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a43-cto-outline306 (#3166) next idea 1. Base: main 308b545 (0.63062), then main 769f331 (0.63241).
Every ratio is the raw-IR capture + `opt -O3` + extracted-`llc` oracle (w13a43 `tools/src.sh`; main reproduces exactly).
Ledger keys `0x22a10-w14-{308b545,769f331}-cold306-*-v1`.

## 1. The weights oracle has two separate parts

On RAR (w13a43 `mkv.py` gene: `let args=&(new,)` back before the CtoState block) + `!prof` Some:None on validate's raw-IR
306 switch, the weight acts twice: in validate's pre-inliner BFI (which call sites of `to_string` are cold, cut 2% of
validate's entry) and, because `!prof` survives to `llc`, in block placement of the final tag test.

Pre-inliner scan (308b545, RAR base):

| Some:None on the raw 306 switch | bytes | ratio | outlined `to_string` |
| --- | ---: | ---: | --- |
| none / 20:12 | 27,376 | 0.62191 | 330 334 338 660 719 |
| 1:1 | 27,384 | 0.61402 | same |
| **12:20 (zero/pointer-heuristic strength)** | 27,384 | 0.60893 | same: 307 BFI 0.0212 > 0.02 |
| 12:22 | 27,128 | 0.62622 | 307 only |
| 12:24 = 1:2 | 26,920 | **0.63161** | original set (307 312 ...) |
| 12:26 .. 12:30 | 26,912 | 0.62989 | original set |

So a zero- or pointer-heuristic spelling of the 306 test cannot outline on its own: BPI's best (12:20) leaves 307 at
0.0212 of validate's entry. It needs about another 0.94 factor upstream.

## 2. Source form for the pre-inliner part: a `#[cold]` marker call (inlined away)

```rust
 Ok(target)}#[cold] fn cold(){}pub fn execute(...      // line 339, no new lines
  let t=if let Some(t)=new{cold();t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};   // line 306
```

- `cold()` is not MIR-inlined (unlike a `#[cold]` closure, w13a49) and reaches LLVM as a call to a `cold` function.
  BPI's estimated-weight heuristic then gives the Some arm 1:16 in validate's pre-inliner BFI, which outlines 307 and 312.
  The empty callee is then inlined, so no call is left: 86 lddw, calls unchanged, 154 internal.
- The result is **exactly** the 1:2 oracle with the `!prof` stripped before `llc` (308b545: both 0.62203 @ 26,912).
- Placement matters: the marker in the 307 and 312 error branches (c2) also outlines but gives 0.62117 @ 26,960.

| form | 308b545 | 769f331 |
| --- | --- | --- |
| main | 0.63062 @ 27,400 | **0.63241** @ 27,400 |
| RAR | 0.62191 @ 27,376 | 0.62371 @ 27,376 |
| RAR + 1:2 weights (oracle) | 0.63161 @ 26,920 | 0.63342 @ 26,920 |
| **c1 = RAR + `cold()` in the Some arm** | 0.62203 @ 26,912 | 0.62385 @ 26,912 |
| c1 + llc-time None:Some 1:1 on the final tag test | 0.62708 | 0.62889 |
| c1 + llc-time 20:12 | 0.62557 | |
| c1 + llc-time 2:1 | 0.63161 (= oracle) | 0.63342 (= oracle) |
| `cold()` without RAR (main + C1) | | 0.56290 @ 27,016 |

## 3. What is left: the llc-time weight on the final tag test

After inlining, the 306 test is `icmp eq i8 %_27.sroa.0.0.copyload, 0`. That compare was already folded inside validate,
where the tag is a ranged discriminant load. BPI's zero heuristic then makes None *unlikely* (12:20), and MBP lays out
`298 289 312 296 326 306 307`. The original lays out `289 298 306 296 326 312 307`. Getting 306 ahead of 296 takes
None:Some >= 2:1 at llc: the 20:12 order is `296 306 326 312` and the 1:1 order is `296 312 306`.

- The original's test is `ldxdw [r10-0x8f8]; and64 r1,1; jeq` on the entry-copied tag byte (`ldxb [r7+0]` at orig 0x4d8).
  That is a range-free `and 1`, which BPI's zero heuristic ignores (single-bit mask), so it is 1:1.
- e1 reproduces that form: execute passes `has:bool = args.0.is_some()` and validate tests `if has{..}`, giving a range-free
  `and i8 %copyload, 1` at llc. But `new.unwrap_or_default()` in the arm changes codegen (0.62035 @ 26,720), and 1:1 still
  places 306 after 312. e2 (`if let (true,Some(t))=(has,new)`) folds back to the tag test, byte-identical to c1.
- `Option<&Pubkey>` (d1 `args.0.as_ref()`) moves the read into execute, but MIR forwards it to a ranged load of `%new`,
  so the zero heuristic applies again (0.60088 @ 26,752). d2 (`new.as_ref()`) is byte-identical to c1.
- Swapping the branch successors at 1:1 gives 0.60955. Holder threading (`tools/thread2.py`, block-name version of w13a43
  `thread.py`) on c1 and e1 gives 0.62298 and 0.619, and 306 stays behind 296.
- llc-only single-weight scan (`tools/scanw.py`; 20:12 and 12:20 on each of validate's 25 inlined branches): with the
  default tag test the best is the tag test itself at 20:12. With the tag test at 1:1, the best is `bb94.i` 20:12 at 0.62940
  (308b545). No source-reachable heuristic weight reproduces the 2:1 placement.

Bound: on 769f331 the outline source form sits at 0.62385 (1:1 reachable only with a codegen change: 0.62889) against
main's 0.63241. Even the full oracle is only +0.001 over main, and 488 B must still be filled.

## Next ideas

- A 306 tag test on the entry-copied tag that is range-free *and* placed first. The original's whole validate region works
  on the SROA'd entry copy of `new` (orig 0x4d8-0x538). Combine c1 with w13a41/w13a42 entry-copy forms that keep the tag
  as a copyload, and check layout at 1:1.
- w14a08 outlinefill: screen fills on c1 (the real source form), not on the `!prof` oracle. The oracle's extra 0.0096
  comes from the llc weight, which source cannot express.

## Tools (`tools/`)

- `mkv.py`: w13a43's gene applier plus genes `C1` `C2` `C3` (cold marker), `OR1` `OR2` (Option<&Pubkey>), `HB` `HB2` (has:bool).
- `llw.py <ex.ll> <outdir> <tag> <regex>:<a>:<b>`: set or strip an llc-time weight on the branch after a final-IR line, then llc.
- `scanw.py <ex.ll> <outdir> [base line:a:b]`: single-weight scan over validate's inlined branches.
- `lseq.py <fn.txt> [maxaddr]`: error-line site order. `thread2.py` / `thr.sh`: holder threading by block name.
