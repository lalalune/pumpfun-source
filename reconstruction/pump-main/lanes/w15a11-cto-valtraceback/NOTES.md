# w15a11-cto-valtraceback: true-LCS cause table for validate, and the price of 99 validate trials (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 90300f9d2 (0.67346, 3,124 slots) for most trials. Main moved to 86e2a6b74 (#3666, 0.67376) during the lane;
the key trials were re-run there (keys `...-86e2a6b-valtraceback-*`). Ledger approach `valtraceback`, keys
`0x22a10-w15-{90300f9,86e2a6b}-valtraceback-<trial>-v1` (about 100 rows, plus `...-valtraceback-causemap-v1`).
Oracle: w14a108 raw-IR capture + `opt -O3` + `llc` (`tools/cv2.sh`, `tools/rx.py`). `m0`/`m1` reproduce main exactly
(`eq_main`). The true-LCS metrics use w14a128's DP (`tools/lcschunk_m.py`).

**Result: no landable change. Main is still the best zero-loss measurement (0.67376 @ 27,400 on 86e2a6b).**
Validate-local idioms are exhausted on main's structure. Of 99 trials, 11 fold to main's bytes and 88 lose. Only one
trial moves validate's true-LCS skeleton toward the original: `b01`, validate takes `holder_key` by value. It is not
landable (section 3).

## 1. Cause table: orig-only true-LCS tokens in validate (orig 0x0-0x1800, mask rfj, main 86e2a6b)

`tools/cause.py main` runs the whole-function DP traceback (`matched()` from lcschunk.py) and classifies each orig-only
token in orig 0x0-0x1800 by its source construct. `traceback-86e2a6b-validate.txt` lists the unmatched runs.

| class | tokens | where (orig) | source construct | status |
| --- | ---: | --- | --- | --- |
| A | 23 | 0x80-0x140 | holder-rewards PDA computed before `shared` | PDA-first collapses (w14a04/09/11/93, w14a106 GP) |
| B | 8 | 0x150, 0x210-0x268, 0x288-0x2b0 | curve bools a3/a5/a2 and the global ptr loaded early and held | flaghoist collapses (w14a106 F0/G1) |
| C | 13 | `stw [r10-0x238/0x2b8]` immediates | error-block order: orig 289 298 306 296 326, ours 298 289 296 326 306 | B/Br, excluded (w14a87/98/104) |
| D | 16 | 0x1280-0x1370 | 307/312 `to_string` outlined | excluded (w15a02 t312repay) |
| E | 25 | 0x4d8-0x530, 0xc08-0xc58, 0x1138-0x1180, 0x1850-0x1890 | entry copy of `new`, SROA pieces 1/7/8/8/8/1 | entry-copy collapses (w12b10, w13a03, w13a42, w14a113) |
| F | 20 | [-0x950]/[-0x958]/[-0x8f8] stores, `mov rN, imm` | per-arm phi constants: orig tests `shared` inside the non-holder arm (0xdc0) before the fee checks and threads each exit | `ov1`-`ov4` here, w14a126 ov, w10r1/w12a08: collapse |
| G | 13 | 0x428-0x4b8 | CtoState store order: orig cb, hr, my, creator ascending, ql, fc, he, max_fee | literal-order permutations fold or lose (w14a73, w12a13) |
| H | 13 | 0x5e0-0x748, 0x8f8-0x908, 0xd70, 0xe28-0xe58 | holder `and 1` in r8, tag `and 1`, `jeq +1; ja` pairs | and-1 basin (w14a75/78, `v14`, `v21`) |
| I | 45 | scattered | copies and spill/reload placement that follow from A-H | RA, not a construct |
| J | 7 | 0x1a0, 0x358, 0x3c8, 0x618, 0x738, 0x1510, 0x1528 | other ISel (`add64 r9,8` curve+8 GEP, `and64 rN,1`) | c1/c3 fold (w14a106) |

Total 183 of the 332 orig tokens in validate. A, B, E, F and H are the original's head order and its and-1 basin. Every
spelling that produces them collapses the rest of the function (w14a128 census: none of 3,511 captures gained in
validate under true LCS). C and D are excluded here. G and J fold. I follows from the rest. Nothing run-local is left.

