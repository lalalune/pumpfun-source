# Captured website Create video-upload caller

This packet fills the signed-video request and result-handoff gap in the
existing Create evidence. It is a **static contract**, reconstructed from the
retained `/create` response and its actual factory/dependency closure. It does
not implement or mount an upload client. No captured JavaScript was evaluated,
and no request, upload, wallet action or signing was performed.

The existing [Create media binding](../../contracts/create-media-bindings.json)
already covers the image/JSON Pinata flow (#681). The existing
[video binding](../../contracts/create-video-bindings.json) and #885 cover the
offline thumbnail consumer. This packet reuses those facts rather than claiming
a new image upload, classifier, thumbnail implementation or npm SDK recovery.

## Newly connected boundary

| Step | Actual captured caller behavior |
| --- | --- |
| Selection | Create lazily resolves `320853` → `658259.FileDropzoneInner`. Its media callback passes the first selected File to the hook's actual handler. The page supplies `!!wallet` as `isLoggedIn`; the selector passes login-derived `noClick`/`noDrag` props to its dropzone and provides a wallet-UI callback. This is a UI prerequisite, not proof of server eligibility. |
| Classification | Existing `807757.x` inspects the file prefix. The caller splits the returned MIME into category and extension; a null classification throws. The original ordered image/video checks, including shadowed later signature branches, are preserved. Filename extension and browser MIME are not substituted for this result. |
| Presign | Website client `759257.j` selects `https://frontend-api-v3.pump.fun` through `503630.R` and `30181.K`/the contract transport. Actual request: **GET `/videos/get-signed-url?extension=<classified suffix>`**, `credentials: include`, JSON Content-Type and shared WEB/platform headers. No request body. An `afterResponse` hook throws when `response.ok` is false. |
| Declared result | Registry `402030` includes `717721.videosRoutes`: `{filename: string, url: {url: string, fields: Record<string,string>}}`. The transport consumes `.json()`; it does **not** runtime-validate the successful result against this declaration. |
| Provider POST | The caller creates XHR and browser FormData, opens **POST to the returned `url.url`**, appends every returned `url.fields` entry in enumeration order, then appends the original File under `file`. The provider URL and policy fields are opaque, not a fixed reconstructed host. |
| Admission/error | `200 <= XHR.status < 300` resolves `XHR.response`; other statuses, network errors and abort events reject. The response body is not parsed or otherwise used. Computable progress is `loaded / total * 100`. No explicit XHR credentials, headers, timeout or retry are configured by this uploader. |
| Result state | Only after awaiting provider success, the caller derives `https://media.pump.fun/videos/` + returned filename, stores that filename, marks video uploaded, clears uploading, then extracts three thumbnails. No additional filename validation or URI encoding appears in this used concatenation. |
| Metadata | Page state passes the same stored filename to **both** `778435` direct metadata assembly and `421159` resolved-mint wrapper. Both use the common assembler: when `video && videoUploaded`, set the actual metadata property **`video`** to `https://media.pump.fun/videos/` + filename. The separate uploaded image hash remains mandatory. `videoS3Url` is separate display state, not the metadata input. |
| Handoff | Both helper results supply metadata and `metadataUri` back to the caller. The zero-initial-purchase branch passes the metadata/video and URI to the website creation request; the other branch passes the URI to the existing transaction helper. These downstream boundaries are witnessed only and were not invoked or reimplemented. |

## Preserved lifecycle and authorization limits

The captured Promise executor returns `{cancel: () => xhr.abort()}`. A Promise
does not expose its executor's returned object, and no assignment to the
returned `xhrRef` is established here. This packet therefore records the abort
event rejection but does **not** claim working caller cancellation. The handler
logs and rethrows errors without a `finally` reset. Uploaded/idle state is set
before thumbnail extraction, so thumbnail failure cannot be described as a
provider-upload rejection or a proven state rollback.

The later submission validator requires a truthy decoded context value, video
size at most 10,000,000 bytes, uploaded state and its thumbnail condition. These
checks are **later than the file-selection upload**; they are not proven
pre-upload authentication or size checks. No actual session, cookie, credential,
key or wallet data was read. The accessor/provider is not emulated.

The declaration calls the returned payload an S3 presigned POST. Its actual
provider host, policy values, expiry, ownership, persistence, server auth/CSRF
rules, quotas and error schemas remain unknown. There is no retained successful
production video-upload response in this qualification. Static credential
options establish neither anonymous access nor authenticated permission.

## Source binding and verifier

The deterministic
[contract](../../contracts/original-create-video-upload.json) contains 14 roles
for 13 distinct factory variants and 88 actual AST witnesses. Each witness has
the original object URL/hash, exact UTF-16 and UTF-8 byte ranges, node type and
source-slice hash. The direct and resolved metadata exports share one physical
factory. The two `586090` variants are not conflated: this packet pins the
`6a1606765ef3e83e.js` variant used in this route context.

The unchanged shared source reader authenticates capture bytes, inventory
entries and actual Turbopack registrations. Direct dependencies must belong to
the retained Create HTML script set; the selector additionally binds the
literal chunk path and factory ID in the actual lazy-loader bridge. The
verifier checks the consumed function scopes, values, argument aliases and
operation ordering, then compares the entire generated packet. It never
imports or evaluates a recovered factory.

From the repository's `app` directory, with the existing pinned dependencies
and checked-in capture inputs available:

```sh
node scripts/original-contracts/create-video-upload/verify.mjs --check
node --test tests/original_create_video_upload.test.mjs
```

`--app-root "/path with spaces/repository/app"` selects another complete input
tree explicitly. `--write` regenerates only the contract JSON; `--check` writes
nothing. Both require the real captures, manifest, inventory and existing media
binding. No generated WebM, local server, Next build, upload provider or private
runner is required. The new test file is included by the maintained
`node --test tests/*.test.mjs` step; no package or workflow change is needed.

The three focused tests rederive the actual source contract and reject changes
to origin, method, body order, status/result semantics, fabricated eligibility,
qualification counts and source witness identities. These are source/integrity
checks, not simulated requests or original-runtime behavior tests.

No application/SDK/backend implementation, mounted behavior, native API
compatibility, browser qualification, original source-file identity or feature
milestone is claimed. Existing captures, source packets and SDK bytes are
unchanged.
