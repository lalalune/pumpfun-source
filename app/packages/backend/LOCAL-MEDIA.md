# Local Create-media lifecycle (not IPFS compatibility)

This opt-in backend module stores **synthetic/local development images and
metadata** on the local filesystem. It is an actual upload/read/delete service,
not fixture replay or a 501 placeholder. It does **not** implement Pump's IPFS
API, publish content, create a CID, obtain a presigned URL, connect a wallet,
construct/sign a transaction, launch a token, or call any network provider.

The default app/server leaves these routes disabled. An operator must explicitly
provide both `LOCAL_MEDIA_DIRECTORY` and `LOCAL_MEDIA_TOKEN` to enable them.
The current `/create` browser page
remains an in-memory draft. **This is a loopback API/CLI capability, not a working
browser Create-upload integration.** Every `Origin` header is rejected; future
browser use requires a separately reviewed exact-origin model, not relaxing the
guard in place.

## Evidence and what it establishes

`contracts/create-media-bindings.json` pins seven retained capture objects, ten
factory identities, their UTF-16 ranges, and the import chain. Every selected
factory's exact source chunk appears in the authenticated `/create` HTML script
set. Numeric IDs are resolved in that route context, not treated as globally
unique. The `586090` limit variant in the Create route is `5ddcdce058df…` from
`6a1606765ef3e83e.js`; the other known variant is not silently substituted.

The captured public snapshot is dated **2026-10-28**, acquired using the recorded
Googlebot user agent. It does not establish an authenticated browser state.
Captured scripts were read as inert text and never evaluated.

Observed static flow:

1. Create factory `734638` calls image helper `729047.w`.
2. That helper uses `759257.j` → `30181.K` → contract client `402030`/`898661`.
   Origin factory `503630.R` supplies `https://frontend-api-v3.pump.fun`.
3. The helper calls **GET `/ipfs/pinata-presigned`**, with `credentials: include`,
   and reads `presignedUri`. Cookies being sent does not establish actual auth
   enforcement, token format, CSRF rules, expiry or response status.
4. It posts multipart fields `file`, `network=public`, and `name` to the returned
   URL through the bundled Pinata client, then consumes `data.cid`.
5. Metadata factory `778435` requires the uploaded image hash and assembles
   `name`, `symbol`, `description`, `image`, `showName`, `createdOn`, plus optional
   social/video/community fields. `729047.o` uploads `data.json` using another
   presigned URL and constructs an IPFS gateway metadata URI from `data.cid`.

The captured route declaration `15086` separately describes multipart
**POST `/ipfs/image`** and **POST `/ipfs/token-metadata`**. The current Create
helper does not call them. In particular, a JSON-only imitation of
`POST /ipfs/token-metadata` would contradict the declared multipart contract and
would not reproduce the observed Create path.

The unchanged published SDK's `createInstruction` / `createV2Instruction` accept
a `uri: string` for transaction instruction construction. They do not provide
the image/metadata upload lifecycle. This service never imports or invokes the
SDK. The website's use of this exact SDK version is not established.

Production response/error codes, server limits, rate/cache behavior, ownership,
pinning/deletion, provider availability and authenticated state remain unknown.
No successful production upload response or authorized mutation was captured.
**Production operations implemented/qualified by this module: 0/0.**

## Explicit enablement and access boundary — local design

The server opt-in uses `startWithLocalMedia`: neither setting means disabled;
one setting without the other, an invalid capability, or `HOST` other than
literal `127.0.0.1`/`::1` fails **before creating a directory**. `HOST` defaults
to `127.0.0.1`. No aliases, wildcard bind, credentials, or directory are guessed.
The runtime helper closes only a store it actually opened when construction,
registration, readiness or listening fails. Cleanup failures are preserved with
the startup error, not silently swallowed. A successful `buildApp` owns its
configured store and awaits `store.close()` on shutdown.

