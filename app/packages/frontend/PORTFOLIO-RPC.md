# Live Solana portfolio boundaries

This note separates captured Pump evidence from the independently implemented
Solana JSON-RPC portfolio at `/portfolio`. The feature reads public mainnet
accounts. It does not reconstruct Pump's proprietary portfolio, position, PnL,
or trade-history services.

## Observed Pump evidence

The static operation inventory contains portfolio-related literals, but their
service origin and runtime behavior remain unresolved:

- `GET /portfolio-summary` occurs in
  `evidence/web/objects/767cc801e3f88f8b.js`, SHA-256
  `8fd66b61a591235d4e3b0509b23d067bb76e0c4ec2e8a4d5d5ff738e29808e12`,
  at UTF-16 range `[32642, 32666)`.
- `GET /portfolio-summary/chart` occurs in
  `evidence/web/objects/2b47dd0b38a1608f.js`, SHA-256
  `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d`,
  at UTF-16 range `[330095, 330125)`.
- `GET /user-portfolio/{userId}` occurs in
  `evidence/web/objects/0c88b57cea9aa9be.js`, SHA-256
  `137a2bf8282b85a4faa96b666dcfbe4e757553e2af9a00cb586752a3cb2af2c7`,
  at UTF-16 range `[14562, 14592)`.

These are inert static literals from `contracts/internal-operations.json`, not
qualified website request origins or compatible local implementations. This
feature does not call them and does not change the developer API compatibility
count.

## Declared Solana contract

The server adapter uses the official read-only Solana JSON-RPC methods:

- [`getGenesisHash`](https://solana.com/docs/rpc/http/getgenesishash) identifies
  the cluster and must equal the mainnet-beta genesis hash.
- [`getBalance`](https://solana.com/docs/rpc/http/getbalance) returns lamports and
  its context slot.
- [`getTokenAccountsByOwner`](https://solana.com/docs/rpc/http/gettokenaccountsbyowner)
  is called once for the SPL Token program and once for Token-2022, using
  `jsonParsed` encoding. Each response keeps its own context slot.

All calls use `confirmed` commitment. Live reads are opt-in: the server must set
`SOLANA_RPC_URL` (for example Solana's public `https://api.mainnet.solana.com`, or a
dedicated provider); when it is unset the route returns 503
`RPC_CONFIGURATION_INVALID`. Browser input cannot change the endpoint, and
`tests/live-portfolio.mjs` requires a server started with `SOLANA_RPC_URL` set.

## Local implementation

- Wallets, token accounts, mints, and owners must be canonical Solana public
  keys.
- Raw amounts are parsed as bounded unsigned integers and aggregated with
  `bigint`; JavaScript floating-point values are never the balance source of
  truth.
- Token accounts remain individually visible. Mint totals combine only accounts
  returned by one token-program query with the same mint and decimals.
- Duplicate account identities, unexpected program owners, unsupported parsed
  states, malformed quantities, and wrong-cluster responses fail closed.
- Token-2022 extension names returned by the parser are reported, but extension
  semantics are not interpreted.
- The configured RPC URL must be a public HTTPS hostname. Credentials,
  fragments, non-443 ports, IP literals, localhost/local domains, redirects,
  and DNS resolutions to private or reserved addresses are rejected. The
  selected public DNS address is pinned for the request.
- DNS setup has its own bounded wait using the configured per-call timeout,
  and observes the caller's cancellation signal before and during lookup.
  The portfolio, public-wallet-record and holder-configuration wrappers all
  pass that signal into setup. A setup timeout reports `RPC_TIMEOUT`; caller
  cancellation preserves its reason. This is a local transport policy, not a
  Pump API contract or an aggregate deadline spanning DNS and every RPC call.
  The setup timer and abort listener are removed on settlement. Node's pending
  OS lookup cannot itself be canceled through this API: its late result is
  observed and discarded, never used to initiate HTTPS after interruption.
  Timer values must be integer milliseconds from 0 through 2,147,483,647;
  ordinary reads retain their existing 10-second or 12-second phase limits.
- The browser calls only the same-origin `/api/portfolio` route. No private key,
  signing method, mutation RPC, or arbitrary user-supplied RPC endpoint exists.

`packages/backend/test/portfolio-dns-deadline.test.ts` exercises the maintained
live-read wrappers with mocked DNS and HTTPS only, including never-settling and
late lookups, cancellation, cleanup, rejected addresses and successful pinned
reads. Run with the existing backend Node loader: `node --import tsx --test
test/portfolio-dns-deadline.test.ts` from `packages/backend`. No DNS query, socket,
production RPC, wallet connection or transaction is involved in these regressions.

## Live qualification

`packages/frontend/tests/live-portfolio.mjs` loads the real page, submits a
public wallet, refreshes it, reloads at a mobile viewport, and validates the
mainnet genesis hash, reported slots, successful response shape, browser network
origins, request methods, console errors, and horizontal overflow. The retained
receipt and screenshots are in `visual/portfolio-live-20261028/`.

The retained response is a dated acceptance observation, not production data
for the page and not a cache or fallback. Every displayed successful result must
come from a new RPC response.

## Unknown and intentionally unsupported

Pump positions, cost basis, realized or unrealized PnL, token symbols, prices,
USD values, metadata authenticity, spam classification, historical activity,
and original Pump portfolio visual parity remain unqualified. Separate RPC calls
may observe different slots, so the UI explicitly does not claim an atomic
account snapshot.
