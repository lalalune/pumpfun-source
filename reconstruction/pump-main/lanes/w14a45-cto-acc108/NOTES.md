# w14a45-cto-acc108: TCF clone-run register lane (accounts+0x108 live range)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Region: the sweep `transfer_creator_fees_to_pump_v2` clone run, orig 0x26e8-0x3930 (w14a38 REGIONS.json, +0.0575 if
spliced, rm 118). Bases: main 28ab23a9f (0.65488), then **6e011ea42 (0.65548, 3,280 slots, 1034/1035)**; every
number below was re-measured on 6e011ea unless marked.
Ledger approach `acc108`, keys `0x22a10-w14-6e011ea-acc108-*-v1`.

Result: **no gain**. No IR edit to the sweep-head live ranges beats main, and the forced original spills do not
reproduce the original TCF register naming. The source forms are byte-identical to main or lose.

## Step 1: what accounts+0x108 is

- `%_266` is the `AdminCto` accounts pointer. `holder_creator_vault: AccountInfo<'info>` is stored inline at +0x108
  (264), so `&a.holder_creator_vault` is the GEP `%327 = gep %_266, 264`.
- Post-opt uses of `%327` (in `rx/m0/m.ll`): the key load for the 648 `key()!=dest` compare (`[r8+264]`); the
  `with_pubkeys` key in the 648 error block; the outlined `AccountInfo::clone` of the 719 `Create.authority`; and the
  `ensure_rent_exempt` / `transfer_native` arguments in the 664 native arm. All of them are merged into one GEP in
  `bb84` (the sweep head), so the GEP is live across the TCF clone run. The TCF itself never uses it.
- +0x48 (72) is `creator_vault_quote_token_account` (an `UncheckedAccount`, 8 B). The original's in-place
  `add64 r8,72` is the token arm's `%514`. The accounts pointer is dead after this point in both builds: the
  original gives the amount r6 and turns r8 into the field pointer, while main gives the amount r8 and copies to r6.
  p1 (PDA first) already has the in-place form (on r6). It follows from the register choice. It does not cause it.

## What the original does at the sweep head (orig 0x1d28-0x1f70)

| value | original | main 6e011ea |
| --- | --- | --- |
| sharing tag (`sharing_update` i8) | reloaded into **r6** at the gate (0x1d30), live through the head | stays in its slot [r10-0x8e8], not in a register |
| bump `ctx.bumps.creator_vault` (argpromoted `ldxb [ctx+35]`) | r7, spilled to [-0x910] right after the dest compare | r9, kept in a register |
| native (memcmp i32) | r9, spilled to [-0x918] right after the dest compare | r7, spilled to [-0x918] |
| `&a.holder_creator_vault` (+0x108) | `mov r1,r8; add r1,0x108`, spilled to [-0x8e0] at once | `mov r6,r8; add r6,0x108`, kept in r6 until a mid-TCF spill (0x3090) |
| accounts | r8, reloaded from [-0x8d8] per clone in the second half of the TCF | r8 through the whole run |

## Step 2: IR bounds (tools/px.py post-opt llc oracle, tools/screen1_edits.py)

`px.py` applies edits to the slimmed post-opt module that `rx.py` writes and runs llc as fastbuild does
(0.25 s per variant; `p0` reproduces main exactly). The l0/l1/l2 columns are `segdiff.py` per-call-segment match
totals (raw / frame masked / frame+regs masked). TCF is seg 69. Main 6e011ea: l0 2092, l1 2326, l2 2585, TCF
regdiff 127 (`segregs.py`).

| edit | main: ratio @ B | l1 | l2 | TCF regdiff | p1: ratio @ B | p1 TCF l1 / regdiff |
| --- | --- | ---: | ---: | ---: | --- | --- |
| none | 0.65548 @ 27400 | 2326 | 2585 | 127 | 0.5716 @ 27344 | 259 / 329 |
| g1: remat the +0x108 gep at each later use | 0.59604 @ 27384 | 2310 | 2572 | 127 | 0.56144 @ 27312 | 259 / 329 |
| g3: remat at the native uses only | 0.65319 @ 27416 | 2316 | 2579 | 127 | 0.57991 @ 27352 | 259 / 329 |
| s1: +0x108 to its own slot at the def | 0.37998 @ 27384 (frame shift) | 2308 | 2576 | 127 | 0.33333 | 259 / 329 |
| b1: bump reloaded from ctx+35 at the vsigner store | 0.62343 @ 27400 | 2207 | 2562 | 174 | **0.60420 @ 27352** | 435 / **98** |
| sb: bump to its own slot | 0.34681 @ 27416 | 2218 | 2569 | 174 | 0.30815 | 435 / 98 |
| s1+ns+sb: all three original head spills | 0.32449 @ 27392 | 2279 | 2570 | 128 | 0.27439 | 315 / 179 |
| g1+ns+sb / s1+ns+b1 | 0.350 | 2286 / 2269 | 2572 / 2565 | 128 | 0.32 | 315 / 179 |
| fake `asm "r"` use of the sharing tag at bb84 (28ab23a) | 0.65419 @ 27408 | -1 | -1 | 130 | 0.57181 | 259 / 331 |

