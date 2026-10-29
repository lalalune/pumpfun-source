# Connected public-address mainnet overview

After explicitly connecting a Wallet Standard public address, the chooser
offers **Read public mainnet overview**. Connecting alone makes no balance
request. The overview displays the exact returned SOL quantity, separate SPL
Token/Token-2022 account and mint counts, confirmed context slots, UTC
observation time and sanitized RPC host. Counts are inventory, not cross-token
monetary totals. No prices, PnL, positions or rewards are inferred.

This combines two existing capabilities: the source-bound public-address
workflow from [PUBLIC-WALLET-EVIDENCE.md](PUBLIC-WALLET-EVIDENCE.md), and the
existing public-chain read contract in
[PORTFOLIO-RPC.md](PORTFOLIO-RPC.md#declared-solana-contract). It is a local
integration, not proof of the original authenticated wallet widget or private
server semantics. A public address and its holdings do not authenticate the
application or establish ownership/spendability. Provider login and signing
remain disabled. The reader always requests mainnet; the connected wallet may
be using another network.

## Used path and lifetime

Connected address → explicit read button → unchanged address-bound
`holder-rewards/read-balances.ts` helper → credentials-omitting, no-store GET
`/api/portfolio?address=…` → existing pinned HTTPS RPC service. Despite its
historical `readPdaBalances` name, that helper accepts any public address and
does no PDA derivation. It verifies the response address, cluster, token-program
roles and owners. This unit aliases its name locally; its bytes are unchanged.

The overview is keyed by the connected address. Account change, revocation,
disconnect, dialog close and navigation discard the result and abort/invalidate
pending reads. A20-second local deadline leaves an honest error and keeps
disconnect available. Refresh removes the previous observation while awaiting
the next result; failures never substitute a cached, historical or zero value.
Rate-limit and timeout messages are bounded local strings; provider bodies are
not displayed. This view saves no data to cookies, local/session storage or a new
page URL. The public read supplies no authenticated principal.

The connection controller, shared balance reader, portfolio API route, RPC
transport, schemas, SDK, captured sources and dependencies are unchanged. Exact
preimage hashes are retained in
`research/public-wallet-overview-20261029/DEPENDENCIES.json`. Existing #774,
#815 and portfolio work are dependencies, not new recovery claims. The auth
milestones remain pending; only evidence pointers/narrative are updated.

## Validation

```sh
pnpm --filter @pump-reconstruction/backend exec tsx --test ../../tests/public_wallet.test.ts
node --test tests/holder_public_balances.test.mjs tests/public_wallet_protocol.test.mjs
pnpm --filter @pump-reconstruction/frontend exec tsc --noEmit --incremental false
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/public-wallet.spec.ts --max-failures=1
```

The existing14 controller, seven balance-client and one real HTTP/Chromium
protocol checks pass, as does frontend TypeScript. They exercise the reused
foundations, not this new mounted view. Nine new product cases are authored
alongside the six existing public-wallet cases: explicit/no-cookie read, exact
SOL/inventory/provenance, retry/rate limit, wrong identity, account changes,
disconnect, close, deadline and320/1440px layout. Their actual Next results and
full production qualification are pending until recorded. Synthetic wallet and
portfolio responses are test inputs; no live-chain observation, original API or
visual parity, wallet signing or native developer-operation credit is claimed.
