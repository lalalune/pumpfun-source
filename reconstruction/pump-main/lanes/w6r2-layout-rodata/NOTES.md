# Lane w6r2-layout-rodata (wave 6, round 2): rodata / data layout for raw

Base: origin/main a7135a6a6, rebased onto 2162b3b00 (both 1027/1035 normalized, 276 raw).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w6r2-layout-rodata/`. Lane tools are in `tools/`:

| tool | what it does |
| --- | --- |
| `trial.sh NAME [src]` | fastbuild + score + the w3-raw-layout data metrics (`BASEJ=` picks the baseline score.json) |
| `dataoff.py so` | for every normalized window: does some matching symbol have every `.rodata`/`.data.rel.ro` lddw at the original in-section offset? (resolves duplicate string copies per symbol) |
| `shiftraw.py so` | raw count if only the data-section bases moved to the original addresses, i.e. `.text` total size equal and everything else as built |
| `failclass.py so` | splits the remaining non-raw windows of that model into call-displacement / text-pointer lddw / other |
| `refs.py so lo hi [sec]` | who references a `.rodata` offset range, in the original and in a candidate |
| `capture.py`, `mirdump.sh` | experiment-only pre-opt IR (`-C no-prepopulate-passes`) and PreCodegen MIR (`-Zdump-mir`) capture. Never used for proposals |
| `rpo.py file.mir pat...` | rustc's MIR reverse postorder (Postorder visits successors with `next_back`) and the RPO index of the blocks that contain each pattern |
| `lines.py so sym` | Source line immediates in a candidate function, by offset |

## Result: `.rodata` is byte-identical to the original

| metric | main 2162b3b | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276 (0 losses, 0 raw losses) |
| `.rodata` aligned bytes (of 32031) | 31993 | **32031 (section byte-identical)** |
| path-string order/offset mismatches (of 33) | 1 | **0** |
| normalized windows with every data lddw at the original offset | 1027/1027 | 1027/1027 |
| `.data.rel.ro` vs main | | identical |
| `.text` vs main | | 17 bytes differ, all lddw operands in admin_cto::execute |
| admin_cto::execute (0x22a10) | 0.37637 / 27344 B | 0.37637 / 27344 B |
| unstripped sha256 | fd54954f04c05e29... | ec660de760c3feb4... |

Also checked on top of PR #2168 (w6r1-layout-order merged into 2162b3b): 0 losses, `.rodata` byte-identical.

### Mechanism (attempt `7e25255a`)

The only `.rodata` difference left was the `programs/pump/src/creator/admin_cto.rs` path being created after
the `No canonical pump pool for this mint; curve only` msg! literal (line 766). Both are first created while
admin_cto code is codegened. rustc creates constants as it codegens: mono items in DefIndex order, and inside a
function, MIR blocks in reverse postorder.

The PreCodegen MIR dump plus `rpo.py` gives the cause (attempt `29916500`). `execute` has 120 blocks. The msg is in bb49
at RPO 61. The only Source site inside `execute`'s own MIR is line 410. `require!(creator_fee==0)` becomes
`switchInt(creator_fee) -> [0: continue, otherwise: err]` (SimplifyComparisonIntegral). Postorder visits
successors back to front, so the error block is visited first and lands last in RPO (112). The other Source
sites are in the nested fns `validate`, `wallet` and `sweep`. Each is its own mono item. Their DefIndex
follows `execute`'s, so they are codegened after it. The IR define order is create_v2::execute,
create_event, init_curve, admin_cto::execute, validate, wallet, sweep, token_frozen, token_raw_amount.

Two probes confirm the model:
- `bd8860c2` (diagnostic only): with `require!(creator_fee<1)` the bool switch stays, require!'s swapped `if !c`
  puts the error block first, and `.rodata` becomes byte-identical. But this changes admin_cto's text
  (0.37637 -> 0.35977): the earlier codegen of the error block reorders LLVM blocks.
- `7e25255a` (kept): `validate` becomes a module-level fn defined before `execute`. `execute`'s header and its first
  statement line move from lines 100/101 to line 339, right after `validate` closes. Every Source line is
  unchanged, and the `layout-pad` comment moves to line 101 with count 183. `validate` now has the lower
  DefIndex, so it is codegened first and creates the path literal before `execute` creates the msg literal. This
  matches the original `.rodata`. LLVM still inlines `validate`, so `.text` is unchanged apart from the moved
  literal addresses.

This also tells admin_cto lanes something: the original's validation code was not nested inside `execute` after
its first statements. A module-level `validate` before `execute` reproduces the original constant order.
Keep that form, or another form that codegens an admin_cto.rs Source site before the line-766 msg block.

## Census of data references (attempt `b41d91fc`)

- All 1027 normalized windows already reference the original's data offsets (601 have data lddw). This was
  checked independently of w3's `datamis.py`, choosing per symbol among identical twins (e.g. the two copies of the
  ProgramError/PubkeyError variant-name strings at `.rodata` 0x74f and 0x4a92 are referenced by the
  root-crate local copy 0x10d80 and the upstream copy 0x19aa88 respectively, in both binaries).
- Official raw is blocked only by `.text` size: main is +0x238 B (unmatched windows +56, plus the 512-B
  `v2_native_payments::ensure_rent_exempt` wrapper that PR #2168 removes). If only the data bases moved
  (`shiftraw.py`), raw would be 405 on main and 407 on #2168, against 276/277 today. In that model, the rest of the
  non-raw windows on #2168 are call-displacement only (557), calls plus text-pointer lddw (44) and text-pointer lddw
  only (19, function pointers). All of these depend on function placement, and none on data layout.
- Unmatched-window size deltas on main a7135a6 (cand - orig): sweep +48, buy_handler +32, buy_exact_quote_in
  +32, v3_buy_costs +16, buy_exact_quote +16, create_v2 0, swap_hop -40, admin_cto -56.

## Attempts

| id | trial | result |
| --- | --- | --- |
| - | t00: main a7135a6 repro | 1027/276, sha 31ec6381 = verify-r1 base |
| `44545178` | t01: line 410 `require!` -> `if creator_fee!=0{return err!(..)}` | byte-identical, rejected |
| `48e7cf01` | t02: `#[inline(always)]` on nested validate | not MIR-inlined (call stays); rodata order unchanged; admin_cto 27168 B 0.37756; rejected |
| `29916500` | MIR RPO model of execute | msg RPO 61, Source 410 RPO 112; nested fns codegened after execute |
| `bd8860c2` | t03: `require!(creator_fee<1)` | `.rodata` identical but admin_cto 0.35977; diagnostic |
| `b41d91fc` | data-offset census + rebase model | 1027/1027 data-offset equal; raw-if-size-equal 405/407 |
| `7e25255a` | t04/t05: validate module-level before execute | **kept**: `.rodata` identical, 0 losses, admin_cto unchanged |
| - | t07: rebased on 2162b3b | same result, 0 losses vs fresh main build |
