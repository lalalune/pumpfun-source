# w17a16-shim-outlinerepay: 307/312 to_string outline + the original's validate order, repaid to 27,400 B

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Shim track.
Main moved four times during the lane (bf01b5f M 2,270 -> 8330455 2,278 -> 8350fae 2,284 -> a51791e 2,288); every result
below names its base. Ledger: approach `outlinerepay`, keys `0x22a10-w17-<main7>-outlinerepay-*`.

## Result (on main a51791e2e, 0.68544)

| build | admin_cto ratio | M | bytes | lddw | normalized / raw | `.rel.dyn` vs original | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main a51791e2e | 0.68544 | 2,288 | 27,400 | 88 | 1034 / 1034 | +2 entries | |
| **this PR (q)** | **0.68553** | 2,289 | 27,400 | **86** | 1034 / 1034, zero losses | **equal (`rel_dyn_entry_delta 0`, relocation multiset equal)** | 388 / 0 |

- Both 307 and 312 `to_string` calls are outlined, as in the original: the callee multiset now equals the original's, and
  `elf_meta_diff.py` reports no relocation difference at all ("all non-.text differences follow from .text content";
  main had 2 extra `.rel.dyn` entries).
- The validate error blocks are in the original's order: from-order `289 298 306 296 326 312 307 330 338 334`, name-order
  `289 306 298 326 296 312 307 330 338 334` (main: `298 289 296 326 306 312 307` / `298 296 289 326 312 306 307`).
- Note: at 27,400 B two fewer lddw means two more instructions, so the outline candidate needs M >= main + 1 to rank higher.

### Mechanism (all on existing lines, every steering construct marked `/*shim:*/` on its line)

