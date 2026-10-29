# Actual finite browser qualification

Frozen source: `07bb57f3b515cb30b1e6c4ed6aeabdcf1391f218`.
Base: `604917c16410d67d9b981305e28e160a93728f50`.
Public source: `9667a81fd01ac7fe1e0c4180f6e576168993d499`, whose complete
source tree is identical to the measured local source above.

The same final-method target first verifies that the actual base `/live`
response is HTTP 200 and its 42-card archive is available, then fails because
the Archived highlights workflow is absent. The candidate passes all **20
browser cases**: four new Hero workflows and all 16 maintained Live controls,
with zero failures, skips or retries.

The new cases cover the actual six-record mount/order/initial selection,
Next/Previous wraparound, direct/native keyboard selection, retained focus,
320px/1280px overflow, selection without navigation, local read/media
boundaries and cooperation with search, URL metadata selection, Escape and
reload. The maintained test file executes unchanged at its existing strict
3010 origin. The browser uses the existing closed local-browser fixture; no
original or user consent state is inferred.

Every frontend source file present in each runtime phase is authenticated
against its actual Git revision: **209 base files and 213 candidate files**.
The complete manifests are retained losslessly as gzip files, with compressed
and decoded hashes in `checks.json`. The executed controller/config and exact
posts/users/following seed preflight are included. It restores only owned
runtime source files to the base for the first phase, then restores and
re-authenticates the candidate before the second. The new test and CI/docs
remain available as the probe; no response body or data fixture is substituted.

Other completed checks:

- Source proof authenticates five factory variants, the actual initial-data
  consumers, initial/loop/direct-selection boundaries and six-slot SSR state.
- Existing `test:live` runs 15 retained Live cases and seven new Hero
  data/source cases: **22 passed**. Malformed, missing, extra, duplicate,
  unresolved, unexpected-identity and inconsistent metadata fail closed.
- Frontend typecheck passes. App evidence checks pass all 698 objects, npm
  integrity and 31 unchanged SDK source files. Progress and nine progress
  tests pass.
- Required root checks pass nine captures and ten tooling tests on the frozen
  source. The exact final public-head result is recorded separately in the PR.

The two candidate screenshots show actual selected metadata and native focus.
The mobile browser scrolls its focused navigation control into view, so its
viewport image is not a complete top-of-page image. No screenshot was edited.
No original visual/layout parity is claimed; this is a metadata-only local
presentation of the recovered selection behavior. Existing NO_COLOR and React
script-tag dev warnings remain in raw logs. The expected baseline
`--max-failures 1` stop is preserved.

These six records are existing identities in the Most viewers archive. No
additional unique streams, current-live status, provider query, player/mute,
financial values, analytics, excluded coin-detail action, wallet/chain mutation,
native backend/API compatibility, full production build, whole-app browser
suite or feature credit is claimed. #1570's second-section route and the
separate selection PRs are not composed here; retain both CI additions during
integration.

The owned server/browser exited successfully after the finite run, its port
was released and only its inactive Next cache was removed. All source, raw
logs, screenshots and traces remain in the private qualification directory.
Captures, SDK source and dependency lockfiles are unchanged.
