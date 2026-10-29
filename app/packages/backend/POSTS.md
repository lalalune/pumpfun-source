# Native /posts implementation

Status: six operations of the 67 documented developer API operations are now served natively
alongside the existing seven `/users` operations (total 13 native operations).

| Operation | Path | Response |
| --- | --- | --- |
| `get_posts` | `GET /v1/posts` | 200 `{ "posts": Post[] }` |
| `get_posts_by_postId` | `GET /v1/posts/{postId}` | 200 `{ "post": Post }`, 404 on miss |
| `get_posts_by_postId_replies` | `GET /v1/posts/{postId}/replies` | 200 `{ "replies": Post[], "nextCursor": string \| null }`, 404 on miss |
| `get_posts_by_postId_likers` | `GET /v1/posts/{postId}/likers` | 200 `{ "likers": Profile[], "hasMore": boolean }`, 404 on miss |
| `get_posts_by_postId_quotes` | `GET /v1/posts/{postId}/quotes` | 200 `{ "quotes": Post[], "nextCursor": string \| null }`, 404 on miss |
| `get_posts_by_postId_reposters` | `GET /v1/posts/{postId}/reposters` | 200 `{ "reposters": Profile[], "hasMore": boolean }`, 404 on miss |

Unimplemented routes continue to fall through to fixture replay, and to `501 COMPATIBILITY_NOT_IMPLEMENTED`
when no fixture matches.

## Source layout

- `src/posts-store.ts` - `PostStore`, deterministic in-memory store with O(1) post lookup,
  keyset-paginated replies and quotes, offset-paginated likers and reposters, and hydration
  linking to `UserStore` for author and profile lookups. `defaultPostStore` is the singleton.
- `src/posts-seed.json` - hand-authored synthetic post fixtures (roots, replies, quotes, reposts,
  deleted, and hidden posts), all conforming to `Shared_47a8d5353d95`.
- `src/posts-routes.ts` - the six native Fastify route handlers.
- `src/app.ts` - `buildApp()` registers post routes before generic fixture replay and excludes
  all six OpenAPI path patterns in `NATIVE_ROUTES`.
- `src/schema-validator.ts` - JSON Schema validator resolving `$ref` against the OpenAPI root,
  honoring `additionalProperties: false`, required keys, and `nullable` across `allOf` wrappers.
- `test/posts.test.ts` - comprehensive functional, pagination, boundary, route ordering, and
  schema tests.
- `test/contract-conformance.test.ts` - validates each native `/posts` response against its
  documented 200 schema in `contracts/developer.openapi.json`.

## Data source and its limits

The post seed is hand-authored synthetic data shaped strictly to the contract schema
`components.schemas.Shared_47a8d5353d95`. It is **not** captured production traffic, and no real
pump.fun posts or interactions exist behind these rows.

`app/AGENTS.md` forbids fabricated domain responses, so this data is labelled wherever it surfaces:

- `SYNTHETIC_POSTS_SEED` and `DATA_SOURCE = 'synthetic-seed-play'` in `src/posts-store.ts`.
- Every successful native response carries `X-Reconstruction-Data-Source: synthetic-seed-play`.
  Error responses carry no marker because they contain no domain data.
- Contract and functional tests assert the marker header is present on every 200 response.
- Post author and interactor profiles reuse `UserStore` and its existing seed data
  (`src/users-seed.json`) rather than inventing a separate user model.

## Documented assumptions

The contract does not specify these behaviors. Each was decided deliberately; changing any of them
is a contract decision, not a bug fix.

