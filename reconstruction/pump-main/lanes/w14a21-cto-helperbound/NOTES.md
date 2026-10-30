# w14a21-cto-helperbound: helper-boundary screen for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main b174038c1 (0.63571), then d2d1875 (0.6417), then 06967d378 (0.64649, M 2,158). Result 1 was measured on b174038c1; the closure leads were re-measured on each main. Ledger: approach `helperbound`, keys `0x22a10-w14-b174038-helperbound-*-v1`.

## Oracle

Raw-IR capture + `opt -O3` + `llc` (w14a11/w14a15 `capvar.sh`, `rx.py`), repointed to this lane. It reproduces main
(`m`: 0.63571, 27,400 B, `eq_main: true`). Other tools, in `tools/` and `e/`:
- `e/hb.py <src> <gene..>`: the helper-boundary genes below (newline count checked). `e/pool.py`: genes47 (`g.*`) and
  size-knob (`K.*`) genes applied on top of a base edit list.
- `tools/q.py <out.jsonl> <name..>`: 2-worker capture queue over `src_edits/<name>.py`.
- `tools/calls.sh <name..>`: `call` count in execute (main 157 = 154 internal + 3 syscalls). `tools/syms.py`: which
  `admin_cto::execute*` symbols exist (an outlined nested fn shows up as a second symbol).
- `tools/vsorig.py <name..>` (`STEP=0x100`): median candidate-minus-original offset per original region.
- `tools/side.py <name> lo hi`: original vs candidate side by side (skeleton aligned).
- jm = ratio with jump offsets masked (w14a15 `jm.py`): the ratio a build would reach if every jump distance matched.

## Result 1: helpers that contain calls change inlining, so they break the call multiset

The original's call multiset equals main's. Every boundary that moves code with calls into or out of a helper changed
which callees LLVM inlines, so none of them can be the original's form:

| gene | form | bytes | calls | ratio | jm |
| --- | --- | ---: | ---: | ---: | ---: |
| m | main b174038 | 27,400 | 157 | 0.63571 | 0.6429 |
| f1 / f1c / f1a | tail (curve update + pool CPI) as `fn finish(&mut ctx,..)` / closure / `fn finish(&mut AdminCto,..)` | 30,232 / 30,288 / 30,200 | 148 | 0.454-0.479 | |
| p2 / p2a | pool CPI as `fn pool(&ctx\|&AdminCto,pargs,seeds)` | | | | pool stays **outlined** (own symbol) |
| p2b | gate + pool CPI + msg in `fn pool` | 30,488 | 148 | 0.48541 | |
| e3 / e3q | AdminCtoEvent build + emit + emit_cpi as `fn event(&ctx,..)` | 29,264 / 29,208 | 154 | 0.235 / 0.283 | |
| e3b | `fn event(..)->Result<AdminCtoEvent>`, emit in execute | 27,528 | 158 (memcpy) | 0.27794 | |
| t6 / t6w / t6s | token_frozen / token_raw_amount written by hand (all / wallet / sweep sites) | 32,088 / 28,360 / 31,112 | 171 / 166 / 162 | 0.23-0.52 | |
| w4c | wallet split, collect body as `fn collect(&ctx)` | | | | collect stays **outlined** |
| w4i | wallet body written by hand into `if collect_old{..}` | 28,944 | 154 | 0.13831 | |
| v7l / v7m | validate body in execute as a labeled block (`break 'v Err(..)`) | | | | wallet and sweep stop inlining |

Call-free boundaries keep the call set but none gains:

| gene | form | bytes | ratio | raw/fm/sk chunk delta |
| --- | --- | ---: | ---: | --- |
| s8 / s8c | CtoState literal in `fn state(..)` | 27,400 | = main (identical) | 0 |
| hk / sd | holder-rewards / sweep-dest PDA in a helper | 27,400 | = main | 0 |
| pu | `fn pool_ok(&AccountInfo)->bool` | 27,400 | 0.63331 | -8/-9/0 at 0x4800 |
| sh / sh2 | shared gate in a helper | 27,400 | 0.63391 | -6/0/0 at 0x0 |
| c1 | curve update in `fn update(&mut BondingCurve,..)` | 27,368 | 0.6247 | -35/-17/-8 (0x4800-0x5000) |
| dz | sharing decision tuple in `fn decide(..)` | 27,384 | 0.55199 | |
| w5n | sweep native arm as `fn native_arm(&AdminCto,vsigner)` | 27,416 | 0.61725 | -50/-52/-56 |

