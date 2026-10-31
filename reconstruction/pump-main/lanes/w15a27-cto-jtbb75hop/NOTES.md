# w15a27-cto-jtbb75hop: what fee-None threading through bb75 is worth, and why it is not worth it (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 9120883a9
(0.67376, 3,124 slots). This lane continues w15a20-cto-ovarmpin (#3718), next idea 2. Ledger: approach `jtbb75hop`, keys
`0x22a10-w15-9120883-jtbb75hop-<trial>-v1` (8 rows).

**Result: no landable change. Main is still the best zero-loss measurement (0.67376 @ 27,400 B).** The class F shape
(the original's fee-None edges threaded into the tree arms) is worth at most **-5 true-LCS rfj tokens** against main, even
with the threading free and main's block layout kept. Its gain is +10 tokens in validate/tree (0x800 +3, 0x1000 +1,
0x1800 +6), and that gain is used up by -15 tokens of scattered single-token RA and spill noise. No ordinary spelling gets
there: every spelling that makes the tree-test block cheap loses 71-485 tokens.

## 1. The bb75-only bound (step 1)

Two oracles, both new and reusable (`tools/`):

- **Resume-after-JT2 oracle (`rxt.py`).** Run `opt -O3 -print-before=jump-threading -filter-print-funcs=<execute>
  -print-module-scope` and keep dump #2. That is the module just before execute's second JumpThreading. Then run only
  the rest of the O3 pipeline (`tailpipe.txt`, cut out of `-print-pipeline-passes`) and llc. The round trip is
  **eq_main** and takes 2.4 s, against 35 s for a full dbg-opt `-O3`.
- **Per-block JT threshold plugin (`mkjtf.sh` → `jtf.dylib`).** This is a private copy of LLVM 18 `JumpThreading.cpp`,
  built as an `opt -load-pass-plugin` pass named `jt-force`. It raises `BBDupThreshold` only in
  `maybeThreadThroughTwoBasicBlocks`, and only for the PredBB names in `JTF_BLOCKS` (`bb75` or `bb75:bb18`). The shared
  llvm-dbg tree is not touched. With no override, `tailpipe_f.txt` (jt-force in place of JT2) is eq_main.

| trial | what | bytes | true-LCS vs main (--- / r-- / rf- / rfj) | rfj per orig 0x800 chunk |
| --- | --- | ---: | --- | --- |
| t20 | JT2-only `-jump-threading-threshold=20` | 27,576 | -351 / -359 / -66 / **-49** | 800:+3 1000:+1 1800:+6 **4800:-44**, rest -15 |
| f75 | plugin, bb75 only | 27,576 | byte-identical to t20 | same |
| c3 | pre-JT2 IR edit: bb75 chain cut to main's post-memcpyopt 3 memcpys; JT threads natively at 6 | 27,480 | -316 / -281 / -66 / -49 | same |
| c2 | same, 2 direct memcpys target.i→target | 27,480 | -173 / -98 / -66 / -49 | same |
| **c2__pj** | c2 + main's layout kept (MIR `JMP %bb.262` at bb88's end) | 27,488 | -139 / -56 / -19 / **-5** | 0:-1 800:+3 1000:+1 1800:+6 2800:-3 3000:-3 4000:-3 5000:-1 5800:-3 6000:-1 |
| c3__pj, f75__pj | same layout fix | 27,488 / 27,584 | rfj -5 each | same |
| g_bb18 / g_bb21 | plugin `bb75:bb18` only / `bb75:bb21` only | 27,576 / 27,536 | -49 / -538 (the 6 KB chunk hoist) | |

- The global-threshold result in w15a20 (m0 -49) was not "threading elsewhere". bb75 alone gives the same bytes.
- **The bb75 memcpy count does not change the price, only the threading does.** c2, c3 and f75 have the same rfj pattern.
- The remaining -15 tokens are single-token spill and copy differences (for example orig 0x2ea0 `mov64 r9,r6` and 0x2eb8
  `stxdw [r10-0x9b8]`) spread over 0x2800-0x6000. They are RA perturbation, not structure.

### The 0x4800 -44 mechanism (new, useful to other lanes)

- BPF `analyzeBranch` cannot analyze conditional branches. So MachineBlockPlacement **pre-merges every block that ends in
  a conditional jump with a fallthrough to its layout successor** ("Pre-merging due to unanalyzable fallthrough",
  `llc -debug-only=block-placement` with the llvm-dbg llc, which reproduces the SDK llc).
- In main, `bb88` (the post-sweep sharing-tag test) ends with `JNE ..; JMP %bb.262`. That is because the copy block
  `bb87` (`$r8 = MOV $r3; $r4 = LDD [r10-2288]`) sits between it and `bb37`. bb37 (the curve state write, orig 0x4aa8)
  is then placed after the sharing CPI arm, as in the original.
- With the threading, greedy puts the sweep-join value in **r6 instead of r3**, so bb87 is empty and the branch folder
  deletes it. bb88 then falls through into bb37, the pre-merge pins bb37 there, and the state write moves about 0xd00 B
  earlier. That costs -44.
