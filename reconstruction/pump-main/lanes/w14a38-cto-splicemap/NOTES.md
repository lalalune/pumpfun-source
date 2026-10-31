# w14a38-cto-splicemap: whole-window residual map for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 81d3d9abe (0.65069, 3,171 slots), then 6db95a764 (`$BASE/unstripped.so`, 0.65458, 3,280 slots), 1034/1035 normalized and raw.
Ledger approach `splicemap`, keys `0x22a10-w14-81d3d9a-splicemap-*`.

## Method (tools/splice.py, tools/regions.py)

- Tokens are `score.normalize` instructions, exactly what target_metric's ratio uses (`splice.py load` reproduces
  0.65069 / 3171).
- A region [lo,hi) is spliced by replacing the candidate's tokens and bytes in that offset range with the original's
  (both boundaries must be instruction boundaries in both). `dratio` / `dslots` = the gain if that region alone matched.
- Each region's local residual is split by re-aligning the region with progressively masked tokens:
  `fm` = misses removed by masking r10 frame displacements (and negative add64 immediates), `rm` = then by masking
  registers, `jm` = then by masking jump offsets, `sk` = structure misses that remain (opcode / immediate / block order).
- `splice.py anchors` lists equal-offset runs whose fully masked tokens are equal (>= 4 instructions). There are only 18
  on 81d3d9a: 0x0-0x80, 0x1028, 0x1c38-0x1d30, 0x46b8-0x4970 (87 insns), 0x5c38-0x6b08 runs (wallet). Everywhere else
  ours is shifted by 8-0x40 bytes against the original, so large regions are spliced between call landmarks instead.
- `lst.py` names every call (orig call targets resolve through the candidate symbol table, the layout outside the window
  is identical); `o.calls`/`c.calls` side by side give the call LCS used for the source mapping.

## Ranked map (REGIONS.json, regenerated on main 6db95a764: 0.65458, 3280 slots; FIXED200.jsonl has the same split per 0x200 chunk)

