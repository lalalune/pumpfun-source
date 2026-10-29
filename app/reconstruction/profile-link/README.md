# Trader identity → known local profile

The native trader board shows identities as plain text. Both retained original
`996005` trader-row variants instead supply `walletAddress` to `409954.o`.
This unit recovers that complete ProfileLink component and its ordinary-click
guard, and uses it for identities that the existing offline profile page can
actually display.

The local adapter admits a link only when `(walletAddress, userId, username)`
exactly matches a person in the existing hash-bound user/post dataset. It uses
the same seed SHA-256 pins and validators as `/profile/[id]`. Unknown, mismatched
or corrupt/unavailable local data leaves the name plain. The server passes only
those three public synthetic identity fields to the client. This is a display
availability hint, never account ownership or authentication. The destination
already labels itself **Local synthetic example — not a real Pump.fun user**.

## Original source and retained boundaries

`contract.json` records raw-capture hashes, actual factory registrations,
UTF-8/UTF-16 expression ranges and all retained origin metadata. The two physical
`409954` variants have different factory hashes but their **complete component
ASTs agree after lexical binding normalization**. The common normalized AST is
`1cefef53dec5db2a4829c4d049508ca4f8a9b0e44977f1c56130df3660f626ca`.
The emitted editable module preserves the full component, inline context hook,
compiler caches, props, nullish href override, callback order, pending state and
class-merger call. No captured bundle or registration factory is executed.

- `409954.o`: complete component from `eb0b23ee6feb7543.js` and
  `97dc53c5c25c1fdc.js`; neither is selected as a deployment winner.
- `432405.f`: complete default-prevented/button/modifier guard.
- `146695.$`: reused unchanged from accepted search-navigation recovery. No
  additional recovery credit is claimed for that URL builder.
- Both actual `996005` consumers: the row-cover call supplies the wallet address.
  The rest of the original row/avatar/follow implementation is outside this unit.

React/compiler runtime, Next Link, class merging and the original private
navigation provider remain explicit capabilities. The native adapter uses real
React/Next, the captured null-default context, and a local class join for its
fixed class set. It does **not** implement the unknown provider or claim parity
with the original Tailwind merger. No private provider/auth state, remote profile
discovery, follow action, media loading policy, ranking or PnL calculation is
invented. Links disable prefetch and identify their local destination.

## Repeatable checks

From `app` with the pinned existing pnpm 10.24 installation:

```sh
node scripts/original-profile-link.mjs --check
node --experimental-strip-types --test tests/profile-link.test.mjs tests/original_source.test.mjs
pnpm -r typecheck
python3 scripts/verify-evidence.py
# Reserve a Next slot first. Own fixture starts/stops Next and loopback Fastify.
PUMP_PROFILE_PORT=3027 PUMP_PROFILE_PHASE=fixed node packages/frontend/node_modules/@playwright/test/cli.js test --config tests/browser/profile-link.playwright.config.mts
```

The loopback harness adapts prior selected-measure test infrastructure, not new
original application logic. Its explicit child-only environment constructs a
public synthetic key from a fixed prefix and `"A".repeat(49)`; no parent key is
read. The existing native API key gate remains active. Test redirection confines
the documented developer read to the owned Fastify handler and preserves the
request path/query/method/headers/signal. Browser responses are never fulfilled
with JSON. All captured material and prior packets remain unchanged.

Finite before/after outcomes and exact tested revisions belong in the separate
qualification receipt. Synthetic local functionality does not establish native
production API/provider compatibility, visual parity, financial correctness or
milestone completion. Original material retains its authorship; this project
makes no ownership or license inference.
