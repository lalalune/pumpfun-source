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

Landed as #3393 (merge 0d04cf460): land.py 0 losses, differential 363/0.

---

# Part 2 (branch -2): screens on main 0d04cf4 (0.66507, 3,228 slots, M 2,220)

Ledger keys `0x22a10-w14-0d04cf4-rescan304-*`. The raw-IR capture of #3393's source is the new oracle base (`eq_main` true).

Short names (all relative to main 0d04cf4): wlB = wallet `!is_writable` (drop `==false`), smB = sharing `if let` (drop the
`match`), rP = pool_authority `rent_epoch:x.rent_epoch` (drop that re-read), rL / nO = drop the pump_fees lamports / vault ATA
owner re-reads, aP = drop the sweep `amm_present` let (#3361), cu = curve `fee.unwrap_or(..)` (undo cu_iflet2), gw = wallet
event `let ts=Clock::get()?..` (w14a31 `g_w_clock_local`), ecl = event `is_cashback_coin:cashback`.

## Converged screens on 0d04cf4

| screen | runs | best at 27,400 |
| --- | ---: | --- |
| re-read singles + within-clone pairs, 18 clones | 600 | = main (+8 B best x18 data 2,217) |
| pscan place (729) + pp on sharing clones `%x19`, `%x20`, `%_470` | 2,646 | main order and placement |
| 48 single knobs (w14a31 catalog that still applies, plus aP / cu / wlB / smB) | 48 captures | 14 byte-identical; none above 2,220 |
| sweep-head +8 B spellings on wlB (PDA check, `amm_frozen`, `native`, `dest`) | 13 captures | 2,220 at best |
| PDA ConstraintSeeds error spellings (`require_keys_eq!`, `Err(..)?`, `let r:Result`, closures) | 7 captures | all byte-identical or far worse |
| fill lattice at net 0 B (wlB / smB / rP / rL / nO / aP / rO with cu / gw / ecl) | 15 captures | 2,218 at best |
| irre / irremat / irhold on wlB | ~490 | no source-expressible gain (see below) |

## Size levers on 0d04cf4 (bytes / M; main 27,400 / 2,220)

| lever | bytes | M | note |
| --- | ---: | ---: | --- |
| wlB | 27,392 | **2,220** | free -8 B |
| aP | 27,384 | 2,219 | |
| smB | 27,392 | 2,218 | |
| rP | 27,392 | 2,218 | |
| wlB + rP | 27,384 | **2,221** | junk bound 2,223 @27,400 (entry 0x148 / 0x180) |
| **C0 = wlB + smB + rP** | **27,376** | **2,224** | +4 M at -24 B; junk bound 2,226 @27,400 |
| C0 + cu / + gw / + wl_ts_clockvar | 27,384 / 27,392 / 27,392 | 2,220 / 2,221 / 2,221 | |
| C0 + gw + {wl, sm, rP, cu, ecl} | 27,400 | 2,218 / 2,218 / 2,218 / 2,217 / 2,214 | gw moves 160 slots |
| C0 + one re-read (rscan) | 27,384 | 2,221 (pool_authority rent = rP back) | |

**C0 is the lead:** removing three fills (the pool_authority rent re-read from #3369, and the wallet `==false` and sharing
`match` that #3393 brought back) is +4 M at -24 B on 0d04cf4. Put another way: 39eb377 with both the pump_fees owner and the
pool_authority rent re-reads dropped. It lands once 24 B of faithful code costs at most 3 M. No known knob or re-read does that
(best: wl + sm + cu, 2,219).

## Junk maps (pure +8 B insertions with jumps fixed; `tools/junkmap.py`, w14a55's `junkgreedy.py`)

- wlB base: +8 B anywhere in the sweep head (ours 0x22c8-0x2468) gives **+2 M**. That region is the PDA ConstraintSeeds error
  path. There the original reloads `&holder_creator_vault` from a spill slot (`ldxdw r1,[r10-0x8e0]`, the w14a41 remat lead)
  and, after `with_pubkeys`, re-tests the Result tag (`ldxdw r1,[r10-0x950]; jne r7,2`), which ours threads away. Every
  source spelling of the check folds to main's tokens (table above).
- C0 and wlB + rP bases: the best junk is at the entry (0x148-0x190, the PDA-first / `shared` chain residual, +1 each).

## IR oracles on wlB (27,392, M 2,220)

- irre `--sub`: +8 B re-reads to 2,221 @27,400: `%_391@bb1` (sharing_config pointer; no source form, w14a41) and
  `%_254.val` / `.val54` (the drop of the `authority_info` copy after `invoke_signed`).
- irhold: `%_128<-%x` = the rP removal (2,221 @27,384, source-confirmed as wlB + rP); `%_338<-%_337` (curve pointer held
  across the cu store, 2,220 @27,384) and `%_177<-%x21` (= rL) are free -8 B as IR edits.
- On C0: irre +8 B leads `%_389@bb1` 2,225, `event_infos.val32.i` 2,223, `%_253.val` 2,222 (none with a known source form).

## More screens on 0d04cf4 (all below main)

| screen | runs | best |
| --- | ---: | --- |
| pscan place (729) on 10 TCF clones | 7,290 | main placement for every clone |
| C0 + cross-clone re-read pairs / triples (top 14 +8 B singles) | 455 | 27,400: 2,216; 27,392: 2,219 |
| C0 + one more removal (aP, rL, nO, aP+nO, tp) | 5 captures | 2,218 (rL @27,368): C0 is a local max for removals |
| `read_volatile` placeholder through `sharing` / as `u64` (main and C0) | 6 captures | identical M and size to the `holder_key as u8` form |

## Next ideas

1. **C0 (+4 M at -24 B)** is the open lead. It needs 24 B of faithful code that costs at most 3 M. The junk maps say pure size is
   free in most regions and +1 at the entry, so the cost of every knob tried comes from its register/schedule side effects.
   The cheapest known fills are wl + sm + cu (2,219) and the pool_authority rent re-read (2,221 @27,384).
2. The sweep-head PDA ConstraintSeeds error path is where the original has three instructions that ours lacks (the spill
   reload of `&holder_creator_vault` and the `jne r7,2` Result-tag test after `with_pubkeys`). Ours threads the tag test away
   because the Err discriminant load carries `!range [0,2)`. A sweep whose error result goes through a `Result<u64>` memory
   slot (range [0,3)) would keep the test. On the wlB base, +8 B there is worth +2 M even as junk.
3. Rerun the "move a re-read" step after every landing. The re-read fills (#3361 owner, #3369 rent) changed from free to -2 to -3 M
   within two landings.