## Result 2: validate as an immediately-called capturing closure (v7c) is the original's validate boundary shape

```rust
// main: fn validate(st:&CtoState,hopt,fee,new,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{..} and
let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;
// v7c: execute's head moves up to validate's line, and validate's body (same lines, so every error line is unchanged)
// becomes a closure that captures st/hopt/fee/new/holder_key/sk by reference
let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);
 ..validate body unchanged..
 Ok(target)})()?;
```

| | main | v7c |
| --- | ---: | ---: |
| bytes | 27,400 | 27,432 (+32) |
| calls | 157 | 157 |
| ratio | 0.63571 | 0.62216 |
| **jm (jump offsets masked)** | 0.6429 | **0.66138 (+0.0185)** |
| chunk raw/fm/sk delta | | +63 / +4 / +20 (0x400-0xc00 +68 raw, 0xc00-0x1000 -27 fm) |

- The closure env passes `hopt`, `fee` and `new` **by reference**, so validate loads `new`'s pieces through a pointer, as
  the original does (orig 0x4d8 `ldxb r2,[r7+0]`, `ldxw [r7+4]`, `ldxw [r7+1]` ...).
- Variants: v7c2 (no `let st=&st`) and v7cV (closure in a `let`) are identical to v7c. `move` with reference captures
  (v7cB 0.43982), closure parameters instead of captures (v7cR 0.45256), using the outer `holder` (v7cH 0.25413) and
  the outer `cashback` (v7cK 0.5069) are all far worse.
- Offsets against the original (`vsorig.py`, STEP 0x100): main sits at -48..-80 B from orig 0x2000 to 0x5a00 and at 0
  from 0x5c00 on. v7c sits at -8..-32 B across 0x1c00-0x5a00 (closer to the original) but +32..+72 from 0x5b00 on.
  Size repay must remove about 40 B before orig 0x5c00, ideally in the sweep native arm (orig 0x5a00-0x5c00, where both
  main and v7c carry about 48 B more than the original: `jeq r1,0x2,+1; ja` pairs where the original has one `jne r1,0x2`).

## Result 3: the mechanism is `new` read through a pointer that ArgPromotion cannot undo

Capture screens on d2d1875 (closures with `move` and explicit reference captures):

| variant | captured by reference | bytes | ratio | jm |
| --- | --- | ---: | ---: | ---: |
| v7c | st, hopt, fee, new, holder_key, sk | 27,440 | 0.62835 | 0.66876 |
| vm_new | **new only** (hopt, fee by value) | 27,440 | 0.62835 (= v7c) | 0.66876 |
| vm_fee_new, vm_hopt_new | new plus one other | 27,440 | = v7c | |
| vm_hopt_fee, vm_fee, vm_hopt, vm_none | **new by value** | 27,440-27,456 | 0.457-0.459 | 0.49 |
| v7f | `fn validate(.., hopt:&Option<bool>, fee:&Option<u64>, new:&Option<Pubkey>, ..)` | 27,400 | = main | |
| pc* (23 capture-order permutations) | | 27,440 | = v7c | |

- Only `new` (Option<Pubkey>, 33 B) matters. A plain fn with a `&Option<Pubkey>` parameter is promoted back to values
  by ArgPromotion (v7f = main). The closure env adds a second indirection, so `new` stays behind a pointer.
- Where the closure copies `new` matters (on d2d1875 and on 06967d3, exact matched original instructions per 0x400
  region, `tools/exact.py`):

| region | main 06967d3 (M) | v7c | vx1 (`let new=new;` at closure start) | **vy1** (`let new=new;` at the start of the non-holder arm, line 298 `}else{`) |
| --- | ---: | ---: | ---: | ---: |
| 0x400 | 38 | +1 | +4 | +4 |
| 0x800 | 81 | +8 | -16 | +8 |
| 0xc00 | 43 | -23 | -23 | -1 |
| 0x1000 | 77 | -27 | -6 | -5 |
| 0x1400 | 60 | -1 | -1 | -1 |
| 0x2400-0x3c00 | | 0 | | -18 (spill-slot colours) |
| total M | 2,158 | -47 | | -17 |
| bytes / ratio / jm | 27,400 / 0.64649 / 0.65488 | 27,432 / 0.63204 / 0.67275 | | 27,440 / 0.64092 / **0.67744** |

