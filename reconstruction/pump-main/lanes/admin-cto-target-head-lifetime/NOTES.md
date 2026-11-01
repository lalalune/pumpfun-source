# admin_cto target-head lifetime (shim track)

Target: Pump Main window `0x22a10`, 27,400 bytes. Baseline: main `8827554121996bfad7f7db05f292f100332efdc9`.

The validation target now uses separate `MaybeUninit<[u8; 7]>` and `MaybeUninit<[u8; 25]>` buffers. This allows the non-holder branch to end only the head lifetime while preserving the tail. The non-holder head is copied before `t.to_bytes()` initializes the tail source; this preserves the required head-first copy through SROA and MemCpyOpt. A single 32-byte output is fully reconstructed before `assume_init`.

All error source lines remain unchanged (772 physical lines). Copy ranges are bounded within distinct allocations; both success arms initialize all 32 bytes, and error paths return before reconstruction. No target machine code, instruction arrays, or assembly are embedded.

| Measure | Fresh main | Candidate |
| --- | ---: | ---: |
| Normalized aligned instructions | 2346 | 2347 |
| Normalized instruction similarity | 0.702605571 | 0.702905061 |
| Raw aligned instructions | 2225 | 2226 |
| Same-offset raw equal bytes | 13978 | 13978 |
| Same-offset raw equal 8-byte slots | 229 | 229 |
| Exact normalized / raw windows | 1034 / 1034 | 1034 / 1034 |
| Window bytes | 27400 | 27400 |

Both `losses` and `raw_losses` are empty. The candidate changes 30 bytes across 18 instructions, exclusively target-fragment stack offsets. Aligned instructions at original window-relative offsets `0xac0` and `0x14a0` gain matches; `0x19c0` loses one, for a net gain of one. Positional equality counts are unchanged. `admin_cto` is still not byte-for-byte exact.

Validation: identity-recipe standard build with no stack warnings; full `reconstruction/harness/score.py` against the fresh main build; unchanged 154 internal and 3 unresolved external calls; 388 signed synthetic differential cases with zero mismatches. Independent host Miri checks passed 5,056 comparisons using the extracted validation bodies, with transparent key/error models and identity/no-op compiler intrinsics. These checks cover Rust memory accesses and validation results; LLVM lifetime coloring and complete Anchor behavior are covered separately, not by Miri.

Source input SHA-256: `3c027e74d34e8bd6f0aefee7d96bd51bb3867df00333d5a758f85e612c6a3d9c`.
Unstripped SHA-256: `5b6c579950b0fe89bdcf9ea0d57fd41cfb4d0d1d3d38b8f540819c4cb9d85691`.
Stripped runtime candidate SHA-256: `8616f77dcfffc96ba47710fa8a5783779d066a5531185c2cdf85d4963b31b1a2`.

Reproduce by building the baseline and candidate with `reconstruction/harness/fastbuild.py --src programs/pump --work <separate-work> --out <separate-out>`, scoring each unstripped output with `score.py` (candidate uses `--baseline <main-score.json>`), then running `target_metric.py <unstripped.so> 0x22a10 --sym 'admin_cto::execute$'` and `scripts/pump_admin_cto_differential.py --candidate <candidate.so> --output <report.json>`.
