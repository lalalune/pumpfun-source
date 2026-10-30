# Lane y1-cto-callee: 0x22a10 `admin_cto::execute` (family: callee and inline boundary)

Base: origin/main dce6faf97 (programs/ equal to baseline 0bcf7223c except the unrelated token_schedule files);
baseline score 1032 normalized / 347 raw. Builds: `~/.cache/pumpfun-reconstruction/lanes/y1-cto-callee/`.

## Result (committed)

| metric | main | this branch | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,384** | 27,400 |
| win.py ratio | 0.37637 | **0.38945** | 1 |
| calls (internal, syscall) | 154, 3 | 154, 3 | 154, 3 |
| `<T as ToString>::to_string` calls / inlined | 5 / 10 | **7 / 8** | 7 / 8 |
| official normalized / raw | 1032 / 347 | 1032 / 347 | |
| gains / losses (norm, raw) | | 0 / 0, 0 / 0 | |
| unstripped sha256 prefix | 3ca6911a64bd | 48ab3c97a3b8 | |

`swap_hop` (0x5b3b0) now sits 16 B early instead of 56 B; its ratio and `create_v2` are unchanged.

Source (validate only, line numbers unchanged):
1. #2370 + #2416 mechanism rebuilt: the line-296 `HolderRewardDisabled` check moves into the `if holder` arm, and
   `validate` takes `mut new` with `new.take()` at 298 and 306. The 307/312 `error!` sites drop below the 2% cold
   call-site cut, so `to_string` stays outlined there as in the original (lddw multiset equal). Alone: 27,144 B / 0.39061.
2. New: `validate` takes `holder_key: &Pubkey` instead of by value (`*holder_key` in the holder arm, `t==*holder_key`).
   This adds 240 B of the original's spill/copy traffic: 27,144 -> 27,384 B. The ratio is 0.38945, slightly below
   step 1 alone, but the size gap to the original drops from 256 B to 16 B, and every metric beats main.

## Why 307/312 are inlined on main (BFI dump of `validate`, diagnostic `-print-bfi`)

Before the inliner, 307 (bb29) is at 0.02197 and 312 (bb36) at 0.02232 of validate's entry, just above the 2% cut.
The top-level `holder && !hr && !he` check leaves an infeasible holder=true edge (bb18 -> bb20, 0.047) into the
non-holder arm. That edge alone puts 307/312 above 2%. Note that `if st.mayhem` is `icmp eq i8 0` (ZeroHeuristic):
only 0.375 continues.

## Attempts (ledger approach `callee`)

| variant | mechanism | bytes | ratio |
| --- | --- | ---: | ---: |
| v1 | sweep(a:&AdminCto, bump:u8, holder_key) instead of &Context | 27,368 | 0.36960 |
| v2 | 306 as `new.ok_or_else(|| error!(..))?` | 27,392 | 0.36165 (tag check folded, 307/312 still inline) |
| v3 | #2416 rebuild | 27,144 | 0.39061 |
| a, d | v3 + sharing by ref / CtoState by value | = v3 | |
| e | v3 + fee:&Option<u64> | 27,112 | 0.39055 |
| f | v3 + new:&Option<Pubkey> | 26,928 | 0.32392 |
| **b** | **v3 + holder_key:&Pubkey** | **27,384** | **0.38945** |
| b2/b3/b5/g13/h3/h7/k4 | b + sharing ref, compare spelling, param order, `.0`, map_err identity on sweep/wallet, clone | = b | |
| b4 | b + &a.sharing_config.key field | 27,040 | 0.23458 |
| g5 | b + target out-param | 26,800 | 0.13206 |
| g11 | b + sweep holder_key by value | 27,448 | 0.22262 |
| h1 | holder_key:&Pubkey on main (no v3) | 27,440 | 0.35983 (to_string 5) |
| k1 | b + validate takes sharing &AccountInfo | 27,112 | 0.24210 |

The remaining big lever is still the sweep-tail placement (the merged sweep-exit tag re-check; see w9r1/w10r1 notes).
No callee-boundary spelling tried here (map_err identity, out-param, by-value/by-ref keys) un-threads that exit.
