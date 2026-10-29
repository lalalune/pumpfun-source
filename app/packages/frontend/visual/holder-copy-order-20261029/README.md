# Clipboard feedback regression evidence

`RESULT.json` records the maintained baseline, exact component hashes and
before/after outcomes. The baseline trace shows the stale live-region text
after a mint edit. The final candidate passes all three delayed-clipboard cases
and eight existing inspector cases on the same source revision.

The first candidate's separate failure was a missing tracked font, caught by
the existing console-error assertion after ten cases passed. Its trace/log and
the Git-authenticated font-restoration receipt are retained. The unchanged
candidate then passed all11 cases. No request was mocked to hide the404.

Text logs and error contexts are losslessly compressed with gzip; Playwright
traces are original ZIPs. `MANIFEST.json` authenticates every retained file.
The input Clipboard API Promise is controlled in the browser test. This proves
the local feedback race and correction, not original visual/API equivalence or
the completion/cancellation of a real operating-system clipboard operation.
