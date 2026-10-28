# plainbody lane PROGRESS (base L06: 899 normalized / 165 raw, identity recipe)

Targets: W/targets/r4-plainbody.json (26 windows without Source sites).
Lane src: W/lanes/plainbody/src (copy of W/base/current/pump = L06). Experiments: W/lanes/plainbody/exp/<name>/{src,out}.

## Experiments
- e01 (0x49708 migrate v1 refund_pool_authority): seeds nested temporary passed into an inlined closure calling transfer_native (bodyloB-01's migrate_v2 form), line-neutral -> 900/165, gain 0x49708, no losses. DELIVERED plainbody-01.
- e02..e18 (0x17bc48 = create_v2 quote_extensions_supported(data,len,allow) -> bool, 1192 B, called by 0x1a918 create_v2.rs:528):
  rewrote the TLV walk as the original's shape (tlv=&data[166..]; loop head `let Some(rest)=tlv.get(offset..) else {return false}`;
  u16 reads via `from_le_bytes(rest[..2].try_into().unwrap())` -> ldxh; `size+4>rest.len()` before the kind match; checked_add
  advance) plus a separate per-type helper `extension_data_valid(kind,bytes)` with arms ordered 14,6,1 (e09). Findings:
  * without the helper LLVM non-trivially unswitches the TLV loop on `allow` (e02/e03 1448/1432 B): the original's loop was big
    enough at SimpleLoopUnswitch time because the 32-byte TransferHook check came in already unrolled from a callee.
  * arm order 1,6,14 lowers as `jeq 1; jeq 14; jne 6`; order 14,6,1 gives the original `jeq 1; jeq 6; jne 14`.
  * e09 (1184 B vs 1192 B) is byte-identical to the original except the shared `exit` block: original lays it out after the
    loop latch (`jge r5,r7,HEAD; exit`, padding-loop failure is a `ja`), ours places it after the padding loop. 72 structural
    variants (standalone exploration compiles, identical bytes to fastbuild for this function) and LLVM MBP knobs
    (tail-dup/tail-merge/branch-fold-placement) never move it. Parked: block-placement of the shared return; not a gain, so
    not delivered (lane src keeps the base form).