| orig region | what | lines | owner | dratio | dslots | fm | rm | jm | sk |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0x26e8-0x3930 | TCF transfer_creator_fees_to_pump_v2 inline AccountInfo literals | 661 | sweep TCF (w14a17/w14a23) | +0.0575 | 585 | 39 | 118 | 18 | 25 |
| 0x3c38-0x46b8 | sharing CPI admin_cto_sharing_config inline literals | 745-751 | sharing CPI (w14a30) | +0.0563 | 336 | 24 | 0 | 0 | 173 |
| 0x1068-0x1940 | validate fee errors 326/312/307/330/338/334 (to_string outlined in orig) | 307-338 | validate (w14a15/w14a21); w14a07/w14a10 notes | +0.0356 | 277 | 22 | 14 | 4 | 111 |
| 0x5c38-0x6b08 | wallet(): flags, ATA create, collect + event, coin CPI | 556-580 | wallet r8 (w14a35); w14a24 notes | +0.0321 | 396 | 25 | 50 | 20 | 15 |
| 0x80-0x400 | entry head: holder-rewards PDA (orig first), shared test (orig creator==key), quote_locked memcmps | 339 | unowned (w14a09/w14a11 notes: PDA-first = orig head but RA cascade -0.07) | +0.0168 | 107 | 4 | 7 | 0 | 48 |
| 0x400-0x6a8 | CtoState/holder_key copy + validate head (mayhem, holder tests) | 339,283-296 | validate (w14a15/w14a21); w14a02/w14a29 notes | +0.0162 | 84 | 6 | 18 | 3 | 45 |
| 0x838-0xe08 | validate 298/312 memcmps, 306/296 error blocks | 296-312 | validate (w14a15/w14a21) | +0.0162 | 181 | 20 | 0 | 19 | 43 |
| 0x4970-0x4e60 | curve update, pool gate, admin_cto_pool clone run + CPI | 752-766 | curve tail (w14a34); w14a25 notes | +0.0102 | 154 | 6 | 14 | 1 | 26 |
| 0x1940-0x1c38 | sharing/collect_old tuple, prepare_bonding_curve, require 410 | 339-410 | w14a29 hcbools notes | +0.0090 | 92 | 6 | 3 | 3 | 27 |
| 0x1d30-0x2300 | sweep head: native test, creator-vault PDA, amm_frozen, raw_amount, 660 error | 647-660 | unowned | +0.0081 | 185 | 3 | 10 | 11 | 9 |
| 0x46b8-0x4970 | sharing CPI tail: skeleton equal, frame only (AccountInfo array 0x30 B lower in ours) | 749 | frame only | +0.0075 | 87 | 37 | 0 | 0 | 1 |
| 0x4e60-0x5538 | AdminCtoEvent build + emit + event CPI | 767 | unowned (w14a26/w14a20 landed pieces) | +0.0069 | 215 | 3 | 15 | 3 | 15 |
| 0x3968-0x3c38 | TCF call, Rent::get, native sweep head | 661-663 | native join (w14a33) | +0.0057 | 90 | 9 | 6 | 1 | 9 |
| 0xe28-0x1068 | validate 306/296 error blocks | 296,306 | validate (w14a15/w14a21) | +0.0053 | 72 | 16 | 0 | 4 | 16 |
| 0x5570-0x5a80 | tail error blocks: unwrap_failed, mayhem 284, NotWritable 556, Rent min balance | 284,556,663 | unowned | +0.0042 | 162 | 8 | 6 | 2 | 13 |
| 0x5a80-0x5c38 | sweep native: ensure_rent_exempt + transfer_native + return join | 664 | native join (w14a33) | +0.0042 | 55 | 6 | 4 | 4 | 10 |
| 0x6a8-0x838 | validate error blocks 289/298 (Display fmt) | 289,298 | validate (w14a15/w14a21) | +0.0036 | 50 | 14 | 2 | 4 | 12 |
| 0x2498-0x26e8 | sweep 719 frozen/raw_amount + token_frozen | 719 | holder vault ATA (w14a27) | +0.0033 | 74 | 0 | 3 | 8 | 12 |
| 0x2330-0x2478 | ConstraintSeeds error block 648 | 648 | unowned | -0.0024 | 40 | 0 | 1 | 0 | 7 |

Readings:
- Four owned regions (TCF, sharing CPI, validate fee errors, wallet) hold 0.183 of the 0.349 gap. The unowned ones are
  each worth at most +0.017 if matched exactly; the entry head is the largest and is already known to be the original's
  PDA-first form that loses to the register cascade.
- The sharing CPI region is pure structure at the masked level (sk 170, rm 0): the literal load order, not register names.
  TCF and wallet are register dominated (rm 118 and 58).
- The call sequences are equal from 0x1cc8 to the end (157 calls each). The only call-order differences are in the entry
  (orig: find_program_address first) and in validate's error-block order (orig 289, 298, 312-memcmps, 306, 296, 326, 312,
  307, 330, 338, 334, prepare, 410; ours 298, 289, memcmps, 296, 326, 306, 312, 307, 330, 338, prepare, 410, 334) and
  the two inlined to_string (orig 7 to_string + 6 name/fmt pairs, ours 5 + 8).

## PDA-first (p1) re-measured on 81d3d9a: structure gain, one register swap

`p1` = holder-rewards PDA before `shared`, `a.bonding_curve.creator==a.sharing_config.key()` (the original head, w14a11).
Oracle (raw-IR capture + opt + llc, tools/capvar.sh + rx.py, m0 reproduces 0.65069 @ 27,400): **0.56903 @ 27,360 B**.
`tools/segdiff.py` splits both functions at their 157 calls and counts matches against the original per call segment:

