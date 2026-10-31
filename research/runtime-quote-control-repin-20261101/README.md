# Quote-control receipt identity across candidate paths

The parallel validator copies its candidate into a new private path for each
invocation. At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, the quote-control
producer records the candidate only as a path key in `bound_inputs_sha256`.
Its specialized receipt consumer consequently rejects the same image at the
next pin path with `KeyError`, although the retained outcomes remain valid.

[PR #3689](https://github.com/lalalune/pumpfun-source/pull/3689) corrected the
analogous issue for five generic suites. This follow-up covers the separate
quote-control producer and admission function. The producer now records
`original_sha256` and `candidate_sha256` from its existing admitted and rechecked
input map. The consumer checks those explicit roles when present and retains
path-based admission for old receipts. The full provenance map and all outcome,
comparison-key, count and duplicate-case checks remain. Retained outcome fields
use the same type-sensitive JSON comparison as the generic suites, so a boolean
signature result cannot equal the integer `1` through Python coercion.

The exact-base and fixed producer CLIs each executed their unchanged 507 cases
against the captured original used as both images. The first pin admitted in
both versions. A second byte-identical pin failed before and admits all 507
cases after. Every retained case record is identical across the two runs:
SHA-256 `0085eebaef3c31cc7125ec74aec4a4c0ef65b149a16f0590297a892df1cbf125`.

The fixed consumer rejects thirteen controls: a different candidate or original,
the wrong suite, either wrong explicit image hash, a missing case, a duplicate
case, a changed outcome, a missing comparison field and a changed comparison-key
list, plus nested or scalar boolean-to-integer and lamport integer-to-float
changes. Those last three contradictory JSON values were accepted before.
Old path-only receipts still admit at the recorded path and reject a new
path. Inputs and saved reports remain byte-identical during admission.

## Repeat

With the pinned requirements installed, run this same probe against a clean
base checkout and the fixed checkout, choosing fresh output directories:

```sh
python -B research/runtime-quote-control-repin-20261101/probe.py \
  --repo <base-or-fixed-checkout> --output <fresh-output-directory>
python -B tests/test_quote_control_repinned_receipt.py
python -B tests/test_quote_control_output_publication.py
python -B tests/test_pump_quote_control_pinned_image.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The probe invokes the actual producer CLI and the production `validate_result`
consumer used by the parallel runner. It does not invoke the complete build-bound
44-suite aggregate CLI, compile a candidate, add runtime cases or claim source
equivalence. The historical path-only receipt format is preserved, not migrated.
`results.json` retains the bounded before/after measurements; each local probe
also writes its full authentic receipt and producer log.
