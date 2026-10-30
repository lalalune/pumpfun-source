# Lane w12a02-cto-iroracle: llc IR oracle for 0x22a10 `admin_cto::execute`

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 20a1ae9c0 (baseline unstripped sha 8cd7695c…): admin_cto 0.43919, slots_diff 3,352.
Angle: capture main's post-opt IR, prove `llc` reproduces our admin_cto exactly, then edit the IR
(frame/alloca order, lifetimes, branch weights, block order, phi order) and rank which differences
from the original are worth the most. Everything here is an experiment on IR; nothing in this
directory is a source proposal.

## Oracle (scripts/, ~1-5 s per run, no build slot)

| script | what it does |
| --- | --- |
| `capture.py <crate> <work> <out>` | identity build (slot-locked, like `measure.sh`) that also writes `out/pump_recovered.ll`. Stripped candidate sha equals the normal build (4eb9dc9e…). |
| `trim.py in.ll out.ll` then `trim2.py out.ll small.ll` | every function but execute (and alias targets) becomes a declaration; unreferenced declarations, globals and metadata are dropped. 42 MB -> 3 MB, llc ~0.5 s CPU. |
| `ctoracle.py run <mod.ll> <dir> [--edit e.py]` | llc exactly like fastbuild (`-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext`) and score execute with **target_metric's own tokens**: relocated lddw masked, a call to a `sol_*`/`abort` symbol becomes `call -1` (src 1, imm -1 kept), every other call the masked internal form. Prints ratio, abs_ratio (segab-style: r10 offsets, frame add64 immediates and jump offsets masked), bytes and slots_diff. |
| `ctoracle.py so <unstripped.so>` / `cmp <so> <obj>` | the same metric from a linked build / token-equality check. |
| `iredit.py run <mod> <dir> SPEC` | composable IR edits, SPEC = comma list of `bw:BLOCK:T:F` (branch weights), `inv:BLOCK`, `mv:A:B` (alloca A before alloca B or END), `nolt:A` (drop lifetime markers), `sz:A:N`, `blk:A:B` (IR block order), `swapphi:BLOCK`. `scan` runs base+item for a list. `PF=1` also reports `pf_ratio`. |
| `greedy.py <mod> <dir> BASE items N` | greedy forward selection (logs individual and cumulative gain per round). |
| `regionmap.py <fn.bin or so> [seg]` | per original segment: matched % plain and with a perfect frame, unmatched tokens, and landmarks (original call targets resolved through the baseline window symbols, error-line immediates). |
| `pfboard.py <so>...` | rank builds by perfect-frame ratio (code closeness with the frame factored out). |
| `framebound.py <fn.bin or so>` | **perfect-frame ratio**: aligns with r10 offsets abstracted, votes ours-offset -> orig-offset, remaps every frame offset and re-scores exactly. The gap to `ratio` is what a perfect stack frame is worth on that code. |

Validation on main 20a1ae9c0: `ctoracle.py cmp` -> **tokens equal** (3,337 insns) for both the full
module and the trimmed 3 MB module; ratio 0.43919, abs 0.64679, slots_diff 3,352 = `measure.sh`.

## Decomposition of the remaining gap (main 20a1ae9c0)

