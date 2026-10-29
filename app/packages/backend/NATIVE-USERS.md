# Native /users implementation

Status: seven of the 67 documented developer API operations are now served natively
(with six /posts operations also served natively; see [POSTS.md](./POSTS.md)).

| Operation | Path | Response |
| --- | --- | --- |
| `get_users` | `GET /v1/users` | 200, array of User |
| `get_users_by_id` | `GET /v1/users/{id}` | 200 User, 404 on miss |
| `post_users_batch` | `POST /v1/users/batch` | 201, array of User |
| `get_users_username_exists_by_username` | `GET /v1/users/username-exists/{username}` | 200 `{ "exists_flag": boolean }` |
| `get_users_search_v2` | `GET /v1/users/search-v2` | 200, array of User |
| `get_users_by_id_overview` | `GET /v1/users/{id}/overview` | 200 UserOverview, 404 on miss |
| `post_profiles_verified` | `POST /v1/profiles/verified` | 201 `{ [id: string]: boolean }` |

Everything else still falls through to fixture replay, and to `501` when no fixture
matches. That behavior is unchanged and covered by a regression test.

## Source layout

- `src/users-store.ts` - `UserStore`, a deterministic in-memory store with O(1)
  address / userId / username indexes, search filtering, and verified tracking.
  `defaultStore` is the singleton used by the app.
- `src/users-seed.json` - five seed rows, all satisfying the contract's required keys.
- `src/users-routes.ts` - the seven native Fastify handlers.
- `src/app.ts` - `buildApp()` registers native routes first and skips their OpenAPI
  paths in the generic replay loop, so native always wins over a captured fixture.
- `src/schema-validator.ts` - dependency-free JSON Schema validator for the subset the
  OpenAPI snapshot uses (type, nullable, enum, properties, required,
  additionalProperties, items, minItems/maxItems, minLength/maxLength, minimum/maximum,
  oneOf/anyOf). Usable by any operation, not just the seven here.
- `test/contract-conformance.test.ts` - validates every native response and every
  captured fixture against the published schema.

## Data source and its limits

The seed is hand-authored fixture data shaped to the contract. It is **not** captured
production traffic, and no real users exist behind these rows. This is a behavioral
implementation of the contract, not a replication of pump.fun's database.

`app/AGENTS.md` forbids fabricated domain responses, so this data is labelled wherever
it surfaces rather than left to look like evidence:

- `SYNTHETIC_SEED` and `DATA_SOURCE` in `src/users-store.ts` name the dataset for what
  it is.
- Every successful native response carries `X-Reconstruction-Data-Source:
  synthetic-seed-play`. Error responses carry no marker because they contain no domain
  data.
- A contract test asserts the header is present, so the label cannot be dropped without
  failing CI.

Replacing this store with fixture-backed or recorded data would not change any route,
test, or schema. Only `UserStore` would change.

Group metadata is checked when `UserStore` admits its snapshot, before read indexes
are constructed. A supplied `member_count` must be a finite number; the published
schema does not require an integer or nonnegative value. A supplied `group_badges`
must be an array of complete badge objects with exactly `group_id`, `username`,
`profile_image_url` and `role`. The first two and `role` are strings; the image is
a string or null. Empty arrays, absent metadata and future string roles remain
valid under the declared open enum. Invalid metadata fails local construction
instead of being serialized into successful schema-invalid responses. This is
bounded local data admission, not full User validation or upstream qualification;
see the [HTTP/regression evidence](../../research/users-group-metadata-20261029/README.md).

## Documented assumptions

The contract does not specify these behaviors. Each was decided deliberately; changing
any of them is a contract decision, not a bug fix.

1. **Lookup miss on `GET /users/{id}`** returns `404 {"error":"NOT_FOUND"}`. The spec
   documents only 200 and transport-level errors, so 404 is an addition.
2. **`id` resolution order**: wallet address first, then `userId`. Addresses and userIds
   are namespaced by construction in the seed, so a collision cannot currently occur.
3. **Negative `offset`** clamps to 0. The contract's integer schema permits negatives
   (minimum `-9007199254740991`) but says nothing about their meaning.
4. **Negative `limit`** returns an empty array, for the same reason.
5. **Non-integer `offset`/`limit`** are ignored (treated as absent) rather than rejected.
6. **Unknown `sort` value** falls back to seed insertion order. The contract types `sort`
   as a plain string with no enum, so there is no documented set to reject against.
   Recognized keys are `followers`, `following`, `address`, `username`.
7. **`order`** is only honored alongside a recognized `sort`; anything other than
   `desc` is treated as `asc`.
8. **Null values sort last** in both directions. This affects rows whose `username` is
   null.
9. **`POST /users/batch` with more than 100 addresses** returns
   `400 {"error":"TOO_MANY_ADDRESSES","maxItems":100,"received":N}`. The contract declares
   `maxItems: 100`; rejecting is preferred over silently truncating.
10. **Missing addresses inside a batch** are omitted from the response rather than
    returned as null entries. The response schema is an array of User with no nullable
    element, so omission is the only conformant option.
11. **`username-exists`** compares case-insensitively and ignores viewer identity, matching
    the contract note that the check has no viewer.
12. **Error bodies use the documented `Error` component shape** (`statusCode` plus `error`,
    with route detail added alongside). The contract declares no schema for the 400 and
    `default` responses, so the envelope is a choice; using the component keeps error
    responses machine-checkable instead of free-form.
13. **`searchTerm` in `GET /users/search-v2`** performs a case-insensitive substring match
    against `username`, `address`, `userId`, `x_username`, and `wallet_label`. An omitted,
    empty, or whitespace-only `searchTerm` matches all eligible users.
