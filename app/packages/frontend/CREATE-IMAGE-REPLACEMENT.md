# Local image replacement safety

The maintained form previously committed a MIME/size-valid file before its
image loaded. A corrupt PNG could therefore replace the accepted image, revoke
its URL, then clear the image slot on the new preview's error. This is a local
draft-safety correction, not evidence of the captured site's replacement policy.

`prepareImagePreview` runs only after the existing file validator. It waits for
a browser image load with nonzero dimensions, limits waiting to ten seconds,
and revokes its candidate URL on rejection/cancellation. Success transfers that
URL to the form's existing preview owner. It does not authenticate MIME, resize
files, upload, fetch, sign, or create metadata URIs.

The previously accepted image stays visible and in the local JSON until a new
image is ready. A failed replacement reports its error without erasing the
accepted draft. Reset, removal, unmount, newer admitted image/video choices and
explicit video-cover selection invalidate pending image work. Invalid file
metadata does not supersede a pending valid choice. A local status identifies
pending image preparation.

Video cancellation distinguishes pending preparation from a committed cover.
`cancelPreparation()` aborts only older extraction; the existing `cancelPending()`
callback runs after the manual image commits. This distinction permits composition
with the separately owned cover-marker fix without detaching a cover on failure.

Focused model commands from `app`:

```sh
node --experimental-strip-types --test tests/create_image_preview.test.mjs tests/create_image_video_intent.test.mjs tests/create_video_preview.test.mjs
```

The new model cases use explicit image events and synthetic video preparation;
they establish cleanup, timeout and selection ownership, not native codec or
browser compatibility. The browser regression uses a tiny PNG and deliberately
invalid bytes labelled PNG:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test tests/create-image-replacement.spec.ts
```

Native candidate execution remains pending in the private review packet. The
test is authored and typechecked, not represented as passed. No upload, original
visual/API parity, production build, full workspace verification, or new feature
completion credit is claimed by these focused tests.
