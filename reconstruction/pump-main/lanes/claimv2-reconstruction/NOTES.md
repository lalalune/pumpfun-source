# Lane claimv2-reconstruction

Target: original `0x77940` (8,832 B) = `token_incentives::claim_token_incentives::cashback::claim_v2`
(claim_token_incentives.rs:256). Not `migrate_v2::execute` (that is the matched 0x49888).

## Original structure (from `win.py orig 0x77940`, call targets resolved through score.json windows)

Error sites (`coords.py window 0x77940`): 305 (InvalidQuoteTokenProgram, 0x17b0), 310
(AccountTypeNotSupported, 0x177a), 342 (InvalidCashbackRecipient, 0x17bc), 333
(AccountTypeNotSupported); lines already matched the source.

Physical order of the original:

1. `Clock::get`, `quote_mint.key() == native_mint::ID` (memcmp).
2. Token branch first: two memcmps for token / token-2022 program (305, inline `to_string`);
   inline `AccountInfo` clone of `quote_mint` and owner memcmp (310, error path re-clones
   inline, i.e. `require_keys_eq!(*a.quote_mint.to_account_info().owner, ...)`);
   `associated_user_volume_accumulator.data_is_empty()` (AccountInfo call) -> 0, else
   `try_borrow_data` + `TokenAccount::try_deserialize`.
3. Native branch: `Rent::get`, inline clone + `data_len` + `minimum_balance`, then
   `lamports()` on the borrowed `&AccountInfo` (no clone) -> `get_lamports().saturating_sub(min)`.
   This is the same spelling as the v1 `claim`.
4. `amount == 0` is jump-threaded into each branch (shared `msg!` block).
5. Native `sub_lamports` inline; token payout checks (333 with an *outlined*
   `AccountInfo::clone` of `associated_quote_user`, `TokenAccount` decode, 342); `msg!`;
   native `add_lamports` inline (user = accounts+0xa8); `record_cashback_claim`; emit/emit_cpi;
   333 error (re-clones via outlined call); mint decode and `transfer_checked` (5 outlined clones).

## Trials

| trial | change | bytes | ratio | calls (orig 68+2) | official |
| --- | --- | ---: | ---: | --- | --- |
| base (d2cb88d) | - | 8,464 | 0.16706 | 62+2 | 1019/188 |
| t1-tokenfirst | token-first amount, `data_is_empty`, v1-style native rent, `to_account_info().owner` at 310/333 | 9,008 | 0.21729 | 63+2 | 1019/188, no gains/losses |

| t2-A | t1 + `if !native {token} else {native}` payout | 9,008 | 0.21729 | identical bytes to t1 | - |
| t2-B | t1 + manual user credit | 9,336 | 0.22525 | 66+2 | 1019/188 |
| t3-C | B + separate `if !native {333; recipient; 342}` before payout | 9,336 | 0.38510 | 66+2 | 1019/188 |
| t4-E | C with `add_lamports` | 9,008 | 0.38003 | 63+2 | 1019/188 |
| t4-F | C with `*associated_quote_user.owner` (no clone) | 8,824 | 0.40225 | 66+2 | 1019/188 |
| t5-G | zero check + 333/342 + mint/transfer on the token path, native has own zero check | 8,880 | 0.35508 | 68+2 | 1019/188 |
| t5-GF | G without clone at 333 | 8,584 | 0.20958 | 66+2 | 1019/188 |
| t6-GE | G + `a.user.add_lamports(amount)?` | 8,904 | 0.36389 | **68+2, all 70 calls equal to the original in order** | 1019/188 |
| **t7-H** | GE + `emit!(event)` (no clone; original builds the event once) | **8,808** | 0.36968 | 68+2, all 70 equal | 1019/188 |
| t8-I1/I2 | H + early `let user=&a.user;` | byte-identical to H | | | |
| t9-S1 | seeds inline in the call with `a.user.key()` | 8,800 | 0.35487 | 70 equal | 1019/188 |
| t9-S2 | `let user`; seeds inline in the call | 8,808 | 0.35938 | 70 equal | 1019/188 |
| **t9-S3** | `let user`; `let signer_seeds:&[&[&[u8]]]=&[&[..,user.as_ref(),&[bump]]]` | 8,808 | **0.37716** | 70 equal | 1019/188 |

### Residual after H (frame layout)

