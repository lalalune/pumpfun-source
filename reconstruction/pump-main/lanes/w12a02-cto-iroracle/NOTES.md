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

Frame reading (agrees with w12a01-cto-frame's slot map): the original has two 7+9 B Option<Pubkey>
piece pairs and a 32 B Pubkey slot right after val.sroa.6.i (inlined region end), then `_184`…
`old_creator`, `val7`, the **entry copy of `new`** (7 B at T 0x658 and 9 B at T 0x668, written at
0x22f00..0x22f48 from the stack-passed `new` pointer: the original loads all 33 bytes of `new` at
entry) and a 24 B slot, then holder_key (0x6a0) and mint (0x6c0).

Ledger keys: `0x22a10-w12-20a1ae9-iroracle-*`.