Per-chunk true-LCS on main (orig 0x400 chunks, matched tokens): `---` 0:65 400:38 800:79 c00:43 1000:77 1400:80, `rfj`
0:88 400:81 800:106 c00:94 1000:77 1400:100. The 0x400 and 0xc00 chunks lose mostly on frame (`-f-` 48 and 82).

## 2. Idiom price table (true LCS; deltas against main; `val[...]` = rfj delta per orig 0x400 chunk 0x0-0x1800)

Folded to main's bytes (`eq_main`): `v03` 296 `!(hr||he)`, `v04` `if let Some(_)=new`, `v05` `new!=None`, `v06` 306 as
`match`, `v08` `!holder&&st.cashback`, `v10` `!(1..=max).contains`, `v12` `f>max||f==0`, `v28` `mayhem==true`, `v29`
`Pubkey::new_from_array([0;32])`, `v32` `else{t}`, `v33` `let new=new`.

| trial | change | ratio @ bytes | true-LCS --- / rfj | validate rfj |
| --- | --- | --- | ---: | --- |
| `v01` | 312 `t==*holder_key\|\|t==*sharing` (original memcmp order) | 0.67136 @27,400 (86e2a6b 0.67166) | -1 / 0 | 0 |
| `v02` | 289 `st.holder_reward&&!holder` | 0.66926 @27,400 | -14 / -17 | 800:-18 |
| `v09` | `if let Some(f)=fee` | 0.6473 @27,408 | -50 / -2 | |
| `v14` | `holder=matches!(hopt,Some(true))` (and-1 basin) | 0.4109 @27,416 | -738 / -574 | c00:-23 1000:-21 |
| `v21` | 296 `!hr&&!he&&holder` | 0.43067 @27,416 | -729 / -559 | c00:-22 |
| `v22` | 289 `!holder&&hr` | 0.48252 @26,592 | -358 / -114 | 800:-48 c00:-29 1000:+19 |
| `v24`/`v25` | cashback `st.cashback&&!holder` / inline at 330 | 0.624 / 0.608 | -59/-86 | 800:-27 |
| `v26` | `!st.holder_enabled==true` | 0.43347 @27,440 | -720 / -549 | |
| `v27` | 298 arm `if hopt==Some(true)` | 0.42609 @26,960 | -716 / -562 | c00:-41 1000:+17 |
| `v30` | 338 split into two sites | 0.55501 @27,608 | -232 / -26 | 1400:-23 |
| `v31` | 326 `Err(..)?` | 0.62819 @27,352 | -53 / -37 | |
| `b01` | **validate `holder_key:Pubkey` by value** | 0.53575 @27,480 (86e2a6b 0.54595 @27,360) | -250 / **+3** | **400:+6** |
| `b02` | b01 + 312 holder first | 0.53724 @27,480 | -248 / +3 | 400:+6 |
| `b03`/`b04` | `sharing:Pubkey` by value (± 312 order) | 0.571 @27,400 | -223 / 0 | 0 |
| `b05`/`b06` | both keys by value | 0.542 / 0.540 @27,360 | -292 / -2 | 400:+3 |
| `h1`/`h2`/`h3` | `holder_key=find_program_address(..).0` / `(holder_key,_)=` / scoped `hk` | 0.5596 @27,400 | -224 / 0 | 0 (frame -0x28) |
| `h*b01/b03/b05` | PDA temp + by-value keys | 0.529-0.557 | -224..-287 / -2..+3 | |
| `ov1` | validate takes `shared`, non-holder arm yields `if shared{st.creator}else{t}` | 0.44401 @27,360 | -677 / -535 | 0 (loss in 0x2000-0x5800) |
| `ov2`-`ov4` | whole sharing tree inside validate's arms (if / match forms) | 0.37384 @27,576 | -891 / -552 | 1400:+10 |
| `b01_<knob>` | b01 + each of the 41 applicable `sizeknobs-cto.json` knobs | best at 27,400: `s_dest_borrow`/`g_s7_dborrow` 0.53355 | -262 / -7 | 400:+6 |
| `b01nv` | b01 without both `read_volatile` placeholders | 0.53022 @27,464 | -271 / -19 | 400:+6 1400:-22 |
| `nv` | main without both placeholders | 0.66677 @27,384 (86e2a6b 0.66707) | -25 / -22 | 1400:-22 |
| `T` (86e2a6b) | w14a141 312-outline trigger | 0.66165 @27,184 | -40 / -46 | c00:-34 1000:+8 1400:-20 |
| `Tb01*` | T + b01 (± le306, dv1) | 0.537-0.546 @27,136-27,144 | -293 / -47 | 400:+5 |

