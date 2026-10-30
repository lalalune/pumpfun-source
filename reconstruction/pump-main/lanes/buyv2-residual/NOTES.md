# Lane buyv2-residual

Targets (programs/pump/src/buy_v2.rs + v2_native_payments.rs):

- `0x13f630` `buy_v2::buy_exact_quote_in_handler`
- `0x13b9b8` `buy_v2::buy_handler`

Base: origin/main ef40086 (CompleteEvent+prepare helper already merged).

## Baseline (ef40086)

| window | bytes | ratio | calls |
| --- | ---: | ---: | --- |
| 0x13f630 | 20,192 / orig 20,184 | 0.97829 | 130 |
| 0x13b9b8 | 15,488 / orig 15,480 | 0.95334 | 90 |
| official | | 1020 / 188 | no losses |

## Accepted: rent-dual-matched-blackbox

Root cause (same as sellv2 NOTES): in-crate `ensure_rent_exempt` lets DeadArgElim poison the
unused `_size` argument, so call sites omit the original's `mov r2,0` (and the None spill that
reuses it). Using `size` in the callee body fixes callers but loses matched window `0x3b598`.

Fix:

1. Keep `ensure_rent_exempt_matched` with the old body (`minimum_balance(0)`, unused `_size`) so
   window `0x3b598` stays matched.
2. Callers keep calling `ensure_rent_exempt`, whose body uses
   `minimum_balance(black_box(size).wrapping_mul(0))` so DAE cannot poison the arg, while the
   effective rent size remains 0.
3. An unreachable `size == usize::MAX` arm calls the matched twin so it is not DCE'd.

| window | before | after |
| --- | ---: | ---: |
| 0x13f630 | 20,192 / 0.97829 | 20,216 / **0.99351** |
| 0x13b9b8 | 15,488 / 0.95334 | 15,512 / **0.97366** |
| 0x144508 (collateral) | 13,944 / 0.93984 | 13,968 / 0.96294 |
| 0x3b598 | matched | matched (`ensure_rent_exempt_matched`) |
| official | 1020 / 188 | 1020 / 188, no gains/losses vs main's membership |

Unstripped sha256: `8ae6c6a6c92c98f70870586ae737bfc6669fbe1dd162cc64b30efc797529dcdb`.

## Rejected on this base

- helper early-return nonzero reserves (eq 0.874, calls +1)
- shareholders flat three-arm match (eq 0.693)
- Complete emit IIFE closure (eq 0.445; incidental raw 0xa880 Debug::fmt — not accepted)
- `minimum_balance(_size & 0)` / `wrapping_mul(0)` alone (byte-identical; DAE still poisons)
- black_box without matched twin (eq 0.99351 but **loss** of 0x3b598)
- `#[cold]` emit helper (E0382 Context move)
- `core::hint::unlikely` (E0425 on this rustc)
