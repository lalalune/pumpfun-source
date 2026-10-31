# w14a125-cto-outlinecollapse: the "outline-pattern" holder spellings do not outline (admin_cto::execute, 0x22a10)

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387e1 (0.67316, M 2,247, 3,123 slots). The raw-IR capture + `opt -O3` + `llc` oracle (w14a108 `cv.sh`/`rx.py`)
reproduces main exactly (`eq_main: true`).
Ledger: approach `outlinecollapse`, keys `0x22a10-w14-ebe5387-outlinecollapse-*-v1` (14 rows).

**Result: no source change. The angle is dead.** Its premise is wrong. The four validate holder spellings do not reproduce
the original's 307/312 to_string outline pattern in the real `-O3` pipeline. They are the and-1 basin with main's outline set.

## 1. bfi.py's COLD prediction is a light-pipeline artifact

w14a108's `bfi.py` runs `sroa,early-cse,simplifycfg,instcombine,simplifycfg` on validate and reads the BFI. For
`hopt.unwrap_or(false)`, `matches!(hopt,Some(true))`, `hopt.unwrap_or_default()` and `hopt.is_some_and(|h|h)`, it reports
307 at 0.0176 and 312 at 0.0179, both COLD. The real pipeline gives a different answer:

- **`tools/inl.py`** reads the post-`-O3` IR of execute. For every `error!` line it reports I (to_string inlined) or O (outlined
  call). The ground truth on the deployed program comes from the call-target multiset: the original has 7 calls to the
  outlined to_string (0xa938) and main has 5. The original outlines 307 312 330 334 338 660 719 and inlines 326.

| form | 284 289 296 298 306 | **307 312** | 326 | 330 334 338 | 660 719 |
| --- | --- | --- | --- | --- | --- |
| original | I | **O O** | I | O | O |
| main ebe5387 | I | I I | I | O | O |
| v_uo / v_mt / v_ud / v_isa (byte-identical) | I | **I I** | I | O | O |
| every step-(b) row below | I | I I | I or O | O | O |

- The inliner remarks (`-pass-remarks=inline`) agree. In validate, main and v_uo each inline 7 to_string calls and refuse 4
  (326 330 334 338). In execute, the inliner decides those 4 again: 326 is inlined there.
- **`tools/vbfi.py`** prints the real BFI of validate's fully simplified body, which is the body that gets inlined into execute.
  On main, 307 and 312 are 0.0124 and 0.0126 there, but they were already inlined in validate's own CGSCC inline pass. On v_uo,
  they are 0.0337 and 0.0342: hotter than on main.
- So the and-1 spellings do not make 307/312 colder where it matters. To outline a site, its call must be cold at the moment
  validate's inliner visits it. By then the earlier callees (Option `eq`, `unwrap_or`, `PumpError::name` and others) are
  already inlined, so the light pipeline's BFI does not apply. **Screen outline forms with `inl.py` on the rx output, not
  with `bfi.py`.**

## 2. Collapse decomposition on ebe5387 (`tools/decomp.py`)

- M is the scorer-matched tokens. fR, rfR and rfjR are w14a87 `fbound.py` legal-frame bounds: frame remapped, then registers
  masked, then jumps masked as well.
- J is the validate-exit join flip. `tools/jfix3.py` is `jfix2.py` with any `%bb5.iN` end name; it moves the arm chain back in
  front of `%bb56.i` after RA.

