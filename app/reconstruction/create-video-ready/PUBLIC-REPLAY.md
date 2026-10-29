# Replay from public commits

These commands replay the candidate tests. Historical before/after results remain
in `validation/`; collection does not repeat a browser run. Use an existing clean
checkout with pinned dependencies and Chromium already available. No install,
ffmpeg, private commit or generated media input is required: both WebM fixtures
are tracked public Git blobs.

Public source `f4c54995dac4a2d294799393a23f00f514b921f2` has complete tree
`569f4049c4d3af32f9dd50ff53b886da92ea870a`, identical to historically measured
private `4fa1124d7d20bcb5182e23c2122c9e3e0dc65252`. The later public
`9abaa060565daaf7ac658d0e4774def6f3376274` adds receipts without changing those
runtime files or tests. Use the fetchable source below.

From the repository root, verify the checkout is clean and fetch the exact
public source. This leaves the checkout detached at that source; record your
starting branch/commit before switching if you intend to return.

```sh
set -e
test -z "$(git status --porcelain)"
git rev-parse HEAD
git fetch --no-tags --depth=1 --filter=blob:none \
  https://github.com/shawkkkkk/pumpfun-source.git \
  f4c54995dac4a2d294799393a23f00f514b921f2
git switch --detach f4c54995dac4a2d294799393a23f00f514b921f2
test "$(git rev-parse 'HEAD^{tree}')" = 569f4049c4d3af32f9dd50ff53b886da92ea870a
VIDEO_REPLAY_OUTPUT="$(mktemp -d)"
cd app
node --experimental-strip-types --test \
  tests/create_video_preview.test.mjs tests/create_video_bindings.test.mjs \
  > "$VIDEO_REPLAY_OUTPUT/models.log" 2>&1
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test \
  tests/create-video-ready.spec.ts tests/create-video.spec.ts tests/create.spec.ts \
  --list > "$VIDEO_REPLAY_OUTPUT/collection.log" 2>&1
```

Expected: 37 model/source-binding tests and collection of 16 browser cases.
The filtered `exec` sets cwd to `app/packages/frontend`, where the fixture
resolver looks. The VP8 file is 677 bytes, SHA-256
`6e6a587654ecde9db701232d18836a37e84bb5ef2e676d3f4572e0633e9e9f35`;
`empty.webm` is a real zero-byte file. The optional ffmpeg example records
provenance, not a setup step or a cross-version regeneration guarantee.

To run the actual finite browser cohort, first release port 3010. Continue from
the same `app` directory and shell, retaining the fresh output variable:

```sh
PLAYWRIGHT_JSON_OUTPUT_FILE="$VIDEO_REPLAY_OUTPUT/browser.json" \
corepack pnpm --filter @pump-reconstruction/frontend exec playwright test \
  tests/create-video-ready.spec.ts tests/create-video.spec.ts tests/create.spec.ts \
  --reporter=line,json --output "$VIDEO_REPLAY_OUTPUT/browser-artifacts" \
  > "$VIDEO_REPLAY_OUTPUT/browser.log" 2>&1
```

No temporary config or test copy is needed. Outputs go to the newly created
external directory; published receipts and previous runner artifacts are not
used as the output directory. Keep that directory, including failed results.
Next may regenerate `app/packages/frontend/next-env.d.ts`; after all owned
processes stop, compare it with the pinned Git blob and restore that generated
file if needed. Do not delete another process's cache or alter dependencies.

The archived `validation/run-final.py` is the exact historical executed
controller, including old absolute paths and its private HEAD guard. It remains
unchanged and is **not** the public replay entry point. The sequence above uses
the same checked-in cases and application safety guards without removing the
historical guard or requiring its private object. It does not automatically
repeat the historical baseline phase.
