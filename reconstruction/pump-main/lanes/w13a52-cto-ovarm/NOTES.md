# w13a52-cto-ovarm: the shared target override in validate's non-holder arm (OV)

Target: 0x22a10 `admin_cto::execute`, pinned at 27,400 B. This is a wave-13 lane, continued in wave 14 on main 53abf28b1 (0.62672). The findings were re-checked on main 23322b07c (0.62882).

Result: notes only. No OV form reaches main. The question this lane was given is answered: on current main the OV sweep-tail collapse is gone, and what is left is a frame loss plus a register loss.

## Answer to the angle question (is the OV collapse the MBP veto?)

- On older mains (3912c47, 74b3171), OV collapsed to 0.17–0.30 because the sweep tail was relaid out (w13a04, w13a18). w13a31 traced the same symptom in lv3 to a MachineBlockPlacement fallthrough veto.
- **On 6ff770f, 53abf28 and 23322b0, plain OV does not relayout.**
  - The call/exit landmarks (`tools/callperm.py`) match main exactly: the same 6 runs, including the 113-call tail run 0x1c58–0x6a68.
  - errseq equals main's.
  - Result-tag tests are on r7 at 19 sites (main 18, original 21).
  - So the MBP veto plays no part in OV today, and the tag web stays on r7.
- OV is 0.53309 at 27,176 B on 53abf28 (0.53099 on 23322b0), against main's 0.62672 (0.62882).
  - Skeleton (frame and registers masked): 0.85680, above main's 0.85410.
  - Frame-masked: 0.71781, below main's 0.72588.

## Mechanism 1: OV's target is SSA in MIR, so its 9 B SROA piece is unmerged

- In main, `target` is assigned twice (`validate()?`, then `target=st.creator` in the shared non-holder arm), so it keeps StorageLive/Dead.
- In OV it is assigned once. CopyProp merges it into the `?` payload and drops its storage markers. As a result, `%target` has no `llvm.lifetime` in the raw IR.
- After SROA, the 9 B piece `target.sroa.4` has no lifetime markers and gets its own frame slot (−1640). That pushes mint, holder_key and hk down 16 B, and the whole spill band at orig 0x6a8–0xc28 sits +0x10 from the original (`tools/fdelta.py`: 188 refs at +0x10).
- OV also gains a 33rd 16 B sret slot, as the original has; main has 32.
- IR oracle (lifetime.start/end added to `target.sroa.4`): **0.53309 → 0.59356** at the same 27,176 B. With the frame-sweep greedy on top, the best is 0.60499.
- None of the source spellings tried restore the markers. These are byte-identical to OV: `let target; target=..`, `{let t=..?;t}`, `*&target`, `target.clone()`, `target=target` in the arm, `let (target,)=&(..?,)`, match / `!shared` / shared as the first param.
  - `let mut target=Pubkey::default();target=..?` gives 0.51292 at 27,240 B.
  - The `&(..?,)` borrowed tuple gives markers, but they end too early (0.53279).

## Mechanism 2: the `Ok::<_,Error>((target,sharing_update,cashback))?` wrapper is anti-OV

- Dropping the wrapper (OVw1) gives **0.58271 at 27,096 B**. Frame-exact refs rise to 1,020 (main 984), but fm falls to 0.71287.
- `target` becomes a single 32 B alloca and `target13` disappears.
- The best single frame edit is `mv:buf.i32.i:END`, at 0.59295.

## Ceiling and size

- Every OV form is 224–304 B short of 27,400.
  - The original's missing code is mainly the 53-insn shared-arm block at orig 0xd90–0xe58: st.creator is copied into [r10-0x4e8..] and into [r10-0x530..], the 8/24 split, and fee-None is threaded per arm.
  - Two error-construction blocks at 0x9f0 and 0xe60 are laid out inline.
- Per-arm store spellings (`let r;if shared{r=st.creator}else{r=t}r`, `let mut r=t;if shared{..}`) are folded back to one select copy (0.58309 at 27,088 B).
- fm for every OV variant (0.713–0.718) is below main's 0.726, so even a frame-perfect OV stays below main.

## Structural note: OV plus holder_key PDA first

- OV plus holder_key PDA first (L9) gives the **best skeleton seen, 0.86525** (main 0.85410).
  - The original's entry call order is restored, worth +35 skeleton insns at 0x0–0x400.
  - There is no relayout.
- But the AccountInfo clone-run register allocation collapses: fm 0.68697, ratio 0.36585 at 27,304 B. This is the same failure as w13a32 hk-first.

## New oracle: addlt (tools/addlt.py)

- The oracle adds lifetime markers to every execute alloca that lacks them.
  - On main there are 8 such allocas: sharing_update14.sroa.3, target13, _230, _215, inner_data, authority_info, old_creator, val6.
  - Two variants: start at the first use, or after the allocas.
- On main, no gain: the best equals main and the others score 0.29–0.55. On OVw1, also no gain.

## Tools (tools/)

| tool | what it does |
| --- | --- |
| `capvar.sh <name> <edits.py> <slot>` | source edit, then raw-IR capture (`capraw.py`), then the `rx.py` opt+llc oracle (equals the build) |
| `frsweep.py` / `frgreedy.py` / `bwfm.py` | alloca move/nolt sweep and greedy, scored as ratio + fm + sk + errseq |
| `addlt.py` | the add-lifetime oracle |
| `frl.sh <m.ll>` | named frame layout (offset, size, name) via `llc -stop-after=prologepilog` |
| `regcmp.py a.dis b.dis fm\|sk\|raw [seg]` | per-original-chunk matched-insn counts for two candidates |

## Results table (raw-IR oracle = build tokens)

| variant | main | ratio | bytes | fm | sk |
| --- | --- | ---: | ---: | ---: | ---: |
| main | 53abf28 | 0.62672 | 27400 | 0.72588 | 0.85410 |
| OV (all spellings) | 53abf28 | 0.53309 | 27176 | 0.71781 | 0.85680 |
| OV + s_map | 53abf28 | 0.53183 | 27152 | 0.71783 | 0.85628 |
| OV + IR lifetime on target.sroa.4 | 53abf28 | 0.59356 | 27176 | 0.71781 | 0.85680 |
| OV + lifetime + frame greedy | 53abf28 | 0.60499 | 27176 | 0.71781 | 0.85680 |
| OVw1 (no Ok wrapper) | 53abf28 | 0.58271 | 27096 | 0.71287 | 0.85478 |
| OVL9 (PDA first) | 53abf28 | 0.36585 | 27304 | 0.68697 | 0.86525 |
| OVMK (override in both) | 53abf28 | 0.53199 | 27256 | 0.71163 | 0.84920 |
| main | 23322b0 | 0.62882 | 27400 | | |
| OV | 23322b0 | 0.53099 | 27176 | | |
| OVw1 | 23322b0 | 0.58090 | 27096 | | |

Ledger keys: `0x22a10-w13-53abf28-ovarm-*`.
