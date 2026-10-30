# w13a23-cto-irexact2: exact-IR recipe for 0x22a10 `admin_cto::execute` on main 1043a51e8

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a01-cto-irexact (#2899, `origin/swarm/w13a01-cto-irexact`): its recipe was for 4394685 and is stale.

## Oracle validation on 1043a51e8

`tools/capraw.py` + `tools/rx.py` on main's unedited pre-opt IR: 0.53206, 27,400 B, `eq_main=true` (tokens equal the
landed baseline build). The post-opt `llc` oracle (`tools/iredit.py run`, w12a02) on the slimmed `opt -O3` output gives
the same 0.53206 / 3,324 slots. ~0.1 s per edit when run as several processes (the per-item difflib is GIL-bound, so
run `iredit.py scan` as 8 processes with `-j 2`, not one process with `-j 8`).

## Step 1 (landed in this PR): the wallet emit_cpi `invoke_signed` result slot

Scan: every alloca moved before every 4th alloca (+END), every `nolt`, `bw` 2000:1 / 1:2000 and `inv` on every condbr.
The only single edit above main at 27,400 B was **`mv:_115.i:_92.i` = 0.54793** (abs ratio unchanged: a pure frame move).
`_115.i` is the 24 B `sret` of the wallet's `invoke_signed` (the `CollectCreatorFeeEvent` emit_cpi). Plateau of its
position: before `_100.i`, `ix.i` or `_92.i` (0.54793); in place 0.53206; just below (ix_data/inner_data/authority_info)
0.534-0.535; anywhere else lower.

LLVM lists the inlined function's allocas in reverse MIR-local order, so the plateau means the call's destination
local must be created **after `ix`'s initializer temps and before the signer temps** (`event_inner`'s `[&[u8];2]` and
`[authority_bump]`). The original matches anchor's `emit_cpi!` order (destination first, then the signer temps in the
call args); ours created the signer temps in an earlier `let event_inner` statement.

Source (same lines): evaluate the signer setup and the call as one block that is the receiver of `map_err`.
`as_temp` allocates the receiver temp before lowering the block, and the block's tail call writes straight into it:

```rust
         ({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&event_signers)}).map_err(anchor_lang::error::Error::from)?;
```

| build | ratio | slots | bytes | normalized/raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 1043a51e8 | 0.53206 | 3,324 | 27,400 | 1034/1034 | |
| this change (measure.sh, sha 32fc305775dd5c06) | **0.54793** | 3,323 | 27,400 | 1034/1034 | none |

Runtime differential: 363 cases, 0 mismatches. The source result equals the IR oracle exactly.

Rejected spellings (ledger `0x22a10-w13-1043a51-irexact2-*`):

| trial | form | ratio | bytes |
| --- | --- | ---: | ---: |
| t4 | anchor literal `invoke_signed(&ix,&[authority_info],&[&[b"..",&[bump]]])`, no `event_signers` | 0.52756 | 27,400 |
| t1 | `let r;` before `event_inner`, `r=invoke_signed(..); r.map_err(..)?` | 0.52394 | 27,128 |
| v1 | `let r={..block..}; r.map_err(..)?` | 0.5399 | 27,128 |

t4 puts the destination in the right place but the 16 B signer slice leaves its F1 position; t4 + moving the slice back
is 0.55033 in IR. `Result<(),ProgramError>` needs drop, so a named `r` adds drop code (t1/v1 size change).

## After #2991: ranked oracle edits on the following mains (ledger `0x22a10-w13-{bf9a05d,d81d0f5}-irexact2-*`)

Machine-readable: `recipe.json`. All runs are the post-opt `llc` oracle at 27,400 B unless noted.

