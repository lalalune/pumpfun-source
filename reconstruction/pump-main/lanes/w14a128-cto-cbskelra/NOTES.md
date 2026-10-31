# w14a128-cto-cbskelra: the sharing-CPI "skeleton" leads are difflib artifacts

Target `0x22a10` `admin_cto::execute`, main ebe5387e1 (0.67316, 3,123 slots, 27,400 B, difflib M 2,247).
This lane relaunches w14a124-cto-cbskelra, which died with no results. Ledger approach `cbskelra`, keys
`0x22a10-w14-ebe5387-cbskelra-*` and `0x22a10-w14-13fe453-cbskelra-*`.

Angle: two lanes reported a skeleton lead in the first sharing-CPI clone run (orig 0x3c00-0x4800). The leads were
ev_cb_local (w14a108, rfjM +62) and F0 "curve bools first" (w14a106, L2 +62, with +58 in 0x4000-0x4800, "main lays the
first clone run one block early"). Neither lead was priced.

## Result: no placement gap exists

Every skeleton metric used so far (skM, rfjM, L2, sk_oo) is a `difflib.SequenceMatcher` match count. SequenceMatcher
is greedy: it takes the longest block first, so it is not an LCS. A few single-instruction changes can flip how it aligns
a 138-instruction run of near-identical clone blocks (each clone is an Rc increment, an overflow trap and 5 field
loads/spills). The new `tools/lcs.py` computes the TRUE LCS (bit-parallel, exact, ~30 ms per mask) under the same masks:

| capture | difflib rfj | true-LCS rfj | true-LCS --- (real tokens) |
| --- | ---: | ---: | ---: |
| main ebe5387 | 2,810 | **3,007** | 2,252 (difflib M 2,247) |
| ev_cb_local @27,392 | 2,872 (+62) | **3,006 (-1)** | 2,232 (-20) |
| w14a106 m0 (13fe453) | 2,787 (L2) | 3,007 | 2,250 |
| w14a106 F0 @27,352 | 2,849 (+62) | **3,009 (+2)** | 2,144 |
| w14a106 GPF @27,344 | 2,883 (+96) | 3,028 (+21, all in entry chunk 0x0) | 2,054 |

In orig 0x3a00-0x4a00, true LCS is 451/511 for both main and ev_cb_local. The true-LCS traceback (`tools/lcsalign.py`)
of main has no unmatched run longer than 11 tokens in that range, so the first sharing clone run is already where the
original has it. Main and ev_cb_local skeletons differ only by about 30 single inserts/deletes: the cashback spill
`[r10-0x908]`, its reload at the curve store, and recolouring.

ev_cb_local's real loss, from the true-LCS factorial (ev minus main): `---` -20, `--j` -14, `-f-` -8, `-fj` -4,
`r--` -14, `rf-` -6, `rfj` -1. Roughly, about 10 tokens are frame-slot drift from the extra cashback spill slot, about
6 are jump drift from the -8 B, and about 4 are registers. Nothing about placement is left to recover, so step (c)
(repairing ev_cb_local's block sizes) has no target.

## Screens of the cashback-flow spellings (raw-IR capture + rx oracle, ebe5387)

| variant | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| main (m0, eq_main) | 27,400 | 2,247 | 0.67316 |
| ev_cb_local (event `is_cashback_coin:cashback`) | 27,392 | 2,222 | 0.66577 |
| cb_curveread (event takes `curve.is_cashback_coin` read in the curve-store block) | 27,424 | 2,232 | 0.66836 |
| cb_aftervalidate (`let cashback` after `validate(..)?`) | 27,120 | 1,763 | 0.53094 |
| cb_aftershared (`let cashback` at the end of the tuple block) | 27,248 | 1,832 | 0.55040 |
| ev_cb_local + cb_aftershared | 27,256 | 1,832 | 0.55032 |

True-LCS rfj for these: cb_curveread 3,006, cb_aftershared 2,994, cbev_aftershared 2,993 (main 3,007). Moving the
`cashback` let re-lays out the head (-150..-280 B). Reading it at the curve store adds 24 B and loses 15 M.

## Census: where real skeleton room is (true LCS over 3,511 distinct w13/w14 captures)

`tools/scan.py` scored every `rx/*/fn.bin` in the w13/w14 lane out dirs (`census-top-rfj.tsv`):
- The true-LCS skeleton maximum is **3,038** (w14a85 s1reload sa1__364). That is only +31 over main.
- The true-M maximum is 2,253 (w14a108 crl2 @27,472). Nine captures at 27,400 B tie main's 2,252.
- Per-chunk traceback (`tools/lcschunk.py`) shows every capture above 3,020 gains in one of two places:
  - orig 0x4000-0x4800 (+16..+28): the s1 family (w14a85 s1reload, w14a81 s1colour, w14a74 s1tagjoin, w14a122 r_s1,
    w14a87 S3). That is the original's per-clone reload of the accounts pointer from `[r10-0x8d8]`. Those lanes priced it:
    it needs the original register naming of the whole region and costs 48-900 real tokens.
  - the entry chunk 0x0-0x800 (+21..+34): PDA-first / GP head order (w14a93, w14a77, w13a28).
- `main-history-lcs.txt` covers all 76 landed mains. The true-LCS skeleton stayed flat at 2,978-3,007 while true M rose
  from 2,008 to 2,252: every wave-13/14 gain was registers and frame, not structure. The old main a6412c2 still had the
  s1-shaped +21 at 0x4000, which was lost by 53abf28.
- Main's whole-function true-LCS factorial: `---` 2,252, `--j` 2,364, `-f-` 2,483, `-fj` 2,594, `r--` 2,600,
  `r-j` 2,722, `rf-` 2,888, `rfj` 3,007 (orig 3,339 tokens). The remaining gap is about 330 scattered skeleton tokens (no
  run over 23; list in the ledger row `cbskelra-lcsmap`), plus registers, frame and jumps.

**Rule for other lanes:** before you call a difflib skM/L2/rfj delta a structural lead, re-check it with `tools/lcs.py`
(or `lcschunk.py` per chunk). difflib flips of ±60 tokens are common in the clone runs.

## Tools (`tools/`, experiment only; `oracle.py`, `xled.py`, `dis.py` copied from w14a108 / w14a80)

- `lcs.py <cand>... [--lo --hi --clo --chi --masks ---,rfj]`: true LCS per mask. `cand` is `main`, a .so, a fn.bin or an rx name.
- `lcsalign.py <cand> olo ohi clo chi [mask] [minrun]`: DP traceback that lists unmatched runs.
- `lcschunk.py <ref> <cand>... [--mask] [--sz]`: true-LCS matched orig tokens per chunk, as cand minus ref.
- `fact.py <cand>... [--lo --hi]`: difflib factorial (8 masks), whole function and per range.
- `scan.py <out.tsv> <fn.bin>...`: census.
