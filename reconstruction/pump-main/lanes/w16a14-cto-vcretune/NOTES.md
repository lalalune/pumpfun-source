# w16a14-cto-vcretune: VC validate closure as the head, main's back half re-tuned under it (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto.rs identical to 1f4e396b5): 0.67436, 3,141 slots, M 2,251 (Mperm 2,295, Mhc 2,302).
Angle: w16a05-cto-skelsplice next idea 1 (#3869). Adopt VC (w15a03 `L_N3h` = `v7c+lv_ny+lv_le+lv_cf_skc+lv_h289`, the
le_vy1 validate closure) as the head and re-tune main's back half under it, instead of splicing main's back half on.
Ledger approach `vcretune`, keys `0x22a10-w16-1f4e396-vcretune-<cell>-v1` (one row per capture, written by `tools/vscr.py`;
IR probes and joint ceilings as `...-vcretune-irp-*` / `...-vcretune-joint-*`).

**Result: notes only, no landing.** Main stays the best zero-loss measurement (0.67436 / 3,141 / 27,400 B).
- The best VC composite at 27,400 B is basin A + the #3859 sweep revert + a -8 B knob: **M 2,217 (-34)**. No back-half
  re-tune moves either VC basin by more than +4 M: the compensators landed since #3409 are inert under VC.
- Basin A's loss is not code shape: its Mhc is 2,298 (main 2,302), and three TCF literal genes put it above main
  (`c2`, `tai_tv` 2,305; `s_tai2` 2,303). The loss is the **spill colour order** (section 4). VC's masked holder is the
  heaviest spill slot, so it takes -0x8d8 from the accounts pointer and rotates 7 window slots (about -36 M).
- Both VC basins have joint RA ceilings above main's at pass 2 (B 2,355 with 16 forces, A 2,351 with 14, main 2,338 with 9).
  The decisive forces are the known lever-less families: TCF clone temporaries for B and the payload phi `=r9` for A.
- Kill test (best VC composite at 27,400 B 10 M or more below main, and its joint ceiling does not beat main's): the first
  half holds (-34). The second holds only at equal force counts: A's pass-1 joint (2,312, 6 forces) is below main's pass 1
  (2,328, 7 forces), but at pass 2 both VC basins exceed main. Their decisive forces have no source lever, so the angle is
  closed as notes.

## Oracle (experiment only)

- `tools/vscr.py`: w16a05's `scr.py` (w15a03 capraw identity build with pre-opt IR, SDK `opt -O3`, slim, SDK `llc`, exact
  M and the w16a05 per-region dM) with this lane's paths. `m0` reproduces main (`eq_main: true`, M 2,251).
