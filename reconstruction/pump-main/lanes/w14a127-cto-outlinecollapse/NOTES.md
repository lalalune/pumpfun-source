# w14a127-cto-outlinecollapse: why the to_string outline spellings collapse admin_cto

Target: 0x22a10 `admin_cto::execute`, main ebe5387e1 (0.67316, 3123 slots, M 2247 @ 27,400 B). This is a notes-only result: nothing beats main.

## Finding
The four validate holder spellings `hopt.unwrap_or(false)`, `matches!(hopt,Some(true))`, `hopt.unwrap_or_default()` and
`hopt.is_some_and(|h|h)` give byte-identical code (fn.bin md5 14e52240). They reproduce the original's cold-callsite pattern
(bfi: 307/312 to_string callsites 0.0176/0.0179 cold, 296 hot), and the holder test becomes the original's `and i8 h,1`.
They also collapse the function to M 1373 @ 27,416 B.

**Root cause:** an entry copy of `new` that is never forwarded.
- The `(new,)` tuple behind `let args=&(new,)` keeps a 32 B alloca `%_45.sroa.5`, filled by a memcpy from `%new+1` at entry.
- The sharing arm's `Some(args.0)` memcpy (bb20 -> `%_553.sroa.6`) reads from that copy instead of from `%new`. On main the
  same memcpy reads `%new` directly.
- MemCpyOpt keeps the copy because the MemorySSA clobber walk from bb20 back to entry runs into the walk limit. The proof:
  `opt -O3 -memssa-check-limit=10000` (an experiment-only flag) removes the alloca.

The copy has three effects:
1. +160 B of code.
2. A reload at the head of the validate-exit join `%bb56.i`. MachineBlockPlacement then moves the 119-block second
   validate arm chain (`%bb9.i112`..`%bb93.i`) behind the join. This is the same J flip as #3511 (jfix3 = jfix2 with
   `%bb5.i\d*`).
3. The 32 B frame object stays allocated even when nothing uses it, so the middle of the frame shifts by 0x20.

## Decomposition (one row covers all four spellings, M = scorer tokens)
| form | bytes | M | fM | rM | rfjM | regonly | fbound fR / rfR |
|---|---:|---:|---:|---:|---:|---:|---|
| main ebe5387 | 27400 | 2247 | 2346 | 2562 | 2810 | 0.76753 | 2295 / 2623 |
| spelling (v_uo = v_mt = v_ud = v_isa) | 27416 | 1373 | 1628 | 1557 | 2137 | 0.46631 | 1568 / 1939 |
| + J relayout (jfix3) | 27424 | 1620 | 2158 | 1932 | 2709 | 0.57853 | 2043 / 2415 |
| + IR: copy forwarded (bb20 reads %new+1, entry memcpy/lifetimes dropped) | 27256 | 1633 | 2256 | 1832 | 2768 | - | 2102 / 2453 |
| + IR: dead 32 B alloca also deleted | 27256 | 1968 | 2256 | 2293 | 2768 | 0.6888 | 2101 / 2453 |

How the 874 M loss splits:
- J layout flip: about 247 M.
- The copy's frame object: about 335 M.
- Copy code and skeleton: about 13 M.
- Remainder against main, even with the copy gone: 279 M (about 90 frame by fM, about 270 register by rM), and the form is
  144 B short of 27,400.

## Source screens (raw-IR capture + rx oracle, ebe5387)
| name | change (on top of hopt.unwrap_or(false)) | bytes | M | note |
|---|---|---:|---:|---|
| u_after | `args` after the validate call | 27504 | 1535 | copy gone, J flip stays (moved 121) |
| u_none | `Some(new)`, no args | 27496 | 1534 | same |
| u_inarm | `args` inside the else arm | 27496 | 1534 | same |
| u_val | `let args=(new,)` by value | 27496 | 1534 | same |
| u_top | `args` at block top | 27416 | 1373 | = v_uo |
| m_after | main spelling, `args` after validate | 27376 | 1603 | J flip, moved 119 |

No ordinary spelling found here gives the forwarded IR. Even that IR form is 279 M below main and 144 B short, and the
reachable forms stay more than 60 M below main under both bounds (relaid 1620, regonly-of-relaid about 1983). The kill
criterion is met. The origfill fills (w14a123) target a different base (call-site noinline, 26,992 B) and were not
applicable.

## Next ideas
- A source form that removes the `(new,)` temporary entirely while keeping the copy-free sharing payload. The candidates
  above all change something else that triggers the flip, so the flip has a second trigger besides the copy.
- Diagnose the u_after flip (no copy, still a J reload) with `-debug-only=block-placement`.

Ledger keys: `0x22a10-w14-ebe5387-outlinecollapse-{spell4,collapse-decomp,argsplace}-v1`.
Tools: `tools/llcs.py` (llc-only scoring of an edited post-opt module), `tools/lay.py` (block layout from llc asm),
`tools/offmap.py` (frame-offset shift map against orig), `tools/an.sh`, `tools/mine.py` (genes).