| measure | value |
| --- | ---: |
| ratio (target_metric) | 0.43919 |
| perfect-frame ratio (same code, every r10 offset remapped to the original's) | **0.5719** |
| abs_ratio (frame offsets and jump offsets masked) | 0.64679 |

So about 0.133 of the gap is the stack frame alone; jump offsets (block layout) are worth up to
~0.075 more; the rest (~0.35) is instruction selection, register allocation and scheduling.

## Ranked features (v1)

Individual gains are on main's IR; cumulative is the greedy composite.

| # | feature (IR edit) | ratio alone | gain | notes |
| --- | --- | ---: | ---: | --- |
| F1 | `mv:_117.i74:holder_key`: the wallet `emit_cpi!` signer slice (`&[&[u8]]`, 16 B, `.i74` = inlined wallet) placed in a slot just above holder_key | 0.48892 | **+0.0497** | slots_diff 3,350. Fixes the -16 B at orig 0x488..0x540. Same number as w12a01-cto-frame's remap estimate. In the original that slot is a 24 B slot (T 0x680) that also hosts the final emit_cpi slice and the 24 B Pubkey-tail copy made at 0x243b8. |
| F2 | branch weights alone on main (best of 286 single 1:2000 / 2000:1 edits) | 0.47357 (`bw:bb19.i:1:2000`, 27,408 B) | +0.034 | **does not stack with F1**: on top of F1 every single branch weight gives <= +0.005 (`bw:bb7:2000:1` 0.49395 at 27,504 B). The bb19.i gain on main is a frame side effect (ISel order of the 16 B call-return slots), not layout. |
| F3 | F1 + `nolt` of one 24 B wallet/validate buffer (`buf.i18.i`, `buf.i25.i`, `buf.i32.i`, `_49.i`, `_63.i`) | 0.49491 | +0.006 over F1 | partly fills the +80 B the original has between val.sroa.6.i (T 0x530) and `_184` (T 0x598). |
| F4 | F1 + validate's `target.i.sroa.0/9` without lifetimes + execute's `target.sroa.0/8` and `sharing_update2.sroa.3` moved after them | 0.32325 | (negative) | the frame from val.sroa.6.i (0x530) through old_creator (0x630) then matches the original **exactly** (0x538/0x548/0x550/0x560/0x580/0x598/.../0x630), but the 1 B `_124.i` loses its merge partner and the 0 B `_11.i296` merges, so the whole top of the frame moves by 8 B. A source fix must keep those two as they are. |

| F5 | branch weights judged by the **perfect-frame ratio** (`PF=1`), on top of F1: best of 286 | pf 0.5749 vs 0.5719 | +0.003 | the Rc `inc_strong` overflow checks of the AccountInfo clones; median single weight -0.008. Once the frame is factored out, block-placement probabilities are not where the gap is. |
| S1 | **source**: the CtoState/validate/sharing_update/collect_old block as a nested `fn state(..)->Result<(bool,bool,Pubkey,Option<Option<Pubkey>>,bool)>` (LLVM-inlined) | 0.37845 at 27,896 B | (negative) | frame: validate's target pieces (`target.i.sroa.0/9.i`), state's target pieces (`target.sroa.0/8.i`) and execute's `target` (32 B, no lifetime) land in **exactly the original's pair A / pair B / E32 order right after val.sroa.6.i**, and `_124.i` merges into `target.i.sroa.9.i` (which F4 lacked). Only the -16 of `_117` and an extra 12 B `sharing_update.sroa.5` piece are off. The Result<tuple> plumbing costs +496 B and the perfect-frame ratio drops to 0.5337, so this spelling is evidence for where those allocas come from, not a candidate. |

## Refresh on main b5975fa67 (#2749 k4size landed: 0.45147 / 3,308 slots)

Oracle re-captured and re-validated: `ctoracle.py cmp` -> tokens equal; ratio 0.45147, abs 0.66597.
The wallet emit_cpi slice is now `%_114.i` (fi41, still its own 16 B slot at T 0x480).

Ranked features on b5975fa67's IR (`greedy.py`, every step kept at 27,400 B):

| # | IR edit | ratio | gain | pf_ratio |
| --- | --- | ---: | ---: | ---: |
| 0 | main | 0.45147 | | 0.58119 |
| 1 | F1 `mv:_114.i:_183` (wallet emit_cpi slice out of the inlined region; any position after val.sroa.6.i gives the same) | 0.49670 | +0.04523 | 0.58209 |
| 2 | + `nolt:buf.i32.i` (any one 24 B validate/wallet buffer kept unmerged: buf.i18.i, buf.i32.i, _63.i, _49.i, _40.i, _30.i, _20.i all tie) | 0.50899 | +0.01229 | 0.58238 |
| 3 | + `mv:val6:_183` (sharing-config CPI `val` copy, 33 B, moved below old_creator) | 0.51618 | +0.00719 | |
| 4 | + `mv:sharing_update.sroa.3:st` | 0.51648 | +0.0003 | |
| C1 | code: `inv:bb11.i` (validate's holder test in the `!st.holder_reward` arm with swapped successors: error 289 now precedes 298 as in the original) | 0.45327 alone, 0.4967 with F1 | +0.0018 alone | **0.59257 (+0.0114)** |
| C2 | code: best single branch weight on F1 (pf objective) | | | +0.003 at most |

Rows 1-4 are frame-only (they cannot change pf beyond noise); C1 is the largest code-level (pf)
feature found by single edits: error order after C1 is 289, 298, 330, 296, 306, 326, 312, 307
(original 289, 298, 306, 296, 326, 312, 307, 330). Without the size constraint the greedy also
takes `nolt:_42` (+0.0156 but 27,368 B): 0.52068 after 4 edits.

The last row shows how chaotic StackColoring is: shortening one range re-pairs half the 24 B
groups instead of letting `_114.i` move. A source fix has to keep `_11.i294` (the 0 B to_string
alloca at T 0x1) unmerged as well: every edit that lets it merge shifts the whole frame top by 8 B
(that is what sank F4 and the forced-H24 variants: 0.268).

### The features stack on the leading candidate family (sibling t23)

w12a11-cto-sibling t23 (amm_cb_local + k4_oldfee_after, 0.48449 at 27,392 B) captured and
re-scored with llc: tokens reproduce its build. Its frame has the same defect (`_114.i` alone at
fi41, T 0x480), so the frame features apply unchanged:

| edit on t23's IR | ratio | pf_ratio |
| --- | ---: | ---: |
| t23 | 0.48449 | 0.59566 |
| F1 `mv:_114.i:_183` | 0.51026 (+0.026) | 0.59655 |
| F1 + `nolt:buf.i40.i` + `mv:val6:_183` | **0.52614 (+0.042)** | 0.59685 |
| + C1 `inv:bb11.i` | 0.52718 at 27,408 B | 0.60087 |

### Code-level greedy (pf objective, on F1 + C1, 27,400 B)

| round | edit | pf_ratio | ratio |
| --- | --- | ---: | ---: |
| 0 | F1 + C1 | 0.59257 | 0.49670 |
| 1 | `bw:bb1.i:2000:1` (284 mayhem error's to_string unwrap test made "hot") | **0.61174** (+0.019) | 0.50419 |
| runners-up | `bw:bb34.i`/`bw:bb35.i` 2000:1 (the 312 `t==holder_key` / `t==sharing` memcmp tests) | 0.60015 | |

These are block-frequency effects inside validate (they move spill weights and the error blocks'
placement), the same mechanism w12a08-cto-errorder documents: one hypothesis is that original holder/new tests compile as
`trunc` tests with the 50/50 BPI heuristic, while this candidate receives the zero heuristic. Single branch
weights elsewhere are worth <= +0.003.

### Where the unmatched mass is (scripts/regionmap.py, 256-instruction original segments)

`pf` = matched after remapping every frame offset to the original's; `pf-miss` = original tokens
still unmatched with a perfect frame, i.e. the code (not frame) gap per region.

| orig offset | plain | pf | pf-miss | landmarks (original call targets / error lines) |
| --- | ---: | ---: | ---: | --- |
| 0x0 | 44% | 50% | 126 | holder_key PDA, shared test, quote lock, CtoState |
| 0x850 | 19% | 41% | 149 | validate errors 289, 298, 306, 296 (inlined `fmt`) |
| 0x10b8 | 19% | 26% | **187** | validate errors 326, 312, 307 (outlined `to_string` in the original) |
| 0x1938 | 56% | 67% | 82 | prepare_bonding_curve, 410, wallet start |
| 0x2198 | 62% | 73% | 69 | sweep 719, 648 |
| 0x29e8 | 46% | 60% | 100 | sweep body |
| 0x31e8 | 8% | 62% | 95 | sweep body (frame-only mismatch: 8% -> 62%) |
| 0x39e8 | 44% | 54% | 116 | transfer_creator_fees_to_pump_v2 CPI |
| 0x41f0 | 34% | 24% | **193** | AccountInfo clone runs (CPI account lists) |
| 0x49f0 | 59% | 73% | 67 | sharing-config CPI, pool CPI |
| 0x5210 | 72% | 82% | 45 | final emit_cpi |
| 0x5a80 | 57% | 64% | 91 | native sweep path |
| 0x6288 | 59% | 69% | 77 | wallet collect emit_cpi |

The validate error chain (0x850..0x1938, ~420 tokens) and the CPI AccountInfo clone runs
(0x41f0, 193) hold the largest code-level (non-frame) mass.

### Heuristic frame-remap leaderboard of the swarm's builds (scripts/pfboard.py, refreshed 06:20 local)

`pf` is the heuristic frame-remap score (see the review boundary below): a build whose frame is still
off but whose remaining code aligns better scores higher here even when its plain ratio does not.
It is a ranking aid for choosing experiments, not a measurement of an emitted build.

| pf | ratio | bytes | build |
| ---: | ---: | ---: | --- |
| **0.60877** | 0.48510 | 27,424 | w12a07-cto-sweepthread t/cb_skip_vsig |
| 0.59946 | 0.48562 | 27,400 | w12a04-cto-k4size t/M3.p_seeds_nested |
| 0.59876 | 0.40863 | 26,992 | w12a10-cto-optoracle t/v2 |
| 0.59835 | 0.43631 | 27,312 | w12a08-cto-errorder t/k02 (= w12b10-cto-handler t/n6_keys_byval) |
| 0.59676 | 0.48562 | 27,400 | w12a04-cto-k4size t/Z.evfl_sue_fur |
| 0.59655 | 0.48569 | 27,392 | w12a11-cto-sibling t/t32 |
| 0.59527 | **0.48652** | 27,400 | w12b13-cto-callgraph t/d1 (best plain ratio at the pinned size) |
| 0.58149 | 0.45177 | 27,400 | main 70f27048e (k4size-2) |
| 0.58119 | 0.45147 | 27,400 | main b5975fa67 |
| 0.54852 | 0.43538 | 27,152 | w12a06-cto-relocs t/w1 (original lddw/to_string set, but code further away) |

### Probabilities and the register-allocation residual

- Emulating the original's BPI in IR (1:1 weights on validate's holder tests bb6.i/bb11.i, new-tag
  tests bb19.i/bb20.i and the mayhem test) on F1 lowers the heuristic frame-remap score pf (0.5677..0.5798 vs 0.58209) and moves the
  size (27,224..27,416 B); only the validate error region gains (+17..19 tokens). The original's
  probabilities come with its `and 1` instruction forms and per-arm fee threading; weights alone do
  not reproduce it.
- The CPI AccountInfo clone runs (orig 0x4180..0x4a00) are register allocation: the original reloads
  the accounts pointer from a spill slot (`ldxdw r1,[r10-0x8d8]`) before each clone group, ours keeps
  it in r6; the load offsets are the same sequence. No local IR edit near them changes that, but
  block-frequency edits inside validate do (`global_quote.exit` 1:2000: +42 tokens there, +30 in the
  native sweep, -38 in the sweep body; `inv:bb47.i`: +31). The clone-run residual is coupled to
  validate's block frequencies through spill weights.
- Re-creating the original's deep pieces directly (validate's target pieces unmerged, outer target
  pieces and `target1` moved after them, `_11.i294` kept unmerged) on top of F1 gives 0.459..0.466:
  without the matching code the exact deep order is worth less than the greedy frame edits.

Frame reading (agrees with w12a01-cto-frame's slot map): the original has two 7+9 B Option<Pubkey>
piece pairs and a 32 B Pubkey slot right after val.sroa.6.i (inlined region end), then `_184`…
`old_creator`, `val7`, the **entry copy of `new`** (7 B at T 0x658 and 9 B at T 0x668, written at
0x22f00..0x22f48 from the stack-passed `new` pointer: the original loads all 33 bytes of `new` at
entry) and a 24 B slot, then holder_key (0x6a0) and mint (0x6c0).

Ledger keys: `0x22a10-w12-20a1ae9-iroracle-*`.


## Review boundary for region and ranking diagnostics

`regionmap.py` and `pfboard.py` reproduce 0.45147 / 0.58119 on the retained
27,400-byte k4 candidate. The latter number is a heuristic score after voting
for stack-offset substitutions in the candidate bytes; it is not an emitted
build, a proven optimal frame, or proof that stack effects have been isolated.
Region labels borrow names from the explicit `--names` score report (default:
the repository baseline), and are an analysis aid rather than original symbols.
Use these diagnostics to choose source experiments; accept changes only through
the official raw/normalized scorer. Failed ranking inputs now return nonzero,
and region segment sizes must be positive. No new matched window is claimed.

Other exploratory IR tables are producer-reported observations, not independently
replayed in this review. They do not qualify a source candidate for merging.