- `tools/genes_vc.py`: w16a05 `genes_w16` + aliases `VC` (= L_N3h) and `VCsh` (VC + `lv_sh_ifelse`, w16a05 `Lsh`) + the
  pre-PR spellings of every back-half compensator landed since #3409 (`r30w r30v r37p r37n r80e r80o r95 r21 r21n r66
  r59s r59e`; each was checked to reproduce the pre-PR source when applied to main) + the w16a04 additions (`c2 s1 tf_g1a g0
  po`) + this lane's new genes (sections 3, 5, 6).
- `tools/mploop.sh` runs w15a16 `mp.py` on every capture: Mperm = best permutation of the build's own spill offsets,
  Mhc = vote swap climb on top. Both are independent of the frame order. `tools/tab.py` prints the table, and
  `data/res-vc.jsonl` has every row.
- `tools/vpipe2.sh` / `vpipe2b.sh`: the core of w16a04's `lpipe.sh` (colmap vote, single-force screen, greedy sticky
  climb with the w15a24 RAPRIO llc), then the joint = Mhc of the forced build. `mpf.py` is `mp.py` run with
  `MP_LLC=llcf.sh` (`tools/mpf.patch`). `vscreen.py` runs the force screen in threads, because w16a04's `screen.py` process
  pool hung on 2 of 80 jobs. `tools/floo.py` gives the leave-one-out of each force.
- `tools/ssord.py` / `ssw.py`: spill-slot creation order and StackSlotColoring weight/colour order from a debug llc trace
  (`-debug-only=regalloc,stack-slot-coloring`, `~/.cache/pumpfun-reconstruction/llvm-dbg`; its object is byte-identical
  to the SDK llc's). `tools/hitdiff.py A B`: original tokens matched by one build and not the other.
- `tools/frc.py <m.ll> <name> [FORCE]`: patched llc with RAPRIO forces, M and region dM. It is used for the IR probes.

## 1. Ports (step 1)

| cell | genes | bytes | M | dM | Mperm | Mhc |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m0 | main | 27,400 | 2,251 | 0 | 2,295 | 2,302 |
| B = Lsh | VCsh | 27,224 | 2,139 | -112 | 2,241 | 2,247 |
| A = Lsh_t1n | VCsh + t1n | 27,400 | 2,216 | -35 | 2,259 | 2,298 |

(w16a05's `LN3h_c0s_shie` 2,201 / 27,376 and `LN3h` 2,105 were already re-priced on 1f4e396; the source is the same on
599891304.) B is the "VC basin": it keeps the original's wallet registers but puts the TCF accounts pointer in r6. A is
basin A: t1n moves it to main's TCF, and the wallet loses 14. Region dM is as in w16a05.

## 2. Leave-one-out of the back-half compensators (step 2)

Each landed compensator reverted to its pre-PR spelling, on both VC bases (`B_*` on VCsh, `A_*` on VCsh+t1n):

| revert | PR | B M (dM vs B) | B bytes | A M (dM vs A) | A bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| r95 shared test `key()==creator` | #3495 | 2,137 (-2) | 27,224 | 2,214 (-2) | 27,400 |
| r21 / r21n tuple-form sharing_update | #3621 | 2,137 (-2) | 27,224 | 2,215 (-1) | 27,392 |
| r66 CtoState fee_configurable last | #3666 | 2,139 (0) | 27,232 | 2,216 (0) | 27,400 |
| r80o curve store cashback first | #3480 | 2,139 (0) | 27,224 | 2,216 (0) | 27,400 |
| r80e event holder from the arg | #3480 | 2,139 (0) | 27,216 | 2,216 (0) | 27,392 |
| r59s sweep guard if / else-if | #3859 | **2,142 (+3)** | 27,232 | 2,217 (+1) | 27,408 |
| r59e event is_holder_reward late | #3859 | 2,139 (0) | 27,216 | 2,216 (0) | 27,392 |
| r37n event fee re-read (no nf local) | #3437 | 2,134 (-5) | 27,200 | 2,207 (-9) | 27,376 |
| r37p pool_authority rent_epoch re-read | #3437 | 2,140 (+1) | 27,232 | 2,216 (0) | 27,408 |
| r30w wallet `is_writable==false` | #3430 | **2,143 (+4)** | 27,232 | 2,216 (0) | 27,408 |
| r30v drop the 334 read_volatile | #3430 | 2,139 (0) | 27,216 | 2,216 (0) | 27,392 |
| c0h curve store from the tuple bool | #3409 | w16a05 Lsh_c0h 2,203 (basin A) | 27,376 | 2,203 (-13) | 27,392 |

No revert moves B's TCF out of its basin (TCF -122/-123 in every B cell), and none moves A by more than +1. In basin A the
compensators are inert: M stays 2,216 for 8 of 11 reverts. The two original-direction alternatives are both 0: the event
reading `is_holder_reward` late (r59e), and the curve store reading VC's masked holder (B itself).

`r30v`, which drops the 334 `read_volatile` placeholder, is M-neutral on both VC bases (-8 B), as on main (vol334_back
-1). Splice-priced composites (w16a02 `splice.py`, exact on local changes): A + r59s + one of r30v / r80e / r59e / I6n is
**2,217 at exactly 27,400 B**. That is the best VC composite at the pinned size (`A_r59s_r30v` also removes one forcing
placeholder).

## 3. Back-half family re-screen on basin A (step 3)

52 single genes on A (VCsh+t1n), from the TCF, sweep, sharing, wallet, pool/event and tail families of the w15a16/w15a03
library, plus w16a04's `c2 s1 tf_g1a g0 po`. Each family's representatives were the genes that apply to the VC source.
Rows with M >= 2,213, or with Mhc above main (full table in `data/res-vc.jsonl`, `tools/tab.py A_`):

| gene (on A) | bytes | M | dM vs main | Mperm | Mhc |
| --- | ---: | ---: | ---: | ---: | ---: |
| r59s | 27,408 | 2,217 | -34 | 2,260 | 2,299 |
| wl_frozen_let, w_ccswap, ur3d, pu_neg, g0, fru2, cu_match, I6n (-8 B) | 27,400 | 2,216 | -35 | 2,259 | 2,298 |
| sw1, cu_replace, cs_old_fee_first | 27,400 | 2,215 | -36 | 2,257-2,259 | 2,296-2,299 |
| K_g_canedit_first, cbu (-32 B), tl_PAN (+24 B) | | 2,213-2,214 | | | |
| m_a1 (-32 B), k3 (+8 B), sw2 | | 2,213 | -38 | 2,255-2,256 | 2,294-2,295 |
| **s_tai2** (TCF `program` via to_account_info) | 27,400 | 2,210 | -41 | 2,264 | **2,303** |
| **c2**, **tai_tv** (TCF vault ATA literals) | 27,392 | 2,201 | -50 | 2,266 | **2,305** |
| rw7, rw7b, w_cconly (wallet coin gate) | 27,400 | 2,208 | -43 | **2,293** | 2,299 |

Everything else loses more. Collapses (M < 2,100) come from s1, ct, wl_owner_chk, frl1, po, p0u, tl_NAP, evo_*,
sw_ifskip, w_collmatch, K_w_create_rev and e_nc. The best single is +1. The screen does not rescue basin A in M, but
the Mhc column shows that A's code is at main's level and that the TCF literal family puts it above main.

On basin B (VCsh), the sweep/TCF families (`tools/tab.py B_`): B's TCF responds to the TCF literal genes where A's does
not.

| gene (on B) | bytes | M | dM vs B | B's TCF dM |
| --- | ---: | ---: | ---: | ---: |
| **frl1 + c2** | 27,200 | **2,169** | +30 | -93 |
| frl1 (first pump_amm clone as `..*x`) | 27,216 | 2,161 | +22 | -98 |
| c2, tai_tv | 27,232 | 2,154 | +15 | -109 |
| frl3 | 27,256 | 2,147 | +8 | -112 |
| ct, k3, r30w, r59s | | 2,140-2,143 | +1..+4 | -122/-123 |
| s_tai2, m_a1, n_mapamt, sh_dest_ne, cd_holder_dest, fru1-4, frl2 | | 2,129-2,139 | -10..0 | |
| m_t1, sw_ifskip, s1, lf_au, frl4 | | 1,988-2,095 | collapse | |

A_frl1 is 2,099 (-117 vs A). B's best stays 82 M below main and 200 B short of the pinned size.

## 4. Why basin A loses: the spill colour order, not the code (mechanism)

A's code is as good as main's: **Mhc 2,298 against 2,302 (-4), but Mperm 2,259 against 2,295 and M 2,216 against 2,251.**
Of the 76 original tokens that main matches and A does not, 13 are reloads of the accounts pointer from `[r10-0x8d8]`
(`tools/hitdiff.py`). w16a04's `winrot.py` gives A a 7-slot window rotation (main 0): A's first spill slot, -0x8d8,
holds the original's 0x918 value, and the accounts pointer moves to -0x8e0.

The cause (`tools/ssw.py` on a debug llc trace): StackSlotColoring hands out colours in spill-weight order.
- On main the accounts slot (`fi#180`, weight 2.060) is the heaviest and takes the first colour (-0x8d8, as in the original).
- On A the heaviest slot is `fi#183` (2.454). It holds `hopt`, whose vreg becomes VC's **masked holder** in place
  (`%16 = COPY $r3; %16 = AND_ri %16, 1`, the closure's `and i8 %0,1`). That vreg is used by the two holder tests and by
  the curve store.
- The slot has two hot reloads at the head. One is the closure's `ldxdw r8,[hopt]; and64 r8,1` (A 0x5b8), which is exactly
  the original's 0x610. The other is the outer block's `and 253` for `cashback=!holder&&st.cashback` (A 0x470), which the
  original does not have.
- Main's `hopt` slot is the raw argument, reloaded once at the head (`and 253`) and once at the curve store (weight 2.004,
  third colour). The original masks its reloaded `hopt` once (0x610) and stores a per-arm constant flag (0x950, written
  with 1 / 0 in the validate arms) at the curve store.

