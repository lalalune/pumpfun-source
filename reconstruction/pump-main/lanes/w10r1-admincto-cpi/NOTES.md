# Lane w10r1-admincto-cpi (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`).
Angle: CPI shapes (pump_amm `admin_cto_pool`, pump_fees `admin_cto_sharing_config`, token transfers and sweeps).
Base: origin/main e61baa928 (1032 normalized / 347 raw). Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-cpi/`.

## Result r2: `with_signer` on the sharing_config CPI, admin_cto at the original size

The `admin_cto_sharing_config` CPI builds its context as `CpiContext::new(program, accounts).with_signer(signer_seeds)`
instead of `CpiContext::new_with_signer(program, accounts, signer_seeds)`. Behaviour is identical
(`with_signer` just sets the same `signer_seeds` field). r1 changed both signed CPIs; all 56 B come from the
sharing CPI, and keeping `new_with_signer` on `admin_cto_pool` is better (r2).

| metric | main e61baa9 | this PR (r1) | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,400** | 27,400 |
| win.py ratio | 0.37637 | 0.34572 (r1 0.33074) | 1 |
| slots_diff (equal size only) | n/a | 3,372 (r1 3,373) | 0 |
| calls (internal+external) | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1032 / 347 | **1032 / 1032** | 1035 |
| gains / losses (norm, raw) | | 0 / 0, **+685** / 0 | |
| unstripped sha256 | 3ca6911a... | b87fba61... | |

With admin_cto at 27,400 B every later function sits at its original address, so every normalized
window is now also a raw match (raw 347 -> 1032). `elf_meta_diff.py`: all non-.text differences follow
from .text (only the known 2 extra `String` vtable lddw relocations remain).

The ratio drop is an artifact of jump offsets: the 56 B are inserted inside the sharing CPI block
(the CpiContext is built in place and its signer field written afterwards), every jump that crosses
that block changes its immediate. With jump offsets masked the listing ratio is unchanged
(main 0.3860, r2 0.3856); the code outside the sharing block is byte-identical to main.

## Analysis: CPI shapes already match

- Clone order and accounts-struct field offsets of every CPI equal the original: `admin_cto_pool`
  (8 outlined `AccountInfo::clone` calls, same `[ctx+off]` sequence 0x58,0x0,0x60,0x70,0x68,0x30,0x78,0x58),
  `transfer_creator_fees_to_pump_v2` (inlined Rc increments, identical field sequence
  0x58 0x0 0x18 0x20 0x28 0xb0 0xa8 0xb8 0x80 ... 0xe8), the two `create_idempotent`s and
  `collect_coin_creator_fee`.
- The call sequence (callseq.py) differs only in placement: (1) validate's error blocks, (2) the
  sweep tail (amm frozen check, transfer_creator_fees CPI, native path) laid out after the post-sweep
  code instead of before it.
- llc oracle (post-opt IR, 4 s, reproduces the build's function byte for byte): `!prof` 1:2000 on the
  sweep.exit re-check moves the tail back (ratio 0.3764 -> 0.4067, 27,336 B). Un-threading the sweep's
  Ok paths into sweep.exit alone (IR surgery) does not (0.3228). MBP trace (llvm-dbg llc
  `-debug-only=block-placement`): the tail-duplicated re-check after the CtoSharedVaultFrozen error
  picks bb38 (post-sweep) as a 50% "CFG break" successor because no other unplaced predecessor of
  bb38 is hot; in the original, the merged sweep exit (Ok constants + errors, 0x3c50) is that hotter
  predecessor and falls through into post-sweep.

## Size catalogue of mechanisms (for stitchers; deltas vs main 27,344 B, not additive)

`with_signer` / `c.signer_seeds=` on the sharing CPI: +56 (exactly the original size). Where it comes from:
the struct literal `CpiContext{..}` is byte-identical to `new_with_signer` (both build the context in the
call's argument slot); `with_signer(self)` and the `let mut c` form move the finished context once more.
On the pool CPI the same change is 0 B (ratio down). Other genes measured on this base: PR #2509 `ql_before_shared` +56,
PR #2518 wallet flags +32, PR #2515 sharing tree +24, inline signer-seed literal 0, sweep Result merged with
the skip path (`if g {sweep()} else {Ok(0)}?`) -104, native early return +64. Compositions are strongly
non-additive (#2518+#2515 = +136; sws+#2518+w8 = +48; sws+hc+w8 = +120). None of 20 compositions beat
PR #2509 at 27,400 B (0.358 / 3,361 slots); the best near-miss was sws+#2518+w8, 27,392 B, 0.35835.

## Attempts (ledger approach `cpi-shapes`)

| trial | mechanism | bytes | ratio |
| --- | --- | ---: | ---: |
| base | main e61baa9 | 27,344 | 0.37637 |
| v1 | `.with_signer()` on both signed CPIs | **27,400** | 0.33074 |
| r2 | `.with_signer()` on the sharing CPI only (kept) | **27,400** | **0.34572** |
| pool | `.with_signer()` on the pool CPI only | 27,344 | 0.34128 |
| v2 | signer seeds as one literal (no pb/poolseeds locals) | 27,344 | 0.37727 |
| r2+v2 | | 27,400 | 0.34512 |
| sl, slp | `CpiContext{..}` literal (sharing / pool / both) | 27,344 | identical to main |
| mset | `let mut c=CpiContext::new(..);c.signer_seeds=..` | 27,400 | identical to r2 |
| w8 | `swept=if shared&&holder{sweep()}else{Ok(0)}?` | 27,240 | 0.3765 |
| w10 | gate passed into sweep | 24,416 | sweep not inlined |
| w1 | native arm returns early | 27,408 | 0.3199 |
| w3 | frozen arm returns `Ok(0)` | +168 on r2 | callseq worse |
| IR u1 | un-thread sweep Ok paths (llc oracle) | 27,480 | 0.3228 |
| IR bw | `!prof` 1:2000 on sweep.exit re-check (llc oracle) | 27,336 | 0.4067 |
| combos | 20 gene compositions (see ledger `gene-combo-*`) | | none better at 27,400 |
