# w14a70-cto-a1reread: a1 token-arm order + re-read / size repays (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a59-cto-unownedrgn (#3377). Ledger approach `a1reread`, keys `0x22a10-w14-<main7>-a1reread-<name>-v1`
(about 200 rows). Main moved three times during the lane: 304b03a (0.65788), 39eb377 (#3386, 0.66477) and
0d04cf4 (#3393, 0.66507, M 2,220). Every number below comes from the raw-IR capture + opt + llc oracle
(`tools/capvar.sh`, `rx.py`). `m0` reproduces main exactly on each base (`eq_main`). M is the count of matched masked
tokens and jM is M with jump offsets also masked (`tools/mm.py`).

**Result: no gain.** a1 (`token_raw_amount` before `token_frozen`) is M-neutral at 24 B short of the pinned size. No
repay reaches main. A new structural lead, **t1** (a1 plus separate `?` on `create_idempotent` and `transfer_vault_tokens`),
is +4 tokens over main with frame, registers and jumps masked. Its best pinned-size pairing is **0.66477, 1 M below
main**. The register naming of the token arm blocks both a1 and t1, and the greedy register allocator decides it.

## 1. a1 on each main

| main | main M @ 27400 | a1 | a1 M | jM (a1 / main) |
| --- | ---: | --- | ---: | --- |
| 304b03a | 2196 | 0.65728 @ 27376 | 2193 | 2225 / 2228 |
| 39eb377 | 2219 | 0.66507 @ 27376 | 2219 | 2247 / 2250 |
| 0d04cf4 | 2220 | 0.66507 @ 27376 | 2219 | 2246 / 2249 |

a1 needs a +24 B repay that does not lose M.

## 2. Repay screens on a1 (none reaches main)

| screen | base | runs | best at 27400 / best result |
| --- | --- | ---: | --- |
| re-read oracle (w14a43 `rscan.py`), 18 inlined AccountInfo clones (`allclones.py`), singles | 304b03a | 136 | every +8 re-read loses. Best x18 data 0.65658 @ 27384 |
| same | 39eb377 | 136 | x18 data 0.66377 @ 27384, x12 data 0.66157 @ 27392 |
| catalog knobs (`sizeknobs-cto.json` + w14a43 `klib.py`, 53 distinct) | 304b03a | 53 | no size-adding knob is M-positive. The -8 B rP (pool_authority rent via x) gave M +4 on 304b03a (0.65857 @ 27368) |
| a1+rP + re-read singles and within-clone pairs | 304b03a | 608 | best 0.65518 @ 27400 |
| w14a64 gene library (98 genes that apply) + 8 amount spellings + `&&Context` sweep | 39eb377 | 106 | none M-positive. n3/n3b/n8/n13/n15 (`.map(\|()\|amount)`, `.and_then(\|()\|Ok(amount))`, `match` for `?`, `Ok(0)` tail) give a1's exact stream. n12/n14 (`return Ok(..)` in the frozen arm) are +24 B but 0.66297. `&&Context` 0.62361 |
| pure +8 pad bound (shift.py model, greedy, 3 pads) | 39eb377 | | M 2219 -> 2220 -> 2221 -> 2221: pads alone cap a1 at 0.66537 (main+2 M). Real knobs all lose more than a pad |

rP lost on 39eb377 (a1+rP 0.66457 @ 27368, M 2217).

## 3. The naming blocker (a1 and t1)

Original 0x20b0-0x2160: `ldxdw r2,[r8+0x48]; call token_raw_amount; ... add64 r8,0x48; ldxdw r6,[r10-0x2c8]` (amount in
r6, field pointer in place in r8). a1 instead does `stxdw [r10-0x9b8],r6; mov64 r6,r8; add64 r6,0x48; ldxdw r8,[r10-0x2c8]`.
The field pointer gets r6, which evicts accounts+0x108 to a mid-arm spill, and the amount gets r8.

- MIR after register-coalescer (`llc -stop-after=register-coalescer` on a1): `%245 = COPY %0; %245 = ADD_ri %245, 72`.
  `%0` is the function-wide accounts vreg. It stays live past the arm, so the coalescer cannot join them. Whether the
  in-place `add64 r8` appears depends on where greedy RA splits `%0`, not on the token-arm source.
- Bound (`tools/rename2.py` / `rename3.py`: swap r6/r8 in the arm and in the create/transfer uses of the a1/t1 `fn.bin`):
  a1 M 2219 -> **2224** at 27376 (0.66657). t1+rP M 2218 -> **2223** at 27400 (0.66597, +0.0009 over 0d04cf4).
- None of these reproduce it: IR accounts+0x108 via-slot / remat on a1 (w14a45 `ed.py`: s1 0.38165, g1/g2 0.59991,
  g3 0.66217), `&&Context` (same naming), or any of the 15+8 token-arm spellings (they fold).

## 4. t1: the original's create/transfer error shape (a1-specific)

`t1` = a1 + `create_idempotent(..)?;crate::collect_v2::transfer_vault_tokens(..)?;return Ok(amount);` (main has
`create_idempotent(..).and_then(|()|transfer_vault_tokens(..))?`). It restores the original's Err tests: `ldxdw r7,[-0x770]; jne r7,2`
after create_idempotent, and an out-of-line transfer Err pad. At level 3 (frame, registers and jumps masked) t1 is
**+4 over main** (segments orig 0x20d0 +1, 0x60c0 +1, 0x6328 +2). On frozen-first main the same `?` split collapses
(f1 0.63115 @ 27456), so the two changes go together: the original is a1 **and** separate `?`.

t1 is 32 B over a1's size (27408 on 39eb377/0d04cf4, M 2216, jM 2249-2250). -8 B pairings:

| base | pairing | bytes | M | ratio |
| --- | --- | ---: | ---: | ---: |
| 39eb377 (main 2219) | t1 + rP | 27400 | 2218 | 0.66447 |
| 39eb377 | t1 + rL / cu_match | 27400 | 2217 | 0.66417 |
| 39eb377 | t1 + rO (drop pump_fees owner re-read, -16) + x18 data re-read | 27400 | | 0.66447 |
| 39eb377 | t1 + rP + rO (27384, M 2218) + every cross pair of the top-12 re-reads | 27400 | | 0.66447 |
| **0d04cf4 (main 2220)** | **t1 + nB (`!is_writable`)** | 27400 | **2219** | **0.66477** |
| 0d04cf4 | t1 + shif / rP | 27400 | 2216 | 0.66387 |
| 0d04cf4 | t1 + nB + rP / shif (27392, M 2217) + re-read singles | 27400 | | 0.66477 / 0.66447 |

Shift map on t1+nB: the best pure pair is +3 M (+8 at cand 0x54a8, -8 at 0x5c98). The +8 is the original's missing
`mov64 r9,r1` after the Rent `ProgramError::from` (orig 0x54e0, the swept/Err payload in r9 residual of w14a06/w14a33).

## Next ideas

- t1 is the closest skeleton to the original in the token arm. Any lever that puts the amount in r6 (sweep-head RA:
  accounts split before the arm, or accounts+0x108 spilled at its def) is worth about +5 M on top of t1.
- t1+nB is 1 M below main at the pinned size. A zero-size lever with +2 M, or the swept-r9 copy at 0x54a8 (+3 bound),
  would land it.

## Tools (tools/, experiment only)

- `capvar.sh`, `capraw.py`, `rx.py`, `mm.py`, `runlist.sh`, `rec.py`, `osbs.py`, `sbs.py`, `segdiff.py`, `splice.py`
  (w14a59/w14a38, re-pointed to this lane).
- `rscan.py`, `allclones.py` (w14a43), `shift.py` (w14a64).
- New: `greedy.py <fn.bin> <n>` applies the best pure +8 pad n times (the size-repay ceiling for a short base).
  `rename2.py` / `rename3.py` compute the a1 / t1+rP token-arm naming bound.
- `e/*.py` holds every spelling (EDITS for capvar). `results/*.jsonl` holds every oracle row: r* are source captures,
  s* re-read singles, p* re-read pairs.