Probes:
- IR, recomputing `and i8 %0,1` at A's curve store (`irp/A_hst`): slot 183 becomes the raw argument (2.003), but fi#260
  (2.384) takes the first colour. M 2,218, rot 6, Mhc 2,297.
- Source, `cbu` (outer cashback through `hopt.unwrap_or(false)`): GVN merges it into the masked value, the slot weight
  rises to 3.387, and M is 2,214 at 27,368 B.
- Source, `cbn` / `cbn2` (outer cashback through `new.is_some()`, semantically equal after validate): the outer `and -3`
  holder disappears, as intended, but A collapses (M 1,608, Mhc 1,638). The block layout swaps (TCF -487, the 6 KB tail
  swap of w16a12's h2p). Every source spelling that removes the outer holder i1 from A swaps the layout: cbn, cbn2,
  cbu+c0s (1,636) and vflag2 (section 5).

So on basin A the gap to main is a frame-colour artefact of VC's long-lived masked holder, worth about 36 M. No
back-half gene touches it, because the weight comes from the head's reloads.

## 5. The original's per-arm flags, as source on VC

The original stores `is_holder_reward` from a phi of per-arm constants (`[r10-0x950]` = 1 in the holder arm at 0x1130, 0
at 0xe40 / 0x14e0) and `is_cashback_coin` from `[r10-0x958]&1` (0 in the holder arm). New genes:

| gene | spelling | B (dM vs B) | A (dM vs A) |
| --- | --- | ---: | ---: |
| vflag2 | `let mut hflag=false;` set to `true` in the closure's holder arm; tuple `(hflag,..)`; store `_holder` | 2,132 (-7) | 1,616 (collapse) |
| vflag | the closure returns `Result<(Pubkey,bool)>` | 1,286 | 987 |
| vcb2 | `let mut cbf=false;` set from the closure's cashback; the outer cashback removed | 1,825 | 1,632 |
| vboth | vflag2 + vcb2 | 1,849 | 1,735 |

`vflag2` is the first source that keeps the original's flag phi: post-opt IR stores
`%hflag.sroa.0.1 = phi i8 [0,..],[..],[1,..]` and LLVM does not fold it back into `holder` (w16a12's h1b folded). On B it
is M-neutral (Mhc 2,248) with an unchanged pass-1 joint (2,333). On A it triggers the layout swap. `vflag`'s
`Result<(Pubkey,bool)>` moves the Pubkey to an 8-aligned offset (w16a12's `ft` frame artefact). The per-arm cashback
forms (`vcb2`, `vboth`) restructure validate's error blocks (nonholder -28, e306 -36, e312 -49, fee_chain -27).

## 6. Conditional-update idioms at the curve store (new; semantically equal, all lose)

`if let Some(h)=holder{curve.is_holder_reward=h;}` equals `holder.unwrap_or(false)`, because 289 forces
`is_holder_reward==false` whenever `holder!=Some(true)`. `if holder{curve.is_cashback_coin=false;}` equals
`cashback=!holder&&st.cashback`. Neither had been tried (no ledger rows). They lose everywhere: on main c0cs 2,244 (-7,
+16 B), c0cm 2,247 (-4), c0uc 2,245 (-6), and cbcs collapses (1,855). On VC: B_c0cs 2,038, A_c0cs 2,075. B_c0cs still has
Mhc 2,304, above main's 2,302: its code shape is intact and its frame collapsed. The original stores both flags
unconditionally (`stxb [r1+0xa5]` from `[r10-0x950]`, `stxb [r1+0xa3]` from `[r10-0x958]&1`), so these are not its idiom.

## 7. Joint RA ceilings and decisive forces (step 4)

`joint` = Mhc of the forced build (sticky RAPRIO forces + legal spill relabel), the same definition as w16a04 (#3855).

| cell | pass | forces | forced bytes | forced M | joint | main (w16a04) |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| B = Lsh | 1 | 11 | 27,216 | 2,255 | 2,337 | p1 2,328 (7 forces) |
| B = Lsh | 2 | 16 | 27,224 | 2,267 | **2,355** | p2 2,338 (9 forces) |
| A = Lsh_t1n | 1 | 6 | 27,224 | 2,233 | 2,312 | p1 2,328 |
| A = Lsh_t1n | 2 | 14 | 27,232 | 2,277 | **2,351** | p2 2,338 |
| B_vflag2 | 1 | 11 | 27,200 | 2,247 | 2,333 | |

Decisive forces (leave-one-out, `cm/*.loo.jsonl`; vreg ids on each module's pre-RA MIR):
- B: `1870=r6` (-80; root `%171 = LDB_V1 %163, 42`, the `executable` byte of a TCF AccountInfo clone), `1816=r5` (-48; root
  `%159 = LDD_V1 %154, 32`, a clone's `rent_epoch`), `1748=r0` (-32; root `%131`, a clone's data pointer), `1731=r3` (-21;
  root `%61 = MOV_ri 0`, a join constant), `215=r1` (-17; `a`+72), `1682=r6` (-11; the accounts pointer's tail piece).
  B's TCF loss is the TCF clone-run force family. Forcing only the sweep-head pieces to the original's registers
  (`1684=r8` accounts, `1734=r7` native) makes the TCF worse (-112 / -89).
- A: `1659=r9` (-69), the payload phi (the pointer half of the shared Err return, in r9 across the whole original; w14a82,
  w15a33). Then `1674=r7` (-11) and `1681=r6` (-8), the accounts pointer's pieces. Everything else is -6 or less.

IR probes on B that did not move it: the sweep gate as `skip` (the original's polarity) costs the wallet 13 (2,126); a
single `1684=r8` force gives TCF -242.

## 8. Kill test

- Best VC composite at 27,400 B: A + r59s + r30v, splice-priced and built at M 2,217 (section 2). That is -34, which fails
  the 10 M bar.
- Joint: at pass 1, A (2,312) is below main (2,328). At pass 2 both VC basins exceed main (B 2,355 and A 2,351 against
  2,338), with more forces (16 / 14 against 9). The decisive forces are lever-less families: the TCF clone temporaries
  and the payload phi.
- So the angle is closed as notes. VC's ceiling is real but needs RA forces with no source lever, and VC's at-size
  realisations stay 34 M below main because of the frame colour order (A) or the TCF clone rotation (B).

## Next ideas

1. **Frame colour on VC-A is the gap.** A source that keeps VC's single masked-holder reload (orig 0x610) but stops the
   outer block's `and 253` reload would leave the `hopt` slot with one hot reload, as in the original. That needs the outer
   `cashback` without the outer `holder` i1 and without A's layout swap. `cbn` removes the i1 but swaps the layout, and
   `cbu` merges into the masked value. A lane could look for the cause of the swap (block frequencies after the cashback
   select changes) and pair `cbn` with a layout repay.
2. A's code shape is above main with the TCF literal genes (`c2`, `tai_tv` Mhc 2,305; `s_tai2` 2,303). If item 1 fixes
   the colour order, these are the first genes to add.
3. `vflag2` reproduces the original's per-arm holder flag phi on VC without collapsing B. It is a faithful head piece
   for any lane that can get B's TCF out of its rotation.
