# Lane w12b11-cto-fresh (wave 12, pool b): fresh-eyes rewrite of `admin_cto::execute` (0x22a10)

Angle: write `execute` from scratch in the idiom of the byte-matched siblings (pump-amm
`admin_cto_pool.rs`, `create_v2::execute`, pump-fees `admin_cto_sharing_config`), keep the
semantics, place every `line!()` site on its original line, then compare against main by whole
ratio, by segab, and region by region.

Result: no rewrite beats main. Main is structurally much closer to the original than any of these
clean-room versions. With registers and frame offsets masked, main's per-call-chunk similarity is
0.8744 (b5975fa). The fresh versions score 0.79 to 0.81. The rewrites did produce two mechanisms
and a placement-independent oracle that separates structure from regalloc/frame noise. All of it is
below.

## Trials (measure.sh, all 0 normalized losses; raw losses are size-only)

| trial | base | bytes | ratio | chunk-struct | notes |
| --- | --- | ---: | ---: | ---: | --- |
| main 20a1ae9 | | 27,400 | 0.43919 | 0.8635 | |
| main b5975fa | | 27,400 | 0.45147 | 0.8744 | |
| f1: full rewrite, every `require!` an early exit from `execute` | 20a1ae9 | 10,688 | 0.11953 | n/a | **helpers not inlined**: the wallet (4,184 B) and sweep (9,008 B) helpers are emitted on their own, 86 calls |
| f2: main head through line 410, fresh sibling tail | 20a1ae9 | 27,408 | 0.21537 | 0.8077 | post-sweep code laid out after the native/wallet tail |
| f3: full rewrite, `impl AdminCto { fn validate(&self, ..) -> Result<Pubkey> }` | 20a1ae9 | 26,840 | 0.15496 | 0.7871 | **to_string inline/outline set and lddw count (86) equal the original** |
| ta_unwrap_or: `validate -> Result<()>`, then `target=new.unwrap_or(holder_key)` | b5975fa | 26,952 | 0.14199 | 0.8135 | frame collapses (16/388 offsets equal) |
| ta_ifexpr: same, with `if holder{holder_key}else{new.unwrap_or_default()}` | b5975fa | 26,944 | 0.14836 | | same collapse |

The templates are kept in `fresh/`. They are padded with `tools/pad.py`, which puts each
`//@NNN` marker line on line NNN:

- `fresh/f1_separate_exits.tmpl`
- `fresh/f3_validate_method.tmpl`

## Mechanism 1: the original validation has to merge before the helper calls (f1)

If validation is a run of direct `require!` exits in `execute`, as in the AMM sibling, LLVM no
longer inlines the wallet and sweep helpers.

- The static BPI halves the block frequency at each exit. After about 11 exits, the helper call
  sites fall below `ColdCallSiteRelFreq` (2 % of entry).
- `InlineCostCallAnalyzer` then drops every bonus, including the 15,000 last-call-to-static bonus,
  and caps the threshold at 45.
- So both helpers stay out of line.

The original inlines both helpers (154+3 calls, one 27,400 B function). Its validation must
therefore reach the helper calls through a single merge: a `Result`-returning helper, method or
closure, with one `?` at the call site. Main's `validate(&st, ..)?` and f3's
`self.validate(..)?` both restore 154+3.

Corollary: the 2 % rule also decides which `to_string` calls stay inline inside `validate`. See
w12a06's pre-inliner BFI note. Any validate change that adds or removes a branch ahead of a site
can flip that site's `to_string` between inlined and outlined.

## Mechanism 2: a sibling-style validate reproduces the original `to_string` set (f3)

f3's validate reads the accounts through `&self` and uses these forms:

- the 296 check inside the holder arm (`create_v2` idiom): `if !bc.is_holder_reward { require!(global.is_holder_reward_enabled, ..) }`;
- `let Some(t)=new else { return err!(..) }` at 306;
- `require_keys_neq!` at 307;
- `require!(t != hk && t != sk)` at 312;
- `require!` for the fee block.

