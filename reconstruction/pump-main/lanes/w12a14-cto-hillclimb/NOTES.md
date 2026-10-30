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

(filled in as the climb runs)
