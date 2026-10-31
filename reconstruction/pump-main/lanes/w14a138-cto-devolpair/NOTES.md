# w14a138-cto-devolpair: both validate placeholders out at once (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main ebe5387e1 (0.67316, 3,123 slots, M 2,247).
Continues w14a115-cto-devol338st (#3510) and w14a119-cto-devol334t1 (#3575), plus w14a121-cto-delwin's (#3524) next idea 2.
Ledger approach `devolpair`, keys `0x22a10-w14-ebe5387-devolpair-<variant>-v1`.

All numbers come from the raw-IR oracle (capraw identity capture of the varied crate, then opt -O3 and llc, scored with
masked tokens; `tools/scr3.py`, a copy of w14a119's scr2 pointed at this lane). M is the count of matched masked tokens and
ratio = 2M/(6676+(bytes-27400)/8). To tie main, a variant needs 27,400 B and M >= 2,247.

The base for every row is **w14a115's devol338st source**: `validate(st:&mut CtoState,..)`, `let hr=st.holder_reward;`
reused at line 298, and `st.fee_configurable=false;` in place of the line-338 `read_volatile`. Gene names are from the
stitch13 / w14a119 library (`tools/genes*.py`, `tools/mine108.py`) plus `q_*` validate spellings in `tools/genes_p.py`.

## Pair table (devol338st base)

| key | genes | bytes | dB | M | dM |
| --- | --- | ---: | ---: | ---: | ---: |
| P0 | (devol338st only) | 27400 | 0 | 2247 | 0 |
| P1 | vol334_back+I6s | 27400 | 0 | 2244 | -3 |
| P2 | vol334_back+I6 (VI6) | 27408 | +8 | 2247 | 0 |
| P3 | vol334_back | 27392 | -8 | 2246 | -1 |

P0 ties main exactly (w14a115). P1 and P2 reproduce w14a119's I6s / VI6 numbers on the devol338st base, so the 338 store
and the 334 removal do not interact.

## The 334 placeholder is 8 bytes of pure fill (P3 vs P0)

P3 differs from P0 in exactly one instruction: P0's `ldxb r1,[r10-0x6a0]` at 0x1580 (the line-334 volatile, the head of the
fee_configurable test block) is gone, and every later jump target shifts by 8. Nothing else in the window changes. So the
placeholder's whole effect is 8 B of fill whose +1 M comes from re-aligning jumps that cross 0x1580.

## Insertion map (`tools/insmap.py`, new oracle; inverse of w14a119's delmap.py)

`insmap.py fn.bin out.json` inserts one non-matching 8-byte slot before each instruction in turn, re-fixes the jumps and
reports M. On P3 (M 2,246) a junk slot anywhere in **0x180-0x1a0, 0x6d8-0x8b8, 0x978-0xeb8, 0xf10-0x14a8, 0x1588-0x18d0,
0x19c0-0x1a90** (519 positions) gives back M 2,247. No single insertion gives 2,248. So any ordinary source change that adds
exactly one instruction in the validate region (0x6d8-0x18d0) and changes nothing else ties main with no placeholder; one
whose instruction also matches the original would beat it.

## Screens

See the batch tables below (filled in as the screens finish).
