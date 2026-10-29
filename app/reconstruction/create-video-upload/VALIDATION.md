# Static qualification

Public source commit: `6c416150a3e4df04c15b286a9de1a2e71a526a9e`.
It has the exact full tree `91d0847ff20a3b8c9104778bcf51aed38962321d`
measured locally as `f63e4bb8edf90751bb78b0e93e5e446c4faf769c`, with
parent `094a06f18df738d41e77070c1a009e135671ac1a`. Publication changed
commit metadata, not file bytes. Subsequent qualification files do not change
the four source/documentation files in that source tree.

| Check | Result |
| --- | --- |
| Deterministic contract `--check` | 14 roles, 13 unique factories, 88 AST witnesses |
| New source/integrity tests | 3 pass; nine altered packet variants rejected |
| Existing #681 media binding tests | 2 pass |
| Existing #885 video binding tests | 2 pass |
| App evidence | 698 objects, npm integrity, all 31 unchanged SDK sources pass |
| Progress ledger check and tests | check passes; 9 tests pass; no milestones changed |
| Exact public source mandatory root checks | 53 authenticated inputs; 9 captures and 10 tooling tests pass |
| Independent static review | all source/range hashes rebound; no concrete source/protocol blocker found |
| Public Git-authenticated minimal export | 16 exact source/capture inputs; `--check` and 3 tests pass from a path containing spaces; zero input changes |

Complete finite logs and SHA-256 inventory are in [validation](validation/).
The review is explicitly read-only static review, not a second test run or
server/security approval. The export uses existing dependencies read-only;
it is not a clean dependency installation or a full repository checkout.

To reproduce the source checks on the fetchable public source revision:

```sh
git fetch --no-tags https://github.com/shawkkkkk/pumpfun-source.git 6c416150a3e4df04c15b286a9de1a2e71a526a9e
git switch --detach FETCH_HEAD
cd app
node scripts/original-contracts/create-video-upload/verify.mjs --check
node --test tests/original_create_video_upload.test.mjs
python3 -B tests/test_create_media_bindings.py
node --test tests/create_video_bindings.test.mjs
```

Run this in a clean checkout with the normal pinned dependencies and retained
capture inputs present. The commands do not use a private commit or absolute
private runner. Output is ordinary stdout/stderr; redirect it to a new external
directory when retaining a replay so these historical receipts remain intact.
Use `--app-root` when invoking the verifier from another working directory.

Initial preparation attempts stopped on missing existing sparse-checkout inputs,
including capture metadata, progress references and SDK source files. The
missing unchanged files were authenticated against the base Git blobs before
restoring them; mismatched older donor source files were rejected. Those failed
setup attempts are preserved privately and are not relabelled as passes. The
final results above use the completed exact input closure.

The review also encountered the source packet while its witness count was
being expanded from 82 to 88; the final test expectation was corrected before
the three passing tests. The independent report preserves that development
history. No earlier incomplete reading is presented as the final result.

No Next process, production build, browser, original captured-code execution,
provider call, upload, session inspection, wallet action or signing was needed
for this source-only contribution. The full application and original upload
workflow were not exercised. No native compatibility, backend completion,
mounted feature or progress credit follows from these checks.
