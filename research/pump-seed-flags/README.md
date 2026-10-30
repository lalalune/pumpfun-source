# Preserve compiler flag inputs in clean-producer cache seeds

The current verified builder preserves inherited `RUSTFLAGS` and
`CARGO_ENCODED_RUSTFLAGS` for Cargo, but omits them from its saved environment.
`DependencyCache.import_clean_build()` correctly requires those exact flag inputs
to match before admitting external artifacts from a clean build. Consequently a
real clean producer invoked with explicit flags cannot seed its next build with
the same flags: the producer's report loses an input the consumer must check.

Record both optional flag carriers when present, using their exact strings. The
existing strict seed comparison stays unchanged; a different flag context remains
ineligible. Reports without either override retain their existing field set. No
source, dependency/cache recipe, target-library profile, compiler behavior or
admission relaxation changes. The single frozen root-script transition is bound
in the adjacent proposed asset record.

The actual proof uses the preserved Round38 primary source from
`75e2066c99a4f862f545cb66fda855e67d684a03`, tree
`fb436ff37d4ff6e0d05d7af8f2011b056b258511`. Its published checkpoint records clean
and external-cache parity; all 254 external locked packages are registry packages,
with no unsupported local/path dependency. The proof fetches that exact public
commit and verifies the tree and both manifest/lock hashes before extracting only
the source into an owned work directory. It does not remove current path
dependencies to manufacture an admissible input.

Using the authenticated native v1.44 SDK and the admitted Linux SBPF profile, the
driver performs a real clean build with `RUSTFLAGS=-Zremap-cwd-prefix=` (the same
flag the builder normally supplies through the target-specific carrier), then a
real cache-seeded build with the same environment and registry path. Their actual
candidate and symbol ELF hashes must agree and the cache must report a verified
hit. A fresh cache with deliberately different flags must still reject the seed
before a compiler build; it is an admission-negative control, not a flag search.

```sh
python -B research/pump-seed-flags/reproduce.py
```

Actual compiler logs, producer reports, ELF gzip files and negative-control logs
are retained in `work/scoped-proof`. SDK/cache/target trees remain outside the
artifact. This is supported historical-source tool behavior with the explicitly
supported SBPF profile, not a claim to reproduce Round38's published SBF ELF, new
byte matches or VM equivalence. The primary run exercises the plain flag carrier;
both carriers are preserved by the same optional-field serialization rule.
