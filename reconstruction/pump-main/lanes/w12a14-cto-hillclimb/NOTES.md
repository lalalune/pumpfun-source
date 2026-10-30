# Lane w12a14-cto-hillclimb (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: large-scale automated source hill-climb. Base: main 20a1ae9c0 (admin_cto 0.43919 / 3,352 slots at
27,400 B), then the k4 composite of w9r2-admincto-harvest as landed by w12a04-cto-k4size (#2749:
k4 + `bump` before `old` + `match sharing_update`, 0.45147 at 27,400 B).

## Tooling (text copies in this directory; working copies and results in `~/.cache/.../lanes/w12a14-cto-hillclimb/hc`)

- `hc12.py`: gene engine and build driver. A variant is the base text plus an ordered list of gene ids;
  each gene is a list of exact `(old, new)` substitutions with equal newline counts, so every
  `error!`/`require!` site keeps its `line!()` immediate. Variants build through `measure.sh` (identity
  recipe, the shared 10-slot lock, `score.py` against the landed baseline) with at most two builds at once.
  `hc12.py daemon genes12.py queue.txt` pops variants from a queue file that can be re-ordered while it runs.
  Every variant goes to the shared ledger (approach `mutation-hillclimb`, key `0x22a10-w12-20a1ae9-hc-<variant sha12>-v1`).
- `genes12.py`: about 150 genes over the current text: statement reorders, binding scopes, `?` vs `match`,
  borrow vs copy, `if let` vs `match`, combined vs split checks, the k4 components, the residual-catalog
  ideas (sweep gate as a phi of constants coalesced with `collect_old`; `match` None-first), and the
  state-tuple element order (MIR local order, hence alloca order).
- `framemap.py <unstripped.so> [--summary]`: frame slot map. It aligns the original and candidate
  `admin_cto::execute` with every r10 displacement (and `mov rX,r10; add rX,imm` lea immediates) masked,
  then pairs the r10 offsets of matched instructions. It prints `orig T -> ours T (count)` and the delta,
  so a delta run shows how many bytes of frame objects one side has more in front of a group of slots.
  `--summary` gives `r10_equal` (pairs with equal offsets) and `first_div_T` (first diverging slot); the
  hill-climb records both for every variant.

## Frame map of main 20a1ae9c0 (framemap.py, delta = orig T - ours T)

| orig T range | delta | accesses | reading |
| --- | ---: | ---: | --- |
| 0x001..0x470 | 0 | 617 | equal: the whole top of the frame already matches |
| 0x478..0x480 | -24 | 6 | one slot sits 24 B higher in ours |
| 0x484..0x530 | +16 | 87 | ours has 16 B more in front of this group |
| 0x538..0x580 | mixed | | orig-only slots: the 7 B and 9 B SROA pieces of `Some(new)` (sharing_update) and a 32 B `target` copy (8 B spill + 24 B tail) |
| 0x598..0x651 | -64 | 23 | ours lacks those ~64 B |
| 0x688..0x6e0 | -32 | 16 | |
| 0x750..0x890 | -16 | 18 | |
| 0x8d8..0x9e0 | mixed | | register-allocator spills (r10-0x928 arg spill vs ours 0x8f0) |
| 0xa20..0xc38 | -24..-40 | 60 | |

So the frame of main is equal down to T=0x470 and first diverges at T=0x478. In the original,
`sharing_update`'s `Some(new)` pieces are copied (when `shared`) from the entry copies of `new`
(T 0x650/0x658 and 0x660/0x668, or T 0x450/0x2d0) into T 0x538 (7 B) and T 0x548 (9 B), and copied
again to T 0x550/0x560 next to a 32 B `target` built from a spilled u64 (T 0x918) plus 24 B (T 0x520..0x530)
at T 0x568..0x580. Ours keeps the same pieces at T 0x480 and 0x4f8 and has no 32 B target copy there.

## Results

### Candidate (branch `swarm/w12a14-cto-hillclimb-2`)

