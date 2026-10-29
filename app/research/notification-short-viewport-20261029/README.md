# Settings notification reference in short landscape

At base `094a06f18df738d41e77070c1a009e135671ac1a`, the default read-only Notifications panel clips its existing Done control at 568×320. The button is 44px high, but only 21.390625px intersects the dialog's clipping region. Its geometric center hits `DIALOG`; trusted pointer-down/up/click events reach the dialog rather than `BUTTON`. The dialog still closes through outside dismissal. This is a visibility/hit-target defect, **not a lost-close or lost-data result**.

Extend the existing compact frame's `min(90dvh, 720px)` height to `max-height: 480px`. The six added CSS lines give the header/footer enough space at the tested landscape size while keeping the existing content scrollport. No component, data, label, controller, URL or backend behavior changes.

| Actual run | Result |
| --- | --- |
| Original outcome-only probe | 2 PASS: both clicks closed the dialog and preserved unrelated URL state. That oracle did not establish Done activation. |
| Corrected frozen probe on unchanged base | Desktop PASS, landscape FAIL: trusted click target is `DIALOG` rather than `BUTTON`/`Done`. |
| Exactly the same frozen probe after the CSS change | 2 PASS: both expose all 44px and trusted center clicks target `BUTTON`/`Done`. |
| Final test with added scroll control + retained Settings controls | 18 PASS: 3 new cases and 15 unchanged Settings cases. |

`OBSERVATIONS.json` decodes the raw reports. At 1280×900 the Done rectangle and all measured ancestor rectangles are identical before/after; this is a geometry control, not a pixel-parity claim. At 568×320, Done moves from y270.796875–314.796875 to y258–302, fully inside the dialog. Trusted wheel input moves the existing content from scrollTop0 to500 (clientHeight40, scrollHeight1541). All thirteen reference rows remain present; there are no preference switches in the default view.

The corrected pair used frozen `corrected-probe.spec.ts` SHA-256 `7d0a56fd06fcbc2d212be757646fbcfd7cc0d4092a1608208454317a934fe158` before/after. The final maintained test formats those same assertions and adds the scroll case. `SOURCE-BINDING.json` records both hashes and the sole runtime delta. Raw reports/logs are losslessly compressed in `raw/`; pre-click screenshots show the actual clipped and corrected control. The first mistaken blanket-negative interpretation is retained under `historical/` and explicitly superseded by the actual recorded hit targets. No historical result was relabelled.

Validation completed on the stated base plus only this CSS change and the final test:

- 18 browser cases PASS on Chromium/Next16.4.1 at localhost3027, including SSR/hydration, focus, Escape/Back, search, URL preservation, four existing viewport sizes and body-lock restoration.
- The one existing transport/no-permission browser case hard-codes origin3010 and was excluded from this3027 batch; no complete16-case Settings suite claim is made.
- Frontend TypeScript check PASS; 10 Settings model, 29 notification state/action and 3 source-contract tests PASS.
- Application verifier PASS:698 captured objects, npm integrity and unchanged SDK sources.
- Progress check PASS after restoring the exact tracked root README omitted by the sparse checkout. The initial missing-file setup failure is preserved separately. No ledger, progress report or root README change is proposed.

Repeat the maintained three-case regression using the repository's normal browser configuration (which starts localhost3010):

```sh
cd app
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test tests/notification-short-viewport.spec.ts
```

For the exact historical pair, use isolated base/fixed checkouts with `corrected-probe.spec.ts` copied to `packages/frontend/tests/notification-short-viewport.spec.ts` and `paired-browser-config.ts` copied to `packages/frontend/playwright.notification-short.config.ts`. Start Next manually on localhost3027, then run the pinned Playwright CLI with that config and `--max-failures=1`. It is the same test/config on both sources; only the six CSS lines differ. `controls-browser-config.ts` records the final18-case configuration; its historical command additionally excluded `settings interaction makes no service requests` for the origin reason above. The final product/test paths, raw source preimages and hashes permit independent reproduction without captured-JavaScript execution.

This qualifies a local reconstructed layout at the stated sizes and browser. Other engines, extreme window heights, OS/browser zoom matrices, native/account notifications, delivery, permission requests, original geometry/translation parity and feature-completion credit remain unqualified. Captured source already maps the reference fields; that mapping is unchanged and does not prove this local layout. No account notification adapter, synthetic current account data, production service, wallet or authentication flow was used. All servers are stopped; only owned inactive generated Next cache was removed after retaining source hashes/logs/screenshots.
