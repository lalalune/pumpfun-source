# w14a33-cto-nativejoin: the sweep native arm's Result join

**Result (main faf9962, 0.65129 / 3,170 slots): 0.65458 / 3,280 slots at 27,400 B, normalized 1034 / raw 1034, zero losses,
differential 363/0 mismatches** (`t/b9q7`, unstripped sha 1afec025103d223b). Source change (`e/b9q_Q7.py`):
1. native arm: `let min={let rent=Rent::get()?;rent.minimum_balance(0)};` and
   `(if amount>0{ensure_rent_exempt(..)?;transfer_native(..)}else{Ok(())}).map(|()|amount)` (r1j1, section 2);
2. token arm: `transfer_vault_tokens(..)?;return Ok(amount);` inside `else if amount>0` (w14a27's b9, which on its own is +8 B);
3. -8 B repay with w14a31's Q7 knob set: TCF first `program` literal `data:a.pump_amm.data.clone()`,
   `is_writable==false`, and the event's `new_creator_fee_bps:a.bonding_curve.creator_fee_bps` read in place (drops `nf`).
r1j1 + b9 is 27,408 B (jM 2220 vs main 2199); other -8 B repays on it: sh_iflet 0.65339, ev_hr_curve 0.65309,
tp_dlen 0.65249 (oracle, 81d3d9a, main 0.65069).

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 5ee681d (0.6450), 4233bd9 (0.64979), 81d3d9a (0.65069). Ledger: approach `nativejoin`,
keys `0x22a10-w14-<main7>-nativejoin-*`.
Oracle: w14a31's raw-IR capture (`capvar.sh` -> `capraw.py`) + `rx.py` opt/llc, eq_main verified on each base;
`tools/pe.py` = post-opt IR edit + llc only (5 s). Site/chunk tables use w14a25's `sites.py` / `ch.py` / `sbs.py`.

## 1. Map: how the native arm reaches the swept join

Original (offsets in the function):
- ONE swept join at orig 0x3c50/0x3c58 (`ldxdw r1,[0x950]; ldxdw r6,[0x8f8]; jne r7,2`), phi (r7 = tag, r9 = value).
  Its preds: frozen require Ok(0) 0x2160, frozen require Err 0x2230, AMM CPI Err 0x3bb0, Rent::get Err (From,
  falls through at 0x3c40), native amount==0 0x5a50, transfer_native Ok 0x5b10, transfer_native Err 0x5b28,
  token amount==0 0x5e88, token Errs 0x62f8/0x6388/0x63b0. The Err side goes straight to the function's return
  block (0x5868: `[ret+8]=r9; [ret]=r7`), so r9 is both the swept value and the return payload.
- ensure_rent_exempt's `?` is `jne r1,2,+0x10a` to a far block (0x62e8: `r9=[0x838]; r7=r1; ja 0x3c50`).
- transfer_native Ok/Err feed the same (r7,r9) phi: that is `.map(|()|amount)`.

Main (5ee681d..81d3d9a): the native arm has its OWN join (main 0x5b00: `ldxdw r2,[0x968]; jne r7,2; ja Ok`,
Err `mov r8,r2; ja ret`) and the phi value lives in spill slot 0x968. The common join J1 (main 0x3c18) serves
the other arms. ensure's Err merges with the Rent::get Err (sunk `extractvalue`+`lifetime.end rent`, IR bb54).

## 2. Mechanism

The native arm's local join is IR `bb34.i` = `lifetime.end(rent)`. `let rent=Rent::get()?` keeps `rent`'s
storage live to the end of the native arm, so every native path (amount==0, transfer Ok, transfer Err) goes through
bb34 before the common Ok join bb50, and early tail-duplication copies the swept tag test into it (J2 + the 0x968
phi slot). ensure's and Rent's Errs both end `rent` too, so SimplifyCFG sinks them into one block.

IR oracle `e/p3.py` (post-opt: delete bb34, native preds straight to bb50) reproduces the original's native arm
exactly: no J2, ensure `jne r1,2` to a far block, transfer Ok/Err into the common phi. fm +2 / sk +4 overall.

Source form that does it: scope `rent` so its storage dies before the gate:
`let min={let rent=Rent::get()?;rent.minimum_balance(0)};` (r1; `Rent::get()?.minimum_balance(0)` r2 is the same).
With the Result<()> join j1 `(if amount>0{ensure?;transfer_native(..)}else{Ok(())}).map(|()|amount)` (-8 B):

| form (main) | bytes | ratio | M | jm (jump-masked) jM | native-arm site raw |
| --- | ---: | ---: | ---: | ---: | ---: |
| main 81d3d9a | 27400 | 0.65069 | 2172 | 2199 | 39 |
| r1j1 (81d3d9a) | 27408 | 0.6482 | 2164 | **2209 (+10)** | 51 (+12) |
| r1j1 (4233bd9) | 27408 | 0.6473 (main 0.64979) | 2161 | 2207 (+8) | |
| r1 alone (4233bd9) | 27416 | 0.646 | 2157 | 2203 | |
| j1 alone (4233bd9) | 27392 | 0.64629 | 2157 | 2198 | |

r1j1 is the native-arm structure of the original (+12 raw at the site, +10 jM overall), but it is 8 B long: the
common join is now laid out after the wallet (`jne r7,2; ja Ok`, a 2-instruction block) and the Rent::get Err
block keeps its own tail-duplicated copy of the test. It needs a -8 B repay (screen in section 3).

## 3. Screens (raw-IR oracle, all on the base named)

See the ledger rows. Native-arm spellings without the rent scope (j2..j23, 5ee681d) are main or worse;
early returns (j4, j5, j12, j14) and `?`-then-Ok forms (j2, j7, j16) lose 0.06-0.28 (they split the transfer Err off the phi).

## 4. Landed (#3315, merge 6db95a764) and post-landing screens on main 6db95a7 (0.65458)

Landed: r1j1 + b9 + Q7 at 0.65129 -> 0.65458 (land.py re-measure: zero losses, differential 363/0).
After it, the native arm site is 66 sk / 59 fm / 49 raw of 68 orig (was 57/48/39).

On 6db95a7 (raw-IR oracle, `tools/gen5.py`, `gen6.py`, `gen7.py`):
- Native spellings: `let r=..;r.map(..)` (v_j3), `.and(Ok(amount))`, `match ..{Ok(())=>Ok(amount),..}`, `Rent::get()?.minimum_balance(0)`,
  `rent:Rent`, an amount block around the rent temp: all byte-identical to main. The old `.map` form with the rent scope
  (v_old), `Ok(0)` in the zero arm (v_ok0), `and_then` (v_j10) and the closure (v_j6) are worse; `Rent::get().map(..)?` loses
  0.006; `return (..).map(..)` from the arm collapses (0.376).
- Token arm: tail `Ok(0)` / `Ok(0u64)` byte-identical; frozen arm `return Ok(amount|0)` loses 0.0146 (-8 B);
  one if/else-if/else expression undoes b9 (0.65069).
- Arm order: `if !native{token}else{native}`, `match native{false=>..,true=>..}` and `{true=>..,false=>..}` are byte-identical.

## 5. What is left at the native join (mechanism, not source-reachable so far)

- **J2 remains:** `exit` (`jne tag,2`) is early-tail-duplicated into the Ok-side join bb49 (native amount==0 / Ok / Err,
  frozen Ok(0), token zero) and the Err-side join bb57. The original has ONE join at 0x3c58 for all of these.
  `-disable-early-taildup` globally gives 0.586; merging bb49/bb57 into `exit` in post-opt IR (`e/p5.py`) collapses (0.24).
  Threading the token Ok past the test in post-opt IR (`e/p4.py`) is +14 fm but shifts the frame (raw -1030).
- **swept register:** the original keeps the swept phi in r9 (= the Err payload register) through the whole post-sweep region.
  Ours carries it in r3 at the join, spills it to 0x968 and copies it to r8 for the Err return. This is w14a06's swept-coalescing
  residual. It needs an Err-join degree change, and those changes shift the frame.
- The tail sites downstream (token ATA create, transfer_vault_tokens) now differ only in frame slots (accounts pointer 0x8d8 vs ours
  0x8e0, orig 0x8e0 vs ours 0x9b8). That is the spill-slot-order residual, not code shape.
- Zero-size knob screen on 6db95a7 (58 catalog and w14a31 knobs whose last measured delta was 0 B, `tools/gen4.py base m4`):
  none is above main (best = main, 0.65458).
