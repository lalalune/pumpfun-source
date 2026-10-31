# w14a72-cto-rescan304: re-read / Rc-swap / move-a-re-read rescan on main 39eb377 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `39eb377aa` (#3386 feeedge: 0.66477, 3,230 slots, M 2,219). The angle was written for 304b03a; main moved
to 39eb377 before the lane started, so every screen here ran on 39eb377.
Continues w14a43-cto-tcfrescan (#3380) and w14a41-cto-derefreread (#3332). Ledger approach `rescan304`,
keys `0x22a10-w14-39eb377-rescan304-*`.

`M` = matched tokens; `ratio = 2M / (3339 + n)` with `n = bytes/8 - 88` (88 lddw). Only M counts at the pin.

## Result 1: drop the pump_fees owner re-read, pay its 16 B back with two old +8 B knobs

| | main 39eb377 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.66477 | **0.66507** |
| M | 2,219 | **2,220** |
| slots_diff | 3,230 | **3,228** |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses, 0 gains |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | e41fae3c34c0472c |

Change (three spellings, line count unchanged):
- rO: sharing CPI `program:` literal `owner:a.pump_fees.owner` -> `owner:x.owner` (undoes #3361's re-read). On 39eb377 this is
  **-16 B and +2 M** (0.66557 @ 27,384, M 2,221). After #3386 the re-read is no longer free.
- wl: wallet `if !a.current_creator.is_writable` -> `if a.current_creator.is_writable==false` (+8 B; #3379 had taken it out).
- sm: `if let Some(val)=sharing_update{..}` -> `match sharing_update{Some(val)=>{..}None=>{}}` (+8 B; #3369 had taken it out).

## Screens on 39eb377 (all post-opt llc oracle on a raw-IR capture; `eq_main` true on the empty edit)

| step | runs | best at 27,400 | main |
| --- | ---: | --- | ---: |
| (1) re-read singles + within-clone pairs, all 18 inlined clones (`allclones.py` now finds 18) | 600 | = main (next 0.66387) | M 2,219 |
| (2) Rc-order swap / literal per clone, source captures (10 TCF, 8 sharing incl. CpiContext pump_fees and sharing_config literals) | 19 | src_evL ties M 2,219 (not eq_main, same slots); progL / event_authority 2,218 | |
| (2b) each Rc base + one re-read over all clones | 2,472 | none above 2,219 | |
| (4) remove one re-read or one -8 B lever | 8 captures | rO **M 2,221 @ 27,384**; rP 2,219 @ 27,392 (free -8 B); rD / rF byte-identical (eq_main); rL 2,218 @ 27,392; nO 2,213; tp 2,216; ev_hr_curve 2,210 | |
| (4) rO base + one or two re-reads (singles + within-clone pairs) | 600 | +8 B best x18 (sharing global) data 2,219; +16 B best vault ATA data pair 2,213 | |
| (4) rO base + old +8 B knobs | 7 captures | **rO+wl+sm 2,220 @ 27,400 (Result 1)**; rO+wl+cu / rO+cu+sm / rO+rP+wl+cu+sm 2,219; rO+sm 2,220 @ 27,392; rO+cu 2,219 @ 27,392; rO+wl 2,218 @ 27,392 | |
| (5) w14a41 `irre.py --sub` (291), `irremat.py --sub`, `irhold.py` | | no at-pin gain. `%_393@bb1` (sharing_config ptr) +1 M @ +8 (no source form, w14a41). `%520` (token_frozen flag) re-read after `lifetime.end` -24 B M same: invalid IR (same artifact class as `%_196.1.i`) | |

cu = revert #3386's curve `if let Some(f)=fee{..}` to `fee.unwrap_or(..)` (+8 B).

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- w14a43's `rscan.py`, `allclones.py`, `rx.py`, `capraw.py`, `capvar.sh`, `cq.sh`. `capvar.sh` now copies from a pristine
  main crate (`$OUT/mainsrc`, or `SRC=`) so the worktree can carry a candidate while captures run.
- `rbase.sh <name>`: instnamer + allclones + rscan singles on a captured base's `rx/<name>/m.ll`.
- `top.py <jsonl> [k]`: rscan results by size.
