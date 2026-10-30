# Current-source composition: 1,031 normalized / 335 raw windows

On main `42babccf82001346f26f020caea38bf63f5c22a2`, composing the credited
source fixes below raises the qualified Windows recipe from **1,029 / 293**
to **1,031 / 335**: two normalized gains and **42 raw gains**, with zero lost
memberships. All 1,035 windows were checked, including by an independent
census. A separate source/cache staging reproduces the entire final
2,665,720-byte compiler output:
`8286c8d7c86e9c44ff51f9b5fa5014536e94aab17c571b12cda3550dd376a2e4`.

This is an independent composition/verification contribution, not authorship
of the upstream source fixes. No `programs/` file is changed by this PR.
The exact selected upstream diffs and rebased composition are retained:

| Contribution | Pinned head | Selected source |
| --- | --- | --- |
| [#2168](https://github.com/lalalune/pumpfun-source/pull/2168), wrapper removal and original placement | `b588742e5bce9b00c7774fe676c0f75bc3bd557e` | Complete program-source diff |
| [#2225](https://github.com/lalalune/pumpfun-source/pull/2225), normalized buy-handler | `8b8ebe7812489ee3bb1792b256a474c82c014eb0` | `buy_v2.rs`, `lib.rs` |
| [#2309](https://github.com/lalalune/pumpfun-source/pull/2309), normalized sweep | `44428ebcb2d3a380b0e82161bc4dcc9eec1774cd` | `sweep_fees.rs` |
| [#2341](https://github.com/lalalune/pumpfun-source/pull/2341), create-v2 at original size | `61ea2e62de1fc541c231c03952dc65ebd95ef8ce` | `create_v2.rs` |

`review.json` records each base, head, selected paths and patch hash. Selecting
these paths avoids older inherited create/trade edits in #2225 and create
edits in #2309. Current main already includes #2287, #2346 and #2347; those
exact-quote/V3 changes are preserved. The first literal #2168 application
failed before compilation because two attributes already exist in main.
`FAILED-PREFLIGHT.json` retains that refusal. Three-way composition retains
current `partial:&bool`, combines the independent buy/program attributes,
and keeps current exact-quote attribute whitespace. `merge-review.json` and
`MERGE-INPUTS.json.gz` expose every conflict input and resolution.

The already-open [#2288](https://github.com/lalalune/pumpfun-source/pull/2288)
was reviewed at `064a4cd846b212ef656dd715d76c083903eff1c2`: its native
integration uses #2313's partial sweep improvement and reports 1,030 / 296.
The newer [#2356](https://github.com/lalalune/pumpfun-source/pull/2356) layout
analysis tests #2168 on an earlier base and explains the extra wrapper's
obstruction. This packet tests a different full composition, with the
normalized #2309 sweep and #2341 create source, on the retained Windows
recipe. It does not claim a native score or duplicate either integration PR.

At publication, upstream reached
`255a0fd2e431627bb01e139aabb51b56eaa0357a`, merging #2348 (the #2225 buy
mechanism), #2309 and #2168. Those maintainer decisions are welcome progress;
the scores here remain tied to the earlier compiled baseline. The cutoff
source comparison is retained in `CUTOFF-REVIEW.json`; it is not a build of
the newer main. The local patch application also produces CRLF source files
under the observed system Git `core.autocrlf=true`. Their exact bytes are
pinned in the compiler inventories and replayed, rather than presented as
byte-identical Git blobs. The cutoff report separately labels newline-only
differences and displays any remaining text difference with line endings
normalized for readability only.

## Measured outputs

| Output | Normalized / raw | Bound formatter span difference | `.text` difference |
| --- | ---: | ---: | ---: |
| 01 fresh main, diagnostic default order | 1,029 / 273 | +576 B | +504 B |
| 02 fresh main, regenerated Windows order | 1,029 / 293 | +736 B | +504 B |
| 06 composition, diagnostic default order | 1,031 / 315 | -256 B | -96 B |
| 04 composition, regenerated Windows order | **1,031 / 335** | **-96 B** | **-96 B** |
| 05 independent repeat of 04 | **Whole-file identical to 04** | -96 B | -96 B |

Both source comparisons (01 -> 06 and 02 -> 04) gain exactly
`0x72810` and `0x13b9b8` normalized and the same 42 raw memberships, without
losses. `MEMBERSHIPS.json` and `VERIFICATION.json` retain full sets. The
unmodified #2251 generators produce exactly the prior packet's Windows
scripts: main SHA-256 `e5df24b5ad14a66b2bc60350ae7ec08d30af3ebbd8f64d85f79be2953aa9ba9b`,
composition `72ef693c883fb68e9939f408f785f230742cb533b30cbf1321719d4852123569`.
Their CRLF bytes are pinned inputs. Separate regeneration agrees exactly.
Link-only comparisons preserve all complete normalized-body multiplicities.

The fresh source no longer needs the prior V3/exact-quote fixes applied as
patches. The original-sized buy handler, sweep and create bodies remove
another 88 bytes, and the wrapper removal eliminates 512 bytes. This is
observed whole-source composition, not an attribution of the 42 raw gains
to any single source edit; no single-edit ablation is claimed.

## Four remaining bodies; two remaining size deficits

The original formatter interval is `0xa868 -> 0x1a25b0`; the final interval
is `0xa868 -> 0x1a2550`. Its true matching callee is now **96 bytes earlier**,
so the thunk remains non-raw. Both intervals have 788 physical functions
without gaps. The complete-body multiset shares 784 occurrences and has four
missing/extra bodies: 69,416 original bytes versus 69,320 candidate bytes.

| Original body | Original / candidate bytes | Size difference | Normalized match |
| --- | ---: | ---: | --- |
| create-v2 `0x1e7c0` | 15,576 / 15,576 | 0 | No |
| admin-CTO `0x22a10` | 27,400 / 27,344 | -56 | No |
| swap-hop `0x5b3b0` | 18,584 / 18,544 | -40 | No |
| V3 exact-quote `0x1489f8` | 7,856 / 7,856 | 0 | No |

The previous composition's +40-byte span contained cancelling positive and
negative errors. Removing positive size errors exposes these two deficits;
the absolute span distance is larger while actual raw and normalized matches
improve. Equal total size is insufficient: create and exact-quote still need
body reconstruction despite already having the original size.

## Actual callee binding

The final five inspected bodies have matching complete normalized bodies,
matching direct-call offsets and **354 / 354** direct targets whose complete
normalized bodies match the original:

| Caller | Direct callees | Syscalls with identical instruction bytes |
| --- | ---: | ---: |
| Sweep `0x72810` | 37 | 2 |
| V3 costs `0x80df8` | 17 | 0 |
| Buy V2 `0x13b9b8` | 90 | 0 |
| Exact-quote V2 `0x13f630` | 130 | 1 |
| Sell V2 `0x144508` | 80 | 0 |

Fresh main's exact-quote and sell bodies are normalized matches but each
still calls the 512-byte rent wrapper instead of the original 416-byte body.
Those actual-target mismatches disappear in the composition. A negative
fixture changes buy's rent-call operand without changing normalized bytes;
the binding check rejects it. These are one-hop static observations, not
recursive or behavioral equivalence. `CALLS.json` retains the controls.

## Reproduction and limits

`PRODUCTION.json.gz` contains five compiler command/result records and all
source/dependency/module/sysroot inventories. Compiler logs, actual linker
receipts, source patches, generator reports, failed preflight and merge
inputs are retained. The existing Windows bridge is reused unchanged from
the [combined-span packet](../combined-span/NOTES.md); its source/binary and
upstream wrapper identities are pinned in every launch record. No bridge or
dependency compiler was run this increment.

Provide the retained image directories, exact original/inventory and the
eight harness files pinned in `review.json`:

```text
python -I -B reconstruction/pump-main/lanes/startrack3r-rent-call-binding/source-composition/verify_composition.py --images /path/to/retained-builds --original /path/to/deployed.so --inventory /path/to/functions.tsv --harness /path/to/pinned-harness --work /path/to/new-replay-output
```

Normal Python, optimized Python and a minimal relocated replay agree.
Independent parsing agrees on every membership for the four unique outputs.
Full source replay agrees, including the deleted account-name file; recorded
base/theirs files agree with the exact Git revisions. The ledger snapshot has
1,166 rows; schema-valid local attempts retain the failed preflight. The
shared POSIX ledger is unavailable on Windows.

This is five successful offline root rustc commands, one rejected source
preflight and zero target/VM/live-chain executions. The raw compiler outputs
are unpatched and unpadded; they are not the original allocation image.
The verifier checks their equality with retained compiler destinations.
Original bytes serve only offline order calibration and verification, not
compiler input. No clean-machine/native bootstrap, historical compiler
authentication, whole-original byte identity, completeness or security claim
is made. Remaining source work should start by reviewing the existing four
body lanes, not by padding the 96-byte deficit.
