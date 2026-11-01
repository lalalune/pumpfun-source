# w16a20-cto-s3flagcolour: colour of S3's per-arm holder-flag spill slot (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 599891304
(admin_cto.rs as on 1f4e396b5): 0.67436, M 2,251, 3,140 slots at 27,400 B. Continues w16a08-cto-basinbound (#3876) next
ideas 1 and 3 and w15a08-cto-holderflagjoint (#3653) next idea 2. Ledger: approach `s3flagcolour`, keys
`0x22a10-w16-5998913-s3flagcolour-<cell>-v1`.

**Result: notes only, no source change (KILL).** No ordinary source form moves S3's flag slot. Every S3 form that keeps
main's layout spills the flag once, at the validate exit merge `bb75`, with weight 0.0430. The slot then shares colour k5
(`-2304`) and pushes the clone-run spills one colour down. Even the oracle-best colour for the flag (deepest) gives raw M
2,244 at 27,416 B, which is below main's 2,251 before the 16 B repay. The original's slot (`-2384`) cannot be reached by
weight at all. One by-product is worth handing on: **`Fdec`**, an S3 base that is 48 B smaller and has better code. See
section 5.

## 1. Tool: one private llc with the RAPRIO, SSC-weight and SSC-segment hooks

`sscpatch/build2.sh` copies w15a24's RAPRIO build directory (`lanes/w15a24-cto-raforce3/llvmb`: sticky forces and vreg
tags). It applies w15a32's `SSC_WSET` hook (`sscpatch/apply.py`), recompiles StackSlotColoring.cpp, re-archives
libLLVMCodeGen and relinks bin/llc. It takes about 2 minutes. `sscpatch/segb_hook.diff` adds two more hooks to the same TU.
They change only the overlap test of the colouring:
- `SSC_SEGB="ss:A:B"` adds `[start(bb.A), end(bb.B))` to spill interval SS#ss.
- `SSC_SEGU="ss:o"` adds the segments of SS#o to SS#ss.

With no environment variables set, the llc reproduces main and S3n byte for byte (M 2,251 and 1,990). RAPRIO_FORCE and
SSC_* combine in one run.

- `tools/flagcol.py <m.ll> <tag> <ss,..> [SPEC..]`: per SSC_WSET spec, prints M/ratio/bytes, the colour count and each
  watched interval's weight rank, colour fi and final offset (colour k sits at `-2264-8k`).
- `tools/fl.py <name> [--ir base.ll edits.py]`: the one-shot flag screen. It finds the flag slot as the `LDD %stack.N`
  that feeds the `STB ..,165` curve store and runs flagcol natural, deepest (5e-4), 0.01 and 0.2. It writes
  `rx/<name>/{fl.json,fn.bin,f.o,pei.mir,pressc.mir}`.
- `tools/flforce2.py <m.ll> <force> [w..]`: the same under `RAPRIO_FORCE` (sticky), with objects through w16a08's `llcw.py`
  join-restore, as w16a08's forced pipeline does.
- `tools/fdelta.py <m.ll> <force|-> <out.jsonl> [N] [deltas]`: single weight deltas on the N heaviest intervals, forced and
  restored (the w15a32 deltamap under forces).
- `tools/sscprep.sh <name>` writes the pre-SSC MIR, PEI MIR and SSC debug log that w15a32's `sstab.py` needs.
  `tools/slotmap.py` gives the per-offset k, ref count, first/last access and stores of any fn.bin or the original.

## 2. Where S3n's flag goes, and why (`data/sstab-m0n-S3n.txt`, `data/flagweight-S3n.jsonl`)

- The flag interval is SS#187. It is one store `STD $r2` at the top of `bb75` (the validate Ok merge; IR block frequency
  0.03901) and one reload at the curve store `bb37` (0.00394), so its weight is 0.04296, rank 17 of 182.
