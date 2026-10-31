# w15a23-cto-decisionenum: the admin_cto decision as a sum type (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883 (`$BASE`, not rebuilt). admin_cto is 0.67376 with 3,124 slots at 27,400 B. Its true-LCS is `---` 2255,
`-fj` 2599 and `rfj` 3007. Binary-approximation Mperm is 2292.
Ledger approach `decisionenum`, keys `0x22a10-w15-9120883-decisionenum-*` (75 rows).

**Result: notes only, no source change.**
I built 75 variants with full `measure.sh` builds. Every enum, sum-type or validate-return form loses at least 0.0014, and
most lose 0.1 to 0.45. The only near-neutral form is `d9`. It is byte-identical to w15a20's `m_il` polarity lever
(-8 B), and none of the 33 size knobs repays it.

## 1. The original's sharing tag is `Option<Option<Pubkey>>`, not a decision enum

`webs.py` on the original bytes gives the definitions of the sharing tag slot `[r10-0x8f8]` (5 defs, all inside
validate):

| orig offset | def | meaning |
| --- | --- | --- |
| 0x4e0 | `ldxb r2,[r7+0]` | `new`'s own Option tag (the `Some(args.0)` arm copies it, it is not a constant 1) |
| 0x1188 | `mov r1,0` | `Some(None)` (shared, holder) |
| 0x1838 | `r0` (= `[0x8f8]` reloaded) | pass-through |
| 0x18d8, 0x1980 | `mov r1,2` | `None` (not shared) |

The value set is {new.tag, 0, 2}, which is exactly the niche layout of `Option<Option<Pubkey>>`. No def stores a third
constant (3 or more). So the original has no 3-or-more-variant decision tag carrying the sharing payload. The only
enum spellings consistent with these values are isomorphic to main's `Option<Option<Pubkey>>`:
- `enum Sharing{Reset(Option<Pubkey>),Keep}` (d9);
- `enum Next{Shared(Option<Pubkey>),Unshared{collect}}` (d8).

The sweep gate and `collect_old` stay separate values, as w14a46 and the w12 residual catalog found.

## 2. Price table (full builds, zero normalized losses unless noted; size not repaid; `data/table.md`)

| family | best variant | ratio | bytes | LCS `---` / `-fj` / `rfj` | what happens |
| --- | --- | ---: | ---: | --- | --- |
| main | - | 0.67376 | 27,400 | 2255 / 2599 / 3007 | |
| d1: `Next{Holder,Shared(Option<Pubkey>),Wallet{collect}}` in execute, every later use from `match`/`matches!` (7 spellings) | d1c | 0.40831 | 27,520 | - | the tag is tested at 4 sites; JumpThreading threads the later tests and re-lays the tail |
| d4: 4 variants (shared x holder), holder store from the enum | d4 | 0.23987 | 28,104 | - | +704 B of duplicated tail |
| d5: payload-less `Tail{Sweep,Neither,Collect}` replacing only `(collect_old,skip)` | d5 | 0.55744 | 27,408 | 1961 / 2387 / 2795 | losses in orig 0x4800-0x6000 (sweep/wallet tails: -45/-59/-104 rfj per chunk) |
| d6: payload-less `Next{Holder,Shared,Wallet{collect}}`, payload `Some(new)` from the argument | d6b | 0.36759 | 27,400 | 1408 / 1819 / 2220 | rfj -787, in 0x2000-0x6000 |
| d7: `Tail` enum with ONE `match` dispatch at the sweep site (wallet in the `Collect` arm) | d7 | 0.18807 | 29,248 | 848 / 1938 / 2459 | +1,848 B and 1 normalized loss (0xbc108); the bool version of this join (w14a71 k1) also re-laid everything |
| d8: `Next{Shared(Option<Pubkey>),Unshared{collect}}` (orig tag values) | d8 | 0.44586 | 29,312 | 1617 / 2132 / 2870 | +1,912 B, 1 normalized loss |
| **d9: `Sharing{Reset(Option<Pubkey>),Keep}`** | d9 | **0.67236** | 27,392 | 2250 / 2600 / 3007 | **byte-identical to `m_il`** (`if let Some(val)=sharing_update`): one fewer `ja` after the sharing CPI |
| v: `validate(..,shared)->Result<(Pubkey,Next)>` | v1 | 0.37036 | 27,648 | 1410 / 1824 / 2229 | as d6, plus the sret tuple |
| h: validate returns `Result<Creator>`, `Creator{Holder,New(Pubkey)}` or `Result<Option<Pubkey>>` or `Result<(Pubkey,bool)>` (11 spellings) | h1n | 0.37601 | 27,352 | 1478 / 2548 / 2992 | frame re-laid (see 3) |
| k: `Kind{Holder,Wallet{cashback}}` / `Option<bool>` for the curve holder and cashback stores (8 spellings) | k1 | 0.56722 | 27,248 | 1924 / 2316 / 2983 | -120 to -150 B, `-fj` -280 |
| mil + 33 sizeknobs-cto.json knobs (repaying the -8 B) | mk_ev_auth_deref and 6 others | 0.67236 | 27,392 | | knobs that are byte-neutral leave it at 27,392 |
| | mk_L_fee_unwrap_again / mk_cu_fee_oldunwrap | 0.66926 | **27,400** | | the only exact-size repays; both lose 0.0045 |

