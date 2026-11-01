# w17a19-shim-lifetime: explicit llvm.lifetime.start/end markers (shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 4d09af488 (0.68514, 3,092 slots, M 2,287). First found on main 8330455eb (0.68244 -> 0.68334).
Ledger approach `shim-lifetime`, keys `0x22a10-w17-<sha7>-lifetime-*`.

## Result: +3 M, 0.68514 -> 0.68604 at 27,400 B

| build | admin_cto ratio | slots | bytes | normalized / raw | losses | calls | unstripped sha16 |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| main 4d09af488 | 0.68514 | 3,092 | 27,400 | 1034 / 1034 | - | 154 / 3 | |
| this lane (r3a2) | **0.68604** | 3,092 | 27,400 | 1034 / 1034 | 0 / 0 | 154 / 3 | 4ad326fd57505151 |

Runtime differential: 388 cases, 0 mismatches. (On main 8330455eb the same edit measured 0.68244 -> 0.68334, sha16
136de889cecf08ca, 388/0.)

### Mechanism: a LIFETIME_START node between the fee_configurable load and the creator memcpy flips the copy

The original writes the CtoState creator ascending (`stxdw [r10-0x38]`, `-0x30`, `-0x28`, `-0x20`, E3 at orig +0x470).
Main wrote it descending. In SelectionDAG every `llvm.lifetime.start` becomes a LIFETIME_START node chained on
`getRoot()`, so it sits between the pending loads and the memcpy's loads/stores; that changes the list-ilp bottom-up
order of the four independent stores. Post-opt IR probes (llc only, `tools/pscr.py`):

| probe (post-opt IR, main 8330455) | creator stores | M |
| --- | --- | ---: |
| main | -0x20 -0x28 -0x30 -0x38 | 2,278 |
| start(st) moved to bb5, or a 2nd start(st) before the copy | unchanged (byte-identical) | 2,278 |
| start(sk1/target.sroa.0/target.sroa.8/_51.sroa.11) right before the memcpy (after the fee_configurable load) | **-0x38 -0x30 -0x28 -0x20** | **2,281** |
| the same start before the global-pointer or fee_configurable load | unchanged | 2,278 |
| start(q) before the memcpy (q is non-conservative: recolours) | ascending, frame collapses | 1,874 |

So the marker must (a) be a different slot than the copy's destination, (b) come after the fee_configurable load and
(c) not change StackColoring (sk1 is already conservative, live from bb12, and colours into FI47 either way).

### Source (line 339, no line added)

- line 8: `extern "C"{#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);}`
  (unused it is byte-identical: capture `n0`, signature equal to main).
- the validate key `sk` becomes a `MaybeUninit<Pubkey>` declared just before the CtoState literal, so its slot exists
  when the literal is evaluated;
- the creator field is `creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: ...*/;a.bonding_curve.creator}`;
- `let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(a.sharing_config.key());&*skm.as_ptr()};` replaces `let sk=..key();`
  and validate takes `sk`.

The capture of this source has the same output signature as the post-opt probe `c16` (sk1 start moved before st's
start plus one more start right before the creator copy).

Peel note: the construct to replace is the extra lifetime start; any ordinary-Rust form that leaves a StorageLive of a
dead, already-conservative slot between the fee_configurable field and the creator copy reproduces it. A plain
`let x` binding inside the creator field does not: MIR CopyProp removes its storage markers.

## Screens (all on main 8330455 unless noted; tools in `$C/lanes/w17a19-shim-lifetime/tools`)

- `lscr.py` (pre-opt IR, capraw slim + opt -O3 + llc, ~2-4 s/variant under load): 307 execute variants over 17 anchors
  for mint sk hkx q st sk1 target sharing_update pargs e ix ix_data _48 _51 _52 _296 _81 _445 — extra start (S2), moved
  start (MV = deferred `let x;`), early end (E), and an extension segment after rustc's end (X). 188 byte-identical, none
  above main. Every X extension of sk1/st/sk/target into wallet/sweep adds or moves a host and collapses (M 1,215-1,893).
  184 validate/wallet/sweep variants (`gen2.py`, block-start anchors): none above main.
- Why S2/MV are mostly identical: 50 of execute's 137 marked slots are conservative (two ends from the `?` Err path, or
  two starts), so StackColoring makes them live from the first START; the rest use first-use liveness, so moving their
  START earlier changes nothing. Only extensions that create an overlap move colouring, and those cascade.
- `pscr.py` (post-opt IR, llc only, ~1 s): b01 (validate takes holder_key by value) on 8330455 is M 1,858 @27,384
  (frame shift +8 below -0x548, the 7 B `target.i.sroa.0` loses its FI54 host). Moving `_51.sroa.11`'s START from bb12
  into bb79 (its only use) restores main's host list exactly (all offsets/sizes equal) but M is 2,019: b01 itself is
  -259 in code shape on this main, so its frame repair is not worth realising.
- `flipscr2.py` (post-opt, main 4d09af4): every START that follows a >=16 B memcpy in the same block, moved before it.