- At rank 17 the first colour free over `[17696B, 64640B)` is fi#183 (k5, `-2304`), which holds SS#297 `[2896r,16480B)`.
  The flag takes it. The next interval, SS#188 (`&a.system_program`, w 0.03947, main's SS#187), then cannot use fi#183. It
  moves to fi#186, and the cascade runs through the 0.00789 clone-run batch: S3n needs 109 colours against main's 108.
  This is w16a08's "71 slots move by +8".
- Weight map (code fixed, exact colours):

| flag weight | flag colour | M @27,416 |
| --- | --- | ---: |
| >= 2.1 | k0 `-2264` | 1,978 |
| 0.1 - 1.5 | k1 `-2272` (sharing-tag colour, before SS#186) | 1,990 |
| 0.04 (natural 0.043) | k5 `-2304` | 1,990 |
| 0.015 - 0.03 | k8 `-2328` | 1,990 |
| 0.008 - 0.012 | k14 `-2376` | 2,039 |
| 0.006 - 0.0075 | k18/k19 | 2,039 |
| 0.0009 - 0.005 | k64 `-2776` | 2,177 |
| <= 0.0007 | k108 `-3128` (deepest) | **2,244** (0.67206) |

- **No weight gives `-2384`.** fi#193 (k15) is opened by SS#320 (w 0.3775, a CtoState byte spilled at validate entry).
  It is closed for the flag by SS#322 from the 0.00789 batch, which is processed in one block with the flag's neighbours.
- **Deepest needs w < 7.807e-4**, the weight of the clone-run batch. That is 55 times lighter than the `bb75` store alone.
  No form that spills on the main Ok path can reach it.
- Interval-extension oracle (`SSC_SEGB`, the original's spill at the phi leaves): when the flag interval starts inside
  validate (from bb.13/27/36/40/43), the flag opens k16 (`-2392`). From bb.47/52 it joins k15 = **`-2384`**, the
  original's slot, beside SS#320. M is 2,039-2,040 in both cases, because everything from k16 down still cascades.
  `-2384` is right only inside the original's whole colour structure (next section).
- Self-copies (`tools/selfcp.py`): the original has 3, all on the flag `-0x950` (0x1d48, 0x44c8, 0x5b30). Main and S3n
  have 4, all on the sharing tag `-0x8e0` (0x3100/3118, 0x3cd8/3cf0, 0x5940/5950, 0x5b18/5b28).

## 3. The original's spill colours (`data/slotmap-orig-main-S3n.txt`)

- The original has 115 spill offsets, main 114 and S3n 115. The original's k15 (`-0x950`, 26 refs) is the holder flag.
  Its k16 (`-0x958`) is the cashback flag (first store 0x0db8; stores 0x0db8, 0x1138, 0x1850, 0x18b8). Its k17 and below
  are clone-run spills, as in main.
- Main's k15 and k16 are validate-head spills instead: SS#320 (a CtoState byte) and SS#294/SS#284 (`[7752r,13408B)`).
  So the original's head colours hold the two flags, and ours hold two short validate spills. Our flag cannot take k15
  unless those two values stop opening colours. That needs the per-arm cashback flag as well; w16a21-cto-s3cashflag
  (#3888) killed that on S3: 27 forms, best stacked c20 2,291 < 2,347.
- The original's sharing tag is in k4 (`-0x8f8`). It is stored at 0x1838 (r0) and at 0x18d8 and 0x1980 (const 2), and
  reloaded into r6 next to every dead flag reload (0x1d30/0x1d48, 0x3c58/0x3c50, 0x4a90/0x4a98, 0x60e0/0x60e8).
- **The original's event re-reads the curve** (0x4fe0 `ldxb r5,[r3+0xa5]`), which is main's form. S3n's event carrier
  `holder.unwrap_or(false)` (0x4fc0 `ldxdw r1,[r10-0x8e8]; and64 r1,1`) is the unfaithful piece that keeps the layout.
  The faithful S3 (S4 + pool from the flag, w15a08 fl_c) collapses at bb56.i.

## 4. Source and IR forms screened (raw-IR oracle `capraw` + opt -O3 + llc; `tools/fl.py`)

Every row is S3n (w16a08 `e/S3n.py`) plus the change. Edit sets are in `e/`, generated by `tools/mk*.py`. IR edits on S3n's
post-opt module are in `ei/`.

| form | change | bytes | M | flag slot | M flag deepest | note |
| --- | --- | ---: | ---: | --- | ---: | --- |
| S3n | (w16a08) | 27,416 | 1,990 | k5 -2304, w .0430 | 2,244 | Mperm 2,289, Mhc 2,296 |
| Fu8 / Hopt / Hvcb / Htop | flag as u8 / as Option<bool> / validate cashback from `*hf` / `let mut hf` at the top | 27,416 | 1,990 | same | 2,244 | **byte-identical to S3n** |
| **Fdec** | post-validate decision `if shared{if hf{..` | **27,368** | 1,998 | k5 -2304, w .0430 | 2,244 | Mperm **2,293**, Mhc **2,300**; = IR I7 |
| Hmatch / Hdecvcb | decision as `match (shared,hf)` / Fdec + Hvcb | 27,368 | 1,998 | same | | byte-identical to Fdec |
| Hcsfirst | flag store first in the curve block | 27,416 | 1,989 | k5 | 2,243 | same bb37 reload block |
| Fend | one write `*hf=holder` before `Ok(target)` | 27,432 | 1,894 | k5 | 2,148 | |
| Fpool | `pargs=(target,_holder,fee)` (orig 0x4e20) | 27,440 | 1,858 | k5, w .0437 | 2,112 | = IR I1; w15a08 e1hpa layout break |
| Fdecpool | Fdec + Fpool | 27,392 | 1,864 | k5 | 2,110 | |
| Fev | event `is_holder_reward:_holder` | 27,512 | 1,724 | k2 -2280 (holder-arg colour, ncol 108) | | collapse; = IR I2, restored 2,041, Mperm 2,199 |
| Fboth / Fdecev | pool+event / Fdec+event from the flag | 27,496 / 27,416 | 1,700 / 1,621 | k2 | | collapse |
| Hdf | flag set in the decision arms, validate unchanged | 27,424 | 2,026 | none | | folds to a holder test at bb37 (no flag spill) |
| (w16a08) S3b / S3c | flag writes at arm heads / init true | 27,416 | 1,990 | | | byte-identical to S3n |
| Fnew / Fnewev | main + curve flag from `new.is_none()` (equal to holder on Ok paths) / plus S3n's event carrier | 27,512 / 27,272 | 1,702 / 1,913 | none | | collapse / re-layout |

- 19 source forms and 4 IR forms in all. The flag colour is unchanged (k5) in every form that keeps main's layout. The only forms that change it are the event
  carriers (Fev, Fboth, Fdecev). They free the holder argument's colour after validate, so the flag reuses k2 and the
  count drops to 108. They also lose the `%0` event carrier and collapse at bb56.i. Restored (`ares.py`), I2 has M 2,041
  and Mperm 2,199: the code itself is worse.
- The weight is set by the `bb75` store (0.0390 of 0.0430). Every form spills there, because the flag reaches `bb75` in a
  caller-saved register (r2) from the phi copies. Moving the store into the phi leaves would make it heavier (bb44.i alone
  is 0.0755).

## 5. Under the S3 RA forces (the s3sweptr9 basin)

`tools/flforce2.py` with w16a08's S3n force sets, restored through `llcw.py`:

| forces | natural M @bytes | flag lighter than SS#188 (w 0.0390) | flag w 0.008 | flag deepest |
| --- | --- | ---: | ---: | ---: |
| `1739=r9` | 2,175 @27,384 | | | 1,973 |
| `1739=r9,1847=r5` | 2,236 @27,368 | **2,247 (+11)** | 2,250 (+14) | 2,089 |
| p1 (7 forces) | 2,204 @27,320 | | | 1,958 |
| p2 (13 forces) | 2,273 @27,304 | 2,276 (+3) | 2,277 (+4) | 2,074 |

- Under the forces the flag's natural colour is close to right. Deepest costs 150-200 M, and the only flag lever is
  ordering it after SS#188 (`&a.system_program`), worth +3 to +14.
- That needs the flag lighter than 0.03947, which is the store at `bb75` (0.03901) without the curve-store reload. No
  form found removes the reload.
- Forced deltamap (`data/deltamap-S3n-force2.jsonl`, 2 forces, 30 heaviest intervals x {+1, +0.375, -0.375, =5e-4}):
  - the largest lever is any single 0.00789 clone-run spill (SS#279/300/231/249/321/263) sent deep: **+37 (2,273)**;
  - it does not add to the flag lever (2,273 with both);
  - next come SS#320/SS#232 +0.375: +7.
  - P2 deltamap: `data/deltamap-S3n-p2.jsonl` (section 5b).

### 5a. Fdec, a better S3 base for the RA basin

`Fdec` (`e/Fdec.py`) is S3n with the post-validate shared decision reading the flag: `if shared{if hf{..}else{..}}`. That
is ordinary Rust and the same value on every Ok path. It is 48 B smaller than S3n (27,368, 32 B under the pin), and its
code is better: Mperm 2,293 and Mhc 2,300 against S3n's 2,289 and 2,296. Its flag colour problem is the same (k5, deepest
2,244). w16a08's restore-aware RA pipeline (`t2/rpipe.sh`, `t2/rpass2.sh`) gives:

| build | bytes | M | Mperm | Mhc | RA pass 1: M (forces) @bytes / joint Mhc | RA pass 2: M (forces) @bytes / joint Mhc |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main m0n (w16a08) | 27,400 | 2,251 | 2,295 | 2,302 | 2,278 (7) / 2,329 | 2,283 (9) @27,376 / 2,339 |
| S3n (w16a08) | 27,416 | 1,990 | 2,289 | 2,296 | 2,204 (7) @27,320 / 2,308 | 2,273 (13) @27,304 / 2,347 |
| **Fdec** | 27,368 | 1,998 | 2,293 | 2,300 | 2,202 (5) @27,312 / 2,283 | **2,293 (11) @27,288 / 2,357** |

- Fdec's forces follow S3n's numbering, shifted by one vreg. Pass 1 is `1738=r9,1690=r6,1677=r7,1284=r2,2191=r6`. Pass 2
  adds `1846=r5,469=r2,1086=r5,237=r5,1712=r4,1708=r3`. The decisive pair is the same: payload in r9 and the sweep r5.
- With only the decisive pair (`tools/flforce2.py`): Fdec `1738=r9,1846=r5` gives 2,242 @27,328 (S3n: 2,236 @27,368), and
  2,248 with the flag lighter than SS#188. `1738=r9` alone gives 2,180 @27,344 (S3n 2,175 @27,384).
- Forced deltamap on Fdec (`data/deltamap-Fdec-force2.jsonl`, 2 forces): the best single weight levers are SS#232
  +0.375 (+8), the flag at 0.039 (+6) and SS#184 -0.375 (+5).
- So Fdec raises the S3 basin's stacked ceiling from 2,347 to **2,357** (+18 over main's 2,339). It is also 40 to 112 B
  smaller than the matching S3n builds, so the repay goes the other way: add faithful bytes instead of removing 16 B.

## 6. Handoff and next ideas

- To s3sweptr9 (w16a19): no source colour lever exists for the S3n flag. Once the r9 and r5 levers exist, the flag's
  colour lever is small (+3..+14, flag after SS#188). The larger forced lever is one clone-run spill sent deep (+37), and
  it is not the flag. Try `Fdec` as the S3 base: -48 B, and its forced pass reaches M 2,293 with 11 forces and a joint Mhc of 2,357 (S3n 2,347, main 2,339). Captures:
  `$C/lanes/w16a20-cto-s3flagcolour/rx/<form>/{m.ll,fn.bin,res.json,fl.json}`.
- The original's colour structure (holder flag k15, cashback flag k16, sharing tag k4, holder arg dead inside validate,
  event re-reading the curve) is one joint change, not a flag spelling. The faithful S3 (S4 + pool from the flag) first
  needs a non-collapsing layout at bb56.i (accounts pointer r5 live-in, w16a08 section 2).
