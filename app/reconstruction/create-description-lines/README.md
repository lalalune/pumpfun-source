# Preserve multiline local draft descriptions

The existing Create contract calls Description an optional multiline field
(`packages/frontend/CREATE-COIN-EVIDENCE.md`, field decisions), and its live
textarea says “Multiline text is supported.” The form and descriptive JSON
retain the exact newlines, but the preview paragraph rendered them as spaces.
At both 390 and 1280 pixels, `First\n\nSecond\nThird` appeared on one line.

Add `white-space: pre-wrap` to that existing paragraph's scoped class. Retain
`overflow-wrap: anywhere`, so ordinary words and long words continue to wrap.
No field value, metadata, validation, limit, component or media operation
changes. This corrects the documented local drafting behavior; no original
Create appearance or whitespace-formatting parity is established.

The source commit `8239192d14107040b0f4f468ed69ce8136323219` and public source
`1d019c45b7abf5b6003927d666a868ce47ed1043` have the identical complete Git tree
`6c9aa89838bee28c94861855e63051eb6603fa59`. The base is
`094a06f18df738d41e77070c1a009e135671ac1a`. The only production difference is
that one CSS declaration. The follow-up packet is documentation only.

The finite executed browser probe types the description into the actual Next
Create form and checks the textarea and parsed JSON byte-for-byte. DOM Ranges
measure the three rendered words: the blank line requires a two-line-height
gap, then a one-line-height gap. Screenshots supplement these measurements.

| Same-method result | Base | Candidate |
| --- | --- | --- |
| Multiline and blank line, 390 | FAIL: all words share one Y position | PASS: 41.6px then 20.8px gaps |
| Multiline and blank line, 1280 | FAIL: all words share one Y position | PASS: 41.6px then 20.8px gaps |
| Wrapping, long word, exact JSON, reset and empty placeholder, both widths | PASS | PASS |
| Existing Create cases | Not rerun in baseline | All 11 PASS |

The final candidate has **14 passing cases, no skips/retries**. Its paragraph
height is 83.1875 pixels (four 20.8px lines), compared with 20.796875 on the base.
The existing native image/video/launch boundaries remain intact. Requests are
restricted to same-origin GET/HEAD; no external media or service is contacted.
The existing explicitly closed local browser-consent fixture is used without
inferring anyone's prior consent or the original capture state.

Frontend typecheck, 698-object/npm/unchanged-SDK evidence verification, progress
check and nine progress tests passed. Mandatory official checks on the measured
source authenticate 53 Git-bound inputs and pass nine captures plus ten tooling
tests. No separate normal production build was run for this one-property unit.

`validation/qualification.json` binds raw logs/reports, all 209 runtime source
hashes per phase, original screenshots, exact measurements and cleanup. Gzip
files are lossless and include stored/decoded hashes. The three-case finite
probe is retained as an executed receipt, not added to the maintained browser
suite. To repeat it, copy `validation/finite.spec.ts.txt` temporarily into the
frontend `tests` directory, copy the executed config beside the ordinary
Playwright config, substitute its output paths for your workspace, and run:

```sh
corepack pnpm exec playwright test --config playwright.create-description-lines.tmp.config.ts tests/create-description-lines.tmp.spec.ts
```

The candidate additionally runs the existing `tests/create.spec.ts`; its sole
executed-copy change is the strict origin's port 3010→3027, recorded in
`retained-port-only.patch`. Restore that copy and remove temporary files after
the run. No permanent tests, package, lockfile or CI changes are necessary.

Three unsuccessful setup/check stages remain separately recorded. The first
selector omitted the field's Optional label and never reached the intended
measurement. A later setup working-directory error left a subsequent run
unqualified; it was interrupted and contributes no passing claims. Initial
headless checks lacked sparse support inputs; 53 exact current Git blobs were
restored before the successful typecheck/progress runs. None was repaired by
changing application behavior or assertions. Source, logs and images remain
preserved, and only the owned inactive Next cache was removed after stopping.
