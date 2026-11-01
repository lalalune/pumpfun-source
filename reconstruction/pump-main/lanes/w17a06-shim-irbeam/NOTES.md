# w17a06-shim-irbeam: shim alphabet calibration and an IR beam over shim-expressible edits

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 1647da0f2 / 11789175c (programs/ identical to 599891304): 0.67436, 3,141 slots, M 2,251 at 27,400 B.
Wave 17 SHIM track. Ledger: approach `irbeam`, keys `0x22a10-w17-1647da0-irbeam-<item>-v1`.

## 1. An exact pre-opt oracle in about 2 s (`tools/preslim.py` + `tools/fx.py`)

The raw-IR oracle (capraw pre-opt IR, `opt -O3`, slim, `llc`) runs `opt` on the whole 35 MB crate module. Under
this wave's machine load (load average 120-160) that takes 110 s wall per evaluation. `preslim.py` cuts the pre-opt
module down to what `execute` can see, and `fx.py` scores it. The result is **token-identical** to the full-module
oracle on main: 3,337 tokens equal, M 2,251 at 27,400 B, about 2 s wall.

How the reduction stays exact:
- keep every function and global in the reference closure of `execute` and `validate` (353 of 5,772 defines, about
  5% of the module). Every other define becomes a declaration, and unreachable metadata is pruned;
- add one `optnone noinline` caller, `@__keep_uses`, that calls each closure function which has callers outside the
  closure **and survives the full-module `opt -O3`** (`data/surv-1647da0.txt`: the full run's surviving defines, plus
  `slice_contains`). Without it a helper used by many handlers becomes single-use in the slim module. It then gets
  the LastCallToStatic inline bonus, or IPSCCP specialises it. For example, `slice_contains` with its one caller
  passing length 1 unrolls and reorders the `quote_locked` phi, which costs 8 B;
