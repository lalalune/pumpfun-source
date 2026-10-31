# w15a32-cto-lbasinweight: spill-weight levers for the L basin (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 9120883a9
(admin_cto 0.67376, 3,124 slots, M 2,249; `programs/` unchanged on e61121452). Continues w15a16-cto-mpermrank (#3740), next
idea 1: get L's code gain without its spill-window rotation. L = `mv_5_1+t1n+m_crl2+devol` (cashback before creator in the
CtoState literal, `if new.is_none()` holder test, `let cr=` creator binding, both read_volatile placeholders removed).
Ledger: approach `lbasinweight`, keys `0x22a10-w15-9120883-lbw-*-v1`.

## 1. Exact spill-colour oracle (new tool)

`sscpatch/build.sh <out>` builds a private llc (copy of the shared llvm-dbg build, about 2 minutes, 445 MB) whose
StackSlotColoring reads `SSC_WSET="ss:=w,ss:+d,..."` and sets or offsets the weight of spill interval `SS#ss` before the
weight sort. The code is untouched, so the result is exactly the binary that the same code would give with that colour
order. Without the variable the private llc reproduces main (0.67376) and L (0.66926) byte for byte.

- `tools/sscw.py <m.ll> <tag> <spec>...`: one llc run per spec, scored like measure.sh (M, ratio, slots, bytes).
- `tools/sstab.py <name>`: per interval table: SS#, weight, live range, colour fi, final offset, original-offset vote,
  first referencing instruction. Needs `-stop-before=stack-slot-coloring` and `-stop-after=prologepilog` MIR plus a
  `-debug-only=stack-slot-coloring` log.
- `tools/ordclimb.py`: swap/move climb over the rank order of the top intervals (slow under load; not finished).
- `data/ssc-table-9120883.txt`: the tables for main and L.

Colours are handed out in descending weight; colour k sits at `-2264 - 8k` in both main and L.

## 2. Why L loses 15 M of frame

| interval | main SS# | main w | L SS# | L w | cause of the difference |
| --- | --- | ---: | --- | ---: | --- |
| accounts ptr | 180 | 2.0577 | 181 | 2.0577 | |
| `new` ptr (stack arg) | 260 | 2.0080 | 261 | 2.0080 | |
| holder arg (r3) | 183 | 2.0039 | 184 | **2.3789** | L reloads it again in validate bb6.i (`and -3`, freq 0.375); main keeps the bb8 reload in r5 |
| sret (r1) | 178 | 2.0000 | 179 | 2.0000 | L keeps r1 in r6 and spills it in bb8 |
| bonding-curve data ptr | 321 | 1.0463 | 299 | **0.4262** | L keeps it in r9 until bb13 (freq 0.375); main spills it in bb10 (freq 1) |
| fee_configurable byte | 297 | 1.3995 | 297 | 0.3995 | main spills in bb12, L in bb13 |
| `new` tag byte | 284 | 0.6365 | 287 | 1.6372 | L spills in bb12 (freq 1), main in bb13 |

The holder arg becomes the heaviest interval, takes colour c0 (`-2264`) and pushes accounts, `new` and the rest one colour
down: the w15a16 rotation. Exact oracle on L (code fixed):

| L + weight change | M | ratio | slots |
| --- | ---: | ---: | ---: |
| none (L) | 2,234 | 0.66926 | 3,075 |
| holder := 2.0039 (below `new`) | 2,248 | 0.67346 | 3,072 |
| holder anywhere below accounts (2.03 .. 0.41) | 2,246-2,249 | | |
| holder := 1.3789 (bb8 reload gone) | 2,249 | 0.67376 | 3,072 |
| holder := 2.0039, bc ptr := 1.046 | **2,261** | **0.67735** | 3,070 |
| holder := 2.0039, fee_configurable byte := 1.3995 | 2,260 | 0.67705 | 3,069 |
| main's rank order mapped onto L's intervals | 2,261 | 0.67735 | 3,072 |
| accounts := 2.4327 (above holder) | 2,247 | | |
| `new` / sret above holder | 2,235 / 2,232 | | |
| new tag := 0.637 | 2,230 | | |

So L needs two RA facts back from main to beat main: the holder arg must not be reloaded twice in the validate head, and
the bonding-curve pointer (or the fee_configurable byte) must be spilled on the freq-1 entry path. Both come from the same
schedule change: with cashback loaded before the creator memcpy, the cashback select diamond (bb10/bb11) is scheduled
before the max_fee, holder_enabled, mayhem and holder_reward loads, which then land in bb12 and take r5 (holder) and keep
r9 (bc) live into bb13.

## 3. Source screens on L

(in progress)
