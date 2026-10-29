# Local Create media drop selection

The Create draft now accepts one local image or video dropped on its explicit
media surface. Image drops use the existing image validator and object-URL
preview. Video drops use the existing `VideoDraftSession`, bounded decoder and
three-cover selection. Native image/video file controls remain available for
keyboard and non-drag users. This does not replace them with a pointer-only UI.

## Static source binding

These retained factories were read as text, never executed. Factory ranges are
UTF-16 offsets within complete hash-authenticated objects:

| Factory               | Object / range                   | Factory SHA-256                                                    |
| --------------------- | -------------------------------- | ------------------------------------------------------------------ |
| Create `734638`       | `89ce7de3b9bad421.js`, 119–66825 | `616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc` |
| Lazy wrapper `320853` | `01f240a1f9100e9d.js`, 119–224   | `f11b9e82b5951d62d9717dad92358a120241bab0e6453ad8550cd8f2775975d9` |
| Selector `658259`     | `762f0784b7be61c0.js`, 138–5776  | `691ff5f669927ccece0478631066f80ac94a832dd5fadae2a3a175f09372e6fa` |

`/create` HTML includes the Create and lazy-wrapper scripts. The Create factory
loads `320853` and selects `FileDropzoneInner`; the wrapper explicitly loads
`static/immutable/chunks/3r6p9e97ury3w.js` and resolves `658259`. The selector
chunk is **not** a directly included HTML script. The binding test checks this
actual lazy edge, full object hashes/lengths and recovered inventory ranges.

Observed selector behavior: file input/drop root, accept and reject indicators,
`onDrop`/`onDropRejected`, and default `maxFiles: 1`. The Create call site passes
`onDrop: e => er(e[0])`, its image/video accept set and `maxFiles: 1`. Existing
Create/video evidence documents the image and video bounds used here.

The original also has login and upload state. Those paths are **not** rebuilt or
bypassed: this existing offline draft has no provider credentials, server
upload, production request, storage persistence, SDK call, signing or launch.
The drop interaction is a local consumer reconstruction, not production parity.

## Local admission and ownership decisions

- Exactly one file. Multiple file items or FileList entries are rejected before
  materializing their contents. String/HTML/URL items are never read or followed.
- Directory entries are rejected when the browser exposes entry metadata. No
  directory enumeration or filesystem access is requested. Browsers with only
  FileList still require a single admitted file and the existing media checks.
- A missing/unreadable file or browser entry-access error is explicit feedback;
  it cannot fall back to a different file. An accompanying string item is ignored.
- Existing image MIME/nonempty/4,500,000-byte rules and video extension/MIME/
  nonempty/10,000,000-byte rules remain unchanged. Video still needs local decode;
  file metadata is not content authentication or malware scanning.
- Rejection does not replace committed media or cancel unrelated pending work.
  A successful dropped manual image cancels pending video work, just like the
  file control. Late video results cannot restore an obsolete cover.
- Successful video drops enter the same session as the video file control.
  Cover selection, replacement, remove, reset and unmount keep existing owner
  tags, deadlines and URL disposal. No second decoder or resource owner is added.
- Reset removes drop feedback. A new selected image remounts the non-focusable
  drop surface to clear obsolete rejection/drag state. File controls are cleared
  after image selection so the same file can be selected again after a drop.
- Native navigation is prevented only inside the explicit drop surface. No
  document-wide drop interception affects text fields or unrelated pages.
  Drag highlights reset on balanced leave, drop, window blur and drag-end.

Error copy, folder rejection, the explicit local surface and cancellation policy
are local design decisions. No original layout, native OS drag behavior, upload
compatibility, completed feature count or production-qualified operation is claimed.

## Verification

Explicit focused commands (do not run a root test wildcard):

```sh
node --test tests/create_media_drop.test.mjs tests/create_media_drop_bindings.test.mjs
node --test tests/create_video_preview.test.mjs tests/create_video_bindings.test.mjs tests/video-ready-reentrancy.test.mjs
pnpm --filter @pump-reconstruction/frontend typecheck
# Authored browser regressions; execution status must be reported separately:
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/create-media-drop.spec.ts
```

Admission tests use synthetic File/DataTransfer ports. Binding tests perform only
hash/range/string checks on inert captured inputs. The browser spec covers native
DataTransfer events, a real PNG, rejected/undecodable video, and one explicitly
stalled decoder case; a successful native video codec is not implied. Supplemental
React/jsdom integration exercises actual maintained components with synthetic
media ports and zero external requests; it is not browser or visual qualification.

On the isolated candidate based on app tree `e3d6d8cd`: 52 explicit focused
checks pass (14 new admission/binding checks plus 38 existing video checks), as
do frontend types and SDK/backend/Next build stages. The app evidence gate
verifies 698 objects and unchanged SDK sources. Progress passes after the first
source-only attempt reported its missing root README; the exact pinned README
was then hydrated, without changing progress or qualification records.

A separate private `git merge-tree` composition with inspector PR #1259 head
`6a734f41b2cf5db3368cea5a7a384baf29e59d50` merges automatically. Its actual
React tests pass 24 cases: 12 inspector, six existing video, and six new drop
flows. Main-only React tests pass the corresponding 12 media cases. The pending
inspector and its dependency patch are not included in this contribution.
Browser tests are authored but not yet executed for this candidate. No full
root wildcard, raw captured runtime, real-codec success or native visual parity
is claimed.