- vy1 is the best validate boundary found: the validate region gains (+5 exact, +80 jump-masked) and jm is +0.0226
  over main. The holder-arm copy (vy2), copying before `let target` (vy3), `let new:Option<Pubkey>=new`, `*&new`, and copying
  at line 306 (vz2) are equal or worse.
- What blocks landing is size and the tail. vy1/v7c put the code from orig 0x1c00 to 0x5a00 at -8..-24 B from the original (main: -48..-80),
  so the extra ~40 B are bytes the original also has. Main makes up its short validate with about 48-64 B too much in
  the sweep native arm (orig 0x5a00-0x5c00): the `ensure_rent_exempt` Err edge has an inline `jeq 2,+1; ja` where the
  original has a cold `ldxdw r9; mov r7,r1; ja` stub, and the `transfer_native` result goes through an unthreaded join
  (`mov r7,r1; mov r2,r9; ldxdw/stxdw [r10-0x8e8]; jne r7,2; ja`, 48 B) where the original threads it. A source fix there
  (it needs a CFG change, as w14a06 found) composes with vy1 directly: together they would put both regions at the original's offsets.
- Size-repay screens on the closure base (all applicable genes47 `g.*` and size-knob `K.*` genes: 140 on v7c/d2d1875,
  and the vy1/06967d3 screen) found no gene that reaches 27,400 B above main. Sweep-arm forms on vy1 (early-return native arm `r1`,
  `native_arm` fn `w5n`, curve `update` fn, `pool_ok`) are all negative.

## Result 4: best lead le_vy1 on main 81d3d9a (closure + non-holder copy + 306 let-else)

```rust
// execute's head moves up to validate's old line; validate's body stays on its lines inside the closure
let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);
 ..
 let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{let new=new;
 ..
  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};
 ..
 Ok(target)})()?;
```

| | main 81d3d9a | vy1 | **le_vy1** | le_v7c (no copy) | le_m (let-else on main alone) |
| --- | ---: | ---: | ---: | ---: | ---: |
| bytes | 27,400 | 27,440 | 27,440 | 27,432 | 27,400 |
| ratio | **0.65069** | 0.64661 | 0.64781 | 0.64251 | 0.6462 |
| M (exact matched orig insns) | 2,172 | 2,160 | 2,164 | 2,146 | |
| jm | 0.65878 | 0.68283 | 0.66038 | 0.67754 | |

Exact matched original instructions per 0x400 region for le_vy1 against main 81d3d9a: 0x400 +4, 0x800 +8, 0xc00 +3, 0x1000 -5,
0x1400 -1, 0x2400 -2, 0x2800 -2, 0x2c00 +1, 0x3800 -5, 0x3c00 -5, 0x4800 -1, 0x5400 -1, 0x6000 -2 (total -8).
Offsets against the original (`vsorig.py`): le_vy1 puts orig 0x1c00-0x5800 at **-8..+16 B** (main: -48..-128), and the tail
(0x5c00 on) at +16..+64 (main: 0..-24).

- Ratio is 2M/(3339+n). At 27,400 B le_vy1 would score about 0.6483 even with a lossless size repay, so it needs about
  +9 M more. The size shift itself costs almost no exact matches (per-region exact counts outside validate do not move when
  the tail shifts by 40 B). The -17 outside validate are spill-slot colour changes (`[r10-0x9b0]` vs `[r10-0x990]` etc.) in
  orig 0x2400-0x3c00. They follow from the changed validate lifetimes.
- No genes47 or size-knob gene on the closure bases (about 140 on v7c, 80 on vy1, 29 validate genes on le_vy1) reaches 27,400 B above main.
- The 306 let-else helps only with the closure (le_m on main alone: 0.6462).

## For later lanes

- The closure is a separate, composable lever on the validate region. The tail lanes (sharing/pool/sweep literals)
  land independently of it. Re-test `le_vy1` on every new main with `e/mk.py` plus `tools/exact.py m <name>`:
  each main gain in the tail carries over unchanged, and it may cross main once the tail removes about 40 B of
  non-original code. The best candidate for that is the sweep native arm's ensure_rent_exempt and transfer_native Err joins
  (orig 0x5a00-0x5c00, about 48-64 B over the original).
- The ledger keys are `0x22a10-w14-{b174038,d2d1875,06967d3,81d3d9a}-helperbound-*-v1`.
