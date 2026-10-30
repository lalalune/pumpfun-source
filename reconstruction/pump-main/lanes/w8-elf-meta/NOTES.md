# w8-elf-meta: whole meaningful-ELF identity beyond .text

Lane of wave 8 (build inputs). Base: origin/main ce53d867a (rules #2221), identity recipe,
unstripped `31ec6381…`, stripped `1b04b8d4…`, 1,027/1,035 normalized and 276 raw against
`pump-main/baseline/score.json` (no losses).

## Result

There is no ELF-metadata difference left for a build input to fix. Every byte outside `.text`
that differs from `evidence/original/pump/deployed.so[:1934800]` (meaningful-ELF boundary,
zero allocation tail excluded, same rule as the Mayhem/Fees verifiers) follows from `.text`
content. With the current recipe, whole meaningful-ELF identity therefore comes down to
`.text` identity plus one `.rodata` literal swap, and that swap is controlled by source.

`elf_meta_diff.py` (in this directory) does the classification and exits 1 if any difference
is build-input-controlled:

```bash
python3 reconstruction/pump-main/lanes/w8-elf-meta/elf_meta_diff.py \
  evidence/original/pump/deployed.so $OUT/candidate.so --unstripped $OUT/unstripped.so --json $OUT/elf-meta.json
```

### Identical (already correct in the recipe)

| Item | Original = candidate | Controlled by |
| --- | --- | --- |
| e_ident, e_type DYN, e_machine SBF (247), e_version, ehsize/phentsize/shentsize | yes | linker (ld.lld in platform-tools v1.44) |
| e_flags | 0 (SBPF v0) both | target triple `sbpf-solana-solana` (identity recipe), no `-C target-cpu` / `+v1..v3` |
| program headers | 4 (LOAD RX .text, LOAD RW .rodata+.data.rel.ro, LOAD R dyn, DYNAMIC); flags and align 8 equal | target linker script in the rustc target spec |
| section table | 9 sections in the same order; type/flags/link/info/align/entsize equal; no .bss/.data | linker script, `--strip-all` |
| `.shstrtab`, `.dynstr` | byte-identical | strip mode, exported/imported symbol set |
| `.dynsym` | 19 entries, same names/order/info/size (custom_panic, entrypoint, 16 syscalls, abort) | source (`custom-panic`), syscall usage |
| `.dynamic` | same 11 tags in the same order (FLAGS TEXTREL, REL, RELSZ, RELENT, RELCOUNT, SYMTAB, SYMENT, STRTAB, STRSZ, TEXTREL, NULL) | linker |
| relocation types | identical multiset except +2 text R_SBF_64_RELATIVE; all syscall (type 10) relocs per symbol equal | text content |
| `.data.rel.ro` | size 0x2870, same 590 pointer slots, every non-pointer byte equal | text content (pointer values only) |
| `.rodata` | size 0x7d1f equal, one 86-byte permutation | source (see below) |
| stripping | `llvm-objcopy --strip-all` = `fastbuild` candidate (sha 1b04b8d4) | recipe (already correct) |

### Differences, all implied by .text

* `.text` is 0x230 (560) bytes larger: +512 from `v2_native_payments::ensure_rent_exempt`, a
  separate function that has no counterpart in the original (1,036 candidate functions vs 1,035
  windows), plus a net +48 from 7 unmatched windows (buy_handler +32, buy_exact_quote_in_handler
  +32, trade::buy_exact_quote +16, admin_cto -56, swap_hop -40, sweep +48, v3_buy_costs +16;
  create_v2 is already the same size). This shifts e_entry, every later section/segment address,
  the two exported `.dynsym` values and the `.dynamic` address tags by exactly D.
* +2 text R_SBF_64_RELATIVE relocations: `admin_cto::execute` has 86 lddw relocations against 84 in
  the original window 0x22a10 (all the other unmatched windows have equal counts). This adds 32 bytes to
  RELSZ, gives RELCOUNT 5879 vs 5877 and moves e_shoff/`.shstrtab` by D+32.
* `.rodata` 0x1b68cc..+86: the original has `programs/pump/src/creator/admin_cto.rs` and then
  `No canonical pump pool for this mint; curve only`; we have them the other way round. rustc
  creates constants in MIR reverse-postorder codegen order, and lld keeps module order. This is
  source (admin_cto.rs line 410 require! / line 766 msg!). w6r2-layout-rodata confirmed the
  mechanism (`0x22a10-main-a7135a6-rodata-410-nonintegral-require-v1`). It belongs to the
  admin_cto lanes, not to the recipe.
* `.data.rel.ro` pointer values: rodata pointers move by D. Text pointers follow function placement
  (layout order: the w8-linker-order and w6r1-layout-order lanes), including the documented
  0xa868 coincidence.

### Recipe trials (diagnostic)

| Trial | Meta verdict | Score |
| --- | --- | --- |
| identity recipe (current) | 0 build-input differences | 1027 / 276, no losses |
| `--recipe mac` (macOS v1.44 sbf-solana-solana target libs) | `.rodata` +12 B, 8 non-pointer `.data.rel.ro` bytes, cascading addresses | 1022 / 268, 5 losses |
| `--strip-unneeded`, `--strip-debug` | keep .symtab/.strtab: 14 structural differences | n/a |
| `--strip-sections` | drops the section table | n/a |

## Implications for other lanes

* Recipe lanes (toolchain, profile, linker, deps): run `elf_meta_diff.py` on each candidate. Any
  `build_input_differences` entry is a regression the current recipe does not have.
* The quickest whole-ELF lever outside the 8 windows is the extra 512-byte ensure_rent_exempt
  wrapper (see `raw-main-099b0dd-ensure-rent-twin-direct-v1`). Removing it brings `.text` to
  within +48 bytes of the original (D 0x230 -> 0x30). The remaining 48 bytes are in the unmatched
  windows. Rodata/data `lddw` immediates can only be raw-equal at D = 0.

Ledger: 01a5b3f55fb0488e8b4d00d84dd316a2 (census), acc3ff07dd3147f69a6a4bd7e844171f (strip
modes), 30fc21e06753424e8c7deda0eff2b840 (mac recipe).
