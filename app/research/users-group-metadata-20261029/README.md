# Keep group profile metadata within the declared read schema

The maintained local `UserStore` accepted malformed `member_count` and
`group_badges` data, then served it through successful profile reads. On base
`630a074126a13d4133514d599129c6ac9a3179bc`, real ephemeral-loopback
`GET /v1/users` requests returned 200 for all six invalid examples below. The
unchanged captured OpenAPI response schema rejects those bodies.

| Supplied local metadata | Before HTTP result | Captured-schema discrepancy |
| --- | --- | --- |
| `member_count: "3"` | 200 | number required |
| `member_count: null` | 200 | number required |
| `group_badges: null` | 200 | array required |
| badge without `profile_image_url` | 200 | required property missing |
| badge with boolean `role` | 200 | string/open enum required |
| badge with an extra field | 200 | `additionalProperties: false` |

A valid control returns 200 and passes the same schema. `before-http.json`
retains all response bodies, provenance markers, schema issues and source/spec
hashes. The data is the maintained **synthetic local snapshot**, not production
accounts or captured API traffic. The existing public test-key fixture is used
only to exercise the unchanged local gate; no request headers are recorded and
no authentication compatibility is claimed.

## Correction and limits

`UserStore` now validates these two fields during snapshot admission, before its
read indexes are built. Invalid metadata raises a local `TypeError` before an
application can listen, rather than producing a schema-invalid successful read.
`after-http.json` records the same six fact variants rejected before listening,
while the valid control still returns a conforming 200. This is a local admission
choice consistent with existing invalid-snapshot rejection, not a reconstruction
of an upstream error response.

Only the declared constraints are added. Member counts remain finite numbers,
including fractional or negative values because no integer/minimum is declared.
Badge arrays may be absent or empty. Badges have the four required fields and
no additional keys; their image may be a string or null. String fields may be
empty where the schema permits it, and arbitrary future string roles remain
valid under `x-open-enum`. Array holes and incomplete/mistyped badge objects
are rejected. No other User validation, `kind`/status handling, identity lookup,
pagination, route, authorization or paused social-store behavior changes.

The oracle is the retained declaration at
`paths./users.get.responses.200.content.application/json.schema.items.properties`,
specifically `member_count` and `group_badges`. The same fields are checked through
the documented single-user and search response schemas. No original backend
source, production behavior, security acceptance, native-operation qualification
or feature-milestone credit is inferred.

## Executed checks

- New regression before: two admission failures, one real HTTP positive passes.
- Fixed: all three regression tests pass, covering malformed metadata, allowed
  numeric/open-enum boundaries and actual loopback list/single/search reads.
- Entire maintained backend: **967 pass, zero failures/skips**, two workers.
- Strict backend typechecking passes.
- App evidence verification passes 698 captures, npm integrity and unchanged SDK
  sources. Captures and the specification are unmodified.

Run from the repository root with the existing pinned dependencies:

```sh
cd app/packages/backend
node node_modules/tsx/dist/cli.mjs --test test/users-group-metadata.test.ts
node node_modules/tsx/dist/cli.mjs --test --test-concurrency=2 test/*.test.ts
node node_modules/typescript/bin/tsc --noEmit
cd ../../..
python3 app/scripts/verify-evidence.py
```

`repro.mts` and `repro-after.mts` retain the exact executed historical drivers.
Their relative imports/output paths expect staging under
`work/backend-group-metadata/` in a checkout. The former targets the base revision;
the latter targets the fix. To rerun the fixed HTTP/admission record:

```sh
mkdir -p work/backend-group-metadata
cp app/research/users-group-metadata-20261029/repro-after.mts work/backend-group-metadata/
node app/packages/backend/node_modules/tsx/dist/cli.mjs work/backend-group-metadata/repro-after.mts
```

The first outside-package `.ts` invocation was treated as CommonJS and blocked
on top-level await before any HTTP ran. The unchanged driver in explicit `.mts`
mode ran successfully; `setup-module-mode.log` retains that setup error. Source
hashes are rechecked after both HTTP runs. `MANIFEST.json` binds all retained
files; saved records are finite evidence, not an independent attestation or a
fresh execution. Earlier packages and unrelated open work remain untouched.
