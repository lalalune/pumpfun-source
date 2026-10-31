# w14a52-cto-prep410: the validate→sweep bridge region (orig 0x1940-0x1c38) of admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`, line 339 tuple/Ok carry, prepare, line 410),
pinned at 27,400 B. Bases: main 0fbf8daa1 (0.65578, 3,280 slots), then 63308119b (0.65698, 3,193 slots), 1034/1035 normalized and raw.
Ledger approach `prep410`, keys `0x22a10-w14-0fbf8da-prep410-<name>-v1` and `0x22a10-w14-6330811-prep410-<name>-v1` (80 rows).

**Result: no zero-loss gain. Notes only.** The region's +0.0090 splice value (w14a38 REGIONS.json: 92 slots, fm 6, rm 3,
jm 3, sk 27) is mostly the E334 block's placement (+0.0075, w14a36's bound). The rest is the order and placement of the
tuple data flow, which none of 70 source spellings moves without a loss. The only lead, a sharing_update-first tuple
(`t_ord_suf`), gave +2 matched tokens at +24 B on 0fbf8da (0.65609 @27,424). It is negative on 6330811 (0.65669 @27,424
against main's 0.65698), and no -24 B knob pairing reached 27,400 B.

## Block-by-block miss table (orig 0x1800-0x1c38 against ours 0x16a0-0x1c78, `tools/rdiff.py`)

Ours is 0x90 B earlier from the fee-Some exit to the 410 error block, because E334 is not before it. The sk 27 of the
region is E334's 26 instructions sitting at our 0x1ba8 instead of before the region.

| # | orig | ours | kind | difference |
| - | --- | --- | --- | --- |
| 1 | 0x1730-0x17f8 E334 (`name`,`to_string`,`From`, 6077 line 334) | 0x1ba8-0x1c70, after E410 | block order | The original places E334 after E338 and before the fee-Some exit. Ours puts it after the 410 block. This costs 26 sk misses here, plus a 0xd0 shift. w14a36 (#3325) found the cause: in the original the fee-Some exit is a split block made by register-allocation edge copies, so E334 (freq .0092) is placed before it. In ours that exit is merged into the hotter join `bb76` (.039). |
| 2 | 0x1800 fee-Some exit: `stxdw [-0x918],r4; stxdw [-0x948],r3; mov r7,1` | none (merged into `bb76`) | missing block | These are spill copies plus the fee-tag constant (r7=1, read again at the curve store). Ours has no such block. |
| 3 | (none) | 0x16a0-0x16e8 `bb76`: 4 piece copies of validate's `Result<Pubkey>` (`target.i.sroa.0` 7 B, `.sroa.9` 9 B through `_48.sroa.11`) + `stxdw [-0x8d8],r8` | extra stores | Ours copies validate's target into execute's `target` BEFORE the shared tree. The original copies it AFTER the tree, at the post-tree join (0x19a0-0x1a48, through the temp [-0x670..-0x680]). |
| 4 | 0x1818-0x1828 shared test `ldxdw [-0x920]; jne; ja` | 0x16e0-0x16f8 | equal (jm only) | The original tail-duplicates this small test into every validate exit: fee-None holder at 0x1118, fee-None non-holder at 0x1500, and fee-Some here. In ours it sits once, after the copies in #3, so the block is too big to tail-duplicate. |
| 5 | 0x1830-0x18a8 shared arm: spill holder r6→[-0x950], sharing tag r0→[-0x8f8], `jeq r8,0` (falls into !holder; the holder arm is laid out at 0x1128, in the validate region), cashback r5→[-0x958], new pieces [-0x655/-0x658/-0x668/-0x660]→sharing payload [-0x535/-0x538/-0x548/-0x540], r3=1, r6=0 | 0x1700-0x1808: `mov r1,r8; and r1,0xff; jne` to the join (the holder arm becomes join constants); !holder arm re-reads `args.0` through the pointer (r7+8: `ldxw [r1+0]`, `[r1+3]`, `[r10-0x21]`, `[r10-0x19]`) and copies st.creator 32 B from [r4] into [-0x2d0..-0x2b8] | polarity, extra mask, extra load/store | The holder test is `jeq` in the original and `jne` in ours. Ours has an extra `and 0xff`. Ours reads the sharing payload through the `&(new,)` pointer, where the original copies it from the entry copy of `new`. Ours has no holder/cashback spills in the arm (MachineSink, w14a29 #3301). |
| 6 | 0x18b0-0x18f0 !shared arm: holder/cashback spills, r3=1, r6=0, tag 2→[-0x8f8], `ldxdw [-0x8e0]` (holder_reward) | 0x1810-0x1850: dead `ldxdw [-0x908]`, `mov r1,r3`, tag 2→[-0x8e8], r9=0, `ldxdw r8,[-0x8e0]` | frame + reg | The sharing tag slot is [-0x8f8] in the original and [-0x8e8] in ours. Skip is kept in r3 in the original and in r9 in ours. |
| 7 | 0x18f8-0x1970 collect_old memcmp `st.creator != default` | 0x1868-0x18d8 | equal (12 insns) | Ours spills r0/r5 (the sharing payload pieces) around the call. The original keeps `mov r3,1` (skip) after the memcmp. |
| 8 | 0x1978-0x1a50 post-tree join: re-store tag 2, reload r2=[-0x910] (system_program), skip r3→[-0x8e0], fee tag r7→[-0x8e8], target [-0x918]+[-0x520..-0x530] → [-0x580..-0x568] (via [-0x670..]), payload → [-0x560..-0x549], reload accounts r8=[-0x8d8] | 0x18e0-0x1978: target [-0x2d0..] → [-0x560..-0x548], payload → [-0x580..-0x561] | field order in frame | The Ok-carry tuple's target and sharing_update are swapped in the frame. The original has target at the lower address. |
| 9 | 0x1a58-0x1a88 prepare call | 0x1980-0x19b8 | 1 reg | Prepare's r2 is a reload of [-0x910] in the original and r7 kept live in ours. |
| 10 | 0x1a90-0x1c30 410 test + E410 | 0x19c0-0x1ba0 | equal skeleton | Only the jump offsets differ, and the error-result register (r9 in the original, r8 in ours). |

So the region is three coupled mechanisms: E334 placement (#1/#2), the pre-tree target copy that blocks the original's
per-exit tail-duplication of the shared test (#3/#4), and spill-slot/register naming (#5-#9). #1-#4 are one CFG fact:
the original has no single post-validate join. w14a36's IR proofs (`dup76.py`, `sink76.py`) reproduce the original's
order only at 0.607-0.644.

## Screen (raw-IR capture + rx opt/llc oracle; m0 reproduces main exactly on both bases; edits in `e/`)

On 0fbf8da (main 0.65578 @27,400, M 2,189):

| family | spelling | bytes | ratio |
| --- | --- | ---: | ---: |
| tuple order | `t_ord_suf` (sharing_update,collect_old,skip) | 27,424 | **0.65609** (M +2) |
| | `t_ord_scs` / `t_ord_ssc` / `s_su_cs` | 27,408 | 0.49783 |
| | outer tuple permutations `o_su1..5` (with/without suf) | 27,400 / 27,424 | = main / 0.65609 |
| separate lets | `t_sep`, `t_sep2` | 27,528 / 27,600 | 0.50269 / 0.52261 |
| skip as expression | `t_skipexpr` (`!shared\|\|!holder`) | 27,464 | 0.54668 |
| collect_old form | `t_coif` (if-else) | 27,400 | = main (identical) |
| | `t_comem` (memcmp first) / `t_coand` (`&`) | 27,384 | 0.64909 |
| | `t_codefl` (default on the left) | 27,400 | 0.65518 |
| tree shape | `t_notsh` (!shared first) / `t_match` (match tuple) / `t_hnot` (!holder first) | 27,400 | = main (identical) |
| payload source | `t_new` (`Some(new)` instead of `args.0`) | 27,368 | 0.46942 |
| target assignment | `t_tgtlate` (after the tree) / `t_tgtexpr` (target in the tuple) | 27,368 / 27,400 | 0.45204 / 0.38346 |
| | `ts_if`, `ts_if2`, `ts_sel`, `ts_su` (target=st.creator moved to the curve store, pargs from curve) | 27,496-27,688 | 0.316-0.334 |
| | `ts_pa` (pargs from curve only) | 27,560 | 0.53943 |
| | `t_notgt` (no `target=st.creator`; oracle only, not faithful) | 27,088 | 0.39385 |
| Ok carry | `ok_ord_stc` / `ok_ord_cst` | 27,400 | 0.65398 |
| | `ok_ord_tcs`, `ok_co`, `ok_skip` | 27,400 | = main (identical) |
| | `ok_tonly` (target only) | 27,400 | 0.54344 |
| prepare | `p_ctx`, `p_bind` | 27,400 | = main (identical) |
| | `p_beforeok` / `p_inblk` (prepare before the carry / inside the state block) | 27,504 / 27,392 | 0.55075 / 0.44105 |
| 410 | `r_if`, `r_ifgt`, `r_tmp` | 27,400 | = main (identical) |
| | `r_ne` (`<1`) | 27,416 | 0.63252 |
| fee arm return | `f_someret`, `f_tail`, `f_tail2`, `f_okfee` | 27,448-27,464 | 0.487-0.537 |
| size pairs | `sh` (sharing `if let`, -8) / `tp` (pool `data_len`, -8) | 27,392 | 0.65558 / 0.65468 |
| | `suf_sh` / `suf_tp` / `suf_sh_tp` | 27,416 / 27,416 / 27,408 | 0.65439 / 0.65349 / 0.65359 |
| | `suf_cm`, `suf_ca`, `suf_cm_sh`, `suf_cm_tp`, `suf_ca_sh` | 27,376-27,384 | 0.648-0.649 |

Re-measured on 6330811 (main 0.65698, M 2,193): `t_ord_suf` 0.65669 @27,424 (M +0), `sh` 0.65678 @27,392,
`tp` 0.65588, `suf_sh` 0.65618, `suf_tp` 0.65529, `suf_sh_tp` 0.65479, `ok_ord_stc` 0.65518. `t_comem` collapses
(0.54496 @27,456) on this main. Carry after prepare/410 (`c_afterprep`, `c_after410`) 0.552 @27,504. `c_nomut`
(drop `let mut target=target`) is identical.

`t_ord_suf`'s +2 on 0fbf8da is register-allocation noise: three extra movs and r0/r5 swaps through 0x0600-0x1980
(`segdiff.py`: segs 11/12 +1 each), not a change in region structure. The pairing knobs do not add up: suf + sh + tp lands
at 27,408, not 27,400.

## IR oracle: post-tree target copy (`tools/postjoin.py` + `tools/llcscore.py`, main 6330811)

This edits the post-opt `m.ll` (the base round-trips to 0.65698 @27,400). It removes validate's target copies from the
pre-tree join (`bb74`: `target.i.sroa.0` 7 B → `target.sroa.0`, `target.i.sroa.9` 9 B → `_48.sroa.11` → `target.sroa.8`).
The copy into `target13` at the post-tree join `bb26` then reads a phi of source pointers: the arm's own copy for the
shared&&!holder block `bb21`, and validate's pieces for every other predecessor. This is the original's post-tree copy (#3).

| variant | bytes | ratio | error order |
| --- | ---: | ---: | --- |
| `pj` (7 B + 9 B moved) | 27,440 | 0.3739 (frame shift) | 330 338 410 334 (unchanged) |
| `pjk` (7 B moved, 9 B hop kept) | 27,432 | 0.6479 | 330 338 410 334 (unchanged) |

So the pre-tree target copy is NOT what keeps E334 after the 410 block. Even with `bb74` reduced to the `new`-piece copies
and the shared test, MBP still takes the join before E334. The lever is only the split fee-Some exit (w14a36). Ledger keys
`0x22a10-w14-6330811-prep410-irpostjoin-{pj,pjk}-v1`.

## Reading

The IR oracle above shows that #3 alone does not move E334. Every faithful spelling of the bridge either folds to main's IR (MIR canonicalises if/match/polarity, require!/if,
by-ref/bind) or changes the frame and loses 0.01-0.3. The region's structural misses (#1-#4) need validate's exits to
stay unjoined. That is the same CFG fact as w14a36's E334 analysis and w13a18's fee-phi notes, and the
validate-outline lanes (w14a10, w14a15, w14a21) own it. No bridge-local source form gets there.

## Tools (`tools/`, experiment only)

- `capvar.sh`, `capraw.py`, `rx.py`, `splice.py`, `segdiff.py`, `lst.py`, `cdis.py`, `regions.py`, `regpairs.py`: w14a38's
  oracle and splice tools, repointed to this lane.
- `batch.sh <res.jsonl> names...`: 2-worker capvar queue (deletes crate copy, IR and objects per row).
- `gen*.py`: the edit generators for `e/*.py`. `rec.py`: ledger recorder (`SHA=`/`BASE=` env for the base).
- `sl.py lo hi` / `rdiff.py olo ohi clo chi lvl`: orig/cand listing slices with named calls, and an aligned diff at a
  mask level (0 raw, 1 frame, 2 +regs, 3 +jumps). Both read `orig.dis` (`win.py orig 0x22a10`), `cand.dis` (`cdis.py`),
  `o.lst`/`c.lst` (`lst.py`) from the current directory.
