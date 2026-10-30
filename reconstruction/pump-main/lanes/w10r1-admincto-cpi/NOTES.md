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

## Attempts (ledger approach `cpi-shapes`)

| trial | mechanism | bytes | ratio |
| --- | --- | ---: | ---: |
| base | main e61baa9 | 27,344 | 0.37637 |
| v1 | `.with_signer()` on both signed CPIs | **27,400** | 0.33074 |
| v2 | signer seeds as one literal (no pb/poolseeds locals) | 27,344 | 0.37727 |
