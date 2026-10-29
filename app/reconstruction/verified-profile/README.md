# Original verified-profile read and identity-consumer boundary

This reconstructs the **complete captured179736 client**, through its two
physical variants, and binds its result to all four154121 identity-hook variants
and the actual693124/107240 identity renderer. It is an unmounted executable
model with explicit transport, timer, compiler-memo and query-hook ports.
Import performs no request. No captured JavaScript is imported or evaluated.

The existing profile lookup (#870), user-row coalescer (#910), strict batch and
fallback query (#901/#922), profile callouts and local profile/verified endpoints
remain unchanged. In particular, this is not another implementation of the
developer API's declared read handler, a new verified-status authority, or a
replacement for the accepted user-row coalescer.

## Complete used source boundary

The deterministic [contract](contract.json) records 15 physical factory roles,
their original object URLs/hashes and exact UTF-16/UTF-8 source witnesses. It
includes both indexed179736 variants and all four indexed154121 variants;
there is no arbitrary global-ID winner. The original Googlebot capture and
retained dependency graph do not establish a currently active provider or UI.

| Boundary | Captured behavior retained |
| --- | --- |
| HTTP read | Both179736 variants use the literal website origin `https://frontend-api-v3.pump.fun`, the shared K-shaped client, and `POST /profiles/verified`. Body is `{ids:[...new Set(values)].filter(Boolean)}`; empty direct input returns `{}` without transport. Explicit credentials are `same-origin`. No ID-format validation, fetchOptions or new HTTP retry policy is inserted. |
| Response/failure | An afterResponse hook throws `Error('Failed to fetch verified profiles')` for a non-ok response. The used safe wrapper catches every failure and returns `{}`. The successful value is raw; no response schema is enforced here. Shared transport/declaration behavior remains a credited dependency. |
| Resolver | One resolver per origin in a module instance. Its first pending key schedules50ms; duplicate keys retain every waiter. Flush resets the timer and swaps the pending Map **before** asynchronous reads. Unique keys are partitioned into100-key requests; chunks settle independently. |
| Projection | Resolve each waiter with `response[id] ?? false`. A chunk failure resolves its remaining waiters false. No boolean conversion or own-property filter is added at this stage. Even partial settlement before a throwing property access is retained. |
| Query hook | Exact10-slot compiler memo, raw `['user-verified', identifier??'']` key, old callback capture, enablement `(enabled===undefined||enabled)&&!!identifier`, staleTime1800000 and retryfalse. Options only read `enabled`; there is **no** final option spread. The query-context signal is not consumed. |
| Hook result | Return `query.data === true`. A raw truthy string, number or inherited function is not true. This is a captured rendering-data decision, not verification of identity or permission. |
| Identity hook154121 | Verification subject is `enabled ? user?.userId ?? address : undefined`, retaining an empty supplied user ID. The verification hook is called **before** the later absent-address view return. This is distinct from its existing profile lookup, which has its own address/missing-user gate. Broader name/avatar normalization is witnessed, not reimplemented here. |
| Renderer693124 | Query only for the literal `verified==='lookup'` mode and its exact unsuppressed identity condition. Subject is `userId ?? address ?? null`; empty user IDs are not repaired. Otherwise retain the supplied verified prop. The actual badge element consumes that selected value's truthiness. |

The renderer's used Near-display predicate is bound through646908.B/R,
253623.D in both variants, and605587.h. The model reproduces only those used
predicates and their literal regular expressions. They are not wallet
validation, chain support, account existence, ownership, authentication or
authorization. Unrelated wallet/provider functions in the same captured
factories are not reimplemented.

The existing declaration850620 describes a `profiles.read` map of booleans
whose rendering flag incorporates two server-side flags. Its provenance is
retained separately from the client. This unit does not derive those flags or
implement their server policy. Declaration presence is not runtime validation,
anonymous permission, API-host equivalence or compatibility proof.

## Maintained model and explicit capabilities

```js
import { createVerifiedProfileReader } from './client.mjs';

const reader = createVerifiedProfileReader({
  serverUrl: explicitlyChosenIsolatedOrigin,
  createClient, // ({clientServerUrl}) => async (operation, options) => rawResult
  schedule,    // (callback, delayMs) => timerHandle
  memo,        // correctly initialized10-slot cache, separate per hook instance
  useQuery,    // receives actual options; returns {data}
});
```

There is no production URL default or implicit fetch implementation. The
captured fixed origin remains source evidence; tests pass only synthetic
capabilities. Constructor/port type checks are local host-capability admission,
not additional original data validation.

`readBatch` exposes the original private direct-read boundary for inspection;
`readOrEmpty` is its used error wrapper. `resolverFor(origin).fetch(id)` exposes
the original pending-waiter boundary. These descriptive adapter names are not
claimed original public exports. `useVerifiedProfile` reconstructs the complete
captured hook policy through host ports without implementing React or a query
scheduler. A host must reuse one reader instance to share one source module's
per-origin queues and supply a separate initialized memo cache per hook instance.

`identityVerificationSubject`, `rendererVerificationSubject` and
`rendererVerificationValue` model the exact used caller handoffs. They do not
mount a badge, read a wallet/session, fetch a whole profile or create a trust
decision. No networking is performed by these policy helpers.

The accepted #910 coalescer has no generic public queue export to reuse: it
indexes user rows, preserves typed errors/rejections and hydrates aliases.
179736 instead coalesces raw flag lookups and resolves failures false. This
unit leaves the accepted implementation untouched and claims no new recovery
of its already-published helper or shared HTTP/source/declaration tooling.

## Repeatable finite checks

From `app`, with the repository's existing pinned dependencies and captures:

```sh
node scripts/original-verified-profile.mjs --check
node --test tests/original_verified_profile.test.mjs
```

`--write` explicitly regenerates only the contract. `--check` authenticates
complete capture bytes, literal factory registrations, physical variants,
imports/used calls, implementation/dependency hashes and deterministic contract
bytes. It rejects a changed raw capture and even a resealed changed original
factory. It parses inert AST; it never executes recovered code.

The14 focused cases exercise the complete maintained model through real
Promises and controlled synthetic ports: ID/body normalization, safe failures,
duplicate waiters,50ms grouping, queue swap while HTTP is pending, independent
100/1 chunks/origins, raw/missing/partial projection, strict-true result,
memo identities/option precedence, old callbacks and ignored signals, both
actual caller policies and their result handoff. Native Response JSON parsing
is used only on in-memory synthetic responses. **No HTTP POST, including
loopback, is performed.** Timer/query scheduling and original runtime behavior
are not inferred from these finite adapter tests.

The baseline main lacks this maintained model and source contract; no fabricated
original response or live baseline is used. Captures, SDK, product routes,
backend, dependencies and feature ledger stay unchanged. No current badge
trust, UI mount, visual parity, native backend/API compatibility, security
approval, provider winner or feature-milestone credit is claimed.
