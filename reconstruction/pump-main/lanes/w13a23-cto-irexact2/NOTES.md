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
