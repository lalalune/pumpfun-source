# w17a15-shim-passthrough: `llvm.bpf.passthrough`, a zero-footprint shim (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Wave 17 SHIM track. Base: main bf01b5fd9 (0.68005, M 2,270), merged with d5751b26e (#4011, 0.68065) before landing.
Ledger: approach `passthrough`, keys `0x22a10-w17-bf01b5f-passthrough-<item>-v1`.

## 1. The construct

```rust
extern "C"{#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64;
           #[link_name="llvm.bpf.passthrough.i1.i1"]fn pt1(seq:u32,v:bool)->bool;
           #[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(seq:u32,v:u8)->u8;
           #[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}
```

Declared on line 8 of admin_cto.rs (no new line; `link_llvm_intrinsics` is already on lib.rs line 1). The call is an
`IntrNoMem` intrinsic call: `opt -O3` keeps it and cannot fold through it. The SBF backend's `BPFCheckAndAdjustIR`
(in llc's `addIRPasses`, before CodeGenPrepare and ISel) replaces it with its argument, so it emits **no instruction**.
In MIR it is an opaque `Call` terminator, so MIR JumpThreading/GVN cannot see through it either.

Rules: use a distinct constant `seq` per site (identical calls are CSE'd); never `llvm.bpf.compare` (crashes this
backend). Every use carries `/*shim: passthrough ...*/` on the same line.

## 2. Calibration (main bf01b5fd9)

| variant | slim oracle | real build (measure.sh) |
| --- | --- | --- |
| main (fresh build of the worktree) | M 2,270 @27,400, sig 6ebb02255691 | unstripped sha 69f35a15bc2a5d9e |
| cal0: the four declarations only | identical | **69f35a15bc2a5d9e (byte-identical)** |
| cal1: + `let nf=unsafe{pt64(1,a.bonding_curve.creator_fee_bps)}` (line 761) | identical (unmasked fn.bin too) | **69f35a15bc2a5d9e (byte-identical)** |

So a neutral passthrough, including its MIR block split, is byte-identical. Note: the `current-baseline/unstripped.so`
(748fbfba...) differs from a fresh build of the same main source by 19 masked tokens inside admin_cto (a spill-order
difference near 0x26da0), with the same ratio and slots. The slim oracle matches the fresh build masked-exactly.

### Fold table (`tools/ptprobe.rs`, identity rustc, sbpf-solana-solana, opt-level 3; about 1 s)

| fold | without pt | with pt | probe |
| --- | --- | --- | --- |
| InstCombine/JT on a constant tag phi with a store user and a compare user | tag test threaded into the arms; phi kept only for the store | ONE phi (r7) with both users, tested with `jeq r7,0` | a0/a1 |
| select formation / SimplifyCFG speculation | `x=if c{a+7}else{b}` becomes a select (add hoisted above the branch) | not speculated: add stays in its arm, phi | b0/b1 |
| compare on an `Option<bool>` byte | `ldxb; and64 r1,1; jne r1,0` | `transmute`+`pt8`: `ldxb; jne r1,1` | c0/c1 |
| zext of a bool select | `zext` | same (nothing to block) | d0/d1 |
| GVN load-load forwarding across a call | second load merged into the first | `ptp` on the pointer: reloaded after the call | e0/e1 |
| GVN PRE / hoisting of a load available on one arm | load hoisted above the branch | one load per arm | g0/g1 |
| jump threading of a bool phi (MIR JumpThreading and LLVM JT) | threaded (MIR: `switchInt` duplicated into the arms) | bool materialised, `and64 r3,1; jeq r3,0` | h0/h1 (MIR dump: the Call keeps one switchInt) |
| CSE of two passthroughs | same `seq`: one call left | distinct `seq`: two calls | i0/i1 |
| sinking | unchanged | unchanged | j0/j1 |
| compare predicate canonicalisation (`x>=5` to `ugt 4`) | canonicalised | still canonicalised (`pt64(x)>=5` and `pt1(x>=5)` give the same `jlt r1,5`) | k0/k1/k2 |
| `(b as u64)==1` | folded to `br b` in opt | kept as `icmp eq %pt,1` in opt, but ISel re-folds it after the pt is gone: same code | l0/l1 |

Practical rules found while realising IR cells in source:
- The value that reaches the pt matters, not just the site. `pt1(do_coin)` (an i1) keeps the bool phi i1 and is
  byte-identical to main; `pt8(do_coin as u8)` puts `trunc`+`zext` in front of the pt and leaves an `and 1` on the
  promoted phi; `transmute` adds `assume(x<=1)` on both sides. Only a raw byte read
  `pt8(6,*(&do_coin as *const bool as *const u8))` gives the IR cell (pt8 on the loaded byte) exactly.
- A pt inside an `expect_p(..)` operand (sC) or on a compare that is first stored to a bool alloca (sD) does not reach
  the cell that sits on the alloca round trip: byte-identical.
- `ptp(n,&**a as *const AdminCto as *const u8)` (a passthrough of the accounts pointer value, not of `&ctx.accounts`)
  does not trip w17a06's readonly trap; the source capture equals the IR cell exactly.

## 3. IR beam (`tools/ptgen.py` + w17a06 `screen.py`, slim pre-opt oracle)

983 single edits on main's pre-opt bodies of validate/execute/wallet/sweep: a passthrough after every i1/i8/i64/ptr
value definition (load, icmp, trunc, zext, select, phi, xor), all uses rerouted through it (`pt`), plus `pb` (only the
`br` use of a multi-use i1). 703 are byte-identical, 64 change code at 27,400 B, 216 change the size.

| cell | IR value | source site | dM | dB |
| --- | --- | --- | ---: | ---: |
| pt:wallet:31205 | `load i8 %do_coin` at the AMM collect test | line 578 `if coin_present&do_coin` | +5 | 0 |
| pt:sweep:32129 | `trunc` of the TCF program-clone `executable` byte | line 659 first AccountInfo literal | +5 | 0 |
| pt:sweep:32132 | same literal, `is_writable` | line 659 | +1 | 0 |
| pt:execute:29037 | accounts pointer that the shared-arm curve reload derefs | line 339 | +2 | -8 |
| pt:execute:28751 / 28759 | accounts pointer of CtoState `mayhem` / `holder_reward` | line 339 | +1 | -8 |
| pt:validate:27786 | holder-arm `new.is_some()` tag | line 298 | 0 | +8 |
| pt:validate:27872/27874, pt:execute:28620/28744 | 312 memcmp bool round trip; accounts ptr of `shared` owner test / `max_fee` | | 0 | +8 |

Combinations (oracle): 31205+32129 = 2,280 (+10); + 29037 + 27786 = **2,282 (+12)**; greedy forward selection over
every cell with dM >= -3 adds nothing to either.

## 4. Result (landed form)

Four marked shims, no line added (lines 8, 298, 339, 578, 659):

```rust
// 298 holder arm
if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test ..*/{return Err(..298..)}
// 339 shared non-holder arm
target=unsafe{read_volatile(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as ..)}/*shim: ..*/.creator;
// 578 wallet
if coin_present&((unsafe{pt8(6,*(&do_coin as *const bool as *const u8))}&1)!=0)/*shim: passthrough on the do_coin byte ..*/{
// 659 sweep TCF program clone
executable:unsafe{pt1(7,x.executable)}/*shim: passthrough on the TCF program-clone executable byte*/,
```

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main bf01b5fd9 | 0.68005 | 2,270 | 3,170 | 27,400 | 1034 / 1034 | - |
| q4 on bf01b5fd9 (oracle sig 4d1e60e0d26d = IR quad) | **0.68364** | 2,282 | 3,313 | 27,400 | 1034 / 1034 | 0 / 0 |

Differential (q4 on bf01b5fd9): 388 cases, 0 mismatches. Calls 154 / 3.

Merged with main d5751b26e (#4011, 0.68065): **0.68424** (M 2,284), 3,313 slots, 27,400 B, 1034 / 1034, zero losses
(unstripped a950162cc7d5201c). The gains add: +2 from #4011, +12 from this change.

## 4b. Landing history and the moving base

- #4018 (this lane): land.py merged main 445fe1405, where #4017 had changed the wallet guard to
  `collection_native==false||coin_present`. There the do_coin cell is worth 0 (it changes code, same M) and the TCF
  executable cell is still +5: landed 0.68095 -> **0.68244**, merge 8330455eb, zero losses, differential 388/0.
- #4019 (w17a18) reverted the guard on top of #4018: main ac37d7415 = **0.68424** (M 2,284), the full q4 + #4011 value.
- The cells are base-specific. On 8330455 the beam found `coin_present` (+3 @-32 B) and a +6 five-cell set; on ac37d74
  neither carries over (xC = 2,276 there). Re-run the beam on every new main before building on a cell.

## 4c. Round 3 on main ac37d7415 (M 2,284): +3

Beam (1,004 singles) on the new main: nothing above main at 27,400 B alone; `pt:wallet:31374` (a pt1 on the landed
do_coin test compare) is +4 at -24 B. Size-neutral subsets (`tools/combo.py`, 250 screened) give +3 at 27,400 B with
three +8 B repay cells, each of which reproduces its IR signature in source:

| cell | source (line) | single dM / dB |
| --- | --- | --- |
| pt:wallet:31374 | `coin_present&unsafe{pt1(27,(pt8(6,*(&do_coin as *const bool as *const u8))&1)!=0)}` (578) | +4 / -24 |
| pt:execute:28731 | `ptp(23,&**a ..)` for the `shared` owner test (339) | 0 / +8 |
| pt:execute:28855 | `ptp(24,&**a ..)` for CtoState `max_fee` (339) | 0 / +8 |
| pt:validate:27964 | `expect_p((pt8(4,(t==*sharing) as u8)&1)!=0,true,0.625)` (312) | -1 / +8 |
| (alt) pt:execute:28808 | `((pt8(5,(q==native_mint::ID) as u8)&1)!=0)` in quote_locked (339) | -1 / +8 |

| build (measure.sh) | admin_cto ratio | M | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main ac37d7415 | 0.68424 | 2,284 | 3,313 | 27,400 | 1034 / 1034 | - |
| yA (alt 28808 form) | 0.68514 | 2,287 | 3,096 | 27,400 | 1034 / 1034 | 0 / 0 |
| **yB (27964 form, proposed)** | **0.68514** | 2,287 | **3,092** | 27,400 | 1034 / 1034 | 0 / 0 |

Not realised: the collect_coin_creator_fee `?` Result-tag cells (pt on the tag word of the `?`, +4..+6 in IR combos on
two bases). `let r=..; if pt64(tag)!=2 {return r}` and `pt1(r.is_err())` both collapse (1,917 @27,440: a let-bound
Result instead of `?`), and a `map_err` closure that passes the Err tag word through `pt64` is folded away. A pt on an
operand inside validate's tests collapses (v284..v338: 1,425-2,278; MIR/LLVM threading is what main relies on).

## 5. Leads (a)-(d) from the angle

- (a) w17a06's MIR-threaded cells: the C1 family (w17a11, the 296 check inside the holder arm) with `pt1` on the split
  holder so LLVM JT cannot thread the hr path: c1p_49 1,827 / c1p_48 1,822 / c1pi_49 1,827 @27,056. Blocking JT keeps
  the hr path through the split (an extra test, a different CFG from main), which is not the C1-pred oracle shape.
  The pargs / wallet-fence cells of w17a06 were not re-priced as volatile cells; the beam above covers the passthrough
  family on the same IR positions (the do_coin cell is the fence block's successor test).
- (b) fee-tag phi: the probe (a0/a1) shows a pt on a constant tag phi keeps ONE phi with a store user and a compare
  user, which is what w16a24 needed. It still needs the fo/fb restructuring (-200 M on main), so it was not built.
- (c) PDA-first: not attempted (k8 is 325 M below main before any shim).

## Tools (`tools/`, experiment only)

- `ptgen.py <slim.ll> <edits.jsonl>`: the passthrough edit family (`pt`, `pb`) in w17a06's edit format.
- `screen.py`: w17a06's screen with module-level declarations de-duplicated (combos of pt edits).
- `greedy.py`: greedy forward selection at 27,400 B over the screened singles.
- `cap.sh`, `mk.py`, `variants.py`: source variants (line-asserted replacements) captured into the slim oracle.
- `ptprobe.rs`: the fold-table probe.
- The oracle itself (`capraw.py`, `preslim.py`, `fx.py`, `oracle.py`, `modparse.py`, `gen.py`) is on
  `origin/swarm/w17a06-shim-irbeam` under `reconstruction/pump-main/lanes/w17a06-shim-irbeam/tools/`.

## Maintained source qualification — 2026-11-01

The current program change is independently rebuilt with the maintained identity
recipe and official full-window scorer. The four passthrough sites retain their
measured source behavior on the pinned compiler; an independent small target
probe checks bool, byte and pointer identity against ordinary controls.

The private capture, beam, screening and signature claims above remain author
research history. They are not standalone reproducibility or linked-image proof.
The eight private-cache tool changes added or modified by PR #4026 are excluded
from the maintained integration: existing tools retain their prior main versions,
and the new private queue/composition scripts are not shipped. No private oracle
or patched compiler is used for current acceptance.

Against a freshly built main `8350fae5a`, PR #4026 measures 68.514% token
similarity at 27,400 bytes with 3,092 positional differences. Adding PR #4023's
private CtoState declaration order raises token similarity to 68.544% at the
same size and positional count. Both full-window comparisons preserve all
1,034 raw and normalized matches with zero losses. No new exact window, whole
Pump ELF identity, historical source attribution or exhaustive semantics is claimed.
