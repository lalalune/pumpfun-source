# w3-sweep: 0x72810 `sweep::execute`

Base: origin/main 6654999 (1022 normalized / 276 raw). Target: 7,832 B, 39 direct calls.

| metric | base (main) | r1 (a08) | r2 (a22) | now (a23) |
|---|---|---|---|---|
| ratio (target_metric) | 0.46947 | 0.46985 | 0.48150 | **0.49139** |
| cand bytes (orig 7832) | 7688 | 7744 | 7840 | 7824 |
| direct calls (orig 39) | 38 | 39 | 39 | 39 |
| structural ratio (regs + stack offsets masked) | 0.8084 | 0.8096 | 0.8723 | **0.8805** |
| official normalized / raw | 1022 / 276 | 1022 / 276 | 1022 / 282 | 1022 / 276 |
| gains / losses vs main | - | none / none | 6 incidental raw gains (call-distance at 7840 B) / none | none / none |
| unstripped sha256 | | b25e6708.. | eb96c799.. | b7005220e751980610ffc30b5b52cfe6bdbd1bff9d5b0ce52113aa7759fe1cc5 |

a23 = a22 with `admit_quote_accounts(a: &mut SweepFees)`: a `&mut` param (like execute's own `a`) makes
LLVM reload payer/system_program from the accounts struct for each admit (orig +0xdd0), instead of
caching them across the calls as it may for a noalias-readonly `&`.

## Mechanisms found

1. **The per-bucket quote==default memcmp is rustc MIR JumpThreading, not LLVM.** With the fee take
   written as its own `let amount = if creator {take} else {take}` after the vault/validate dispatch,
   the MIR JumpThreading pass (mir-opt-level 2) threads the later `switchInt(creator)` of
   `creator && native` back through the raw_eq call, `Default::default()` and the zero check to the
   take switch (within MAX_BACKTRACK=5, cost < 100), duplicating the memcmp chain per bucket. When the
   take sits inside the vault/validate if/else the `switchInt(creator)` is more than 5 blocks away and
   nothing is threaded (that is why the prior lane could not get 39 calls with single evaluation).
2. **SBF `analyzeBranch` cannot analyze conditional branches**, so MachineBlockPlacement force-chains
   every conditional-branch block with its next block in IR order when that block is a successor.
   The layout is therefore mostly fixed by rustc's LLVM block creation order (first reference while
   codegenning MIR in reverse postorder; RPO visits the first switch successor first).
3. `match creator as u8 {1 => vault, _ => validate}` gives `switchInt -> [1: creator, otherwise:
   protocol]`, so the creator path is codegenned first; take_c then glues to msg and take_p falls into
   memcmp_p as in the original. `if creator` / `if !creator` both give `[0: protocol, ..]` (bool Not
   is normalized), protocol first, and the msg block glues to take_p (ratio 0.398).

4. **Rent top-up is a Result-returning helper** (`ensure_rent_exempt`, inline(always)): the original
   merges the `Rent::get` From error and the transfer Result in one phi before a single `?`
   (orig +0x1538 `jeq r1,2`), which inline `?`s do not give.
5. **`emit!(event); emit_cpi!(event)`** (both macros take `&event`) instead of `emit!(event.clone())`:
   the original builds the event once.
6. **Protocol-native threading = MIR JT through the recipient clone.** `match (creator,native)
   {(true,true)=>rent,(_,false)=>token,(false,true)=>{}}`: the explicit `(false,true)` arm gives the
   protocol-native edge its own (empty) MIR block, so MIR JT can thread the `if native {None}` Option
   switch back through the `to_account_info()` call (JT skips SwitchInt predecessors of multi-pred
   blocks, so `else if !native {token}` never threads). Verified in a synthetic MIR lab (jt/lab.py).
7. **Cold call sites**: after that threading the shared rent/token join's clone has pre-inline block
   frequency 1.5-1.7% of entry (< ColdCallSiteRelFreq 2%), so LLVM leaves it out of line (40 calls).
   The token admits in an inline(always) Result helper (`admit_quote_accounts`) merge the two admit
   errors, raising the join above 2%, and every clone is inlined (39 calls).

## Residuals (structural diff vs original)
- token helper region: arg spills (+8 at +0xde0), first-admit error branch shape (+0xf28).
- rent transfer block placed inline after lamports (orig places it after protocol-native, +0x14f0),
  Rent::get From placement.
