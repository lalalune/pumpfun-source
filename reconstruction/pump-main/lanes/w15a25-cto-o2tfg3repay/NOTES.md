# w15a25-cto-o2tfg3repay: outline trigger table, O-repay grid, and a 3-second oracle for validate's inline decisions

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883a9 (`programs/` unchanged on e61121452): 0.67376, 3,124 slots, M 2,249, true LCS 2,255 / 3,007.
Lane: wave-15 lane continued in wave 16 (the first run died at the w15 account limit). It continues w15a21-cto-creatorcopy
(#3723), Result 2 and next idea 1. Ledger approach `o2tfg3repay`, keys `0x22a10-w15-9120883-o2tfg3repay-*-v1`
(24 rows from the first run, plus `-grid-*`, `-trig-*` and `-irexp-*` rows from this run).

**Result: no landable change.** Main is still the best zero-loss measurement (0.67376 / 3,124 slots / 27,400 B).
- Every faithful source trigger found that outlines `to_string` at 307 and 312 gives the original's exact outline pattern
  and its lddw count (86). Every one of them also collapses the rest of the function, to M 1,400-1,550.
- The collapse comes from a CFG change made at inline time, and this lane names it: threading, or un-threading, the
  holder split. Outlining does not cause it, and tf_g3 does not repair it.
- The control experiment changes only the branch probability, with a steering-only flag (F2, w14a07 `cold306-f2`), so it
  is not landable. It outlines without collapsing: M 2,186 at 26,920 B. That is still 480 B short of the pin and 64 M short
  of main.
- The final CFG of validate is threaded in main, in the triggers and in the original alike (section 3). What differs is
  *when* the holder split is threaded. Main threads it only after validate's inliner visit, so 307/312 are still hot at
  that visit. The original's sites were cold there. A source spelling that threads it before the visit (T289n) reaches
  the same CFG shape through a different transformation order, and that order costs a global RA reassignment.
- The faithful pieces add their main-base costs on the IR-forced outline base O. No cell of the O-repay grid comes near main.

## Tools (`tools/`, experiment only; paths point at this lane's out dir)

- **Fast V oracle (new).** It gives the same inline decisions as the full pipeline in about 3 s. The full `opt -O3` on the
  35 MB capture takes about 2.5 min wall on this loaded machine.
  - `reduce.py <raw.ll> <out.ll>`: keeps `validate` (made external) and its transitive callees, and stubs every other
    define with `unreachable`. The module shrinks from 35 MB to 3.5 MB.
  - `vbfi.py <ll> [edits.py]`: validate's block frequencies at the start of its own CGSCC inliner visit, from the real
    `-O3` snapshot (`-print-before=inline`), per `to_string` site. `C` marks a site below 0.02 of the entry, where the
    cold-callsite threshold of 45 applies. `VB_ALL=1` prints every block.
  - `thr.py <ll> [edits.py]` (from this lane's first run): per-site cost and threshold from `-pass-remarks=inline`.
    `V:` is validate's own visit and `E:` is execute's.

  `reduce.py` + `thr.py` on `m0` reproduces the full module's V decisions exactly.
- `capt.sh <name> <genes> <slot>` captures the raw IR (one build) and runs the fast V oracle, writing to `trig2.txt`.
  `rxf.sh <name>` runs the full oracle on a kept capture (`rx.py` + `inl.py` outline map + call/lddw counts + `fr.py` tiers).
  `tq.sh` and `tqf.sh` are the queues.
- `ed/`: raw-IR experiments.
  - `e1.py` / `e2.py`: point the 289 branch at `%holder` (direct, or as an `xor`).
  - `e2i.py`: e2 with the 307/312 call sites `alwaysinline`.
  - `o326.py`: forced O plus the 326 site `alwaysinline`.
  - `bw.py`: branch weights on the holder split.
  - `ni.py`: w15a09's forced O.
- Genes are in `g25.py`.

## 1. Why main inlines `to_string` at 307 and 312: the V-time frequency table

The decision is made when the inliner visits `validate` (V), using validate's own BFI. A site is cold when its frequency is
below 2 % of validate's entry. Cold sites get threshold 45, against a cost of 130, so they stay outlined. A site that is
inlined at V never reaches execute's visit (E). The original's pattern is I at 284 289 296 298 306 326 and O at 307 312
330 334 338.

BPI facts at V (LLVM 18):

| construct | IR at V | probability |
| --- | --- | --- |
| `if st.flag {err}` (bool loaded from `&CtoState`) | `icmp eq i8 x,0` (InstCombine form of `trunc`) | zero heuristic: error edge 62.5 % (284 = 0.625) |
| `holder` (`hopt==Some(true)`, or a fresh `eq` call) | `i1` value | no heuristic: 50/50 at every re-test |
| `if let Some(t)=new` | SimplifyCFG range form `icmp ult i1 %trunc.off, true` | no heuristic: 50/50 |
| `t==Pubkey::default()`, `t==*sharing` | `memcmp(..)==0` | libcall heuristic: equal 37.5 % |

Main at V (`vbfi.py`, which matches a hand computation to 4 digits):

| site | 284 | 289 | 296 | 298 | 306 | **307** | **312** | 326 | 330 | 334 | 338 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| freq | 0.625 | 0.1172 | 0.0264 | 0.0403 | 0.0754 | **0.0283** | **0.0287** | 0.0183 C | 0.0011 C | 0.0031 C | 0.0037 C |

- The early SimplifyCFG threads only one holder-false edge into the non-holder arm: hr=0 and !holder (`bb14` →
  `bb23.critedge`, 0.0703).
- Two holder-true flows still re-test `holder` at `bb21`, which is 50/50:
  - hr=1 reaches it through a *fresh* `eq` call (`%_20`, from `!(hopt==Some(true))` at 289);
  - hr=0 with holder_enabled reaches it through the he test.
- So the non-holder arm gets N = 0.0703 + 0.0806 = 0.1509, and 307 = N x 0.5 x 0.375 = 0.0283.
- Outlining needs N < 0.1067.
- The table is wired: once 307 and 312 are cold, the holder arm gets more flow, so 326 turns hot at V. That is harmless, see
  `Io326` below.

## 2. Trigger table (fast V oracle, then the full oracle; main = `m0`)

| trial | source (validate) | V: 307 / 312 / 326 | final outline map | calls / lddw | bytes | M | true LCS --- / rfj | Mperm |
| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |
| main | `!(hopt==Some(true))` at 289 | 0.0283 / 0.0287 / 0.0183C | 307I 312I 326I | 157 / 88 | 27,400 | 2,249 | 2,255 / 3,007 | 2,292 |
| T289h (= B1) | 289 `st.holder_reward&&!holder` | 0.0220 / 0.0223 / 0.0118C | 307I 312I | 157 / 88 | 27,400 | 2,235 | 2,241 / 2,990 | |
| **T289n** | 289 `if st.holder_reward{if !holder{return Err(..)}}` | **0.0132C / 0.0134C** / 0.0279 | **orig pattern** | 157 / **86** | 27,008 | 1,410 | 1,535 / 2,452 | 1,524 |
| T289e | 289 `st.holder_reward&&holder==false` | 0.0173C / 0.0176C / 0.0253 | orig pattern | 157 / 86 | 27,008 | 1,410 | (same bytes class as T289n) | |
| T289ie | 289 `if st.holder_reward{if holder{}else{return Err(..)}}` | = T289n | | | | | | |
| T289ntf | T289n + tf_g3 | = T289n | orig pattern | 157 / 86 | 27,024 | 1,393 | 1,506 / 2,454 | |
| U1 / U2 | T289n + `holder=hopt.unwrap_or(false)` (validate / + execute) | 0.0121C / 0.0123C / 0.0125C | **307I 312I 326O** (E inlines them back) | 157 / 87 | 27,048 / 27,016 | 1,021 / 1,025 | 1,249 / 2,823 | |
| U4 | T289n + `matches!(hopt,Some(true))` (both) | = U1 | | | | | | |
| Y2 (v27) | split on a fresh `hopt==Some(true)` | 0.0176C / 0.0179C / 0.0182C | orig pattern | 157 / 86 | 26,960 | 1,411 | | |
| Y1 | T289h + v27 | = Y2 | orig pattern | 157 / 86 | 26,960 | 1,411 | | |
| Z2 (w13a17) | `let target=match new{Some(_) if holder=>298, None if holder=>*holder_key, None=>306, Some(t)=>{307;312;t}}` | 0.0176C / 0.0179C / 0.0182C | orig pattern | 157 / 86 | 27,016 | 1,471 | | |
| **F2** (w14a07 `cold306-f2` port, pricing only) | RAR + `validate(..,has:bool,..)` with `has=args.0.is_some()` + 306 as `if let (true,Some(t))=(has,new)` | 0.0141C / 0.0144C / 0.0155C | orig pattern, **no collapse** | 157 / 86 | 26,920 | **2,186** | 2,199 / 2,958 | |
| F2t | F2 + tf_g3 | = F2 | orig pattern | 157 / 86 | 27,008 | 2,184 | | |
| Z1 | 312 as `require!(t!=*sharing&&t!=*holder_key,..)` | = main (0.0283 / 0.0287) | 307I 312I | | | | | |
| W1 / W2 / W3 | T289n + 298 as `if let Some(_)=new` / `new!=None` / `require!(new.is_none(),..)` | = T289n | orig pattern | 157 / 86 | 27,008 | 1,410 | | |
| X1 / X2 / X3 | T289n + `sharing_update=Some(new)` / + drop `args` / `args=(new,)` by value | = T289n | orig pattern | 157 / 86 | 26,992 | 1,548 | 1,603 / - | |
| first run | A1-K2 (h296in, B2 = h296in+p289h, B4a new_target helper, K1/K2), `data/trig-w15.txt` | | B2/B4a/C1/G*: orig pattern | 157 / 86 | 26,880-27,000 | 1,421-1,623 | 1,507-1,870 / 2,447-2,979 | |

Notes on the table:
- T289h misses by 10 %. SimplifyCFG merges both holder-true paths into one 296 block, `select(hr==0, he==0)`. That block's
  pass edge re-tests holder at 50/50, so N = 0.0703 + 0.0469.
- In T289n, T289e and T289ie the 289 branch is on `%holder` itself. The early SimplifyCFG then threads that path straight
  into the holder arm, so N = 0.0703.
- Z1 shows that a per-site error-macro spelling cannot move N. Such spellings change only their own error block, so they
  cannot trigger the outline.
- Y2 and Z2 trigger the outline by *removing* main's critedge threading, which adds a 50/50 on every path. They collapse
  just like the threading triggers do.
- F2 is the control experiment. It adds one 50/50 test of a bool argument on the Some path and keeps main's holder
  split, so the change is BPI-only and nothing is threaded. It gets the original's outline set and keeps main's later code:
  - M 2,186 at 26,920 B, with true-LCS chunk deltas against main of only -3 to -19;
  - fM 2,387 and rfM 2,670, against main's 2,350 and 2,621.

  `has` repeats `new`'s tag and exists only to steer BPI, so under the RULE it is a pricing probe, not a candidate. At the
  pin F2 still needs +480 B and +64 M (w14a07 found no faithful fill for this basin on cef0574).
- An older lane found the `holder==false` trigger on 917ee61 (`r1-289-holder-eq-false`, 26,856 B). w13 recorded
  `outline306-t289-nested-ifelse` as rejected.

## 3. Why every trigger collapses: V-time threading, not outlining

| IR experiment | what it isolates | bytes | M | true LCS --- / rfj | Mperm |
| --- | --- | ---: | ---: | --- | ---: |
| Otf_g3 (w15a21 forced O on tf_g3) | outline only | 27,024 | 2,199 | 2,248 / 2,983 | 2,244 |
| `Ie2` = main IR + 289 branch on `%holder` (xor form) | threading at V, source-free | 27,008 | 1,410 | = T289n (same class) | |
| `Ie2i` = Ie2 + 307/312 `alwaysinline` | threading **without** outlining | 27,432 | 1,423 | 1,538 / 2,478 | |
| `T289hb_O` = T289h source + forced O | p289h's MIR change, no V threading | 26,992 | 1,941 | 2,029 / 2,958 | 2,099 |
| main + forced O (w15a21 `none_O`) | reference for the row above | 26,992 | 1,955 | 2,043 / 2,976 | 2,113 |
| `Io326` = forced O + 326 `alwaysinline` at V (tf_g3 IR) | 326 inlined at V, as in the triggers | 27,072 | 2,198 | 2,247 / **2,988** | 2,243 |

- The spelling costs only 14 M (T289hb_O against none_O).
- The timing of 326's inlining is harmless. It is even +5 rfj (Io326).
- Threading the holder split at V collapses the function with or without outlining (Ie2i).
- The concrete residual is one extra alloca. T289n's `execute` has 141 allocas, main's has 140 (Ie2, Ie2i, T289e and U1
  have it too; T289ntf as `%_46.sroa.5`). The extra one is `%_45.sroa.5 = alloca [32 x i8], align 1`: the Pubkey payload
  of **execute's `args=&(new,)` tuple copy** (`_45 = alloca [33 x i8]`, `memcpy(_45 <- new, 33)` in execute's raw IR).
  - In main it is forwarded away: the sharing arm reads `new` directly.
  - Under the trigger the copy survives. It is filled from `new+1` and read only by the `sharing_update.sroa.6` memcpy of
    the shared arm. Its tag byte becomes the `sharing_update.sroa.0` phi input.

  Its consequences:
  - The frame moves: the arg spill goes from `-0x910` to `-0x920`, and the `-0x6a8..` band moves 8 B deeper.
  - The RA changes from the first instruction on. `lcschunk` against main (`---`): 0x2000 -268 and 0x3000 -281, the same
    numbers as w15 B2. Under `rfj` the validate chunk 0x1000 is +18, so the trigger's own region is fine.

  Forwarding the copy does not fix it. `X1` (`sharing_update=Some(new)`) and the IR edit `Tfwd` give the same bytes:
  140 allocas, M 1,548. That is only +138 M, and the losses at 0x2000 and 0x3000 stay (-258 / -285 `---`). The copy is a
  symptom. The remaining cause is a register-allocation reassignment that starts at the first instruction, for example r6
  holding ctx instead of the accounts pointer. It follows from the threaded validate CFG.

  This is the original's class E ("entry copy of `new`", w15a11): the original keeps such a copy too, but as SROA pieces
  (1/7/8/8/8/1 B), not as one 32 B alloca. The 298-site spellings W1 (`if let Some(_)=new`) and W2 (`new!=None`) fold to
  T289n's bytes, which confirms the 298 temporary is not involved.
- Some V-time CFG changes are harmless: T289h's merged 296 block costs only -14. That change apparently ends in main's
  final CFG. The threading triggers (T289n, Ie2i) and the removal of the critedge (Y2, Z2) do not.
- U1/U2 show another way to fail: with `unwrap_or(false)`, V marks 307/312 cold but E inlines them back.
- BPI-only triggers do not collapse.
  - w14a07-cto-cold306's `c1` is a `#[cold] fn cold(){}` call at the head of the 306 Some arm. On 769f331 it scored near
    main: 0.63342 with an llc-time tag weight, against main's 0.63241.
  - Its marker-free `f2` (the `has` flag) is ported here as F2: M 2,186 at 26,920 B, a mild shift (chunk deltas -3 to
    -19).

  Both work only through redundant steering constructs. `c1` is a dummy call and `has` repeats `new`'s tag, so the RULE
  excludes both. No faithful construct found here lowers N or P(Some) by 30 % through BPI alone. BPI's levers are
  zero/null/memcmp compares, cold or noreturn calls, loops and unwind edges.
- The final validate CFG is the same threaded shape in the original, in main and in T289n. Holder is tested once per hr
  path. The holder arm is shared by hr=1&holder and hr=0&holder&he. Only hr=0 & !holder reaches the non-holder arm.
  - Original: hr=1 `jne r8,0` at 0x640 (r8 = `hopt & 1`) goes to the holder arm at 0x900, else to the 289 error at 0x648.
    hr=0 goes to `jeq r8,0,+1; ja` at 0x720: holder reaches the he test at 0x8f8 (then the 296 error at 0xf40, or the
    holder arm at 0x900); !holder reaches the new-tag test at 0x730-0x748 (Some to the 307/312 checks at 0xc08, None to
    the 306 error at 0x750). The holder arm then runs its own copy of the fee checks (0xab8-0xb40, class F).
  - Main: hr at 0x5e0. hr=1 tests holder at 0x5f8 (else the 289 error at 0x8a8). hr=0 tests holder at 0x6e8, sending
    !holder to the non-holder arm at 0xb98 and holder through the he test at 0x6f8 into the shared holder arm at 0x600.
    T289n has the same skeleton.

  So the difference is not the final shape but *when* it is threaded:
  - The original: at V its N must be about 0.0703 (as in T289n), which is why 307/312 are cold there. So its validate is
    already threaded, or otherwise as cold, before validate's inliner visit.
  - Main: LLVM threads only afterwards, in validate's function simplification, so at V N = 0.1509.
  - The triggers: a spelling that threads at V (T289n, Ie2i) reaches main's final shape by a different transformation
    order. It ends with a different IR order, the surviving `args` copy and a global RA reassignment of about 700-850 M.

  A faithful trigger has to give V-time coldness through a source shape that LLVM later builds into exactly main's final
  IR. None of the forms tried here does.

## 4. O-repay grid (IR-forced O on tf_g3 captures; `vr.sh` plain / O / O312)

| cell | plain bytes / M | O bytes | O M | O true LCS --- / rfj | O Mperm |
| --- | --- | ---: | ---: | --- | ---: |
| Otf_g3 (w15a21) | 27,456 / 2,248 | 27,024 | 2,199 | 2,248 / 2,983 | 2,244 |
| + b01 (validate `holder_key:Pubkey`) | 27,384 / 1,773 | 26,960 | 1,760 | 1,956 / 2,981 | 2,107 |
| + b02 (b01 + 312 holder-first) | 27,384 / 1,778 | 26,960 | 1,765 | 1,958 / 2,981 | |
| + Fa (validate reads `args.0`) | 27,584 / 1,461 | 27,256 | 1,402 | 1,518 / 2,470 | 1,519 |
| + b02 + Fa | 27,632 / 1,309 | 27,296 | 1,362 | | |

- b01 costs -439 M on O and -428 on main, so it is additive. Its known 7-byte `target.i.sroa.0` alloca shift (w15a19) is
  not cancelled by outlining.
- Fa collapses on this base.
- With w15a21's knob result (knobs are additive on O), the 376 B of room on O cannot be bought back with these pieces.
  Even a perfect source trigger for O would sit about 50 M below main before any repay.

## 5. Verdict and next ideas

- The angle is exhausted. The trigger exists (T289n/e/ie), but it reaches O only through a V-time CFG change that main's
  later code cannot survive, and O's room has no faithful repay.
- For any future outline lane:
  1. A BPI-only trigger keeps main's later code (F2; also the banned w14 cold marker). The faithful ones tried here
     thread or un-thread the holder split before V, and all of those collapse, even though the final CFG shape equals
     main's. The remaining faithful route is a validate shape that is cold at V by structure (as the original's was) and
     that LLVM still builds into main's final IR order. Or it is a whole-region rewrite that re-fits the later RA around
     the early-threaded order.
  2. Screen candidates with `capt.sh` (V decisions in seconds) before any full build.
  3. Check for the surviving `args` copy (`%_45.sroa.5`, `[32 x i8], align 1` in execute's post-O3 IR) before scoring.
- Even a perfect O trigger would sit near the IR-forced O (M 2,199 at 27,024 B with tf_g3), about 50 M below main, with
  376 B to repay. The faithful pieces repay nothing (section 4), so the outline route cannot land on its own. It is worth
  pursuing only as part of a whole-region validate rewrite that also changes the skeleton (classes A-J of w15a11).

## 6. Data

- `data/trig2.txt`: fast-V-oracle rows for every capture of this run.
- `data/rxf.txt`: full-oracle rows (outline map, calls/lddw, `fr.py` tiers, ratio).
- `data/grid.txt`: O-repay grid rows (plain / O / O312).
- `data/lcs26.txt`: true LCS (`---` / `rfj`).
- `data/mperm26.txt`: Mperm (w15a08 `relab.py bin`).
- `data/trig-w15.txt`: the first run's rows.