For explicit programmatic use, the integration contract is:

```ts
const store = await LocalMediaStore.open(operatorChosenDirectory);
registerLocalMediaRoutes(app, { store, token: operatorSuppliedLocalCapability });
app.addHook('onClose', async () => { await store.close(); });
```

Alternatively, `buildApp(fixtures, { localMedia: { store, token } })` registers
the local module and close hook independently of the developer API-key scope;
other app options and handlers remain intact. A caller constructing the app
without the startup wrapper must release its own store if construction throws.

No directory or capability is selected/generated automatically. Register only
when both are explicitly configured, and arrange cleanup if startup fails.
The independent local capability is 32–256 base64url characters, kept out of
browser code, logs, committed config and production credentials. The tests use
only a visibly synthetic token. This is a single-owner development capability,
not user authentication, wallet ownership or the format-only developer-key gate.

Every read and write checks the direct socket peer, not `X-Forwarded-For`:
`127.0.0.1`, `::1`, or `::ffff:127.0.0.1` only. An `Origin` header or cross-site
Fetch Metadata is rejected. Bearer authorization is checked using constant-time
SHA-256 digest comparison. No CORS headers or cookie authentication are added.
This is defense in depth for an explicitly loopback-bound development server;
it is **not** a safe way to expose these endpoints through a public reverse
proxy (whose socket would itself be loopback).

All responses are no-store and nosniff, with a sandbox/default-deny CSP and a
`X-Reconstruction-Mode: local-only` marker. Image bytes are served as attachments,
not trusted inline content. Capability access is required for content reads too.

## Local protocol

All paths below are relative to `/__reconstruction/media`. These are new local
routes, intentionally not `/services/frontend/ipfs/*` or `/v1/*`.

| Method/path | Behavior |
| --- | --- |
| `POST /images` | Raw image bytes with explicit JPEG/PNG/GIF/WebP Content-Type. Returns content hash, MIME, byte length, relative `contentUri`, and local-only marker. |
| `GET /images/:id` | Image descriptor. |
| `GET /images/:id/content` | Exact stored bytes, attachment disposition. |
| `POST /metadata` | JSON `{imageId,name,symbol,description,showName,twitter?,telegram?,website?}`. Image must already exist. Returns assembled metadata, hash, relative `metadataUri`, and local-only marker. |
| `GET /metadata/:id` | Descriptor and metadata envelope. |
| `GET /metadata/:id/content` | The assembled metadata JSON document itself; this is `metadataUri`. |
| `DELETE /metadata/:id` | Removes metadata, retains its image. |
| `DELETE /images/:id` | Removes an unreferenced image; returns 409 while any metadata references it. |

New images/metadata return 201, exact repeats return 200 without consuming another
quota slot. Deletion returns 204; missing IDs return 404. SHA-256 identifiers are
lowercase hexadecimal, **not CIDs**. Client filenames and paths are never used.

Metadata contains `image: /__reconstruction/media/images/<hash>/content` and
`createdOn: urn:pump-reconstruction:local-media`. All returned paths are relative,
authenticated loopback-only references. **They are not IPFS gateway URLs, public
metadata URLs, or chain-usable launch metadata.** No production-style URI is
invented. Repeated canonical metadata produces the same ID. No timestamps or
user/mint identities are fabricated. Social URLs are stored text and never fetched.

The narrower captured Create UI bounds are reused: name 32, symbol 10,
description 2,000 JS code units, image 4,500,000 bytes. Requiring well-formed
Unicode and HTTPS credential-free social links, restricting X/Telegram hosts,
rejecting unknown fields, and refusing video/community metadata are **local
design**. These are not inferred production-server limits. `showName` must be a
boolean; no server default is invented. The 16 KiB JSON request cap, 16 MB total
image-byte quota, 128-image quota, 128-metadata quota, error names and statuses
are local choices. Quotas can be explicitly lowered for tests/development.