| main | base | best single edit at 27,400 B | kind |
| --- | ---: | --- | --- |
| 1043a51e8 | 0.53206 | `mv:t.i:END` / `sk` before `t.i` 0.55183; `mv:_115.i:_92.i` 0.54793 | frame (landed: #2989 valslot, #2991 this lane) |
| bf9a05d02 | 0.55872 | `bw:bb82:2000:1` 0.56351; `mv:target.sroa.8:<inlined>` 0.55902 | block frequency (spill-slot order) / frame +0.0003 |
| d81d0f588 | 0.571 | `bw:bb27.i64:1:2000` 0.5719; `mv:target.sroa.8:<inlined>` 0.5713 | frequency / frame +0.0003 |

- **Alloca order is exhausted on d81d0f5.** 6,051 single edits (every alloca before every 4th alloca and END,
  `nolt`, `bw` both ways, `inv`), the full 15k stride-1 move matrix on bf9a05d, and 7.9k pairs of moves to TOP/END
  on d81d0f5: nothing beats `mv:target.sroa.8` (+0.0003). No E32-style two-object lever is left.
- **Greedy (bf9a05d)**: `bw:bb82` +0.0048, `bw` clone exit52.i +0.0021, `bw:bb27.i64` +0.0009, then
  `mv:target.sroa.8` +0.0003: 0.56681. Everything but the last is block frequency only, which no source construct
  sets here (rustc emits weights only for `#[cold]`/`likely`; an inlined empty `#[cold]` call vanishes before BPI).
- **movescan (w13a12) on bf9a05d**: no gain at 27,400 B (best 0.56419 at 27,336).
- **Per-call-site noinline/alwaysinline (raw-IR opt oracle, 53 of 68 sites)**: no gain; each real change moves size.
  `to_string` noinline at 307/312 on d81d0f5: 0.55478 at 26,984 B (-416 B).
- **Size oracle (`sz:A:N`, new)**: on bf9a05d shrinking any object between old_creator and mint by 8 B gained
  +0.006-0.008 (`sz:holder_key:24` 0.56651, `sz:st:40` 0.56621). That located the +8 B: `st` (48 B, kept in memory only by
  the `st.creator` memcmp) in the original's 40 B new-copy/X24 area. #3011 (ctostatesroa) then fixed it, and on
  d81d0f5 mint and every spill slot from 0x6d0 to 0x8c8 sit at the original offsets.
- **Frame object map (`tools/objmap.py`, new)**: per frame object from debug `llc -debug-only=prologepilog,stack-coloring`
  (`tools/layout.py`), it votes the original offset over frame-masked aligned accesses. On d81d0f5 every object from
  the top of the frame through old_creator (0x630) has d=0. The open displacements are:
  - the 0x630-0x6a0 block: val6, `target.sroa.0` (7 B), `hk` (33 B), holder_key, and the original's 24 B host at 0x680
    that holds the signer slices (`event_signers.i` votes 0x680);
  - the deep RA spill slots (0x8d0 and below), which follow allocation order, not allocas.
  Perfect-frame bound on d81d0f5: 0.6336 (`PF=1 iredit.py run`).
- Region split (`tools/rsplit.py`, w13a15 thirds) for reference on bf9a05d: R1 0.17016, R2 0.15518, R3 0.23337.

### Tools added (text only)

| tool | use |
| --- | --- |
| `mkscan.py` + `pscan.sh` | build the 6k single-edit list and run it as 8 processes (difflib is GIL-bound; ~17 edits/s vs ~3/s threaded) |
| `layout.py <pe.log> <post.ll>` | our frame layout: offset, FI, alloca, size, stack-coloring members |
| `objmap.py orig.rel cand.dis pe.log post.ll` | per-object original offset votes and displacement `d` |
| `csedit.py` + `csscan.sh` | raw-IR opt oracle with a noinline/alwaysinline attribute on the k-th call site of a function |
| `rsplit.py fn.bin` | ratio split by original thirds for oracle outputs |
| `allocas.py post.ll` | alloca list with sizes and lifetime flags |

### Main 06e6bb829 (0.57669, after 6968c84's system-clone literal)

Single-edit scan plus size-pinned greedy: **0.58748**. The new lead is block frequency in the clone runs:
`bw 1:2000` on an `AccountInfo::clone` `Rc::inc_strong` overflow-abort branch (`..inc_strong..exit.i98.i`) alone gives
**0.58448** at 27,400 B, abs 0.67466 -> 0.68814. It changes register allocation in the clone run (our insns ~1157-1413).
The greedy then adds `exit.i115.i` (+0.0015), `bw:bb27.i64` (+0.0009), `mv:target.sroa.8` (+0.0003) and `inv:bb69`
(+0.0003). BPI already treats the abort edge as cold, so the gain comes from making it colder; this is clonefeat's
clone-run register allocation territory. Alloca moves still give only `mv:target.sroa.8` (+0.0003). Perfect-frame
bound: 0.61714.
