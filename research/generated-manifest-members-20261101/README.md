# Fresh generated verifiers reject repeated manifest members

Tested base: `60a42309a4908577f0a386513eeaee6cd6f84f42`.

The four maintained generators (`analyze_program.py`, `deep_disassembly.py`,
`deep_section_analysis.py` and `bytecode_signatures.py`) emitted standalone
verifiers that used last-value-wins JSON parsing. A freshly generated real
capture packet with a contradictory earlier `summary.json` declaration still
printed `All checks passed.`, while the repository's canonical
`revalidate_all.check_manifest` rejected that same file as
`manifest_parse_error`.

This extends the already accepted manifest admission rule from
[harrywu666's #3525](https://github.com/lalalune/pumpfun-source/pull/3525) and
[dbstkddl8-create's #3274](https://github.com/lalalune/pumpfun-source/pull/3274)
to newly generated standalone verifiers. #3525 documented an actual retained
manifest with three conflicting declarations; it deliberately preserved the
old packet verifier. This change likewise leaves previously generated packets,
manifests and captures untouched. It does not claim a new original discovery
of JSON's last-value-wins behavior.

Each template now uses an `object_pairs_hook` that rejects a repeated decoded
member name, then reports an explicit failure and exits 1. The check remains
active under `-O` and `-OO`; escaped spelling does not hide a repeated name.
Keeping the short parser in each generated script preserves standalone packet
verification without importing repository modules.

## Reproduction

From this candidate checkout with Python 3.12:

```sh
python -B research/generated-manifest-members-20261101/reproduce.py . \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect before \
  --output /tmp/manifest-members-before.json
python -B research/generated-manifest-members-20261101/reproduce.py . \
  --expect fixed --compare /tmp/manifest-members-before.json \
  --output /tmp/manifest-members-after.json
```

Each run executes all four actual generator CLIs against owned copies of the
retained captures. Analyze/deep/section generate Mayhem packets; the signature
CLI uses its normal Pump, AMM and Mayhem inputs. Only each owned manifest is
varied. For every packet, seven variants run the emitted `verify.py` in normal,
`-O` and `-OO` modes: **84 verifier CLI calls per run**.

| Manifest variant | Base generated verifier | Fixed generated verifier | Canonical manifest checker |
| --- | --- | --- | --- |
| Unique valid members | Pass | Pass | Pass |
| Valid uniquely escaped member | Pass | Pass | Pass |
| Earlier contradictory duplicate | Pass | Fail | Parse error |
| Identical duplicate | Pass | Fail | Parse error |
| Duplicate decoded name using `\u0073` | Pass | Fail | Parse error |
| Unique incorrect digest | Fail | Fail | Fail |
| Malformed JSON | Fail | Fail | Parse error |

The [before](before.json) and [after](after.json) records bind all source bytes
and nine retained capture identities. The **36 duplicate false passes become
36 failures**. All **33 non-verifier analysis payload hashes** are unchanged;
new `verify.py` bytes and their manifest digests intentionally change. The
probe asserts the source/evidence copies and original capture inputs remain
unchanged. It calls only the canonical manifest-check API, not the batch
revalidator or any unrelated archived verifier.

## Maintained wrapper and composition

[Source review](source-review.json) records the complete template-only source
transition and the exact current-source hash search. The maintained
`tooling-analysis-output-retention-20261029/generate.py` wrapper receives the
two explicitly reviewed analyze/deep identities. Its previous allowed
identities and all publication checks remain in place. Historical identity
records are unchanged.

```sh
python -B research/generated-manifest-members-20261101/wrapper_controls.py . \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 \
  --output /tmp/manifest-wrapper-before.json
python -B research/generated-manifest-members-20261101/wrapper_controls.py . \
  --compare /tmp/manifest-wrapper-before.json \
  --output /tmp/manifest-wrapper-after.json
```

Each wrapper run makes 13 actual CLI calls: direct and wrapped generation for
all four supported programs, rejection of three independently altered helper
files, and preservation of an existing file and empty output directory.
[Before](wrapper-before.json) and [after](wrapper-after.json) outputs show all
eight direct/wrapped packets identical within their revision and all analysis
payloads unchanged across revisions. Unreviewed helpers remain rejected.

The concurrent token-constant change
[#3920](https://github.com/lalalune/pumpfun-source/pull/3920), exact head
`492a9d7da5614d0f7f87e9d789bbf9efe0d89179`, touches a different region of the
signature generator. The [composition replay](compose_token.py) applies this
candidate's template diff to that exact source in a temporary directory:

```sh
git fetch https://github.com/lalalune/pumpfun-source.git pull/3920/head
python -B research/generated-manifest-members-20261101/compose_token.py . \
  --output /tmp/manifest-token-composition.json
```

Run that replay at this candidate's tested source, where the only signature
change relative to the stated base is the verifier template. Its
[retained result](token-composition.json) records two real signature generation
CLIs and 12 verifier invocations. All ten token-aware analysis payloads remain
identical; duplicate rejection composes with the detector change. This is a
composition check of those pinned sources, not admission of arbitrary future
helper hashes.

## Validation and limits

The existing CI-invoked `tests/test_generated_packet_census.py` now exercises
actual generated packets with conflicting, identical and escaped duplicate
names in all three Python modes. Its seven methods, four maintained wrapper
methods, 48 publication methods and the canonical duplicate-manifest method
pass: 60 focused static test methods in total. `scripts/verify_evidence.py`
verifies all nine captures. Required full tooling validation is tracked in the
PR handoff separately.

This corrects the admission behavior of future generated static evidence
packets. It does not retroactively validate or rewrite archived packets. No
ELF, program model, VM, compiler or rebuilt candidate is executed; there is no
new reconstruction, runtime-equivalence or security claim. Malformed variants
are deliberate, isolated manifest edits around genuine generated artifacts.

## Same-PR completion of the maintained generator family

The original proof above records the first four-generator change, published at
`a073c5c8e561dfe0f8a842d27aa1b446de140333`. Its scripts and retained before/after
receipts remain unchanged. A subsequent source-family audit reproduced the same
last-value-wins failure in three further maintained producers:

- `scripts/reconstruction_roadmap.py`;
- `scripts/revalidate_all.py`;
- `reconstruction/tooling/revalidation-qualification/audit.py`.

These three emitted verifier templates now apply the same explicit decoded-name
check. This is an appendix to the same correction and PR, not another claimed
contribution. The original **36** duplicate false passes plus **27** additional
false passes are **63** across seven producers. The extra checks cover three
manifest variants in normal, `-O` and `-OO` modes. Valid, uniquely escaped,
wrong-digest and malformed-JSON controls retain their outcomes.

```sh
python -B research/generated-manifest-members-20261101/residual_probe.py . \
  --revision a073c5c8e561dfe0f8a842d27aa1b446de140333 --expect before \
  --output /tmp/residual-manifest-before.json
python -B research/generated-manifest-members-20261101/residual_probe.py . \
  --expect fixed --compare /tmp/residual-manifest-before.json \
  --output /tmp/residual-manifest-after.json
```

Each run makes four actual generation calls and 63 emitted-verifier calls.
The roadmap reads genuine Pump, AMM and Mayhem captures. Each auditor receives
an owned repository containing exactly one newly generated static Mayhem packet,
whose verifier only checks file hashes. The probe never audits the real research
tree or executes unrelated archived/program verifiers. These boundaries are
asserted in the reproduction and the existing CI census suite's new method.
The [before](residual-before.json) and [after](residual-after.json) records retain
source/capture hashes and every outcome. All compared report data is unchanged;
comparison explicitly excludes generated verifier/manifest bytes, run provenance,
elapsed fields and disposable path spelling. It does not claim byte equality
of timestamped audit reports.

Five maintained source-binding sites move to the explicitly reviewed current
source identities: the three roadmap diagnostic adapters, the manifest-admission
runner and the qualification adapter. Historical proof/archived source identities
stay fixed. The current single-version guards reject both the previous root
identity and an unreviewed source edit; the older four-generator allowlists
remain unchanged and still retain all of their previous identities.

```sh
python -B research/generated-manifest-members-20261101/residual_bindings.py . \
  --revision a073c5c8e561dfe0f8a842d27aa1b446de140333 \
  --output /tmp/residual-bindings-before.json
python -B research/generated-manifest-members-20261101/residual_bindings.py . \
  --compare /tmp/residual-bindings-before.json \
  --output /tmp/residual-bindings-after.json
```

The [15 before](residual-bindings-before.json) and
[20 after](residual-bindings-after.json) actual adapter calls cover normal
regeneration, source drift, old identity refusal after rebinding, and occupied
output preservation. They retain analysis/verdict payloads and check published
source identities. Source/input receipts, emitted verifiers, timing and run
provenance are deliberately separate from those semantic comparisons.

The concurrent defined-call writer correction [#3925](https://github.com/lalalune/pumpfun-source/pull/3925),
exact `1b0be728950b66a26b86e92069cd69c6e85ce5bd`, modifies the writer while this
appendix updates its reviewed roadmap identity. The
[composition replay](residual_composition.py) applies the two source changes in
both orders, verifies identical combined bytes, and executes six genuine CLIs:
normal generation, a real 64-byte file-size limit, then same-path retry for each
order. Four emitted-verifier invocations pass. The
[result](residual-composition.json) confirms identical complete packets, no
partial output after the bounded write failure, and successful retry.

```sh
git fetch https://github.com/lalalune/pumpfun-source.git pull/3925/head
python -B research/generated-manifest-members-20261101/residual_composition.py . \
  --output /tmp/residual-composition.json
```

Run the composition replay at this appendix's tested source, before integrating
other writer changes. The [source review](residual-source-review.json) binds the
three template edits and their current adapter transitions. No immutable
historical packet is rewritten and no stopped runtime scope is reopened.