| mask level | main matches | p1 matches | delta | where |
| --- | ---: | ---: | ---: | --- |
| raw (rx mask) | 2076 | 1812 | -264 | seg 69 (TCF clone run, orig 0x26e8) -219, seg 72 (sharing CPI) -37 |
| frame masked | 2309 | 2049 | -260 | seg 69 -234 |
| frame + registers masked | 2585 | 2608 | **+23** | gains in segs 0-4 (the head, +44), small losses elsewhere |

So p1 is the better skeleton, and the whole loss is one register swap: in the sweep the reloaded accounts pointer
(`ldxdw rX,[r10-0x8e0]`) gets r6 and `&a.<0x108>` (= accounts+0x108) gets r8, where main and the original have the accounts
pointer in r8. Every TCF clone load is based on that register, so the swap costs ~-0.08. The original never keeps
accounts+0x108 live: it computes `mov r1,r8; add r1,0x108` and spills it to [r10-0x8e0] at once, and later does
`add64 r8,0x48` in place (the accounts pointer dies there and is reloaded). Ours keeps both in callee-saved registers.
p1 also adds one 8-byte spill slot (the TCF spills sit 8 B lower). Ten p1 partners (dest/native operand order, by-ref
keys, PDA binding forms, owner-first, `&`) stay in 0.534-0.587.

## Region-local screens on 81d3d9a (oracle, all at or below main; ledger keys 0x22a10-w14-81d3d9a-splicemap-*)

| variant | region | bytes | ratio |
| --- | --- | ---: | ---: |
| hL: `shared` with creator on the left | head | 27,400 | 0.64889 |
| e_sk / e_skL: `let sk=` hoisted into `shared` | head | 27,112 | 0.54277 |
| e_skref: `*a.sharing_config.key==creator` | head | 27,320 | 0.64926 |
| s_destL / s_destne / s_destref / s_destrefcmp / s_destkeyvar | sweep PDA check | 27,400 / 27,536 / 27,320 / 27,320 / 27,400 | 0.65009 / 0.31227 / 0.64746 / 0.64746 / 0.40144 |
| s_desttuple `let (dest,_)=` | sweep | 27,400 | = main |
| s_nativeL / s_native_late | sweep | 27,400 | 0.64979 / 0.6459 |
| s_amm_if / s_amm_present / s_amm_and | sweep amm_frozen | 27,400 / 27,416 / 27,784 | = main / 0.6499 / 0.36621 |
| s_oldfirst (vault seeds `old` first) | sweep | 27,400 | = main |
| s_holderkey_val (sweep takes Pubkey by value) | sweep | 27,464 | 0.40365 |
| s_gate_if `if !skip{sweep()?}else{0}` | sweep gate | 27,416 | 0.51303 |
| n_rentmin / n_lamfirst | native | 27,416 / 27,400 | 0.6469 / = main |

## Register permutation census (tools/regpairs.py, main 81d3d9a)

Aligned instructions (registers and frame masked) whose registers differ, by region: TCF 126 (orig r9->ours r0 18,
r0->r5 18, r6->r5 13: clone-load temporaries), sharing CPI 74, wallet 50 (r9->r7 18, r7->r8 11: the do_coin r8 cascade),
entry copy 25, curve tail 15, event 16, sweep head 10.

## Tools