(`ns` = the native memcmp i32 stored to a slot after the call, with the icmp moved to the branch.)

Readings:
- **On main, freeing r6/r7/r9 in the sweep head does not fix the TCF naming.** With all three of the original's head
  spills forced, the TCF regdiff goes 127 -> 128 and l1 drops by 47. The TCF temp permutation (orig r9 -> ours r0 19,
  r0 -> r5 18, r6 -> r5 11, r6 -> r9 9) is decided inside the clone run, not by values that live across it.
- If only the +0x108 gep goes (s1/g1), native takes the r6 it frees. The TCF is unchanged and the frame or size shift
  costs raw. This matches w14a17's cef0574 `ir-hcv-remat` row.
- **On p1 the bump is the TCF key.** Under p1, holding the bump in a register is what pushes the accounts pointer out of
  r8: the TCF regdiff is 329, mostly orig r1 -> ours r3 x170. Reloading the bump late (b1) brings the p1 TCF to
  regdiff 98, which has better register names than main's 127. But it changes the TCF block layout (post-RA tail
  merging of the Rc-overflow arms: l2 589 -> 467), and the vsigner segment (orig 0x1fa8) loses 20 because the original
  reloads the bump from its spill, not from ctx. p1+b1 stays at 0.6042, 0.051 below main.

## Step 3: source forms (raw-IR capture + rx oracle, tools/capvar.sh)

| form | main 6e011ea | p1 |
| --- | --- | --- |
| `let hcv:&AccountInfo=&a.holder_creator_vault` at the sweep head, used at 648/664/719 | byte-identical | - |
| `let bump=ctx.bumps.creator_vault` moved to the sweep head | byte-identical | - |
| **`fn sweep(ctx:&&Context<AdminCto>,..)`, called `sweep(&&ctx,..)`** | 0.62043 @ 27400 (IR == b1) | 0.6015 @ 27352 (+0.030 over p1) |
| `&&Context` + bump at the head | byte-identical to main | - |

The ledger already holds the other forms from the lane prompt: fresh `&ctx.accounts` in the arm, `.clone()`,
`*ctx.accounts..key`, `key!=&dest`, `dest!=key()` (w14a41 `hcvremat-srcforms`, byte-identical or -80 B), the
`as_ref()`/by-ref key compares (w14a38 `s_destref*`), and bump reloads (w14a17 `ir-bump-reload`).

**Mechanism others can use:** passing `&&Context` to a single-call helper stops ArgPromotion from hoisting the
helper's `ctx.<field>` loads to the call site. The helper's ctx loads then stay where the source puts them after
inlining. It is the only source form found that moves the bump load. It loses on main and gains on p1.

## Tools (tools/)

- `px.py <name> <edits.py> [--base rx/<b>/m.ll]`: post-opt llc oracle (edits as (old,new) pairs or callables).
- `ed.py`: `via_slot(var, keep, ty)` (store at def, load per use) and `remat(var, keep)` (recompute a gep per use).
- `screen1_edits.py`: the edit set above (b1, g1-g3, s1, sb, ns, nl, fu84). `screen1.py` runs singles and pairs.
- `segregs.py <fn.bin> [seg...]`: per call segment, l1/l2 matches and the dominant (orig -> variant) register
  pairs. Seg 69 is the TCF.
- `segview.py <fn.bin> <seg> [lvl]`: opcode-level orig/variant diff of one segment. `dump.py <fn.bin|orig> [lo hi]`:
  listing. `regcount.sh`: register def counts in a range.
- `capvar.sh`, `rx.py`, `capraw.py`, `segdiff.py`, `splice.py`, `regpairs.py`, `lst.py`, `cdis.py`, `regions.py`,
  `rec.py`: w14a38's tools, repointed to this lane.
