# coordinate-archaeology lane notes

Lane `coordinate-archaeology` of the main-Pump byte-matching swarm. This lane enables the others:
it maps every source coordinate (Anchor `Source{file,line}` sites and `core::panic::Location`
records) in the 16 unmatched windows between the deployed program and our build. Base: origin/main
d2cb88d plus the merged #1171 harness.

Machine-readable output:
- `LINEMAPS.json`: one entry per target. Each original site has its order, slot, file, line,
  column or error code (with the PumpError/Anchor name), and is paired with our site (order, slot,
  line, statement kind, and the text at our line). Each target also records whether the site
  order is identical.
- `IMMEDIATES.json`: per target, the multiset of error-code immediates (2000..7000) and of
  string literals, comparing original with ours.
- `tools/`: the extractors (`linemap.py targets|locset|scan`, `build_linemaps.py`, `imms.py`,
  `strcensus.py`, `lddw_content.py`). Run them with `python3 -I`. They import
  `$TOOLS/harness/{score,coords}.py`.

## Headline results

1. **Line numbers are solved for all 16 unmatched windows.** After the fix below, every
   original Source or panic site matches one of our sites with the same file, line, column and
   error code. Remaining differences:
   - `0x5b3b0` swap_hop has one extra site that the original lacks: multi_hop_curve_swap.rs:581
     `require!(q != 0, PumpError::Overflow)`. It is also the only target whose error-code
     multiset differs (+1 × 6024).
   - Five targets emit the same sites in a **different order**: `0x80df8`, `0x1e7c0`, `0x77940`,
     `0x5b3b0` and `0x22a10`. This comes from block layout or codegen order, not from line numbers.
   - `0x4c158` create_token_account_v2 has no Source or panic sites on either side. Its
     error-code multiset is equal.

   So none of the 16 windows can be fixed by line numbers alone. The remaining work is CFG and
   statement shape. Lanes can rely on these coordinates staying fixed while they restructure code.

2. **Fix in this PR: two panic-Location lines in sell.rs.** `process_cashback_inner` (0x6cd78)
   references `Location{sell.rs, 76, 13}` and `{sell.rs, 77, 13}` in the original. Ours had
   60/61. These are `data[..8].copy_from_slice(DISCRIMINATOR)` and
   `data[8..40].copy_from_slice(user_key)`. I moved the two statements 16 lines down, inside the
   existing pad block, without changing the file's line count. Effects:
   - `.text` and `.rodata` are byte-identical to the baseline. `.data.rel.ro` changes by 2 bytes.
   - Official score: 1019 normalized / 188 raw, zero gains, zero losses. No score change is
     expected, because Location content sits behind a masked lddw.
   - The whole-program multiset of panic `Location (file,line,col)` (142 records) now **equals
     the original's**. Before the fix, these two lines were the only difference.
   - Ledger: `07a61bdab36e431395ceb5a07eacd85d`.

3. **Bug in `coords.py`.** It takes the *first* `stw [r10+X+8]` within ±30 instructions as the
   line. When consecutive error sites reuse one stack slot (common in admin_cto, create_v2 and
   claim_v2), that store belongs to the *previous* site, so lines get mislabeled. For example,
   coords.py reports admin_cto 306 as 284 and claim_v2 310 as 305. With that bug, about 10 fake
   line mismatches show up across 0x1e7c0, 0x77940 and 0x22a10. `tools/linemap.py` instead takes
   the nearest store in the same straight-line run, and reads the error code from
   `stw [r10+X+136]` (392 of 392 original sites follow this pattern). Use `LINEMAPS.json`,
   not raw coords.py lines, before "fixing" any line.

4. **Literal that only the original has: `"Creator is a program; fees left in the vaults"`**
   (original rodata 0x1b699d, used at 0x24718 in admin_cto 0x22a10). The original branches on
   `current_creator.executable` first and logs this message. Only after that does it check the
   owner against the system program and log `"Creator is not a system-owned wallet; …"`. Our
   source has only the second message. Across the whole program, this is the only original
   string literal missing from our image; the other census hits are length-heuristic noise.
   Experiment `cto1`:
   `if a.current_creator.executable{msg!("Creator is a program; …");}else if !wallet{msg!(…)}`.
   Results: zero losses and the literal is restored, but the ratio fell from 0.0952 to 0.0773
   (difflib is unstable this far from a match). The change is semantically required, but it is
   not in this PR's source. Ledger: `509950343b63499582f84b283ee29b95`. **For admincto-reconstruction.**

