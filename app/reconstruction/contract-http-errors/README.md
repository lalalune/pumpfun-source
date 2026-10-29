# Captured contract-client HTTP error decoder

The retained website client has a concrete error boundary that the route-binding ledger alone does not describe: a response-shaped HTTP failure becomes `ContractError`, with separate raw body and parsed data, while ordinary/network/hook errors keep their original identity. This unit reconstructs that boundary as an independently maintained pure adapter. It adds no endpoint or server error policy.

The original JavaScript remains attributed to its original authors. Descriptive names are analyst names; original TypeScript, paths, stack traces and backend implementation are not recovered. No captured JavaScript is imported or evaluated.

## Source and used call edges

The fixed captured source contexts are authenticated by URL, object length/SHA256, actual registration IDs, exact UTF-16/UTF-8 ranges and expression hash in [contract.json](contract.json). The producer rejects a second physical registration for a selected ID even if the inventory omits it. Context selection is physical source provenance, not a claim about the active winner of a global runtime ID.

The HTTP constructor in factory 30181 calls the contract barrel 402030's `createContractClient`, whose actual reexport targets 898661. That client catches the real request's `.json()` failure and invokes its async `c(route,error)` normalizer. The normalizer imports the actual 858694 error class, 233815 route error-schema builder, 4171 generic envelope and 402030 route catalog. 858694 reads 525364's domain-code function. These used import/reexport/catch edges and their expressions are preserved in the contract.

The primary capture is `evidence/web/objects/2b47dd0b38a1608f.js`, SHA256 `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d` (507700 bytes). Selected raw UTF-16 half-open ranges include:

| Operation | Factory | Range |
| --- | ---: | --- |
| HTTP error normalizer | 898661 | [1036,1722) |
| Actual request catch | 898661 | [3086,3117) |
| ContractError class | 858694 | [29745,30035) |
| Domain-code regex | 525364 | [4385,4425) |
| Raw-body domain-code extraction | 525364 | [29480,29618) |
| Route error-schema dependency | 233815 | [37389,37815) |
| Generic envelope dependency | 4171 | [467704,468169) |

The complete values, including the actual catch range, are generated from AST nodes in `contract.json`; source positions are not byte offsets. The PnL callback 864024 supplies an important limit: its afterResponse hook throws a plain Error without a response property, so this normalizer does not wrap it. This unit does not assert that every website failure becomes ContractError.

The original recovery reused the search authenticator revision `0a9a1f084`, SHA256 `49b11417fd4d500d8821c94df6c215b77da2248875f943570f2b9df6c9b35213`. The current `pathless-capture-errors-v1` helper has SHA256 `ef7acaad8c20e23d6f9821dc683cfc0dc66cc3eb1b14642674a9007c9c064205`: it excludes capture.py's pathless `{url,error}` transport-failure records from the file index, while retaining successful-source hashes, duplicate-path checks and AST/range authentication. The contract is regenerated with that reviewed dependency; its captured witnesses and runtime adapter remain unchanged. Historical validation receipts retain their original helper hashes. Shared utility/source declarations are dependencies, not new recovery credit. Home-feed's source-contract work also retains these error declarations; the distinct addition here is the maintained runtime normalization/error-object adapter and its conformance tests.

`inventory-compatibility.json` records a complete-entry comparison for the selected eight IDs between the maintained 4915 inventory and PR679's 5947 inventory. Every selected entry, including IDs, hashes, paths and origins, is identical. The producer pins those selected complete entries rather than making this unit depend on unrelated global inventory records. There is no repeated inventory-recovery claim or large inventory patch in this branch.

## Maintained behavior

`decode.mjs` exports `normalizeContractHttpError`, `withContractErrorNormalization`, `ContractError`, `isContractError` and `domainCode`.

```js
import { withContractErrorNormalization } from './decode.mjs';

// request is an explicit caller-provided operation. The adapter makes no fetch.
// These must be genuine caller-provided contract/schema implementations.
const value = await withContractErrorNormalization(route, request, {
  contracts,
  routeErrorSchema,
  contractErrorBody,
});
```

- The guard accepts a non-null object error whose non-null object response has a numeric status and callable text method. It does not require a particular HTTPError class. Other failures return undefined from the normalizer; the request wrapper rethrows the original value by identity, including AbortError.
- Read `response.text()` once. Valid JSON retains any JSON value, including scalars/null/arrays. Invalid JSON retains the text. Read rejection, including an already-consumed response body, produces undefined raw body; the original thrown error remains the cause.
- Resolve the known route's status schema and parse it when present and not `true`. Always attempt the generic envelope parse afterward, even after declared success. Data precedence is declared success, generic success, then `{statusCode:response.status}`. Raw body remains independent. Schema/accessor exceptions retain their original propagation boundary.
- Server message comes from the raw body: a string passes unchanged; an array filters string elements and joins them with `"; "`; other values yield undefined. Empty/all-nonstring arrays yield an empty string.
- Domain codes use `/^[A-Z][A-Z0-9_]+$/` rather than registry membership. Future well-shaped codes remain visible. Error message, fields, status predicate, class/optional-route predicate and original cause follow the captured class. Repeated property evaluation is retained where the original performs it.

The route catalog, route-error schema generation and generic schema's actual `safeParse` implementations remain explicit dependencies. They are not approximated here. Controlled parser results in tests prove normalization precedence and invocation order; they are not claims about reconstructed Zod acceptance, projection or transformations. The caller also retains HTTP transport/retry/auth/header behavior and request preflight encoding. No production-origin default or network transport is supplied.

## Verification

From `/app`, with the existing pinned dependencies:

```sh
node scripts/original-contract-http-errors.mjs --check
node --test tests/original_source.test.mjs tests/original_contract_http_errors.test.mjs tests/original_contract_http_error_source.test.mjs
```

`--write` regenerates the contract after an intentional source review. To reproduce the optional inventory comparison against a checkout of PR679:

```sh
node scripts/original-contract-http-errors.mjs --compare-inventory /path/to/expanded/app/recovered/modules.json
```

The focused 30 tests cover physical/capture/artifact tampering, unindexed nested contenders, the runtime metadata negative, inventory isolation, raw JSON/text/read failures, both parser paths and their exceptions, status evaluation order, code/message/cause/class semantics and non-HTTP/abort identity. They include a real native Response, the hash-authenticated existing public 401 body and a loopback HTTP response; the loopback transport/schema controls are explicitly synthetic. No original bundle execution or production request is part of these checks.

These finite tests and static witnesses do not establish a complete client, Zod implementation, server compatibility or security acceptance. Captured evidence, SDK source, existing bindings/coverage and feature-completion ledgers remain unchanged.
