# Lane w6r2-layout-order (wave 6, round 2): function order and placement for raw

Base: origin/main a7135a6a6 (1027/1035 normalized, 276 raw, 8 unmatched windows).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w6r2-layout-order/`. The model is
layout-order-census `fastmodel.py` + w3-raw-layout `m13.py` + w6r1-layout-order `metrics.py`
(copied there, paths repointed). `tools/resid.py` (new) lists, for the full-original-order /
fixed-size scenario, every window that still fails and the call that breaks it.
`tools/trial.sh` = fastbuild + score + unmatched-window check + sha.

Open PR #2168 (w6r1-layout-order) already put the L block (local items) in the original order
except buy_handler. Its head (b588742e5, main merged in) scores 1027/277 (+0xa868) here. This lane's
change is independent of #2168 and composes with it.

## Kept: twin `transfer_native` helpers in the original definition order (`c0ffb98d`)

On #2168 the full-original-order model with fixed sizes gave 1023 of 1027, not 1027. `resid.py`
showed that all four residual windows (0x45fa0 `migrate::init_pump_amm_boost`, 0x49888
`migrate_v2::execute`, 0x52660 `migrate_v2::init_pump_amm_boost_v2`, 0x97930
`user_payments::transfer_from_user`) call one of two twin 1208-B units, 0x8df98 and 0x8e450, and
miss by +-1208 B. The twins have identical bodies: their raw bytes differ only in the displacement of
one call to the same target, at +1152. So pairing cannot tell them apart, and only the callers do. In the
original, transfer_from_user calls the first one (0x8df98) and the migrate callers call the second
one (0x8e450). In our source, `migratenp_transfer_native` (called by migrate) was defined before
`uqp_transfer_native` (called by transfer_from_user).

Change: swap the two definitions in `util/payments.rs`. Neither has a `line!()`/Location site,
and the swapped block keeps its total line count, so every later line is unchanged.

| metric | main a7135a6 | + swap (t01) | #2168 | #2168 + swap (c01) |
| --- | ---: | ---: | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276 (0 gains, 0 losses) | 1027 / 277 | 1027 / 277 (0 losses vs #2168) |
| 8 unmatched windows (bytes, ratio) | | identical | | identical |
| refine `badcalls` (paired call operands pointing at an unpaired callee) | 6 | 1 (the ensure_rent wrapper #2168 removes) | 5 | **0** |
| model: full original order, fixed sizes | 1022 | 1026 | 1023 | **1027 (every matched window)** |
| model: original L order, U/D as built, fixed sizes | 654 | 656 | 702 | **706** |
| model: our order, fixed sizes (P8) | 429 | 429 | 462 | 462 |
| unstripped sha256 | 31ec6381 | ba4e5184 | 419a8456 | b1fee8da |

Official raw does not move: transfer_from_user also has data lddw and calls into D across the
unmatched windows' size deltas.

## Why official raw cannot rise from order at today's sizes (scen3 on #2168)

| scenario (today's sizes) | raw |
| --- | ---: |
| as built (#2168) | 277 |
| original L order | 277 (+0: L is exhausted) |
| original U order | 279 (+0xa7e0, 0xea68, 0xf130, -0xa868) |
| original D order | 291 (+14) |
| full original order | 293 |

- U (upstream generic instances in our crate, sorted by symbol name): the remaining differences are
  `17h<hash>` order within same-path groups. Legacy symbol hashes mix in our StableCrateId
  (crate name + cargo `-C metadata`) and the DefPathHashes of the type arguments, so they are
  not reachable from source. The only re-orderable members would come from moving local types to other modules
  (hash fishing), which is not an ordinary source-order change. Three
  non-hash anomalies remain: `drop_in_place<pump_recovered::{migrate::Migrate, admin_cto::AdminCto,
  multi_hop_curve::PreviousHop}>`. They sort by length prefix, and that length fits a 4-character crate
  name (`pump`, w6r1-layout-order). Moving each type to a module with a shorter path could fit the lengths. That changes
  def order, though, and is again a path game for +3 model / +0 official.
- D (dependency objects): every remaining difference is same-generic hash order inside a dependency
  (borsh `Option<T>` (de)serialize in mpl_token_metadata, `RawVec::grow_one`, `&T as Debug/Display`,
  `std::io::Error::new`). That order comes from the dependency's own cargo metadata, not from this crate.

Where raw is left once the unmatched windows match their sizes (#2168 + this change): 462 with our
order. buy_handler at the #[program] position (handler lanes, see w6r1-layout-order) adds +244 (706).
U/D hash order adds +321 (1027).

## Size marginals (`tools/sizemarg.py`, #2168 + this change, our order)

Size deltas (original - ours): admin_cto +56, swap_hop +40, sweep -48, v3_buy_costs -16, buy_handler -32,
buy_exact_quote_in -32, buy_exact_quote v3 -16, create_v2 0. Fixing only sweep gives 459 official raw (model).
The other deltas happen to sum to 0, so `.text` would reach the original size and the data windows would unlock.
That is a coincidence, like 0xa868: any later size change of another unmatched window undoes it. Each other
single fix alone gives 276. Fixing all of them gives 462.

## Attempts

| id | trial | result |
| --- | --- | --- |
| `c0ffb98d` | t01 / c01: twin transfer_native definitions swapped | kept: 0 losses; full-order model 1027/1027, badcalls 0 |
| `a59ea8b9` | scen3 order ceiling at today's sizes on #2168 | analyzed: L +0, U +2 net, D +14 (all hash) |
| `dce0be0c` | unmatched-size marginals | analyzed (above) |
| `bd501961` | drop_in_place path-length check | analyzed: our module paths are right, only the crate name differs |