5. **swap_hop site 581 (for multihop-reconstruction).** I tried replacing
   `require!(q != 0, Overflow); let effective = q - 1;` with `let effective = sub(q,1)?;`.
   Results:
   - The coordinate sequence now equals the original exactly (6/6 sites, same order).
   - Ratio rose from 0.15752 to 0.15764, but internal calls fell from 94 to 92 (original: 107)
     and size fell from 18056 to 17904 (original: 18584). That is not strict progress, so the
     change is not in the source.
   - Ledger: `9976071f032f43f6b730d45c698ef801`.

   The original performs the q==0 Overflow check without an inline Source, for example through
   an outlined helper.

## Original site order compared with ours (`p` = panic Location, `*` = only in ours)

```
0x80df8  v3_buy_costs      orig: 1939p 2559p 371 375 1936p
                           ours: 2559p 371 375 1936p 1939p
0x1e7c0  create_v2         orig: 716 774 732 738 719 258 198 778 205 541 758 210 2559p 709 547 553 220 243
                           ours: 716 732 738 719 205 198 210 243 774 758 778 2559p 709 547 541 553 220 258
0x77940  claim_v2          orig: 2559p 305 310 342 333
                           ours: 2559p 305 310 333 342
0x5b3b0  swap_hop          orig: 2559p 484 546 686 599 590
                           ours: 2559p 484 546 581* 686 599 590
0x22a10  admin_cto         orig: 289 298 306 296 326 312 307 330 338 334 410 719 648 660 2559p 284 556
                           ours: 296 289 326 298 2559p 284 306 307 312 330 334 338 410 556 660 648 719
```

Reading the order as cold-path layout:
- v3_buy_costs: in the original, both protocol_fee_split `checked_sub(..).expect` (lib.rs:1939) checks branch
  to ONE merged panic block placed inline right after the second split (0x80fe8; first split `jgt r6,r0,+0x1e`,
  second split `jlt r1,r9`). Our build sinks it to the tail next to the 1936 `try_from(..).expect` panic. The
  1936 checks are the `jgt hi,0x270f` tests after `__multi3`, and they do go to the tail in both builds.
- create_v2: the quote-mint validation group (205/198/210/243) sits late in ours. In the
  original it is split: 258/198 come early, 205/210 in the middle, and 220/243 at the end. 774
  (CreatorFeeNotConfigurable) and 778 (CreatorFeeBpsOutOfRange) are early in the original.
- claim_v2: the original emits 342 (InvalidCashbackRecipient) before 333 (AccountTypeNotSupported).
- admin_cto: the original emits the 284 mayhem check and the 556 not-writable check *last*, as
  cold blocks at the function tail. Ours emits them early or in the middle.

The original files per window match our file assignment for every target: buy.rs, trade_v3.rs
(+lib.rs), sell.rs, buy_v2.rs, sell_v2.rs, sweep_fees.rs, create_v2.rs,
token_incentives/claim_token_incentives.rs, multi_hop_curve_swap.rs, creator/admin_cto.rs.

## The 831 normalized-only windows (raw blockers)

- `linemap.py scan`: all 1019 normalized windows have **identical** site sequences, covering
  292 Source sites and 369 panic Location references with the same file, line, column and code.
  No coordinate blocks raw identity. This confirms prior raw-layout-relocation's
  `same_path_line_sequence: 831` and extends the check to panic Location content.
- Normalized equality fixes every unmasked immediate, so the only raw blockers are masked
  lddw/call values. `lddw_content.py` compared the data behind each masked lddw pair. Every
  difference it found was a layout artifact:
  - .text function-pointer values inside vtables (175 hits);
  - over-read neighbours of packed strings;
  - pubkey tables whose first 32 bytes are equal.

  None was a content difference.
- Order of panic Location records in `.data.rel.ro` (raw/whole-ELF only; their content now
  matches). The original places the admin_set_idl_authority.rs (86/101/96) records before
  create_v2's, and lib.rs 1939/1936 right after lib.rs 1477/1478. It also swaps
  distribute_creator_fees.rs:327 with distribute_creator_fee_v2.rs:342, and places
  volume_accumulator.rs:436 after 431. This is emission order, so it moves with CGU and
  function order (see prior raw-layout-relocation).
- Prior raw-layout-relocation's `SUMMARY.json` (source_coordinates) agrees on 831/831
  same_path_line_sequence and on 0 coordinate-only equal-length candidates. Its unmatched
  coordinate extraction used coords.py and therefore inherits the stack-slot mislabel above.

## Ledger rows

| attempt | target | status | mechanism |
| --- | --- | --- | --- |
| 3c120455d2ef4f16bbcefd8a65e12671 | all | analyzed | coordinate line-map census |
| 07a61bdab36e431395ceb5a07eacd85d | 0x6cd78 | built | sell.rs panic Location 60/61 to 76/77 (this PR) |
| 9976071f032f43f6b730d45c698ef801 | 0x5b3b0 | partial | drop Source site 581 using the `sub(q,1)?` helper |
| 509950343b63499582f84b283ee29b95 | 0x22a10 | partial | restore the "Creator is a program" msg branch |
