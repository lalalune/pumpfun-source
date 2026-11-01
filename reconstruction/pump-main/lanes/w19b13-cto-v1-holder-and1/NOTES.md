# w19b13-cto-v1-holder-and1: the original's holder test in V1, the 307 key in V4

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Wave 19 shim track. Ledger approach `v1-holder-and1`, keys
`0x22a10-w19-<sha7>-v1holderand1-<item>-v1`. Tools are in `tools/`; `tools/genes.py` holds every source gene, each a text
replacement on main's `admin_cto.rs`.

## Result

| form | base | M @ bytes | note |
|---|---|---|---|
| and-1 holder + V4 + pads (PR #4149, `c1`/`c3`) | 0325ac1d5 (2,341) | 2,345 @27,400 (measure.sh) | differential 388/0, zero losses |
| same | 882755412 (2,346) | 2,350 @27,400 (measure.sh) | zero losses; land.py exit 3 twice: lines 289/306/312/339 kept moving |
| same | 1053a7fb8 (2,353) | 2,348 @27,392 (slim oracle) | the T1 colour LP (#4153) and fill moves changed the base: needs a re-tune |
| V4 alone (`v4s`) | 9357bd934 (2,354) | 2,357 @27,400 (measure.sh) | PR #4165 |
| V4 alone minus one fill read (`v4r+d312`) | 665ffe46b (2,367) | 2,370 @27,400 (measure.sh) | PR #4165; `new` was a reference on a596efe59 |

**Landing.** land.py did not merge either PR. #4149 lost the queue twice (exit 3). Its genes reached main through the w17a36 train
#4162 (M 2,389, 0.71548), integrated by #4167 at b4331b4d1, so `hopt.unwrap_or(false)`, both 0.625 weights, the `pt8` curve store,
the single-bit 306 test, the 306 error-path read and the 307 key are on main bc659cc44. #4149 and #4165 are closed, with no
further programs/ change from this lane.

Checked with this lane's capture of main bc659cc44 (slim oracle): M 2,389, 0.71548, 27,400 B. V1 has one `and64 r5,1` at 0x628, then
`jeq r5,0,+1; ja +0x59`; the 306 tag test has `and64 r1,1` at 0x748; the 307 key loads `[r10-0x4a0]`, `-0x4a8`, `-0x4b0` at 0x12d8-0x12f8.

## 1. The original's holder test (V1)

The IR form is one `%h = and i8 %hopt, 1` at the head of the block after the mayhem test, with `icmp eq %h,0` used by the 289,
!hr and shared-arm branches. Source: `let holder=hopt.unwrap_or(false);` after the mayhem test, and `hopt.unwrap_or(false)` at
the shared arm. This gives `and64 rX,1` once, then `jeq rX,0,+1; ja`, as at the original's 0x618, 0x720 and 0x1840. Moving it
inside the block changes nothing.

**Why every earlier and-1 basin collapsed.** `BranchProbabilityInfo::calcZeroHeuristics` returns no probability for a compare
of `and x, <single bit>`, so the test goes from the zero heuristic's 12:20 to 50:50. Every block frequency after validate then
drops by 0.85. Spill weights in T1, C1 and W2 scale with them, but entry intervals do not, so SS ranks flip and the T1/C1 slots
shift by one colour (M -39 to -51; `tools/ivmap.py` maps intervals between two builds and shows the flips).
**Fix: `expect_p(holder,true,0.625)` on the 289 and shared-arm tests**, which reproduces 12:20 exactly. The 289 weight must be
0.375 on the error edge. Grid (post-opt, main e60774c17, 2,338):

| 289 error edge | shared arm 0.35-0.45 |
|---|---|
| 0.3 | 2,337 @27,352 |
| 0.35 | 2,328 @27,344 |
| **0.375** | **2,338 @27,360** |
| 0.4 | 2,328 @27,352 |
| 0.45 / 0.5 | 2,297 |
| 0.55+ | below 1,780 |

Shared arm at 0.25-0.3 or at 0.5+ loses 2-22 M.

Forms on e60774c17 (M 2,338 at 27,400; post-opt unless marked src):

| form | M @ bytes | all-masked | note |
|---|---|---|---|
| late and-1, no weights | 2,287 @27,232 | -4 | the 0.85 scale above |
| **late and-1, weights** (`h1`, src `s1`, same sig) | **2,338 @27,360** | +1 | 40 B of room, RA unchanged |
| + curve store on the same value | 2,291 @27,344 | -6 | keep the store's own and-1 with `pt8` |
| early and-1 (`hopt.unwrap_or` everywhere) | 2,058 @27,200 | -12 | |
| late and-1, cashback at its use, no early `and -3` (`h6`) | 2,016 @27,272 | **+20** | best skeleton, C1 all-masked +35; sret stays in r7 instead of its spill, T1 -104, C1 -80 |
| same, cashback in the holder block | 1,506 @27,256 | -102 | |
| same, cashback at the validate join | 1,652 @27,224 | -709 | tail layout |
| `h6` on 882755412 | 2,021 @27,304 | +17 | still -329 |
| early `and -3`, cashback zext not sunk | 2,343 @27,392 vs 2,350 | -1 | |

Other findings:

- **Block order.** The original's `jne r8,0,+0x57` needs the 289 error block next after the hr-arm test in IR. rustc's
  first-reference order gives that only when the hr test's other edge is a join reachable from the arm (`if hr&&!holder{..}`,
  RPO trick), not with `if` or `match` arms. At post-opt it is -1 M, -8 B, all-masked +1 (`swap87`). No source was tried.
- **306 tag test.** `(*(&new as *const Option<Pubkey> as *const u8)&1)==0` gives `and64 r1,1` as at 0x738. V1 all-masked +1,
  exact 0, +8 B. On the old base (without weights) it flipped C1 by -13; with weights it is neutral.
- **Volatile reads inside validate.** On a non-error path a read blocks memcpy forwarding of `new` and `creator` (M 1,612, src
  `s3` and `r1`), since it adds a MemoryDef on the walk, which w17a30's memssa-limit row describes. Error-path reads are safe,
  so a read on the 306 error path stands in for the original's dead reload at 0x710: E289's first `jeq r0,0,+0x22` then has the
  original's displacement (+1).
- **Fill scans.** Single fill-read cells on the and-1 base are flat: one cell gives +1 at 27,400 (`pad306`), and a second round
  gives nothing (`tools/ps.py`, `tools/h8.py`). `tools/padsim.py` and `tools/padls.py` simulate fill moves without llc (LCS proxy,
  5 ms): they suggest +3 from moves, but those need reads at E1 before the PDA or on non-error paths.
- **`!prof` scan.** A scan of about 1,000 cells on the and-1 base found nothing above 2,338 at or below 27,400 B.

## 2. The 307 key from the t stack slot (V4)

The original loads the key from `[r10-0x4a0..-0x4b8]` at 0x13f0-0x1428. Main reads `[r9+0x18..0]` because MemCpyOpt forwards
`memcpy(k <- t)` to `new+1`.

| form | M delta | why |
|---|---|---|
| whole copy from `t` (post-opt) | -87 (-499 on d493b88f4) | `new+1` no longer live in that block: r9 goes elsewhere, W2 -45 |
| whole copy + keep-alive read of `new+1` (post-opt) | **+4**, +8 B | |
| `ptp(t)`, or `read_volatile(t)` (volatile memcpy) | -488 | a volatile memcpy is a capture in CaptureTracking; t escaping blocks the creator forwarding |
| volatile keep-alive read of `new+1` in the source | -488 | same capture effect on `new` |
| four word copies, word 0 from `new+1` | -3 | the scheduler moves the `new+1` load first (r1, then r4) |
| **24 B copy from `t+8`, then word 0 from `new+1`** | **+3**, 0 B | original's load/store sequence; `new+1`'s interval is unchanged |

MemCpyOpt 18 forwards only when `M.source == MDep.dest`, so a copy from `t+8` is not forwarded.

## 3. Next

- Re-tune `vh+e23+p755+tag1+pad306` on current main. `tools/reland.sh` re-applies the genes after a merge. Check the size first:
  the and-1 genes are -40 B before fills, and fill positions move every few landings.
- `h6` frees one register before C1 and has C1 all-masked +35. Keeping the sret spill while dropping the early `!holder` is the
  open RA question.
- The error phi r9/r8 tokens (12 sites) stay. `!holder` no longer has branch uses, only the cashback at bb30, so w18a01's chain
  (cashback phi and `do_coin` in r8 free r9) is a step shorter now.
