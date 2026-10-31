# Pump swap_hop residual byte measurement

An independent check of the retained macOS identity-recipe candidate from
source commit `20a1ae9c0f243669f8ffb4633ee017b50f55958e` finds **47 raw and
47 normalized differing bytes** in `multi_hop_curve::swap_hop`. Its function
is 18,584 bytes. The normalized differences form one cluster at original
window offsets `0x29f9..0x2a84`. Full positions and artifact hashes are in
`RESULT.json`.

The source manifest is `4300235deb4eff8541903774bedca0bece9d9261fd7bd92b9dacbd7da7832ccc`.
The unstripped candidate is `8cd7695c3fc638fc8ccfaba49a55b7615421e6f1c4c02f623124d9cc67a8ebf2`;
the stripped candidate is `4eb9dc9e542e9b9a3e3873d10673067d6839a28703e5560fbc795524128830da`.
The analyzed source file is unchanged between that commit and `4cc7946e`.
The retained build artifacts are external to this source packet: its default
checks validate recorded identities and internal consistency; optional candidate
verification remeasures the actual ELF, and optional source-manifest verification
binds the retained build receipt. The current source-file comparison is reported
for information and does not invalidate this historical packet when source advances.

## Reproduce

```sh
python3 research/swap-hop-residual-20261030/test_verify.py
python3 -O research/swap-hop-residual-20261030/test_verify.py
python3 research/swap-hop-residual-20261030/test_verify.py --candidate /path/to/retained/unstripped.so --source-manifest /path/to/retained/source-inputs.json
python3 research/swap-hop-residual-20261030/analyze.py /path/to/candidate/unstripped.so
```

The analyzer requires exactly one named, unstripped `swap_hop` function of the
original size. It reads the candidate at that symbol's address, verifies the
captured original hash and window, and prints raw and normalized differences.
It exits **1 while normalized differences remain**, 0 for a normalized match,
and 2 for rejected inputs. Optional verification accepts only the recorded
candidate hash and recomputes all recorded window values. A normalized match
alone does not establish raw or whole-ELF identity.

The default verifier checks the exact checksum inventory, recorded source and
measurement-tool identities, metadata consistency, malformed-input controls,
and synthetic relocated-function admission. Its checks remain active under
optimized Python.

The recorded `score.sections` identity follows `f49c8e86`, which adds each
section's ELF type to the returned map. The measurement reads only each
section's address, offset and size, which that change leaves unchanged.

The recorded `score.body` identity follows `2c1c1c73a`, `8a59273e2` and
`1225f898e`, which tighten range alignment validation, harden temporary-file
cleanup and pin report line endings. The swap-hop measurement is a single
aligned function range and the recorded numbers are unaffected; only the
checker bytes moved.

## Limits and author-reported work

The original contributor reported a native-Linux candidate with 125 raw and
47 normalized differing bytes, and two source-shape experiments. Those candidate
ELFs, full scores, and experiment receipts are not retained here, so the claims
remain **author-reported and unverified**, separate from the independently
recomputed macOS window measurement.

The contributor interpreted the cluster as instruction scheduling around
`complete_fill`, including a stack-slot interpretation for `&a.fee_config`.
This packet has not independently verified that interpretation from decoded
instructions. The byte positions localize further work; they do not prove
semantic equivalence or rule out source changes. No program source change or
new whole-program completion claim is made.
