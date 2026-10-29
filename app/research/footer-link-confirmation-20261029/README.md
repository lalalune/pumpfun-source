# Footer links share the device confirmation preference

With the existing Privacy switch enabled, the unchanged footer opened Blog and
other external anchors directly. Create draft previews already used the same
captured preference/controller. This integration connects normal interactive
footer clicks to that controller without changing its URL rules or storage key.
The local shell supplies the same explicit capability as Create; the original
`WEB_SETTINGS_HUB` rollout remains unknown.

`FooterOutboundLinks` remains mounted when a Resources portal item unmounts. It
restores focus to the menu trigger or direct anchor, supports cancellation and
remembering, and shares immediate preference changes with Settings and Create.
An opening exception keeps a retry and native browser link available. A null
`window.open` result is not treated as a blocked popup or delivery receipt.
Failed persistence retains the source's page fallback and displays read-back
feedback. Original anchor attributes remain intact.

## Actual before and after

The base is `ef400863f4e476b2eaaab0866c0b1187d8060abc`. Its app tree is
`e3d6d8cd07df4f561a4fd058dad29d22de451bfc`, also the exact app tree obtained from
the read-only live main `9f9d94c56f7bbedb6c3e45a9e95c287321313621` before publication.
The same final test and producer were run against the base's three mounted
frontend files, then against the candidate. All other declared test/runtime
inputs were identical. `before/execution-inputs.json` and the current browser
receipt bind these inputs; `QUALIFICATION.json` lists the three differences.

The base fails the first assertion: Blog does not show confirmation with the
preference enabled. The candidate passes seven interactive workflows and one
SSR anchor-attribute check, with no page or console errors. The workflows cover
cancellation/focus, remembered choice and reload, portal teardown, mobile links,
opening exceptions/retry/native fallback, rejected storage and unchanged Create
preview interoperability. All 16 existing Settings tests and five existing
Create external-link tests also pass. Strict frontend typechecking, 29 affected
source/runtime/tamper tests, and app evidence verification (698 captures, npm
integrity, unchanged SDK sources) pass.

Two test-readiness corrections are explicit. The existing menu dismisses on
scroll, so the helper finishes its intentional scroll before opening it.
Settings dismissal waits for the URL change before reloading. Neither required
a product menu or history change. The initial raw outcomes remain preserved
privately; `before/menu-scroll-observed.json` retains the observed event sequence.

The initial JavaScript-disabled activation attempt was blocked by the existing
clickwrap overlay. Its raw report is retained as `before/no-js-blocked-report.json.gz`.
The final eighth check verifies SSR href/target/rel attributes and that visible
barrier only; it does not claim a usable JavaScript-disabled app workflow.

## Reproduce

Start the existing frontend separately on loopback, then run from the repository:

```sh
node app/tests/footer_privacy.browser.mjs \
  --base-url http://127.0.0.1:3010 \
  --output app/research/footer-link-confirmation-20261029/browser/verification.json
node app/scripts/original-privacy-external-links.mjs --check --check-browser --check-app-browser
node --test app/tests/original_privacy_external_links.test.mjs app/tests/original_source.test.mjs
python3 app/scripts/verify-evidence.py
```

The browser driver uses the existing frontend configuration with its server
startup disabled, one worker, a finite failure limit and the dedicated footer
spec. It records the declared source inputs before execution and checks them
again afterward. The existing Settings/Create specs were run unchanged through
an equivalent server-disabled configuration; their raw JSON report is retained
in `regressions-report.json.gz`. The actual frontend typecheck used
`tsc --noEmit --incremental false` with the existing pinned dependencies.

The current `--check-app-browser` selection points to this packet and binds the
runtime, mounted consumers, test/producer/verifier bytes and three screenshots.
The prior shared-Settings-host exception remains explicit: the receipt records
its executed hash, while later checks require the privacy row to stay mounted;
later unrelated host edits are not qualified. The original switch-only packet,
screenshots, producer and isolated controller receipt remain unchanged historical
evidence. Source/consumer/receipt/screenshot tampering and unsupported server
claims are rejected by the affected Node tests.

## Limits

This is authored local integration of an existing source-backed policy, not a
recovered original footer renderer or security boundary. Only normal footer
clicks and the existing Create consumer are connected; no global outbound-link
coverage is claimed. Opening uses an explicit test port; the one native fallback
receives controlled HTML without contacting the destination. The finite run
does not establish delivery, other browser engines, full browser-process restart,
upstream flag availability, backend compatibility or production acceptance.
No captures, contracts, dependency/SDK sources, global styles, clickwrap,
DropdownMenu or paused backend prototype were changed.
