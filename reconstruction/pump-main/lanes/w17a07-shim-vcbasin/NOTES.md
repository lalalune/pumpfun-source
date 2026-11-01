# w17a07-shim-vcbasin: VC basin mixing with marked shims (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 SHIM
track. This lane owns the VC base: the le_vy1 validate closure (`VC` = w15a03 `L_N3h`; `VCsh` adds `lv_sh_ifelse`).
It continues w16a05-cto-skelsplice (#3869) and w16a14-cto-vcretune (#3884).
Ledger: approach `vcbasin`, keys `0x22a10-w17-<main7>-vcbasin-<trial>-v1`.

**Result: notes only, no landing.** Main moved three times during the lane: from 1647da0 (M 2,251) to 6d498c5
(w17a03 owner pin, 2,252), 442ae70 (rcinc, 2,257) and 9336aaf (312 `expect_p` + sharing `pf` pin, 2,259 / 0.67675). On the last one every VC composite is at least 38 M
below main. Its code-shape ceiling (Mhc) ties main's at best (A_c2 2,308 against main's 2,307). The kill test holds.
No marked construct moves basin B's TCF accounts pointer to r8 without either flipping the wallet or shifting the TCF
spill slots. No marked construct fixes basin A's colour order without the tail swap or a collapse.
While these notes were written, main reached e679b59e9 (0.67915, more w17a04 Rc-clone weights). Those shims are also
calibrated on main's basin, so the VC gap can only have grown. The VC rows were not re-priced there.

## 1. Oracles (experiment only)

Everything runs from `$OUT/tools`. That directory holds the w15a03, w15a16, w16a05 and w16a14 toolchains with their
paths re-pointed, plus the files below (committed under `tools/` and `probes/`).

- `tools/vscr.py <spec> [workers]` is w16a14's capture screen pointed at this lane. It does a capraw identity build
  with pre-opt IR, then SDK `opt -O3`, slim and SDK `llc`, and gives exact M and region dM. `m0` reproduces main
  (`eq_main: true`) on every base. A capture takes 20-250 s, depending on machine load.
- `tools/genes_vb.py` = w16a14 `genes_vc` plus this lane's shim genes: `cbr`, `cbrv`, `cbr2`, `n312`, `p312_*`,
  `stcb`, `stcb2` and `stcb3` (see sections 3-4).
- `tools/probe.py <m.ll> <name> [edits.py] [--opt]` is the post-opt IR probe (about 3-20 s). It prints M, region dM,
  and the TCF orig-r8 / wallet orig-r9 register maps (the w16a05 `regmap` over skeleton-matched tokens), so the basin
  shows in one line. `probes/*.py` are the IR edits used below.
- `tools/bscreen.py <m.ll> <kind> <out> [workers] [lo hi]` runs single-edit screens: `load`, `store` and `memcpy` make
  one access volatile (a `read_volatile` / `write_volatile` pin). `bw:<a>:<b>` puts `!prof` a:b on one conditional
  branch (the `expect_p` shim). Every row carries M, region dM and both register maps.
- `mp.py` (w15a16) gives Mperm / Mhc, the code-shape ceilings under a legal spill recolouring. It needs `rx142.py` and
  `llc.sh` from w16a14's `s16/`. Do not name a tool `dis.py`: it shadows the stdlib module and breaks `inspect`.

## 2. The VC basins on a moving main

| main | build | bytes | M | dM vs main | Mhc | TCF orig r8 | wallet orig r9 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 6d498c5 | m0 / B=VCsh / A=VCsh+t1n | 27,400 / 27,224 / 27,400 | 2,252 / 2,139 / 2,216 | 0 / -113 / -36 | | r8 / r6 / r8 | r7 / r9 / r7 |
| 442ae70 (rcinc) | m0 | 27,400 | 2,257 | 0 | 2,306 | r8:33 | r7:22 |
| 442ae70 | B | 27,224 | 2,144 | -113 | 2,248 | r6:20 | r9:32 |
| 442ae70 | A | 27,400 | 2,216 | -41 | 2,297 | r8:33 | r7:22 |
| 9336aaf (312 expect_p, pf pin) | m0 | 27,400 | **2,259** | 0 | **2,307** | r8:33 | r7:22 |
| 9336aaf | B (main's 312 `expect_p` 0.625 kept) | 27,392 | 1,726 | -533 | | tail swap | |
| 9336aaf | B_n312 (VCsh, 312 shim reverted) | 27,224 | 2,146 | -113 | 2,250 | r6 | r9 |
| 9336aaf | A (VCsh+t1n) | 27,408 | 2,221 | -38 | 2,302 | r8 | r7 |
| 9336aaf | A_n312 | 27,400 | 2,217 | -42 | 2,298 | | |
| 9336aaf | A_c2 / A_tai_tv | 27,400 | 2,205 | -54 | **2,308** | | |
| 9336aaf | B_frl1c2 | 27,368 | 1,728 | | | tail swap | |

- The main-tuned wave-17 shims do not carry over to VC. A did not get rcinc's +5 (A's TCF stayed at -14 when main's
  rose). Main's 312 `expect_p(..,0.625)` puts VCsh into the 6 KB tail-swap layout (1,726). B needs it reverted (`n312`)
  or set to 0.375 (`p312_375`: 2,146). 0.5 also swaps.