- `tools/pjgen.py` + `tools/mbp.sh` (stop before block-placement, add the explicit JMP, resume) restore main's layout.
  This is an oracle only.
- Any variant whose curve state write (`stxb [..+0xa5]`, `[..+0xa3]`) moves before the sharing CPI should look at bb88's
  terminator in `-stop-before=block-placement` MIR first.

## 2. Spellings that cut bb75's memcpys (step 2)

Each spelling was gated with `tools/tcost.py`, which gives the JT-cost and memcpy count of the `br i1 %shared` tree-test
block in dumps #1/#2, and with a dbg-opt `-debug-only=jump-threading` trace. All were captured on 9120883 (`tools/cap.sh`,
then the w15a20 `rx.py`).

| spelling | tree-test block at JT2 | threads bb75? | ratio @ bytes | rfj vs main |
| --- | --- | --- | --- | ---: |
| main `let mut target=validate(..)?;` | bb75: 10 memcpys, cost 20 | no (cost 8 > 6) | 0.67376 @27,400 | 0 |
| s11 `#[inline] fn validate` | = main | no | byte-identical | 0 |
| s1/s6/s13/s14 `match validate(..){Ok(t)=>t,Err(e)=>return Err(e)}` (plain, deferred-init, +#[inline], `let r=..;match r`) | n/a | n/a | 0.29949 @22,600 | -485 |
| s21/s22 cashback after validate (match or `?`, byte-identical; = w14a128 cb_aftervalidate) | bb17: 0 memcpys, cost 1 (the chain stays in the validate exit block) | no | 0.53444 @27,192 | -71 (4800:-44 again) |
| s27 `validate(..)->Result<&'a Pubkey>`, `let mut target=*validate(..,&new,..)?` | bb75: 1 memcpy, cost 2 | **yes**, bb75+bb18 twice (class F) | 0.29929 @27,024 | -121 (validate 800:-12 1000:-5 1800:-9) |
| s28/s29 `validate->Result<()>`, then `target=new.unwrap_or(holder_key)` / `if let Some(t)=new{t}else{holder_key}` | bb76: 0 memcpys, cost 0 | no tree threading needed | 0.29217 @27,112 / 0.28528 @26,936 | -126 / -119 |

- **The match spelling is not a `?` alternative.** rustc's MIR JumpThreading threads the preceding
  `cashback=!holder&&st.cashback` holder test through the match. That duplicates the whole validate call: the raw IR
  has 2 call sites, so LLVM no longer inlines validate. Once nothing branches before the call (s21 vs s22), match and
  `?` are byte-identical.
- **Where the 10 memcpys come from.** All of them are the `?` desugaring of `Result<Pubkey>`: `target.i` (validate's
  pieces) → `_49` (the sret Result) → `_411` (the `Try::branch` ControlFlow) → `_48` → `val` → `target`, each a 7 B + 9 B
  pair. The block tuple and the `Ok::<_,Error>` hop come after bb18/bb21 and add nothing to bb75. memcpyopt (after JT2)
  later collapses the chain to 3 memcpys. So any `Result<Pubkey>`-through-`?` form has at least 8 memcpys at JT2, and
  only a by-reference or unit return gets under the threshold. Both of those re-lay the frame and lose more than 100
  tokens.

## Conclusion and next ideas

- The class F threading is worth ≤ +10 validate/tree tokens, about 0.3% of rfj. Its best possible net is -5 rfj, so
  it is not a lever for the remaining ~0.33 gap. Do not spend lanes on making bb75 cheap.
- The bb87 / unanalyzable-fallthrough mechanism is the general reason why "RA moves one value r3→r6 and a 0xd00 B
  block moves". It is worth checking in other variants that show a lone big chunk loss. s21/s22 also show 4800:-44,
  but s22 keeps bb87 between bb88 and bb37 in its pre-placement MIR, so its loss has a different cause.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `rxt.py <name> <jt2-module.ll>`: resume the O3 tail after execute's JT2, then llc and score (`PIPE=tailpipe_f.txt` uses
  the plugin; extra opt flags in `OPTX=`).
- `mkjtf.sh <dir>`: build the `jt-force` plugin. Env `JTF_BLOCKS`, `JTF_T`; trace with `-debug-only=jtf`.
- `bbed.py`: replace a block's body in a dumped module (used for c2/c3; bodies in `e/e_c2.txt`, `e/e_c3.txt`).
- `tcost.py <name>`: tree-test block JT cost and memcpy count in each pre-JT dump.
- `mbp.sh <name> <tag> <edits>` + `pjgen.py` (`PJN=<name>`): stop-before block-placement MIR edit and resume. With no edit
  the round trip is identical.
- `mapr.py <cand> <lo> <hi>`: global true-LCS map of orig tokens in a range to cand offsets, plus unmatched runs.
- `evcm.py` (`MASK=r--` etc.): per-chunk true-LCS under any mask. `dd.py`: disassemble orig/cand ranges.
- `cap.sh`: w15a20 `cv2.sh` without the rx step (capture only). `e/`: all spelling edit sets.
