# w13a32-cto-hkfirst2: holder-rewards PDA as the first call of admin_cto::execute

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a13-cto-region1of3 (#2927/#2967, ledger `region1-*hkfirst*`, `v6_hkfirst`).
Ledger keys: `0x22a10-w13-*-hkfirst2-*`.

## The edit (`hk1`)

Move `let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;`
in front of `let shared=if a.bonding_curve.creator==a.sharing_config.key(){..}`, as in the original (the PDA is the
original's first call, orig +0x80..+0x148, before the sharing-config memcmps). Same line, no line-number change.

- `hk` must stay alive (`let hk=..;holder_key=hk.0`). `let holder_key=FPA.0` and `let (holder_key,_)=FPA` both give
  0.52346 at -40 B on d81d0f5 (hk1: 0.57503 at -40 B).
- With `hk1` the first 0x148 bytes match the original instruction for instruction except the frame of the PDA result
  (ours copies `hk` from `-0x679`, the original from a `-0x2d0` temp) and the head registers (orig r6 = stack args,
  r8 = accounts; ours r9 / r6).

## Measurements (raw-IR capture + rx oracle = identity build tokens; measure.sh where sizes are 27,400)

| main | main ratio | hk1 bytes | hk1 ratio | note |
| --- | ---: | ---: | ---: | --- |
| 9eb6c00 / 74b3171 (w13a13) | 0.49131 / 0.51348 | +32 | lower | old result |
| d81d0f5 | 0.57100 | 27,360 (-40) | 0.57503 | |
| 06e6bb8 | 0.57669 | 27,384 (-16) | 0.57687 | |
| dfc3693 | 0.59916 | 27,392 (-8) | 0.59745 | frame-masked 0.69023 -> 0.69273, frame+reg masked 0.83942 -> 0.85004 |

So hk-first improves the code skeleton every time, but the plain ratio follows the frame.

### Mechanism: hk-first gives the original's exact spill-slot set

On dfc3693 the set of `[r10-X]` offsets >= 0x8d0 is the original's exactly with `hk1` (0x8d0..0xc38, 109 spill slots);
main lacks 0xc38 (108 slots: the "109th spill slot" residual of #3011 / w13a29). The cost is the order: the slots are
coloured by spill weight, and with `hk1` the 0xb70..0xc30 run shifts by +8 against main and region-1 values change
registers (ours spills `&new` at [r10-0x8d8] and keeps the sharing_config pointer in r8; the original keeps `&new`
in r7 until the entry copy of `new` at orig 0x4d8 and spills the sharing_config pointer to [r10-0x8e0]).

### Conflict with the payer-first clone run (w13a29 / w13a21)

On 06e6bb8: payer-first alone 0.58889 at 27,408; `hk1`+payer-first 0.55546 at 27,368. Frame and register masked the
two differ only by the moved PDA block (skeleton 0.98156 vs payer-first), so the loss is register allocation and
spill colouring in the sweep clone run (0x3180..0x3478), not structure.

### Size repair on 06e6bb8 (measure.sh, all 1034/1034, 0 losses)

| form | bytes | ratio |
| --- | ---: | ---: |
| main | 27,400 | 0.57669 |
| hk1 + `w_clock_local` | 27,400 | 0.57639 |
| hk1 + `w_clock_local` + `z_sh_flat` + `fee_unwrap` | 27,400 | 0.57639 |
| hk1 + `w_clock_local` + `z_sh_flat` | 27,392 | 0.57708 |
| hk1 + `w_clock_local` + `z_sh_flat` + `old_fee_first` | 27,392 | 0.57678 |
| hk1 + `fee_unwrap` + `z_sh_if_owner_first` | 27,424 | 0.57374 |

### IR oracle (w13a23 `rx.py` / `iredit.py`, run as `hkie.py`)

A scan of `nolt`, branch weights (1:2000, 2000:1), inversions and alloca moves on the hk1 IR (06e6bb8: 4,052 items;
d81d0f5: 2,333 items) finds no frame-only repair: the best frame edit is +0.0003 (`mv target.i.sroa.9` late). Only
std `Rc::inc_strong` / `AccountInfo::clone` overflow-trap weights in the sweep clone run gain (+0.014 at 27,384), and
they are not source-expressible (w13a26 reached the same conclusion on main).

Caution for oracle users: other lanes run `pkill -f capvar.sh` / `pkill -f "iredit.py scan"`; give your copies
lane-unique names.
