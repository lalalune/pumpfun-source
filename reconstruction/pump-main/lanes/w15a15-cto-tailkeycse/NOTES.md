# w15a15-cto-tailkeycse: the long-spill sets across the sharing CPI (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 86e2a6b (#3666), admin_cto 0.67376 with 3,124 slots at 27,400 B, Pump Main 1034/1035 normalized. Numbers are
from `$BASE`; I did not rebuild main.
This lane continues w15a06-cto-swepts1joint (#3656), next idea 2 ("key-load CSE"), and its finding that the original has a
different *set* of function-long spills.
Ledger approach `tailkeycse`, keys `0x22a10-w15-86e2a6b-tailkeycse-*` (9 rows).

**Result: notes only, no source change.**
- **The premise of the angle is false.** In the original, the E0, E2 and E4 tail key and lamports pieces do not read
  long-lived slots. Inside the sharing-CPI run, slots 0x910, 0x8e0 and 0x908 hold fresh spills made within the run.
  w15a06 saw these slots as "live from 0x150-0x420 to past 0x5a00", but that span covers several different values that
  share one colour.
- **The spill sets live across the sharing CPI** are 8 values in the original and 9 in ours. They differ by which values
  they hold, as listed in the table in section 2.
- **Prices.** The five key-binding spellings this angle proposed lose 0.06 to 0.19. A joint "every late use reads a
  validate-exit value" rewrite loses about 0.33.

## 1. Tool: CFG-aware slot webs on the final code (`tools/webs.py`, no build, about 2 s)

`webs.py <dis>` builds the CFG of a `dis.py`-style disassembly. It works on the original window and on any candidate
(`SYMS=<llvm-readelf -sW funcs>` resolves the call targets). It then runs reaching definitions on every exact
`[r10-X]` offset and joins definitions and uses into webs.

Calls that never return end their block:
- `unwrap_failed` and other panic helpers;
- the relocated syscall that has no `r1/r2` argument setup. That one is `abort()`, the overflow path of `Rc::clone`
  (orig 0x26e0, ours 0x26b8). The other two syscalls are `msg!`'s `sol_log_`.

Without this rule the abort fall-through creates a fake 1,214-instruction cycle (orig 0x1fb8-0x63b0), and the
path-insensitive analysis then merges unrelated values. With it, both CFGs are acyclic (`tools/scc.py`).

Modes:
- `--min-span N`: webs whose code span is at least N;
- `--why 0xOFF`: the reaching definitions of every use of a slot;
- `--live-at 0xA,0xB`: backward slot liveness, giving the webs live into a point;
- `--per-def`: intervals per definition;
- `--path 0xS,0xT 0xOFF`: a path from S to T that avoids any redefinition of OFF.

`tools/calls.py` lists the resolved call sites. The original and main line up call for call (157 each).

## 2. Spill slots live across the `admin_cto_sharing_config` call (`data/live-sharingcpi-*.txt`)

The call is at orig 0x4a78 and ours 0x4a20. The table lists slots at 0x8d8 and above. The aggregate locals below
0x8d0 are the same in both.

| value | original: slot, defs, late uses | ours (86e2a6b): slot, defs, late uses |
| --- | --- | --- |
| accounts pointer | 0x8d8, def 0x280 (r8) | 0x8d8, def 0x3d8 |
| entry r1 / r2 | 0x8f0 / 0x938, entry | 0x8f0 / 0x938, entry |
| fee value (stack argument) | 0x930, def 0x1f0, uses 0x4ba0 (curve), 0x4dd8 (pool CPI) | 0x930, def 0x120, uses 0x4b58, 0x4da0 |
| sharing_update tag | 0x8f8, a 5-def phi (0x4e0..0x1980); reloaded into r6 at 0x4a90 right after the CPI, and again at 0x4d48 | 0x8e0. Split at the run entry by a copy into the same slot (`ldxdw r1,[0x8e0]; stxdw [0x8e0],r1` at 0x3ce0/0x3ce8). The post-CPI piece runs 0x3ce8 -> 0x4ee0 |
| fee tag | **0x8e8: a validate-exit phi of constants** (`mov r7,1` on the fee-Some exit, def 0x1998). Used at 0x4b80 (`jne r1,0`) and 0x4dc8 (pool-CPI tag) | **0x910: the entry `r4` argument spill** (def 0x8). Used at 0xaa0, 0x1468 (validate), 0x4b38 (`jeq r1,1`) and 0x4d90 |
| holder (curve +0xa5, pool CPI r4) | **0x950: computed holder flag phi** (def 0x1d50 plus copies into the same slot). Used at 0x4b60 and 0x4e20 | **0x8e8: the entry `r3` argument spill** (def 0x10), `&1` at 0x4b08 |
| cashback (curve +0xa3) | **0x958: cashback phi** (defs 0xdb8, 0x1138, 0x1850, 0x18b8), `&1` at 0x4aa8 | **two head values**: `!holder` in 0x908 (def 0x4a0, `mov r8,1/0`) and `st.cashback` in 0x8f8 (def 0x4c0). They are ANDed after the CPI (0x4a48-0x4a60), because MachineSink sinks the `and` to the store |
| **count** | **8** | **9** |

What the table shows:
- **The set is one value larger in ours.** The extra value is the cashback AND, which is sunk past the CPI, so both of
  its inputs stay live. The original has a single cashback phi.
- **Identity, not count, explains the colour clash.** In the original, the arguments die early:
  - the holder argument `[0x918]` is used once, at 0x610;
  - the fee-tag argument `[0x928]` dies at 0x1500.

  All of the original's late uses read phis defined at the validate exit, from 0x1980 to 0x1d50.
- **Ours keeps two entry arguments, plus two head values defined at 0x4a0/0x4c0, live up to the end.** Their intervals
  start at slot index 0. That is why they sit on colours 0x910, 0x908 and 0x8f8, which the original keeps free for
  the in-run tail pieces.

The provenance matches w14a107's per-use-site table. This table adds the CFG-exact live sets and the +1 count.

## 3. The original's 0x910 / 0x8e0 / 0x908 are multi-occupancy colours (`data/why-orig.txt`)

| slot | webs (def -> uses) | content inside the sharing-CPI run |
| --- | --- | --- |
| 0x910 | 0x350 -> 0x630..0x1988; 0x1f70 -> 0x2060 (`ctx.bumps.creator_vault`, w15a07); **0x3f30 -> 0x4550, 0x49e0**; 0x5b50 -> 0x5d40, 0x61d0, 0x6900 (wallet) | E0 key piece. `r5 = ldxdw [r1+0]` at 0x3dc8, where `r1 = [accounts+0x98]`, the pool_authority info. It is spilled at 0x3f30 |
| 0x8e0 | 0x150; 0x2a8; 0x1990; 0x1f48 (`&holder_creator_vault`, w15a07) -> 0x2130..0x3bb8 and the sweep tail 0x5a78/0x5ae8/0x5f10; **0x3f50 -> 0x3fd8, 0x48d0**; 0x4b50 (old_fee) | a fresh in-run spill |
| 0x908 | 0x420 -> ..0xdb0; 0x1a78 -> 0x2a70; **0x4190 -> 0x4218, 0x47d0** (later sweep uses reach from 0x1a78) | a fresh in-run spill |

The sweep's native and token blocks are laid out after the post-sweep code: block placement runs after register
allocation. Reading spill spans in final address order therefore joins values that are never live together. This
produced the "live past 0x5a00" reading.

So the original does not CSE the tail key loads. Binding keys early can only add live values.

## 4. Prices (full `measure.sh` builds, zero normalized losses, size not repaid; `data/results-*.jsonl`)

| variant | what | bytes | ratio |
| --- | --- | ---: | ---: |
| main 86e2a6b | - | 27,400 | **0.67376** |
| k0top | E0 `pool_authority` key bound once at the execute entry, literal `key:k0` | 27,408 | 0.61465 |
| k2top | E2 `global` key bound at the entry, `key:k2` | 27,424 | 0.58901 |
| k02top | both | 27,440 | 0.60141 |
| k0mid | E0 key bound just before the sharing `match` | 27,424 | 0.48690 |
| k02mid | E0+E2 just before the `match` | 27,512 | 0.49268 |
| j_all | validate returns `(target,holder,cashback,fee)` with fee rebuilt per arm; curve stores and pargs read those values | 27,560 | 0.30884 |
| j_nofee | as j_all, fee returned unchanged | 27,640 | 0.35759 |
| j_nohr | as j_all, curve holder store keeps the argument | 27,264 | 0.34089 |

- Every key binding adds a long value across the run. The losses (-0.06 to -0.19) are far beyond any size knob.
- The joint rewrite changes validate's return to an sret tuple, which re-lays the whole frame, as w14a54 found for
  `opt_both`. It does not reach the original's set either. In j_all, the values live across the CPI are the accounts
  pointer in 0x8d0, the entry arguments, a 2-def phi in 0x8f8, and so on.

## 5. Verdict and next ideas

- Within this angle, the only set difference left is the +1 from the sunk cashback AND. w15a14-cto-holder465 is pricing
  that one (IR oracle rows at 14:39 UTC). Earlier spellings of it lose: w14a82 re-derive, w15a09 per-arm forms
  c1-c6, and w14a116 forcing the AND to stay in the head.
- The other identity differences each have a ledger record of losses:
  - fee-tag phi forms: w14a54, -0.08 to -0.33;
  - holder phi or curve-store forms: w14a107 cs_hb, w14a111, w15a08 (main +2 even with a perfect spill frame).
- Untried idea:
  - A source form where the fee tag and the holder flag reach the curve store as validate-exit phis *without*
    changing validate's signature or return type. Two things block it: jump threading never creates the fee-Some
    edge block (w14a54 §2), and an inlined `match fee{Some(f)=>Some(f),None=>None}` folds back to the argument.
    Any lane that finds such a form should first check, with `webs.py --live-at`, that the entry argument spills die
    in validate.
- Use `webs.py` instead of linear spill spans whenever a question is about which value occupies a frame slot. It runs
  on the original bytes directly.

## Tools (`tools/`, analysis and experiment only)

- `webs.py`: CFG reaching-def slot webs, liveness at points, paths, and per-def intervals. Default `SYMS=/tmp/syms.txt`
  (`llvm-readelf -sW $BASE/unstripped.so | awk '$4=="FUNC"{print $2,$3,$8}'`).
- `scc.py`: CFG cycle check.
- `calls.py`: resolved call list.
- `runv.sh <edits.py> <variant> <slot>`: copies the crate, applies exact single-occurrence edits (the line count is
  kept) and runs `measure.sh`.
- `edits/keys.py`, `edits/joint.py`: the variants in section 4.

- `dis.py` (copied from w14a139 `t139/dis.py`): `dis.py orig 0 100000`, or run it on `$BASE/unstripped.so[0x22a10:+27400]`.
