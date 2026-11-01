# w16a14-cto-vcretune: VC validate closure as the head, main's back half re-tuned under it (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto.rs identical to 1f4e396b5): 0.67436, 3,141 slots, M 2,251 (Mperm 2,295, Mhc 2,302).
Angle: w16a05-cto-skelsplice next idea 1 (#3869). Adopt VC (w15a03 `L_N3h` = `v7c+lv_ny+lv_le+lv_cf_skc+lv_h289`, the
le_vy1 validate closure) as the head and re-tune main's back half under it, instead of splicing main's back half on.
Ledger approach `vcretune`, keys `0x22a10-w16-1f4e396-vcretune-<cell>-v1` (one row per capture, written by `tools/vscr.py`).

**Status: in progress (first table).**

## Oracle (experiment only)

- `tools/vscr.py`: w16a05's `scr.py` (w15a03 capraw identity build with pre-opt IR, SDK `opt -O3`, slim, SDK `llc`, exact
  M and the w16a05 per-region dM) with this lane's paths. `m0` reproduces main (`eq_main: true`, M 2,251).
- `tools/genes_vc.py`: w16a05 `genes_w16` + aliases `VC` (= L_N3h) and `VCsh` (VC + `lv_sh_ifelse`, w16a05 `Lsh`) + the
  pre-PR spellings of every back-half compensator landed since #3409 (`r30w r30v r37p r37n r80e r80o r95 r21 r21n r66
  r59s r59e`; each verified to reproduce the pre-PR source when applied to main) + the w16a04 additions (`c2 s1 tf_g1a g0
  po`) + conditional-update idioms at the curve store (`c0cs c0cm c0uc cbcs cbcs2`).
- `tools/mploop.sh` runs w15a16 `mp.py` (Mperm = best permutation of the build's own spill offsets, Mhc = vote swap climb on
  top) on every capture; `tools/tab.py` prints the table.
- `tools/vpipe2.sh`: w16a04 `lpipe.sh` core (colmap vote, single-force screen, greedy sticky climb with the w15a24 RAPRIO llc)
  plus the joint = Mhc of the forced build (`mpf.py` = `mp.py` with `MP_LLC=llcf.sh`, `tools/mpf.patch`). `vscreen.py` runs
  the force screen in threads (w16a04 `screen.py`'s process pool hung on two of 80 jobs).
- `tools/ssord.py` / `ssw.py`: spill-slot creation order and StackSlotColoring weight/colour order from a debug llc trace
  (`-debug-only=regalloc,stack-slot-coloring`, `~/.cache/pumpfun-reconstruction/llvm-dbg`; its output is byte-identical to
  the SDK llc).

## 1. Ports (step 1)

| cell | genes | bytes | M | dM | Mperm | Mhc |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m0 | main | 27,400 | 2,251 | 0 | 2,295 | 2,302 |
| B = Lsh | VCsh | 27,224 | 2,139 | -112 | 2,241 | 2,247 |
| A = Lsh_t1n | VCsh + t1n | 27,400 | 2,216 | -35 | 2,259 | 2,298 |

(w16a05's `LN3h_c0s_shie` 2,201 / 27,376 and `LN3h` 2,105 were already re-priced on 1f4e396; same source on 599891304.)
B is the "VC basin" (original wallet registers, TCF accounts pointer in r6); A is basin A (t1n moves it: main's TCF, wallet
-14). Region dM as w16a05.

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
| c0h / c0s (curve store from the tuple / `==Some(true)`) | #3409 | w16a05: 2,203 (basin A) | 27,376 | w16a05 T_c0s 2,202 | 27,392 |

No revert moves B's TCF out of its basin (TCF stays -122/-123 in every B cell) and none moves A by more than +1. In basin A
the compensators are inert: M stays 2,216 for 8 of 11 reverts. The only original-direction alternatives
(the event reading `is_holder_reward` late = r59e; the curve store reading VC's masked holder = B itself) are 0.

`r30v` (dropping the 334 `read_volatile` placeholder) is M-neutral on both VC bases (-8 B), as on main (vol334_back -1).

## 3. Conditional-update idioms at the curve store (new; semantically equal, all lose)

`if let Some(h)=holder{curve.is_holder_reward=h;}` is equal to `holder.unwrap_or(false)` because 289 forces
`is_holder_reward==false` whenever `holder!=Some(true)`, and `if holder{curve.is_cashback_coin=false;}` equals
`cashback=!holder&&st.cashback`. Never tried before (no ledger rows). They lose everywhere:
main c0cs 2,244 (-7, +16 B), c0cm 2,247 (-4), c0uc 2,245 (-6); cbcs collapses (1,855). On VC: B_c0cs 2,038 /
A_c0cs 2,075 (but B_c0cs Mhc 2,304 > main's 2,302: code shape intact, frame collapsed). The original stores both flags
unconditionally (`stxb [r1+0xa5]` from `[r10-0x950]`, `stxb [r1+0xa3]` from `[r10-0x958]&1`), so these are not its idiom.

## 4. Why basin A loses: the spill colour order, not the code (mechanism)

A's code is as good as main's: **Mhc 2,298 vs 2,302 (-4), but Mperm 2,259 vs 2,295 and M 2,216 vs 2,251.** Of the 76
original tokens main matches and A does not, 13 are reloads of the accounts pointer from `[r10-0x8d8]` (`tools/hitdiff.py`);
w16a04's `winrot.py` gives A a 7-slot window rotation (main 0): A's first spill slot `-0x8d8` holds the original's 0x918
value, the accounts pointer moves to -0x8e0.

Cause (`tools/ssw.py` on a debug llc trace): StackSlotColoring hands out colours in spill-weight order. On main the accounts
slot (`fi#180`, weight 2.060) is the heaviest and takes the first colour (-0x8d8, as in the original). On A the heaviest
slot is `fi#183` (weight 2.454), which holds VC's **masked holder** (`%16 = AND_ri %16, 1`, the closure's `and i8 %0,1`,
spilled at its def and reloaded at the curve store and at the sweep's native-arm exits). The original never spills a
masked holder: it masks the reloaded raw argument (`ldxdw r8,[r10-0x918]; and64 r8,1` at orig 0x610) and stores a
per-arm constant flag (0x950, written with 1 / 0 in the validate arms) at the curve store. Main's slot 183 is the raw
argument (weight 2.004, third colour). An IR probe that recomputes `and i8 %0,1` at A's curve store (`irp/A_hst`) frees
slot 183 but another slot (fi#260, 2.384) takes the first colour: M 2,218, rot 6.

So on basin A the gap to main is a frame-colour artefact of the long-lived masked holder, worth about 36 M.

## 5. Joint RA ceilings (step 4)

| cell | forces | forced bytes | forced M | joint (forced Mhc) | main p1 / p2 (w16a04 #3855) |
| --- | ---: | ---: | ---: | ---: | --- |
| B = Lsh | 11 (`1816=r5,1870=r6,215=r1,1682=r6,1748=r0,1731=r3,1663=r4,1714=r6,1707=r4,1275=r1,1703=r3`) | 27,216 | 2,255 | **2,337** | 2,328 / 2,338 |

B's TCF loss is a sticky local rotation: four forces inside the TCF clone runs (1816, 1870, 215, 1682) take B from
0.64292 to 0.67258. B's pass-1 joint (2,337) is above main's pass 1 (2,328) and level with main's pass 2 (2,338).
