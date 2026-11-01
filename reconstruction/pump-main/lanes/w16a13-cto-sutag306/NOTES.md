# w16a13-cto-sutag306: the 306 None test as a bit test on an Option<Option<Pubkey>> tag (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto.rs unchanged since 7e5ba44a7/1f4e396b5): 0.67436, 3,141 slots, M 2,251, Mperm 2,293,
true LCS rfj 3,006. Continues w16a06-cto-bonoutline next idea 1 (#3863). Ledger: approach `sutag306`, keys
`0x22a10-w16-1f4e396-sutag306-<form>-v1`.

**Result (in progress): no landable change yet; main stays the best zero-loss measurement (0.67436 / 3,141 slots / 27,400 B).**
- The 306 trigger has an ordinary-Rust form. A `match` on `Some(Some(_))` of an `Option<Option<Pubkey>>` that validate
  receives as a parameter outlines 307 and 312 at V (P(Some) 0.25, or 0.125 with the double test) without any
  forcing construct.
- **tAn2 / tB2** do not collapse: 27,040 B, M 2,219, lddw 86. They use the tf_g3 creator binding, a copy `Some(new)` read
  by validate, and the 306 line `match (*su,new){(Some(Some(_)),Some(t))=>t,_=>Err}`. They also give the original's
  post-opt 306 bit test (`and 1; jeq 0`) next to the unmasked 298 test on the same tag value, as at orig 0x730/0x908.
- Every non-redundant carrier collapses (M 1,381-1,525 on main and on tf_g3). In those, the copy is the real
  `sharing_update` (su-first), or the Pubkey is read from the copy (the original's entry pieces).
- tAn2 cannot land. It is 44 below main in true LCS (rfj), and the faithful repay pieces collapse it (Fa) or lose
  (b01). Its extra conjunct is also redundant (the F2 class).

## 1. Oracle (tools/, experiment only; paths point at this lane's `$OUT`)

- `capV.sh <name> <genes> <slot> [rx]`: copy the worktree crate, apply `sg.py` genes (exact single-occurrence edits or
  callables, line count kept), one identity raw-IR capture (w15a25 `capraw.py`), then the fast V oracle (w15a25
  `reduce.py` + `vbfi.py` + `thr.py`, about 2 s: validate's BFI at its inliner visit and each to_string site's inline
  threshold), and with `rx` the full `opt -O3` + SDK `llc` (w16a06 `rx.py`, about 35 s). Rows go to `data/V.txt`.
- `eo.py`: error-site offsets and lddw count against the original and main. `rdiff.py`: opcode-skeleton diff of two
  blobs. `llcx.py`: post-opt IR edit + llc. `rst.sh`: w16a09 `blkrestore.py` layout restore against a reference.
- Scores: w16a06 `sc.py` (M, fM, skM), w15a16 `mp.py` (Mperm, true LCS), w14a128 `lcschunk.py` (rfj true LCS).

## 2. What the original's 306 test is

- At V (validate's own inliner visit) main's 306 test is `icmp ne i8 new.tag,0` folded into a 2-way range switch: BPI has
  no heuristic, P(Some) = 0.5, 307 = 0.0283 and 312 = 0.0287 of entry: both above the 0.02 cold cut, both inlined.
- A `match` that reads `Some(Some(_))` from an `Option<Option<Pubkey>>` that validate cannot see the origin of (a
  parameter) stays two tests at V: `icmp eq i8 tag,2` (niche decode, 50/50) and then `and i8 tag,1` (the inner tag of a
  value with `!range [0,3)`, 50/50). P(Some(Some)) = 0.25, 307 = 0.0141C, 312 = 0.0144C: **both outline at V
  (threshold 45, lddw 86 = the original's count)**. Every spelling of the match does this (`_` arm, let-else, if-let,
  3-arm, nested, by value or by reference).
- After inlining, CVP sees `tag != 2` before the inner test and the two tests become `switch i8 tag [2,0]` (llc:
  `and 0xfd`). Only when the inner test is the only one left at that point does the original's **`and i8 tag,1` +
  `icmp eq 0`** survive (`and64 r1,1; jeq r1,0` as at orig 0x730), on the same range-free copyload that the 298 test reads
  unmasked (`jeq r1,0`, orig 0x908) and that feeds the sharing tag phi `{tag,2,2,0}` (orig slot [r10-0x8f8]). The
  double-test forms below (tAn2) give exactly that.

## 3. Carrier table (V oracle + rx on raw-IR captures; main = 27,400 B, M 2,251)

| carrier | 306 IR at V | V 306 / 307 / 312 | lddw | bytes | M | note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| main (m1) | `icmp ne tag,0` range switch | 0.0754 / 0.0283 / 0.0287 | 88 | 27,400 | 2,251 | |
| IR-forced target tf_g3 + V 1:2 (w16a06 `tfg3n_vw1_2`) | `!prof` | | 86 | 27,032 | 2,234 | not source |
| rw: su-first, `match *su{Some(Some(t))=>t,_=>E}` (validate takes `&sharing_update`) | tag==2, and 1 | 0.1132 / 0.0141C / 0.0144C | 86 | 27,152 | 1,443 | collapse: 660 chain after the sweep |
| rle / rm3 / rm3s / rne / rne2 / vw / vm3 (spellings) | same | same (m3/ne keep two 306 blocks) | 86-90 | 27,152-27,464 | 1,395-1,431 | collapse |
| trw / trle / tvw / trm3 (same on tf_g3) | same | same | 86-90 | 27,224-27,464 | 1,381-1,462 | collapse (trm3: 660 placed, sweep body moved) |
| rw/trw post-opt switch -> `icmp eq 0` or `and 1` (IR) | | | 86 | 27,160-27,248 | 1,417-1,421 | the 306 form is not the cause |
| trw, blkrestore to vw / main layout | | | | 27,272 | 1,631 / 1,616 | skM 2,717: RA, not only layout |
| mA / mAv: temporary `&Some(new)` for validate, payload from it, main form | tag==2, and 1 | outlined | 86 | 27,208 | 1,525 | collapse |
| tA / tAv: same on tf_g3 | same | outlined | 86 | 27,144 | 1,789 | 660 placed; entry i64/ptr pieces of the copy (orig 0x4d8-0x538 shape) wreck RA: Mperm 1,930, skM 2,792 |
| tAn1: tf_g3 temp, `Some(Some(_))=>new.unwrap_or_default()` | | outlined | 86 | 27,040 | 1,889 | |
| trn1 / trn2 / trn3 / rn2: su-first + payload from new | | outlined | 86 | 26,920-26,936 | 1,408-1,409 | collapse (su payload initialised at entry) |
| mAn2: temp + double test, main form | | outlined | 86 | 27,008 | 1,972 | partial collapse |
| **tAn2 / tAn3 / tAn4: tf_g3 + temp `&Some(new)` + `match (*su,new){(Some(Some(_)),Some(t))=>t,_=>E}`** | tag==2, and 1, new tag | **0.1320 / 0.0071C / 0.0072C** | **86** | **27,040** | **2,219** | **no collapse**; Mperm 2,262, Mhc 2,272, LCS 2,233, rfj 2,962 (main 3,006) |
| tAn2 + Fa (validate reads `args.0`) / + Fs | | outlined | 86 | 27,280 | 1,393 | collapse |
| tAn2 + b01 / + Fa + b01 | | outlined | 86 | 26,976 / 27,320 | 1,777 / 1,363 | loses / collapse |

B form (the copy is the sharing payload itself: `let args=&(Some(new),)`, the shared non-holder arm takes
`sharing_update=args.0`, validate reads `&args.0` or `args.0`):

| carrier | bytes | M | note |
| --- | ---: | ---: | --- |
| tB2 / tB2v (tf_g3, double test) | 27,040 | 2,219 | byte-identical to tAn2 |
| mB2 (main form, double test) | 27,008 | 1,972 | = mAn2 |
| tB1 (tf_g3, `match *su{Some(Some(t))=>t,_=>E}`, payload from the copy) | 27,496 | 1,391 | collapse |
| iw / in2 (the update built inside validate: `let su=Some(new);match su{..}`) | V only | | folded before V: main's V (307/312 inlined) |

## 4. Findings

1. **The source trigger exists.** An `Option<Option<Pubkey>>` whose origin validate cannot see makes the 306 Some path
   P = 0.25 (or 0.125 with the double test) at V and outlines both 307 and 312 to_string calls, which no `Option<Pubkey>`
   spelling can (w16a06 section 7). It also gives the original's post-opt 306 bit test (`and 1`) next to the unmasked
   298 test on the same tag value, and the original's lddw count (86, which removes the 2 extra `.rel.dyn` entries).
2. **What collapses.** When the 3-valued value is the real `sharing_update` built before validate (su-first), or when
   validate reads the Pubkey from the copy, LLVM keeps the copy's pieces live from the entry (the i64 [8,16) and ptr
   [16,24) pieces the original loads at 0x4d8-0x538, plus the 7/9 B memcpys = the original's "unmerged 7/9 pieces").
   Greedy RA then changes in the sweep CPI clone chunk (orig 0x3000: M 29 vs main's 158) and the MBP 660/post chain
   flips (w15a31's tail-merge mechanism). Layout restore does not recover it (trw restored 1,631; skM 2,717).
3. **What does not collapse.** A temporary read only by validate's 306 test, with the Pubkey taken from `new`: on the
   tf_g3 creator binding (w15a21) it lands at M 2,219 @27,040 B, 15 below the IR-forced target (2,234 @27,032) and the
   original's 306 IR. On main's form it half-collapses (1,972), as w16a06 found for every outline base.
4. **Why it does not land.** At the pinned size tAn2 needs +360 B (43 tokens) carrying at least 33 matched tokens
   (M 2,252). Its true LCS (rfj 2,962) is 44 below main's 3,006 (validate chunk 0x800: -39), the same deficit the
   IR-forced outline bases have, so the outline route still has no skeleton gain over main to repay with. The faithful
   repay pieces collapse it (Fa: the entry copy is exactly the RA trigger of finding 2) or lose (b01).
5. **Steering caveat.** The temporary in tAn2 is redundant with `new` (it is `Some(new)`), the same class as F2's `has`
   flag; the angle's rule says such a conjunct is not a carrier. The non-redundant forms (su-first, where the copy is
   the real sharing update) are the ones that collapse. The B form makes the copy real data (it is the non-holder sharing payload), but the double test in
   validate is still redundant.

## 5. Kill test

- P(Some) at V below 0.4: **met** by every 3-valued carrier (0.25, or 0.125 with the double test).
- Every non-redundant outlining carrier collapses below M 2,150, with or without tf_g3 (1,381-1,525): **met**. The only
  carrier that does not collapse (tAn2/tB2, 2,219) relies on a redundant conjunct. Its route is also bounded below main:
  true LCS rfj 2,962 against main's 3,006, and it needs 33 matched tokens in 43 repay tokens.
- The 306 trigger question is closed. The original's 306 test is an `Option<Option<Pubkey>>`-style 3-valued bit test,
  and its outline effect is reproducible from ordinary Rust. On the current skeleton it costs more RA/frame than it buys.