## 3. The b01 lead: the original's validate-entry key copies, reproduced exactly

The original copies the sharing key to `[r10-0x470..-0x458]` and `holder_key` to `[r10-0x518..-0x500]` before the mayhem
test (orig 0x548-0x5d0). Main copies the sharing key to `-0x518` and compares `holder_key` in place at `-0x6a0`. With
`fn validate(..,holder_key:Pubkey,sharing:&Pubkey)` (call `validate(..,holder_key,&sk)`), ours emits the same 16
instructions with the same frame offsets (`tools/sbs.py b01 0x540 0x640`). The copy is natural. It survives without the
`read_volatile` placeholders (`b01nv`), so it is not forced by them.

The price:
- +64 B for the 8-instruction copy, plus about 16 B of RA noise in the sharing-CPI clone run (0x4050-0x4700). On
  86e2a6b the same edit lands at 27,360 B.
- A frame shift: about 280 slot accesses below orig -0x548 move 8 B deeper (`tools/fhist.py`, `tools/fpair.py`).
- Bound with that shift undone (`tools/fshift.py b01 0x2000 0x568 8`): 0.62549 @27,480. That is still below main.

So b01 is a faithful piece of the original that main's shape cannot absorb. It fits a frame-layout composite, not a
validate-local landing. No size knob repays it: all 41 applicable knobs were tried, and the best at 27,400 B is 0.53355.

## 4. Other findings

- **v01 (312 operand order)** is skeleton-neutral (true LCS --- -1, rfj 0) and the original's order: it compares the
  holder_key copy first. It costs 0.0021 ratio through difflib alignment alone. Keep it in mind for composites that
  already take holder_key by value.
- **The sharing-tree-in-arm family (ov1-ov4)** loses 535-552 true-LCS rfj tokens. All of the loss is in orig
  0x2000-0x5800, the CPI and event bodies, and the validate chunks stay flat. It is a block-placement collapse of the
  later body, not a validate effect. A cand-vs-cand diff names the moved block: the whole `match sharing_update{Some(val)=>..}`
  sharing-CPI arm, 799 instructions starting `jne r7,2`, moves from main 0x3c38-0x5580 to 0x2458, ahead of the sweep. The
  original keeps it at 0x3c00-0x4800, after the TCF run. Merely passing `shared` into validate does this, even with
  execute's tree left byte-for-byte as main's (`ov1a`/`ov1b`, 0.42682 @27,448, same chunk deltas). Once `shared` is
  tested inside validate's arms, the downstream sharing_update match is threaded and created earlier in IR order. Any
  shared-split-in-arm form must first keep that arm's IR position, for example by carrying sharing_update through a
  non-inlined or `#[cold]` boundary (the w12 #2766 mechanism).
- **T's 0xc00 loss (-34) is partly spurious matches leaving.** On main, the original's non-holder `shared` split (orig
  0xd78-0xe58) is matched against our inlined 312 to_string block. Once T outlines 312, those false matches go. When a
  t312repay variant is priced in true LCS, read its 0xc00 delta with that in mind.

## Tools (`tools/`, experiment only; oracle/xled/fact/lcs/lcschunk/lcsalign/dis/rx/capraw from w14a128 and w14a108)

- `cv2.sh <name> <edits.py> <slot>`: copy the crate, apply `EDITS` (line count must hold), capture raw IR, run the rx
  oracle. `bat.sh <list>` runs a list two at a time.
- `ev.py <rx>...`: ratio, bytes, true-LCS `---`/`rfj` deltas, and validate per-chunk rfj deltas against
  `$BASE/unstripped.so`.
- `sbs.py <cand> <olo> <ohi> [mask]`: whole-function DP traceback, printed side by side for an orig range.
- `cause.py <cand>`: the cause table of section 1.
- `fhist.py` / `fpair.py`: histogram of r10-offset deltas over true-LCS-matched pairs, and the orig-to-cand slot map.
  They show frame shifts behind ratio drops that have a flat skeleton.
- `fshift.py <cand> <lo> <hi> <d>`: bound oracle that adds `d` to every r10 offset and r10 lea in (lo,hi].
- `e/gen*.py`: every edit set used here.
