# w4-sweep: 0x72810 `sweep::execute`

Base: origin/main 630a074 (1023 normalized / 277 raw). Target: 7,832 B, 39 direct calls.

| metric | base (main, a23) | a37 (w3 near-match) | p1 | s6 (PR head) |
|---|---|---|---|---|
| ratio (target_metric) | 0.49139 | 0.78830 | **0.82199** | **0.88669** |
| structural ratio (regs + stack masked, llc oracle) | 0.8805 | 0.8926 | **0.9403** | 0.9459 |
| cand bytes (orig 7832) | 7824 | 7528 | 7768 | 7880 |
| direct calls (orig 39) | 39 | 40 | **39** | **39** |
| stack operands at original offset | ~50 | 370 | **398 / 403** | 398 / 403 |
| official normalized / raw | 1023 / 277 | 1023 / 276 | 1023 / 276 | 1023 / 276 |
| gains / losses | - | raw 0xa868 | raw 0xa868 (call-span drift, see below) | raw 0xa868 (call-span) |
| unstripped sha256 | 5d661a63.. | d010211c.. | cc82d04c55efda15d3f5df34b54307cd49183e408d34466597d8246b06a8ed69 | b944e16bdfb2f1b523b56b94c877134b0984a0d5dc6e51f06ee03ae711782033 |

## Mechanism

a37 (token code and quote keys inline in execute, so the frame matches) had 40 calls because
the shared rent/token join's `AccountInfo::clone` had pre-inline block frequency 1.469% of
entry (< ColdCallSiteRelFreq 2%), so it stayed out of line.

- Merging the two admit errors inside execute (`match admit1 {Ok=>admit2,Err(e)=>Err(e)}?`,
  `admit1.and_then(|()| admit2)?`) does not help: MIR JumpThreading threads the `Err` constant
  through the merge, so the pre-inline CFG still has two independent halvings (0.01469).
- p1 keeps `quote_mint`, `quote_token_program`, `quote_mint_info`, `quote_token_program_info`
  as execute locals (their allocas stay mid-frame in MIR-local order), and moves only the two
  `admit_associated_token_account` calls into an `#[inline(always)]` helper taking them by
  reference. The helper is too big for the MIR inliner, so it is LLVM-AlwaysInlined: its Result
  return is a phi that the later `?` re-splits 50/50, and the join's frequency becomes 0.02337
  (>= 2%). The join clone is inlined: 39 calls. Its only new allocas are the by-value Pubkey
  copies, which colour onto the original's slots.
- With the second admit as the helper's tail expression (or `let r=admit1(..);r?;`), the
  bonding-curve `to_account_info()` temporary is dropped before the first admit's error branch,
  as in the original (+0xe88..+0xf20). With `admit2?; Ok(())` the drop is duplicated per edge
  (0.747).

## s6: rent top-up back in an LLVM-inlined helper

`(true,true)=>ensure_rent_exempt(..)?` with `#[inline(always)] fn ensure_rent_exempt` whose body is
`let minimum=Rent::get().map(|rent|rent.minimum_balance(0))?; if lamports<minimum {transfer(..)} else {Ok(())}`.
As a helper the merged Result (From error / transfer / Ok) is not MIR-jump-threaded, so the
original's single `jeq r1,2` test after From and transfer comes back; `map` keeps the frame
(no uncolored ControlFlow slice) -> 0.8867.

IR-oracle finding (e2 = same helper with `let rent=Rent::get()?`): the original's frame and the
payload copy before the Rent::get branch (+0x1290..+0x12b8, From reading -0xd0) are exactly the
`?` ControlFlow payload slice *with* lifetime markers (oracle 0.8808, 410 stack operands at the
original offset). In source builds MemCpyOpt's stack-move merges `val`/`residual` into that slice
and drops its lifetime markers, so it is an uncolored 24 B slot at the frame top (+24 on 288
operands, 0.5497).

## Raw membership 0xa868

0xa868 (`<&T as Debug>::fmt`, 24 B) is a raw match only through call displacement: its tail call
crosses sweep::execute, and it matches raw only when sweep is exactly 7824 B (base). Any sweep size
change (a37 7528, h1 7864, p1 7768, and the original's own 7832) loses it until the other +8 B
drift in that span is fixed.

## Residuals at s6 (fullmask diff 64 lines)
1. Admit branch polarity (3 insns): IR oracle (scripts/mv2.py, s6a) shows it is only IR block
   order: the protocol-native clone chain must sit between the first admit's drops and the second
   admit (as in a37, where admit2 is a MIR block created after bb27). With the LLVM-inlined
   helper the two admits are contiguous. Oracle fix 0.8867 -> 0.8898.
2. Rent payload slice lifetime (see s6 section): oracle e2+lifetime = 0.8808 with the exact
   payload copy; no source spelling found that avoids MemCpyOpt's stack-move (LLVM 18.1.7 erases
   lifetime markers of merged allocas).
3. Join loads: original loads quote_token_program/quote_mint fields after the Option diamond
   (+0x16d8); ours hoists them. Binding the Options/recipient in lets breaks MIR JT threading
   (0.52-0.69).

## Older residual notes (p1)
1. Admit branch polarity: original first admit `jeq r1,2,+1; ja err`, second `jne r1,2,err`;
   p1 has them the other way round.
2. Rent::get error: original places the `From<ProgramError>` block after the protocol-native
   clone (+0x14b0, reached by `jne r1,0` at +0x12c8, Rent copied to -0xd0 first); p1 calls From
   right after Rent::get.
3. Some field load orders (+0x10/+0x58/+0x30) at the join and in the protocol-native copy.

IR block-move scans (blk.py) on p1 give at most 5 fewer structural lines; the residuals are not
block order alone.

## Tools (reconstruction/pump-main/lanes/w4-sweep/scripts; lane scratch has the full set)
bt.sh (trial + pre-inline BFI listing), par.sh (3 parallel trials), mv2.py (IR block-range move
with value renaming for the llc oracle), fm.py (full-mask diff count), stkmap.py (orig->cand stack
slot map), blist.py (IR block list), tgt.py (branch targets), lt_e2.py (lifetime-marker IR edit).