- Splice targets on 9336aaf (`splice2.py`; every row has 157 calls and each error line once):
  - B_n312[0:0x1c68] + main[0x1c68:0x5a08] + B_n312[0x5a08:] is **2,300 (+41) at 27,288 B**;
  - B_n312 front + main back (cut 0x1c68) is 2,285 (+26);
  - main front + B_n312 wallet (cut 0x5a08) is 2,274 (+15);
  - A_c2 front + main middle + A_c2 wallet is 2,253.
- Code-shape ceilings: A_c2's Mhc (2,308) is one token above main's (2,307), but its colour gap is 103 tokens against
  main's 48. A spill-colour repair of A_c2 that matched main's own colour quality would tie main, not beat it.

## 3. Basin B (mechanism 1): the second holder value, the TCF accounts pointer and the wallet

The IR facts on VCsh: `%45 = and i8 %0,-3` is the outer holder. Its i1 feeds the head `cashback` and the shared-arm
branch after validate, so it is live across validate. `%46 = and i8 %0,1` is the closure's holder. It feeds the closure
tests and the curve store. `%0` dies at `%46`, so in RA `%46` is `hopt`'s vreg masked in place.

| probe (IR unless noted) | construct (as a shim) | bytes | M | TCF r8 | wallet r9 | note |
| --- | --- | ---: | ---: | --- | --- | --- |
| B | (VCsh) | 27,224 | 2,139 | r6:20 | r9:32 | 6d498c5 base (vi..nop); ra, hm2, rbar and cbr are on 442ae70 (B 2,144) |
| vi | outer holder through a new volatile slot to the shared-arm branch | 27,368 | 2,214 | r8:33 | r7:22 | exactly basin A |
| vr | raw hopt in a volatile slot; the shared arm re-masks it | 27,376 | 2,214 | r8:33 | r7:22 | basin A |
| vh / vhl | `%46` through a new volatile slot to the curve store (vhl adds lifetime markers) | 27,216 / 27,136 | 1,956 / 1,994 | r6 | r9 | TCF -278 / -250 |
| vhr | raw hopt in a slot; the curve store re-masks it | 27,280 | 1,960 | r7 | r9 | collapse |
| nop | an unused 1-byte alloca stored at entry (calibration) | 27,272 | 2,120 | r7:18 | r9:32 | any new frame object moves the basin |
| ra (442ae70) | the sweep re-derives `a` with `read_volatile(&ctx.accounts)` | 27,248 | 2,025 | **r8:23** | **r9:26** | TCF -224, Mhc 2,217 |
| ra2 (9336aaf) | `ra` plus a second re-derive at the post-sweep join | 27,296 | 1,961 | r8:23 | r9:26 | sharing -73 |
| rbar (raw IR + opt) | `black_box(())` memory barrier at the start of `execute::sweep` | 27,224 | 2,144 | r6 | r9 | M unchanged (B and main) |
| hm2 | the closure's `and 1` reads hopt from a stack-coloured entry slot | 27,224 | 2,152 | r6 | r9 | +8, wallet +25 |
| source `cbr` | outer cashback from a raw u8 read of `new`'s tag | 27,120 | 2,140 | r6 | r9 | wallet +22 |
| es / esv (9336aaf, B_n312) | early curve store: `is_holder_reward` written (plain or volatile) right after the closure's mask, and the late store dropped | 27,136 | 1,993 | r6:20 | r9:32 | TCF -252; on A a tail swap (1,591) |

- **Basin B is exactly "a second holder value in a register across validate".** Carrying that value through memory
  (vi, vr) turns VCsh into basin A token for token (2,214, the same regions as `Lsh_t1n`).
- Ending the masked holder before the sweep (vh, vhl, es) never moves the accounts pointer. B's TCF stays in r6 and
  gets worse (-250..-278), so the masked holder's long range is not what holds the pointer in r6.
- **Only `ra` moves B's TCF accounts pointer to r8 and keeps B's wallet.** The original's TCF pointer is a spill-slot
  reload (`ldxdw r8,[r10-0x8d8]`). The re-derivation is a second accounts value with its own spill slot: every TCF
  spill offset moves by 8 and the TCF loses 224. On main the same construct costs 6 at +8 B (`m0_ra`). Its Mhc
  (2,217) is below B's (2,248), so the loss is code shape, not colour.
- The volatile-load screen on B shows the basin is rigid. All 445 single pins (`data/scr-B_load.jsonl`) keep TCF r6
  and wallet r9. The best is +32 on B (2,171, TCF -92), from pins in the TCF clone run (IR lines 4775-4780). Those are
  local scheduling gains, and they do not reach main.
