# Current public packet minimizes preview metadata

The original qualification at `60b6bae7` retained a Next prerender manifest in
this packet. The current public tree omits that entire raw file. Its preview
field values are unnecessary to review the application source or the recorded
build/typecheck/evidence/progress outcomes. No field values were opened,
displayed, parsed, compared or classified for this follow-up.

The original artifact is preserved privately as opaque bytes, matching the
previously recorded 5,513-byte length and SHA-256. `PREVIEW-METADATA.json` retains
only its historical path, Git blob, public commit and digest. The exact previous
35-file inventory remains in `HISTORICAL-SHA256-MANIFEST-6ee012d6.json` as
**historical metadata**, including the old digest reference. It is not the
current packet membership list. The packet's top-level `SHA256-MANIFEST.json`
lists the files currently provided; it excludes the omitted raw file.
Six of the seven originally retained Next build artifacts remain unchanged;
the omitted seventh is represented by historical metadata only.

## Nonsecret generation provenance

The existing `checks.json`, `SOURCE-UNCHANGED.json` and cleanup receipt bind the
normal local build at `60b6bae73d661444b6e80680e418be9dc92c417a`. The operator who
ran it identifies it as an undeployed local build. These original receipts are
unchanged. The repository pins Next 16.4.1 and runs `next build --turbopack`;
its public `next.config.ts` defines no preview override.

The installed pinned Next generation code establishes the relevant path:

- `dist/build/index.js`, lines 737–741, calls
  `generatePreviewKeys({ isBuild: true, distDir })`.
- `dist/build/preview-key-utils.js`, lines 43–48, defines generation of a 16-byte
  preview ID and 32-byte signing/encryption fields using `crypto.randomBytes`.
  Lines50–91 may instead reuse valid string fields from a local `.previewinfo`
  cache. An expired cache is rejected during a build.
- `dist/server/cache-dir.js`, lines 19–25, returns no persistent cache directory
  for its Docker predicate, otherwise `distDir/cache`. That source branch is
  described here; no cache file or actual branch outcome was inspected.
- `dist/build/index.js`, lines 1756–1768, places `previewProps` under
  `prerenderManifest.preview`.

The JSON note binds the exact installed generation-source hashes and the public
repository configuration blobs. It does **not** establish whether this artifact
used fresh or cached fields, whether any particular value is a placeholder,
whether a value has any deployment use, or whether it is safe to publish. It
records framework provenance rather than classifying the retained values.

## Preservation and limits

Application/SDK source, tests, build configuration, raw build/check logs, browser
proofs and their measured revisions are unchanged. No tests, build, Next server,
network operation, provider connection or deployment was rerun. This is evidence
minimization, not a new runtime qualification or security review.

The raw artifact was present in earlier public Git history, including `6ee012d6`.
This follow-up does not rewrite that history, remove cached copies, establish
history erasure or provide security clearance. Historical exposure remains an
explicit limitation; the current public packet simply stops redistributing the
whole raw manifest. No sensitive-value inspection or private report submission
is part of this change.