**Mechanism of the d-family losses.** A tag that several later sites test (wallet, sweep, sharing CPI, event) becomes a
phi of constants at the tree join. JumpThreading then threads each later `icmp eq tag,k` through that phi. It
duplicates or re-orders the wallet, sweep and sharing-CPI regions. This is the fold the angle hoped for ("per-arm
constant phis"), but it applies to the tail, not to the validate exit, and the original does not have it. Main's
separate `i1` flags are not threaded, and neither are the original's.

`d9`/`mil` changes exactly one thing (normalized diff, 2 lines). It turns main's `jeq r7,2,+1; ja err` after the
`admin_cto_sharing_config` call into `jne r7,2,err`, which is the original's form at orig 0x4aa0. Main reaches the CPI
88 B earlier than the original (0x4a20 vs 0x4a78). So the faithful repay is +8 B before the CPI, but none of the
catalog knobs adds bytes there neutrally.

## 3. Validate-return sum types reach the original's liveness identity, then lose the frame

`tools/gate.sh` (`webs.py --live-at` the sharing CPI; `data/live-sharingcpi-*.txt`):

| build | high slots (>= 0x8d0) live across the CPI | entry arg spills still live |
| --- | ---: | --- |
| original | 8 | r1 (0x8f0), r2 (0x938) |
| main, mil, d5 | 10 | r1, r2, **r3 holder (0x8e8)**, **r4 fee tag (0x910)** |
| h1 / h1n / h3 (`Result<Creator>` / `Result<Option<Pubkey>>`) | 9 | r1, r2, r4 (r3 dies inside validate, as in the original) |

What h1 gets right:
- The holder argument spill dies inside validate.
- cashback becomes a 2-def validate-exit phi (`[0x910]`, defs 0x1728/0x18a8), like the original's 4-def `[0x958]`.
  The `and` is no longer sunk past the CPI, which is the "+1" of w15a15.
- The post-CPI code has the original's shape: the holder value is loaded before the Err test, and cashback is loaded and
  `&1`-ed after it (orig 0x4a90-0x4ab0).
- The frame top grows to 0xc38, the original's size (main stops at 0xc30).

Why it still loses (`data/allocas-main-vs-h1.diff`):
- The enum payload moves the Pubkey to offset 2 of the `Result`, so SROA splits target into 6/10-byte pieces. Main
  and the original use 7/9.
- Two extra `c.sroa.*` pieces (+16 B of allocas) appear.
- Every aggregate offset below 0x440 moves by -8. The original equals main there: 725/757 multiset matches for main,
  548 for h1.

The cost is `--j` -780. With the frame masked, `-fj` is still -51 (h1n) to -342 (h4b) below main, so no frame fix can
recover these forms. They are bounded below main.

## 4. Verdict and next ideas

- The angle is exhausted. There are 75 builds in 9 families, and the original's tag values rule out a decision enum
  beyond `Option<Option<Pubkey>>`.
- The one source change toward the original found here is the post-CPI `jne r7,2` polarity (d9 = mil, -8 B). It
  needs a faithful +8 B *before* orig 0x4a78, where main is 88 B short. A lane with a pre-CPI size map (for example
  w14a72's sweep-head junk bound: +8 B in 0x22c8-0x2468 is worth +2 M) should price mil plus a pre-CPI +8 B.
- The h-family shows that a validate-return change is what kills the holder argument spill and gives the cashback phi.
  The obstacle is layout only: the Pubkey must stay at offset 1 (7/9 pieces) and no extra piece allocas may appear.
  The obvious layout-keeping form is a holder `&mut bool` out-param with `Result<Pubkey>` kept, and it is already
  priced: w13a38 h2, w14a02 `h2`/`hm`/`hu` and w14a04 hk1+h2, all below main. A lane that wants this lever should start
  from h1's `-fj` and gate numbers, not from a new spelling.

## Tools (`tools/`, experiment only)

- `mv.py <slot> <edits.py>...`: crate copy, exact single-occurrence edits (line count kept), `measure.sh`, one JSON line
  per variant into `res.jsonl`. It keeps `unstripped.so` for LCS/webs.
- `prep.sh <so> <prefix>`: fn.bin, disassembly and window-relative syms for `webs.py`/`calls.py` (w15a15).
- `gate.sh <name>`: the live-at-sharing-CPI gate above.
- `mperm.py <so>...`: w15a08's `relab.bestperm` on the binary spill-set approximation (`binspills`). Main gives 2292.
- `cap.sh <name> <edits|-> <slot>`: raw-IR capture plus w14a118 `rx.py --keep` (post-opt `m.ll`); main reproduces
  `eq_main`.
- `edits/gen*.py`: every variant's EDITS.
