# w15a10-cto-newentrycopy: the entry copy of `new` cannot pay as one joint state (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 90300f9d2 (admin_cto unchanged through ed47ac7 / d530a71): 0.67346, 3,124 slots, scorer M 2,248, true-LCS
`---` 2,253 / `rfj` 3,007 / `rf-` 2,888. The oracle (raw-IR capture, then `opt -O3` and `llc`; w14a127 `rx.py`) gives
`eq_main: true`.
Ledger: approach `newentrycopy`, keys `0x22a10-w15-ed47ac7-newentrycopy-*` (74 trial rows plus `-pricetable-v1`).

**Result: no zero-loss gain and no source change.** This PR is a joint price table showing that the entry-copy state
cannot pay on today's main (best 0.59360 @27,712; rfR +10 over main at best). The table covers form x pda x fl x hkc, plus by-value keys (V1/V2), the sharing-payload
source and an inline `quote_locked`.

## 1. Forms of `new` (each alone, on main)

| gene | source form | ratio @ bytes | note |
| --- | --- | --- | --- |
| main | `let args=&(new,)` after CtoState; validate takes `new`; sharing arm `Some(args.0)` | 0.67346 @27,400 | |
| `Frn` | validate takes `new:&Option<Pubkey>`, called with `&new` | = main (identical) | |
| `Fv` | `let new=new;` as validate's first statement | = main (identical) | |
| `Fb` `Fb0` `Fc` `Fc0` `Fs` `Ft` | named local `nc` before CtoState; `let args=(new,)` by value; `NewArg{new}` struct; `let new_c=new` at the top of execute (before the shared chain and PDA) | **all identical**: 0.48082 @27,368 | J flip (below) |
| `Fa` | validate reads `args.0` (the tuple copy) | 0.43713 @27,688 | **the only form whose entry copy survives** |
| `Fr` | validate takes `&args.0` | 0.43496 @27,808 | |
| `Fa_sn` | Fa, with the sharing arm `Some(new)` | 0.62777 @27,336 | copy forwarded again |
| `sut` | sharing arm `Some(Some(target))` (the validated target, the original's P2<-P1 copy at orig 0x19a0) | 0.52627 @27,288 | |
| `V1` / `V2` | holder_key (and the sharing key) by value | 0.53575 @27,480 / 0.53995 @27,360 | V1 = hkc, identical |
| `qli` | `quote_locked` inline in the CtoState literal (w13a41 t22) | 0.62862 @27,264 | |

Readings:
- **Main's `&(new,)` is special.** Its temporary hoists the tag load (`%_45.sroa.0.0.copyload`) to the args statement,
  where validate's tests and the sharing phi all reuse it. The payload copy is forwarded (`%_45.sroa.5` is `%new+1`).
- Every non-reference spelling compiles to the same code. Without that temporary, the tag is loaded twice inside validate.
  RA then splits the accounts pointer, so `ldxdw r5,[r10-0x8d8]` appears at the head of the validate-exit join
  `%bb56.i`, and MBP moves the 119-block second validate arm chain behind it. That is the w14a127 J flip, with the same
  trigger. Relaid with `jfix3`, it is 0.59523 @27,376, still -0.078.
- **The copy survives only when validate and the sharing arm both read it (Fa).** This is w14a127's walk-limit
  mechanism.
  - Fa then reproduces the original's entry pattern: tag spill, 7 B `ldxw [+4]/[+1]`, `[8]`/`[16]` in registers and the
    9 B end.
  - It also reproduces the original's single read of the copy at the fee-Some exit: Fa at 0x18c0 against orig 0x1858.
  - If the sharing arm drops its read (`Fa_sn`, `sut`), the copy is forwarded and the entry pattern goes away.
- Raising `-memssa-check-limit` to 10000 on Fa does not rescue it: 0.4323 @27,584.

## 2. Joint table (form x pda x fl x hkc; `_p` = PDA before the shared chain, `_f` = curve bools read right after it, `_h` = `&{holder_key}`)

Columns: scorer ratio at bytes, then w14a93 `regceil` (plain/regonly/L1/L2), then w14a87 `fbound`: fR (legal frame),
rfR (legal frame plus perfect colouring) and rfjR (also jumps masked).

| state | ratio @ bytes | L1 | L2 | M | fR | rfR | rfjR | true-LCS rf- / rfj |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **main** | **0.67346 @27,400** | **0.70282** | **0.78550** | **2,248** | **2,296** | **2,623** | 2,623 | 2,888 / 3,007 |
| fl | 0.63448 @27,352 | 0.66597 | 0.78081 | 2,116 | 2,181 | 2,583 | 2,616 | - / 3,007 |
| pda | 0.58059 @27,400 | 0.62522 | 0.78520 | 1,938 | 1,989 | 2,554 | 2,595 | - / 3,019 |
| hkc | 0.53575 @27,480 | 0.69488 | 0.79539 | 1,791 | 2,197 | 2,536 | 2,705 | - / 3,010 |
| F0_f_h | 0.54385 @27,448 | 0.66776 | 0.79796 | 1,817 | 2,164 | 2,565 | 2,693 | - / 3,018 |
| F0_p_f (+h) | 0.474 / 0.430 | 0.477 | 0.607 | 1,584 / 1,439 | | | | collapse |
| Fc0_p | 0.58238 @27,400 | 0.61294 | 0.78910 | 1,944 | 1,993 | 2,558 | 2,638 | |
| Fc0_f | 0.57993 @27,240 | 0.66406 | 0.77434 | 1,930 | 2,114 | 2,551 | 2,591 | 2,860 / 2,991 |
| Fa_f | 0.50700 @27,736 | 0.49539 | 0.74933 | 1,703 | 1,942 | 2,475 | 2,487 | |
| **Fa_f_h** (= FaV1_f) | 0.49725 @27,760 | 0.64038 | 0.78292 | 1,671 | 2,052 | 2,587 | **2,734** | 2,896 / **3,034** |
| FaV2_f | 0.51094 @27,760 | 0.64038 | 0.78292 | 1,717 | 2,071 | 2,604 | 2,653 | - / 3,034 |
| FaV2_f_hkt (+ plain PDA) | 0.56242 @27,760 | 0.64038 | 0.78232 | 1,890 | 2,080 | 2,609 | 2,658 | - / 3,032 |
| **FaV2_qli** (w13a41 t22 form) | 0.53343 @27,712 | 0.64899 | **0.78541** | 1,791 | 2,157 | 2,617 | 2,659 | **2,901** / 3,032 |
| **FaV2_qli_hkt** (+ plain `(holder_key,_)` PDA = w13a41 t8+t22, the full faithful form) | **0.59360 @27,712** | 0.64899 | **0.78541** | **1,993** | 2,176 | **2,633** | 2,675 | **2,901** / 3,032 |
| Fa_h_qli | 0.52658 @27,712 | 0.64899 | 0.78541 | 1,768 | 2,138 | 2,598 | 2,736 | 2,901 / 3,032 |
| Fa_p*, Fr_p*, FaV*_p*, V2_p_f | 0.425-0.462 @27,720-28,016 | ~0.49 | ~0.60 | ~1,450 | | ~1,900-2,030 | | layout collapse |
| Fa_sn / Fa_f_sn | 0.62777 @27,336 / 0.58996 @27,392 | 0.666 | 0.775 / 0.777 | 2,093 / 1,969 | 2,163 | 2,573 / 2,564 | 2,574 | |

All 74 rows are in `results.txt` (`res.json` metrics, scorer M/skM, true-LCS `---`/`rfj`, per-0x800-chunk true-LCS
deltas against main) and in `bounds.txt`.

Readings:
- **Only one joint state reaches main's legal-frame + perfect-colouring bound with real jumps (rfR):** FaV2_qli_hkt,
  the full faithful form (Fa + V2 + inline `quote_locked` + plain `(holder_key,_)` PDA), at 2,633 against 2,623 (+10).
  Every other state stays below; the next best are FaV2_qli at 2,617 and FaV2_f_hkt at 2,609.
  - FaV2_qli_hkt's scorer M is 1,993 against 2,248, so it would need about 640 tokens back from register assignment and
    frame alone, and 312 B back to reach the pinned size. Main's own gap to its rfR is 375 tokens.
  - RA-only levers are bounded at about +0.0066 on main (w14a84) and about +0.017 on the PDA states (w14a93). The bound
    margin (+10 tokens, about +0.003) is far below what the state costs, so it cannot pay as a landing.
- The entry-copy states are structurally closer to the original:
  - true-LCS rf- (registers and frame masked): FaV2_qli 2,901 against main 2,888;
  - rfj: Fa_f_h 3,034 against 3,007, close to the w14a128 census maximum of 3,038;
  - the gains are in the entry chunk 0x0-0x800 (+23..+27), so this is a real lead, not a difflib flip.
- The cost is concentrated:
  - frame (true-LCS r--: Fa_f_h -272 tokens, mostly orig 0x2800-0x3800, where the extra copy slots shift the wallet and
    sweep frame);
  - registers (true-LCS -f-: -119);
  - +312..+360 B of size, from about 23 more head instructions (the copy and the fl loads) plus spill code: 11 more
    reloads and 7 more reg-reg moves.
- **Every PDA-first composite with Fa, Fr or fl collapses** (orig 0x2000-0x5000 match about 600 fewer tokens): the
  layout collapse w14a93 reported. The `fl` gene removes Fa's own collapse but not PDA's.
- The by-value keys are byte-identical to hkc (V1) or within noise (V2). The plain `(holder_key,_)` PDA binding (`hkt`)
  helps FaV2_f by +0.05 but not Fa_f_h.

## 3. Mechanism summary for other lanes

1. The original's entry copy is validate's by-value `new` argument temporary. It survives MemCpyOpt only while a far
   reader (here the sharing arm's `Some(args.0)`) keeps the MemorySSA walk over its limit. When it survives, the
   original's fee-Some exit read appears too.
2. The original's sharing payload is copied from validate's result join slot (orig 0x19a0-0x1a48: P1 0x538.. to P2
   0x550/0x560 and E32 0x580). So `Some(Some(target))` is the faithful payload, but on its own it costs -0.147 (`sut`),
   and with it the copy is forwarded (`Fa_sut`). The two faithful pieces exclude each other in today's pipeline.
3. Main's `&(new,)` hoisted tag load is what keeps the J layout. Any other spelling of the `new` temporary flips J.

## Next ideas (not run here)
- A source form in which the sharing payload comes from the validate result (`sut`) while the `new` copy still has a
  far reader that is semantically equal. Today's execute has no such reader: the event and the pool CPI read the updated
  curve or `target`, not `new`.
- FaV2_qli_hkt is the best-structured state (rf- +13, L2 equal, rfR +10). It needs about +640 register/frame tokens and
  -312 B, so it is only worth pricing with a private-llc colour climb (w14a93 `cclimb.sh`; that llc is no longer on disk).

## Tools (`tools/`, experiment only)
- `genes.py`: every gene as an exact-replacement edit list, composable with `+`. In the scratch dir it is `mine.py`.
- `cv.sh`: copy the crate, apply the genes, capture raw IR and score with rx.
- `run.sh`: two-worker batch that appends to `res.txt`, with true-LCS and per-chunk columns from w14a128 `lcs.py` and
  `lcschunk.py`.
- `rec2.py`: ledger recorder.
- `laydiff.py`: aligned block-size and layout diff of two `lay.py` layouts.
- `relayoff.py`: relayout by byte ranges, a wrapper around w14a93 `relay.py`.
- `rng.py`: disassemble a byte range.
- Oracle and bound tools come from w14a127 (`rx.py`, `oracle.py`, `capraw.py`, `lay.py`) and from w14a93/w14a87 (`t93/`:
  `regceil.py`, `fbound.py`, `jfix3.py`, `relay.py`).
