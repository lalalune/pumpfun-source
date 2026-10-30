# Composed source fixes: measured 40-byte formatter span excess

At main `7e26cbf36c5c0c824e3eb36417ce8a35866f530a`, the local Windows
compiler recipe plus upstream #2168 and #2272 produces a **40-byte** excess
between the original formatter thunk and its actual, normalized-matching
callee. Regenerating the admitted linker selectors for this recipe also
recovers **20 raw window matches**, without losing any normalized or raw
membership. An independent source/cache staging reproduces the entire final
2,665,848-byte compiler output, SHA-256
`c371a6a17694d84be350e07715a69688c29a87e015b6c2a7780b89a56b4fcd3b`.

This packet independently qualifies other contributors' source and recipe
work. It introduces no program-source change:

- [#2168](https://github.com/lalalune/pumpfun-source/pull/2168),
  `a7135a6a64c446166895f7e3ea4ca84ac1a9b848` to
  `b588742e5bce9b00c7774fe676c0f75bc3bd557e`: removes the extra rent wrapper
  and changes helper/handler order. Its complete source patch is retained.
- [#2272](https://github.com/lalalune/pumpfun-source/pull/2272),
  `2b8582135d33f498db4c30d8309447573baebb9c` to
  `fcce9275e35c1cb6685a83c40d70b84c9caa91fd`: the labeled-block V3 source
  fix, credited to lane `w7r1-v3buycosts-blockorder`.
- Merged [#2251](https://github.com/lalalune/pumpfun-source/pull/2251): the
  unmodified selector generators and admitted linker wrapper, pinned at the
  main revision above. Only the offline map's Windows path separators are
  converted to slashes before its basename parser reads the map.

The broader source integration in
[#2288](https://github.com/lalalune/pumpfun-source/pull/2288), observed at
`115f62966fc085ac1b5538e062d84d84697e13f9`, was reviewed and is not duplicated.
It reports stronger native results with additional source contributions.
The gains here are against the prior **Windows default-link diagnostic
recipe**, not a claim to improve on that native integration or native main.

Publication-time review found main had advanced to
`98dc07311db3e305030c448c70c9b1fa23015a5f`: #2287 improves exact-quote code
and #2346 merges the V3 labeled-block mechanism. The contribution rules and
link recipe did not change in that delta. Those newer source inputs were
reviewed but not compiled in this packet; the measurements below remain
pinned to `7e26cbf` plus the two recorded patches. Do not transfer their
hashes or residual sizes to the newer main.

## Compiler results

All counts cover the same 1,035 original windows. The formatter endpoint is
selected by the complete original 1,088-byte normalized callee, not an
arbitrary alias with the same normalized thunk bytes.

| Retained output | Normalized / raw | Bound start -> end | Span excess | `.text` excess |
| --- | ---: | --- | ---: | ---: |
| 01 current, diagnostic default link | 1,027 / 273 | `0xa820 -> 0x1a27e8` | +640 B | +568 B |
| 02 current, literal native selectors; rejected | 1,027 / 140 | `0xafe8 -> 0x1af770` | +51,776 B | +568 B |
| 03 #2168 + #2272, diagnostic default link | 1,028 / 273 | `0xa908 -> 0x1a25d8` | -120 B | +40 B |
| 07 current, regenerated Windows selectors | 1,027 / 293 | `0xa780 -> 0x1a27e8` | +800 B | +568 B |
| 08 #2168 + #2272, regenerated Windows selectors | **1,028 / 293** | **`0xa868 -> 0x1a25d8`** | **+40 B** | **+40 B** |

The original interval is `0xa868 -> 0x1a25b0`, 1,670,472 bytes. Both its
partition and the final candidate contain 788 physical functions, with no
unaccounted gaps. The final thunk starts at the original address but still
does **not** match raw bytes: its actual callee remains 40 bytes too far away.

The previous packet's `624 - 512 = 112` was an explicitly unbuilt arithmetic
estimate. The full #2168 patch also moves a 232-byte account-name helper and
other bodies. The measured default-link composition is -120 bytes; after
regenerating the U/D order it is +40 bytes. Neither number follows from
subtracting only the wrapper size.

The only normalized membership gained is V3 `0x80df8`. All 17 of its actual
direct callees match complete original normalized bodies at matching offsets.
All three V2 rent calls now reach the matching 416-byte body, whereas the
controls call the mismatching 512-byte wrapper. These are one-hop static
checks, not runtime equivalence. `MEMBERSHIPS.json` and `VERIFICATION.json`
retain the exact gained/lost sets; equal counts do not imply equal members.

## Seven remaining bodies account for the net 40 bytes

There are 781 shared complete normalized-body classes by multiplicity,
seven missing original bodies totaling 112,912 bytes and seven extra
candidate bodies totaling 112,952 bytes. `RESIDUALS.json` retains complete
addresses, sizes, symbols and normalized hashes.

| Original body | Original bytes | Candidate bytes | Difference |
| --- | ---: | ---: | ---: |
| create_v2 execute `0x1e7c0` | 15,576 | 15,584 | +8 |
| admin_cto `0x22a10` | 27,400 | 27,344 | -56 |
| swap_hop `0x5b3b0` | 18,584 | 18,544 | -40 |
| sweep `0x72810` | 7,832 | 7,880 | +48 |
| buy_handler `0x13b9b8` | 15,480 | 15,512 | +32 |
| exact_quote_in `0x13f630` | 20,184 | 20,216 | +32 |
| tradebuy_exact_quote `0x1489f8` | 7,856 | 7,872 | +16 |

Positive and negative size errors cancel. Matching the net size alone would
not establish any of these bodies' normalized or raw identity. Review the
existing source lanes and #2288 before attempting a new fix.

## Recipe qualification and rejected evidence

Only 145 of 553 exact selectors from the literal upstream native script
occur in the retained Windows image. Applying it here loses 133 raw matches
and gains none; output 02 is rejected and retained. This demonstrates a
metadata mismatch in this local recipe, not a defect in the upstream native
recipe. Regeneration produces 554 current / 555 combined selectors, including
the catch-all selector. No rodata or data reordering is added.

The Windows PE launcher in `LinkBridge.cs` forwards arguments and output to
the unmodified upstream Python linker wrapper. Its seven-sample argument
roundtrip passes. Outputs 05/06 enable this bridge with the default script
and a link map, and are whole-file identical to 01/03 respectively. The
current/combined scripts regenerate byte-identically in a separate offline
run. Their **CRLF bytes are intentional pinned compiler inputs**.

Root CGU object bytes remain identical across link-only variants and the
independent final repeat. Whole root `.rlib` bytes do not: only `lib.rmeta`
differs. `archive-comparison.json` and the verifier check this boundary; the
cause of metadata differences has not been established.

Failed preparation is preserved: a C# path-parsing error produced no launcher;
the first successful launcher failed a stdout-forwarding probe; and an early
verifier passed raw CRLF text to script admission instead of using upstream's
universal-newline reading. The final launcher and verifier correct these
issues without modifying compiler outputs. An early validation runner also
incorrectly assumed identical source path sets; #2168 deletes
`util/account_name.rs`. Complete source-patch replay now checks that deletion.

## Replay and limits

`SUMMARY.json` pins eight compiler outputs (five unique), original capture,
inventory and root archives. `PRODUCTION.json.gz` contains commands, source
and dependency inputs, compiler-module/sysroot inventories, before/after
checks and results. Logs, linker receipts, controllers and generator reports
are retained separately. The tracked ledger snapshot has 1,166 rows; Windows
cannot use the shared POSIX live ledger, so schema-valid local rows accompany
this packet. No claim of a shared live reservation is made.

With those external retained images/caches and the eight exact harness files
listed in `review.json`, run from a checkout containing this packet:

```text
python -I -B reconstruction/pump-main/lanes/startrack3r-rent-call-binding/combined-span/verify_combined.py --images /path/to/retained-builds --original /path/to/deployed.so --inventory /path/to/functions.tsv --harness /path/to/pinned-harness --work /path/to/new-replay-output
```

Normal Python, optimized Python and a relocated minimal packet produce the
same report. The independent census agrees on every membership of all five
unique images. A wrong-callee negative fixture leaves normalized V3 bytes
unchanged but is rejected. Exact upstream source patches replay to the full
compiled source inventory. Script regeneration and input/log checks pass.
Eight root rustc commands succeeded; three host C# compiler commands include
one failure. No dependency compiler or target/VM execution ran this increment.

The compiler/linker outputs are unpatched, unpadded and kept outside Git.
The 10,485,715-byte original is an allocation capture, not a same-sized raw
compiler output. Original bytes are used for offline order calibration and
verification, never as compiler/linker input. This is a qualified local
Windows recipe with retained caches, not a clean-machine native bootstrap,
historical source/compiler authentication, whole-program raw identity,
behavioral equivalence, completeness or security claim.
