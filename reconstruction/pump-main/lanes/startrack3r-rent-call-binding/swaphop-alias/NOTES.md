# Exact-size swap-hop composition and the raw-match tradeoff

On pinned main `80393778f840329d65de1783f1b6e8e94c2bfa1a`, composing
the initial [#2403](https://github.com/lalalune/pumpfun-source/pull/2403)
Context parameter with three hints from
[#2387](https://github.com/lalalune/pumpfun-source/pull/2387)
restores swap-hop's original **18,584-byte size**. This qualified Windows
recipe gains **10 raw memberships**, from 335 to 345, without losing any
of the 1,031 normalized memberships or existing raw memberships.
The target itself remains neither normalized nor raw matched.

| Source variant | Swap-hop bytes | Instruction ratio | Normalized / raw | Bound formatter span delta |
| --- | ---: | ---: | ---: | ---: |
| Fresh pinned main | 18,544 | 0.73320 | 1,031 / 335 | -96 B |
| Initial #2403 Context only | 18,600 | 0.83042 | 1,031 / 335 | -40 B |
| Context + three hints | **18,584** | **0.83472** | **1,031 / 345** | **-56 B** |
| Above + `const NO_FEE` | 18,608 | 0.83636 | 1,031 / 335 | -32 B |

The last variant improves ratio and total span size but loses all ten raw
gains relative to the exact-size variant. It is retained as rejected evidence
for this composition. A smaller total span difference is not sufficient to
select a reconstruction: positive and negative body-size errors can cancel.
All four variants use the same previously qualified Windows linker input.
These are local Windows measurements, not the native scores reported upstream.

## Source attribution and current upstream work

`composition.patch` applies to the exact LF source at the pinned main revision.
Context source is from #2403 head
`baff84df87dee976ec7a174f48292612fde4d968`. The three composed mechanisms
are `require_gt!`, reading `base_out` from `post_fill` instead of carrying a
separate tuple member, and removing the redundant buyback-zero guard. Credit
belongs to #2387 and its source lanes
[#2368](https://github.com/lalalune/pumpfun-source/pull/2368) and
[#2366](https://github.com/lalalune/pumpfun-source/pull/2366).
The two stale `pay_out_native_owned` reversions in #2387's base/head diff are
explicitly excluded. Whole-file line count and current owned helpers remain intact.

During this run #2403 advanced to
`91ee46c8dcdd6c875089f284398c77f87864c7db`, adding all four hints and a scoped
user key. That author's notes report 18,640 bytes and 948 native raw matches,
explicitly explaining that swap-hop's +56 B cancels admin-CTO's -56 B.
We did not build that later source or transfer its scores to this recipe.
This packet contributes the independently repeated, exact-size three-hint
control and the ten-member regression when adding `NO_FEE`; it claims no
new source mechanism and is not a competing program-source PR.

Subsequent duplication review also found
[#2412](https://github.com/lalalune/pumpfun-source/pull/2412), head
`17a9ce06477950e0065e0669bc1027fee5b2959c`. Its 16-subset census already
measured both exact-size controls, including the same three-hint combination
used here. It selected the two-hint form for fewer differing slots. This
packet's contribution is the retained Windows reproduction, ordinary/IR
qualification, complete callee checks and independent repeat; neither the
composition nor its native ten-raw-gain result is new to this lane.
Later #2403 head `8073709c650c7fcd9996ac72220983c1c4929779` reports an
exact-size 0.85352 variant. Neither later source is substituted into the
measurements below, and this packet should not be read as the latest best
swap-hop source proposal.

At publication review, main was
`168232c98d8308e958d1040339ed8f3d54c93f9d`. It includes #2397's V3 exact-quote
match. The only changed Pump source since our compiled base is `trade_v3.rs`.
That later main was not compiled here. Its normalized count must not be
inferred from this packet's 1,031 measurement. Review/pins are in
`PUBLICATION-REVIEW.json` and `review.json`.

## Compiler and IR qualification

Seven successful offline root rustc commands: four IR-emitting source variants,
ordinary-link baseline and exact-size variant, and a separately staged ordinary
repeat. No dependencies or host tools were rebuilt; no target/VM was executed.
The ordinary exact-size output and independent repeat are byte-identical:

`e91a702c9a38782292f15adba015aab918e8a850e8f874061e854b1a3cc7f70c`

Both are 2,665,720 bytes, copied unchanged from rustc's destination. No patching,
padding or stripping is applied to the measured output. The 10,485,715-byte
original is an allocation capture, not an equivalent raw compiler-output file.

Adding `llvm-ir` emission changes whole-output hashes and `.symtab`/`.strtab`.
For both baseline and selected variant, all seven allocated sections have
identical contents, addresses, offsets and sizes across the two emit modes,
including `.text`, `.rodata`, `.data.rel.ro` and `.rel.dyn`. Full memberships
also agree. This qualifies these IR probes; it is not a general claim that
IR instrumentation is artifact-neutral. See `emit-comparison.json`.

The baseline IR accounts parameter has `noalias`. The Context variants have
the promoted `ptr readonly %ctx.8.val, i8 %ctx.34.val` pair, without accounts
`noalias`, while the `h` parameter retains it. This is consistent with the
upstream ArgumentPromotion explanation. Complete target IR bodies and full
IR hashes are retained; generated IR is evidence, not edited compiler input.

All 107 actual direct callees have the same multiset of complete normalized
callee bodies as the original, and the single syscall's instruction bytes
match. This does not establish matching call order or behavior. A mutated
callee fixture preserves the target's normalized bytes but fails the multiset
check. The selected target still has 1,657 differing normalized 8-byte slots.

The complete bound formatter interval has a 56-byte deficit. Swap-hop now
has its original size; admin-CTO's net size deficit is 56 bytes. Equal size
does not resolve the other unmatched bodies, and admin-CTO itself can contain
offsetting internal differences. Do not pad this residual.

## Replay and retained failures

The verifier reads external retained outputs, original allocation capture,
inventory and pinned harness. It needs this directory plus sibling
`verify_rent_edges.py` and runs without compiler, VM or network access:

```sh
python -I -B verify_alias.py --images /path/to/pump-swaphop-alias \
  --original /path/to/deployed.so --inventory /path/to/functions.tsv \
  --harness /path/to/harness --work /new/replay-directory
```

Official and independent census agree on all 1,035 memberships for all seven
outputs. Normal, optimized-Python and minimally relocated verifier reports
are identical. The source patch replays to the complete selected source tree
byte for byte with `git -c core.autocrlf=false apply`. Production inventories,
commands, logs, linker receipts, metrics, members and validation are retained.
Compiler/sysroot/dependency inputs were checked unchanged before/after builds.
This uses retained Windows v1.44 inputs with a Linux-target sysroot; it is not
a clean-machine or native bootstrap, historical-source authentication, runtime
equivalence, whole-original raw identity, completeness or security claim.

Two linker-generator attempts incorrectly supplied already-ordered maps,
contrary to `genld.py`'s default-order input requirement. They emitted 414
selectors and failed the expected-script check; neither output was compiled.
`GENERATOR-FAILURES.json.gz` preserves them. The used 555-selector script
remains the earlier qualified input, hash
`72ef693c883fb68e9939f408f785f230742cb533b30cbf1321719d4852123569`.
No fresh default-map regeneration is claimed. The first verifier prototype
also failed because Python tuple call counts were compared directly with JSON
lists; its source/log are retained and the corrected verifier compares the
serialized metric representation. No compiler result was changed by that fix.

The tracked ledger snapshot contains 1,166 rows; the shared POSIX live ledger
is unavailable here. Local attempts are retained. The earlier proposed raw
pointer experiment was cancelled before code or compilation when #2403
supplied the ordinary-Rust source spelling. No raw-pointer trial was run.
