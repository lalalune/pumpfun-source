# Native video-picker readiness

An enabled native video input accepted a real file before its Create client
chunk arrived. After bootstrap, the file remained in the native FileList but
the form never processed its earlier change event: no decoder or covers, and
no feedback for an empty file. A ready-input control decoded the same 677-byte
WebM successfully into three JPEG covers. The controlled form's metadata JSON
updated after bootstrap in the failing cases, distinguishing a missed file
event from a client script that did not execute.

Keep the native input disabled until the actual `VideoDraftSession` consumer is
installed, and report a simple loading status. After installation it remains
available during preparation/replacement, retaining the existing lifecycle and
validation behavior. No file is admitted before its handler can process it.
This is an independently reconstructed local draft correction, not evidence
of the captured site's startup or upload policy.

The original four hash-bound factories and quarter-duration/JPEG contract are
preserved in `contracts/create-video-bindings.json` and
`packages/frontend/CREATE-VIDEO-EVIDENCE.md`. No captured code is executed.
The helper, session ownership, image replacement/cover marker behavior, MIME/
size policy and metadata schema are unchanged. Separate pending work #1446,
#1525, #1318, #1619, #1424 and #1387 is not composed or duplicated.

The final browser harness delays only an actual local Create-input script
response, forwards its bytes unchanged, and records its hash. Its identical
precondition logic selects once at the earliest point the native control
admits selection. When disabled, a trusted pointer attempt must open no
picker; after readiness, one native file-chooser selection must produce real
covers or the existing validation error. The new cases do not replace or
override HTMLVideoElement, loading, seeking, canvas or JPEG encoding. Input
events/value changes and object-URL allocation are observed transparently.
The retained deliberately stalled decoder test remains a synthetic lifecycle
control and is not counted as native-codec proof.

The synthetic fixture is VP8, 64×64, two seconds, 677 bytes, SHA-256
`6e6a587654ecde9db701232d18836a37e84bb5ef2e676d3f4572e0633e9e9f35`.
It was generated locally with:

```sh
ffmpeg -hide_banner -loglevel error -f lavfi -i color=c=red:s=64x64:r=4:d=2 \
  -an -c:v libvpx -pix_fmt yuv420p -fflags +bitexact -flags:v +bitexact native-2s.webm
```

The checked-in bytes are fixed; regeneration across ffmpeg versions is not a
byte-identity claim. `empty.webm` is the zero-byte rejection control. No
external media, uploads, provider requests, wallet signing, launch, persistence
or fabricated media URI is involved. Only this finite Chromium VP8 workflow is
qualified; broad codec/browser or original visual/API parity is unclaimed.

Run from `app`:

```sh
node --experimental-strip-types --test tests/create_video_preview.test.mjs tests/create_video_bindings.test.mjs
corepack pnpm --filter @pump-reconstruction/frontend typecheck
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test tests/create-video-ready.spec.ts tests/create-video.spec.ts tests/create.spec.ts
```

The baseline, corrected candidate, initial harness limitation and exact finite
source/command/data receipts are recorded separately in the validation packet.
For fetchable source pins, explicit working directories and fresh retained
outputs, use [the public replay sequence](PUBLIC-REPLAY.md). It needs no private
commit or regenerated WebM; the archived controller remains unchanged.
