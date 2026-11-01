# w16a19-cto-s3sweptr9: the S3 post-sweep payload in r9 (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 / 1647da0f2 (admin_cto.rs as on 1f4e396b5): 0.67436, 3,141 slots, M 2,251 at 27,400 B.
Angle (handoff from w16a08-cto-basinbound #3876, NOTES sections 3-4, next idea 2): find an ordinary source lever that
puts S3's post-sweep Result payload (the swept value) in the original's r9 without the RA force `1739=r9`.
Wave-16 lane, died at the 02:30 UTC app restart and CONTINUED in wave 17 (shim track open for `admin_cto.rs`).
Ledger: approach `s3sweptr9`, keys `0x22a10-w16-5998913-s3sweptr9-*` (43 rows).

**Result: notes only, kill test met. No source form (ordinary or marked shim) puts the payload in r9 unforced, and no
screened cell beats S3n's Mhc of 2,296 or main's 0.67436 at 27,400 B.** The mechanism is mapped below. In every base a
heavier value holds r9 over the payload's range: the `!holder` phi on S3n, and `nf` plus clone temps on main. Freeing r9
does not hand it to the payload, because the payload is allocated as split pieces and its post-sweep piece is the
lightest range in that region.

## 1. Who holds r9, and why the payload loses (dbgocc chain on S3n)

`llc -debug-only=regalloc` replay on the private RAPRIO llc (`dbg/S3n.ra.txt`, `tools/dbgocc.py`), S3n on 5998913:

- The payload is phi `%1632` (weight 1.005e-06, size 13,440): defs are the `MOV 0` at the gate plus 13 sweep-exit
  reloads; its only use is the event store `[r10-0x218]` at slot 68000.
- At its first dequeue (seq 329) r6 holds the sharing tag `%58` (w 1.33e-06), r7 locals incl. `%1332` (w 1.84e-06),
  r8 the accounts pointer `%0` (w 1.47e-04), and **r9 holds `%467`** (w 3.36e-05, live 3216..64640, head to tail).
- `%467` is the `!holder` flag: `hopt==Some(true)` lowered to a phi of constants (`MOV_ri 1` / `MOV_ri 0` at 3216/3264)
  that stays live until the curve block, where `cashback = !holder & st.cashback` is sunk (`AND_rr %467,%468`,
  `AND_ri 1`, `STB +163`). In the post-opt IR it is `%cashback.sroa.0.0.off0 = and i1 %_0..i.not, %extract.t` at the head,
  with its only use `zext` + `store i8` at bb37.
- No free register and no eviction, so greedy splits the payload: `1738` r6, `1739`, `1740` r6, `1742` spilled to fi190
  (`[r10-0x970]`). `1739` (w 7.86e-06, around the sweep exits) has r3/r4/r5 free and takes r3 by allocation order
  `[r1 r2 r3 r4 r5 r0 r6 r7 r8 r9]`; r9 there holds `%1717`, a split child of the tag. No copy hint links `1739` to r9.
- Coalescer order (`tools/coalor.py`, w14a69's ideal-order oracle): SW (`%1632`) does not merge into RP (`%1664`).
  bb.359 (IR bb64, the post-sweep CPI Err join, degree 4) merges its phi `%1662` into RP first; bb.270 (IR bb87, the sweep
  `?` Err, degree 3) then fails on interference at `%1664:29@64528r`, exactly as w14a69 found on main 39eb377. Forcing the
  ideal order merges them, but the class then takes **r6** (it evicts the tag): S3n M 1,935 / Mhc 2,165, main 1,935 / 2,164.

On main the r9 occupant is different: `nf` (`let nf=a.bonding_curve.creator_fee_bps`) is loaded into r9 at 0x4b78 and
held across the pool CPI to the event store `stxdw [r10-0x220], r9` (0x4fd0), and the sharing CPI clone run uses r9 as
its temp (0x3e40-0x4218). The original reads the new fee at the event (`ldxdw r4,[r3+0x70]`, 0x4fd8) and its clone run
uses r6/r5 for the same temps, because r9 is the payload from the last sweep exit (0x3c40, `ldxdw r9,[r10-0x828]`) to the
event store (0x5030).

## 2. Freeing r9 does not give it to the payload

| base | change | bytes | ratio | M | payload exits / gate zero / event reg |
| --- | --- | ---: | ---: | ---: | --- |
| main m0n | | 27,400 | 0.67436 | 2,251 | r3 / r3 / reload r1 |
| n1 | `nf` dropped, event reads `a.bonding_curve.creator_fee_bps` (the original's read) | 27,376 | 0.67106 | 2,239 | r3 / r3 / r1 |
| S3n | w16a08 S3 | 27,416 | 0.59599 | 1,990 | r3 / r3 / r1 |
| S3n1 | S3 + n1 | 27,392 | 0.59416 | 1,983 | r3 / r3 / r1 |
| S3n + IR cbmem | cashback through a head stack slot (no `!holder` range) | 27,488 | 0.58472 | 1,955 | r3 / - / r1 |

- n1 frees r9 over the post-sweep region (pool_updated and clone temps take it instead) and the payload still exits in r3
  and is reloaded at the event. Forces on n1 (`cm2/n1.json` vreg ids): `1728=r9` (payload piece) 0.51438 (collapse,
  exits 939888), `1681=r6` (event accounts piece, w15a04's force) 0.67296 @27,392, `1728=r9,1657=r9` 0.67017 @27,256,
  `1728=r9,1681=r6,1657=r9` 0.67318 @27,256.
- On S3n, removing `%467` (cbmem) frees r9 head to tail, and the payload still takes r3.
- So the payload never competes for r9 as a whole range. In the original its post-sweep segment is one call-crossing range
  in the 4th callee-saved register; in ours it is split before r9 is ever free over that range, and its post-sweep piece
  (one reload, one store) is the lightest range there, so it is spilled.

## 3. Gate polarity: the only large raw lift on S3 needs a join restore

`ie/zerogate.py` gives the gate the original's polarity (`br skip -> join, else sweep`, as `jne r1,0,+0x3e4` at 0x1d40).
`s_okq` (`swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;`) is its source form (identical code).

| cell | bytes | ratio | M | note |
| --- | ---: | ---: | ---: | --- |
| S3n + zerogate, plain llc | 27,464 | 0.50090 | 1,674 | = `s_okq` raw |
| S3n + zerogate + bb56.i join-restore (`tools/ares.py`) | 27,360 | 0.64758 | 2,160 | Mperm 2,239 / Mhc 2,254 |
| main + zerogate (`ie/zerogate_m.py`), plain | 27,448 | 0.51242 | 1,712 | |
| main + zerogate + join-restore | 27,344 | 0.58839 | 1,962 | |

The restore removes one extra live-in at the post-sweep join bb56.i: a value in **r9** with 13 feeders (6 COPY, 5 LDD,
`MOV_ri 2`, `MOV_ri 0`, slot -2344), i.e. a tag phi carried across the join. The original reloads the tag after the join
(`ldxdw r6,[r10-0x8f8]` at 0x1d30 and 0x3c58). With the restore the payload still exits in r3. Even this best S3 cell is
below S3n's Mhc and main.

## 4. Shim-track checks (wave 17)

- **Branch weights** (`ie/bw.py`, `!prof` on one `br`; this is what w17a02's `llvm.expect.i1` extern produces):
  - gate `br %_552/_553` 1:2000 (sweep cold): S3n 0.43179 @27,536, main 0.43133 @27,520 (collapse; payload exits r8).
  - gate 2000:1 (sweep hot): S3n 0.58265 @27,376, main 0.57473 @27,360.
  - sweep.exit Ok/Err `br %570` 2000:1: = S3n; 1:2000: 0.59629 (+1 M). No weight moves the payload to r9.
- **Volatile pins** (`tools/vpay.py`, w17a03's `vscreen.py` plus the payload readout; one load made volatile = one
  `read_volatile` shim at that IR site), S3n lines 3389-6357 (post-validate to the end of `execute`): see section 6.
- No construct in the allowed list pins a register: BPF has no ABI copy hint into r9 (args r1-r5, return r0), and
  `asm!` stays forbidden. A shim can only change live ranges, weights or memory order, and sections 2-3 show that
  neither freeing r9 nor reweighting the gate hands r9 to the payload.

## 5. Source screen (kill test)

All forms are exact single-line replacements with the line count kept (`e/*.py`, regenerated by `e/mk.py` for the
first batch). Raw = capture + `opt -O3` + plain `llc` (`tools/rx.py`), the realisable number. Mperm/Mhc are the w16a08
spill-permutation bounds (`tools/permhc.py`, oracle only). Payload = sweep-exit reload registers / event store register.

| form | change (on S3n unless noted) | bytes | raw ratio | M | Mperm | Mhc | payload regs: exits / event |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m0n | main 599891304 (reference) | 27,400 | 0.67436 | 2,251 | 2,295 | 2,302 | 33333 / 111 |
| S3n | w16a08 S3 (reference) | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| s_if | `swept=if skip{0}else{sweep(..)?}` | 27,456 | 0.59225 | 1,979 | 2,063 | 2,073 | 33333 / 111 |
| s_ifn | `swept=if !skip{sweep(..)?}else{0}` | 27,456 | 0.59225 | 1,979 | 2,063 | 2,073 | 33333 / 111 |
| s_match | `swept=match skip{true=>0,false=>sweep(..)?}` | 27,456 | 0.59225 | 1,979 | 2,063 | 2,073 | 33333 / 111 |
| s_mut | `let mut swept=0; if !skip{swept=sweep(..)?;}` | 27,464 | 0.50090 | 1,674 | 1,760 | 1,760 | 333888 / 111 |
| s_okq | `swept=if skip{Ok(0)}else{sweep(..)}?` (original gate polarity) | 27,464 | 0.50090 | 1,674 | 1,760 | 1,760 | 333888 / 111 |
| s_uor | `(!skip).then(..).unwrap_or(Ok(0))?` | 26,784 | 0.57827 | 1,908 | 2,175 | 2,189 | 33333 / 111 |
| t_uod | `.transpose()?.unwrap_or_default()` | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| t_iflet | `if let Some(r)=(!skip).then(..){r?}else{0}` | 27,256 | 0.47702 | 1,588 | 1,841 | 1,850 | 73777 / 111 |
| t_match | `match (!skip).then(..){Some(r)=>r?,None=>0}` | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| t_split | `let r=(!skip).then(..).transpose(); swept=r?.unwrap_or(0)` | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| g_hf | gate from the flag: `if shared&&hf{sweep(..)?}else{0}` | 27,560 | 0.50777 | 1,700 | 1,802 | 1,814 | 33333 / 211 |
| t_hf | gate from the flag: `(shared&&hf).then(..).transpose()?.unwrap_or(0)` | 27,560 | 0.50777 | 1,700 | 1,802 | 1,814 | 33333 / 211 |
| b_arg | bump passed to `sweep` as its own `u8` argument | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| b_accts | `sweep(&AdminCto,&AdminCtoBumps,&holder_key)` instead of `&Context` | 27,144 | 0.55418 | 1,841 | 2,021 | 2,027 | 83888 / 111 |
| b_seed | `let bump=ctx.bumps.creator_vault` read at the vault-seed site | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| d_scope | vault-seed check in its own block | 27,456 | 0.48212 | 1,611 | 1,867 | 1,883 | 63666 / 116 |
| d_rev | seed check as `dest!=key` | 27,416 | 0.59539 | 1,988 | 2,287 | 2,294 | 33333 / 111 |
| r_chain | `Rent::get()?.minimum_balance(0)` (Rent `?` site) | 27,416 | 0.59599 | 1,990 | 2,289 | 2,296 | 33333 / 111 |
| r_flat | `let rent=Rent::get()?; let min=rent.minimum_balance(0)` | 27,384 | 0.51094 | 1,705 | 2,000 | 2,006 | 33331 / 111 |
| sd_if | s_if + d_scope | 27,488 | 0.45970 | 1,537 | 1,689 | 1,689 | 63611 / 161 |
| sd_okq | s_okq + d_scope | 27,488 | 0.51952 | 1,737 | 1,807 | 1,845 | 63666 / 116 |
| sd_mut | s_mut + d_scope | 27,488 | 0.51952 | 1,737 | 1,807 | 1,845 | 63666 / 116 |
| db_arg | d_scope + b_arg | 27,456 | 0.48212 | 1,611 | 1,867 | 1,883 | 63666 / 116 |
| S3n1 | S3 + n1 (event reads the new fee; frees r9 post-sweep) | 27,392 | 0.59416 | 1,983 | 2,282 | 2,289 | 33333 / 111 |
| S3n1if | S3n1 + s_if | 27,432 | 0.59012 | 1,971 | 2,055 | 2,065 | 33333 / 111 |
| S3n1okq | S3n1 + s_okq | 27,440 | 0.49693 | 1,660 | 1,756 | 1,756 | 333888 / 111 |
| S3n1po | S3n1 + owner-first pool gate | 27,432 | 0.55898 | 1,867 | 2,165 | 2,172 | 33333 / 111 |
| n1 | main + n1 | 27,376 | 0.67106 | 2,239 | 2,283 | 2,290 | 33333 / 111 |
| n1okq | main + n1 + s_okq | 27,424 | 0.50966 | 1,702 | 1,755 | 1,755 | 333888 / 111 |
| n1po | main + n1 + owner-first pool gate | 27,416 | 0.63492 | 2,120 | 2,163 | 2,170 | 33333 / 111 |
| mpo | main + owner-first pool gate | 27,440 | 0.63493 | 2,121 | 2,164 | 2,171 | 33333 / 111 |

31 forms. None gives an unforced payload in r9 and none has Mhc above S3n's 2,296 (best: `d_rev` 2,294, n1 2,290).
Byte for byte (`fn.bin` compared): `b_seed`, `t_uod`, `t_match`, `t_split`, `r_chain` and `b_arg` equal S3n;
`s_if` = `s_ifn` = `s_match`; `s_mut` = `s_okq`. So the bump spelling, the Rent `?` chain and the `then`/`transpose`
spellings are not levers at all, and every gate spelling that changes code puts the sharing tag across the post-sweep join
(section 3) or collapses the sweep layout (exits `333888`).

## 6. Volatile-pin screen on S3n

`tools/vpay.py` on `rx/S3n/m.ll`, lines 3389-6357 (post-validate to the end of `execute`), one load made volatile per
cell, which is exactly what one `read_volatile` shim at that IR site produces (`data/vpay-S3n-5998913.jsonl`):

- 421 pins, 0 errors. The payload exits in r3 in all 421; the event store reads it from r1 (417), r2 (3) or r1/r2 (1).
  **No pin puts the payload in r9.**
- Best M 2,043 @27,424 (lines 4671-4674, loads in the sweep's AccountInfo clone, +53 over S3n). At exactly 27,400 B:
  line 4579 0.61114 (M 2,040) and line 4581 0.61084 (M 2,039). All far below main's 2,251.
- A partial screen of n1 (116 of 445 loads, stopped because the machine load average was ~200;
  `data/vload-n1-partial-5998913.jsonl`) found four pins that move n1 to exactly 27,400 B without losing its ratio
  (lines 3989/4002 0.67106, 4056/4069 0.67016): a +24 B size lever on the faithful event form, nothing above n1.
- IR `hfmem` (`ie/hfmem.py`, the flag written and read through a volatile 8 B slot, the emulation of
  `write_volatile`/`read_volatile` on a local): 0.55068 @27,424, M 1,839, Mhc 2,185 (i8 and i64 slots identical). The
  slot becomes an alloca, and PEI places every alloca before every spill slot, so all spills move 8 B deeper (w16a20's
  sV1/sV2 source forms show the same).

## 7. IR edits from the handoff (step 2)

| edit (`ie/`) | bytes | ratio | M | Mperm / Mhc | payload |
| --- | ---: | ---: | ---: | --- | --- |
| bumpseed (bump load in the vault-seed block, undoing ArgumentPromotion's hoist) | 27,424 | 0.59979 | 2,003 | 2,223 / 2,223 | r3 |
| zerogate (original gate polarity), with join-restore | 27,360 | 0.64758 | 2,160 | 2,239 / 2,254 | r3 |
| cbmem (cashback via a head stack slot) | 27,488 | 0.58472 | 1,955 | 2,068 / 2,085 | r3 |
| ltA / ltC (drop `dest.i` lifetime.end in bb56.i: SW merges into RP) | 27,520 | 0.45344 | 1,517 | 1,743 | class r6 |
| ltB, ltD-ltH (other sweep-exit lifetime drops) | 27,408-27,416 | 0.246-0.596 | | | r3 |
| force `1739=r9` alone (reference) | 27,384 | 0.65178 | 2,175 | 2,249 / 2,271 | r9 exits, event r1 |

Only the RA force moves the payload, and alone it pays only on raw M (spill numbering); the stacked S3 ceiling stays the
w16a08 13-force joint (2,347).

## 8. What a landing would need (next ideas)

- r9 for the payload is the 4th callee-saved class over the post-sweep region: tag in r6, pool AccountInfo pointer in r7,
  pool_updated in r8 (w15a04 section 4), and a payload range that crosses the sharing and pool CPIs unsplit. That is a
  whole-region RA fact, and no source construct names a register. Lanes should treat `1739=r9` as a consequence of the
  r6/r7/r8 colours (w15a04 `358=r7`, `1681=r6`), not as a lever of its own.
- S3's binding blocker is still spill numbering (w16a08 section 4, w16a20): a one-slot relabel takes S3n's raw M from
  1,990 to 2,234. Without that, the payload colour cannot lift S3 above main.
- The gate-polarity cell (section 3) is the largest raw lift on S3 (+170 M), but only with the tag reloaded after the
  post-sweep join. A source spelling that re-derives `sharing_update`'s tag after the sweep (instead of carrying the phi
  across bb56.i) is untested and would be the next screen.
- w16a20's `Fdec` (S3 with the post-validate decision reading the flag, -48 B, Mhc 2,300, forced joint 2,357) keeps the
  same signature: its decisive forces are `1738=r9` (this payload) and `1846=r5`, and `1738=r9` alone gives 2,180 @27,344
  (w16a20 section 5a). So on Fdec too the payload is not in r9 unforced. This lane did not re-screen its forms on Fdec;
  `tools/cap.sh` takes `SRCB=<crate copy>` for that, and the S3-relative edits in `e/*.py` need re-basing first.
- The faithful event form `n1` frees r9 on main at -24 B and -0.0033; with w15a04's `1681=r6` colour it reaches 0.67296
  @27,392, still below main. Four single volatile pins move n1 to exactly 27,400 B at its ratio (section 6), so the size
  side is cheap there; the colour side has no lever.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `cap.sh` / `capq.sh` / `capraw.py`: raw-IR capture of a source variant (build slot), then `rx.py` (opt + llc).
- `ire.py <name> [edits] --base <m.ll> [--force F] [--perm] [--no-ares]`: post-opt IR edits, RAPRIO llc, payload
  registers (`exits`, `zero`, `ev218`), Mperm/Mhc. `evn.sh` prices captured forms with it.
- `vpay.py`: volatile-pin screen with the payload readout. `ie/bw.py`: branch-weight oracle.
- `dbgocc.py`, `coal.py`, `coalor.py`, `payreg.py`: RA replay, coalescer merge check, ideal-order coalescer oracle.
- `llcw.py` + `ares.py`: the bb56.i join-restore wrapper (oracle only, never a proposal).
