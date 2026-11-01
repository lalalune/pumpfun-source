# w17a22-shim-varpin: `llvm.var.annotation` as a zero-instruction memory pin (fold table, priced beam, size knobs)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Ledger approach `varpin`, keys `0x22a10-w17-<main7>-varpin-*`.

Bases: main a51791e2e (0.68544, M 2,288) for calibration, then main 2f3597f99 (0.68634, M 2,291; #4040 sk lifetime
start) for every beam. Oracle: w17a06's exact slim pre-opt oracle (`capraw.py` + `preslim.py` + `fx.py`, survivor list
`surv-1647da0.txt`), re-captured on each main (`m1` reproduces 0.68634 / M 2,291 / 27,400 B, sig `1ce34f20c053`).

## The construct

```rust
// admin_cto.rs line 8, appended (no new line; `link_llvm_intrinsics` is already on lib.rs line 1):
extern "C"{#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);}/*shim: llvm.var.annotation = a zero-instruction memory pin on one local (no clobber)*/
// use (one per pinned local, the marker on the same line):
unsafe{vann(&x as *const _ as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: var.annotation keeps x in memory*/;
```

With null string/arg pointers there is no static, section or relocation. ISel drops the call (`SelectionDAGBuilder`:
`Intrinsic::var_annotation` is discarded), so it emits no instruction.

## 1. Calibration (main a51791e2e)

