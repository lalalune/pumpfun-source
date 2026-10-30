# w14a08-cto-outlinefill: fills for the outline basin (RAR + 1:2 weights) on admin_cto::execute

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 308b545f1 (0.63062) for the full screen, then cef0574cf (0.63421) to re-check the key forms.
Continues w13a43-cto-outline306 (#3166, next idea 3) and w13a41-cto-entrycopy3 (#3160, next idea 2).
Ledger keys: `0x22a10-w14-308b545-outlinefill-*-v1` (77 rows) and `0x22a10-w14-cef0574-outlinefill-*-v1` (8 rows).

**Result: no fill works. The angle is exhausted on current main. No source change.**

Every number comes from the raw-IR capture + `opt -O3` + extracted-`llc` oracle (w13a43 `src.sh`/`brw.py`).
On both mains it reproduces the baseline exactly (0.63062 and 0.63421 at 27,400 B). For each trial, `tools/fw.py`
builds the source variant, captures the raw IR once, and scores it twice: unweighted, and with Some:None = 1:2 on
validate's 306 tag switch. That switch is the outline stand-in, located automatically after `lifetime.start(%t)`.

## 1. Compare off-pin trials by matched instructions, not by ratio

`ratio = 2M / (3339 + n)`, where M is the number of matched original instructions and n is the candidate's
instruction count. At the pin, n = 3339, so ratio = M / 3339. A shorter candidate gets a higher ratio for the same M.
A pinned candidate can only beat main by matching more original instructions. Filler that matches nothing
leaves the pinned ratio at M / 3339.

| form | bytes | ratio | n | **M** | M frame-masked |
| --- | ---: | ---: | ---: | ---: | ---: |
| main 308b545 | 27,400 | 0.63062 | 3,337 | **2,105** | 2,254 |
| RAR + 1:2 weights (308b545) | 26,920 | 0.63161 | 3,279 | **2,090** | 2,292 |
| main cef0574 | 27,400 | 0.63421 | 3,337 | **2,117** | 2,258 |
| RAR + 1:2 weights (cef0574) | 26,920 | 0.63433 | 3,279 | **2,099** (1:3, 2:5, 3:7, 1:10, 1:100: 2,094-2,099) | 2,296 |

The "+0.001 at -480 B" of w13a43 is a size artifact. The outline basin matches **15-23 fewer** original
instructions than main. A 480 B fill would have to add more than that many matched instructions without moving
anything else. `tools/rep.py` and `tools/tab.py` print M for every trial.

## 2. The fill screen (308b545; full table in `data/tab_308_w12.txt`)

These are 63 single genes on RAR (the 56 applicable knobs of `$SWARM/w11/sizeknobs-cto.json` plus the faithful entry forms),
14 combinations and 6 `args` placements, each under the 1:2 weights. Columns: dB against RAR+w12 (26,920 B), dM against M = 2,090,
masked M, and fz, the share of aligned r10 offsets equal to RAR+w12 (1.00 = same frame).

| fill | dB | dM | masked M | fz | note |
| --- | ---: | ---: | ---: | ---: | --- |
| 16 knobs (st_ql_first, ev_auth_deref, pu_match, ...) | 0 | 0 | 2,292 | 1.00 | byte-identical, no size |
| wl_ts_clockvar, g_w_clock_local | +16 | -1 | 2,291 | 1.00 | the only cheap positive-size knobs |
| ev_cb_local / g_fee_unwrap, cu_fee_oldunwrap, L_fee_unwrap_again | +8 | -5 / -16 | | 1.00 | |
| w_ev_creator_first | +64 | -15 | 2,277 | 1.00 | |
| s_frozen_first, sig_mint_acct | +48 / +40 | -111 / -117 | | 1.00 | |
| v_fee_split / p_ev_ts_last / w_create_rev / ev_nc_target | +216 / +256 / +272 / +80 | -224 / -410 / -421 / -814 | | ≤0.63 | the only large fills |
| **V1** (holder_key by value) | -8 | **-213** | **2,320** | 0.60 | frame-blind **+28 over RAR+w12, +66 over main** |
| V2N (both keys by value, validate reads `new`) | -8 | -244 | 2,320 | 0.63 | |
| B3 (t28's curve bools before `global_quote`) | -16 | -172 | 2,191 | 0.82 | +17 matched in orig 0x0-0x1900, -127 in the clone run |
| QLIN (t22's inline `global_quote`) | -120 | -240 | 2,295 | 0.69 | |
| HK0 (plain PDA tuple) / VS (sk by value) | 0 | -252 / -246 | 2,292 | 0.60 / 0.57 | **pure frame shift** (-40 / +32), code identical |
| t22 on RAR (V2+HK0+QLIN) / e3 = t8 on RAR (V2+HK0) / t28 on RAR (+B3) | +176 / +168 / +304 | -286 / -357 / -755 | | ≤0.70 | |
| N289 (nested 289, the source threading form) | +24 | -344 | 2,239 | 0.64 | |
| PDA-first (holder_key before `shared`, w14a02 lead) | +48 | -218 | 2,065 | 0.91 | |
| frame-cancelling combos V1+HK0, V2N+HK0, VS+HK0, V1+HK0+QLIN, ... | | -89 to -297 | ≤2,320 | 0.57-0.79 | the shifts do not cancel: spill slots are reassigned, not just shifted |
| `args=&(new,)` elsewhere (fn head, before quote, before shared, after sk, after CtoState) | | -77 to -316 | | | only RAR's spot (right after `quote_locked`) holds the basin, as w14a07 found too |

Ranking at exactly 27,400 B: none. The positive-size knobs that keep the frame add at most +128 B together, for at least -40 M.
Every fill large enough to matter (+80 to +304 B) costs 80 to 800 matched instructions. All the faithful fills (V1, V2, V2N, B3, QLIN, HK0, the t8/t22/t28 forms)
move the frame (fz 0.57-0.82). `tools/regcmp.py` puts the loss in the clone-run basin, orig 0x1900-0x4b00 (B3: -127, V1: -123, t22: -148 per
0x1900 bin). The cef0574 re-check (`data/tab_cef_w12.txt`) gives the same order: RAR+w12 M 2,099, ev_cb_local -5, w_ev_creator_first -16,
B3 -177, V1 -210 (masked 2,325, main 2,258), t22 -295.

## 3. Mechanism

- With the outline set, the original's validate region is about 60-80 instructions longer than ours (`tools/gapmap.py`, orig 0x0-0x1900).
  The candidates for that code are the by-value entry copies of w13a41 (new pieces, sk, holder_key) and the curve bools spilled before `global_quote`.
- Each of those forms adds or removes a 32/40/8 B stack object (or a spill) ahead of the spill area. The greedy-RA spill-slot assignment then
  changes for most of the function (`tools/offd.py`: V1 keeps only 60% of RAR+w12's r10 offsets). The code shape is closer to the
  original (V1: masked M 2,320 against main's 2,254), but the raw M drops by 200 or more.
- So the outline basin needs a frame/spill-slot fix before any faithful fill can pay. Per w13a35, a source-level frame fix is
  not available. The fill itself is not the blocker.

## 4. Hand-off to w14a07-cto-cold306

- The best fill-plus-weights form is **no fill**: RAR + 1:2 at 26,920 B, M 2,099 on cef0574, 18 below main's 2,117. No catalog
  knob or faithful form screened here closes that gap at 27,400 B. w14a07's f2 source form (`has:bool`) reaches the same ceiling
  (0.63261 at 26,912 B, about M 2,093), so it would also need +24 matched instructions from its fill.
- Lead for a frame or RA lane: RAR + V1 + outline is the best frame-blind form seen (masked M 2,325 on cef0574, +67 over main). It loses
  only through spill-slot assignment (fz 0.60). An IR or MIR experiment that pins the spill-slot order to RAR+w12's while keeping V1's code
  would measure what that is worth.

## Tools (`tools/`; the w13a43 oracle with paths repointed, plus these new ones)

- `fw.py <name> <genes> [work] [wts]`: variant from `var/m3` plus genes from `fg.py`, a single raw-IR capture, scored unweighted and with
  weights on validate's 306 switch (located automatically). Appends to `res.jsonl` and deletes the variant and its IR (`KEEPIR=1` keeps the IR).
- `fg.py`: the gene library (RAR, V1, V2, V2N, VS, VA, HK0, B3, QLIN, N289, PDA, ARG* placements, plus every catalog knob as `K:<name>`).
- `batch.py <list>`: runs `fw.py` two at a time. `tab.py [ref] [w]`: dB, M, dM, masked M and frame identity against a reference.
  `rep.py`: ratio and M per trial. `recall.py`: writes the ledger rows.
- `offd.py A B`: frame-offset delta histogram over aligned instructions. `gapmap.py orig cand lo hi`: unmatched runs with addresses.
  `regdiff.py orig A B lo hi`: original instructions matched in A but not in B.
- `brw.py` is w13a43's, with opt's stderr surfaced. Its line argument is a **0-based** index into the raw IR.
- Data: `data/res_*.jsonl` (raw results) and `data/tab_*.txt` (tables).