Opcode-only alignment (registers/offsets ignored) is 0.965; what remains is mostly stack-frame
offsets and register assignment. Frame objects (diagnostic `-print-before=prologepilog`/
`stack-coloring` dumps with `-Zfewer-names=no`, never proposed) show the candidate has the same
19 16-byte result slots and 6 spill slots as the original, and the same 280 B CpiContext,
192 B TransferChecked and 176 B recipient objects, but one extra 24 B object (frame 24 B deeper)
and a different top-of-frame order: original = bump(1) / user Pubkey(32) / outer seeds(16) /
inner seeds(48) / 24 / 48 / 24 / emit_cpi authority clone(48) / 192 / 280 / 176; candidate =
1 / 16 / 24 / 48 / 24 / 48 / 24 / 192 / 280 / 48 (seeds) / 32 (user) / 176. Frame index order is
reverse MIR local order (rustc inserts allocas at the entry top), so the original's seed
temporaries are created later in MIR than ours, or merged differently by stack coloring.

### Key mechanism: cold call sites

LLVM inline remarks (diagnostic copy build with `-C remark=inline`, flags never proposed):
`AccountInfo::clone` / `ToString::to_string` are inlined into `claim_v2` at threshold 325 on
warm sites and rejected at threshold 45 (`inline-cold-callsite-threshold`) on sites BFI
considers cold. The original's outlined clone at the 333 check and outlined `to_string` at
333/342 therefore mean those sites were cold, i.e. on the token path *before* any merge with
the native path. With a merged `amount` phi (t1..F) the 333 site is warm and the clone inlines.
Moving the token zero check and recipient validation onto the token path itself (t5-G) makes
the call sequence match. With that structure `add_lamports` also inlines (cost -14805,
threshold 250), so no outlined `Lamports::add_lamports` exists, as in the original.

Ledger: t1 `b9763c4eb3c9476bb82b7ee32b35a9c3`, A `cad6be18425a4cacb69d0e69ce3259d8`,
B `779096c7f3b0432e929e016dd92e723f`, C `51d54a58e53f4f4c83b2246fba46ff50`,
E `db86f2033bf14ee591c00a43d8142935`, F `131cbbe400594e6095f65d97d77cbfdc`,
G `16727f0ccb3d42f5b338762bfcc1cdad`, GF `ee182e841db741a0ada558adbe3168df`,
GE `1f28944501184011b2aaa4871182a842`, H `c04c00cdc28642d69b27648eed1d6479`, I `f25b14f092604998af3217262beb56be`, S1 `06216a76436f4ff591721bc57a1f02f2`, S2 `975fd093210e4909877edfb9a5ae634a`, S3 `09c26efb4c444d56a6d491a1f7c68db1`.

Frame note: the original's top-of-frame 1/32/16 B objects are the `emit_cpi!` event-authority seed temporaries (bump array, inner `[&[u8];2]`, outer slice); the user Pubkey of the transfer seeds is merged by stack coloring into that 32 B slot in the original, while in the candidate the emit_cpi 32 B slot is absorbed by a larger slot and `user` keeps its own slot.

## Round 2 (stack-coloring analysis)

Tooling (outside git, `$OUT/scripts`): `scsim.py` re-implements LLVM StackColoring
(collectMarkers / first-use starts / conservative slots / liveness / greedy size-sorted merge)
on a `-print-before=stack-coloring` dump and reproduces the candidate's surviving frame objects
exactly; `offmap.py` maps every original `r10` offset to the candidate offset through an
opcode alignment, which shows which original object each candidate object corresponds to.

Findings on S3: the spill/result region was 24 B deeper; the emit_cpi `[AccountInfo;1]` (`_204`)
was merged into the 176 B `recipient` TokenAccount slot, which pushed the emit seeds `[&[u8];2]`
(`_210`) into the transfer seeds slot and left `user` on its own slot. In the original `_204` is its
own slot (holding the transfer seeds), and `_210` holds `user`.

