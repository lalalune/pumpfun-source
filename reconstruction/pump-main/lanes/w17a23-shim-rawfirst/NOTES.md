# w17a23-shim-rawfirst: the sweep token arm in the original's call order (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 SHIM track.
Angle: put the sweep token arm in the original's call order (`token_raw_amount` before `token_frozen`, line 664) and make
it landable with marked shims.
Bases: main 4d09af488 (M 2,287), 2f3597f99 (#4040, M 2,291), aab087f32 (#4050, M 2,294), 5e05222b5 (#4053, M 2,295). Every number below is the
w17a06 slim pre-opt oracle (capraw + preslim + fx), whose source captures are token-identical to the IR cells.
Ledger: approach `rawfirst`, keys `0x22a10-w17-<sha7>-rawfirst-<item>-v1`.

**Result: notes only, no landable cell. The kill condition holds:** no source-realisable combination brings raw-first
to main's M at 27,400 B. The best realisable raw-first build is 6 M below main (RF2), the best IR cell 2 M below (R2FV),
and the token-arm register fix that would carry it past main has no source lever (it needs a private-llc RA force).

## 1. Price table (main aab087f32 = M 2,294 @27,400)

| variant | form | M | bytes | Mj (jumps masked) | note |
| --- | --- | ---: | ---: | ---: | --- |
| main m2 | | **2,294** | 27,400 | 2,307 | |
| R2 | raw-first (line 664 call order swapped) | 2,282 | 27,376 | 2,304 | -12: W2 -10, W1 -1, S1 -1 |
| RF2 | R2 + `black_box(())` on the token-arm transfer Ok continuation (line 719) | 2,288 | 27,384 | 2,306 | source = IR cell `bf:sweep:33187` exactly; +6 all in W2 |
| R2FV | RF2 + volatile load of the raw_amount Ok payload (IR `vl:sweep:32941`) | 2,292 | 27,400 | 2,306 | +16 B in the token arm restores 4 jump offsets; no exact source form |
| RFVC | RF2 + `let ar=..?;let amount=read_volatile(&ar)` | 2,282 | 27,400 | | nearest source form of `vl:32941`: extra re-spill |
| RFVA | RF2 + hand-written `match` with a volatile payload read | 1,720 | 27,400 | | collapse |
| R2 + force 246=r6 (sticky, private RAPRIO llc) | | 2,288 | 27,368 | 2,311 | token arm = original (`add64 r8,0x48; ldxdw r6,[r10-0x2c8]; jeq r6`) |
| R2F + same force | | 2,295 | 27,376 | 2,314 | +1 over main at -24 B |
| R2FV + same force | | 2,294 | 27,392 | 2,313 | main's M at -8 B |
| the same fence on main (frozen-first) | | 2,173 | 27,432 | | raw-first specific |

On the other bases the deltas are the same: 4d09af4 R 2,275 @27,376 (main 2,287), RF1 2,281 @27,384; 2f3597f R1 2,279,
RF1b 2,285 (main 2,291); 5e05222 (latest) R3 2,282 @27,376, RF3 2,288 @27,384 (main 2,295).

Beam over R1 (`gen.py` vl/rr/vs/bw/sw/bf/na + `ptgen.py` pt/pb, 2,311 cells, pre-opt): best singles are the fence (+6 at
+8 B) and volatile loads on the transfer `?` residual copies (`vl:sweep:33202/33204`, +5 at +8 B). Pairs of the fence
with the 116 code-changing cells that keep R1's size or grow it: best F+`vl:sweep:32941` 2,292 @27,400. Triples
F+V+X over 84 cells: none above 2,292 at 27,400. Post-opt weight scan (10 probabilities x the five token-arm branches):
nothing reaches the original register assignment; the best equals RF2.

## 2. Why raw-first loses: the token-arm register assignment

Original (orig 0x20b0-0x2160): `ldxdw r2,[r8+0x48]; call raw_amount; ..; add64 r8,0x48; ldxdw r6,[r10-0x2c8];
ldxdw r2,[r8+0]; call frozen; ..; ldxb r1,[r10-0x2c8]; jeq r1,0 (cold W2); mov64 r9,0; mov64 r7,2; jeq r6,0`.
Raw-first on main: `stxdw [r10-0x9b8],r6; mov64 r6,r8; add64 r6,0x48; ldxdw r8,[r10-0x2c8]; ldxdw r2,[r6+0]` -
GEP and amount swap registers.

Greedy trace (`llc -debug-only=regalloc`, the debug llc is byte-identical to the SDK llc on these modules; vreg numbers
are the same on 4d09af4, 2f3597f and aab087f):
- `%244` = `COPY %0; ADD_ri 72` (the field address `&a.creator_vault_quote_token_account`, passed in r3 to
  `collect_transfer_vault_tokens` in the cold arm) has hints `r3, r8` and therefore priority bit 30. It is dequeued
  while `%0` (accounts) is still whole in r8, so it takes the first free callee-saved register, **r6**. It is evicted
  twice (by `%55` and by the Result tag phi `%1664`) and lands in r6 again.
- `%0` is evicted from r8 later by `%391` (the `new` pointer, weight 4.9e-4) and region-split in round 2; its r8 piece
  ends at the token-arm COPY on both main and raw-first (identical split).
- `%246` = the amount (no physreg COPY, so no hint and no bit 30) is dequeued after that and takes the first free
  callee-saved register, **r8**.
- `tryHintsRecoloring` cannot move `%244` to r8 because `%246` holds it.
- On main (frozen-first) the frozen byte is short and r8 is held by main's amount at that moment, so the byte takes r9
  and `tryHintsRecoloring` moves `%244` r6 -> r8. That is why main has the original's `add64 r8,0x48` and raw-first does
  not.

RAPRIO prices (w15a12 patch, `tools/rapr.sh`): forcing `246=r6` sticky gives the original token arm exactly (above);
non-sticky 2,242; `244=r8` 2,120 (evicting `%0` early collapses the head); `RAPRIO_NOHINT=244` 2,276 @27,408;
hint `246=r6` 2,230; `244` dequeued last gives `add64 r8,0x48` but the amount in r9 (2,269-2,273 @27,408).

Source levers tried for `%246 -> r6` / `%244 -> r8`, none of which reaches it:
- branch weights on the five token-arm branches (post-opt scan above): no;
- the transfer source arg re-derived in the CPI arm through `ptp` (so `%244` is short and loses its r3 hint): RX1
  (inside the `and_then` closure) stops the closure from inlining (a new function, invalid); RX2 (bound before
  `create_idempotent`) folds the token-arm GEP into the second load (`ldxdw r2,[r8+0x48]`) and puts the amount in r9:
  2,273 @27,336 (RX2F with the fence 2,268 @27,360);
- the only consistent order for the original assignment is: amount allocated before `%244` (it then takes r6) and
  `%244` recoloured to r8 at the end. The amount can only be dequeued first with priority bit 30, i.e. a physreg COPY
  (a register-passed use). It has none: it goes to `collect_transfer_vault_tokens` on the stack, and `pt64`,
  `expect_p` and `black_box` give no physreg COPY;
- fences and volatile loads from the beam: none changes the token-arm assignment (`tok` flag in the beam results).

## 3. What other lanes can use

- **Raw-first is a +6 cell with the fence and costs 12 without it.** Any union lane that takes raw-first (w16a11 shows
  s1+n1po / s1+p2 need it to keep the wallet cold block cold) should add the line-719 fence:
  `..&vsigner))?;core::hint::black_box(());/*shim: fence on the token-arm transfer Ok continuation*/return Ok(amount);}`.
- The token-arm RA fix is worth about +7 M jump-masked on raw-first. A lane that finds a way to give the amount a
  physreg hint (a register-passed use), or to keep `%244` out of r6 until the amount is allocated, can price it with
  `tools/rapr.sh <capture> <tag> RAPRIO_FORCE=246=r6 RAPRIO_STICKY=1`.
- `tools/occ.py <ra.txt> <line> <lo> <hi>` replays the greedy assign/unassign log to a dequeue and prints each
  callee-saved register's occupant over a slot range; `tools/rc.py` prices captures per w17a01 Ghidra region;
  `tools/mj.py` splits M into jump, register and frame parts; `tools/jdiff.py` lists the tokens one capture matches and
  another does not; `tools/slot.py` lists every access to one frame slot (orig regions tagged).
- Original slot facts found on the way: [r10-0x950] holds the curve `is_holder_reward` value (stored at orig 0x4b68
  without `and64`, so the original stores a precomputed bool, not `holder&1` of the param byte); the dead
  `ldxdw r1,[r10-0x950]` / `ldxdw r1,[r10-0x8e0]` reloads in the original token arm are reloads of that bool and of the
  `&holder_creator_vault` GEP, which the original spills at its definition (orig 0x1f48). Main keeps that GEP in r6 and
  spills it at the token arm to -0x9b8.

## Tools (`tools/`, experiment only)

`cap.sh` (crate copy + capraw + preslim + fx), `mk.py`/`variants.py` (line-asserted source variants), `rapr.sh`
(private RAPRIO llc on a capture), `apply1.py` (apply w17a06/w17a15 edit ids to a slim module and score with fx),
`occ.py`, `rc.py`, `mj.py`, `jdiff.py`, `slot.py`. The beam drivers are w17a06's `gen.py`/`screen.py` and w17a15's
`ptgen.py`/`screen.py` (patched to record the token-arm pattern as `tok`).
