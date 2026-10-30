# w14a37-cto-collectsib: sibling-handler idiom port for wallet() and sweep() (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 06967d3 (0.64649, 3,169 oracle slots) for batch a*, main e87e001 (0.64709) for batch d*.
Ledger approach `collectsib`, keys `0x22a10-w14-06967d3-collectsib-*` and `0x22a10-w14-e87e001-collectsib-*` (11 rows).

**No source change is proposed.** No rewrite beat main. This PR adds the per-arm outline table (sibling, original and
ours), the per-region residual classes, three small tools, and the screened edits.

## 1. Outline table: sibling vs original vs ours, per arm

The sibling windows were dumped from the baseline `unstripped.so` with `tools/fdis.py`. Those windows are byte-matched, so
they show the original's code. The siblings are `creator::collect_creator_fee::execute` (0x2a8e8, 2,984 B) and
`creator::collect_creator_fee::collect` (0x2b490, 2,696 B), plus `sweep::execute` (0x72810) for the sweep idioms.
`tools/ann.py` names admin_cto's call targets. All other Pump Main functions sit at their original addresses, so an
original call target resolves to the baseline symbol at the same address.

| arm (orig offsets) | sibling (byte-matched) | original admin_cto | ours (main e87e001) |
| --- | --- | --- | --- |
| wallet entry gates (~0x2620-0x26e0) | `collect()`: `require!(*owner!=FEES)`, then `if executable{msg!;return Ok(None)}` | is_writable byte test, `token_frozen(creator ATA)`, merged msg! blocks | same calls and blocks, 0x48 B earlier (validate-side shift) |
| wallet flags (0x5bd8-0x5cc0) | none (`collect()` tests native inside) | memcmp native, `data_is_empty(coin ATA)` -> [r10-0x918], `data_is_empty(cvqta)`, `token_frozen(coin ATA)` -> **r8** | same calls in the same order; do_coin spilled to [r10-0x938] |
| wallet ATA create (0x5cc0-0x5e68) | none | 7 clones, memcpy, `create_idempotent`, then a **tail-duplicated** coin gate (`and r8,1; jne r8`) | same calls; gate not duplicated (`ja` to a gate that reloads the spilled flag) |
| wallet collect arm (0x60f8-0x67b0) | `execute`: `collect`, `Clock::get`, `Event::data` **inlined**, `sol_log_data`, Vec/alloc inlined, `new_with_bytes`, `invoke_signed` | `collect`, `Clock::get`, `From`, `token_frozen(cvqta)` (laid out here), `Event::data` **outlined** twice, `sol_log_data`, clone, `from_iter`, `exchange_malloc`, `new_with_bytes`, memcpy, `invoke_signed` | identical call sequence |
| wallet coin CPI (0x6800-0x6a28) | none (AMM side) | 9 clones, memcpy, `collect_coin_creator_fee` | identical |
| sweep PDA / AMM (0x1e60-0x26e0) | `sweep::execute`: `keys_eq(&recipient.key(),&expected)` | find_program_address, memcmp, 2x `data_is_empty(coin ATA)`, token_frozen / token_raw_amount, TCF CPI | identical call order |
| sweep native (0x3bd0, 0x5970-0x5b40) | `collect()` native: `Rent::get`, **`lamports()` before `minimum_balance`** (receiver first), data_len rent check, `transfer_native` | `Rent::get`, **`minimum_balance` before `lamports`** (`min` bound first), `ensure_rent_exempt`, `collect_transfer_native` | identical to original |
| sweep token (0x5e90-0x60f8) | `collect()`: `try_borrow_data` + `try_deserialize_unchecked` **inline**, `transfer_tokens` | `token_raw_amount` / `token_frozen` **helpers**, `create_idempotent`, `collect_transfer_vault_tokens` | identical |
| sweep exit join | none | tag test **tail-duplicated into every Err edge**: payload r9, tag r7, `ldxdw r1,[r10-0x950]` (dead on both successors), `jne r7,2 -> exit 0x5868`, `ja 0x3c68` | shared join (`LBB206_292: mov r7,r1` / `LBB206_84: jne r7,2`); the payload goes r2 -> [r10-0x968] -> r8 (`LBB206_315`) |

What the table shows:
- **The original's wallet and sweep outlines already equal ours** at the call and block level. The full 157-call sequence
  differs from the original only in the validate region and the PDA position (`find_program_address` at 0x00f8 vs 0x0220,
  the to_string / PumpError::name / From groups at 0x0d28-0x1bf0, `data_is_empty` at 0x4b88 vs 0x4c10). No call in
  [0x1e00, 0x6b08) moves.
- **The original did not port the sibling's statement shapes.** In the sweep native arm, the sibling evaluates
  `lamports()` before `minimum_balance(0)`, and the original evaluates them in the other order. In the token arm, the sibling
  deserializes inline, and the original calls the `token_raw_amount` / `token_frozen` helpers. The only sibling code that
  admin_cto reuses is the `collect()` call itself, together with `collect_transfer_native` / `collect_transfer_vault_tokens`,
  and those are already calls in both builds.
