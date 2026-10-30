# w13a24-cto-ctostatesroa: CtoState back in the frame-top slot (-0x38), holder-rewards PDA result kept alive

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Scratch, IR captures and builds: `~/.cache/pumpfun-reconstruction/lanes/w13a24-cto-ctostatesroa/` (not in git).
Ledger keys: `0x22a10-w13-1043a51-ctostatesroa-*`, `0x22a10-w13-bf9a05d-ctostatesroa-*`.

## Result

| main | before | after | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| 1043a51 | 0.53206 / 3,324 | 0.55992 / 3,316 (h2) | 27,400 | 1034 / 1034 | none |
| bf9a05d | 0.55872 / 3,323 | **0.56291** / 3,315 (k1) | 27,400 | 1034 / 1034 | none |

Runtime differential: 363 cases, 0 mismatches (both builds). k1 unstripped sha16 `042992c528f0f1cd`.

Source change (same line, line count unchanged):

```rust
let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;
...
let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=CtoState{..}; let hopt=holder; ..
  let sk=a.sharing_config.key(); let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?; ..
```

## Mechanism

1. **CtoState inside the block (`y1`).** The original keeps CtoState at `[r10-0x38]` (orig 0x22e78..0x22ee0
   stores at -0x38..-0xb). That slot is the 48 B `_77.i` stack-coloring group. A function-scope `st` has its
   `lifetime.end` at the function exit, overlaps everything and gets its own slot at -0x688. Inside the block
   its StorageDead ends at the block, and StackColoring merges it into `_77.i` at -0x38. IR oracle
   (`e/stend.py`: move st's `lifetime.end` to the validation join) = source y1 exactly (0.51528 on 1043a51).
   Alone this loses: the 48 B leave the frame and holder_key/mint move 48 B up (holder_key 0x678 vs orig 0x6a0).
2. **The holder-rewards PDA result kept alive (`h2`).** Single-edit scan on y1: `nolt:_15` (the 33 B
   `find_program_address` sret temp, MIR `_15`) 0.55992, `nolt:_62` (the `Pubkey::default()` temp) 0.56141.
   Both put a long-lived 32/33 B slot between holder_key and the 7 B target piece, so holder_key lands at the
   original's 0x6a0, mint at 0x6c0 and the 33 sret-demotion slots at the original's 0x6d0..0x8d0.
   Source: bind the call result to a function-scope local (`let hk=find_program_address(..)`) and copy
   `holder_key=hk.0`; `holder_key` is declared first (deferred init) so `hk` gets the higher MIR index and sits
   above holder_key, like `_15`. `let hk=..;let holder_key=hk.0;` (h3) or `&find_program_address(..)` (h1/h4)
   give 0.55962-0.55992. A hoisted `let zero=Pubkey::default()` (z1/z2) lands below the 7 B target piece and
   loses (0.50457 / 0.51108).
3. **On bf9a05d (#2998 sk tuple), revert to a plain 32 B `sk` (`k1`).** #2998 made `sk` 33 B so it sorts ahead
   of validate's `t.i` and takes the `_77.i` slot. With `st` in `_77.i`, the 33 B `sk` goes to `_92.i` (0x4b8)
   and pushes the error-name Strings out of 0x4b8 (orig 0x4a8-0x4b8 accesses: 37 lost; y1+h2 on bf9a05d is
   0.53116). A 32 B `sk` (`sz:sk:32` oracle 0.56291 = source k1) lands in the `_111.i` group at 0x470, the
   original's sharing-key temp (orig 0x22f68..0x22fa0 stores at -0x458..-0x470), and the Strings return to 0x4b8.

## Frame after k1 vs the original (r10 offsets)

`val6` 0x651, target piece 0x658, `hk` 0x679, holder_key 0x6a0, mint 0x6c0, sret slots 0x6d0..0x8d0: all at the
original's offsets. Remaining frame difference: the original has **109** 8 B spill slots (0x8d8..0xc38), ours
**108** (0x8d8..0xc30), so part of the deep spill area is 8 B short (orig 0xa18-0xa50 and 0xb88-0xc38 map to
ours -8; 0xa58-0xb30 are exact). The faithful entry copy of `new` (validate reading `args.0`: u5/y3/y4) gives
110 spill slots.

## Other trials (raw-IR capture + `rx.py`; scores equal build tokens)

| trial (main) | form | bytes | ratio |
| --- | --- | ---: | ---: |
| u5 (1043a51) | `st; args=&(new,)` + validate reads `args.0` (w13a03 U5 on E32) | 27,368 | 0.47362 |
| y3 (1043a51) | st and args both in the block, validate reads `args.0` | 27,368 | 0.51079 |
| y4 (1043a51) | args before the block, st in the block, validate reads `args.0` | 27,464 | 0.52095 |
| y4 + `mv:target.sroa.0:top` (IR) | new's 7/9 B pieces at the original's 0x658/0x668 | 27,464 | 0.53291 |
| y1 (1043a51) | st in the block only | 27,400 | 0.51528 |
| y1+h2 on bf9a05d (sk tuple kept) | | 27,400 | 0.53116 |

y4 places new's SROA pieces exactly at the original's 0x658/0x668 but the function grows 64 B.

## Tools (tools/)

- `capvar.sh <name> <edits.py|-> <slot>`: copies the crate (`CRATE=` overrides), applies exact edits, captures
  pre-opt IR **and** MIR (`capboth.py`, `--emit=link,llvm-ir,mir -C no-prepopulate-passes`) through one
  slot-locked identity build, then runs w13a01's `rx.py` (raw-IR opt oracle).
- `llcx.py <name> <m.ll> <edits.py>`: exact text edits on post-opt IR, llc, score (e.g. lifetime moves).
- `mkitems.py <m.ll> <items>`: nolt of every lifetime alloca + every execute alloca to top/END.
- `pscan.sh <m.ll> <items> <tag> [n]`: w12a02 `iredit.py scan` split over n processes.
