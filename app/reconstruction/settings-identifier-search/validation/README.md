# Frozen native Settings search qualification

Run from `app/`. Final same-method baseline:
`61a6a0cf9c379cb549beb8b924e650f177846d54`.
The one-line product candidate:
`af26533494f4f269c09ccbfb5a13f6037fcd799c`.
The actual Next Settings browser method failed causally at both 390px and 1280px
on baseline and passed both cases on that candidate. Ordinary/accented queries
and unknown/literal-dotted negative controls passed on both. The fixed cases
also reached focus, normal Done dismissal and URL cleanup checks. These are
actual local Next page GETs and DOM interactions, without fulfilled responses
or setting-control activation. No backend/service compatibility is inferred.

Earlier method `721c7d517fcba000768ab0caf8860bfc1f5a42d0` failed both browser
cases before the target assertion because a status locator matched the native
result count and row feedback. Its raw log and observations remain separate.
Only that count selector changed before final baseline qualification; the
product remained unchanged. Model tests on the earlier head recorded 11 passes
and two identifier failures. Candidate model/shared-source tests recorded
24 passes (13 model plus 11 shared-source); those executions are not relabeled.

Candidate typecheck then caught the new test config spreading an `unknown`
synthetic origin entry. Head `b74c1a175ca8fcdf592077c7f2ac247fa5c61e49` changes
only an explicit structural type assertion in that config; it changes no
product, model, browser spec or runtime operation. TypeScript 5.9.3 emits
byte-identical ES2022/ESNext JavaScript before and after that type-only change.
The compiler output/record is included. This is **not** a claim of Playwright
source-map identity or a new browser run at the typing-qualified head.
Three-workspace typecheck passes there; the earlier failure is retained.
698 evidence checks and nine progress tests pass on the product candidate.

Raw logs, four dialog screenshots and phase observations are sealed. Compiled
Next manifests were kept privately under opaque hashes, then only the owned
stopped caches were removed. Both owned servers exited 0; port 3027 and the
finite slot were released. No raw Next manifests or private agent traces are
included. Package/lock and observed versions are recorded without claiming
exhaustive installed/cold dependency identity.

    node scripts/original-settings-id-search.mjs
    python3 reconstruction/settings-identifier-search/validation/verify.py
    python3 -O reconstruction/settings-identifier-search/validation/verify.py

The verifier binds selected phase inputs, exact one-line product delta,
separate typing-only mapping and saved observations. It neither reruns the
workflow nor proves whole original search/provider/visibility, pixel/native
compatibility, preference persistence, security or completion. Original captures,
prior packages and the concurrent #1188 normalization work remain untouched.