20. **Lookup miss on `GET /posts/{postId}` and sub-resources**: Returns `404 {"error":"NOT_FOUND"}`
    when `postId` does not exist, or when the post is marked `deleted: true` or `hidden: true`.
    `GET /posts/{postId}` also returns 404 for a repost whose target is unknown, deleted or hidden,
    because `reposted` is "always present on a served repost" (unlike `quoted`, which is "null when
    the target is hidden or deleted"). The OpenAPI specification documents only 200 and transport errors in its response table, but
    its prose descriptions explicitly mandate "404 for unknown, hidden or deleted posts" and
    "404 unless the post is live".
21. **Omission in `GET /posts`**: Any requested id that is unknown, marked `deleted: true`, or
    `hidden: true` is omitted from the `posts` array without leaving a placeholder or error, matching
    the contract note ("Request order; unknown, hidden and deleted ids leave no placeholder").
    A repost whose target is unknown, deleted or hidden is omitted the same way (item 20).
22. **Request order preservation in `GET /posts`**: Posts are returned in the exact order specified
    in the `ids` query parameter.
23. **Duplicate id collapse in `GET /posts`**: Duplicate IDs in `ids` collapse to their first
    occurrence ("duplicates collapse").
24. **`ids` query parameter validation in `GET /posts`**: Missing or empty `ids` query returns
    `400 {"error":"IDS_REQUIRED"}`. More than 100 IDs returns
    `400 {"error":"TOO_MANY_IDS","maxItems":100,"received":N}` per `maxItems: 100`. Both comma-separated
    lists (`?ids=a,b`) and repeated query keys (`?ids=a&ids=b`) are supported.
25. **Opaque keyset cursor encoding**: Replies (`GET /posts/{postId}/replies`) and quotes
    (`GET /posts/{postId}/quotes`) paginate on an opaque URL-safe base64url-encoded JSON tuple
    `[createdAt, postId]`. Keyset ordering is strictly newest first (`createdAt` descending, with
    `postId` descending tie-breaker).
26. **Cursor termination**: When more rows exist after the current page, `nextCursor` is returned as
    a string. When no more rows exist, `nextCursor` is `null`. Clients page on `nextCursor !== null`,
    never on array length.
27. **Malformed cursor handling**: If an unrecognized or malformed cursor string is passed, the server
    returns `400 {"error":"INVALID_CURSOR"}` rather than silently defaulting to page 1.
28. **Reply and quote limit clamping**: When `limit` is omitted, it defaults to 50. Values above 200
    clamp to 200. Non-positive or zero values clamp to 1.
29. **Liker and reposter offset pagination**: `offset` defaults to 0 (clamps to min 0, max 10000).
    `limit` defaults to 50 (clamps to min 1, max 200). `hasMore` is `true` if `offset + limit < total`,
    `false` otherwise. The local user store accepts either a wallet address or a user ID for an
    account. Resolve these aliases and omit missing accounts before pagination; repeated references
    to one account occupy one row, retaining its first occurrence in the supplied order. This local
    projection policy does not establish an upstream ordering or identity-resolution rule. Seeded
    aggregate like/repost counts remain supplied facts, not totals derived from these lists.
30. **One-level embeds without recursion**: Posts embed immediate parent (`parent`), quoted post
    (`quoted`), and reposted post (`reposted`). To avoid recursive cycles and conform strictly to
    `Shared_47a8d5353d95`, embeds have their own `parent: null`, `quoted: null`, and `reposted: null`.
31. **Tombstone representation**: A deleted parent in a reply embed survives as a tombstone
    (`deleted: true`, `author: null`, `content: null`, `mediaUrl: null`, `mentions: []`, but with
    IDs, counts, and `createdAt` intact), matching the contract description.
32. **Unauthenticated viewer stamps**: Anonymous requests receive `hasLiked: null` and
    `hasReposted: null` on root, reply, and quote rows. On repost rows, `hasLiked: false` and
    `hasReposted: false` per the contract note. `viewerFollows` is omitted from liker and reposter
    profiles.
33. **Route ordering**: Sub-resource routes (`/v1/posts/:postId/replies`, `/v1/posts/:postId/likers`,
    `/v1/posts/:postId/quotes`, `/v1/posts/:postId/reposters`) are registered before `/v1/posts/:postId`
    so `:postId` never captures sub-paths.
34. **Duplicate query keys on posts reads**: A repeated scalar query key on the four paginated
    sub-resources returns `501 {"error":"DUPLICATE_QUERY_KEYS_UNIMPLEMENTED"}`, matching the
    replay harness and the native /users and /following reads: the scalar OpenAPI parameters do
    not establish semantics for repeated keys, so selecting a value or coercing an array would
    invent them. Previously a repeated `limit`/`offset` silently fell through to the default page
    size with 200, and a repeated `cursor` was misreported as `400 INVALID_CURSOR`. The single
    `/v1/posts/:postId` read takes no query parameters but applies the same guard: it previously
    served 200 past any repeated key. The batch `/v1/posts` route is exempt: repeated `ids`
    keys are documented to collapse (item 24).

## Local cursor integrity

The declared developer contract is `https://api.pump.fun/v1`, not a website feed
service. In `contracts/developer.openapi.json` (version `0.294.0`), both
`get_posts_by_postId_replies` and `get_posts_by_postId_quotes` describe a cursor
as the previous response's `nextCursor`, omitted for the first page. Post
`createdAt` is a nullable string described as ISO 8601. The specification does
not disclose the upstream cursor encoding, tie-breaker, or malformed-cursor
error policy. The tuple codec and `400 INVALID_CURSOR` above remain local design.

The local decoder now accepts only the unpadded base64url form emitted by
`encodeCursor`, valid UTF-8 JSON containing exactly two strings, and a timestamp
that the existing local date comparator can evaluate finitely. The empty first
string remains the existing sentinel for a null timestamp. No new timestamp
normalization or narrower ISO grammar is imposed: offset and fractional-second
forms retain their original bytes. A finite JavaScript date parse is not a
complete ISO 8601/calendar validator or evidence of upstream acceptance.

Previously, Node's permissive base64 decoder could ignore appended garbage;
an unparseable timestamp then compared as `NaN` and silently returned a successful
empty page. An explicitly empty cursor also reset pagination to the first page.
Both reply and quote reads now reject those malformed inputs without a synthetic
data marker. Omitting the cursor still selects the first page. Existing emitted
cursors, newest-first ordering, tie-breaks, null-time ordering, unknown-post
precedence, and the API-key gate are unchanged.

`test/posts-cursor.test.ts` pins the documented boundary, all seed cursor bytes,
malformed encoding/tuple/date failures, and full multi-page traversal at equal,
offset-equivalent, null, and pre-epoch timestamps. Its custom rows are synthetic
test inputs only. This correction adds no operation, persistence, website feed,
production observation, or native compatibility qualification.

## Verification

```sh
cd app/packages/backend
npx tsx --test test/*.test.ts     # counts grow as operations are added; the run prints the current totals
../../node_modules/.bin/tsc --noEmit -p tsconfig.json
```