| form | bytes | M | fR | rfR | rfjR | J moved | relaid M | relaid fR | relaid rfR | relaid rfjR | 307/312 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | 2,247 | 2,295 | 2,623 | 2,622 | 0 | = | = | = | = | I I |
| v_uo class (4 spellings, plus `c_tup`, `c_ifl`, `c_m3`, `c_m3n`) | 27,416 | 1,373 | 1,568 | 1,939 | 2,051 | 119 | 1,620 | 2,043 | 2,415 | 2,588 | I I |
| c_vb: validate takes `holder:bool` (execute `==Some(true)`), 289 `!holder` | 27,400 | 2,233 | 2,281 | 2,609 | **2,695** | 0 | | | | | I I |
| c_vbu: c_vb plus execute `hopt.unwrap_or(false)` | 27,232 | 1,814 | 2,084 | 2,513 | 2,645 | 0 | | | | | I I |
| c_mh: `let holder=hopt.unwrap_or(false)` after the mayhem test | 27,032 | 1,121 | 1,994 | 2,390 | 2,509 | 0 | | | | | I I (326 O) |
| c_mh289: c_mh plus 289 `!holder` | 27,264 | 1,690 | 1,898 | 2,232 | 2,422 | 118* | | | | | I I (326 O) |
| c_uo289: v_uo plus 289 `!holder` | 26,848 | 1,731 | | | | | | | | | I I |
| c_uoe: v_uo plus execute `hopt.unwrap_or(false)` | 27,488 | 1,381 | | | | | | | | | I I |

\* jfix3's chain detection does not fit c_mh289 (its relaid result is worse), so the move is not a valid relayout there.

Split of the v_uo class's 874-M loss against main:

| part | M | evidence |
| --- | ---: | --- |
| validate-exit join flip (MBP, cold-edge reload head; w14a113 mechanism) | 247 | 1,373 -> 1,620 relaid |
| frame / spill-slot reassignment | 375 | relaid fR - M = 423, main's 48; mostly orig 0x2800-0x3800, where the skeleton is equal (chunkprof) |
| register colouring | 44 | relaid rfR - fR = 372, main's 328 |
| skeleton at a perfect frame and colouring | 208 | relaid rfR 2,415 against main's 2,623 |
| (of which jump distances) | 174 | relaid rfjR 2,588 against main's 2,622 |

- The skeleton loss sits in the validate head (`tools/sdiff.py`, orig vs relaid): 110 inserted skeleton tokens at cand
  0x380-0x6f0.
- There, the non-holder target arm's three memcmps (zero key, sharing, holder_key) are laid out directly behind the 289
  holder_reward test. Both `h&1` and `h&-3` are live, because 289 still tests `!(hopt==Some(true))`.
- The original tests one `h&1` holder value (`and64 r8,1`) and places the 289 error with its inlined formatter at orig 0x648.
- **Kill criterion met.** The relaid M is 627 below main. The perfect-colour legal-frame bound rfR (an upper bound on any RA
  climb at this code shape) is 208 below. Both are more than 60 M short.

## 3. Step (b) screen readings

- No row outlines 307/312, so there is no outline base to hand to the origfill lane. The origfill lane had no ledger rows
  when this lane ran.
- `c_vb` (validate takes the bool) holds main's skeleton (skM 2,810) and has **rfjM/rfjR +73 over main**, but it is M -14 at
  27,400 B. That is frame and jump-distance only, the same "skeleton yes, frame no" pattern as w14a108's `ev_cb_local`.
  It is a lead for frame/jump-repair lanes, not landable.
- Field order (`c_fo`: holder_enabled before holder_reward) and 296 read order (`c_ro`) were stopped unbuilt: the machine was
  at load ~110 and the time box had run out.

## Tools (experiment only)

- `tools/inl.py <rx|m.ll>`: the real -O3 outline map per `error!` line, checked against the original's set.
- `tools/vbfi.py <raw.ll>`: the real BFI of validate's final simplified body. `VB_AT=<pass prefix>` picks an earlier dump.
- `tools/decomp.py <rx>...`: the table in section 2 (needs the w14a93/w14a113 `tools93` bundle as `../jt`).
- `tools/jfix3.py`: jfix2 with a generalised `%bb5.iN` end.
- `tools/sdiff.py a b`: skeleton insert/delete runs between two candidates, or `orig`.
- `tools/blks.py`: asm block list with IR names.
- `tools/mine.py`: the genes used here.
