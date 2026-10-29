# Portfolio pending navigation reproduction

Base: `ef400863f4e476b2eaaab0866c0b1187d8060abc`.

The Chromium workflow uses the real local Next page/router and local API, with
`SOLANA_RPC_URL` empty. It delays the actual RSC navigation response; it does
not substitute a portfolio payload or contact mainnet. The input starts at the
public system-program address. After Clear, type the public SPL Token program
address while navigation is pending, then release that response.

`before.png` shows the newer draft erased by the old keyed component remount;
`after.png` shows that same draft retained after navigation to `/portfolio`.
The two regression cases also cover delayed submission and Back/Forward.

From `app/packages/frontend`:

```sh
pnpm exec playwright test --config playwright.portfolio-draft.config.ts
```

Both cases fail on the base and pass with the fix. This is local navigation
evidence, with no claim about production portfolio compatibility or balances.
