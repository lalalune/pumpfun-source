# w19b11-shim-custom-mir (landing note)

`validate` in `programs/pump/src/creator/admin_cto.rs` is a `#[custom_mir(dialect="runtime",phase="optimized")]` body on line 283, generated from its own post-opt MIR.
Tools, block-order and RA mechanisms, and how to regenerate it: `origin/swarm/w19b11-shim-custom-mir` (`reconstruction/pump-main/lanes/w19b11-shim-custom-mir/`).
