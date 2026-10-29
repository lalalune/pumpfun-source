# Finite qualification

The final browser method reports **19/19 passed**: three new Highest market cap
workflow cases and all 16 retained Live cases. The same target case on exact
base `03fa4494f36449cd8fd63e121f12ca40bf57090f` fails at the actual HTTP response:
expected 200, received 404. The final source returns the 24 captured records in
their authenticated order, with local keyboard-expandable metadata, sibling
navigation/history and no media requests.

`checks.json` binds the files and compressed/raw log hashes. Source admission
compares every materialized frontend source file with its actual Git revision:
209 baseline files and 210 candidate files, all equal. The initial published
source head is `724d73a03c3b40d96789b3364bb8f6e7523071c3`, with exactly the same
full tree as local `57047e90`. The final local test revision is
`fb92d49884c609ff6522ace1a2a8d498d8e44006`; its only change is five test-readiness
lines. No production source or package-script bytes change between those two
stages. Later qualification additions contain the receipts and this note.

Run the original-source binding and data/negative cases from `app`:

```sh
node scripts/original-live-highest.mjs
corepack pnpm test:live
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
python3 -m unittest discover -s tests -p test_progress.py
```

They pass 22 data/source cases (7 new and 15 retained), frontend typechecking,
698 captured-object checks, npm integrity, 31 unchanged SDK sources and progress
plus nine progress tests. Required root checks pass nine captures and ten
tooling tests on the initial public source head; the exact final-head result
is recorded separately in the PR. No production build or full application
browser suite is claimed.

The browser uses the existing closed local-browser fixture, not an inference
of original or user consent. Its actual controller, config and executed
maintained test copy are retained here. The sole retained-test adaptation is
one strict safety-origin literal, 3010 to 3019; GET/HEAD-only admission and all
existing assertions remain. Every browser request admitted by these new cases
is local; there is no backend/provider API dependency in this workflow.
`preflight-inputs.json` authenticates the exact posts/users/following seed inputs
used by the unchanged adjacent-route controls.

The initial browser run is preserved as **18 passed / 1 failed**. Native
disclosures passed at 320px, then the 1280px Enter action left the first card
closed. That method called `focus()` without establishing keyboard focus while
the shared startup dialog could still run its focus cleanup. One instrumented
probe passed both widths and recorded trusted Enter targeting a focused
`SUMMARY` with `shellInert:false`. It does **not** prove the initial failure's
cause. The final method explicitly waits for the existing closed-fixture
overlay DOM to disappear and the shell to be non-inert, asserts summary focus,
then retains every open/close, full-address, overflow and reload assertion.
No product workaround or consent/native-details defect claim follows from the
initial result. The final exact-base target and full 19-case candidate run use
the same corrected test file. No retries are configured.

The first post-rebase headless `test:live` command also found omitted sparse
test inputs. Its failed log and exact Git restoration manifest are preserved;
the actual command then passes all 22 cases. This is an input-staging failure,
not a product/source correction. Existing React script-tag/NO_COLOR dev warnings
remain in raw logs. The baseline `--max-failures 1` stop is also retained.

The actual 320px and 1280px screenshots show the new native disclosures. The
mobile browser scrolls the focused summary into view. No original child-route
HTML exists in this corpus, so these are local UI evidence, not before/after
original visual-parity measurements. All 24 identities already occur in the
42-record Most viewers section. No ranking formula, current market cap,
broadcast status, additional unique streams, API compatibility, playback,
wallet/chain behavior, excluded token navigation or feature credit is claimed.

The owned server/browser exited after the run. Its inactive Next cache was
removed; raw source, logs, screenshots and traces remain in the private
qualification directory. No captured object, SDK source or dependency lockfile
was changed.
