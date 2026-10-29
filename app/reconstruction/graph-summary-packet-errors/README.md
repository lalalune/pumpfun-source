# Preserve graph summary packet errors

`graph:summary` used to catch every retained-report read error and print a newly
analyzed summary instead. A malformed `GRAPH-SUMMARY.json`, or that file missing
inside an existing packet, therefore produced exit status 0 and successful JSON
unrelated to the broken retained packet. This could hide a damaged or incomplete
packet during an ordinary evidence lookup.

The CLI now performs first-run analysis only when the packet directory itself is
absent. An existing packet's read/parse error reaches stderr with a nonzero exit;
its files are unchanged. Valid retained summaries and genuinely absent-packet
analysis keep their existing behavior. The analyzer, packet reader and all graph
resolution/grammar logic are unchanged. Open #1206 independently adds report hash
authentication; this correction does not duplicate that work or claim that valid
JSON is authenticated by the current reader.

## Reproduction and results

Base: `094a06f18df738d41e77070c1a009e135671ac1a`. Tested source:
`496bd0718eeaac84f4a6555bc74c1242d5f0f7be`.

From `app/`:

```sh
node --test tests/factory-graph-summary-cli.test.mjs
node --test tests/factory-graph*.test.mjs tests/factory_graph.test.mjs
pnpm exec prettier --check scripts/factory-graph/cli.mjs tests/factory-graph-summary-cli.test.mjs
python3 scripts/verify-evidence.py
pnpm check:progress
```

The regression invokes the actual copied CLI and unchanged core in a temporary
workspace. A single inert multiline-template factory satisfies the unchanged
default 250,000-line selection budget, so first-run fallback genuinely executes
the analyzer without a fake graph implementation or altered selection flags.
The synthetic input is never executed or counted as recovered original source.

The same final regression bytes reproduce two erroneous successful commands on
the base: malformed retained JSON and a missing summary in an existing packet.
Both controls already pass on the base. All four scenarios pass after correction
(five Node test counts including their parent). The failed lookups preserve the
malformed/missing file and manifest. A valid current maintained summary also
remains readable, with its exact input/output hashes in `SOURCE-BINDING.json`.

The complete affected graph target passes **25/25**, including the current
authenticated captured-corpus rebuild. Application evidence verifies all 698
objects, npm integrity and unchanged SDK source; progress plus nine tests and
Prettier pass. The exact source commit also passes the required nine-capture and
ten-tooling checks. Compressed raw logs and source/input hashes are retained here.
`SETUP-NOTES.md` distinguishes the initial sparse-input failures from these runs.

No retained graph/capture/factory bytes, qualification counts or application/SDK
runtime inputs change. These tests qualify evidence-tool error propagation;
they do not establish source freshness from a cached lookup, complete graph
resolution, API compatibility, browser behavior or security equivalence.
