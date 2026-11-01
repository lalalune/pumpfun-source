# w17a04-shim-unlockra: shim track, register assignment (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 / 1647da0f2 (same `programs/pump/src`): 0.67436, 3,141 slots, M 2,251, 1034/1034.
Ledger: approach `unlockra`, keys `0x22a10-w17-5998913-unlockra-<trial>-v1`.

## Result

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main 1647da0f2 | 0.67436 | 2,251 | 3,141 | 27,400 | 1034 / 1034 | - | - |
| **rc1964** (this PR) | **0.67615** | **2,257** | 3,141 | 27,400 | 1034 / 1034 | none | 388 cases, 0 mismatches |

Unstripped sha (measure.sh) `49fc5491e3d21a50`.

## Mechanism: a weighted Rc-clone overflow trap re-sorts the spill-slot colouring

- The shim rewrites one `to_account_info()` in the sweep's `transfer_creator_fees_to_pump_v2` CPI literal,
  `token_program: a.quote_token_program.to_account_info()`, as the manual `AccountInfo` literal the derive produces
  (key, lamports, data, owner, rent_epoch, is_signer, is_writable, executable). Its `lamports` clone goes through
  `rcinc`, a copy of `Rc::inc_strong` (load strong, `llvm.assume(strong != 0)`, add 1, store, `if strong == 0 { trap }`)
  whose overflow test carries `llvm.expect.i1(.., false)`, a 1:2000 weight. Everything else in the IR is unchanged.
- `Rc::inc_strong` itself writes `core::intrinsics::unlikely(strong == 0)`, which is a no-op on this toolchain
  (w17a02 #3934), so the stock trap edge gets BPI's unreachable weight (about 1e-6). At 1:2000 the trap edge takes
  0.05% of the frequency, so every block after that clone runs 0.05% colder.
- That moves no instruction and no register. It changes the spill weights StackSlotColoring sorts by: 6 spill slots of
  the sweep / CPI region swap offsets (`-2376..-2416`), and the new numbering is closer to the original's (+6 M).
  `llc -filetype=asm` of the IR screen edit differs from main only in those 36 `[r10 - 23xx/24xx]` offsets.
- Spellings: `extern "C"{#[link_name="llvm.expect.i1"]fn expect..; #[link_name="llvm.assume"]fn assume..;
  #[link_name="llvm.trap"]fn trap()->!;}` and `#[inline(always)] unsafe fn rcinc<T>`, both on the blank line 8 of
  admin_cto.rs (no new line), and `#![feature(link_llvm_intrinsics)]` prepended to lib.rs line 1 (w17a02's gate;
  alone it is byte-identical). Every construct carries a `/*shim: ..*/` marker on its line.
- Peel target: an ordinary spelling that produces the same spill-slot numbering (the 6-slot swap) without the weight.

## IR screens (no build slot; `tools/`, post-opt slim `m.ll` of main, SDK llc, scorer metric)

`m.ll` reproduces main exactly (`rx.py`, ratio 0.67436, M 2,251, `eq_main: true`).

- `vscreen.py`: one edit per candidate: `vl` (load → `load volatile`, models `read_volatile`), `vs` (store volatile),
  `bl`/`bu` (`br` gets 2000:1 / 1:2000, models `llvm.expect`). 1,023 rows in `data/m0-vl-vs-b.jsonl` (vl/vs partial:
  w17a03 owns the full volatile screen and found the same `vl:1821`).
  - Only gains: `bu` on Rc `inc_strong` overflow traps in the TCF clone run (1964 / 1979 +6, 2051 / 2066 / 2179 +2,
    2007 / 2022 +1), `vl:1821` +1 (= w17a03 v4320, built: 0.67466, left to w17a03), `bu:204` +1 at 27,392 B and
    `bu:2912` +1 (unlikely sweep Ok, not a sensible hint).
  - Every `bl`/`bu` on a source-level condition is neutral or a loss as a single.
- `pscreen.py`: perturbs each conditional branch's default BPI probability (from `opt -passes=print<branch-prob>`) by
  x0.999 / 1.001 / 0.98 / 1.02 (models `llvm.expect.with.probability`, which also works on rustc 1.79-dev: probe in
  `data/rc1964.py`'s sibling notes below). No perturbation of a source-level branch gains. Many validate-region
  perturbations hit the same knife edge: -10 M at -8 B.
- `pabs.py`: absolute trap probabilities. The response is chaotic: at 1964, p = 1/2001 (expect) and 1e-2 give +6;
  1e-5 .. 3e-3 and 3e-2 give -4 at -8 B; 0.1 collapses. Stacking two weighted traps loses (`data/inc-combos.jsonl`).
- `force.py`: RAPRIO sticky llc forces on the same `m.ll` (w14a84/w15a24 llc, md5 8d71a7aa): `1685=r6` 0.67675,
  `+1672=r7` 0.67885, main's 9-force set 0.68425 @27,376, `1658=r9` 0.66807 @27,280. These are still the RA-only ceilings;
  no volatile pin or branch weight reached any of those colours in the screens.

`llvm.expect.with.probability.i1` works through the same extern (probe on the identity rustc):
`extern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}` gives
`branch_weights 804898347:1342585302` for p = 0.37481.
