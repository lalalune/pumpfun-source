# Create Coin reconstruction evidence

This note maps the captured Pump frontend evidence used by the local `/create`
drafting form. Recovered factories are inert research inputs, not standalone
source modules, and were inspected statically. Ranges below are UTF-16 code-unit
offsets in the decoded captured object, as defined by
`app/recovered/modules.json`.

## Captured factories

| Factory | Factory SHA-256 | Captured object and range | Confidence | Relevant observation |
| --- | --- | --- | --- | --- |
| `734638` | `616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc` | `evidence/web/objects/89ce7de3b9bad421.js`, 119–66825 | OBSERVED | Create page factory: controlled name, ticker, description, website, X, Telegram and media state; production validation; preview; wallet/upload/transaction boundaries. |
| `29542` | `ede316c07dd8ceb3faff4f840fefbb61a5b1a18d372e600225db0f8410a661bd` | `evidence/web/objects/fd402d4185b44ce9.js`, 5207–9672 | OBSERVED | Create page labels, optional markers, upload guidance and preview copy. |
| `586090` | `dc5f49211b3e3c1d2ceb031e2f40ab9d9b327762c059fce10afedabd0b066f9d` | `evidence/web/objects/230764f4d2b8c952.js`, 33085–33411 | OBSERVED | Limits: name 32, ticker 10, description 2,000; accepted JPEG/PNG/GIF/WebP and video types; validator media bounds of 4,500,000 bytes for images and 10,000,000 for video. |
| `658259` | `691ff5f669927ccece0478631066f80ac94a832dd5fadae2a3a175f09372e6fa` | `evidence/web/objects/762f0784b7be61c0.js`, 138–5776 | OBSERVED | File selector/dropzone, image/video preview, replace action and file guidance. |
| `426091` | `93b70fac45ba969c312e0f7ec965b181d06a8332f7e1a4bba6751a63fd5555a4` | `evidence/web/objects/92f43c917bbc50e2.js`, 119–20735 | OBSERVED | Create-form URL patterns: X/Twitter hosts, Telegram hosts, and HTTPS website validation. |
| `421159` / `778435` | `c5cfe326d6205ed545cad91ccce1de02da3b1ac2429bc534a1f19faebe99e846` | `evidence/web/objects/1147ad0a1bf513f9.js`, 86246–87341 | OBSERVED | Production metadata assembly requires an uploaded image hash, constructs an IPFS image URL and invokes the metadata upload helper. |
| `985722` | `db8a6d669d7c3a8dedf92a8c926999dd0f530ff88ba2ba6926b7b41b0967d635` | `evidence/web/objects/2b47dd0b38a1608f.js`, 100948–124759 | DECLARED | Coin-route request schema admits name, ticker, description, social links, image/video and metadata URI. Its wider 200/100/10,000 limits are a server contract, not proof of the Create UI limits. |

The inventory also contains a second byte-identical-meaning `586090` variant,
SHA-256 `5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4`,
at `evidence/web/objects/6a1606765ef3e83e.js` range 21522–21848.
The reconstructed form uses the narrower limits directly observed at the Create
page call site.

## Field and validation decisions

| Local control | Evidence | Reconstruction decision |
| --- | --- | --- |
| Coin name | OBSERVED in `734638`; required by its production validator; 32 limit from `586090` | Required, 32 JavaScript string code units, whitespace-only rejected. No invented character set. |
| Ticker | OBSERVED in `734638`; required; 10 limit from `586090` | Required, 10 JavaScript string code units, whitespace-only rejected. Unicode is retained; no chain-specific casing or alphabet rule is invented. |
| Description | OBSERVED and marked optional; 2,000 limit | Optional multiline field with the captured limit. |
| Website | OBSERVED and optional | Optional, at most 2,048 characters from the declared route schema. Parsed with `URL`; local safety policy permits HTTPS only. |
| X / Twitter | OBSERVED and optional; captured regex names `twitter.com` and `x.com` | Optional HTTPS URL restricted to those hosts. The captured frontend also tolerated omitted protocol; requiring HTTPS is a documented LOCAL DESIGN safety narrowing. |
| Telegram | OBSERVED and optional; captured regex names `t.me` and `telegram.me` | Optional HTTPS URL restricted to those hosts. Requiring HTTPS is LOCAL DESIGN. |
| Image | OBSERVED production requirement and selector | One local JPEG, PNG, GIF or WebP up to 4,500,000 bytes. MIME and browser decode checks improve feedback but do not prove file-content safety. The object URL is preview-only and is revoked on replacement, removal and unmount. |
| Video | OBSERVED in the production selector and metadata helper | Optional offline MP4/WebM preview with three selectable JPEG covers; the chosen cover becomes the separate draft image. No upload, transcoding service or browser compatibility qualification. See `CREATE-VIDEO-EVIDENCE.md` for exact bindings, local safety bounds and test limitations. |
| Creator fee | OBSERVED as an optional advanced control in `734638`, admitted from 0.01 through 3 percent when a qualifying token/quote pair is selected | Not implemented. The necessary quote-pair dependency and applicability state are absent from this offline draft. |
| Initial buy / quote asset / banner | OBSERVED in conditional production UI | Not implemented. Their wallet, quote-pair, fee-sharing, upload and transaction dependencies are outside this local metadata draft. |

`showName` and `createdOn` occur in the captured production metadata object, but
they are not user-editable controls in this reconstruction. `metadataUri` is not
produced because the captured path requires a real upload first. The advanced
instruction inspector accepts a separate user-supplied URI without fetching it
or claiming it belongs to this draft.

## Local-only behavior

The draft, inline errors, selected file, object URL and structured preview live
in React memory only. Reset or reload discards them. The JSON panel is explicitly
descriptive local output; it is not represented as a production request or a
metadata upload result.

The following are intentionally unreachable: wallet connection, signing, RPC,
production API requests, file upload, IPFS pinning, transaction construction
and token creation. The separate advanced offline inspector constructs only an
unsigned SDK instruction from explicitly supplied public keys and metadata URI;
see `CREATE-INSTRUCTION-PREVIEW.md` for its narrower local inspection boundary. The launch action stays disabled
and explains this boundary. The usable action validates and previews the local
draft only.

Create preview website and social links now use the captured external-link
confirmation controller and the shared device privacy preference. See
[`CREATE-EXTERNAL-LINKS.md`](CREATE-EXTERNAL-LINKS.md) for the scoped integration,
source bindings and validation.

## Unknowns and limitations

- The captured factories do not establish original TypeScript names or the
  exact UI under every feature flag, authentication state or quote-asset pair.
- No retained original Create-page screenshots prove pixel-level appearance at
  the tested viewports. Local screenshots establish responsive quality only.
- Browser-provided MIME, filename and decode behavior do not authenticate media
  contents. No file is uploaded or persisted.
- The route schema is evidence for accepted request fields, not evidence that
  every field was simultaneously visible in the original form.
