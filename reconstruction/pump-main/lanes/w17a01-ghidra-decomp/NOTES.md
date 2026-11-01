# w17a01-ghidra-decomp: Ghidra decompilation of admin_cto::execute (original and main)

This is an analysis lane: there is no source change and no build. The target is `admin_cto::execute` at 0x22a10
(27,400 B), at 0.67436 on main 599891304, M 2,251 of 3,339.

## What is here

| file | content |
|---|---|
| `orig_admin_cto.c`, `ours_admin_cto.c` | Ghidra 12.2 pseudo-C of the original and of main 599891304, with every call, syscall and constant named |
| `ghidra_out/{orig,ours}_admin_cto.addr.c` | the same C, each line prefixed with the window offsets of its instructions |
| `ghidra_out/*.lst` | Ghidra listing with callee names and lddw data comments (3,339 / 3,337 instructions) |
| `ghidra_out/*.cfg.json`, `*.cfg.dot` | basic-block CFG (378 / 373 blocks): offsets, sizes, calls per block, successor kinds, exit/noreturn terminators |
| `ghidra_out/*.calls.json` | the 157 calls in address order, with the decompiler's statement text (arguments as Ghidra recovered them) |
| `ghidra_out/*.frame_ghidra.json` | decompiler high symbols with r10 storage offsets, sizes and types |
| `frame_map.json` | r10 census per side: every slot with reads, writes, lea, sizes, regions and first/last offset, joined to the Ghidra names |
| `regions.json`, `REGIONS_TABLE.md`, `regions/*.c` | 19-region comparison (generated) and per-region C excerpts |
| `REGIONS.md` | hand-written region diff: the original's shape against ours, with concrete structural and data-flow differences |
| `CALIBRATION.md` | how Rust/Anchor idioms look in this pseudo-C, calibrated on byte-matched siblings (`calibration/*.addr.c`) |
| `decode_check.json` | Ghidra decode vs `win.py`/objdump decode: 3,339/3,339 and 3,337/3,337 instructions, 0 mismatches |

## Reproduce

Building the tools takes about 2 minutes per program, uses no build slot and needs no network.

```bash
L=reconstruction/pump-main/lanes/w17a01-ghidra-decomp
$L/run_ghidra.sh orig evidence/original/pump/deployed.so 0x22a10
$L/run_ghidra.sh ours ~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so 0x22a10,0x38fc0,0x1308c0,0x10a0e0,0x29518,0x116718
python3 /Users/shawwalters/.cache/pumpfun-reconstruction/w16-strategy/ceilings/decomp.py <unstripped.so> --lcs > lcs.txt   # token values
python3 $L/regions.py ~/.cache/pumpfun-reconstruction/lanes/w17a01-ghidra-decomp/ghidra_out $L --chunks lcs.txt \
  --orig-so evidence/original/pump/deployed.so --ours-so <unstripped.so>
```

To decompile any other candidate, run `run_ghidra.sh ours <candidate unstripped.so> 0x22a10` with `SYMS=<that file>`,
then `regions.py`. A shim lane can diff its candidate's pseudo-C against `orig_admin_cto.c` region by region.

## How the SBF fix-ups work (`prep.py` + `ghidra_scripts/SbfDecomp.java`)

- **Import.** Ghidra has no SBF loader (e_machine 263), so the ELF is imported raw at base 0, which works because
  offset == vaddr in every LOAD segment. The language is the stock `eBPF:LE:64:default` and auto-analysis is off.
  Projects live in `~/.cache/pumpfun-reconstruction/ghidra/`. Ghidra rejects dot-prefixed path elements, so the
  script reaches that directory through a `$TMPDIR` symlink. The raw block is split by section with real permissions.
- **Calls.**
  - Internal calls are `call imm` with src=1 and a pc-relative imm. The stock `CALL disp32` decodes them correctly.
  - Syscalls are `call -1` plus an `R_BPF_64_32` relocation, which the stock module decodes as a call to itself. Each
    site gets a primary `CALL_OVERRIDE_UNCONDITIONAL` reference to a named stub with a Solana prototype (`sol_log_`,
    `abort`, ...).
  - `custom_panic` is reached the same way but is a defined function, so its sites are pointed at the function itself.
