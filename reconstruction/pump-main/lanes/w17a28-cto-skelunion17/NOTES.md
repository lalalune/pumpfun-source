# w17a28-cto-skelunion17: the wave-17 structural leads stacked into one union (skeleton against naming)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main 53ec7fb53 (0.68754, 3,096 slots, M 2,295 at 27,400 B). Bound and strategy lane, not an integrator.
Ledger: approach `skelunion17`, keys `0x22a10-w17-53ec7fb-skelunion17-<cell>-v1`.

**Result: notes only, no source change.** Every union step is below main in exact M (best 2,163 true LCS against main's 2,300).
The answer to the lane's question:

- **The naming loss is not a fixed tax per lead.** The taxes are strongly sub-additive. The union pays one basin-switch
  cost, when the entry changes (K8, PDA first). After that, s_nat1+MV58, ve1n, fo and S3n add skeleton at zero or
  negative net naming cost. ve1n repays 133 tokens and S3n 9.
- **Register naming converges, and frame naming does not.** With registers masked, the union's naming loss
  (`r` LCS minus exact LCS) falls from 564 (K8) back to 333 by step 5. Main's is 331. The frame share (`f` minus exact)
  rises from 203 on main to 340, because each lead adds or reshapes allocas.
- **The residual loss is mostly spill colouring.** At step 5 the naming loss is 179 tokens above main's. The frame share
  accounts for 137 of them (`f` minus exact: 340 against 203), the jumps for 16 and the registers for 2. A legal
  spill-slot relabel recovers +170 (Mperm) to +205 (Mhc) tokens at step 5. On main the same relabel recovers only +26
  to +34.
- **The +40 trigger is not met, so this lane writes no realisation plan.**
  - Main's re-measured RA-only climb is 2,316 at 27,392 B (2,313 at 27,400). On a51791e it was 2,306.
  - The best union climb is K8+NAT at 2,330 (+14 over main), with 29 sticky forces and 56 B short of 27,400.
  - At exactly 27,400 B the best union climb is 2,312 (step 4), against main's 2,313.
  - The joint bound (RA forces plus a legal spill relabel, Mhc) is main 2,347. K8+NAT reaches 2,384 (+37), and the bound
    falls back to 2,347 by step 5. The later leads add skeleton but not ceiling.

**Decision for the replanner.** Do not move the swarm to a union basin on the strength of RA forcing. The union's register
naming is already at main's level, so further RA shims buy little there. The only lever with headroom in the union is frame
naming: spill colouring and alloca hosts, worth +170 to +205 tokens on step 5. A union lane is worth running only as a
frame lane, using the w17a04/w17a08 spill-weight shims, w17a14's host map and w17a19's lifetime markers on the step-5
source. Until such a lane shows its frame fix, local shims on main remain the productive track.

## 1. Method

- **Oracle.** w17a06's slim pre-opt oracle (`capraw` + `preslim` + `fx`). w17a21's copies of it are in this lane's
  `$OUT/tools`. On main it reproduces the baseline window exactly (`eq_main`, M 2,295 at 27,400 B, signature `61dcfe87f489`).
- **Genes.** `tools/genes.py` holds every lead as an exact, line-count-preserving source edit on main 53ec7fb53.
  `tools/capu.py` applies a `+`-joined combination of genes in a fixed canonical order and captures it. Each capture
  takes about 40-90 s and one build slot.
- **MV58.** Every cell that contains s_nat1 gets w17a21's MV58 post-opt block move (`pipe.MV58`) before `llc`. No source
  form of it is known (w17a21 section 3), so it is an IR-only gene.
- **Metrics** (`tools/step.py`, `tools/tab.py`):
  - `M` is the scorer's difflib count.
  - `LCS none/r/f/rf/rfj` is w17a14's `rc.py` true LCS, with registers, frame offsets and jump offsets masked in turn.
    "Skeleton" means `rfj`.
  - `m3` is w17a21's `skel.py` difflib count with the same three masks, a skeleton measure on the scorer's own alignment.
  - `Mperm/Mhc` is w17a06's `mp.py`: the best legal spill-slot relabel, then the vote climb.
  - "climb (1 pass)" is w17a21's `climb.py`: a greedy sticky RAPRIO climb over the top-40 vote genes, with the private
    llc. Union steps ran 12 rounds and singles 8.
  - "re-vote climb" (`tools/climb2.py`) continues from those forces. It re-tags and re-votes under the current forces
    each epoch, until an epoch adds nothing.
  - "joint" (`mpp.py` = `mp.py` with the private llc) is Mperm/Mhc of the re-vote climb's forced allocation. It is the
    stacked RA plus spill ceiling.
- **Greedy.** At each step, add every remaining lead to the current union, keep the one with the largest `rfj` gain, and
  stop when no lead raises `rfj`.

Genes (source in `tools/genes.py`):

| gene | lead | form |
| --- | --- | --- |
| K8 | w17a09/w17a20/w17a25 PDA-first | statement reorder: the `hkx` PDA block before `let shared=` |
| NAT | w17a21 s_nat1 | native tail `if amount>0{..?;transfer_native(..)?;}Ok(amount)` (+MV58 in IR) |
| N1 | w17a13 m2n (w17a21 n1) | the event reads `creator_fee_bps` directly (no `nf` local) |
| VE | w17a20 ve1n (`sh1h2`), ported | `g=&a.global`, early curve flags, `MaybeUninit<CtoState>` with the original's store order (7 `write_volatile`), w17a19's `lts` kept before the creator copy |
| S3 | w16a08 S3n, ported | per-arm holder flag out-param `hf` |
| FO / FOp | w16a24 fo (+ w17a15 a1 passthrough on the tag) | validated-fee out-param `fo`. FOp adds `pt64` on the tag word |
| OL / OLb | w17a16 outline core V (tf_g3 + 306 None 3:1 + crl3 + threaded head Dx49) / outline only | as in w17a16 g16.py |
| HL / HL2 | w17a20 holder-late, source form | holder/cashback after validate; HL2 also moves validate's `holder` after the mayhem test |

## 2. Singles on main 53ec7fb53

| cell | M @ bytes | LCS none | r | f | rf | rfj | rfj-none | m3 | Mperm / Mhc | climb (1 pass) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| main | 2,295 @27,400 | 2,300 | 2,631 | 2,503 | 2,888 | 3,000 | 700 | 2,804 | 2,321 / 2,329 | 2,316 @27,392 (4) |
| K8 | 1,961 @27,400 | 2,005 | 2,569 | 2,242 | 2,889 | **3,017** | 1,012 | 2,863 | 2,049 / 2,050 | 2,159 @27,424 (8) |
| NAT +MV58 | 2,121 @27,384 | 2,180 | 2,559 | 2,427 | 2,867 | 3,003 | 823 | 2,858 | 2,205 / 2,234 | 2,234 @27,488 (8) |
| N1 | 2,284 @27,376 | 2,289 | 2,628 | 2,493 | 2,884 | 3,000 | 711 | 2,804 | 2,310 / 2,318 | - |
| VE | 2,154 @27,328 | 2,171 | 2,559 | 2,431 | 2,869 | 2,997 | 826 | 2,869 | 2,234 / 2,237 | 2,246 @27,232 (8) |
| S3 | 2,055 @27,416 | 2,147 | 2,441 | 2,495 | 2,883 | 3,003 | 856 | 2,809 | 2,313 / 2,320 | 2,125 @27,368 (7) |
| FO | 2,280 @27,440 | 2,289 | 2,634 | 2,497 | 2,890 | 3,002 | 713 | 2,809 | 2,315 / 2,317 | - |
| FOp | 1,873 @27,392 | 1,944 | 2,373 | 2,188 | 2,760 | 2,889 | 945 | 2,680 | 1,979 / 1,985 | - |
| OL | 2,279 @27,208 | 2,293 | 2,631 | 2,485 | 2,877 | 2,994 | 701 | 2,851 | 2,308 / 2,316 | 2,311 @27,208 (4) |
| OLb | 2,257 @27,120 | 2,272 | 2,609 | 2,463 | 2,855 | 2,968 | 696 | 2,779 | 2,283 / 2,291 | - |
| HL | 1,860 @27,232 | 1,961 | 2,404 | 2,343 | 2,856 | 2,990 | 1,029 | 2,851 | 2,124 / 2,140 | 2,121 @27,296 (8) |

- On the true LCS, only K8 is a clear skeleton gain alone (+17).
- The difflib skeleton `m3` credits more: VE +65, K8 +59, NAT +54, OL +47 and HL +47. Those gains are mostly the
  scorer's alignment (block order), not new matched structure.
- On main the fo passthrough (FOp) moves the tail block layout (TL -107 rfj). Plain FO is neutral there.

## 3. Greedy union

Each row gives the change in true-LCS `rfj` and in exact LCS against the current union.

| step | base | candidates: Δrfj / Δexact | kept |
| --- | --- | --- | --- |
| 1 | main | K8 +17/-295, NAT +3/-120, S3 +3/-153, FO +2/-11, N1 0/-11, VE -3/-129, OL -6/-7, HL -10/-339, FOp -111/-356 | K8 |
| 2 | K8 | NAT +9/0, VE +3/+75, N1 -2/+4, S3 -3/0, HL -3/-60, OL -12/-125 | NAT |
| 3 | K8+NAT | **VE +4/+137**, S3 -7/-7, N1 -9/-11, OL -22/-135, HL -389/-377 (tail layout collapses) | VE |
| 4 | K8+NAT+VE | FOp +8/+8 (FO: the same, M 2,036), N1 +6/+6, S3 +5/-66, OL -7/-202, HL2 -377/-340 | FOp |
| 5 | +FOp | **S3 +4/+13**, N1 -1/-1, OL -12/-145 | S3 |
| 6 | +S3 | N1 -1/-3, OL -11/-166 | stop |

The union table (all steps carry MV58 from step 2 on):

| step | M @ bytes | LCS none | r | f | rf | rfj | rfj-none | m3 | Mperm / Mhc | climb (1 pass) | re-vote climb (forces) | at 27,400 | joint Mhc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| main | 2,295 @27,400 | 2,300 | 2,631 | 2,503 | 2,888 | 3,000 | 700 | 2,804 | 2,321 / 2,329 | 2,316 @27,392 | 2,316 @27,392 (4) | 2,313 | 2,347 |
| 1 K8 | 1,961 @27,400 | 2,005 | 2,569 | 2,242 | 2,889 | 3,017 | 1,012 | 2,863 | 2,049 / 2,050 | 2,159 @27,424 | 2,186 @27,432 (16) | 2,110 | 2,275 |
| 2 +NAT | 1,933 @27,512 | 2,005 | 2,500 | 2,259 | 2,891 | 3,026 | 1,021 | 2,911 | 2,046 / 2,047 | 2,209 @27,440 | **2,330 @27,344 (29)** | 2,249 | **2,384** |
| 3 +VE | 2,062 @27,392 | 2,142 | 2,552 | 2,432 | 2,901 | 3,030 | 888 | 2,920 | 2,199 / 2,222 | 2,190 @27,312 | 2,296 @27,272 (20) | 2,120 | 2,378 |
| 4 +FOp | 2,036 @27,384 | 2,150 | 2,490 | 2,493 | 2,908 | 3,038 | 888 | 2,930 | 2,273 / 2,287 | 2,300 @27,400 | 2,316 @27,408 (17) | **2,312** | 2,373 |
| 5 +S3 | 2,079 @27,440 | 2,163 | 2,496 | 2,503 | 2,914 | **3,042** | 879 | 2,942 | 2,249 / 2,284 | 2,280 @27,344 | 2,290 @27,352 (14) | - | 2,347 |
| (6) +OL | 1,821 @27,256 | 1,997 | 2,314 | 2,483 | 2,900 | 3,031 | 1,034 | 2,986 | 2,047 / 2,099 | 1,967 @27,320 | 2,010 @27,312 (18) | 1,994 | 2,265 |

## 4. The convergence question

**Taxes are not additive.** A lead's naming tax is its skeleton gain minus its exact gain (Δrfj - Δexact).

| lead | alone on main | added to the union |
| --- | ---: | ---: |
| K8 | 312 | 312 (step 1) |
| NAT +MV58 | 123 | 9 |
| VE | 126 | **-133** |
| FO / FOp | 13 / 245 | 0 / 0 |
| S3 | 156 | **-9** |
| N1 | 11 | 2 (step 6) |
| OL | 1 | 155 (step 6) |

The five union genes cost 730 alone (with FO). If the taxes were fixed per lead, the union's exact LCS would be
2,300 + 42 - 730 = 1,612. It is 2,163. The cost is a basin switch, paid once when the entry changes. In T1, K8 alone
loses 234 exact tokens (accounts in r6, the clone-run scratch registers renamed, w17a14/w17a25). VE gives back 176 of
them, because ve1n's entry plus PDA-first is closer to the original's entry allocation than PDA-first alone.

**Where the naming loss sits** (true LCS differences between masks):

| step | r-none (register naming) | f-none (frame naming) | rf-none | rfj-rf (jumps) | rfj-none (total) |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 331 | 203 | 588 | 112 | 700 |
| 1 K8 | 564 | 237 | 884 | 128 | 1,012 |
| 2 +NAT | 495 | 254 | 886 | 135 | 1,021 |
| 3 +VE | 410 | 290 | 759 | 129 | 888 |
| 4 +FOp | 340 | 343 | 758 | 130 | 888 |
| 5 +S3 | **333** | **340** | 751 | 128 | 879 |

The register share returns to main's level as the skeleton grows (564 to 333; main 331). The frame share grows
(203 to 340), because VE (a `MaybeUninit<CtoState>`), FO (an out-param) and S3 (an out-param) each add or reshape
allocas. Per region, T1 exact runs 491 (main), 257, 242, 418, 357 and 354. C1 runs 234, 186, 215, 207, 205 and 217.
E1 is +22 from K8 on (57/73 against main's 35/48), and EV +22 and TL +7 at step 5. Step 5's exact loss against main is
-137 LCS: T1 -137, C1 -17, W2 -15, S1 -9, partly offset by E1 +22 and EV +22.

**Spill colouring is the recoverable part.** Mperm - M is +170 at step 5 against +26 on main, and Mhc - M is +205
against +34. The union's frame loss is mostly which spill colour each interval gets, which StackSlotColoring
sets (w17a04/w17a08). Alloca host placement is a smaller share.

**Ceilings.** The RA-only climb and the joint bound peak at step 2, K8+NAT: 2,330 (+14) and 2,384 (+37). After that
the joint bound falls at every step (2,378, 2,373, 2,347), and the RA-only climb stays at or below step 2's (2,296,
2,316, 2,290). This happens although VE, FOp and S3 raise the exact M (1,933 to 2,079) and the skeleton (+16 rfj). So
the later leads raise the floor and lower the ceiling. Their exact gain is naming the climb would have found anyway.

The climbed cells also drift in size. Only step 4 climbs at exactly 27,400 B, to 2,312, against main's 2,313.

**K8 is what makes the other leads cheap.** The same leads without K8 keep their taxes (MV58 on every NAT cell):

| cell | M @ bytes | exact LCS | rfj | rfj-none | m3 | Mperm / Mhc |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| NAT | 2,121 @27,384 | 2,180 | 3,003 | 823 | 2,858 | 2,205 / 2,234 |
| NAT+VE | 1,982 @27,440 | 2,051 | 3,013 | 962 | 2,876 | 2,164 / 2,194 |
| NAT+VE+FO | 2,103 @27,280 | 2,150 | 3,000 | 850 | 2,866 | 2,158 / 2,164 |
| NAT+VE+FO+S3 | 1,889 @27,384 | 2,037 | 3,021 | 984 | 2,888 | 2,168 / 2,183 |
| VE+FO+S3 (no NAT) | 1,949 @27,440 | 2,042 | 3,005 | 963 | 2,871 | 2,151 / 2,169 |
| K8+NAT+VE+FOp+S3 (step 5) | 2,079 @27,440 | 2,163 | **3,042** | 879 | 2,942 | 2,249 / 2,284 |

Without K8, VE costs 129 exact tokens on NAT (T1 -142 against main), and VE+FO+S3 still loses 173 in T1. With K8 the same
genes give T1 back. ve1n's E2/E3 store order and the per-arm flags are tuned to the PDA-first entry, as the original
has them. The union basin is the K8 basin, and its skeleton is also 21 rfj higher than the K8-free one.

Single-lead ceilings (re-vote climb from the 1-pass forces, joint Mhc): NAT 2,312 @27,448 (12 forces), joint
**2,376**; VE 2,270 @27,248, joint 2,343; K8 2,186 @27,432, joint 2,275. So most of K8+NAT's ceiling (joint 2,384)
already comes from NAT's sweep-exit shape (2,376). K8 adds the skeleton, and its ceiling share is only +8.

## 5. Notes for the next union lane

- FO = FOp on the union (M 2,036 at 27,384 B both, LCS within 1 token), so the fo out-param needs no passthrough
  there. Use plain FO; it is ordinary Rust. On main, FOp collapses the tail (TL -107) and FO is neutral.
- HL/HL2 (holder late) break the MV58 tail layout once NAT is in (TL -127, S2 -56, W2 -208 rfj). Without NAT,
  K8+VE+HL2 is rfj +3 against K8+VE. The source form is not w17a20's IR hl2: the original computes `holder`
  after the mayhem test inside validate, and HL2 does that too, but the CSE with execute's copy is not controlled.
- OL raises difflib `m3` by +44 to +55 at every step, but lowers the true LCS (V2 -36 against V4 +20) and the exact
  M by 135 to 202 on the union. Its climb ends far below (1,967 in one pass, 2,010 re-voted, joint 2,265). It is an alignment gain, not structure.
- The step-5 source is `$OUT/src/K8_NAT_VE_FOp_S3.rs` (`capu.py <name> <slot> K8+NAT+VE+FOp+S3`). It needs MV58,
  which has no source form yet (w17a21 section 3). It is 40 B over 27,400 at M 2,079.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `genes.py`: every lead as exact single-occurrence edits on main 53ec7fb53's `admin_cto.rs`, line count kept.
- `capu.py <name> <slot> <G+G+..>` / `batchu.sh <out.jsonl> name=COMBO ..`: crate copy, genes applied in canonical
  order, capraw, preslim, fx (two captures at a time in `work1`/`work2`).
- `step.py <name> [--mv58] [--noclimb] [--R n]`: MV58 if asked, sdk llc M, `mp.py` Mperm/Mhc, RAPRIO tagged asm and
  votes, and the climb.
- `tab.py name=fn.bin ..`: true-LCS region tables at the none/r/f/rf/rfj masks (`rc.py` underneath), in parallel.
- `climb2.py <m.ll> <out.jsonl> --init <forces>`: re-voting greedy sticky climb (re-tag, re-vote, greedy, per epoch).
  `joint.sh <name>` runs `mpp.py` (= `mp.py` on the private llc) on the climb's forces. `c2q.sh`/`climbq*.sh` are
  queues, and `addc2.py` folds the results into `st/<name>/step.json`.
- `rec.py <tab.jsonl> name:label ..`: the union table, and ledger rows with `--ledger`.
- `data/`: the per-cell step files, the climb logs and the region tables behind every number here.
