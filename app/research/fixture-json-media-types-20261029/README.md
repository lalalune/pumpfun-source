# Fixture JSON values with explicit media types

A valid fixture with a structured JSON body and `Content-Type: text/plain`
was accepted at registration but returned HTTP 500 instead of its recorded
200. Fastify 5.6.2's reply path does not JSON-serialize an object, array,
number or boolean when an explicit non-JSON media type selects raw sending.
The replay fallback previously encoded only JSON string/null bodies itself.

The fix encodes structured JSON values before sending them with the recorded
media type. It preserves default/JSON string and null encoding, explicit
non-JSON raw strings and empty null responses, raw `Buffer` bodies, and the
existing status handling. Rejecting these already-valid fixture records would
change admission rather than replay their recorded representation.

`RESULT.json` binds the tested source and lockfile. Base `ccd3330bfd12ed04c3a598af9a2ab95ed5de77ac`
and live main `604917c16410d67d9b981305e28e160a93728f50` had the same app tree.
The oracle is the local `Fixture` type and declared replay behavior in
`app/contracts/README.md`, not a live API response or a developer API schema.
No original captures, native handlers, SDK source, coverage or operation
counts change. Related open #1541 (HEAD lookup), #1524 (transfer framing),
and #1543 (native request JSON parsing) address separate behavior.

The identical synthetic nine-case loopback driver produced four status/media
type mismatches on the base and none after the fix. Five working controls
retain their exact status, Content-Type and response bytes. The portable
regression test failed 1/passed 1 on base and passes both tests after the fix;
it also checks all four structured types with `application/octet-stream`.
The completed full backend suite passes 966 tests, backend typecheck passes,
and app evidence verification preserves all 698 objects, npm integrity and
SDK sources. Raw results and a compressed full test log are retained here.

From `app/packages/backend`, reproduce the checked-in real-socket tests:

```sh
node node_modules/tsx/dist/cli.mjs --test test/fixture-media-types.test.ts
node node_modules/tsx/dist/cli.mjs --test --test-concurrency=2 test/*.test.ts
node node_modules/typescript/bin/tsc --noEmit
```

To rerun the exact matrix driver from repository root, stage it at its original
relative depth, then use the pinned backend runner:

```sh
mkdir -p work/fixture-media-types
cp app/research/fixture-json-media-types-20261029/repro.mts work/fixture-media-types/repro.mts
node app/packages/backend/node_modules/tsx/dist/cli.mjs work/fixture-media-types/repro.mts
python3 app/research/fixture-json-media-types-20261029/verify.py
python3 app/scripts/verify-evidence.py
```

For the before result, use the base revision with the same added regression
test/driver. The driver uses ephemeral loopback ports and synthetic fixtures;
it closes every server. It saves the fresh matrix to
`work/fixture-media-types/observed.json`. The verifier checks retained receipts
and current source bindings; it does not rerun HTTP or infer a wider result.
Tests cover local HTTP/1.1 only, not HTTP/2, proxies, production availability
or compatibility with an original service. Native compatibility remains
unqualified.