Signatures reject obvious content-type mismatches. They do **not** prove that an
image fully decodes, is safe, lacks hidden content, or is malware-free. No image
decoder, transcoder, scanner, thumbnail pipeline or SVG support is implied.

## Persistence and lifecycle limits

`media.json` holds the versioned snapshot; bytes are base64 encoded. All writes
are serialized and create a new 0600 temporary file in the chosen directory,
fsync it, then rename it over the snapshot. Memory changes only after rename.
Validation/quotas happen before publication. Failed publication retains the
prior state and removes that operation's temporary file. This is bounded
development storage, not an efficient large-file database.

The snapshot byte bound is derived from the admitted image-byte and record
quotas, not from the HTTP metadata body limit. It accounts for each image's
base64 padding and JSON envelope, each metadata record's fixed fields, and up to
six JSON-encoded bytes per permitted UTF-16 text code unit. The same bound checks
serialized writes and files before reopening. Quota values are fixed for the
store lifetime; aggregate bounds that cannot be represented exactly as a safe
integer are rejected before acquiring ownership. Reopening uses explicitly
supplied limits again; lowering them below the stored contents still fails.

This corrects an ordinary restart inconsistency: under explicit small image
quotas, valid programmatic metadata with escaped/multibyte text, or many short
signature-accepted images, could be written successfully and then rejected by
the old independent size estimate on restart. For example, four admitted
metadata records produced a 194,172-byte snapshot while that estimate allowed
only 133,120 bytes. No snapshot schema, content hash, field limit, HTTP request
cap, or access policy changes. The 16 KiB HTTP JSON cap is still independent:
larger programmatic metadata is not newly admitted through that route.

An exclusive `.media-owner` file enforces one store/process per directory.
`store.close()` stops new access, drains admitted writes and removes its own
owner file. Graceful close/reopen is tested. **Crash-stale owner files are never
auto-stolen**; an operator must first establish that no writer is alive before
removing one. A stale PID alone is not ownership proof. A host crash can also
leave unreferenced temporary files. Whole-host power-loss durability and network
filesystem semantics are not qualified; the parent directory is not fsynced.

Startup rejects a symlinked storage directory/snapshot, nonregular or oversized
snapshots, unsupported schema versions, unknown fields, noncanonical base64,
altered content hashes, duplicate IDs and broken metadata/image references. A
failed startup releases only its own lock. The configured directory and ancestors
must be operator-controlled; this does not defend against a malicious local user
who can replace ancestor directories or modify files concurrently. In-memory
reads do not reread external disk changes until a graceful restart.

## Checks

From `app/` (no production network access or real credentials required):

```sh
python3 -m unittest discover -s tests -p test_create_media_bindings.py
cd packages/backend
node --import tsx --test test/local-media.test.ts
node --import tsx --test test/local-media-runtime.test.ts
node --import tsx --test test/local-media-snapshot-size.test.ts
```

Synthetic tests cover the complete lifecycle, restart, exact byte readback,
content JSON, repeat/concurrent requests, dependency-safe deletion, missing IDs,
invalid inputs, size/quota boundaries, wrong capability, non-loopback requests,
forwarded-IP spoofing, browser origins, isolated parsers, no `fetch`, immutable
read results, failed publication, owner locking, stale locks, corrupt snapshots,
and symlink paths. Factory mutation tests reject source range/hash/context and
SDK-binding drift. Bootstrap tests additionally cover default-off, paired config,
pre-filesystem host validation, actual opt-in app routing, ownership preservation,
shutdown, restart and startup-failure cleanup. The listen failure is synthetic;
tests do not open a network socket or instantiate a real capability.
Snapshot-size regressions additionally exercise escaped/Unicode metadata and
many short image records across restart, failed-quota rollback, read bounds,
ownership cleanup after rejected files, and exact aggregate quota arithmetic.
These qualify only the stated local service, not the original
website/backend behavior.