| variant | result |
| --- | --- |
| declaration only (line 8) | byte-identical: candidate.so sha256 `fe3b9cef0b51a446` = `baseline-main-a51791e2e` (measure.sh) |
| declaration + `vann(hkx)` after the PDA write (the 72 B holder_key slot of #3993) | byte-identical (same sha) |
| IR: vann on `hkx`, `sk`, `sk1`, `q`, `mint` (memory-resident and passed to memcmp/PDA by pointer) | byte-identical (sig `904118e632c2`) |
| IR: vann on `st` (CtoState) | **not** identical: M 1,972 @27,216 |

Why `st` differs: `st` survives SROA only because `memcmp(%st, ..)` reads its creator bytes. It is memory-resident but
*not captured* (memcmp's pointer args are `nocapture readonly`), so BasicAA proves the later calls cannot write it and
GVN keeps forwarding its field stores to the field loads across every call. `vann` captures it: every later call may
clobber `st`, so each field is reloaded after each call. "Already in memory" is not enough: the pin is free only when
no load of the object is forwarded across a call today (`hkx`, `sk`, `q`, `mint` are read only by memcmp/PDA calls
through their address, so nothing changes).

`vann` on the `new` *parameter* pointer (w17a14's bba/bbb with vann in place of `black_box(&new)`), at execute entry,
after the `(new,)` args copy or before the validate call: byte-identical to main 53ec7fb (sig `61dcfe87f489`).
`black_box(&new)` kept the E3 copy only through its asm memory clobber; a pin of `new` itself does nothing. Only a pin
of a *copy* of `new` keeps E3 stores (section 4).

## 2. Fold table (identity toolchain probe `probe/vprobe.rs`, `rustc --target sbpf-solana-solana -C opt-level=3`)

| pass | effect of `vann(&x)` on the alloca `x` | probe |
| --- | --- | --- |
| SROA | skips `x` entirely (the call is an escaping use): no split into pieces, no promotion to SSA | g1, e3v |
| GVN / EarlyCSE store-to-load forwarding | blocked across any call that may write memory (`x` is captured): the load after the call is a real reload. Still forwarded inside a block with no intervening clobber, and across `vann` itself (`inaccessiblememonly`) | g1 `ldxdw r1,[r10-16]` after `call g` |
| DSE | still removes a store overwritten before any read (d0: the first `t[0]` store is gone); keeps stores a later call might read (d1); removes ALL stores when no call follows the pin, because the escape point is the `vann` call (EarliestEscapeInfo; d2) | d0, d1, d2 |
| MemCpyOpt | `memcpy(dst <- x)` is still forwarded to `memcpy(dst <- original source)` when that source is unchanged (noalias param, m0; e3v: the shared arm reads `new+1`/`new+24`, never e7/e9). The pin keeps the copy *into* `x`, it does not make readers use `x` | m0, e3v |
| StackColoring | lifetime markers still apply: pinned allocas with disjoint scopes share one slot (s0); overlapping ones get separate slots (s1) | s0, s1 |
| ISel | call dropped, no instruction, no relocation | all |

Consequence: a pin reproduces the original's *stores* of an object (e.g. the 7 B overlapping `ldxw [new+4]/[new+1]`
copy and the 9 B `ldxdw [new+0x18]` + `ldxb [new+0x20]` copy at E3), but readers of a forwarded copy still read the
source. To make J1 read the pinned pieces back (orig 0x1858-0x1890), the source itself must be clobberable between the
copy and the reader (or the reader volatile).

## 3. IR beam on main 2f3597f99 (M 2,291): one pin per alloca

`tools/vgen.py <slim.ll> <edits.jsonl> [A|B|C]` emits `call void @llvm.var.annotation.p0.p0(ptr %x, ptr null, ptr null,
i32 0, ptr null)` for every alloca of validate/execute/wallet/sweep: A = after its first write, B = before the first
non-intrinsic call after that write, C = after its lifetime.start. Scored with w17a15's de-duplicating `screen.py`.

- 674 cells (all 491 A + 183 B/C): 130 byte-identical, **none above main**. A/B/C give the same signature in almost
  every cell (on a51791e2e: 1,461 cells, same picture).
- Every pin of a live execute value collapses (target -247, sharing_update -253, `_79` payload -254, args `_59` -647,
  holder -434, quote_locked -869). The rfj-masked region match (`rc.py --mask rfj`, structure only) is flat or worse:
  target pin -5 (V1 +1, J2 -2, T1 -3), sharing_update -21, validate `t` -11 (E3 +4, V4 +3, T1 -8). The pins do not buy
  structure; the exact loss is the frame-host shift and RA (w17a14/w17a10 mechanisms).

### Zero-cost size knobs (M unchanged at main 2f3597f99)

| cell | object | dB |
| --- | --- | ---: |
| `vaA:execute:%_80` | shared non-holder arm: the curve-creator temp copied into `target` (line 339) | +64 |
| `vaA:validate:%_95` / `%_64` | 312 / 306 `error!`: `compared_values: None` (72 B) | +48 |
| `vaA:validate:%_92` / `%_61` | 312 / 306 `error!`: `Some(ErrorOrigin::Source(..))` (32 B) | +40 |
| `vaA:validate:%_94` / `%_63` | 312 / 306 `error!`: `Source{filename,line}` (24 B) | +16 |
| `vaA:validate:%_93` / `%_62` | 312 / 306 `error!`: `ErrorOrigin` (32 B) | +16 |

-1 M: sweep `residual` (0 B), validate `cashback` (+32), 296/289/298 error temps (+40/+48).
The validate knobs need a hand-expanded `error!` at that line (`Error::from(AnchorError{..,error_origin:
Some(ErrorOrigin::Source({let s=Source{filename:file!(),line:line!()};vann(&s..);s})),..})`), on the same line.

The knobs are base-specific: on main 53ec7fb (#4053 moved a holder_key placeholder to the validate top) the same
validate error temps cost 1 M each (`%_65`/`%_66`/`%_99`/`%_100` -1 @+16, `%_64`/`%_98` -1 @+40, `%_67`/`%_101` -1 @+48).

## 3b. Repaying w17a16's outline base Wx with pins (source-built)

w17a16's Wx (`n5_Wx`: 307/312 to_string outlined + the original validate order + its repay genes; 2,295 @27,320, 86
lddw, copied from its lane) needs +80 B. vann beam on Wx: `vaA:wallet:%_53` / `%_47` (the create_idempotent
`token_program` / `payer` `to_account_info()` clones, 48 B) are **+3 M at +48 B**; the validate error temps cost 1-3 M.

| build (main 2f3597f) | M | bytes | ratio | note |
| --- | ---: | ---: | ---: | --- |
| Wx | 2,295 | 27,320 | (0.68836 short) | |
| `wxh`: Wx + hand-expanded `error!` at 306 and 326, no pins | 2,295 | 27,320 | | byte-identical to Wx: the hand expansion is free |
| **`wxp3`**: + pins on the token_program clone (561), the 306 and 326 `Source` temps | 2,295 | 27,400 | **0.68733** | measure.sh: 1034/1034, zero losses; = IR sig `509a2f925677` |
| Wx + validate-only pins (300 combos summing to +80 B) | <= 2,291 | 27,400 | <= 0.68613 | |

`wxp3` was not proposed: the pinned 48 B clone reaches the CPI array through a `memcpy` **libcall** (`mov64 r3,48; call`),
so internal calls go 154 -> 155 (away from the original), and main moved past it (aab087f 0.68724, 53ec7fb 0.68754).
On 53ec7fb, Wx + #4054's lte at 312 is unchanged (the lte is inert once 312's to_string is outlined), and Wx + #4053's
placeholder move falls to 2,282 @27,320: an outline base should keep the placeholder before the fee_configurable test.

Source spellings that reproduce the IR cells exactly:

```rust
// validate 306 (and 326 the same way): error! hand-expanded, the Source temp pinned
return Err(anchor_lang::error::Error::from(anchor_lang::error::AnchorError{error_name:PumpError::CtoNewCreatorRequired.name(),error_code_number:PumpError::CtoNewCreatorRequired.into(),error_msg:PumpError::CtoNewCreatorRequired.to_string(),error_origin:Some(anchor_lang::error::ErrorOrigin::Source({let s=anchor_lang::error::Source{filename:file!(),line:line!()};unsafe{vann(&s as *const anchor_lang::error::Source as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: var.annotation keeps the 306 error Source in memory*/;s})),compared_values:None}));
// wallet 561: one create_idempotent account clone pinned
token_program:{let x=a.quote_token_program.to_account_info();unsafe{vann(&x as *const AccountInfo as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: ..*/;x}
```

## 4. Targeted cells

| cell | what | M @ bytes (main 2,291 @27,400) |
| --- | --- | --- |
| `e3v` | w17a10 e79 layout with vann pins instead of volatile copies: e7/e9 filled from new+1/new+24 at the CtoState site, shared arm built from tag/e7/new+8/new+16/e9 | 1,393 @27,584 |
| `e3v97`, `e3vpb`, `e3v_lt` | 9-before-7, pins before the copies, explicit lifetimes | 1,393 @27,584 |
| `e3v_dead` | entry pinned copies only (no arm change) | 1,457 @27,536 |
| `w59` | pin the whole args tuple `(new,)` | 1,644 @27,272 |

`e3v` reproduces the original's E3 store shapes exactly (`ldxw [new+4]; stxw; ldxw [new+1]; stxw` = the overlapping 7 B
copy, `ldxdw [new+0x18]` + `ldxb [new+0x20]` = the 9 B copy; E3 +7 rfj) but, as in w17a10, the extra live state at the
CtoState site flips the sweep-join placement (S1 -49, T1 -225, P1 -89, EV -141 rfj).

## Tools (`tools/`, experiment only; lane-local paths, set `LANE_OUT`)

- `vgen.py <slim.ll> <edits.jsonl> [ABC]`: the vann pin family (one pin per alloca, placements A/B/C) in w17a06's edit
  format; run with w17a15's `screen.py` (de-duplicates the `declare`).
- `ired.py <slim.ll> <set.py> [names] [--keep]`: named edit sets (`V = {name: [(old,new) | callable]}`), adds the
  `llvm.var.annotation` declaration when used, scores with w17a06's `fx.run`.
- `e3v.py`: the E3 piece cells (section 4). `onbase.py`: singles screened on top of a base cell. `combo2.py`: size-neutral
  subsets (sum of single dB = 0) over several edit families with a predicted-dM floor.
- `probe/vprobe.rs`: the fold-table probe (about 1 s with the identity rustc; see the w17-plan24 `zfprobe.sh` driver).
