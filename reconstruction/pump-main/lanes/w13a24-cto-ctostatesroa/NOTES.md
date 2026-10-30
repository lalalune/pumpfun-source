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

## Part 2 (branch `swarm/w13a24-cto-ctostatesroa-2`)

### Landable: InvalidCreator operands swapped (gene `v312_rev`)

On main dfc3693 (0.59916 / 3,313; after #3011 and the AccountInfo clone layouts):
`if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}` gives **0.60126** / 3,313 at 27,400 B,
1034/1034, no losses, differential 363/0 (sha16 572d269e1c77a501). The same gene was rejected by w13a10's hill climb
on cb298d5, a24e177 and 2ca4d03; it pays only after the frame changes of #3011 and later.

### Holder-rewards PDA before `shared` (original entry order)

The original computes `find_program_address(["holder-rewards",mint])` right after `mint` (orig 0x22a90..0x22b48),
before the `shared` memcmp. Moving our `let holder_key;let hk=..;holder_key=hk.0;` before `let shared` (`k2`)
reproduces that entry order instruction for instruction (seeds slice, sret, copy to holder_key), but the function
shrinks: 0.56813 at 27,360 B on 6ac6f9b (0.56291 at 27,400), 0.59745 at 27,392 B on dfc3693, and
0.59955 / 27,392 with v312_rev. The 8 B (dfc3693) are register moves (no structural change); a size-neutral
companion is still needed. A 153-gene w13a10 library scan on 6ac6f9b+k2 found no +40 B companion (all genes either
keep 27,360 or collapse); best ratio v312_rev 0.57023 at 27,360. In the original the PDA sret temp is short-lived
(in the 0x2d0 group) and the space above holder_key holds X24 + new's 9 B piece; `hk` is a surrogate of the same
size.

### Faithful entry copy of `new` and holder_key by value (6ac6f9b)

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| e1 | validate reads `args.0` (args before block) | 27,464 | 0.49342 |
| e2 | args inside the block after st, validate reads `args.0` | 27,368 | 0.51289 |
| v1 | validate takes `holder_key:Pubkey` by value | 27,312 | 0.54254 (abs 0.69497 vs main 0.68604) |
| v3 | v1 + validate reads `args.0` | **27,400** | 0.51588 |

v1/v3 reproduce the original's frame objects: `sk` at 0x470 (the original's sharing-key temp), the holder_key copy
at 0x518 (orig T 0x518), and in v3 also P2 at 0x550/0x560 and new's 7/9 B pieces (0x660/0x670, orig 0x658/0x668),
but holder_key/mint move 24 B deeper and the build has 110 spill slots (orig 109); ratio is low. The skeleton
(abs) ratio rises, so they are faithful; they need the rest of the frame (X24, no `hk`) to pay.
