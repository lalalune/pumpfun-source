# w14a64-cto-shiftpair: size-shift oracle pairs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a53-cto-stitch11 (#3361) section 3. Ledger approach `shiftpair`, keys `0x22a10-w14-<main7>-shiftpair-<name>-v1`.
Tools (`tools/`, experiment only): `shift.py`/`rx.py`/`fnbin.py`/`segdiff.py`/`splice.py` (from w14a53),
`mcount.py` (w14a55), `cls.py` (w14a47), `shiftk.py` (w14a31), and new `jwhy.py <fn.bin> [+pos] [-pos]`: applies the pure
shift.py edit(s) and lists exactly which jumps / instructions change matched status (explains a shift-map entry).
`run.py <spec> [workers]` + `genes.py` (stitch11 library plus this lane's genes); run with `SRCBASE=<pristine main crate>`.

## 1. Shift map on main 2e1379d (M 2,194 at 27,400)

- Pure -8: best cand 0x16e8 (+5 M; the `stxdw [r10-0x8d8],r8` holder spill in the post-validate join). `jwhy.py`: only 2 of
  the 5 are jump distances (0x7d0->0x5708, 0x8b0->0x5830, both validate edges to the shared error tail at 0x5708/0x5830);
  the other 3 are local re-alignments that need that exact spill gone (RA, not a size knob). Any -8 in 0x800-0x1c00: +2.
- Pure +8: best entry block 0x180/0x1a0 (+1; the local `jne r0` at 0x178->0x1a0). 0x400-0x1c00: +1; 0x2000+: negative.
- Pairs (top-40 and a 256 B grid): +0x180/-0x16e8 +6, +0x54c0/-0x5a20 +4 (0x6d8->0x5708, 0x54b8->0x5830, 0x6370->0x5830),
  +0x2480/-0x5b20 +3.
- On the -8 lead `cu_iflet2` (curve fee `if let Some(f)=fee{..}`, 27,392 B, M 2,193) a pure +8 anywhere in cand
  0x5930-0x5af8 (sweep native arm: Rent / saturating_sub / ensure_rent_exempt / transfer_native) gives M 2,198 (main+4);
  0x5400-0x6100 gives +3.
