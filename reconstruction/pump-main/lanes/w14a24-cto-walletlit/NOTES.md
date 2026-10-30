# w14a24-cto-walletlit: wallet() CPI clone forms and the coin gate (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `walletlit`, keys `0x22a10-w14-1b0ae70-walletlit-*` and `0x22a10-w14-7e6aa9c-walletlit-*`.

## Result

| | main 7e6aa9c | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.6414 | **0.6417** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 79275da273f85033 |

Change (wallet, coin CPI gate): `if coin_present&&do_coin{` -> `if coin_present&do_coin{`. Both operands are plain
bools that are already computed, so `&` and `&&` mean the same thing. The gate now lowers to `and` + `jne +1; ja exit`,
which is the original's shape (`and64 r8,0x1; ...; jne r8,0x0,+0x1; ja -0x96a`). Before, it was `xor -1; or; and 1; jne exit`.
`do_coin&coin_present` gives the same tokens.

## The angle itself (per-site AccountInfo literal forms in wallet()) is dead

Both wallet CPIs, `create_idempotent` and `collect_coin_creator_fee`, are already in the original's form. The same holds
for the collect event's `event_authority` clone. Every account is an out-of-line `AccountInfo::clone` call, in the same order
and with the same field offsets, followed by the same `memcpy` (0x120 / 0x180):
- ATA create: `+0x28, +0x0, +0x40, <mint ptr spill>, +0x18->+0x58, +0x30, +0x20`
- coin CPI: `+0x58, +0x18->+0x58, +0x20, <mint ptr spill>, +0x80, +0x88, +0x40, +0x78, +0x58`

The TCF and sharing runs are different: there `to_account_info()` is inlined into field loads, so a literal's field order
moves the loads (#3250, #3260/#3272). In wallet() a literal inlines the Rc increments, which removes a clone call and
adds size:

| variant (oracle, main 1b0ae70 = 0.63661) | bytes | ratio |
| --- | ---: | ---: |
| coin_creator_token_account as orig-order literal | 28,024 | 0.35446 |
| ATA payer as literal | 27,768 | 0.6144 |
| `Create{associated_token,payer,..}` field order | 27,480 | 0.63147 |
| `Create{payer,authority,associated_token,..}` | 27,480 | 0.63117 |
| `CollectCoinCreatorFee{coin_creator,..}` first | 27,448 | 0.63424 |
| `{let x:&AccountInfo=..;x.clone()}` (token account / CPI program) | 27,400 | byte-identical |

Wallet flag spellings on 7e6aa9c (0.6414): `do_coin`/`do_collect` as if/else and `!(token_frozen(..)?)` are byte-identical;
the ATA gate `coin_present||!collection_native` gives 0.63691; adding `|` to the ATA gate gives 0.63672 @ 27,416;
rebinding `do_coin=do_coin&coin_present` gives 0.63881 @ 27,416.

## What is left in the wallet region: register naming

Ours and the original align exactly at 0x5c40 and 0x6a28. Byte-splice what-ifs on 1b0ae70: if the original's bytes
replace ours over

- [0x5c40, 0x6b08), the ratio rises by **+0.0357** (3,172 -> 2,884 slots);
- the ATA and flags part [0x5c40, 0x6060), by +0.0132;
- the collect arm and event [0x6060, 0x6800), by +0.0177;
- the coin CPI clone run [0x6878, 0x6a28), by only +0.0018.

Remapping only the four wallet spill slots (accounts 0x8e0->0x8d8, exit r1 0x8e8->0x950, mint ptr 0x920->0x910,
0x930->0x938) adds +0.0039 in the region and +0.0069 across the function. So about 85% of the wallet residual is
register naming, and one cause drives it: the `do_coin` flag is spilled to -0x938, where the original keeps it in r8.
That one difference:
- moves the clone buffer from r9 (original) to r7 and the accounts pointer from r7 to r8;
- removes the original's tail-duplicated gate after `create_idempotent`;
- changes the Err-edge payload copies.

w14a03-2 traced the r8 blocker to the sweep payload copy (`mov r8, r2` at 0x5b18), which is the swept/payload coalescing
problem (w14a06).

## Tools

- `tools/hunks.py <orig.dis> <cand.dis> <lo> <hi>`: difflib hunks over a region with registers and frame offsets masked.
- Oracle: w14a03 `capvar.sh` and `rx.py`, repointed to this lane (each variant is about 10-28 s, and `eq_main` holds on the base).

## After the landing (#3281, main d2d1875, 0.6417): non-short-circuit screen of every other pure gate

I screened every other `&&`/`||` in admin_cto.rs whose operands are free of side effects and `?`, using the oracle on main d2d1875.
Comparisons are parenthesized, because `|` and `&` bind tighter than `==`. None helps:

| site | form | bytes | ratio |
| --- | --- | ---: | ---: |
| 289 holder test | `st.holder_reward&!(hopt==Some(true))` | 26,608 | 0.52736 |
| 296 | `holder&!st.holder_reward&&..` | 26,872 | 0.43013 |
| 296 | `..&&!st.holder_reward&!st.holder_enabled` | 27,360 | 0.6197 |
| 312 | `(t==*sharing)\|(t==*holder_key)` | 27,400 | 0.60485 |
| 338 | `(f==0)\|(f>st.max_fee)` | 27,400 | byte-identical |
| shared | `(key==creator)&(owner==&FEES)&&!empty` | 27,392 | 0.55251 |
| shared | `..&&(owner==&FEES)&!empty` (eager) | 27,312 | 0.59715 |
| quote_locked | `(q==default)\|(q==native)\|\|contains` | 27,384 | 0.56818 |
| quote_locked | `..\|\|(q==native)\|contains` (eager) | 27,288 | 0.60883 |
| cashback | `!holder&st.cashback` | 27,400 | byte-identical |
| collect_old | `!st.holder_reward&(st.creator!=default)` | 27,368 | 0.63129 |
| wallet ATA gate | `!collection_native\|coin_present` | 27,416 | 0.63672 |
| pool_updated | `!empty&(owner==&AMM)` | 27,440 | 0.63673 |

The wallet coin gate is the only place where `&` helped, because only there does `&&` cost a separate xor/or block.
The collect-arm `emit_cpi` frame objects (event_signers at 0x680 and the bump at 0x548 in the original, versus 0x540 and 0x658 in ours)
are being screened by w14a25-cto-poollit, so I did not repeat them here.