With these, the inlined/outlined `to_string` choice equals the original at all 12 validation
sites. 289, 298, 306, 296, 326 and 410 stay inline; 312, 307, 330, 338 and 334 are outlined. lddw
is 86 = original (main: 88, with 312/307 inline).

This is the same effect as the #2370 296-in-holder-arm gene that w12a06 is porting. The rewrite
arrived at it independently, as the natural sibling idiom. It costs size: f3's validation region is
shorter, and the frame moves.

## Oracle: placement-independent, register- and frame-abstracted chunk similarity

Main's call order now equals the original after the validation block. So whole-function difflib
on frame-masked text (segab) mixes three effects: layout moves, register allocation and frame
offsets. `tools/chunks2.py` separates them.

- It cuts both listings at every call, and labels each chunk with its call target and occurrence
  number.
- It pairs each original chunk with the candidate chunk that has the same label.
- It scores the pair with difflib, after masking frame offsets, lddw payloads, jump offsets and
  register names.

What is left is structure only, independent of where the chunk was placed. Per-chunk and weighted
results:

```
python3 tools/annot.py <listing.txt> <unstripped.so> > x_annot.txt   # call names from the candidate symtab
python3 tools/chunks2.py orig_annot.txt main_annot.txt cand_annot.txt   # '<<' cand better, '>>' main better
python3 tools/cdiff2.py orig_annot.txt cand_annot.txt '<call label>' <occurrence>   # structural diff of one chunk
python3 tools/framedelta.py orig_annot.txt cand_annot.txt   # orig r10 offset -> cand offset deltas, run by run
```

Listings: `win.py orig 0x22a10` for the original. For a candidate,
`lanes/w3-adminCTO/scripts/cand.py <so> admin_cto7execute`.

Findings on main b5975fa:

- Weighted structure is 0.8744. Most of what is left sits in the validation block: error-block
  order (306 is the third From in the original, 330 in ours) and the inlined `to_string` at
  312/307.
- The two big CPI chunks are close in structure:
  - sharing CPI, 455 insns: 0.86;
  - `transfer_creator_fees_to_pump_v2`, 658 insns: 0.96.
- Their remaining differences are spill/reload placement and one 34-instruction Rc-clone block
  (the `mint` clone, `[accounts+0x10]`) that the original emits after reloading the accounts
  pointer from `[r10-0x8d8]`. Ours keeps that pointer in a register.
  - So those chunks are regalloc-limited, not source-order-limited.
  - The `to_account_info()` order is identical (checked with a per-chunk account-offset sequence).
- Frame (framedelta on b5975fa): 162 of 398 r10 offsets already map with delta 0.
  - The spill area starts at orig 0x8d8 vs ours 0x8c0: the accounts-pointer spill sits 24 B
    shallower in ours. That is the same 24 B as the w12b12 emit_cpi!/target-piece finding.
  - Below it, spill slots are permuted, not shifted: deltas of -0x48..+0x20 with no single run.
- The fresh rewrites move the frame almost completely: 16 to 30 offsets with delta 0. Clean-room
  structure is not a route to the frame.

## Rejected mechanisms (ledger keys under lane w12b11-cto-fresh)

- `0x22a10-w12-e61df03-fresh-sibling-rewrite-separate-exits-v1` (f1)
- `0x22a10-w12-e61df03-fresh-tail-on-main-head-v1` (f2):
  - `swept=if shared&&holder{sweep()?}else{0}` re-places the post-sweep code;
  - an event built from locals is worse than re-reading the curve (0.67 vs 0.97 chunk structure).
- `0x22a10-w12-e61df03-fresh-validate-method-full-rewrite-v1` (f3)
- `0x22a10-w12-b5975fa-fresh-validate-unit-target-unwrap-or-v1`
- `0x22a10-w12-b5975fa-fresh-validate-unit-target-ifexpr-v1`
