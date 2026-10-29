# Independent normal production outputs

Exact tested source: `9dc2b26ab4a1ebc619974ce3fecaad6d9785ad84`.
Pinned pnpm 10.24 SDK/backend/Next production build, recursive typecheck,
698 capture/npm/unchanged-SDK checks and progress checks all exited 0.
`checks.json` is unchanged. The four logs are deterministically gzip-compressed
without editing their text. These are ordinary compiler/check outputs.

`mapping.json` binds raw/compressed bytes and distinguishes runtime/browser-method
inputs (identical at tested 9dc2, evidence-tool 5bde and finite packet 8cca) from
separately verified source-evidence inputs. The latter include the standalone
source verifier added at 5bde; they are not falsely attributed to the 9dc2 build.
The four external public fixture tools remain hash-bound references to #1751,
without copying its source or feature ancestry.

This append-only directory adds eight files. The original finite manifest,
source, same-method observations, PNGs and all prior receipts remain unchanged.
The final public leaf needs its own mandatory common gate. Generated raw Next
manifests remain private. No new browser execution, full-app browser coverage,
original API/provider/pixel parity or milestone claim follows from these checks.