| metric | main 4f24fbc32 (#2792, K5') | this branch | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | **27,400** | 27,400 |
| admin_cto ratio | 0.45177 | **0.48652** | 1 |
| admin_cto slots_diff | 3,308 | **3,278** | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 | 1035 |
| losses (norm / raw) | | 0 / 0 | |
| runtime differential | | 363/363 cases match | |

Variant `d7acbb3d549a` = main 20a1ae9c0 + genes `region2_tree, wallet_flags, fee_unwrap, canedit_first,
old_fee_first, su_iflet_match, amm_cb_local, k4_oldfee_after, v326_match, a2_orig_order, ev_flags_local`
(no `bump_before_old`). Against main K5' the source change is:

- validate (w12a11-cto-sibling `amm_cb_local`, the pump-amm `admin_cto_pool` idiom): on layout-pad line 314
  `let cashback=if holder{false}else{st.cashback};`, and the 330 check tests `cashback`. MIR JumpThreading then
  splits the fee checks per holder arm (0.45147 -> 0.48367 at 27,384 B on #2749).
- validate 326: `match fee{Some(f)=>{..}None=>{}}` instead of `if let` (+0.0012, size-neutral).
- curve store in the original's order (sizeknobs notes): creator, is_cashback_coin, is_holder_reward, the
  `old_fee` read after those stores (w12a11 `k4_oldfee_after`), a branchy `if let Some(f)=fee` store, and
  `can_edit_creator_fee=false` last (+0.0004, -8 B).
- event `is_holder_reward:holder, is_cashback_coin:cashback` from locals (`ev_flags_local`, +24 B) with the
  sweep seeds back in main #2642's `old` before `bump` order (-8 B): together they land the composite on
  exactly 27,400 B.

### Measured hill-climb steps (identity recipe, measure.sh; bytes / ratio)

| base | + gene | result | note |
| --- | --- | --- | --- |
| K5' (main #2792) | `r2_holder_flip`, `tup_target_first`, `su_none_first` | 27,400 / 0.45177 | byte-identical (no-ops) |
| K5' | `r2_sweep3` (sweep gate as a phi of constants in the region2 tree) | 27,392 / 0.36794 | frame equal 683 -> 550 |
| K5' - fee_unwrap (B1, 27,392 / 0.45213) | `fee_iflet_match`, `fee_iflet_none_first` | 27,392 / 0.45154 | |
| A = #2749 + amm_cb_local (27,384 / 0.48367, w12a11 t18) | `k4_oldfee_after` | 27,392 / 0.48449 | w12a11 t23 |
| A2 = A + k4_oldfee_after | `v326_match` | 27,392 / **0.48569** | |
| A2 | `w_collect_match` | 27,384 / 0.47887 | |
| A2 | `a2_cb_first` (cashback stored before holder) | 27,392 / 0.48449 | no-op |
| A3 = A2 + v326_match | `a2_orig_order` | 27,384 / **0.48607** | |
| A3 - region2_tree | `ev_flags_local` | 27,392 / 0.4836 | |
| A4 = A3 + a2_orig_order, minus `bump_before_old` | `ev_flags_local` | **27,400 / 0.48652** | this PR |

Every variant is a ledger row (approach `mutation-hillclimb`, key `0x22a10-w12-20a1ae9-hc-<sha12>-v1`).

## Review on the current nested-seed baseline

The current main source includes #2808's nested pool-authority signer seeds.
Keeping that change with this candidate gives **27,400 bytes, ratio 0.48742,
3,273 differing slots**, with 154 internal calls and 3 syscalls. The fresh
identity build preserves all **1,034/1,035 normalized and raw matches**, with
zero missing, resized or lost windows. This remains a partial admin-window
improvement; it adds no complete matched window.

The selected source digest is
`4b5048e59f11c029ba17f6bad4cc8f3eea784e212105a3cce272826521193428`;
the unstripped ELF digest is
`481ba72865f36b52b3cc27e824ef3762a0baff5509c48135aa627fb927418c2b`.
The candidate passes 363 signed synthetic admin-CTO differential cases against
the captured original. These fixtures are bounded runtime evidence, not a
whole-program equivalence proof. All 20 error/require/message macro sites keep
their previous source line numbers.