- The sibling's `execute` inlines `Event::data` and the Vec build, while admin_cto (original and ours) outlines them.
  The sibling window is therefore not a template for the wallet collect arm's instruction stream.

## 2. Residual classes per arm (`tools/cls.py`, difflib alignment on register-, frame- and jump-masked instructions)

| region (orig) | insns | same | reg only | frame only | reg+frame | jump imm | unaligned (orig) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sweep PDA/AMM 0x1e00-0x2700 | 274 | 229 | 15 | 1 | 1 | 17 | 11 |
| sweep Rent / join 0x3b00-0x3c70 | 46 | 33 | 3 | 3 | 0 | 1 | 6 |
| sweep native 0x5880-0x5b40 | 87 | 55 | 10 | 8 | 1 | 3 | 10 |
| wallet flags + ATA 0x5b40-0x5e70 | 101 | 69 | 17 | 5 | 1 | 6 | 3 |
| sweep token 0x5e70-0x60f8 | 81 | 54 | 15 | 3 | 3 | 1 | 5 |
| wallet collect arm 0x60f8-0x6800 | 220 | 165 | 21 | 14 | 1 | 12 | 7 |
| wallet coin CPI 0x6800-0x6b08 | 97 | 85 | 7 | 3 | 0 | 1 | 1 |

The unaligned instructions are the tail-duplicated gate and join tests, the spill and reload pairs of the do_coin flag and
the sweep payload, and the per-edge `ldxdw r1,[r10-0x950]` copies. All of them follow from register assignment (do_coin in
r8, payload in r9). None follows from the order of the source statements. This agrees with w14a24 (#3293: wallet
residual about 85% register naming, +0.036 splice bound) and with w14a06 (#3219: sweep join coalescing needs a change
to the Err-join CFG).

## 3. Sibling statement-shape screens (raw-IR capture + rx opt/llc oracle; `edits/`; newline counts and `line!()` sites kept)

| key | sibling idiom ported | bytes | ratio | vs main |
| --- | --- | ---: | ---: | --- |
| a0 | `collect()` early returns: each wallet msg! branch `msg!;return Ok(())` | 27,400 | 0.64649 | identical tokens |
| a7 | a0 + `*owner!=ID` deref compare + `require!(is_writable,..)` | 27,400 | 0.64649 | identical |
| a5a | `match executable{true=>msg,false=>if owner..}` (collect_creator_fee match-on-bool) | 27,400 | 0.64649 | identical |
| a5b | same, `false` arm first | 27,400 | 0.64649 | identical |
| a4a | `match *owner!=ID{true=>msg,false=>{body}}` | 27,400 | 0.64649 | identical |
| a4b | same, `false` arm first (collect_creator_fee polarity) | 27,400 | 0.64649 | identical |
| a1 | `let creator_key=current_creator.key()` hoisted before the native test, used in the event | 27,456 | 0.54646 | -0.100 |
| a6 | sweep PDA check through a `keys_eq(&a,&b)` helper (sweep_fees.rs) | 27,760 | 0.30565 | -0.341 |
| d1 | `let r=collect(..)?; if let Some(..)=r{..}` | 27,400 | 0.64709 | identical |
| d2 | `match collect(..)?{None=>{},Some(..)=>{..}}` | 27,384 | 0.57537 | -16 B, -0.072 |
| d3 | `match collect(..)?{Some(..)=>{..},None=>{}}` | 27,384 | 0.57537 | same tokens as d2 |

Spellings found in the ledger and not repeated here: wallet early returns on older mains (w10r1, w12a03), the wallet and
sweep helper signatures `(&AdminCto,&AdminCtoBumps)` (w14a01), sweep `keys_eq` on w13 mains, inline vault seeds at both
transfer calls (w9r1 t23, w12b12), seeds and bump spellings (w13a14, w13a34), the native-arm join spellings (w14a33), the
token-arm shapes (w14a27 b*/c*; b9 = `tvt?;return Ok(amount)` is 0.64879 @ 27,408 and w14a27 is repaying its size), and
the wallet/sweep size knobs (w14a31).

## 4. Conclusion

The angle is exhausted. There is no remaining sibling statement shape to port: the original's wallet and sweep outlines
already equal main's, the original does not follow the sibling's source shape in the sweep arms, and every wallet-level
spelling of the sibling's control flow (early return, match-on-bool in either polarity, binding the result) produces
main's tokens after MIR and LLVM. The remaining gap in these regions is the do_coin and sweep-payload register assignment
(r8 and r9 in the original), which only changes to the global live ranges or the CFG can move.

## Tools (scratch copies of the w14a03 `capvar.sh` / `rx.py` / `capraw.py` oracle were used, repointed to this lane)

- `tools/ann.py <rel.dis> [lo hi]`: admin_cto disassembly with function-relative offsets, call targets named from the baseline symbols.
- `tools/fdis.py <so> <addr> <size>`: the same for any function, here used for the sibling windows.
- `tools/cls.py <orig.rel> <cand.rel> lo hi ...`: per-region residual classes.
