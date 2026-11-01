# w17a30-shim-hk2stand: a zero-instruction frame stand-in for the original's hk2 copy (shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `hk2stand`, keys `0x22a10-w17-8bee075-hk2stand-*`.

## Result

| step | main | admin_cto | M | slots | bytes | normalized / raw | differential |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| before | 57001c014 (= 8bee075 bytes) | 0.68754 | 2,295 | 3,096 | 27,400 | 1034 / 1034 | |
| this lane | 57001c014 + hk2 stand-in + vt + w17a16 WXvp outline/order base + cnat + wown | **0.69542** | 2,322 | 3,224 | 27,400 | 1034 / 1034, zero losses | 388 / 0 |

Calls stay 154 / 3. The 307/312 `to_string` calls are outlined as in the original (86 lddw, the callee multiset and
`.rel.dyn` of w17a16's outline base), and the validate error blocks are in the original's order.

## Mechanism

The original copies holder_key to `-0x518` (hk2) right after the sharing-key copy at `-0x470`, and that copy is live
across validate. Main has no such copy, so StackColoring puts the sharing key (`skm`) into FI47 (`-0x518`) and the
validate error-name Strings into FI39 (`-0x470`), a rotation of the original (sk `-0x470`, names `-0x488`).

1. **Stand-in.** A 32 B `MaybeUninit<[u64;4]>` (`hk2`) declared right after `skm` gets rustc's StorageLive there and
   StorageDead on both block exits (two ENDs, so StackColoring treats it as conservative: live from its START, with no
   use at all). `llvm.var.annotation` (declared on line 8 like the other intrinsics) keeps the alloca through SROA and
   is dropped at ISel, so no instruction is emitted. Its alloca sorts after `t.i` and before `skm`, so FI44 takes `t.i`
   first and FI47 takes `hk2` before `skm`: `skm` -> FI39 `-0x470`, names -> FI40 `-0x488`, `hk2` -> FI47 `-0x518`.
   The source capture has the post-opt probe's exact signature (`b4c5b05f0d5e` on main).
2. **Cascade repair (vt).** Alone, the stand-in replays the b01 cascade: names -> FI40 push `_73.i/_61.i` to FI45,
   which pushes the `?` piece `_64.sroa.11` to FI46, `target.i.sroa.9` to FI52, `target.sroa.8` to FI54, and the 7 B
   `target.i.sroa.0` becomes a new host at `-0x548` (everything below moves 8 B, M 1,884). A post-opt screen of the 122
   single marker deletions (`data/d1.jsonl`) found three nfd-0 repairs; the source-reachable one is validate's own
   `target`: hold it in a `MaybeUninit`, `lte` it at the non-holder arm head and `lts` it right before `target.write(t)`
   (the explicit END/START bracket the 306/307/312 checks, so its offset-1 pieces are free there). The source capture
   equals the IR probe (`608c3b648c24`, nfd 0).
3. **The colouring pays only with the original error order.** On main's inline base the recoloured error blocks match
   the original's blocks out of order, and difflib loses: stand-in + repair has true LCS +15 but M -47 (V2 -35, V3 -20).
   With w17a11's C1-pred order (llc only) the same frame gives +32 (2,303 -> 2,327). w17a16's WXvp base (307/312
   outlined, explicitly threaded validate head, 306 3:1) has that order in source: 2,300 @27,328 -> **2,330** with the
   stand-in and vt.
4. **MemCpyOpt detail on WXvp.** With `hk2` declared between w15a21's `let creator=a.bonding_curve.creator;` and its
   use, the shared arm's `target=creator` copy is no longer forwarded from the curve account: `creator.sroa.0/4` become
   two new hosts (nfd 72). Declaring `hk2` first and the creator binding after it is byte-identical on WXvp and keeps the
   forwarding. A 40 B `hk2` at the block head sorts before `t.i` and merges into FI44 instead (2,154 on main).
5. **Repay to 27,400 B:** w17a16's `cnat` (+40 B, -3) and `wown` (+32 B, -5) are additive here: 2,322 @27,400.

## Probe tables (`data/`)

| probe (llc on the captured post-opt IR) | M | bytes | nfd | sk / names |
| --- | ---: | ---: | ---: | --- |
| main | 2,295 | 27,400 | 0 | -0x518 / -0x470 |
| stand-in X (32 B, before skm) | 1,884 | 27,400 | 89 | -0x470 / -0x488 |
| X + `_64.sroa.11` START moved to its use | 2,248 | 27,400 | 0 | -0x470 / -0x488 |
| C1-pred order (w17a11, `bb14.i` 51:49) | 2,303 | 27,400 | 0 | |
| C1 + X + repair | **2,327** | 27,400 | 0 | -0x470 / -0x488 |
| WXvp | 2,300 | 27,328 | 0 | |
| WXvp + X + repair | 2,331 | 27,328 | 0 | |
| source WXvp + Xc + vt | 2,330 | 27,328 | 0 | |
| source + cnat + wown | 2,322 | 27,400 | 0 | |

Other source results: X before the creator binding on WXvp 1,850 (creator hosts); Dm / Dx49 threaded head on the inline
base 1,994 @27,248 (collapse); `Result<P8>` (aligned validate return) 1,466 / with X 1,380 (collapse).

## Peel notes

- `hk2` + `vann`: the slot only needs to be a conservative 32 B object live from E3 to the end of the tuple block. A
  faithful replacement is the original's actual hk2 copy (holder_key by value into validate, w14/w17a14 b01), which
  so far costs ~259 M of code shape; the stand-in keeps main's data flow.
- vt: the explicit `lte`/`lts` on validate's `target` reproduce what a target binding created after the non-holder
  checks would give; an ordinary spelling needs `target`'s storage to start after the 312 check on that arm.
- The WXvp genes (w17a16) carry their own peel notes (`as u8` match, 306 `read_unaligned`, compares kept in memory).

## Tools (`tools/`, experiment only; paths point at this lane's cache dir)

- `hprobe.py <capopt m.ll> <specs.py> <out.jsonl>`: post-opt llc probe. Inserts a stand-in alloca, lifetime markers,
  `llvm.var.annotation`, raw lines, deletions, a block reorder (`order`) and branch weights (`w`); reports M, bytes,
  signature, the frame-host diff (nfd) and where `skm`, the stand-in and the validate name Strings land.
- `gx.py` (this lane's source genes: `decl`, `X`, `Xt`, `Xh*`, `Xc`, `vt`, `p8`), `mksrc.py` (main + w17a16 g16 genes
  + gx genes), `g16.py` (w17a16's genes, ARM_V updated for main 57001c0), `capg.sh` (crate copy + capopt capture),
  `knobs.sh` (repay knob screen), `dreg.py` (difflib matched tokens per region), `acc.py` (r10 access map per region).
- `specs/`: s0/s1 (stand-in placement, repair), s2 (C1 order), w1 (WXvp), d1 (marker-deletion screen), h1 (vt).

## Maintained source qualification, 2026-11-01

The maintained identity build reproduces 69.542% token similarity (2,322 matched
instruction tokens), with all 1,034 raw and normalized Pump windows preserved.
The `llvm.var.annotation` annotation and filename operands now point to valid
static NUL strings. NULL operands did not meet the documented LLVM contract.
The correction preserves the loaded image exactly, while the unstripped ELF
hash changes; full unstripped identity to the authored build is not claimed.

Fresh current-main and corrected builds used the unchanged maintained compiler
and scorer. The corrected image passed 388 signed Admin CTO case pairs with no
mismatches, plus 22 cross-program lifecycle transactions and independent replay.
The candidate remains unequal to the deployed whole Pump ELF. Positional byte
differences increase from 3,096 to 3,224 despite the token-similarity gain.

The exact validator body received an official-target lifetime/initialization
and Option-layout review. These are pinned compiler, valid live Anchor-context
reconstruction shims, not portable layout guarantees or historical source proof.
The private experiment helpers were not used for qualification and were removed.
