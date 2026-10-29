# Finite video readiness qualification

The final executed harness and its native file fixture are checked in with the
source. `qualification.json` binds the measured candidate
`4fa1124d7d20bcb5182e23c2122c9e3e0dc65252` to public source
`f4c54995dac4a2d294799393a23f00f514b921f2`: their complete Git tree is identical,
`569f4049c4d3af32f9dd50ff53b886da92ea870a`. The source base is
`094a06f18df738d41e77070c1a009e135671ac1a`.

| Final same-method run | Result |
| --- | --- |
| Base: normal ready native selection | PASS; real video produces three JPEG covers |
| Base: earliest admitted valid selection | FAIL at 390 pixels; native FileList remains populated after real form bootstrap, with no decoder or covers |
| Base: earliest admitted empty selection | FAIL at the default 1280 pixels; no existing nonempty-video feedback |
| Candidate: three new native cases | 3 PASS; valid early selection exercised at 390 and 1280, plus ready and empty-file controls |
| Candidate: unchanged Create/video cases | 13 PASS; no skips or retries |
| Existing model and captured-source binding cases | 37 PASS |
| Frontend typecheck | PASS |
| App evidence / progress | 698 objects, npm integrity and unchanged SDK PASS; progress check and nine tests PASS |
| Independent normal SDK/backend/Next production build + recursive typecheck | ALL PASS at the identical measured/public source tree; producer logs and manifest hashes retained |
| Mandatory root evidence / tooling | 53 Git-bound inputs; nine captures and ten tooling tests PASS at the measured source |

The valid baseline test fails on its first width, 390; its final-method 1280
branch was not run. The earlier discovery at 1280 is a separate observation.
The final candidate passes both widths within that same case. The controlled
Coin name field updates metadata JSON after script release in both final phases,
so the baseline result is not merely an unexecuted client script.

The same final test chooses once at the earliest admitted point: an enabled
baseline admits the file before its consumer exists; a disabled candidate must
reject a trusted pointer attempt without opening a picker, then admits one
native selection after readiness. Only the actual local matching script
response is delayed, and its response bytes are forwarded unchanged. The
before/after JSON includes those response hashes, trusted input/change events,
FileList state, transparent value clearing/object-URL observations and actual
video duration/dimensions. Only same-origin GET/HEAD requests are allowed.

The three new cases leave video loading, seeking, canvas and JPEG encoding
unmodified. One of the thirteen retained controls deliberately stalls decoding;
that existing synthetic lifecycle control is not native-codec evidence.
Screenshots are supplemental local UI records, not original-reference visual
comparisons. `base-early-valid-390.png` visibly retains the selected native file
without producing covers. The candidate screenshots show a selected cover and
video draft at the same tested viewport sizes, with their native state recorded
in the corresponding JSON.

## Preserved preliminary and unsuccessful checks

`baseline-*` and `report-baseline.json.gz` retain the discovery: the ready
control passed and early valid selection failed at default 1280. That initial
method did not assert the post-bootstrap controlled form update. It is not
retargeted to the final method.

The first expanded run (`final-*-browser.log.gz` and `report-final-*.json.gz`)
used an exact label selector that missed the required asterisk, and its cleanup
could mask the timeout. Its candidate had fourteen passes and two harness
failures. The correction changed only the selector to the actual textbox role/
name and made cleanup tolerate a closed page. Production source stayed identical
to `3b266067b7e45973b9dd633bc1db3327cd8e6cc5`. Both base and candidate were then
rerun using that corrected, frozen final harness; only the `qualified-*` runs
qualify the result above. Raw unsuccessful logs/reports are preserved here in
lossless gzip, separately from final receipts.

The executed controller/config use the original local workspace/output paths.
To reproduce in another checkout, substitute those paths explicitly; the
checked-in spec itself runs under the ordinary frontend Playwright config and
is automatically included in its existing `test:browser` discovery. No package,
lockfile or CI change is needed. Source manifests enumerate and authenticate all
209 frontend runtime files in each phase against the stated exact Git revision.
The controller restores the one substituted baseline component and generated
Next file. Only the owned inactive build cache was removed after all processes
stopped; cleanup receipts are retained.

The file ledger records stored and decoded SHA-256 hashes for each gzip. There
is no original startup-policy, upload, broad-codec, current API, financial,
launch, persistence or feature-completion claim. The independent normal production build and its recursive typecheck, evidence and
progress gates also passed. `normal-production.json` retains the exact source/tree
mapping, original producer check record, four lossless raw logs and hashes of
seven retained generated Next manifests. This receipt changes no tested source.
