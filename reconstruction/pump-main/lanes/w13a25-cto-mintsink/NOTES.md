# Lane w13a25-cto-mintsink: the sharing-CPI mint-clone sink, re-checked

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w13a12-cto-regalloc finding 3 (closed #2911). On mains 085e5df..9eb6c00, sinking one plain-field load of the
mint `AccountInfo` clone in `admin_cto_sharing_config`'s accounts into the block that stores the struct gave +0.012 at
27,400 B. The task was to find a source form for it.
Bases: main 224ff93a (0.55123, 3,222 slots), then bf9a05d0 (#2998, 0.55872, 3,323 slots).

**Result: the lever is gone on current mains, so the angle is exhausted. No source change is proposed.**

## Oracle re-check (llc oracle; tokens equal the build on both bases)

`scripts/sinkrun.sh <mod.ll> <out> label=value[,value]...` runs w13a12's `edit_sink1.py` through `ctoracle.py` and
prints ratio, abstracted ratio, bytes and the `clonefeat` spill/reg count (original 6/2).

| main | edit (sink one load into the struct-store block) | ratio | abs | bytes | clonefeat |
| --- | --- | ---: | ---: | ---: | --- |
| 224ff93 | none | 0.55123 | 0.69353 | 27,400 | 2/6 |
| 224ff93 | mint owner / rent_epoch / is_signer / executable | 0.54842 | 0.68852 | 27,440 | 4/4 |
| 224ff93 | mint is_writable | 0.54878 | 0.68935 | 27,376 | 2/6 |
| 224ff93 | event_authority key (`_2.i226`) | **0.55542** | 0.69353 | 27,400 | 2/6 |
| 224ff93 | sharing_config owner | 0.55974 | 0.69855 | 27,360 | 2/6 |
| 224ff93 | sharing_config key | 0.55978 | 0.69404 | 27,384 | 2/6 |
| bf9a05d | none | 0.55872 | 0.68604 | 27,400 | 3/5 |
| bf9a05d | mint owner / rent_epoch | 0.55640 | 0.67835 | 27,392 | 3/5 |
| bf9a05d | sharing_config owner/rent/flags | 0.56419 | 0.68776 | 27,336 | 3/5 |
| bf9a05d | sharing_config key | 0.56115 | 0.68885 | 27,368 | 3/5 |
| bf9a05d | event_authority key | 0.56025 | 0.68285 | 27,368 | 2/6 |
| bf9a05d | authority owner | 0.54853 | 0.67376 | 27,400 | 4/4 |

- The +0.012 mint sink of w13a12 is now **+40 B and worse** (224ff93) or -8 B and worse (bf9a05d). It stopped
  working after #2974/#2989/#2991 reshaped the frame and the validate region.
- `movescan.py` (861 cross-block sink/hoist edits of pure values):
  - 224ff93: the only gain at 27,400 B is the event_authority key sink, +0.0042, abs unchanged.
  - **bf9a05d: 222 edits change code and none is above main at 27,400 B.** Every clone-run gain now also shrinks the
    function (-32 to -64 B).
- Pairwise sink combos are not additive. Register allocation in the clone run is chaotic: one sink moves 2-6 spill/reg
  uses and also the spill slots of later regions.

## Source forms (capture builds, `scripts/trial.sh` + `scripts/var.py` genes)

| gene | form | main | ratio | abs | bytes | cf |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `m_let` | `let mint_ai=a.mint.to_account_info();` in the `Some` arm before the CPI, `mint:mint_ai` | 224ff93 | 0.54921 | 0.69693 | 27,392 | 1/7 |
| `m_let` | same | bf9a05d | 0.55259 | 0.67785 | 27,384 | 2/6 |
| `m_let2` | `let program=..;let mint_ai=..;` then the CPI with both | 224ff93 | 0.54145 | 0.68565 | 27,360 | 2/6 |
| `m_helper` | accounts literal in an `#[inline(always)]` helper taking `mint:AccountInfo` by value | 224ff93 | 0.54052 | 0.69004 | 27,392 | 2/6 |
| `ea_let` | `let ea=a.pump_fees_event_authority.to_account_info();` before the CPI | 224ff93 | 0.54164 | 0.69203 | 27,400 | 2/6 |
| `sc_let` | `let sc=a.sharing_config.to_account_info();` before the CPI | 224ff93 | 0.54780 | 0.69314 | 27,384 | 2/6 |
| `hr_first` | curve store `is_holder_reward` before `is_cashback_coin` | 224ff93 | 0.55063 | 0.69323 | 27,400 | 2/6 |
| `scx_own` | `let mut cpi=..; cpi.accounts.sharing_config.owner=a.sharing_config.owner;` | bf9a05d | 0.54676 | 0.65061 | 27,456 | **6/3** |
| `eax_key` | `let mut cpi=..; cpi.accounts.event_authority.key=a.pump_fees_event_authority.key;` | bf9a05d | 0.54769 | 0.65010 | 27,424 | 3/6 |

`let mut cpi` + one late field re-read is the only source form that truly produces the late load: the second load has
no clone noalias scope, so it is re-done after the Rc increments, and the first store is dead.
`scx_own` reaches the original's 6 spilled accounts-pointer reloads. The cost is a second 424 B `CpiContext` alloca
(`_143`/`_127`), which shifts the frame. Its abstracted ratio drops by 0.035, mostly in orig 0x4800 (-27 tokens).
w13a21 got the same result for the mint fields (`mx_*`). Already dead before this lane, so not repeated:
`AsRef`/`(*a.mint).clone()`/`ctx.accounts.X` (byte-identical), mint last or after sharing_config in the literal, and a
let-bound program/accounts/cpi.

## Why the clone run differs (for the spill-slot / flags lanes)

- After the sharing CPI, the original reloads 8 spill slots plus `swept` in r9: 0x8f8, 0x950 (holder byte, stored
  unmasked), 0x958 (cashback, `&1`), 0x8d8 (accounts), 0x8e8 (fee tag), 0x930 (fee), 0x8e0, 0x938.
  Ours reloads 10: 0x900 and 0x910 (the two cashback operands, ANDed after the call), 0x8f0 (accounts), 0x8e8
  (holder), 0x918 (fee tag), 0x930, 0x908, 0x8e0, 0x970, 0x938.
- The original's holder and cashback slots are written on 5 and 6 paths (0x237c8..0x242c8): they are **phis** carried
  through validate. Ours computes `cashback = and i1 %_39.not, %43` in the entry block. MachineSink then moves the `and`
  next to the curve store, so both operands live across the clone run. Hoisting the curve-store zexts in IR does not
  help (0.5585 / 0.52647). This is the flags-as-phis residual that w13a05, w13a08 and w13a18 are working on, not a
  clone-run spelling.
- `slotmap-bf9a05d.txt` (`scripts/slotmap.py <fn.bin|so> <cand.dis> <orig.dis>`) maps each original spill slot
  (>= r10-0x8d0) to the candidate slots used at the aligned instructions, with registers and frame masked:
  - 0xa10-0xa48, 0xb40-0xc38 and 0xfd8-0x1000 are already at the original offsets;
  - 0xa50-0xb30 are all +8 (one extra slot above them in ours);
  - 0x9e8-0xa08 are +0x20;
  - the low slots 0x8d8-0x9a0 are scrambled. These hold the long-lived values: accounts 0x8d8 -> ours 0x8f0, holder
    0x950 -> 0x908, cashback 0x958 -> 0x8e0.

  A fix that removes the one extra spill above 0xa50 would align about 40 slots in the clone and CPI tail at once.

## Ledger keys

`0x22a10-w13-224ff93-mintsink-{oracle-reverify,movescan,m_let,m_let2,m_helper,ea_let,sc_let,hr_first}-v1`,
`0x22a10-w13-bf9a05d-mintsink-{ir-clone-sinks,movescan,m_let,scx_own,eax_key,flag-zext-hoist}-v1`.