| trial | change (on S3) | bytes | ratio | opcode-only | official |
| --- | --- | ---: | ---: | ---: | --- |
| r1A | `let rent=Rent::get()?` | 8,760 | 0.3435 | 0.933 | 1019/188 |
| r1B | decode inside `require_keys_eq!` | 9,280 | 0.4501 | - | 74+2 calls (re-evaluated in error path), rejected |
| r1C | `let decimals=Mint::..?.decimals` | byte-identical to S3 | | | |
| r2D | `{let recipient=..;require_keys_eq!(..);}` block | 8,808 | 0.4913 | 0.967 | 1019/188 |
| r2E | `let user` before the recipient decode | 8,728 | 0.3724 | | |
| r2G | `let cpi_ctx=CpiContext::new_with_signer(..)` | 8,808 | 0.4857 | | |
| r3DG / r3DA | D+G / D+rent let | 8,808 / 8,760 | 0.446 / 0.450 | | |
| **r3D2** | `let recipient=TokenAccount::try_deserialize(..)?.owner;require_keys_eq!(recipient,..)` | 8,856 | **0.60103** | **0.978** | 1019/188 (1020 after merging main: +0x14f4e0 from main) |
| r4A | D2 + `let rent` | **8,832** | 0.5421 | 0.945 | |
| r4R5 | bound `try_borrow_data()` guard (on S3) | 8,848 | 0.3642 | | |
| r4Nc | D2 + min inline in `saturating_sub` | 8,848 | 0.5929 | | |

With D2 the whole spill/result region (-0x388 and below) and the top of the frame
(-0x1..-0xf8: emit bump, `_210`+user, outer seeds, `_204`+transfer seeds, invoke result,
Chain iterator, inner_data, authority_info) sit at exactly the original offsets.
Residual frame difference: candidate keeps the Rent `ControlFlow` SROA piece
(`_140.sroa.5`, 24 B, no lifetime markers) as its own slot after authority_info and has a
120 B SROA piece of the recipient decode plus a 32 B owner slot at the bottom; the original
has one 176 B object at the bottom that also holds the Rent piece and `ix_data`
(original -0x380 maps to the candidate's `_140.sroa.5`).

Ledger: r1A `dcaf8227`, r1B `8d461e42`, r1C `1601eefb`, r2D `a6753aa5`, r2E `af427cca`,
r2G `7a862c65`, r3DG `40b9fd8c`, r3DA `70107109`, r3D2 `fc5f630c`, r4A `709cdfb5`,
r4R5 `152968e3`, r4Nc `960c06ba`.

### Native branch first (r5SW, ratio 0.601 -> 0.817)

`offmap.py` on D2 showed the original's bottom 176 B of frame is three unmarked objects in this
order (deepest first): the `Rent::get()?` ControlFlow payload (`_140.sroa.5`, 24 B), the recipient
owner (32 B), the recipient decode piece (`val6.sroa.2`, 120 B). Frame index order is the reverse
of alloca creation order, which follows MIR local numbering, so in the original the Rent locals
are created before the recipient locals: the native branch comes first in the source.
`let amount=if native{rent; amount; zero check; sub; add; amount}else{305; 310; ..; transfer; amount};`
(native block on the pad line 304, so no error line moves) puts every frame object at the
original offset (offmap: 100 of 109 offsets map with delta 0). Same 68+2 calls, 8,856 B,
ratio **0.81661**. Ledger `1b851d5c`.

Residual: register assignment. The original computes `&a.user` (accounts+0xa8) once right
after `Clock::get` and spills it to -0x4c0; the candidate rematerializes it at each use.

### Account bindings and event fields (ratio 0.817 -> 0.938)

| trial | change | bytes | ratio | opcode-only |
| --- | --- | ---: | ---: | ---: |
| r6U2 | `ctx.accounts.X` everywhere, no `a` | 8,776 | 0.7886 | |
| r6U3 | v1 style `let user_volume_accumulator=&mut ctx.accounts.user_volume_accumulator;`, rest via `ctx.accounts` | 8,856 | 0.81848 | 0.978 |
| r6U4/U4b | U3 + `let user=&ctx.accounts.user` | byte-identical to U3 (shared ref propagated by MIR) | | |
| r7X3 | U3 + `let user=&mut ctx.accounts.user` after timestamp | 8,824 | 0.9266 | 0.991 |
| r7X4 | destructure `let ClaimCashbackV2{user,user_volume_accumulator,..}=&mut *ctx.accounts` | compile error E0502 | | |
| r8F1 | X3 + v1 `let total_cashback_earned` | 8,824 | 0.9210 | |
| r8F2 | X3 + `let total_claimed=..;let total_cashback_earned=..;` then the event literal | 8,824 | 0.93502 | 0.993 |
| r8Pa | X3 with `let user=&mut ..` as the first statement | 8,824 | 0.92941 | 0.994 |
| **r9FP** | F2 + Pa | 8,824 | **0.93782** | 0.9958 |

Mechanism: a `&mut` binding of `ctx.accounts.user` is not propagated away by MIR
(a shared `&` binding is), so `&user` (accounts+0xa8) becomes one SSA value defined at
the entry and spilled to -0x4c0 as in the original. Binding the two totals before the event
literal puts their loads ahead of the user key copy, as in the original.

Residual (r9FP): (1) the original has `jeq ok,+1; ja err` at the `try_borrow_data()?` of the
token amount decode where the candidate has one `jne`; the extra instruction shifts every later
jump offset. (2) the `try_borrow_data` result and `Ref` temporaries of both token decodes sit in
different stack-coloring groups (original: result in the 280 B group at -0x2d0, Ref at -0x1b8;
candidate: result at -0x1b8, Ref at -0x68). (3) emit_cpi seed store order.
Ledger: U2 `449607fc`, U3 `130220a4`, U4 `173d39a6`, X3 `137aae75`, X4 `2e9c66ca`, F1 `75459852`,
F2 `774081e6`, Pa `b15e6736`, FP `aca9d7bd`.

### Decode blocks (ratio 0.938 -> 0.969)

| trial | change (on r9FP) | ratio |
| --- | --- | ---: |
| r10b | `try_deserialize(&mut x.try_borrow_data()?.as_ref())` | byte-identical |
| r10d | `{let data=x.try_borrow_data()?;T::try_deserialize(&mut &data[..])?}` for all three decodes | 0.9612 |
| r10f | `{let mut data:&[u8]=&x.try_borrow_data()?;T::try_deserialize(&mut data)?}` | 0.96587 |
| **r11d2** | r10d with `.amount` / `.owner` taken inside the block (owner copied before the Ref guard drops, as in the original) | **0.96868** (slice form r11both identical) |
| r12J1 | `if !data_is_empty(){..}else{0}` | byte-identical |
| r12SA / r12SC | seed spellings `&[seeds]` / bump array | 0.96868 / 0.9612 |

With the bound guard, the `try_borrow_data` result and the `&[u8]` temporaries land in the original's
stack-coloring groups (result in the 280 B group at -0x2d0, slice at -0x1b8). Remaining opcode
differences: `jeq ok,+1; ja err` at the amount decode's `try_borrow_data()?` (one extra instruction
shifting all later jump offsets) and the order of the transfer signer-seed stores.
Ledger: r10b `6ee8121e`, r10d `56471f27`, r10f `5d3e8733`, r11d2 `9d79c17e`.

