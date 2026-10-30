# w12a05-cto-framemir: admin_cto frame layout via MIR (notes)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `20a1ae9c0` (admin_cto 0.43919, 3,352 slots); main moved to `70f27048e` (0.45147, 3,308) during
the lane, and the frame findings below carry over (k4size changed code, not the frame anchors).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12a05-cto-framemir/` (not in git).
Ledger approach `frame-mir-*`, keys `0x22a10-w12-20a1ae9-framemir-*-v1`.

## Retained diagnostics

- `tools/dis.py <unstripped.so> [symbol regex]` prints the selected function.
- `tools/r10.py orig|<unstripped.so> LO HI` prints decoded frame accesses.
- `tools/layout_probe.rs` models tuple and Result layouts with synthetic Pubkey/error
  types. It is a host compiler experiment, not a probe of actual Anchor types or the
  SBF ABI. Its offsets suggest source experiments; they do not prove original types.

Private capture, mutation, remapping and build runners are omitted. The broad
frame-remapping bounds are already retained in the w12a02-cto-iroracle packet.

## The 56-byte first-spill gap is two things

The original spills its args at `[r10-0x928]` (r4), ours at `[r10-0x8f0]`. That is not one local:

- **+32 B in the alloca region**: mint/holder_key are at T 0x6c0/0x6a0 in the original, 0x6a0/0x680 in ours,
  and the 33 call-return slots follow at +32.
- **+24 B in the spill area**: the four arg spill slots are in a different order (orig r1/r3/r4/r2 at
  0x8f0/0x918/0x928/0x938, ours 0x8c8/0x8b8/0x8f0/0x8f8). Spill slots are created by the register
  allocator, so this part follows from code shape, not from any local.

## Alloca region, original vs main 20a1ae9 (T = r10 displacement of the object base)

Read from the original's code with `r10.py` and from frameoracle's aligned accesses:

| orig T | size | what the original keeps there (from its code) | ours |
| --- | ---: | --- | --- |
| 0x470 | 32 | wallet emit_cpi seeds `[&[u8];2]` (`_120.i`) | same, 0x470 |
| — | 16 | — | **`_117.i74` wallet emit_cpi signer slice `[&[&[u8]];1]`, standalone at 0x480** |
| 0x488..0x530 | | `_110.i`, `_94.i`, `ix_data.i`, `inner_data.i`, `authority_info.i`, `val.sroa.6.i` groups | same groups at +16 (0x498..0x540) |
| 0x538 | 7 | Option-layout `[1,8)` piece P1a: written in both validate arms (new's piece in the non-holder arm), read at the validate exit | none |
| 0x548 | 9 | P1b `[24,33)` piece; later hosts the wallet emit_cpi bump (`stxb [r10-0x548]` at 0x29148) | none (bump `_124.i` is hosted by `target.sroa.0`) |
| 0x550 / 0x560 | 7 / 9 | P2 = copy of P1 made at the validate exit (0x243e0..0x24418); read to build the sharing CPI `val` (0x26738) | none |
| 0x580 | 32 | full `target`: `[0,8)` from a spilled i64 (`[r10-0x918]`), `[8,32)` from X24; read for `curve.creator=` (0x27518) and passed as `&target` to admin_cto_pool (0x27820) | `target1` = MIR `_55`, 32 B, **no lifetime markers**, at 0x658 |
| 0x598..0x630 | | `_184`, `_169`, `inner_data`, `authority_info`, `old_creator` | same, at -64 (0x558..0x5f0) |
| 0x651 | 33 | `val` (sharing CPI Option<Pubkey>) | `val7`, 0x611 |
| 0x658 / 0x668 | 7 / 9 | copy of `new` made at entry (0x22f00..0x22f48), read once in the non-holder arm into P1 | none |
| — | 32 + 32 | — | **`sharing_update2.sroa.3` = MIR `_56` (32 B) and `target1` = `_55` (32 B), both without StorageLive/Dead**, plus `target.sroa.0` (7 B) |
| 0x680 | 24 | X24 = `target[8..32)` at the validate exit (0x243b8..0x24450); later **hosts the wallet signer slice** (0x29108/0x29150/0x29170) | none |
| 0x6a0 / 0x6c0 | 32 / 32 | holder_key / mint | 0x680 / 0x6a0 |

Net: -16 (signer slice) +80 (P1, P2, target before `_184`) -32 (between old_creator and holder_key) = +32.

MIR facts behind the "ours" column (main 20a1ae9, `--emit=mir`):
- `_55` (outer `target`) and `_56` (outer `sharing_update`) have no `StorageLive`/`StorageDead` at all: the
  tuple destructuring `let (holder,cashback,target,sharing_update,collect_old)={..}` is copy-propagated, and
  `let mut target=target;` is the same local. Without lifetime markers StackColoring never merges them.
- The block-internal `target` (`_36`) is split 7/16/9 (`target.sroa.0`, two i64, `target.sroa.8`) because it is
  copied out of `ControlFlow<.., Pubkey>`/`Result<Pubkey>` whose `Error` overlaps bytes `[8,24)` (Pubkey at
  offset 1).
- The original's `target` copies are split 8/24 instead (`[0,8)` in a register, `[8,32)` in memory: X24 and the
  `[r10-0x530]` piece), so its execute-level target is not a plain copy of a `Result<Pubkey>` payload.

## Which Rust shapes give the original's 8/24 target split

Modeled with the pinned rustc 1.79 host compiler (synthetic types; `tools/layout_probe.rs`, run with `RUSTC_BOOTSTRAP=1 ~/.cache/solana/v1.44/platform-tools/rust/bin/rustc -O tools/layout_probe.rs`): offset of
the modeled Pubkey and error inside `Result<T, E>`. Actual Anchor and SBF layouts require separate validation.

| `T` | Pubkey at | Error at | Pubkey bytes overlapped |
| --- | ---: | --- | --- |
| `Pubkey` (main) | 1 | [8,24) | [7,23): 7/16/9 split, as on main |
| `(Pubkey,Option<u64>)` | 0 | [0,16) | [0,16): 16/16 split (trial h3a) |
| `(Option<u64>,Pubkey)`, `(Pubkey,Option<u64>,bool)` | 16 | [8,24) | **[0,8): 8/24 split, as in the original** |
| `(bool,bool,Pubkey,Option<u64>,Option<Option<Pubkey>>,bool)` (block tuple plus fee) | 16 | [8,24) | **[0,8)** |
| `(bool,bool,Pubkey,Option<Option<Pubkey>>,bool)` (main's block tuple) | 36 | [8,24) | none |
| `(Pubkey,u64)`, `(u64,Pubkey,bool)`, `(Pubkey,usize)` | 8 or 0 | | [0,16) |

One hypothesis to test is that the original target travels through a `Result`/`ControlFlow` whose Ok payload is 8-aligned
with the Pubkey at payload offset 16 (an `Option<u64>` such as `fee` placed first), e.g. a validation closure or
helper returning the block tuple plus `fee` with `?`.

## Next ideas

- h4a-style shape with the 8/24 split reaching the execute-level target (X24): the Pubkey must come out of a
  payload where it sits at offset 16 behind an `Option<u64>`; then StackColoring gets the 24 B partner for
  `_117.i74` by itself.
- Keep main's code and only replace `let mut target=validate(..)?` by a helper returning `Result<(Option<u64>,Pubkey)>`
  (fee first) to test the split in isolation.
- Combine with the new main (70f27048e) genes and size knobs (`w12a13-cto-sizeknobs`) to get back to 27,400 B.