14. **`includeLabelledWallets` in `GET /users/search-v2`** defaults to `false`. When false (or
    omitted), users with a non-empty `wallet_label` are excluded from search results; when
    `'true'` or `'1'`, they are included. `'false'` and `'0'` are accepted as explicit false;
    any other supplied value (including an empty one) returns `400 {"error":"INVALID_QUERY"}`.
15. **Lookup miss on `GET /users/{id}/overview`** distinguishes account IDs from wallets,
    as specified by OpenAPI and captured factory `463539-82e5f0bd54e4`. A base58 identifier
    decoding to exactly 32 bytes with no local row returns 200, `profile: null` and
    `isPumpUser: false`; other misses retain `404 {"error":"NOT_FOUND"}`. Existing rows
    take precedence over format classification. This immutable store is the complete
    **local synthetic account snapshot**: absence says nothing about real upstream
    registration, and no network lookup or transport-error classification is performed.
    The separate `GET /users/{id}` response is unchanged.
16. **Overview `viewer` omitted**: Anonymous callers receive no `viewer` object, matching
    the OpenAPI spec description ("Absent on anonymous responses").
    Overview `isPumpUser` follows the documented `profile !== null` invariant (also
    captured in factory 463539), independently of the nested row's optional
    `is_pump_user` field. Raw user rows are unchanged.
17. **Overview unavailable legs**: An absent local wallet has `verified: false` and
    `achievementBadgeIds: []`, the explicit external-wallet defaults in factory 463539.
    Its follow counts, ban verdict and created-coins count are unavailable: both counts,
    `banned` and `createdCoinsCount` are null, with `degraded` exactly
    `["counts", "banned", "created_coins"]` and `Cache-Control: no-store`, as required for
    an anonymous degraded overview. Present profiles retain their existing values and
    `degraded: []`. Every successful response retains the synthetic provenance header;
    this implements a local response state, not production compatibility qualification.
18. **`POST /profiles/verified` validation boundaries**: Rejects with `400` if `ids` is empty
    (`minItems: 1`), exceeds 200 items (`maxItems: 200`), or contains any non-string or id
    longer than 64 characters (`maxLength: 64`).
19. **Unregistered or unknown IDs in `POST /profiles/verified`** map to `false` in the response
    object, matching the spec note ("ids with no user... are false").
20. **Verified identification**: A user is verified if their address or userId is in the store's
    verified set. Default seed marks Alice (`user-001` / `7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`)
    as verified.

## Not implemented

- Authentication or authorization of any kind. All seven operations are open, which is
  only acceptable for a local reconstruction harness.
- Rate limiting and the documented 429/503 responses.
- Any persistence. The store is immutable in memory.
- The other 60 documented operations.

## Developer-host profile boundaries

The shared response schema permits `last_active_at` because it also describes
signed-in website reads. Its description **explicitly requires absence on the API
host**; an optional property is not permission to expose it in that context.
The `/v1/users` list, single, search, batch and overview handlers project the field
out, including when its value is `null`. Follow searches use the same projection.
This is a transport boundary: the source user row, timestamps and all other
profile fields are preserved. A developer API key never establishes a website
viewer, and no last-seen value is inferred from follow edges.

All seven native user/profile handlers reject decoded duplicate query keys with
the replay harness's existing `501 {"error":"DUPLICATE_QUERY_KEYS_UNIMPLEMENTED"}`
response. Repeated scalar parameter semantics are not established by the public
contract, so they are not silently coerced to one value or allowed to crash the
handler. This is an explicit local unsupported boundary, **not** an observed
production error contract. The API-key gate still runs first.

The verified batch map preserves each requested string id as an own data
property, including `__proto__`, `constructor` and `toString`; ordinary object
prototype behavior must not silently remove requested results. This does not
change the synthetic verification dataset or qualify real identity formats.

Authority is the declared developer API `https://api.pump.fun/v1`, OpenAPI
`0.294.0` in `contracts/developer.openapi.json`, not the website profile-service
origin. `contracts/developer-bindings.json` links these operations to captured
contract factories in `recovered/modules.json`:

- users: `941660-5672cd75c90c`;
- overview: `463539-82e5f0bd54e4`;
- verified profiles: `850620-9d34ea015ae0`;
- following: `972407-a77710a323d3`.

Those bindings are static provenance, not executed captured source or website
compatibility evidence. `contracts/routes.json` associates the included profile
surface with `/profile/:id`, but this change does not wire that page to `/v1`.
`test/profile-graph-contract-boundaries.test.ts` exercises populated/null activity,
immutable store rows, complete verified maps, valid requests after rejection and
the existing fail-closed query convention using synthetic data. No native website
operation or compatibility qualification count is added.

## Verification

```sh
cd app/packages/backend
npx tsx --test test/*.test.ts     # counts grow as operations are added; the run prints the current totals
../../node_modules/.bin/tsc --noEmit -p tsconfig.json
```

Both pass as of 2026-10-28. The tests assert schema conformance for every 200 response
(required keys present, no keys outside the allowed set), pagination, sort direction and
null placement, address and userId lookup, batch omission behavior, the `maxItems`
boundary at 100 and 101, username existence true and false, search-v2 filtering and
pagination, overview fields and 404 handling, verified profile mapping and validation,
and that unimplemented routes still return 501.

`test/contract-conformance.test.ts` adds the reusable half: it validates each native
response against the documented schema for that operation and status code, and it
validates captured fixtures the same way. Captured routes outside the developer OpenAPI
(the `/services/...` internals) are reported rather than silently skipped.

## Provenance

Drafted by `claude-opus-4-6-thinking` through the Antigravity CLI, then reviewed,
corrected and completed under Hermes. Extended with search-v2, overview, and verified
endpoints under Antigravity.
