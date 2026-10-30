# Complete captured contract request compiler

This restores the complete **898661 createContractClient request-compilation
owner**, beyond the previously recovered search-query subset and HTTP-error
decoder. It is an executable, independently maintained client adapter with
required transport and schema/catalog ports. Importing it creates no request,
default origin, session, backend handler or product route.

The original code remains attributed to its original authors. Descriptive names
are analyst names; original TypeScript, source paths and server behavior are
not recovered. `contract.json` binds the actual complete owner, imported
dependencies, all recorded origins, source/factory hashes, UTF-16/UTF-8 witness
ranges and maintained adapter bytes. Its producer reads the original physical
registration through the shared authenticated source reader, pins the reviewed
factory and requires the actual export/import edges. No captured JavaScript is
evaluated. The already maintained `contract-http-errors/decode.mjs` is imported
unchanged and receives no new recovery credit.

## Explicit integration

```js
import { createContractClient } from './client.mjs';
const request = createContractClient(hostKyShapedTransport, {
  contracts: hostActualRouteCatalog,
  routeErrorSchema: hostActualStatusSchemaResolver,
  contractErrorBody: hostActualGenericEnvelopeSchema,
});
// Call only when the host has separately authorized its selected destination.
await request('GET /items/{id}', {params: {id: 'supplied'}, query: {tags: ['a', 'b']}});
```

The transport returns an object with `.json()`, like the captured client. Query
schema ports expose their actual `shape[name].safeParse` boundary. This adapter
does not guess Zod parsing, retries, cookies, credentials or response validation.

## Preserved complete behavior

- Split the operation into method/path, drop the leading slash, substitute
  `{word}` params with encoded `String(value)`. Missing params become the string
  `undefined`; an explicitly null params object still fails as in the source.
- Omit undefined query fields, stringify scalar values, join array items with
  commas, reject commas within array items. Empty arrays are omitted only when
  the declared field's `safeParse(undefined)` succeeds; no overall query-schema
  validation is invented.
- Declared multipart routes use their selected file fields (default `image`).
  A hand-built FormData is refused. If no declared file is non-null, keep the
  original JSON body. Otherwise append file parts and stringify non-file fields,
  skipping undefined fields and null files. Browser FormData accepts Blob; the
  native `getParts` branch accepts `{uri,name,type}` descriptors instead. The
  constructors are explicit optional platform ports; native tests do not claim
  to run React Native.
- Lowercase the method, select `searchParams` and JSON/multipart, then spread
  remaining request options last. Intentional transport overrides stay intact.
  Successful `.json()` values are returned without adding schema validation.
- Preflight query/multipart errors occur outside the request catch. Request or
  JSON errors pass through the credited HTTP normalizer; non-response-shaped
  network/abort/parse errors retain their identity. Actual schema ports own error
  envelope parsing; this unit does not expand that existing decoder's scope.

## Repeatable evidence

```sh
node app/scripts/original-contract-client.mjs --check
node --test app/tests/original_contract_client.test.mjs app/tests/original_contract_http_errors.test.mjs
python app/scripts/verify-evidence.py
python scripts/verify_evidence.py
python -X utf8 scripts/test_tooling.py
```

The eight new tests authenticate the full owner and perform actual loopback HTTP
GET/POST requests with authored synthetic data, including real Blob/FormData wire
bytes, JSON fallback, overrides, HTTP errors, empty-array schema admission,
unsupported multipart forms and original-error identity. Separate source-gate
controls reject changed raw capture bytes and changed maintained implementation.
They do not call a production service or act as an original server oracle.

The credited decoder's 13 tests also pass. The broader shared-source suite passes
10 checks; its remaining symlink fixture cannot be created on this Windows host
(EPERM before assertions). A sandboxed attempt also could not connect to local
loopback (EACCES); the same HTTP tests pass with authorized local execution.

Limits: finite offline/local interaction proof and static source binding, not
full original runtime equivalence, native API compatibility, authentication,
complete transitive source closure, browser visual parity or security acceptance.
The browser/React Native platform branching is qualified only by the explicit
local constructors used in tests. Original captures, SDK, feature milestones,
existing video-upload flow and credited packages are unchanged.
