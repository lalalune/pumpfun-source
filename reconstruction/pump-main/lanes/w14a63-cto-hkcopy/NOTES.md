# w14a63-cto-hkcopy: holder_key copy and `_12.i` colouring for admin_cto::execute (0x22a10)

Bases: main 2e1379de9 (0.65728, 3192 slots, 27,400 B), then fc628cfd8 (0.65758, 3183) after main moved during the run.
This lane continues w14a57-cto-frameremap (#3368). Ledger approach: `hkcopy`.
**Result: notes only, no source change.** The holder_key copy has a source spelling that reproduces the original's colouring
exactly. It loses at every level we priced, even with a perfect frame. The `_12.i` lead has no code-neutral source form.

## Oracles (all on post-opt IR with llc only, or a raw-IR capture plus opt and llc; never a full build)
- `tools/hkir.py <m.ll> <out.jsonl> [names]`: holder_key-copy IR variants. It adds an alloca `hkc` (placed before or after
  `sk`), memcpys `holder_key` into it next to the `sk` copy (after or before), and gives it the same lifetime as `sk`. It
  can repoint the second memcmp at 312 and the holder-arm target pieces to `hkc`, swap the 312 order, and kick `_12.i`
  or `sk` out of a colour class.
- `tools/fm.py fn.bin...`: frame-masked ratio. This is the rx metric with every r10 ld/st offset and every lea immediate
  masked.
- `tools/offh.py lo hi fn.bin...`: histogram of r10 offsets, original and candidates side by side.
- `tools/shiftwi.py fn.bin below delta`: what-if that shifts every r10 offset below -`below` by `delta`.
- `tools/capvar.sh` (from w14a57, retargeted): source EDITS -> raw IR capture -> rx oracle.
- The w14a57 tools still apply: rx.py, ltscreen.py, scmap.py, errblk.py, lst.py and odis.py.
- The rx oracle on 2e1379d and on fc628cf gave eq_main=true.

## Findings
1. **Source form for the original colouring.** `validate(&st,hopt,fee,new,&{holder_key},&sk)` (edits/s1.py) creates a
   temporary holder_key copy at the call. It is identical to IR variant `f_a`: hkc alloca first, copy after sk.
   - hkc lands at -0x518, `sk` at -0x470, the validate error names at -0x488 and the to_string buffers at -0x4b8.
     This is exactly what w14a57's errblk/scmap reading of the original shows.
   - Its 8-instruction copy sequence matches the original's (orig 0x598-0x5d0) instruction for instruction.
   - Price: **0.53509 at 27,456 B** (+56 B: the copy is 64 B, less 8 B elsewhere).
   - The equivalent `let sk; let hkc=holder_key; ..&hkc` (s4) gives the same result. When hkc comes before `sk`'s let
     (s3), the copy runs before sk's: 0.54087 at 27,328 B.
2. **Why the copy collapses (priced):**
   - Frame-masked, f_a scores 0.6919 against main's 0.6953, so its code shape is slightly worse but not collapsed.
   - The raw collapse is all frame. Pushing the validate names into the -0x488 class sets off a colour cascade:
     - `_82/_68/_56` names move to the ix_data.i class, and `_48.sroa.11` moves to inner_data.i;
     - `target.i.sroa.9` moves to val.sroa.6.i, and `target.sroa.8` moves to event_signers.i;
     - `target.i.sroa.0` (7 B) becomes its own object at -0x548.
   - The object area therefore grows by 8 B. Everything below -0x548 shifts by -8, all spill slots included (OFFH_frame.txt).
   - Putting the shift back with the shiftwi what-if gives a summed per-call-segment match of 2084 tokens, against main's
     2098 (**-14**). The global difflib ratio is only 0.630, because it re-anchors around the +56 B.
   - So even a perfect frame repair plus a free 56 B repay does not beat main. Ltscreen over all 535 alloca variants of
     f_a peaks at 0.561. No single lifetime edit undoes the cascade.
3. **`sk` kick-out alone** (sk to -0x470, no hkc) scores 0.53911 at 27,384 B, frame-masked 0.6698. Its code shape is much
   worse than f_a's: with no hkc in the authority_info class, the MMO aliasing and the schedule change.
   Adding hkc (f_a) brings most of the code shape back.
4. **312 order:** comparing holder first, as the original does, loses: 0.65518 by IR swap, and every hkc variant with the
   swap loses about the same.
5. **`_12.i` lead re-priced:** kicking `_12.i` out of the -0x470 class (IR) gives **0.65878 at 27,400 B on fc628cf**
   (+0.0012; 0.65848 on 2e1379d). The frame-masked code is identical. In the errblk table this fixes exactly one site, the
   284 mayhem name (orig 0x56a0, -0x488).
   - Moving the lifetime.start (S0) or dropping the lifetime.end (E0) of `_12.i` is byte-identical: llc's StackColoring
     starts lifetimes at first use (lifetime-start-on-first-use).
   - Blocking `_12.i` from the -0x470 class therefore needs a member of that class that comes before `_12.i` (#100) in
     index order and is live in the 284 error block. Only allocas from inlined callees have such indices: validate and
     the helpers inlined into it.
   - None of those allocas is used before validate's mayhem test. Execute-level locals that live across validate (sk,
     args, hk, holder_key, st, mint) all have indices above 100, or are already in other classes.
   - Code-neutral spellings at 284 (s6 `let e=error!`, m1 `Err(..)?`, m2 `require!`) and the holder-arm or 312 copy
     forms (s5, c4, c5) are byte-identical to main. c1 (to_bytes), c2 (move closure) and c3 (`[..].contains`) collapse:
     0.563, 0.618 and 0.502 at -200..+104 B.
   - Conclusion: no code-neutral source form exists. Any spelling that blocks `_12.i` adds a store before the mayhem test.

6. **Full build of s1 on fc628cf** (measure.sh): **0.53539 at 27,456 B**, normalized 1034. Raw is 347 because the size
   change moves every later window. ERRBLK_orig_vs_s1.txt lists the error sites, original vs s1.
   - The validate sites now use name -0x488 with buffer -0x4b8, or name -0x4d0 with buffer -0x488. Both pairs occur in the
     original (main uses -0x470).
   - The remaining residual in this region is the target 7 B piece. s1 stores it at -0x545, in an object at -0x548.
     The original stores it at -0x535 (object -0x538) and copies it to -0x54d (object -0x550) at orig 0x19e0.
   - This is the target 8/24 split region, so the copy only pays off together with the validate target-representation
     change.

## Next ideas (untried here)
- s1 has the original's colouring. It can only pay off if the cascade objects also follow the original:
  - `target.i.sroa.0` and the 7/9 target pieces;
  - the original's 24 B target[8..32) host slot at -0x520..-0x538 (orig 0xab8-0xae8 copies hkc there).
- That means s1 combined with a target 8/24 split and 56 B of non-original code removed elsewhere. Price the combination
  with hkir.py-style IR edits (f_a plus a merged target host) before trying any source form.
