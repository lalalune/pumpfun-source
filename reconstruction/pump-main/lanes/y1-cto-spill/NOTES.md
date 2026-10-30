# Lane y1-cto-spill: 0x22a10 `admin_cto::execute` (family: spill-slot / frame-index order)

Base: main 0bcf7223c (programs/ identical on origin/main 3ca6d5027), baseline score
`pump-main-swarm/y-baseline/0bcf7223c/score.json`: 1032 normalized / 347 raw.
Target on base: 27,344 B (orig 27,400), ratio 0.37637, calls 154/3 (= orig).

## Result: official raw gain

| step | change (admin_cto.rs) | admin_cto bytes | ratio | normalized / raw | losses |
|---|---|---:|---:|---|---|
| base | origin/main | 27,344 | 0.37637 | 1032 / 347 | |
| v19 | `let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;` (old_fee read first) | **27,400** | 0.36159 | **1032 / 1032** (+685 raw) | 0 / 0 |
| k1 | v19 + sweep `let old=..;let bump=..;` (old bound before bump) | 27,400 | 0.36189 | 1032 / 1032 | 0 / 0 |
| **n12** | k1 + sweep token branch `let frozen=..;let amount=..;` (frozen bound first) | 27,400 | **0.36219** | 1032 / 1032 | 0 / 0 |

Head verified with a fresh fastbuild from the worktree: unstripped sha256
`37ef32e5056346300a2fd9514890a8c0702439fc55eabf4be2bc064d26b44488`, 1032/1032,
685 raw gains, 0 losses. swap_hop (0x5b3b0) now starts at its original address too
(ratio unchanged 0.85352).

Swapping the two reads in the `(old_creator,old_fee)` block changes register/spill
assignment downstream so admin_cto grows by exactly 56 B, to the original's size.
Every function linked after it then sits at its original address, so all 1032
normalized windows are also raw matches (685 raw gains, nothing lost). The
admin_cto ratio itself drops 0.015; that is the price of the size match, and any
later admin_cto change must keep exactly 27,400 B or it loses those 685 raw windows.

Sweep `old` before `bump` and `frozen` before `amount` are small regalloc/spill tweaks
(+0.0003 each) that keep 27,400 B.

## Rejected (0bcf7223c base unless noted; all zero losses)

byte-identical: `let new=new;` at entry; `let mut swept=0` at entry; old_creator block
flattened; `let holder` hoisted out of the state block; validate `new` by `&`; wallet
event fields pre-bound; sweep `&[bump]` temp (on v7).
worse: sharing key let before quote_locked (0.336); state block flattened (0.217);
pool seeds declared early (0.355, 27296); `match new` rebind after holder_key (0.352,
27728); `if let Some(val)=&sharing_update` (0.350); validate holder_key by `&` (0.360,
27440); pool_updated before the curve block (0.353, 27408); AdminCtoEvent timestamp
pre-bound (0.373); sweep seeds declared before the amm part (0.273).

On the 27,400 B head (each one moves the size, so it drops raw back to 347, or is
lower at the same size): quote_locked before shared (27392); sweep dest before native
(0.3568); CtoState outside the tuple block (0.3556); pool `&[bump]` temp (0.3613);
lamports before Rent::get (27384); wallet coin_present after source_present (27512,
155 calls); wallet coin_frozen first (27528); wallet coin_present first (27448);
AdminCtoEvent new_creator pre-bound (27480); shared before holder_key (27560).
byte-identical: holder_key `.0`, sweep dest `(dest,_)`, sharing reset flag pre-bound,
sweep `amm_empty` let.

Ledger: `log_attempt.py search --lane y1-cto-spill`. The v1 row
`0x22a10-0bcf7223c-spill-sweep-old-before-bump-v1` is tagged rejected by mistake; it
was +0.0003 closer (see the -v2 row).