- a few base_mint/quote_mint load orders, event bucket store order; stack frame offsets.

## Tools (lane scratch, ~/.cache/pumpfun-reconstruction/lanes/w3-sweep/scripts)
oracle.py (one-function llc oracle, 0.1 s), mkone.py, blk.py/bwscan.py (block move / branch weight
scans), mbp.sh (post-placement block order), sdiff.py (structural diff), trial.sh, capture.py (+MIR).

## Trials after a23 (all in ledger, none better)
- token helper `#[inline]` / no attribute / second admit as tail (0.473, 0.473, 0.450).
- `if let Err(e) = admit(..) { return Err(e) }` for the first or both admits (40-41 calls).
- rent helper bodies (`>= {Ok}`, `match`, `minimum > lamports`, `transfer()?; Ok(())`): identical or worse.
- event `bucket: creator as u8`: identical.
- token code in an immediately-invoked closure: 0.4695.
- IR oracle: inverting the lamports branch or IR block moves/branch weights on a23 give at most
  11 fewer structural diff lines; the rent transfer placement is not an IR-order/weight effect.

## Where the remaining distance is (a23)
- 157 stack operands differ by exactly +24 bytes (one extra 24-byte slot near the frame top in the
  candidate), 56 by +88, 33 by -56; 89 register-only differences.
- Structural (regs/stack masked) diff: ~350 lines, mostly the token-helper spills, rent transfer
  placement, base_mint/quote_mint load order at the join and protocol-native copy.

## Lab tools (scratch ~/.cache/pumpfun-reconstruction/lanes/w3-sweep/jt)
- `lab.py`: synthetic copy of the execute structure (externs), compiled with the hybrid rustc in
  ~0.1 s, dumps MIR before/after JumpThreading; counts memcmp/clone copies (F1/F2 screening).
- `labinl.py` / `labbfi.py`: same with `-print-before=inline` and `scripts/bfi.py` (homebrew opt
  print<block-freq>) to see pre-inline call-site frequencies (cold threshold 2% of entry).

## Near-match candidate a37 (40 calls) — `a37_sweep_fees.rs.txt`

a17 (tuple match, token code inline in execute) with the rent arm written as a Result-producing
`match`:

```rust
  (true,true)=>match Rent::get(){
   Ok(rent)=>{let minimum=rent.minimum_balance(0);if a.recipient.lamports()<minimum{transfer(..)}else{Ok(())}}
   Err(e)=>Err(e.into()),
  }?,
```

| metric | a23 (PR head) | a37 |
|---|---|---|
| target ratio | 0.49139 | **0.78830** |
| differing lines (llc oracle) | 1085 | 414 |
| stack operands at the original offset | 50 | **370** (all) |
| direct calls | 39 | 40 |
| official | 1022 / 276, no losses | 1022 / 276, no losses (sha 5f590f21..) |

Frame findings that led here: rustc creates allocas in MIR-local order (frame top = highest local),
AlwaysInlined helpers' allocas land at the frame top (a23's quote keys at -0x50..-0x70; original
-0x168..-0x1a0), so the original's token code is inline in execute; `Rent::get()?` leaves the
`Result<Rent>` SROA slice without lifetime markers (one uncolored 24 B slot, +24 on 150 operands),
while matching `Rent::get()` into a Result does not.

The only structural residual of a37 is the shared rent/token join's recipient clone: its pre-inline
block frequency is 1.47% of entry, below LLVM's ColdCallSiteRelFreq (2%), so it gets the cold
threshold (45) and stays an out-of-line `AccountInfo::clone` call (clone inline cost is >60:
`-inline-cold-callsite-threshold=60` still leaves it). In the original that site was inlined, so
the original's pre-inline CFG gives the join >= 2%. Frequency budget with the current CFG: p = c =
0.0427 after the zero check, rent 0.375c, the shared native switch 50/50 -> protocol-native 0.0347,
token entry 0.0347 -> token end 0.0087 (two admit `?` halvings), rent end ~0.006; any fix must lift
the join by ~1.37x while keeping protocol-native >= 2% and the MIR JT threading (only the
`(true,true),(_,false),(false,true)` arm order threads, checked in the synthetic lab).
