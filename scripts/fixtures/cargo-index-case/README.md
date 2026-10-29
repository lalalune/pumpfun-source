# Mixed-case Cargo index fixture

These are unchanged public upstream artifacts, retained only as inert offline
cache-preparation test inputs. No crate source is installed, built or executed.
Inflector is by Josh Teeter and upstream contributors; its BSD-2-Clause notice
is retained in LICENSE.md, obtained from the upstream repository's LICENSE.md.
This project makes no ownership claim over these upstream materials.

| File | Source | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Inflector-0.11.4.crate | https://static.crates.io/crates/Inflector/Inflector-0.11.4.crate | 17438 | fe438c63458706e03479442743baae6c88256498e6431708f6dfc520a26515d3 |
| inflector-index.jsonl | https://index.crates.io/in/fl/inflector | 11340 | cb2b8f9cd2baa2934fa604108cd792b30f83b4ba32de329607046984d2213957 |

The regression verifies both hashes and binds the archive to the 0.11.4 index
record's checksum. It wraps all 27 original JSON records in a derived Cargo v3
sparse-cache envelope with an explicit offline fixture revision marker. This
envelope is constructed by the test, not claimed to have been emitted by Cargo.
The framing follows [Cargo cache serialization](https://github.com/rust-lang/cargo/blob/06413ecf8cd3ec5b10b93ac2b85f6fad34f8597c/src/sources/registry/index/cache.rs#L202):
version byte 3, little-endian index version 2, a NUL-terminated revision marker,
and NUL-terminated version/JSON pairs. The JSON record bytes are not rewritten.

Cargo [lowercases the package name before index lookup](https://github.com/rust-lang/cargo/blob/06413ecf8cd3ec5b10b93ac2b85f6fad34f8597c/src/sources/registry/index/mod.rs#L531).
The archive retains the package's original capitalization. This fixture proves
the cache helper's file selection and output spelling; it does not run Cargo or
prove a build. Inflector is a real external compatibility input, not a dependency
claimed to occur in the current Pump lockfile.
