# Local user search in the shared dialog

The shared SearchDialog now consumes the maintained user-search query adapter
instead of only handing every submitted term to the historical coin snapshot.
Typing finds the five existing local synthetic profiles and their exact profile
links. Enter still submits to Explore; this does not add identifier resolution,
coin search, a live users service or an authenticated viewer.

## Source boundary

[The original user-search reconstruction](../../reconstruction/user-search/README.md)
binds actual **238128 SearchDialog -> 600775.N** across three authenticated
physical source contexts. Its unchanged `query.mjs` supplies the two UTF-16-code-
unit threshold, 500 ms debounce duration, per-query callback snapshot, request
shape/status hook and two-pass user/labelled-wallet selection. Its source verifier
still authenticates those factories without executing any captured bundle.
A companion TypeScript declaration types the new host; no generated adapter or
provenance hash is changed.

`LocalUserSearch` supplies a bounded timer and a first-page HTTP port. A separate
observer synchronizes the native dialog open attribute, including its initial
state, and disconnects on unmount. The existing source-bound shortcut effect and
its provenance fingerprint remain unchanged. The host honors
query enablement, forwards the AbortSignal and request options to a same-origin
local GET, runs the original non-OK response hook, validates the local projection,
and applies the original selection. A new trimmed term immediately hides the
old displayed rows. Changed terms, dialog closure and unmount clear the timer,
abort the request and invalidate its callback, even if an injected transport
ignores abort. These lifecycle guards are local host behavior; the source unit
requires its consumer to own scheduling. There is no TanStack/React-compiler
runtime, 30-second cache or full original hook lifecycle claim.

The seed has only five rows, all within the source query's default first-page
limit of 20. This host does not add remote pagination. Raw wallet-label presence
is preserved, including the empty string: the source selector consequently treats
these existing seed rows as wallet-pass rows. It does not reinterpret empty labels
as user rows or use the displayed count as a pagination cursor. Labels in the UI
are generic local profiles/groups, not a claimed upstream row classification.

## Local read boundary

`GET /api/local-users/search?q=...` is an authored local route, not a website or
developer API replacement. It reads the existing users and posts files on the
server, pins both hashes through the existing profile parser, and validates the
same profile dataset used by exact profile navigation. `UserStore.search` supplies
the existing local substring matching and seed order with labelled wallets
explicitly included. These are local model choices, not production search-v2
ranking or search semantics.

The response contains only validated address/userId, optional wallet_label,
display name, canonical profile identifier, person/group kind and banned marker.
Original bio, images, header, social URLs, badges and activity fields do not enter
this response. The browser verifies the small projection and unique canonical
identifiers before rendering links. No API bearer key, production destination,
viewer resolution, ownership, preference write or wallet signature is involved.
Same-origin request credentials do not establish authentication; the local route
ignores cookies and reads only the fixed public synthetic files.

Local query admission requires exactly one q, no unknown keys, 2..200 trimmed
UTF-16 code units and no other request parameters. Invalid queries return a local
400 before reading files; missing, changed or invalid seeds produce a bounded
503 without leaking filesystem paths. These statuses are local policy. Successful
and failed responses are no-store and identify synthetic-seed-play. No production
fallback is configured. A valid unmatched term produces an explicit empty state.

## Validation and limits

- Baseline: the new Alice-result/navigation case fails because no result link exists.
- Six host tests pass for seed reads, preserved empty labels, five exact identities,
  served ordering, empty matches, query bounds, changed/missing posts or users,
  safe projection and source snapshot/selection behavior.
- The unchanged original adapter's ten tests and AST source verification pass.
- Thirteen browser cases pass: five new cases for result navigation, 499/500 ms
  timing and UTF-16 admission, stale response rejection, close cancellation,
  unavailable reads and Enter fallback; eight existing Escape, shortcut,
  keyboard, history and delayed-Clear cases.
- Local mobile/desktop screenshots are under `visual/local-user-search-20261029/`.
  No original screenshot with equivalent query/data is available. The inline list
  layout, disclosure and error copy are local design; visual parity and complete
  SearchDialog/API compatibility remain unqualified. No milestone status changes.
