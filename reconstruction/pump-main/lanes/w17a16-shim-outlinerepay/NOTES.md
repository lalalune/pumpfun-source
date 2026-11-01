# w17a16-shim-outlinerepay: the 307/312 to_string outline, the original's validate order, and the size repay

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Shim track.
Bases: main bf01b5fd9 (M 2,270, 0.68005), then main 8330455eb (M 2,278, 0.68244) after #4011/#4017/#4018 landed.
Ledger: approach `outlinerepay`, keys `0x22a10-w17-bf01b5f-outlinerepay-*` and `0x22a10-w17-8330455-outlinerepay-*`.

M is the scored masked difflib match count: ratio = 2M / (3,339 + N), N = instructions (27,400 B with 86-88 lddw = 3,337
or 3,339). At 27,400 B, beating main 8330455 needs M >= 2,279.

## 1. Oracle

w17a06's exact slim pre-opt oracle (`capraw.py` one identity build that writes pre-opt IR, about 60 s under load;
`preslim.py` with `surv-1647da0.txt`; `fx.py` opt -O3 + slim + llc, 1-2 s). `tools/cap.sh <name> <genes> <slot>` applies
`tools/g16.py` genes (exact single-occurrence edits, line count asserted) to a crate copy and runs the chain; it also writes
the post-opt slim module `fx/<name>/m.ll` (for llc-only work: w17a02 `bws.py`, w17a11 `ro.py`/`px.py`, `tools/pw.py`)
and `framemap.py` (w17a14). On both mains the capture of plain main reproduces `cto.json` exactly (2,270 / 2,278).

## 2. The outline base on current main

| cell (bf01b5f) | genes | bytes | M | lddw | validate from-order | note |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main | - | 27,400 | 2,270 | 88 | 298 289 296 326 306 312 307 | |
| c1 | `cold()` at the 306 Some arm | 27,000 | 2,002 | 86 | | collapse (T1 -163), as on older mains |
| g1c1 | g1 creator binding + c1 | 27,112 | 2,004 | 86 | | collapse: only tf_g3 keeps the base |
| tfvc1 | tf_g3 read through main's volatile curve reload + c1 | 27,088 | 2,002 | 86 | | collapse |
| **tfc1** | tf_g3 + c1 | 27,048 | 2,220 | 86 | 298 289 **312** 296 326 306 307 | exact LCS 2,269 (-6 only) |
| tan2 | w16a13 tAn2 | 27,048 | 2,232 | 86 | 298 289 296 312 306 326 307 | LCS 2,246 |
| tfp67 | tf_g3 + `expect_p(new.is_none(),true,0.6667)` | 27,272 | 2,247 | 87 | 298 289 306 296 326 312 307 | only 307 outlined: main's 312 `expect_p(..,0.625)` keeps 312 warm |
| **tfcp75 / B75** | tf_g3 + `expect_p(new.is_none(),true,0.75)` (+ `cold()`, which is then a no-op) | 27,112 | **2,251** | 86 | 298 289 **306 296 326 312 307** | = tfc1 + llc 3:1 on the 306 tag test, token for token |

- **tfc1's frame is main's frame.** `framemap.py`: every host offset is identical; the outline only drops the inlined
  `Display::fmt` buffers from FI40 and renumbers FIs. So the outline needs no MaybeUninit host stand-in (step 2 of the
  angle is empty).
- **tfc1's -50 M is difflib alignment, not structure.** Exact true LCS is 2,269 against main's 2,275 (V3 -7, V4 +1). The
  312 error block lands before V3 (from-order `298 289 312 ...`), so difflib takes V4 early and drops all of V3 (-57).
- **llc-only sweep (bws.py) on tfc1:** the only lever is the 306 tag test. None:Some 9:5 .. 2:1 gives 2,251 @27,056, 3:1 ..
  16:1 2,251 @27,112-27,120. `expect_p(new.is_none(),true,0.75)` with the payload read through a raw pointer realises it
  exactly (B75); with that branch weight in place the `cold()` marker is ignored, and on 8330455 the variant without
  `cold()` is byte-identical.

