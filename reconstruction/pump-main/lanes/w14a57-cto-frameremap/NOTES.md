# w14a57-cto-frameremap: frame remaps of admin_cto::execute (0x22a10) on main 6330811

Base: main 63308119b (0.65698, 3193 slots, 27,400 B). Ledger approach `frameremap`.
Result: notes only, no source change. One IR-only lead (+0.0012), no source form yet.

## Remaps re-measured (FRAMEPAIRS.txt, REGIONS.json regenerated with w14a38's tools)
- (a) Sharing CPI tail (orig 0x46b8-0x4970): the AccountInfo array stores are now at equal offsets. The remaining fm 34
  are spill-slot reloads, i.e. register-allocator order, not alloca placement.
- (b)/(c) Spill slot swaps (whole-function displacement what-ifs, tools/dispwhatif.py): -0x8d8<->-0x8e0 +0.0039;
  -0x8e8<->-0x950 +0.0024; -0x930<->-0x938 +0.0018; all three together +0.0081. These need StackSlotColoring weight order.
  w14a18 HV1-3 already tried the source spill-weight levers for these.
- (d) Error-name/to_string buffers (tools/errblk.py, keyed by PumpError constant): the original puts names at -0x488
  and buffers at -0x4b8. Ours puts names at -0x470, in the class of `_113.i`, the 32 B event signer-seeds alloca.
  Root cause (tools/scmap.py): in the original, `sk` (the sharing key copy) sits at -0x470 and is live across
  validate. That blocks the validate names from the -0x470 class. Ours merges `sk` into the 48 B authority_info class
  at -0x518, where the original keeps its holder_key copy.
- Displacement what-ifs that apply (d) site by site are non-monotone: they range from -0.036 to +0.0006, because
  difflib's greedy matching re-anchors.

## Mechanism: colouring is not pure frame
Kicking `sk` out of the authority_info class (IR lifetime edit, no instruction change) reproduces the original's
name/buf colouring exactly. It still changes the schedule and RA (0.53911 @ 27,384 B). Merged slots share MMOs, so the
machine scheduler sees different memory dependencies. Alloca colouring changes therefore move code as well.

## Lifetime screen (tools/ltscreen.py, ~37 s for 532 variants, llc only)
For every execute alloca: start hoisted to the entry (S0), ends dropped (E0), markers dropped (SE), and kicked out of
its colour class (K). 135 variants are byte-identical. The only one above main at 27,400 B:
`_12.i` (the name String of the 284 mayhem site, placed in the tail) kicked out of `_113.i`, which sends it to -0x488:
**0.65818** (+0.0012), with frame-masked code identical (segdiff lvl1 delta 0). No source spelling for it has been found.
Kicking any other validate name or buffer out of its class loses (0.498-0.6567).

## Next ideas
- Find a source form that makes the 284 name String overlap the -0x470 class (a validate-spanning 24/32 B local
  declared before the mayhem test). Check it with ltscreen K first, then capvar.
- A faithful holder_key copy (orig -0x518) with size repay, to move `sk` to -0x470. Earlier by-value forms collapsed
  (w13a48, w14a20).
