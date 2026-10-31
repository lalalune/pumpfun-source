# w15a21-cto-creatorcopy: creator-binding spelling table (two codegen classes) + an outline-base stabilizer

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base main 86e2a6b74 (#3666; worktree on 139a01a51, same `admin_cto.rs`): 0.67376, 3,124 slots, M 2,249.
Continues w15a09-cto-tuplelocals (#3668), next idea 2: find a curve-creator binding between g0 (`target=st.creator` in
the shared non-holder arm) and g1 (`let creator=st.creator;` before `validate`) that keeps g1's skeleton without its
SSA pieces living across validate. Ledger approach `creatorcopy`, keys `0x22a10-w15-86e2a6b-creatorcopy-*-v1` and
`0x22a10-w15-86e2a6b-creatorcopy-outline-*-v1`.

**Result: no landable change.** Main is still the best zero-loss measurement (0.67376 / 3,124 slots / 27,400 B).

## Method

w15a09's raw-IR oracle, copied to this lane's out dir with its paths changed: `tools/cv.sh` (capture with
`--emit=llvm-ir -C no-prepopulate-passes` through fastbuild, SDK `opt -O3`, `llc` like fastbuild; `none` gives
`eq_main: true`), `tools/run1.sh` and `batch.sh` (one variant per run, 2 slots), `tools/vr.sh` and `batchO.sh` (the
same capture, also scored with the 307+312 `to_string` call sites marked noinline (O) and with 312 only (O312),
w15a09 `ed/ni.py`). Metrics:

- M / rfjM: difflib (w14a108 `fr.py`).
- True LCS (`---` and `rfj` masks): w14a128 `lcs.py`. This is the skeleton measure; difflib flips on small changes.
- Mperm: w15a08 `relab.py`, wrapped (`relab.py bin <name>`) to read the oracle `fn.bin` and take the spill set from the
  binary (`binspills`). Main's Mperm is 2,292.

New small tools: `tools/lcsdiff.py` (orig offsets that a candidate matches and the reference does not, under true LCS),
`tools/tab4.py` (the table below), `tools/rec4.py` / `tools/recO.py` (ledger rows). Genes are in `tools/tg.py`: exact
single-occurrence replacements, line count kept (w15a09 genes plus rounds `cc*`, `cs*`, `gr_*`, `tf_*`, `sv*`).

## Result 1: every creator spelling is one of two codegen classes

Full table (59 variants): `screen_table.md`. Summary (main 27,400 B, M 2,249, LCS 2,255 / 3,007, Mperm 2,292):

| class | spellings (all byte-identical within the class) | bytes | M | LCS --- / rfj | Mperm |
| --- | --- | ---: | ---: | --- | ---: |
| **g1: value bound before `validate`** | `let creator=st.creator;`, `st.creator.clone()`, `Pubkey::new_from_array(st.creator.to_bytes())`, `st.creator.to_bytes()` then `Pubkey::new_from_array` / `Pubkey::from` / `.into()` in the arm, `let CtoState{creator,..}=st;`, `let &CtoState{creator,..}=&st;`, `*&st.creator`, `Some(st.creator)` + `unwrap()`, `creator.clone()` in the arm | 27,520 | 2,251 | 2,257 / 3,014 | 2,289 |
| **g0: read in the arm** | `target=st.creator`, `st.creator.clone()`, `Pubkey::new_from_array(st.creator.to_bytes())`, `{let c=&st.creator;*c}`, `let creator=&st.creator;` + `*creator`, `let s=&st;` + `s.creator`, binding at the head of the shared arm, `st` passed by value / `&{st}` / `&st.clone()` with `#[derive(Clone,Copy)]` plus `target=st.creator` | 27,392 | 2,246 | 2,254 / 3,009 | 2,291 |
| main form (`target=a.bonding_curve.creator`) | also `st` by value / `&{st}` (sv1, sv2) | 27,400 | 2,249 | 2,255 / 3,007 | 2,292 |

Other forms:

| gene | change | bytes | M | LCS --- / rfj | Mperm |
| --- | --- | ---: | ---: | --- | ---: |
| cs4 / cs9 | g0 / shared-head binding with `target=` before `sharing_update=` in the arm | 27,408 | 2,247 | 2,255 / 3,008 | 2,292 |
| cs5 | main source, `target=` first in the arm | 27,416 | 2,248 | 2,254 / 3,008 | 2,291 |
| cs7 / tf_f6 | g1 / f6 with `target=` first | 27,504 / 27,512 | 2,249 | 2,255 / 3,012 | 2,289 |
| tf_g1a/b/c, tf_g1e, tf_f7, tf_g3 | other binding positions, `target=` first | 27,424-27,480 | 2,239-2,248 | 2,244-2,254 | 2,291 |
| cc11 | `let args=&(new,st.creator);` and `target=args.1` | 27,472 | 2,239 | 2,244 / 3,016 | 2,291 |
| cc7 | g1 plus `creator!=Pubkey::default()` in collect_old | 27,352 | 1,536 | collapse: `st` no longer escapes to memcmp, so its alloca goes (w13a16) |
| cs1 | `CtoState{creator:&Pubkey,..}` | 27,240 | 1,754 | collapse (same reason) |
| cs2 / cs3 | target override after the block (`if shared&&!holder{creator}else{target}`), creator as a 7th tuple field | 27,544 / 27,832 | 1,216 / 962 | collapse |
| cs8 | holder arm writes `target=holder_key` | 27,280 | 2,152 | rfjM +59 is a difflib flip; LCS 2,164 / 3,003 |
| gr_*n | `Some(new)` instead of `Some(args.0)` in the arm (any target source / order) | 27,376-27,448 | 1,603-1,605 | the `(new,)` temporary collapse (w14a127 J flip) |
| g5 | `let creator=..;let st=CtoState{creator,..}` | 27,560 | 2,064 | |

**Mechanism.** LLVM sees only two shapes. If `creator` is bound before `validate`, GVN forwards it to the entry loads that
built `st`, so the four i64 pieces are SSA values live across the whole of validate (g1: +120 B of moves and reloads in
0x4f8-0x1af0). If it is read after validate, it is re-read from `st` memory in the arm (g0), at the misaligned 7/9-byte
slicing of `target` (loads `[r10-0x31]`, `[r10-0x29]`, `[r10-0x21]`, `[r10-0x19]` byte, and a 7-byte piece from the
account), because `target` shares the Result<Pubkey> offset-1 layout. No spelling of the binding sits between the two:
copies, clones, byte arrays, destructuring, references, Option wrapping and binding position all collapse.

**g1's lead is RA noise, not skeleton.** Under perfect spill colouring g1 is *below* main (Mperm 2,289 against 2,292).
Its true-LCS gains are scattered single tokens (`lcsdiff.py none g1`: +15/-8 tokens at 0x5b8-0x1a50 under rfj, and
+6/-4 at 0x3d58-0x5018 under `---`), not a region that moves.

**What the original does.** Orig 0xdc8-0xe18 (the shared non-holder arm, reached by fallthrough from the `t==*holder_key`
test at 0xd70) copies `st.creator` from `[r10-0x38..-0x20]` with four aligned i64 loads into two target homes
(`[r10-0x4e8..-0x4d8]` and `[r10-0x530..-0x520]`) plus `[r10-0x918]` for piece 0: the 8|24 target split. The
validate-head copy at orig 0x598-0x5d0 (`[r10-0x6a0..-0x688]` -> `[r10-0x518..-0x500]`) is **holder_key** (the
`find_program_address` result copied out of `[r10-0x2d0]` at 0x100-0x138), not the creator. The original's st.creator is
stored ascending from a creator pointer `r9 = bonding_curve+8` (orig 0x358, 0x468-0x4a0); main stores it descending from
`r7+0x20..+0x8`. So the original's arm is the g0 form; what g0 lacks is the 8|24 target slicing, and that belongs to the
validate-return-type family (w12a01, w12a05, w13a18, w13a39, w14a54, w15a11), not to the creator binding.

## Result 2 (for the outline lanes): `tf_g3` stabilizes the 307+312 outline base O

On w15a09's IR outline base O (both `to_string` call sites noinline), binding the creator at the start of the state
block (g3: `{ let creator=a.bonding_curve.creator;let st=CtoState{..}`, or the same binding just before the 6-tuple
block, `tf_t`) **and** writing `target=creator;` before `sharing_update=Some(args.0);` in the shared arm recovers main's
code almost everywhere:

| base | gene | bytes | M | LCS --- / rfj | Mperm |
| --- | --- | ---: | ---: | --- | ---: |
| O | none | 26,992 | 1,955 | 2,043 / 2,976 | 2,113 |
| O | g3 (w15a09) | 27,016 | 2,048 | 2,148 / 2,976 | 2,160 |
| O | cs5 (main source, target first) | 26,984 | 2,029 | 2,129 / 2,974 | 2,169 |
| O | **tf_g3 = tf_t** | **27,024** | **2,199** | **2,248 / 2,983** | **2,244** |
| O312 | none / tf_g3 | 27,184 / 27,240 | 2,196 / 2,196 | 2,244 / 2,244 | |
| main | none | 27,400 | 2,249 | 2,255 / 3,007 | 2,292 |

`lcschunk.py none Otf_g3_O --mask ---`: Otf_g3_O equals main's true LCS in every 0x800 chunk except 0x0-0x1000 (-8
tokens, the outlined `to_string` region). The O base's losses at 0x1800-0x4000 (+45/+78/+34 tokens back in
0x2800/0x3000/0x3800) are RA and frame perturbation that this binding plus arm order removes. So O + tf_g3 is main minus
7 LCS tokens at 376 B less code. That is 376 B of repay room for the original's missing data flow, with the 2 extra lddw
relocations gone (the only non-.text ELF difference). On O312 the stabilizer does nothing. No source trigger for O
is known yet: w14a141 / w15a02's T outlines 312 only. Size-knob repay table on O + tf_g3: `screen_table_outline.md`.

## Next ideas

1. Outline lanes: use `tf_g3` as the base form on any source trigger that outlines both 307 and 312, then price faithful
   repays against Otf_g3_O (M 2,199 at 27,024 B), not against bare O (M 1,955).
2. The creator binding itself is exhausted. The original's arm is g0 with 8|24 target slicing. The lever is target's
   slicing (the validate return type / `?` hop), and many lanes have rejected forms of it.
