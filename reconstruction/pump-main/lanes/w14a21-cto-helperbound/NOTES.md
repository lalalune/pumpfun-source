# w14a21-cto-helperbound: helper-boundary screen for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main b174038c1 (0.63571, 3,173 slots, 27,400 B). Ledger: approach `helperbound`, keys `0x22a10-w14-b174038-helperbound-*-v1`.

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
