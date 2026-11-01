# w17a25-shim-pdafirst: PDA-first entry behind an RA firewall (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 4d09af488 (0.68514, slim-oracle M 2,287, "m0"), then main aab087f32 (0.68724, M 2,294, "m1").
Ledger: approach `pdafirst`, keys `0x22a10-w17-<sha7>-pdafirst-<item>-v1`.

Angle: make the PDA-first entry (E1, the original's call order) landable by decoupling the T1/C1 clone runs from the
entry's register allocation ("firewall" = re-derive the accounts pointer at a region head so `%0`'s split no longer
decides that region's allocation). Kill: no firewall brings pf9v's T1+C1 within 40 tokens of main's with E1 >= +20.

## Result: KILL (no landable change)

The firewall mechanism works, but every firewall re-basins the region it protects, on main as much as on pf9v:

- **Decoupling is real.** With a volatile `ctx.accounts` reload at the T1 or C1 head, pf9v+F reproduces main+F in the
  firewalled region (T1 -278/-282, C1 -77/-76; sweep head: T1 -202/-209). The PDA-first entry no longer decides it.
- **No firewall is transparent.** The protected region's accounts value is now a fresh, short vreg. Greedy allocates it
  on its own (a caller-saved r2 in the clone runs, where main has a split piece of `%0` in r8/r5), and every scratch
  register and spill colour in the region moves. main+F loses 53..680 tokens for every placement tried.
- Best PDA-first cells: pFE4 (firewall after validate) 2,004 @27,392 and pMST (manual slot at the 3 original T1 reload
  sites) 1,937 @27,456. main is 2,287/2,294. Best pf9v+F T1+C1: -150 (pFE4), -167 (pFJ), -211 (pMST). Kill threshold: -40.

## Per-region price table (slim pre-opt oracle; region deltas vs main, w17a01 regions via `rc.py`)

`m*` = main + firewall, `p*` = pf9v + the same firewall. pf9v = PDA first + per-use `read_volatile(&a.sharing_config)`
(w17a14). k8 = PDA first with main's `ptp(23)` shared test (w17a09). Old base 4d09af4 unless marked (m1 base).

| cell | firewall (shim) | M @ bytes | E1 | T1 | C1 | other big deltas |
|---|---|---|---:|---:|---:|---|
| m0 | - | 2,287 @27,400 | | | | |
| k8 | none (PDA first, `ptp(23)` kept) | 1,954 @27,400 | +25 | -234 | -48 | S1 -12, W2 -12; reg-masked -61, rfj +17 |
| pf9v | none | 1,925 @27,392 | +27 | -235 | -49 | W2 -23, P1 -6; reg-masked -157, rfj +18 |
| mFT / pFT | volatile `ctx.accounts` reload at the TCF clone-run head | 1,919 @27,256 / 1,778 @27,288 | 0 / +27 | -278 / -282 | -4 / -50 | S1 -30; T1 is 18 insns shorter |
| mFC / pFC | same at the sharing clone-run head | 2,162 @27,352 / 1,904 @27,368 | 0 / +27 | -1 / -235 | -77 / -76 | |
| mFTC / pFTC | both | 1,802 @27,208 / 1,759 @27,264 | | -279 / -282 | -77 / -76 | |
| pPTC | `ptp` passthrough on accounts at T1 and C1 heads | 1,918 @27,384 | +27 | -238 | -48 | no RA effect (deleted before ISel) |
| mFS / pFS | volatile reload at the sweep head | 1,957 @27,240 / 1,836 @27,224 | | -202 / -209 | -4 / -50 | S1 -44, W2 -35 |
| mFW / pFW | volatile reload at the wallet head | 1,967 @27,480 / 1,807 @27,480 | | -116 / -236 | -4 / -50 | TL -101 |
| mFJ / pFJ | volatile reload at J2 (`prepare_bonding_curve`) | 1,823 @27,256 / 1,932 @27,272 | -1 / +24 | -125 / -100 | -67 / -67 | W2 -71 / -39 |
| mFE / pFE | volatile reload after E1 (before `quote_locked`) | 1,605 @27,432 / 1,613 @27,400 | -2 / +22 | -490 / -491 | -7 / -32 | |
| mFE2 / pFE2 | after `quote_locked` | 1,577 @27,456 / 1,597 @27,536 | | -489 / -489 | -15 / -27 | |
| mFE4 / pFE4 | after `validate` | 1,512 @27,472 / **2,004 @27,392** | +1 / +21 | -159 / -131 | -33 / -19 | mFE4 moves TL (lcs -395) |
| mMSC / pMSC | manual slot: accounts stored once in the hkx tail (-0x680), `read_volatile` at each of the 8 C1 clone heads | 2,151 @27,472 / 1,857 @27,496 | | | -87 / -91 | volatile pins the previous clone's flag loads |
| mMSCn / pMSCn | same, plain reads | 2,191 @27,432 / 1,934 @27,472 | | | -53 / -62 | C1 rfj +5/+6 (structure closer to orig) |
| m1 | main aab087f | 2,294 @27,400 | | | | |
| pf9v1 | pf9v on aab087f | 1,932 @27,392 | +27 | -235 | -49 | W2 -23 |
| mMST / pMST | manual slot at the 3 original T1 reload sites (creator_vault, event_authority, program clones) | 2,205 @27,408 / 1,937 @27,456 | | -72 / -187 | 0 / -24 | m1 base |

## What the original does that we do not

- The original spills accounts to `[r10-0x8d8]` (spill colour 0) at E2's first instruction and reloads it at every
  clone head in C1 (8 reloads) and at 3 T1 sites (creator_vault, pump_amm_event_authority, pump_amm program clones) plus
  after the TCF call. Main keeps the C1 piece of `%0` in r5 (1 reload) and the T1 piece in r8 up to the event_authority
  clone (`ldxdw r8,[r8+0x78]` kills it there).
- pf9v keeps the T1 piece of accounts in r8 through the program clone (orig 0x3218-0x3330), so the event_authority
  pointer lands in r3 instead of r8 and the copy-out scratch flips r1 -> r3 (T1 -136 registers).
- pf9v's spill colours k6..k10 rotate because the curve-pointer spill interval (SS#321, `%4`) is shorter and heavier
  (1.375 vs 1.038). `sscsim.py` on pf9v (exact, eq_main true): restoring main's rank for it gains only +5 (1,925 ->
  1,930). The T1 loss is mostly register naming, not this rotation.