## 3. The original's validate order is reachable from source on the outline base

w17a11's C1-pred block order (llc-only on main: 2,287) applied to B75's post-opt IR gives **2,278 @27,064** with the
original's error order exactly (from 289 298 306 296 326 312 307, name 289 306 298 326 296 312 307), where main + C1-pred only
reaches 312-before-296. Probing the orders (`ro.py`, five rustc-creation-model orders + subsets) shows the gain needs just two
things: the holder_enabled test block (`bb16.i`) must not be layout-glued to either successor (BPF's unanalyzable-branch
pre-merge), and P(!holder) > 0.5 on the `!hr` holder test (`bb14.i`). The weight alone gives 2,253.

Source realisation (gene `D`/`Dx49`, lines 289/296/298, no line added): write the validate head as the explicitly threaded
`if if`, so MIR jump threading hands LLVM an already-threaded CFG whose rustc creation order puts the 306 blocks between
`bb16.i` and its successors:

```rust
 let target=if if st.holder_reward{if !(hopt==Some(true)){return Err(..HolderRewardCreatorImmutable..);}true}else if unsafe{expect_p(holder,true,0.49)}/*shim: ..*/{   // 289
  if !st.holder_enabled{return Err(..HolderRewardDisabled..);}true}else{false}                                                                                         // 296
 {if unsafe{pt1(3,new.is_some())}/*shim: ..*/{return Err(..CtoNewCreatorNotAllowed..);}*holder_key}else{                                                               // 298
```

Same semantics as main (hr&&!holder -> 289; !hr&&holder&&!he -> 296; holder -> 298 test; else the non-holder arm).

| cell | base | bytes | M | note |
| --- | --- | ---: | ---: | --- |
| b75D (no weight) | bf01b5f | 27,168 | 2,241 | glue broken, weight missing |
| **b75Dx49** | bf01b5f | 27,128 | **2,277** (+7 over main) | exact LCS 2,287 (+12 over main); `!holder` at 289 is byte-identical |
| b75crl3Dx49 | bf01b5f | 27,200 | 2,277 | crl3 free again |
| **n_b75Dx49** | 8330455 | 27,136 | **2,283** (+5 over main) | |
| n_E = **V** (tfp75 + crl3 + Dx49, no `cold()`) | 8330455 | 27,208 | 2,283 | 306 p 0.7/0.75, holder p 0.45/0.49: identical |

## 4. Repay price table on the outline base (source captures, slim oracle)

On B75 (bf01b5f, 2,251 @27,112):

| piece | bytes | M | verdict |
| --- | ---: | ---: | --- |
| crl3 (`let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}..`) | +72 | 0 | **free** (also on Dx49, both mains) |
| k8 PDA-first (w17a09) | -32 | -514 | collapse (RA cascade as on main); crl3+k8 the same |
| b01 holder_key by value | -88 | -489 | collapse |
| Fa validate reads `args.0` | +176 | -828 | collapse (660 placement cliff) |
| t1n `if new.is_none()` shared arm | -96 | -388 | collapse |
| g1 (instead of tf_g3) | | | collapses the base (g1c1) |

On V (8330455, 2,283 @27,208):

| piece | bytes | M | note |
| --- | ---: | ---: | --- |
| `expect_p(shared,true,0.625)` on the shared split (shw625) | +56 | +1 | = the only byte-adding llc weight with M >= 0 in a 144-branch sweep |
| + holder-vault compare kept in memory (`write_volatile`, w17a06 vs:sweep:31935) (hvw) | +32 | +4 | **2,288 @27,296** |
| + pool owner compare kept in memory (w17a06 vs:execute:29962) (pow) | +32 | +2 | 2,286 @27,296; hvw+pow not additive (2,282 @27,328) |

## Tools

`tools/g16.py` (genes, including the outline base, the threaded head and the repay pieces), `tools/cap.sh`, `tools/pw.py`
(llc-time branch weights on a post-opt slim module), `tools/bsum.py` (block summary of execute's post-opt IR: error codes,
calls, terminators), `tools/info.py` (lddw and error orders), `tools/mbb.py` (final MBB order from the debug llc).