- **Names and noreturn.** All 1,035 functions are created from main's unstripped `.symtab` with demangled names.
  1,034 are byte-identical in both files, and every function sits at the same address. Functions with no `exit` in
  their body (30) are marked noreturn, and their call sites lose their fall-through.
- **lddw data.**
  - `R_BPF_64_RELATIVE` immediates are image vaddrs. Each gets a data reference and a label: `s_<text>` for strings,
    well-known program ids by name (`PUMP_FEES_PROGRAM_ID_1b7a61`, `NATIVE_MINT_1b5cc8`, ...), `k_u32_<n>` for pooled
    scalars (the `&PumpError::X` discriminants), and `obj_*` for sized `.L__unnamed` objects.
  - Sized objects become typed data (`string[n]`, `byte[32]`, `uint`).
- **Stack.** The stock cspec already treats R10 as the stack pointer, so `[r10-X]` become `*Stack_X`. Stack arguments
  arrive through `param_5` (`*(param_5 - 0x1000)`, ...).

## Findings (details in REGIONS.md)

1. **Validate error-block layout order** (by PumpError discriminant / source line):
   - original: 289, 306, 298, 326, 296, then 312/307 with outlined `ToString::to_string`, then 330, 338, 334;
   - main: 298, 296, 289, 326, 312, 306, 307, 330, 338, 334.

   From 410 onwards the two agree. The only callee-multiset difference in the whole function is the 312/307
   to_string outline: the original makes 2 `to_string` calls where main makes 2 `Display::fmt` calls.
2. **Entry.** The original calls `find_program_address` first, into the aligned 32-byte scratch slot -0x2d0 that `sk`
   and `Pubkey::default()` reuse. Main tests `shared` first and puts the `(Pubkey,u8)` sret at the odd slot -0x679,
   then copies holder_key in 7+1-byte pieces.
3. **`new` data flow.** The original loads all SROA pieces of the `new` stack argument at +0x4d8..+0x538: u8@0,
   u32@1, u24@5, u64@8, u64@16, u64@24, u8@32. It keeps them across validate and uses them for J1's target and for the
   C1 sharing CPI argument.
   - The CPI argument is a packed `Option<Pubkey>` at [-0x651,-0x630), with the payload 8-aligned at -0x650.
   - The sharing_update test is `new.tag != 2`: `Some(new)` is bit-identical to `new`.
   - Main keeps a separate tag local and a 32-byte copy at -0x560, and has the object 8 bytes higher. That object
     accounts for all of C1's frame difference: 147 of C1's slots are common.
4. **T1 (TCF) frame already matches.** 228 of 230 r10 slots are common. T1's 207-token exact gap is register naming
   and scheduling, with a masked gap of only 24.
5. **Small order flips.**
   - Sweep gate: the original lays out `token_raw_amount` before `token_frozen`.
   - Pool gate: the original does `memcmp(owner, AMM)` before `data_is_empty`, with one `accounts[0xe]` load.
   - CtoState flag-byte stores: the original order is -0xe, -0xf, -0x10, -0xd, -0xb, -0xc; main stores -0xd first.
6. **Frame.** Both frames are 0x1000 deep (outgoing stack args at the bottom) with 414 and 413 slots. Arg spills:
   original r4→-0x928 and r3→-0x918; main r4→-0x910 and r3→-0x8e8 (r1 and r2 agree).

Token budget (w16 ceilings `--lcs`, attributed by region; exact gap / masked gap):

| group | exact gap | masked gap |
|---|---:|---:|
| entry + validate | 345 | 189 |
| C1 sharing CPI | 226 | 57 |
| T1 TCF | 207 | 24 |
| W2 wallet body | 98 | 12 |
| J1/J2/W1/S1 | 110 | 38 |

## Proposed shim lanes

The full proposals are in the structured result and in `SUMMARY.json`:

1. `pdaslot` (E1)
2. `newpieces` (E3 + J1 + C1)
3. `vorder` (V1–V5, including the 312/307 outline; coordinate with w17a02)
4. `ctostate-store` (E2/E3 flag-byte order)
5. `pool-gate` (P1)

## Ledger

Recorded as `0x22a10-w17-599891304-ghidra-decomp-v1`, status `analyzed`.