- Manual reloads from a stack slot reproduce the original's reload structure (C1 rfj +5), but the slot is at -0x680
  (the hkx tail), not -0x8d8, and the plain-load form still costs ~53 tokens of naming on main.

## Tools (`tools/`, experiment only; paths point at this lane's cache dir)

- `cap.sh <name> <edits.py> [work] [base]`: crate copy, exact edits, `capraw` (pre-opt IR), `preslim`, `fx` (w17a06's
  exact slim oracle via w17a08's `t6` copy). **Fix vs the w17a08 copy:** it deletes stale `pump_recovered*.ll` in the work
  dir before building and fails on `error[E...]`. Without that, a variant that does not compile silently reuses the
  previous variant's IR from the same work dir (this lane's first mFE/pFE rows were such ghosts and were redone).
- `q.sh n1 n2 ...`: two-wide capture queue (work0/work1), region tables via `rc.py` against `fx/${REF:-m1}`.
- `comp.py` + `mk.py`: named source-edit components (k8, pf9v, firewalls FT/FC/FS/FW/FJ/FE/FE2/FE4/F0, ptp PT/PC,
  ptr.annotation PAT/PAC/PAS/PAE4/PA0, manual slot MSst/MSc1/MSc1n/MShk/MSt1cv/MSt1ep) composed into `e/<name>.py`.
- `cdiff.py a b lo hi`: two candidates side by side on an original window range (each aligned to the original).
- `rsize.py`: candidate instruction count per original region. `radiff2.py`: greedy-trace diff with a slot shift.
