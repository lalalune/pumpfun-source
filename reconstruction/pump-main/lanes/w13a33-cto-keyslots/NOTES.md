# w13a33-cto-keyslots: the original's holder_key copy at -0x518 (sk at -0x470) is real but loses 0.045-0.06

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a22-cto-valslot (#2989, notes #2999). Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a33-cto-keyslots/`
(not in git). Ledger keys: `0x22a10-w13-d81d0f5-keyslots-*`, `0x22a10-w13-a6412c2-keyslots-*`.

No source change. This is a notes-only result: the angle is exhausted.

## The residual

The original stores the sharing_config key copy (`sk`) at `[r10-0x470..-0x458]` (orig 0x22f58-0x22fa0), then
copies holder_key (`[r10-0x6a0..-0x688]`) to `[r10-0x518..-0x500]` unconditionally (orig 0x22fa8-0x22fe0). Validate's
holder arm (orig 0x234c8-0x234f8) and the `t==holder_key` compare read that copy. Ours puts `sk` in the
`authority_info.i` group at 0x518, makes no copy, and validate's error to_string scratch lands at -0x470/-0x4b8
instead of the original's -0x4d0/-0x488.

## Step 1: IR oracle (`tools/hkc.py`)

`tools/hkc.py <m.ll> SPEC...` is a post-opt llc oracle on rx.py's slimmed `m.ll`. Item `hkc[:POS[:LT]]` adds a
32 B alloca `%hkc` before alloca POS (or END/TOP). It memcpys holder_key into it right after the `sk` memcpy and
ends its lifetime with LT's (default `sk`). `cmp` makes validate's memcmp read `hkc`, `arm` makes the holder-arm
target pieces read it, and w13a22's `mv:A:B` / `nolt:A` items also work. `RM=1` deletes each trial dir.

| main | spec | ratio | bytes |
| --- | --- | ---: | ---: |
| d81d0f5 (0.57100) | main | 0.57100 | 27,400 |
| d81d0f5 | `hkc:sk,arm,cmp` (hkc before sk: **sk -0x470, hkc -0x518, the original's slots**) | 0.54314 | 27,312 |
| d81d0f5 | `hkc:END,arm,cmp` (sk -0x518, hkc -0x470) | 0.54254 | 27,312 |
| d81d0f5 | best of 1,283 single moves/nolt on `hkc:sk,arm,cmp` (`mv:target.i.sroa.0:END`) | 0.55364 | 27,312 |
| a6412c2 (0.59197) | `hkc:sk,arm,cmp` | 0.53323 | 27,312 |
| a6412c2 | `hkc:sk,arm,cmp,mv:target.i.sroa.0:END` | 0.54374 | 27,312 |

With `hkc` before `sk`, stack coloring puts `hkc` in `authority_info.i` (0x518) and `sk` in `_112.i` (0x470), exactly
the original's offsets. Validate's error scratch moves to the original's -0x4d0/-0x488, and the spill area grows to
109 slots (0xc38, the original's count). With `mv:target.i.sroa.0:END` the named frame (0x440-0x700) equals main's.
It still loses 0.045-0.06.

## Step 2: source forms (raw-IR capture + rx oracle; scores equal build tokens)

| trial | form | main | ratio | bytes |
| --- | --- | --- | ---: | ---: |
| v1 | `validate(..,holder_key:Pubkey,..)`, call passes `holder_key` | d81d0f5 | 0.54314 | 27,312 |
| v2 | `args=&(new,holder_key)`, validate gets `&args.1` | d81d0f5 | 0.50449 | 27,496 |
| c1 | v1 + payer-first TransferCreatorFeesToPumpV2 (w13a29 m1, alone 0.58811 @27,424) | d81d0f5 | 0.54229 | 27,336 |
| c2 | v1 + payer-first + validate reads `args.0` | d81d0f5 | 0.51610 | 27,408 |
| c3 | v1 + validate reads `args.0` | d81d0f5 | 0.51595 | 27,424 |
| c4/c5 | v1 + plain holder_key PDA (`let (holder_key,_)=..` / `..find_program_address(..).0`) | d81d0f5 | 0.52213 | 27,312 |
| f3 | holder_key and sharing both by value | a6412c2 | 0.53233 | 27,312 |
| f4 | sharing by value only (no copy) | a6412c2 | 0.52696 | 27,400 |
| pf2 | payer-first alone on the new clone literal | a6412c2 | 0.53631 | 27,424 |
| pf2v | pf2 + v1 | a6412c2 | 0.50727 | 27,328 |

- v1 is the hkc oracle exactly (same tokens), so passing holder_key by value is the source form of the original's
  copy. The copy reads `hk` (-0x681) instead of holder_key (-0x6a0), because GVN forwards `holder_key=hk.0`.
  With a plain PDA (c4/c5) it reads holder_key but loses more.
- A tuple carrier, a `#[cold]` carrier or a 33 B MaybeUninit tail are moot. v1 already gets the copy without
  CopyProp forwarding it, and the loss comes from what the copy does to register allocation, not from where it sits.
- f4: `sk` by value becomes a function-scope 32 B slot at 0x678 and pushes hk/holder_key/mint 32 B down.
- payer-first (w13a29's +0.017 lead on d81d0f5) is gone on a6412c2, after the hand-built AccountInfo clone literals.

## Why the faithful copy loses: register allocation, not the metric

- Pasting the original's 8 copy instructions into main's token stream at the copy site raises the ratio
  (0.59197 -> 0.59336), so the scorer is not what punishes the copy.
- main2 -> hkc changes 1,091 instruction lines: 303 differ only in frame offset, 107 only in registers, and 186
  otherwise. Skeleton ratio vs the original (registers and frame offsets masked, `tools/skel.py`) drops
  0.8451 -> 0.8051, while the skeleton of hkc vs main differs in only 155 lines.
- Stack reloads (`ldxdw rX,[r10-..]`): original 537, main 508, hkc 498. The copy lowers register pressure, so
  greedy RA spills less and drops 88 B. The original allocates under more pressure than ours does. The copy is
  real, but whatever else raises the original's pressure has to come with it. That is a regalloc problem, not a
  frame-slot one.

## Frame lever on the latest main (a6412c2, 0.59197)

A single-move scan (145 allocas x 26 anchors + `nolt`, 3,882 edits) found best `mv:target.i.sroa.9:END` /
`mv:target.sroa.8:*` at 0.59227 (+0.0003). Every `sk`, `t.i`, `_112.i` and `authority_info.i` move ties or loses.
`nolt:sk` gives 0.52696 and `nolt:t.i` 0.51797. On d81d0f5, 290 `sk` moves gave at best 0.5713 (+0.0003).
w13a22's "sk gets a lower frame index than t.i" lever no longer exists: t.i is already in the `_92.i` group.

## Tools (tools/)

- `hkc.py`: the holder_key-copy oracle above (wraps w13a22's `px.py`).
- `skel.py <orig.dis> <cand.dis>...`: plain, frame-masked, register-masked and both-masked ratios.
- `regdelta2.py <a.o> <b.o>`: matched-token delta per 0x800 B original region.
- `drift2.py <a.dis> <b.dis>`: where the instruction count of two candidates diverges.
- `edits/`: the source edits (`capvar.sh` EDITS format, w13a23/w13a24).