### Empty-ATA early return (ratio 0.969 -> 0.99626, exact size)

Spellings of the amount decode (`if !empty`, `let mut amount`, `match bool`, deref guard, slice binding)
are all byte-identical, an explicit `match` on `try_borrow_data` is worse (0.867), and a helper fn is worse
(67 calls). `305` as `if !(..){return err!(..)}` is identical (that is what `require!` expands to).
Following the cashback-inner lane's finding (LLVM block creation order decides whether the
`try_borrow_data` Ok block is the IR successor of its test; BPF cannot reverse branches afterwards),
the token path now returns early on an empty ATA:
`if ata.data_is_empty(){msg!("No cashback to claim");return Ok(());}let amount={let data=..?;TokenAccount::try_deserialize(&mut &data[..])?.amount};if amount==0{msg!(..);return Ok(());}`.
Result r17Z1: **8,832 B (original size), ratio 0.99626, 15 slots differ**, all in the transfer
signer-seed stores at 0x2080 (the outer seed slice is stored after the seed lengths instead of before).
Ledger: r17Z1 `7f9bfaeb`; rejected spellings `c352c1e6`..`a3a8918e`, `4f4663a7`, `662919ca`.

### Normalized match (r18S4)

`let bump=ctx.bumps.user_volume_accumulator;` bound before
`let signer_seeds:&[&[&[u8]]]=&[&[b"user_volume_accumulator",user.as_ref(),&[bump]]];`
(instead of `&[ctx.bumps.user_volume_accumulator]` inside the array). The bump byte is loaded before the seed
array is built, so the outer seed slice is stored first, as in the original. **0x77940 normalized-equal
(8,832 B, ratio 1.0, 0 slots differ).** After merging origin/main (ef400863f): official 1021 normalized / 188 raw,
gains 0x77940 (and 0x14f4e0, already on main), no losses; candidate sha256 bba5d390... Raw is not equal.
Other seed spellings on the Z1 base: `let seeds` + `&[seeds]` 31 slots, inline in the call 39 slots.
Ledger: r18S4 `73ac75aa`, SA `3e8ede82`, S1 `15b8879a`.
