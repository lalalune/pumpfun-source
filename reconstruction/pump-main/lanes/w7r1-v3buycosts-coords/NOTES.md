# Lane w7r1-v3buycosts-coords: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: coordinate archaeology. Base: origin/main 2162b3b00 (rebuilt here: 1027 normalized / 276 raw,
unstripped sha256 fd54954f...). **No source change is proposed.** This lane is analysis only.

| Build | Bytes | ratio | calls | normalized / raw |
| --- | ---: | ---: | ---: | --- |
| base 2162b3b00 | 2,136 | 0.920 | 17/17 | 1027 / 276 |
| t01 front-multiline-layout | byte-identical ELF | | | 1027 / 276 |

## Findings

1. **Window coordinates all match.** The original's two `Source` sites (`trade_v3.rs:371`, `:375`;
   `stw 0x173/0x177`, filename len 29, error code 6024) equal ours. Its callee neighbours also match:
   add3 (0x801f8) = `trade_v3.rs:285`, gross_up_quote_error (0x81640, placed straight after the
   window in both binaries) = `:382`.
2. **All 16 `lddw` constants in the window decode the same** (`tools/loccensus.py`, plus a per-window
   lddw decoder): Location `lib.rs:1939:14` (protocol_fee_split checked_sub expect), `lib.rs:1936:45`
   (try_from expect), `alloc/src/string.rs:2559:14` (ToString::to_string expect), the same
   vtables, and string lengths 0x26/0x23/0x37. The SBF `.data.rel.ro` Location record stores the file
   pointer in the high 32 bits of the first word.
3. **Global census: every panic Location record in the binary matches.** 142 records, 138 distinct
   (file, line, col), 41 files, including the platform-tools std paths
   `/home/runner/work/platform-tools/platform-tools/out/rust/library/...`: the multisets are identical
   between the original and the candidate. `coords.py unmatched` reports no coordinate-only differences.
4. Line layout alone is code-neutral (t01: spreading the front over lines 366-369, as the original's
   blank lines suggest, gives a byte-identical ELF).

## What this rules out

* A statement-order or file-structure difference visible through coordinates: none exists in or
  around this window.
* A different std/core/alloc *source* in the original toolchain (for example, a library version
  whose `expect`/`to_string` carries a branch hint). Every library Location line and column, and
  the platform-tools build path, is identical. Earlier lanes (w4-v3costs) showed that a 1:2000 weight
  on the line-375 `to_string` Display::fmt failure branch gives a full IR-level match. That weight
  therefore cannot come from a different library version with different line numbers. Any remaining
  toolchain explanation has to be in rustc/LLVM codegen with line-identical std sources.

The residual is unchanged: the greedy split of the sret pointer, decided by
freq(375 to_string panic) vs freq(first try_from panic). See w4-v3costs/NOTES.md and
v3costs-semantic-reorder/NOTES.md.

## Ledger

* 5cc380f937974653b9528f88b7b17081 `0x80df8-main-2162b3b00-coords-window-census-v1` (analyzed)
* bdbc3466359c40aa84b2baddbab835f9 `0x80df8-main-2162b3b00-front-multiline-layout-v1` (rejected, byte-identical)
