# Public-wallet chooser readiness

The initial HTML offered an enabled Sign in button before its client-only chooser
could handle it. Under delayed local client boot, one accepted click disappeared:
after the client loaded, the actual dialog mounted in the closed state. This can
make the public-wallet entrypoint appear unresponsive on the first activation.

`AuthControl` already has a `mounted` flag for its dialog portal. The trigger now
uses that same flag for native `disabled` semantics. It becomes actionable when
the chooser can mount. No new readiness state, event listener, provider, session,
wallet account access, network request or signing capability is introduced.

## Original source and attribution

[AUTH-INTERFACE-EVIDENCE.md](AUTH-INTERFACE-EVIDENCE.md) already attributes the
captured Topbar/hydration source. Topbar 400466 imports 170450, uses its hydration
flag for both branches, renders a disabled `sign-in-prepaint` fallback before
hydration and an interactive signed-out `sign-in-button` after it. Hook 170450
uses a true client snapshot and false server snapshot. This restores a local
boundary supported by those captured source instances, not a new discovery of
authentication/provider behavior or complete original parity.

`PUBLIC-WALLET-READINESS-SOURCE.json` binds two physical factories and six AST
witnesses to whole-capture hashes, UTF-16 ranges and strict UTF-8 byte ranges.
The verifier reuses the source primitive from #684 and never executes captured
JavaScript. A global runtime registration winner is not claimed.

## Reproduction and finite qualification

```sh
node scripts/original-contracts/public-wallet/readiness.mjs --check
pnpm --filter @pump-reconstruction/backend exec tsx --test ../../tests/auth_interface.test.ts ../../tests/public_wallet.test.ts
pnpm --filter @pump-reconstruction/frontend exec tsc --noEmit --incremental false
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/auth-first-open.spec.ts tests/auth.spec.ts tests/public-wallet.spec.ts --max-failures=1
```

Base `ef400863f4e476b2eaaab0866c0b1187d8060abc`, with the test/source witnesses
only at `976ae23a4c67968a1c111d66bf326b0f7d86b55d`, fails the new actual-browser
case: the offered click is accepted, then the real mounted dialog remains hidden.
Candidate `80c99141342ac7aa84af14235fbd136396024bf8` changes one runtime property
and passes the identical case plus all 12 existing runnable auth/public-wallet
cases. Seven opt-in synthetic-adapter cases are explicitly skipped: **13 passed,
7 skipped, 20 discovered**, not 20 passed. Existing 28 model cases, captured AST
verification, frontend TypeScript, 698-object app evidence and progress (9 tests) pass. Required root gates verify nine captures
and pass ten tooling tests.

The regression holds only local Next client scripts. If the server offers an
enabled trigger it clicks exactly once before resuming scripts; otherwise it
resumes scripts and clicks once the trigger is enabled. Both paths require the
real chooser to become visible and ready. It never waits for the portal before
activation, retries the click, increases a deadline or adds a product test port.

`visual/public-wallet-readiness-20261029/` retains raw logs, before screenshot,
source bindings and the complete failing assertion. The raw failure trace is
kept locally with its hash; the public call excerpt is explicitly partial.
After screenshots document the separate existing wallet-connection cases.
No signing/live provider/authentication/private API, visual equivalence or full
production-build claim is made for this one-property source change. Existing
public-wallet attribution and pending auth milestones remain unchanged.