1. **Outline (line 306 + the shared arm on 339).** `tf_g3` (`let creator=a.bonding_curve.creator;` at the CtoState block
   head, `target=creator` in the shared non-holder arm; this replaces main's volatile/passthrough curve reload there) and
   `if expect_p(new.is_none(),true,0.75){306 err}else{read_unaligned(payload)}` (306 None 3:1). The 3:1 weight outlines
   both sites at validate's inliner visit; without tf_g3 every outline collapses (c1/g1c1/tfvc1).
2. **Validate order (lines 289/296/298).** The head is written explicitly threaded:
   `let target=if match st.holder_reward as u8{1=>{if !(hopt==Some(true)){289}true}_=>if expect_p(holder,true,0.49){296 check;true}else{false}}{298 test;*holder_key}else{non-holder arm}`.
   - MIR jump threading hands LLVM an already-threaded CFG, and rustc's creation order leaves the holder_enabled test
     (`bb16.i`) unglued from both successors (BPF pre-merges a conditional-branch block with its ISel layout successor);
     with P(!holder) 51:49 on the `!hr` holder test MBP then lays out the original order (llc-only screens: any order
     with `bb16.i` unglued gives the same bytes).
   - **The `as u8` integer match is load-bearing for the constant pool.** With `if st.holder_reward{..}` RPO codegens the
     non-holder arm (306) before the 289 arm, so the 4-byte constants k_u32_89/k_u32_83 swap in `.rodata.cst4` and
     `creator_migration::execute` (0x37e08) loses its raw match (lddw 0x1b5e78 -> 0x1b5e7c). `match x as u8{1=>..,_=>..}`
     is a switchInt `[1: hr arm, otherwise: else chain]`, which RPO visits hr-first while still creating the else chain
     block first. The function bytes are identical either way (X5 vs X5m: same signature).
3. **Repay (+192 B):** `crl3` (`let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}..`, +72 B, 0 M),
   `expect_p(shared,true,0.625)` on the shared split (+56 B, +1), compares kept in memory with
   `{let mut c=false;unsafe{write_volatile(&mut c,X==Y)};c}` at the holder-vault key test (hvw, +32, +4; w17a06's
   vs:sweep cell), `st.creator==default` (cdw, +32, 0), the wallet `collection_native` (cnat, +40, -3) and the wallet
   `current_creator.owner` test (wown, +32, -5).
4. **Weights/peels:** `expect(t==*holder_key,false)` on the second 312 compare (+4 at 0 B, from the llc sweep), and main's
   default-quote `expect` removed (inert on this base: byte-identical).

## Tables

### Outline base on bf01b5f (main M 2,270)

| cell | bytes | M | lddw | note |
| --- | ---: | ---: | ---: | --- |
| c1 (`cold()` at 306 Some) | 27,000 | 2,002 | 86 | collapse |
| tfc1 (tf_g3 + c1) | 27,048 | 2,220 | 86 | exact LCS 2,269 (-6): the -50 is difflib alignment (312 block before V3) |
| tfcp75 / B75 (tf_g3 + 306 3:1) | 27,112 | 2,251 | 86 | = tfc1 + llc 3:1 on the 306 tag test, token for token |
| tfp67 (p 0.6667) | 27,272 | 2,247 | 87 | 312 stays inline |
| B75 + llc C1-pred order + bb14 51:49 | 27,064 | 2,278 | 86 | (w17a11's order, llc-only) original error order exactly |
| **b75Dx49 (threaded head, source)** | 27,128 | **2,277** | 86 | exact LCS 2,287 (+12 over main) |

`framemap.py`: tfc1's frame hosts are main's (only FIs renumbered), so no MaybeUninit stand-in was needed.

### Repay prices

| piece | base | bytes | dM | |
| --- | --- | ---: | ---: | --- |
| crl3 | B75 / Dx49 (all mains) | +72 | 0 | free |
| k8 PDA-first, b01, Fa, t1n | B75 | -32 / -88 / +176 / -96 | collapse (-388..-828) | |
| p8 aligned validate return | Wm2 (8350fae) | -248 | collapse | |
| shared split `expect_p 0.625` | V (8330455) | +56 | +1 | |
| hvw / pow (w17a06 write_volatile compares) | V+shw | +32 / +32 | +4 / +2 | not additive (+hvw+pow -6) |
| cdw / cnat / wown / wexe / f660 / f719 / f410 / sco / qnat / snat | WmC (8350fae) | +32 / +40 / +32 / +8 / +32 / +40 / -128 / - / - / - | 0 / -3 / -5 / -4 / -6 / -9 / collapse / collapse / collapse / collapse | |
| remove main's pt1 on the 298 test | WmC | -8 | +1 | moves k_u32_90 earlier: raw loss risk, not used |
| `expect(t==*holder_key,false)` | Wm2 (8350fae) | 0 | +4 | |

### Final assembly on a51791e (main 2,288)

| cell | bytes | M |
| --- | ---: | ---: |
| Vm (tf_g3 + 306 3:1 + crl3 + threaded head) | 27,208 | 2,289 |
| Wx (+ shw + hvw + cdw + noq + nopt1 + x312h) | 27,320 | 2,298 |
| q = WmC + noq + x312h + cnat + wown (pt1 kept) | 27,400 | 2,289 (landed) |
| u = WmC + noq + x312h + wown + pow + wexe | 27,400 | 2,289 |
| Z1x (with nopt1) | 27,400 | 2,290, but the 298 constant moves (raw-loss risk) |

## Leads for the next lane

- The base before repay is far above main: Wx is 2,298 @27,320 (+10). The repay costs 8-9 M for its last 72-80 B; any
  cheaper 80 B (or a faithful piece that adds bytes) lands directly. IR-beam cells with +8..+24 B at >= 0 M exist in the
  wallet `?` residuals (`vs:wallet:*` on `_184`, the `token_frozen(..)?` Err residual) but have no source spelling yet.
- llc sweep on Wx: the fee switch (`%switch13.i`, 20:12) gives +2 at -8 B.
- The CtoState-literal/flag order, the E3 `new` pieces and PDA-first still collapse on this base.
- Peel candidates: the 306 `read_unaligned` payload read, the `as u8` match (needed only for the constant pool order).

## Tools (`tools/`)

`g16.py` (genes: the outline base, the threaded head, every repay piece; exact single-occurrence edits, line count
asserted), `cap.sh` (crate copy + genes + capraw + preslim + fx + framemap), `meas.sh` (crate copy + genes + measure.sh +
388-case differential), `pw.py` (llc-time branch weights on a post-opt slim module), `bsum.py` (execute post-opt block
summary: error codes, calls, terminators), `info.py` (lddw count and error orders), `mbb.py` (final MBB order from the debug
llc). The constant-pool order check is `sed -n 85,101p ir/<name>.s.ll` on the slim pre-opt module (k_u32 order must be
`T M N 1E S 13 Y P [ Z X` as on main).
