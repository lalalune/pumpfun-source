# w17a36-cto-stitch18: wave-17 integrator for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Shim track.
Continues w17a18-cto-stitch17 (#4075, branch `origin/swarm/w17a18-cto-stitch17-5`). Base: main 53ec7fb53 for the
leave-one-out (LOO) table, then main 70b3b637a (#4107, w17a33 drift peel, byte-identical: same admin_cto bytes,
sig `61dcfe87f489`, M 2,295 @27,400, oracle slots 3,095). Ledger approach `stitch18`, keys
`0x22a10-w17-<main7>-stitch18-<capture>-v1`.

`M` = masked difflib match count of measure.sh (ratio = 2M / (6676 + (bytes - 27400)/8)); every number below is the
slim pre-opt oracle (`tools/cap.py`: capraw + preslim + fx, survivor list `surv-1647da0.txt`), which reproduces main
exactly on both bases (m0k on 53ec7fb and m070 on 70b3b63: M 2,295 @27,400, sig `61dcfe87f489`).

## 1. Leave-one-out table on 53ec7fb, completed (all 62 genes of `tools/loo.py 50`)

w17a18 priced 41 of the 63 genes; this lane priced the remaining 21 (all w14-era partial reverts). Result: no revert
gains, and no revert is byte-identical except the two known non-shim ones (`loo4025` re-adds the #3985 clone that
#4025 peeled; `loo3993p1` is the `sweep(&ctx,holder_key)` borrow). Compile errors are partial reverts that drop a
helper declaration still used by a later landing (expected, not a result).

| gene | landing | result (M @bytes, vs main 2,295 @27,400) |
| --- | --- | --- |
| `loo4053` | w17a18-cto-stitch17-4 | 2294 @27400 (dM -1, dB +0) |
| `loo4053_0` | w17a18-cto-stitch17-4 | 2295 @27392 (dM +0, dB -8) |
| `loo4053_1` | w17a18-cto-stitch17-4 | 2294 @27408 (dM -1, dB +8) |
| `looaab087f` | #4054 | 2292 @27400 (dM -3, dB +0) |
| `loo4040` | w17a19-shim-lifetime | compile error: error[E0425]: cannot find function `lte` in this scope |
| `loo4040_0` | w17a19-shim-lifetime | compile error: error[E0425]: cannot find function `lte` in this scope |
| `loo4040_1` | w17a19-shim-lifetime | 2292 @27400 (dM -3, dB +0) |
| `looa51791e` | #4037 | 2294 @27400 (dM -1, dB +0) |
| `loo4026p0` | w17a15-shim-passthrough-2 | 2294 @27392 (dM -1, dB -8) |
| `loo4026p2` | w17a15-shim-passthrough-2 | 2291 @27424 (dM -4, dB +24) |
| `loo4025` | #3985 w17a18-cto-stitch17-3 | 2295 @27400 (dM +0, dB +0) byte-identical |
| `loo4025_0` | #3985 w17a18-cto-stitch17-3 | 2295 @27400 (dM +0, dB +0) byte-identical |
| `loo4025_1` | #3985 w17a18-cto-stitch17-3 | compile error: error[E0425]: cannot find function `rcincq` in this scope |
| `loo4019p1` | w17a18-cto-stitch17-2 | 2288 @27408 (dM -7, dB +8) |
| `loo4018p0` | w17a15-shim-passthrough | compile error: error[E0425]: cannot find function `pt1` in this scope |
| `loo4018p1` | w17a15-shim-passthrough | 2295 @27392 (dM +0, dB -8) |
| `loo4018p2` | w17a15-shim-passthrough | 2293 @27408 (dM -2, dB +8) |
| `loo4018p4` | w17a15-shim-passthrough | 2290 @27400 (dM -5, dB +0) |
| `loo4017p0` | w17a18-cto-stitch17 | 2294 @27408 (dM -1, dB +8) |
| `loo4011` | w17a08-shim-sscorder | 2293 @27400 (dM -2, dB +0) |
| `loo4000` | w17a13-shim-pool-gate | 2294 @27400 (dM -1, dB +0) |
| `loo3993p1` | w17a09-shim-pdaslot | 2295 @27400 (dM +0, dB +0) byte-identical |
| `loo3992` | w17a06-shim-irbeam-2 | 2288 @27400 (dM -7, dB +0) |
| `loo3992_0` | w17a06-shim-irbeam-2 | 2294 @27408 (dM -1, dB +8) |
| `loo3992_1` | w17a06-shim-irbeam-2 | 2289 @27392 (dM -6, dB -8) |
| `loo3991` | w17a04-shim-unlockra | 2292 @27400 (dM -3, dB +0) |
| `loo3991_0` | w17a04-shim-unlockra | compile error: error[E0425]: cannot find function `aiclone_r` in this scope |
| `loo3991_1` | w17a04-shim-unlockra | 2292 @27400 (dM -3, dB +0) |
| `loo3974p0` | w16a17-cto-stitch16 | compile error: error[E0004]: non-exhaustive patterns: `None` not covered |
| `loo3974p1` | w16a17-cto-stitch16 | 2288 @27392 (dM -7, dB -8) |
| `loo3969` | w17a04-shim-unlockra | 2281 @27392 (dM -14, dB -8) |
| `loo3969_0` | w17a04-shim-unlockra | compile error: error[E0425]: cannot find function `rcincp` in this scope |
| `loo3969_1` | w17a04-shim-unlockra | 2281 @27392 (dM -14, dB -8) |
| `lood4dfb04p0` | #3934 | compile error: error[E0425]: cannot find function `expect_p` in this scope |
| `loo3950` | w17a04-shim-unlockra | compile error: error[E0425]: cannot find function `assume` in this scope |
| `loo3950_0` | w17a04-shim-unlockra | compile error: error[E0425]: cannot find function `assume` in this scope |
| `loo3950_1` | w17a04-shim-unlockra | 2289 @27400 (dM -6, dB +0) |
| `loo2c47082` | #3936 | 2295 @27400 (dM +0, dB +0) |
| `loo3859p1` | w16a07-cto-sweeptuple | compile error: error: this file contains an unclosed delimiter |
| `loo3859p3` | w16a07-cto-sweeptuple | 2287 @27392 (dM -8, dB -8) |
| `loo3480p2` | w14a91-cto-curvestorereg | 1992 @27272 (dM -303, dB -128) |
| `loo3480p3` | w14a91-cto-curvestorereg | 1828 @27296 (dM -467, dB -104) |
| `loo3437p0` | w14a86-cto-t1vaultname | compile error: error: this file contains an unclosed delimiter |
| `loo3437p3` | w14a86-cto-t1vaultname | compile error: error[E0425]: cannot find value `nf` in this scope |
| `loo3437p4` | w14a86-cto-t1vaultname | 2284 @27376 (dM -11, dB -24) |
| `loo3430p1` | w14a88-cto-sweeptagmem | 2288 @27408 (dM -7, dB +8) |
| `loo3409p0` | w14a82-cto-walletweight | compile error: error[E0599]: no method named `unwrap_or` found for type `bo |
| `loo3409p1` | w14a82-cto-walletweight | compile error: error[E0308]: mismatched types |
| `loo3393p2` | w14a72-cto-rescan304 | 2287 @27416 (dM -8, dB +16) |
| `loo3386` | w14a66-cto-feeedge | 2266 @27400 (dM -29, dB +0) |
| `loo3386_0` | w14a66-cto-feeedge | 2272 @27392 (dM -23, dB -8) |
| `loo3386_1` | w14a66-cto-feeedge | 2287 @27408 (dM -8, dB +8) |
| `loo3361p1` | w14a53-cto-stitch11 | 2288 @27408 (dM -7, dB +8) |
| `loo3361p2` | w14a53-cto-stitch11 | compile error: error[E0425]: cannot find value `amm_present` in this scope |
| `loo3379p1` | w14a64-cto-shiftpair | 2287 @27408 (dM -8, dB +8) |
| `loo3372p0` | w14a43-cto-tcfrescan-4 | 2288 @27408 (dM -7, dB +8) |
| `loo3369p0` | w14a55-cto-ifletrepay | compile error: error: this file contains an unclosed delimiter |
| `loo3369p1` | w14a55-cto-ifletrepay | 2288 @27392 (dM -7, dB -8) |
| `loo3358p0` | w14a50-cto-frozenrepay | 2282 @27376 (dM -13, dB -24) |
| `loo3358p1` | w14a50-cto-frozenrepay | 2176 @27456 (dM -119, dB +56) |
| `loo3354` | w14a43-cto-tcfrescan-3 | 2293 @27400 (dM -2, dB +0) |
| `loo3315p2` | w14a33-cto-nativejoin | 1997 @27368 (dM -298, dB -32) |

Summary of the near-tie knobs on main (unchanged by #4107, see section 2): free -8 B at 0 M are `loo4053_0`
(the 284 placeholder) and `loo4018p1` (the 298 `pt1`), plus the two #4026 `ptp(23)`/`ptp(24)` accounts-pointer
passthroughs (w17a33 IR knobs, no LOO gene because #4026's line also carries other edits); `loo4026p0` (the 312
compare-byte `pt8`) is -1 at -8 B; `loo2c47082` (the #3936 sweep program-clone owner pin) is a tie with different bytes.

## 2. Knobs as source genes on 70b3b63

| capture | genes | M @bytes | note |
| --- | --- | --- | --- |
| m070 | main 70b3b63 | 2,295 @27,400 | sig 61dcfe87f489 = 53ec7fb |
| n_K4 | K284 + K298 + K339a + K339b | 2,295 @27,368 | the four free knobs are additive in source too (w17a33 found it in IR) |

`K284` removes the 284 `holder_key` placeholder, `K298` the 298 `pt1(3,new.is_some())`, `K339a` the `ptp(23,..)` on the
shared owner test, `K339b` the `ptp(24,..)` on the CtoState `max_fee` load (`tools/genes17.py`).

## 3. w17a29 foje (single fee-tag phi, 2,294 @27,432) x the knobs

foje is the original's single fee-tag phi plus a 1:2000 native-quote weight (w17a29 #4100): 1 M below main at +32 B.
The four knobs are exactly 32 B, so foje + knobs was the obvious size-complementary set.

| capture | genes | M @bytes | note |
| --- | --- | --- | --- |
| f_E | foje | 2,294 @27,432 | reproduces w17a29 (sig 154401cd6e4c) |
| f_E1_298 | foje + K298 | 2,294 @27,424 | free on foje |
| f_E2_284_298 | foje + K284 + K298 | 2,294 @27,416 | free on foje |
| f_E1_339a | foje + K339a | 1,873 @27,384 | collapse (w17a29's tail-dup/MBP basin) |
| f_E1_339b | foje + K339b | 1,875 @27,384 | collapse |
| f_EK4 / f_EK4P | foje + all four (+ #3936 pin peel) | 1,875 @27,360 / 1,883 @27,392 | collapse |
| f_EK3_* / f_CK3_* | foje or foce + any three knobs | 1,873-1,875 | collapse whenever K339a or K339b is in |

So on foje the two `ptp(23)`/`ptp(24)` passthroughs are load-bearing (they keep it out of the collapse basin), and only
16 of the 32 B are free.
