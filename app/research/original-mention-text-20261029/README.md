# Original standalone feed content rendering

The maintained feed printed serialized mentions such as
`@[Alice](12345678-1234-1234-1234-123456789abc)` and tweet-status URLs as raw
text. This unit reconstructs the captured standalone/default content path and
mounts it in the existing `FeedItem.content` and `NativeCalloutCard.thesis`
positions. It introduces no endpoint or product route.

## Original source and bindings

[contract.json](../../reconstruction/mention-text/contract.json) retains exact
factory identities, physical capture paths, source URLs, SHA-256 hashes,
UTF-16/UTF-8 ranges, and verbatim inert fragments. The producer authenticates the
manifest and complete retained factory inventory before parsing those sources.
Captured JavaScript is never imported or evaluated.

The actual registered export is `174251.f`, whose display name is `MentionText`.
Its used mention parser is `314012.m`, and its used profile-path formatter is
`146695.$`. All three retained physical `386028.f` consumer variants invoke the
renderer with `content`, omit `withinLink`, and therefore use its standalone
false default. The renderer's density default is `comfortable`. These actual
call bindings do not establish a complete original rendered route or a unique
running consumer variant.

The recovery preserves the ASCII username and loose 36-character hex/hyphen ID
rules, repeated mention order, parsing mentions before tweet candidates, the
original hostname/path qualification and punctuation behavior, and LF/CR text
boundaries. Other URLs remain text. The original greentext theme token is bound
to the captured CSS range. Profile links disable prefetch and stop bubbling;
external status links stop bubbling and retain `target="_blank"` plus
`rel="noopener noreferrer"`. React renders all other markup as literal text.

Shared source-authentication helpers and the already maintained profile-path
source are prerequisites with no new recovery credit. Original captures,
synthetic seeds, SDK source, backend validation, route ledger, and compatibility
qualification are unchanged.

## Reproduce

From `app/` with the existing pinned dependencies:

```sh
node scripts/original-mention-text.mjs --check
node --test tests/original_mention_text.test.mjs tests/original_source.test.mjs
corepack pnpm test:feed
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
python3 -m unittest discover -s tests -p test_progress.py
```

From `app/packages/frontend/`, with ports 3001 and 3016 free:

```sh
corepack pnpm exec playwright test --config playwright.mention-text.config.ts
```

The dedicated browser configuration starts a GET-only, loopback synthetic input
server and the actual Next application. It exercises the existing Home Feed
HTTP loader, provenance/shape validator, mounted renderer, keyboard navigation,
and narrow/mobile layout. It blocks all nonlocal browser requests and all
browser mutation methods. No original service, account, wallet, auth provider,
or authenticated feed is used.

The browser file deliberately uses `.flow.ts` and is selected only by its
explicit configuration; it does not accidentally join the general browser
suite without its input server.

## Limits

Only `withinLink=false` and `density="comfortable"` are implemented/exposed. The
captured `withinLink` button/router path and terminal-density styles are not
reconstructed here. The original SVG icon is represented by an aria-hidden text
glyph, and local CSS fits the existing feed; no pixel identity is claimed.

The HTTP input is synthetic and explicitly labelled by the maintained UI. It
proves a local input-to-rendering path, not original-service compatibility. The
native callout validator rejects multiline thesis values; this unit preserves
that boundary. Multiline/LF/CR behavior is covered by the pure renderer tests.
A mention is a captured text token, not proof of identity, ownership, profile
existence, or authentication. An unresolved synthetic mention navigates to the
maintained unknown-route state rather than fabricating a user.

No composer, mention picker, query provider, social mutation, session API,
feature-ledger completion, backend reconstruction, or binary progress is claimed.

## Retained validation

[VALIDATION.json](VALIDATION.json) binds the actual browser-tested code revision
`581a96977ded85daee3a03694c5d84df88d5db2e`, both product integration file hashes,
the unchanged loader/validator and the identical authored input/browser harness.
Both runs use the same loopback response. The before run restores only the two
integration files from base `abd766d7a8c047f14af34851f64166b840c6728d`, then the
controller restores the candidate files and checks their hashes. No captures,
seeds, SDK files or backend product code are changed.

| Check                                           | Result                                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Base UI with identical input/harness            | 1/1 passed: raw serialized mention remains text, no mention/status/greentext element                                                                                                           |
| Candidate UI                                    | 1/1 passed: mention link, two status links, greentext, literal malformed/HTML/lookalike text, real Tab/Enter, desktop/mobile no overflow, unknown-profile state, ordinary seed-feed regression |
| Source/model and shared authentication controls | 25 passed: 14 new, 11 prerequisite                                                                                                                                                             |
| Existing feed validators                        | 17 passed                                                                                                                                                                                      |
| Frontend typecheck                              | Passed                                                                                                                                                                                         |
| App capture/npm/SDK verifier                    | 698 objects verified                                                                                                                                                                           |
| Progress controls                               | 9 passed                                                                                                                                                                                       |
| Repository evidence and tooling                 | 9 captures verified; 10 tests passed                                                                                                                                                           |

The browser observed the actual local `GET
/services/frontend/home-feed?pageSize=3` in each run. No nonlocal request,
browser mutation, fabricated profile, or real authenticated session was used.
Console-error assertions cover the content view before intentional unknown-profile
navigation; no blanket assertion is made after that navigation. No full Next
production build or entire browser-suite pass is claimed for this unit.

- [Before](proof/baseline-1280.png)
- [After, desktop with keyboard focus](proof/candidate-1280.png)
- [After, mobile with keyboard focus](proof/candidate-375.png)
- [Before browser/frontend/HTTP log](proof/browser-baseline.log)
- [After browser/frontend/HTTP log](proof/browser-candidate.log)

[MANIFEST.json](MANIFEST.json) binds the retained proof files. To verify those
bytes from this directory:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json
for row in json.loads(Path('MANIFEST.json').read_text())['files']:
    data = Path(row['path']).read_bytes()
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
print('Retained proof hashes pass')
PY
```
