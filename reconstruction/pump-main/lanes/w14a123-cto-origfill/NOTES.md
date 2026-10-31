# w14a123-cto-origfill: orig-only run decode and prices on the 307/312 outline base (admin_cto::execute 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base main ebe5387
(0.67316, M 2,247, 3,123 slots). This lane continues w14a108-cto-crlrepay (#3513). Ledger approach `origfill`, keys
`0x22a10-w14-ebe5387-origfill-<trial>-v1`. **No zero-loss improvement. This is a notes PR.**

The lane ran on a machine at load average about 127. Captures took 20-75 minutes each instead of about 40 s, so the screen
is much smaller than planned. Every number below is from the raw-IR capture + opt + llc oracle (`rx.py`; the main capture
is `eq_main` true). M is matched masked tokens. fM, rM, rfM and rfjM mask frame offsets, registers, both, and both plus
jumps (w14a108 `fr.py`).

## Base O (step a)

O is main plus a call-site `noinline` on just the 307 (code 30) and 312 (code 19) `to_string` calls (`tools/ni.py`, an IR
edit, not source). These are the two calls the original outlines (call 0xa938).

| | bytes | M | fM | rM | rfM | rfjM | error-site order |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| original | 27,400 | | | | | | 289 298 306 296 326 312 307 330 338 334 |
| main ebe5387 | 27,400 | 2,247 | 2,346 | 2,562 | 2,622 | 2,810 | 298 289 296 326 306 312 307 330 338 334 |
| O | 26,992 | 1,953 | 2,165 | 2,291 | 2,577 | 2,790 | 298 289 **312** 296 326 306 307 330 ... |

This reproduces w14a108's -408 B. Almost all of the loss is frame and registers (rfjM is -20, M is -294). Per original
0x800 chunk (`tools/ch.py`), the skeleton gains +27 in 0x800-0x1000 and loses 44 in 0x1000-0x1800. The outlined 312 block
moves ahead of 296, while the original puts it after 326.

## Decode of the orig-only runs (step b; `tools/dec.py`, which builds on w14a106 prov.py; full dump in `decode_orig_runs.txt`)

Slot meanings come from the provenance pass and the uses that follow.

| slot | value |
| --- | --- |
| `[r10-0x38..-0x20]` | `st.creator` (CtoState copy of curve+8) |
| `[r10-0x910]` | bonding_curve ptr |
| `[r10-0x928]` | the `fee` tag (R4) |
| `[r10-0x8f8]` | the `sharing_update` tag phi: the new tag in the shared non-holder arm, the constant 0 = Some(None) in the holder arm, 2 = None when not shared |
| `[r10-0x950]` | the is_holder phi (1 in the holder arm, 0 otherwise) |
| `[r10-0x958]` | the cashback phi (curve+0xa3 in non-holder arms, 0 in the holder arm) |
| `[r10-0x918]` | target[0..8] |
| `[r10-0x530..-0x520]` | target[8..32] (the 8/24 split) |
| `[r10-0x4e8..-0x4d8]` | a second copy of target[8..32]. No load reads it inside the window, so it is probably the host slot of a second Pubkey local |
| `[r10-0x535..-0x548]` | the sharing_update payload pieces (7/9 split; new+0x18 lands at -0x548) |

| orig run | B | sits between | decoded data flow | ordinary-source counterpart |
| --- | ---: | --- | --- | --- |
| 0x0c08-0x0c40 | 56 | 298 / 306 | `if let Some(t)=new`: new+1 copied as 4/4/8/1 pieces into the t slot `[-0x4b8..-0x499]`; new+0x10 also kept in `[-0x948]` | the t binding that the memcmps read from the stack (ours reads t through a pointer, r9) |
| 0x0d90-0x0e08 | 120 | 298 / 306 (non-holder t-valid exit) | cashback bool from curve+0xa3; branch on `shared`; shared: target = **st.creator** from `[-0x38..]`, written to both target copies; then the fee tag is tested: None goes straight to the join 0x1850, Some goes to the fee checks at 0x1510 | shared override inside validate's non-holder arm, before the fee checks; fee-None threaded per arm |
| 0x0e28-0x0e50 | 40 | same | the fee-None edge of that arm: `[-0x950]`=0, r7=0, cashback reload | as above |
| 0x0ed8-0x0f00 | 40 | 306 | 306 error payload stores (stw 6089 / stb 2 / 306 imm) in the original's order | 306 error-block order |
| 0x10f0-0x11a8 | 184 | 296 / 326 (holder arm, new None) | `[-0x918]` = holder_key[0], is_holder=1, cashback=0, branch on `shared`; shared: payload pieces copied from **dead slots** (-0x44d/-0x450/-0x2d0/-0x2c8) with tag constant 0 | holder-arm `Some(None)` whose payload is a memcpy of an uninitialised aggregate; the merge keeps per-arm copies |
| 0x14b0-0x1530 | 128 | 307 / 330 (non-holder, not shared) | t pieces copied from the t slot into both target copies; is_holder=0; fee tag test (None goes to the collect_old memcmp at 0x18f8); fee Some reloads the fee and flag registers | per-arm fee-None threading again |

All three large runs are one mechanism. **The original decides the sharing tree (target override, sharing_update,
collect_old) in each validate arm before the fee checks, and the fee test is duplicated into each arm.** In ours,
`validate` returns first and the tree runs after the merged validate exit. Earlier lanes reached the same conclusion
(w13a05 feethread, w14a76 threehop, w13a13 OVMK), on older mains and without the outline.

## Prices (step c)

| trial | source change | bytes | M | rfjM | on O: bytes / M / rfjM |
| --- | --- | ---: | ---: | ---: | --- |
| t1 | shared arm `target=st.creator` | 27,392 | 2,244 | 2,810 | 26,984 / 1,953 / 2,790 (no change) |
| **ha** | holder arm `(false,Some(args.0),false)` (equal to Some(None): validate rejects `new` in the holder arm) | **27,168** | 2,061 | **2,846 (+36)** | 26,696 / **2,003 (+50 vs O)** / 2,825 (+35) |
| hn | holder arm `Some(new)` | identical to ha | | | |
| hat1 | ha + t1 | identical to ha | | | |
| su1 | one shared tuple `(false,Some(args.0),!holder)` + `if !holder{target=..}` | 27,272 | 1,920 | 2,850 | 26,840 / 1,871 / 2,833 |
| su2 | override first, then tuple | 27,440 | 1,464 | 2,184 | 27,016 / 1,451 / 2,167 |
| vin | the whole sharing tree inside validate before `match fee` (the decoded original shape) | 27,168 | 1,555 | 2,791 | 26,736 / 1,550 / 2,793 |
| ha + pu_amm_key / pu_amm_keyfn / ev_auth_deref / ev_mint_key / ev_cb_local | single-gene additions (sweep stopped by machine load) | 27,168-27,248 | 2,036-2,063 | 2,828-2,853 | 1,977-2,006 |

**ha is the lead.** It is a faithful, behaviour-preserving spelling, since the holder arm already requires `new.is_none()`.
It removes 232 B and gains +36 skeleton tokens: +62 in the sharing-CPI chunks 0x3800-0x4800 (`ch.py`), the same region as
w14a108's `ev_cb_local` lead. On base O it is the only union member found that is positive (+50 M). It does not land: at
27,168 B the frame and register cascade costs 186 M, and the 232 B shrink is spread across the function as register spills
(the largest single step is -88 B at the validate-exit join), not one block. ha does not produce orig run 0x10f0: LLVM
merges both shared arms' `Some(args.0)` into one value at the join.

vin, the decoded original shape, keeps the skeleton (rfjM 2,791) but collapses rM to 1,471: a full register-assignment
cascade, as in earlier attempts.

## Next ideas

1. Run the ha + gene sweep to the end (`tools/bat1.sh`, spec `ha_<gene> ha+<gene>` over the 207 applicable s12/mine
   genes) on a machine that is not overloaded. Look for a +232 B partner that keeps rfjM >= 2,846.
2. ha + crl_L (+72 B) + ev_cb_local + other byte-adding faithful constructs, to reach 27,400 B. Then check whether M
   recovers once the frame size matches.
3. vin + ha on base O, and vin with the holder arm `Some(new)`, to see whether the RA collapse is the holder-arm phi.
4. A source form of the holder-arm per-arm payload copy (orig 0x1140-0x1178 copies dead slots), for example
   `Some(None)` built through an `Option<Option<Pubkey>>` local that is assigned in each arm.

## Tools (experiment only; in `tools/`)

- `ni.py`: rx edit that adds call-site noinline on `to_string` for the codes in `NI` (default 30,19).
- `og.py`: this lane's genes (ha, hn, t1, su1, su2, vin, vinh, vinm).
- `cvO.sh`: w14a108 cv.sh capture, then the plain rx plus the `_O` rx with ni.py, the bfi cold-site line and fr.py.
- `bat1.sh`: a one-worker spec runner. `ch.py`: per-original-0x800-chunk M and rfjM deltas. `errseq.py`: error-site order.
  `dec.py`: per-instruction symbolic slot and load provenance (needs w14a106 prov.py, with `analyze` returning
  `(loads,IN,ins)`). `rec2.py`: ledger recorder.