- `tools/splice.py` load / anchors / chunks / regions / fixed / range: splice what-ifs and fm/rm/jm/sk split.
- `tools/regions.py <so> REGIONS.json`: the ranked semantic-region map with owners.
- `tools/lst.py <so> orig|cand`: listings with named calls; `tools/cdis.py`: candidate objdump with window offsets.
- `tools/segdiff.py <base fn.bin> <variant fn.bin> [--lvl N]`: per call-segment match delta of a variant (use rx.py's fn.bin).
- `tools/regpairs.py <so> lo hi`: dominant register permutation in a region.
- `tools/capvar.sh`, `rx.py`, `capraw.py` (w14a01's oracle, repointed), `tools/rec.py` (ledger recorder).

## Size drift and frame remaps on 6db95a7 (DRIFT.txt, FRAMEPAIRS.txt)

`tools/drift.py` aligns the whole window with frame and registers masked and prints, per 0x400 of the original, the
median (our offset - original offset) of matched instructions:
- validate (0x800-0x1400) is block-reordered (drift jumps +408 / -824);
- from 0x1c00 ours runs 24-72 B behind the original; the sharing CPI (0x3c00-0x4400) loses another ~50 B (only 7
  instructions of 0x4000-0x4400 align at all, the literal region is reordered); the tail then gains it back (+40 at
  0x4c00, +32 at 0x5c00, +16, +24), so ours is ~50 B short in the sharing CPI and ~100 B long in 0x4c00-0x6b08.
- ratio is not positional, so drift only matters through jump offsets (jm) and slots_diff.

`tools/framepairs.py`: 253 aligned instructions differ only in the r10 displacement (2,061 aligned are equal). The
largest single remaps: the accounts spill slot (orig -0x8d8, ours -0x8e0, 13 instructions), orig -0x950 -> ours -0x8e8
(7), the error-name String buffer (orig -0x488/-0x4b8 -> ours -0x470, 5+5 per error block), -0x938 -> -0x930 (5).
No single remap is worth more than ~0.004.

## Later screens on 6db95a7 (main 0.65458)

| variant | bytes | ratio |
| --- | ---: | ---: |
| le_vy1 / le_vy1m (w14a21 validate closure lead, re-tested) | 27,392 | 0.63191 / 0.63071 |
| ev_hr: event `is_holder_reward` from the curve (the original's load) | 27,392 | 0.65169 |
| ev_hr_cbfirst | 27,392 | 0.65169 |
| ev_cbfirst, ev_swept_early, ev_pool_early, ev_reset_local (literal order / matches!) | 27,400 | = main (identical) |

## Lead: sharing-arm tuple before the target store (su_tafter, +0.0017 at -40 B)

On main 6db95a7 (0.65458), in execute's `(collect_old,sharing_update,skip)` tree:

```rust
// main
}else{target=st.creator;(false,Some(args.0),true)}
// su_tafter (t2/t3/t4/t6 spellings are byte-identical to it)
}else{let r=(false,Some(args.0),true);target=st.creator;r}
```

| variant (oracle, = identity build tokens) | bytes | ratio |
| --- | ---: | ---: |
| main 6db95a7 | 27,400 | 0.65458 |
| su_tafter | 27,360 | **0.65627** |
| su_tafter + s_amm_present (`let amm_present=!..data_is_empty();let amm_frozen=amm_present&&..`) | 27,376 | **0.65638** |
| su_tafter + clone (`Some(args.0.clone())`) | 27,256 | 0.60258 |
| t5: `target=st.creator` after the whole tree (`if shared&&!holder{..}`) | 27,384 | 0.4519 |
| su_new / su_argsval (`Some(new)`, `args=(new,)` by value) | 27,344 | 0.46904 |
| su_ok_drop (drop the `Ok::<_,Error>((..))?` re-wrap) | 27,400 | 0.54164 |

su_tafter is about +4 exact matches (2M/(n_o+n_c): 2185 -> 2189) and 5 fewer instructions; the change is a register
re-colouring of the validate head and the tuple copies (orig 0x1800-0x1a50 keeps a two-stage copy of `sharing_update`,
ours one). **It is not landable yet: it needs +40 B (or +24 B on the s_amm_present stack) at <= ~3 lost matches.**
67 w14a31 knobs that still apply were stacked on su_tafter+s_amm_present: 46 are now byte-identical (27,376 / 0.65638),
the size-adding ones lose too much (wl_ixlit +32 B -> 0.65208, wl_native_deref +80 B -> 0.6512, ev_bc_deref, s_native_deref,
tp_pargs_hold, wl_infos_ref worse). `Some(args.0)` re-spellings (`map`, `if let`, `match`, `as_ref().copied()`) cost 96-104 B
and fall to 0.603.
