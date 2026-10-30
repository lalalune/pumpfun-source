# Lane admincto-reconstruction: 0x22a10 `admin_cto::execute`

Baseline: origin/main 16eecb1 (1020 normalized / 188 raw; built at `$OUT/out/base`).
Tools in this directory: `annotate.py` (event map: resolved callees, log literals, Source lines),
`cfg.py` (basic-block CFG with successors/predecessors and events) for the original window or a
candidate build.

## Assembly findings (original 27,400 B, 378 blocks)

1. Entry computes, before any validation: `holder-rewards` PDA from the mint, then
   `shared = bonding_curve.creator == sharing_config.key && sharing_config.owner == FEES && !sharing_config.data_is_empty()`
   (that operand order), then `global_quote(bonding_curve.quote_mint)` (default / native / whitelist[0]), then
   caches curve and global scalars.
2. Old-creator wallet handling (logs "is a program" / "not system-owned", writable check line 556,
   frozen log, collect + create_idempotent + collect_coin_creator_fee) runs BEFORE the shared holder
   sweep, and is gated on `!shared && !bonding_curve.is_holder_reward && old != default`.
3. Error sites 556, 648, 660, 719 are followed by an `Ok`-tag (`== 2`) check: the code containing
   them was a Result-returning body inlined into execute and propagated with `?`. Sites 284..410
   return directly.
4. Hot/cold: `<AccountInfo as Clone>::clone` (cost 60) inlines only at sites >= 2 % of entry
   frequency. In LLVM's `updateThreshold`, a cold call site calls `DisallowAllBonuses()`, which also
   removes the 15,000 last-call-to-static bonus, so a big single-use private helper or closure is
   inlined only when its call site is not cold. The caller's BFI is not recomputed while the
   inliner works through execute's call list, so blocks after an inlined helper keep the frequency
   they had before it was inlined.

## Trials (ledger lane `admincto-reconstruction`)

| trial | mechanism | bytes | calls | block_jaccard | insn_jaccard | win ratio |
|---|---|---:|---:|---:|---:|---:|
| base | origin/main 16eecb1 | 18,464 | 178 | 0.068 | 0.200 | 0.095 |
| t1 | hoist PDA/shared/global_quote; wallet section before sweep, original gate | 17,872 | 177 | 0.076 | 0.205 | 0.117 |
| t2 | + wallet and sweep as Result closures | 11,008 | 86 | | | 0.088 (closures outlined: cold sites) |
| t3 | + validations (284..338) in a Result closure at entry | 24,976 | 109 | 0.190 | 0.258 | 0.066 (1 loss: AdminCtoEvent::data inlined) |
| t4 | + wallet gate moved inside its closure (unconditional call) | 26,888 | **154 = orig** | 0.204 | 0.274 | 0.051 |

t4: the direct-callee multiset equals the original's (154 calls, 3 syscalls), the transfer and
sharing-config CPI clones are inlined as in the original, and the other 33 clone calls stay
outlined. Zero losses (1020/188). win.py's difflib ratio falls because the block layout differs;
block_jaccard and insn_jaccard (callgraph-census `blocksim.py`) both rise.
| t5 | + gate `collect_old` computed before prepare_bonding_curve | 24,576 | 163 | | | 0.103 (call order closer, sharing_config CPI goes cold) |
| t6 | + sweep / reset flags precomputed | 24,512 | 163 | | | 0.069 |

t5/t6 not kept: in the original the gate flags are computed before prepare, but here that pushes the
sharing_config CPI site below 2 % entry frequency. Next: tune what is computed early
so physical order matches without losing the hot CPI sites; replace closures with named helpers.

## Round 2 (base: merged main 60bdd8a, then abd766d with #1246 = t8 merged)

Pre-inline BFI of execute (`-print-bfi`, `-print-before=inline`, diagnostic build d5): every `?` tag
check on a Result is 50/50 and `require!(creator_fee==0)` is 37.5 %. t5 called the wallet closure
unconditionally (gate inside), so the post-wallet join was 0.047 of entry and the sharing_config CPI
site 0.0176 (< 2 %, cold, clones outlined). The original branches once on a precomputed gate
(`1c78: jne r6`) before the inlined wallet body, so its join keeps the 0.047 skip mass plus 0.023.

| trial | mechanism | bytes | calls | blocks | win ratio | callseq |
|---|---|---:|---:|---:|---:|---:|
| t7 | `collect_old` before prepare; `if collect_old { wallet()? }` (one precomputed gate) | 27,440 | 154 | 370 | 0.152 | 0.667 |
| t8 | sweep body in original shape (native = quote_mint==native_mint at sweep start; `!empty && token_frozen`; seeds before the native branch; Rent::get then minimum_balance then lamports; raw_amount, frozen, `if frozen {require 719} else if amount>0 {create; transfer}`) | 27,176 | 154 | **378 = orig** | 0.167 | 0.778 |
| t9 | `sharing_update: Option<Option<Pubkey>>` computed after validation (event's `sharing_config_reset` is `tag != 2` in the original); `target=old` for shared&&!holder fixed before prepare | 27,064 | 154 | 374 | 0.183 | 0.778 |
| t10 | old creator/fee read from the curve right before the update; event reads new_creator, fee bps, holder and cashback flags back from the curve (as the original's event block does) | 27,160 | 154 | 371 | **0.193** | 0.778 |

All zero losses (1020/188). t7 and t8 were merged in #1246. Ledger ids: t7 44d5741f, d5 62ab6da8,
t8 eeff1b3e, t9 fe58b274, t10 43a05a3d.