- `llvm.expect` 1:2000 on each of the 146 conditional branches (`data/scr-B_bw1.jsonl`): 99 keep basin B, with a best
  of +13 from Rc-clone trap weights in the TCF. 47 flip into the tail-swap layout (TCF -494) or collapse. None gives
  TCF r8 with wallet r9.

## 4. Basin A (mechanism 2): the extra head reload of hopt and the colour order

| probe | construct | bytes | M | Mhc | note |
| --- | --- | ---: | ---: | ---: | --- |
| A (442ae70) | VCsh+t1n | 27,400 | 2,216 | 2,297 | the hopt slot is the heaviest spill slot and takes -0x8d8 |
| a2 (IR) | outer cashback from the closure's `%46` at the join; head `and -3` removed | 27,336 | 1,868 | 2,021 | collapse, same layout |
| a3 (IR) | curve-store cashback re-read from the curve; head cashback removed | 27,072 | 1,918 | 2,054 | collapse |
| hm (IR) | hopt stored at entry into a lifetime-scoped volatile 1-byte alloca (coloured into -0x4b8); both masks read it | 27,224 | 2,148 | 2,200 | **mixed basin: TCF r8 and wallet r9; accounts slot back at -0x8d8** |
| hm1 (IR) | only the outer `and -3` reads the slot | 27,360 | 2,215 | 2,288 | wallet -5 (from -14), sharing -20 |
| hm2 (IR) | only the closure's `and 1` reads the slot | 27,584 | 1,664 | | tail swap |
| source `cbu` (w16a14) | outer cashback via `hopt.unwrap_or(false)` | 27,368 | 2,214 | | |
| source `cbn` | outer cashback via `new.is_some()` | 27,200 | 1,607 | | tail swap |
| source `cbr` / `cbr2` | the same through a raw u8 tag read (no `!range`) | 27,232 | 1,611 / 1,605 | | tail swap |
| source `cbrv` | volatile tag read | 27,168 | 1,976 | | cold_err -105 |
| source `stcb` (9336aaf) | per-arm cashback in the CtoState local: the holder arm clears `st.cashback` through a raw pointer, and the outer block reads it after the closure (the original's `[r10-0x958]` phi) | 27,160 | 1,912 | 2,018 | the outer `and 253` is gone; the back collapses |
| source `stcb` on B / `stcb3` / `stcb`+`c2` | | 27,168 / 27,160 / 27,144 | 1,977 / 1,912 / 1,965 | 2,236 / - / 2,049 | |

- **What causes `cbn`'s tail swap.** With `cbn` the tag load carries `!range [0,2)` and the sharing tag phi folds to
  constants (`phi [1,..],[2,..],[2,..],[0,..]`). `cbr` removes that fact and the phi stays a phi, but the layout still
  swaps. The swap comes with the tag i1 being live across validate. The post-opt terminators match A apart from the
  outer test's predicate.
- **`hm` is the only probe in the target register basin.** It has TCF r8 and wallet orig r9 in r9, and the accounts
  slot takes the first colour again. But its code shape is worse (Mhc 2,200). Source also cannot scope a local's
  lifetime to entry..validate: a `let` declared at entry lives to the end of `execute`, and a new frame object moves
  every spill slot (see `nop`).
- Volatile-load screen on A (`data/scr-A_load.jsonl`): all 445 pins stay in basin A. The best is +4.
  `expect_with_probability` 2:1 and 1:2 on each of the 33 front branches of A_c2 (66 probes) give at most +6.

## 5. Kill test and conclusion

- B: about 25 marked constructs (sections 3-4) plus 445 load pins and 146 branch weights. None moves the TCF accounts
  pointer to r8 while keeping both the wallet and the TCF frame.
- A: about 20 constructs plus 445 load pins and 66 branch weights. None fixes the colour order without the tail swap
  or a code-shape collapse.
- On main 9336aaf the best VC realisation at the pinned size is A_n312 at 2,217 (-42). A at 2,221 is 8 B over. The VC
  code-shape ceiling (A_c2 Mhc 2,308) ties main's (2,307). So VC's remaining value is its front (+26) and its wallet
  (+15). Using them needs a way to steer register allocation that no marked construct gives.

## Next ideas

1. Keep the splice targets as yardsticks: front +26, wallet +15, and +41 for the three-piece splice on 9336aaf. Lanes
   that find register levers on main can test against them. The register facts are: the original keeps the outer
   holder only as the closure's `and 1` value (`jeq r8,0` at orig 0x1840) and carries per-arm flags in
   `[r10-0x950]` / `[r10-0x958]`.
2. `ra` (re-derive `a` inside the sweep) is the one construct that puts B's TCF accounts pointer in r8. A version
   whose second value needs no spill slot in the TCF, for example one with no use after the sweep, is untested.
3. `hm` shows that the mixed basin exists. A source construct that stores hopt at entry into an existing frame object
   that is dead until validate would make it testable. No such object was found: the entry-time locals (`mint`,
   `holder_key`, `hk`) have no padding.
4. The VC base should not be re-tuned against main's wave-17 shims. Each of them was calibrated on main's basin, and
   the 312 `expect_p` one pushes VCsh into the tail swap.
