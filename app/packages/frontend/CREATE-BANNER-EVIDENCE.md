# Optional local Create banner

The captured Create workflow has an independent optional **Add banner** control.
The maintained offline form had no banner state or preview. This unit adds that
usable local interaction while preserving the existing coin image, video covers,
metadata JSON and disabled launch boundary.

## Original evidence

`node scripts/original-create-banner.mjs --check` authenticates retained capture
bytes, registration ranges and factory hashes through the shared source reader.
It parses JavaScript as inert syntax; no captured factory is executed.
The generated [contract](../../reconstruction/create-banner/contract.json)
contains exact UTF-16/UTF-8 ranges, hashes, source snippets and excluded boundaries.

- Create factory `734638`, SHA `616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc`, in `89ce7de3b9bad421.js`, uses a second `K` selector with `isBanner:true`, `maxFiles:1`, `accept:eX.G`, independent selection/preview state and a replace callback. Its native input is recovered separately in selector `658259`.
- The actual Create HTML `5e15667ed36cac85` includes the page chunk and common chunk `6a1606765ef3e83e.js`. That selected physical common chunk contains `586090` SHA `5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4`, whose `G` map admits JPEG/PNG/GIF/WebP and whose `O.BANNER` is 4,500,000 bytes. Other factory variants are not treated as unique by numeric ID.
- Selected `66094` SHA `a47ef1abe034e30194f5ebc662e2dddefb6beb96a7a9d9cd04f639d6cf664f2d` supplies production image operations. `734638`'s `ta → e7` path sniffs type and may resize static images; GIF and detected animation follow a different path. These operations are recorded as **unimplemented**, rather than inferred from local success.
- Labels `29542` recommend 3:1 and 1500×500. Selector `658259` uses a 3:1 display frame. Neither is a hard aspect-ratio admission rule.
- Production `e6` pins a banner and calls `POST /coins/add-banner` after a successful create response or transaction confirmation. It is separate from token metadata. This unit implements no part of that request/upload/confirmation path.

## Explicit local adaptation

The local picker works anonymously in React memory. It admits only the four
**declared** MIME types and a nonempty file no larger than 4,500,000 bytes before
native image decoding. A 10-second timeout and 16,777,216 decoded-pixel bound are
local allocation policies, not recovered upstream limits. They cannot prevent
all decoder allocations or establish file-content safety.

Files are neither sniffed nor resized. In particular, some oversized static
images accepted after production normalization are rejected locally. No animated
format behavior beyond this browser's native decode is qualified. A non-3:1 file
remains valid; the preview's frame crops only its display, leaving file bytes
unchanged.

The banner stays in its own panel. It adds no property or blob URL to the existing
metadata JSON, SDK parameters or exported token-metadata object. The panel reports
filename, declared type, byte count and decoded dimensions with **not uploaded**
wording. No URI, persistence, immutability, fee, eligibility or launch claim is
made. Historical production copy about irreversible banners is not presented as
local policy.

`BannerDraftSession` owns accepted object URLs and cancels superseded decodes.
Failed replacements preserve the accepted banner; the error must be cleared by
replacement or removal before the form reports a ready draft. Replace, remove,
reset and unmount release resources. Reload discards the selection. Selecting a
banner does not replace the coin image or video cover.

## Verification

- `pnpm test:create-banner`: authenticated source contract plus explicit
  admission, decode, timeout, replacement, cancellation and cleanup tests.
- `node --test tests/original_create_banner.test.mjs`: generated proof freshness.
- Frontend `pnpm typecheck` includes the actual mounted component and browser cases.
- `pnpm exec playwright test tests/create-banner.spec.ts` uses real PNG decoding
  and the native keyboard picker for success, bad files and decode failure,
  resource lifecycle, metadata separation, reload and local desktop/mobile fit.
  One separately labelled stalled-decoder case uses a synthetic port solely for
  cancellation. It does not claim real codec success or source pixel parity.

Exact executed revisions/results and remaining gates are recorded in the PR and
its validation note. Root evidence gates, unchanged capture/SDK checks and relevant
maintained Create cases remain required. No feature-progress or full-compatibility
credit is claimed.
