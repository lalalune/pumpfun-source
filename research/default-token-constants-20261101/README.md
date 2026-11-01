# Token-program constants in the maintained signature CLI

The current `bytecode_signatures.py` CLI still compares an LDDW immediate with
the scalar values 3, 7 and 12, then labels a match `spl_token_instruction`.
Its default report contains no token rows on the three retained inputs. Those
scalars do not identify the 32-byte Tokenkeg or Token-2022 program address.

This integrates [harrywu666's accepted correction #1159](https://github.com/lalalune/pumpfun-source/pull/1159)
into the maintained CLI. The original research packet and its
[reviewed binding #2540](https://github.com/lalalune/pumpfun-source/pull/2540)
remain unchanged. This is a current-consumer integration, not a new discovery
or a replacement of the archived proof.

The detector joins four consecutive complete LDDW immediates in one window and
requires an exact 32-byte match. Stores and other instructions may separate the
loads. Any relocated load invalidates its four-load group; it is not removed
from the sequence to join unrelated chunks. The existing callable name,
`detect_token_transfer_patterns`, and report keys `tokens`/`token_patterns`
remain available. New rows are explicitly `token_program_constant`, with the
program label, bytes and four-load count. These are static constant sequences;
they do not establish a transfer, CPI, runtime reachability or source identity.

## Retained-input result

| Default program | Windows | Before rows | After rows | Windows with constants |
| --- | ---: | ---: | ---: | ---: |
| Pump | 1,035 | 0 | 4 | 4 |
| PumpSwap | 785 | 0 | 2 | 2 |
| Mayhem | 441 | 0 | 20 | 10 |

The complete CLI and its generated verifier pass before and after. A direct raw
instruction walk checks all 2,261 report windows and agrees with the accepted
detector on all 26 constants. Pattern rows, signature counts and summary counts
agree. Every unrelated report field remains identical, including account
comparisons, CPI/error/serialization patterns, shared signatures and n-grams.
The comparison excludes only token rows/counts, the token description in the
generated README, and the manifest hashes that depend on those files.

An official v1.44 `llvm-objdump` confirms the first Pump sequence at
`0x4b10`, `0x4b28`, `0x4b40`, `0x4b58`: four Tokenkeg chunks separated by
stores. The input bytes and all 19 files in the historical token/terminal-error
packets remain unchanged. Fees is part of the historical packet's four-program
corpus but is not added to this CLI's three-program selection.

The same token change was also composed independently with the register-comparison
fix in [#3903](https://github.com/lalalune/pumpfun-source/pull/3903), at head
`56b38a4da4baaf48e842091640259daf8d206431`. Its complete before/after CLI
reports preserve every non-token field, and its signature regression passes.

## Reproduce

From the repository root, using fresh output paths:

```sh
python -B research/default-token-constants-20261101/probe.py --repo . --revision 1647da0f22312730b2e6b3eec7a468d9d3d89041 --expect base --output work/token-before.json
python -B research/default-token-constants-20261101/probe.py --repo . --expect fixed --output work/token-after.json
python -B tests/test_default_token_constants.py
python -B tests/test_bytecode_signatures_lddw_boundaries.py
```

The probe stages complete production modules and unchanged retained captures in
an owned temporary tree. It runs the actual CLI and generated verifier, not a
patched detector in a test double. `results.json` records compact receipts;
the full 26 raw witnesses are emitted by the probe. Witness lists are hashed
as UTF-8 JSON with sorted keys and compact separators `(',', ':')`.

The five new tests cover both exact addresses, partial/wrong/scalar values,
window and EOF boundaries, relocated chunks, no bridging across relocated loads,
and the complete retained-input CLI. Existing logical-boundary tests retain a
full four-chunk positive control. The existing `tests/` discovery runs them in CI.
No program, native model, VM, compiler or network operation is executed by this
proof, and no captured artifact is rewritten.