- the dummy call passes a constant wherever **every** call site in the full module passes that same constant,
  and an opaque `load volatile` from `@__opaque` everywhere else. Otherwise the dummy blocks IPSCCP/DAE argument
  removal that the full module does (`collect_transfer_native`'s constant last argument, +8 B).

Usage: `SURV=data/surv-1647da0.txt python3 tools/preslim.py raw.ll slim.ll keep` once per capture, then
`python3 tools/fx.py slim.ll <name>`. The `--mp` option adds Mperm and Mhc. Edits to admin_cto's own pre-opt bodies
(validate, execute, wallet, sweep) can be applied to `slim.ll` directly: `tools/gen.py` and `tools/screen.py` do that.
Re-derive the survivor list with one full `rx.py --keep` run when main's callees change.

Checks on source captures (full oracle or real build against slim):
| variant | full / build | slim |
| --- | --- | --- |
| main m0 | 2,251 @27,400 (full) | 2,251 @27,400, tokens identical |
| rv_par (`read_volatile(holder_key)` 32 B in validate 312) | 1,741 @28,168 (full) | 1,741 @28,168 |
| rv_own (w17a03 v4320 owner pin) | 0.67466 = 2,252 @27,400 (measure.sh, w17a03) | 2,252 @27,400 |

Caveat: like the full oracle, the slim oracle differs from the linked baseline build in 10 tokens. These are
use-list-order effects of the textual IR round trip. M is unchanged. Confirm final candidates with `measure.sh`.

## 2. Result: two marked volatile reloads, +3 M at 27,400 B (main 9336aaf 0.67675 -> 0.67765)

| build | admin_cto ratio | slots | bytes | normalized / raw | losses | sha16 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| main 9336aafff | 0.67675 | 3,141 | 27,400 | 1034 / 1034 | - | |
| this lane (kA4B1) | **0.67765** | 3,218 | 27,400 | 1034 / 1034 | 0 / 0 | 8fa04fba058407ab |

The runtime differential passes: 388 cases, 0 mismatches. Calls stay at 154 / 3.

Two marked shims on existing lines (no line added):
- line 761, the pool owner test: `unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}.pool.owner==&AMM`
  is a volatile reload of `ctx.accounts` (IR beam cell `vl:execute:29769`, +2 M at +16 B on its own);
- line 339, the shared non-holder arm: `target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}.creator`
  is a volatile reload of the curve's Box pointer (cell `vl:execute:28873`, -1 M at -16 B on its own).

Together the two cells give M 2,261 at 27,400 B on main d4dfb04, 2,258 + 3. The source capture has the same output
signature as the IR pair (`f49be521fde5`). On 9336aaf, `measure.sh` gives the same +3.

**Spelling trap (also in SHIMCAL):** any reference-to-raw-pointer cast of `a` (`a as *const ..`, `&ctx.accounts as ..`,
or `read_volatile(a)` by coercion) is turned into `&raw const ctx.accounts` by MIR RefProp/GVN. `DeduceReadOnly` then
drops `readonly` from execute's by-value `ctx` param. LLVM must reload the accounts pointer after every call, and
admin_cto collapses to M 1,569 @27,464. `core::mem::transmute` of the reference value keeps `readonly`.

## 3. The beam (single edits, pairs, triples)

Edit families (`tools/gen.py`, on the slim pre-opt module):
- `vl`: volatile on a load;
- `vs`: volatile on a store;
- `rr`: a volatile re-read of a field at a later use;
- `bf`: a `black_box(())` memory fence at a block head;
- `bw`: 2000:1 / 1:2000 `br` weights;
- `sw`: switch weights;
- `na`: noalias / attribute drops on nested-fn params.

| base | single edits | pairs | triples | best at 27,400 |
| --- | ---: | ---: | ---: | --- |
| main 1647da0 (M 2,251) | 1,374 | 251 | 174 | +4: `vl:29745` + `vl:28849` + `vl:31885` (w17a03's owner pin), or `+ bf:wallet:30894` instead of the pin; the quad gives +5 (M 2,256) |
| main d4dfb04 (M 2,258) | 793+ | 195+ | - | +3: `vl:29769` + `vl:28873` (landed here) |

Ranked lever table (main d4dfb04, M 2,258 @ 27,400; dM / dbytes):

| cell | IR edit | source line | dM | dbytes | source form | status |
| --- | --- | --- | ---: | ---: | --- | --- |
| vl:execute:29769 | volatile `ctx.accounts` load in the pool owner test | 761 | +2 | +16 | `read_volatile(transmute::<&&mut AdminCto,*const &AdminCto>(a))` | landed (with 28873) |
| bf:wallet:30918 | fence at the head of the no-coin `do_coin=false` block | 560 | +1 | 0 | no exact form: MIR jump threading duplicates the `else{false}` arm, and the source fence lands in both copies (nW: -61) | open |
| bwf:execute:28524 | 1:2000 on `q==Pubkey::default()` (quote_locked) | 339 | +1 | -8 | `expect(q==Pubkey::default(),false)` | not built |
| vl:execute:28606 | volatile cashback byte (CtoState) | 339 | 0 | -16 | `read_volatile(&a.bonding_curve.is_cashback_coin)` | repay knob |
| vl:execute:28616 | volatile holder_enabled byte (CtoState) | 339 | 0 | -16 | `read_volatile(&a.global.is_holder_reward_enabled)` | repay knob |
| vl:execute:28871 | volatile `ctx.accounts` load in the shared arm | 339 | 0 | -8 | transmute form as above | repay knob |
| vl:execute:28873 | volatile curve Box pointer load in the shared arm | 339 | -1 | -16 | `read_volatile(&a.bonding_curve as *const Box<..> as *const &Account<..>)` | landed (with 29769) |
| vs:execute:28489/28491 | volatile stores of the holder-rewards seed array | 339 | 0 | 0 | write_volatile of the seed slice | neutral |
