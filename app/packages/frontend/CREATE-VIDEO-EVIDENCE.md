# Offline Create video and cover lifecycle

## Browser verification fixture correction

At `bbdc0ee08a82b17020efe2e6802504a6ac880fd6`, both existing Chromium
video cases fail before completing their intended checks. The error assertion
matches both the video's alert and Next's route-announcer alert. In the pending
case, replacing `load()` alone does not stop native resource selection when
`src` is assigned: the synthetic bytes already fail decoding, leaving an empty
status and a real codec-error alert.

The browser test now scopes feedback to the existing Video and cover fieldset.
Only its deliberately stalled lifecycle case additionally withholds the video
`src` assignment, keeping preparation pending until manual replacement/reset.
It explicitly verifies pending state before reset. The separate invalid-WebM
case keeps the real browser decoder, manual-image preservation assertions,
disabled launch check and external-request guard. Both complete cases pass
after this test-only correction; no production behavior, codec-success claim,
upload compatibility or feature-completion credit changes.

## Useful local behavior, not an upload reconstruction

The image-only `/create` draft now accepts an optional local MP4/WebM video,
decodes three cover candidates in the browser, selects the first, and lets the
user choose another. The selected JPEG passes the existing image validator and
feeds the existing coin preview and descriptive draft JSON. Video and cover are
separate local files. A manually selected image can replace the cover.

No request is made to an upload, presigned, Pinata, storage, SDK, wallet or RPC
service. No CID, production URL, credentials or metadata URI is fabricated.
The launch button remains unavailable. The operator-capability local backend is
not used or relaxed; this is browser-memory drafting only, not persistence.

## Static observed source

`contracts/create-video-bindings.json` authenticates these factories against
complete retained objects, the `/create` HTML script context, and the recovered
module index. Ranges are UTF-16 code units; no captured code is executed.

| Factory         | Object                | Range       | SHA-256                                                            |
| --------------- | --------------------- | ----------- | ------------------------------------------------------------------ |
| 734638          | `89ce7de3b9bad421.js` | 119–66825   | `616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc` |
| 586090          | `6a1606765ef3e83e.js` | 21522–21848 | `5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4` |
| 807757          | `6a1606765ef3e83e.js` | 35753–37962 | `7094dc3c2113698f06bc9cef420cd9c153d355911226020d467f49a0ad85bf68` |
| 421159 / 778435 | `1147ad0a1bf513f9.js` | 86246–87341 | `c5cfe326d6205ed545cad91ccce1de02da3b1ac2429bc534a1f19faebe99e846` |

Observed: factory 586090 offers `.mp4`/`.webm` and a 10,000,000-byte video
client bound. Create 734638 imports 807757, requests three thumbnails, and
selects index zero. Helper 807757 creates a video/object URL, seeks to
`duration / 4 * (1, 2, 3)`, draws to canvas, encodes JPEG at quality 0.8, and
revokes its source URL. Metadata 778435 still requires a separate image.

The captured Create flow performs a credentialed signed-URL request and upload
_before_ thumbnail extraction. That transfer is deliberately absent here:
offline decoding happens immediately from the selected File. The existing
`create-media-bindings.json` describes the distinct service-origin boundary.
Its provider authentication, expiry, persistence, status/error semantics and
production compatibility remain unknown. Browser filename/MIME and decoding
are not content authentication or malware scanning.

## Local design and resource ownership

- Nonempty files up to the observed byte bound; MP4/WebM extensions, with a
  matching declared MIME when present. Empty MIME is permitted and reported as
  null in descriptive JSON. Browser decoding is still required. This selection
  policy is not a substitute for the captured magic-byte detector.
- Duration must be finite and positive, with three distinct representable
  interior time points. Infinite/live-stream and underflow durations fail.
- Additional local allocation limits: at most 16,777,216 decoded source pixels,
  covers fit within 1,280 pixels per edge without enlargement, JPEG covers are
  nonempty and at most 4,500,000 bytes. These are not upstream video limits.
  Browser decoders may allocate internally before metadata becomes available;
  this is not a complete decoder-memory sandbox.
- A 30-second total metadata/seek/encoding deadline. Unsupported codecs,
  missing canvas context, seek errors, null/invalid encoding and timeout fail
  explicitly. No fallback fabricates a thumbnail or an uploaded state.
- Pending and committed previews have separate ownership. A failed replacement
  preserves the committed video and manual image. Newer selections, cancellation,
  removal and unmount invalidate earlier promises; late results are disposed,
  not published. A successful manual-image selection synchronously cancels any
  pending video decode, preventing it from overwriting the newer image.
- Clear removes only the image owned by that video, not a manually chosen image
  or another video's cover. Reset clears the whole draft. Explicitly choosing a
  cover cancels a pending replacement and replaces the manual image by intent.
- Every generated object URL is owned until replacement/removal/unmount. The
  off-DOM decoder, event listeners, timeout and canvas backing surface are
  released after preparation; successful preview URLs remain until disposal.
  The existing parent image preview separately owns its selected-image URL.
- No localStorage, IndexedDB, downloads, persistence, service-worker changes,
  network calls, signing, transaction construction or token creation.

## Verification and remaining gates

```sh
node --test tests/create_video_preview.test.mjs tests/create_video_bindings.test.mjs
pnpm --filter @pump-reconstruction/frontend typecheck
pnpm build
# Authored only; not run in this environment:
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/create.spec.ts tests/create-video.spec.ts
```

The deterministic tests exercise the actual helper/session with synthetic
EventTarget video/canvas doubles: file/duration/size boundaries, quarter times,
encoding settings, image-validator integration, all failure stages, aborts,
timeouts, late completions, replacement, manual-image ownership and disposal.
They are not real MP4/WebM codec or browser tests. Binding tests authenticate
four factories and reject object/range/context/qualification mutations.

Browser regressions are authored for rejected/undecodable video preserving a
manual image and cancellation/reset during a deliberately stalled decoder.
No browser execution, real-codec success, visual parity or matched screenshots
are claimed. The original UI layout and full video/upload flow remain
unqualified; no route/feature milestone or completion counter is increased.
PR791's separate empty-image validator change is not duplicated; compatibility
is checked by applying its real patch to a separate composition.

Recorded on the isolated candidate with Node 24.22.1 and pinned pnpm 10.24.0:
35 synthetic consumer/lifecycle checks plus two binding checks pass; complete
SDK/backend/Next build, all three package typechecks and explicit browser-test
TypeScript checks pass. The unchanged current backend suite passes 588 tests,
including ephemeral loopback HTTP cases. Capture-tooling tests pass 27 cases
and evidence-verifier tests pass two. PR791's exact two-file patch applies
cleanly in a private composition, whose 42 focused checks and frontend types
pass; none of that PR's source delta is republished here.

The full evidence inventory gate fails on missing retained objects in this
source-only workspace, and the progress check stops at the absent prior
portfolio visual receipt. Full aggregate/browser suites are not claimed. The
first build attempt failed because shared dependency symlinks left Turbopack's
root; copying the already approved same-lock dependency tree inside the isolate
resolved that layout issue without changing configuration or dependencies.
