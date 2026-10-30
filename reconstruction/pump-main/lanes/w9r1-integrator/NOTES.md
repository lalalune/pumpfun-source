# w9r1-integrator

Continuous integration of open swarm PRs onto latest main, scored with `score.py` against a
fresh main build.

## Baseline

origin/main 2bb05a51a (after #2397 merged): 1032/1035 normalized, 337 raw.
unstripped sha256 d2bc54a14d8400a19f3528e9f66a3d8a012fc81125dae63cc6d18bb3e23f413f.

| window | function | main bytes (orig) | ratio | slots |
| --- | --- | --- | --- | --- |
| 0x22a10 | admin_cto::execute | 27344 (27400) | 0.37637 | - |
| 0x5b3b0 | multi_hop_curve::swap_hop | 18544 (18584) | 0.7332 | - |
| 0x1e7c0 | create_v2::execute | 15576 (15576) | 0.99892 | 4 |

## Round 1 combinations (all on 2bb05a51a, zero losses unless noted)

| combination | swap_hop bytes | ratio | norm/raw |
| --- | --- | --- | --- |
| #2403 alone (&Context param) | 18600 | 0.83042 | 1032/337 |
| #2370 alone (admin_cto) | admin_cto 26928, 0.32392 (worse on this main) | | 1032/337 |
| #2403 + #2387 (hillclimb) | 18584 = orig | 0.83472 (1657 slots) | 1032/347 |
| **#2403 + #2368 (frame)** | **18584 = orig** | 0.83297 (**1636 slots**) | **1032/347** |
| #2403 + #2368 + #2366 | 18608 | 0.83636 | 1032/337 |

### Hunk census on #2403 (string-replace mutations, bin/mut.py)

F1 = `require_gt!(base,0,BuyZeroAmount)`, F2 = `match &post_fill` base-out (F1+F2 = #2368),
E = unconditional buyback `else` (#2366/#2387), N = `const NO_FEE` (#2366).

| subset | bytes | ratio | slots_diff |
| --- | --- | --- | --- |
| none (#2403) | 18600 | 0.83042 | |
| E | 18600 | 0.83217 | |
| N | 18624 | 0.83293 | |
| F1 | 18608 | 0.83242 | |
| F2 | 18576 | 0.83184 | |
| F1 E | 18608 | 0.83417 | |
| F2 E | 18576 | 0.83359 | |
| F1 N | 18632 | 0.83493 | |
| F2 N | 18600 | 0.83435 | |
| N E | 18624 | 0.83468 | |
| **F1 F2 (#2368)** | **18584** | 0.83297 | **1636** |
| F1 F2 E (#2387) | 18584 | 0.83472 | 1657 |
| F1 F2 N | 18608 | 0.83461 | |
| F1 N E | 18632 | 0.83668 | |
| F2 N E | 18600 | 0.8361 | |
| F1 F2 N E | 18608 | 0.83636 | |

Only F1 F2 and F1 F2 E reach 18584. By the lane metric (fewer slots_diff at equal size)
F1 F2 wins (1636 vs 1657), so the branch carries #2403 + #2368 (no E). Both give 1032/347.

Mechanism: #2403's `&Context` parameter lets ArgPromotion pass the accounts pointer without
`noalias` (+56 B: a's fields reload after calls like the original); #2368's
`require_gt!(base,0,BuyZeroAmount)` and `match &post_fill` for the post-complete base out
remove 16 B. The two touch disjoint hunks of
multi_hop_curve_swap.rs and their size effects add to exactly the original 18584 B.
With swap_hop at original size the address shift after it disappears: +10 raw.

elf_meta_diff on the combination: `.text` -56 (admin_cto only), every non-.text difference
follows from .text, no build-input differences.

Ledger: cf07fac9359143518e45cf9e5a527702, 9c3174d4844c4a54ad253202716f279a.

## Round 2 (main 7ca3235dc, fresh build 1032/337, sha 56143aaa)

Main merged #2214 (admin_cto `let swept; ... else{swept=0;}`), which moves admin_cto from
27344 B to 27240 B (orig 27400; ratio 0.37637 -> 0.3765). #2403's head (8073709c6) reached
swap_hop 18584 B, slots_diff 1023, ratio 0.85352 on its own, superseding this lane's
#2403+#2368 (1636 slots); the hill-climb of the w7r1-swaphop-hillclimb mutation catalog on
that base (~105 single mutations) found nothing better at 18584 B and was stopped.

| combination on 7ca3235dc | admin_cto | swap_hop | norm/raw | .text |
| --- | --- | --- | --- | --- |
| main | 27240, 0.3765 | 18544, 0.7332 | 1032/337 | -200 |
| #2403 | 27240, 0.3765 | 18584, 0.85352, 1023 slots | 1032/347 | -160 |
| #2403 + #2416 | 27128, 0.39103 | 18584, 0.85352 | 1032/347 | -272 |
| **#2403 + revert #2214** | **27344**, 0.37637 | 18584, 0.85352, 1023 slots | **1032/347** | **-56** |

The branch carries #2403's multi_hop_curve_swap.rs and reverts #2214's one-line hunk
(line count unchanged). elf_meta_diff: .text -56, every other difference follows from .text,
no build-input differences. unstripped sha256 3ca6911a64bdfb6251603f60d69ae6c8919af03d801b82b72fcc3e0dd6c8ec4d.
Ledger 0e0ffcb44d4c4ff19327d84acc31d5f2, 7230782a35e940078c6b52c1de92a5ea.

## Round 3 (main c2f54a62b, no programs/pump/src change since 7ca3235dc)

#2403 head 5e9a02804 adds the post_fill reserves-if tuple: swap_hop 0.89006 but 18520 B
(-64). Removing single v2 hunks from it (rN, rE, rF1, rU, rC, rK) and the size-balancing
pairs: only variants with rC (`?` back on buy_fee_market_cap) reach 18584 B, at 1282..1631
slots (rC alone 0.87713/1282). None beats #2403 v2 (8073709c6: 18584 B, 1023 slots), so the
branch keeps v2 by the size-first, slots-second metric. The v3 ratio gain is real; it needs
+64 B elsewhere to be adoptable.
