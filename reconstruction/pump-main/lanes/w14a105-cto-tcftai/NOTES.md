# w14a105-cto-tcftai: `tai` (to_account_info TCF program) re-priced on 963d1ee / 13fe453 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main `963d1eefb` (#3437, 0.67226 / 3,123), rechecked on `13fe4536b` (#3480, 0.67256 / 3,123).
Angle: w14a90-cto-tcfweight (#3425) next idea 1. Retest `tai` (TCF CpiContext program = `a.pump_amm.to_account_info()`
instead of main's `{let x=a.pump_amm.as_ref();AccountInfo{owner,key,..}}` literal) once w14a86's head changes had landed.
Ledger approach `tcftai`, keys `0x22a10-w14-963d1ee-tcftai-*` and `0x22a10-w14-13fe453-tcftai-src-tai-v1`.

**Result: notes only, no gain. `tai` is dominated on current main, even with perfect RA overrides.**

## 1. tai on the new mains (raw-IR capture + opt/llc oracle, `tools/capvar.sh` from w14a90)

| base | main | tai | bytes |
| --- | ---: | ---: | ---: |
| 95a64ba (w14a90) | 0.66986 | 0.6475 | 27,416 |
| 963d1ee | 0.67226 (capture `eq_main: true`) | 0.6484 | 27,416 |
| 13fe453 | 0.67256 (capture `eq_main: true`) | 0.6487 | 27,416 |

## 2. The clone-run blame did not change (`data/blame-*.txt`, w14a90 `blame.py` / `press.py`)

#3437 (nf local, pool_authority rent_epoch via x, sharing if-let) did not touch the head occupants of the TCF clone run.

| orig [0x2800,0x4000) | reg-only misses | ours-occupant | top occupants | press 0x2600-0x3600 (orig 7.20-7.22) |
| --- | ---: | ---: | --- | ---: |
| main 963d1ee / 13fe453 | 160 | 120 | r6 `&holder_creator_vault` (1f28 `add64 r6,264`) 22, r9 bump (1d48 `ldxb r9,[r1+35]`) 18, r0 clone temp 13 | 7.82 |
| tai 963d1ee / 13fe453 | 177 | 141 | r6 `&holder_creator_vault` 21, **r9 bump 20**, r5 clone1 lamports Rc (2668) 17 | 8.21 |

The clone1 r9 occupant is still the bump. The original loads the bump at the same place (orig 0x1d60, `ldxb r7,[r1+0x23]`)
and `&holder_creator_vault` at orig 0x1f40 (`add64 r1,0x108`), but **spills both at once** (`[r10-0x910]`, `[r10-0x8e0]`).
That leaves r6/r9 free for clone1's owner and key (orig 0x26c8 `ldxdw r9,[r2+0]` held to 0x2958, 0x27a8 `ldxdw r6,[r2+24]`).
Ours keeps both in r6/r9 over the run. w14a90's spill-at-def probes of these two values (on main and tai) already lost, so this is a
greedy decision with no source handle (the bump load is GVN-shared with the collect-arm use at line 563, as in the original).

Side by side, orig 0x2600-0x2a00 (`data/sbs-0x2600-0x2a00-*.txt`): tai has the original's clone1 instruction order (key, lamports,
data, flags 42/41/40, rent, owner). Every miss is a register name or an extra spill store (`[r10-2392]` key, `[r10-2496]` flag 42).

## 3. RA-recoverable part (w14a84 private greedy llc, `cclimb.sh`: colour-target forces + forward selection)

| base | climb | forces | ratio | bytes |
| --- | --- | ---: | ---: | ---: |
| main 963d1ee | pinned 27,400 | 8: 1687=r6, 1674=r7, 1911=r6, 1622=r3, 2077=r4, 1711=r4, 1314=r7, 2256=r2 | 0.67226 -> **0.68005** | 27,400 |
| tai 963d1ee | any size | 11, first 1971=r7 (clone1 lamports Rc, +0.0103, -32 B), then 1687, 2194, 1674, 1622, 468, 1907, ... | 0.6484 -> 0.67316 | 27,384 |
| tai 963d1ee | pinned 27,400 | 7: 1823=r9 (TCF flag-42 load temp at 0x29a0), 1842=r5 (0x2ad8 temp), 1687, 1674, 1622, 1795, 2259 (stopped; +0.0003/round) | 0.6484 -> 0.67046 | 27,400 |

The forces that help tai beyond its clone1-specific ones (1687, 1674, 1622, 1711, 1314) are the same forces that help main, so
they do not close the gap. tai's RA ceiling is 0.007-0.010 below main's, so its correct clone1 instruction shape is worth less than
the register cascade it causes, even under ideal colouring.

## 4. tai + 16 B repays at 27,400 B (stitch12 `genes.py`; `edits/p_*.py`, `data/partners-963d1ee.jsonl`)

| key | partner | ratio | slots |
| --- | --- | ---: | ---: |
| p_amp | amp_inline (-16) | 0.65009 | 3,120 |
| p_evnf | ev_nf_inline (-16) | 0.64859 | 2,925 |
| p_nfb | nf_back (-16) | 0.64859 | 2,925 |
| p_volsu | vol334_back + su_to_st | 0.64829 | 3,198 |
| p_kdvol | crl_kd + vol334_back | 0.64799 | 3,139 |
| p_kdsu | crl_kd + su_to_st | 0.64739 | 3,141 |

All of them are 0.022-0.025 below main, and the clone-run blame is unchanged (177 misses, the same occupants). The repays only
restore the size. The key-first and owner-first literal orders for clone1 were already screened by w14a23/w14a43: the natural literal
equals `to_account_info`, which is `tai`.

## 5. Reading / next

- `tai` is closed: same blame on three mains, RA ceiling below main's, no repay rescues it.
- The clone-run names follow the greedy decision to keep the bump and `&holder_creator_vault` in r9/r6. The original spills both
  right after computing them. No source form is known that changes that decision without codegen-forcing constructs.
- Main's own RA ceiling at 27,400 on 963d1ee is 0.68005 (8 forces, `data/climb-cc_main0.log`). Its top forces (1687=r6 and 1674=r7, accounts-pointer `%0`
  pieces at 0x4e80/0x5cc0, and 1911=r6 at 0x3ea0) are outside clone1, so lanes that want RA gains should look there, not at the TCF program clone.
