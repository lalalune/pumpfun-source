# w14a114-cto-irscantail: whole-function IR-order sensitivity outside validate (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 13fe453 (0.67256 / 3,123, M 2,245), then main ebe5387 (#3495, 0.67316 / 3,123, M 2,247).
Ledger approach `irscantail`, keys `0x22a10-w14-<main7>-irscantail-*`. M = matched masked tokens (difflib over
the call/lddw-masked instruction stream, as `rx.py`). All numbers come from the real-RA post-opt oracle: the raw IR was
captured with w14a101's `capraw.py`, run through `rx.py` (`eq_main` true on both mains), renumbered with `renum.py`, and every
variant was run through `llc` exactly as fastbuild does. No build slot was used for the scans.

## Result: no source change. Outside validate, the IR block order of main is a local optimum

No single post-opt IR block move outside validate beats main, and neither does any if/else arm-region swap. This holds on both
mains. The only IR-level gain is an instruction-order lead, the TCF program literal's `rent_epoch` load (+4 M), and it has no
source form. Every source spelling of that literal tried here collapses the TCF clone run.

### Block-order sensitivity per region (`region-table.txt`)

Units are chains of 1 to 3 consecutive non-validate blocks. Positions are before every non-validate block that follows a
conditional `br` or `switch`. The arm-region swaps move the dominance region of each successor of a conditional branch,
when that region is a contiguous IR run, to just before or just after the sibling region. Validate (`bb6.i..bb65.i`) is
excluded because other lanes own it (brhead, brtarget, irorder14).

ebe5387 (main M 2,247): s3 = 4,827 single moves within 8 blocks, a2 = 229 arm swaps.

| region (first IR block) | variants | at main M | best M | best M at 27,400 | worst M |
| --- | ---: | ---: | ---: | ---: | ---: |
| head (`start`) | 34 | 7 | 2,247 | 2,247 | 2,169 |
| post-validate (`bb75`) | 298 | 94 | 2,247 | 2,247 | 2,166 |
| wallet (`bb2.i72`) | 1,294 | 426 | 2,247 | 2,247 | 1,755 |
| sweep (`bb83`) | 2,032 | 301 | 2,247 | 2,247 | 1,080 |
| sharing-CPI arm + clone run (`bb88`) | 817 | 16 | 2,247 | 2,247 | 1,657 |
| curve/event/pool tail (`bb38`) | 579 | 207 | 2,247 | 2,247 | 1,648 |

13fe453 (main M 2,245) also adds s2 = 4,727 single blocks moved 9 to 30 blocks away. Every region is capped at main
M 2,245 as well. The sweep region is the most sensitive: moving the sweep exit or return-phi blocks costs up to 1,167 M.
The sharing clone run has the fewest neutral moves: 16 of 817 keep main's M.

Size-neutral movers, useful as fills: on 13fe453, `bb2+bb6@bb11` and `bb9@bb2` in the head keep M 2,245 at +8 B, and
`bb22+bb19@bb21` in post-validate keeps M 2,244 at -8 B. They are layout-only (short-circuit chain blocks) and have no source
spelling.

### Pairs and greedy (oracle bounds, not source)

- Pairs of the 70 best distinct near-neutral moves (2,415 pairs, 13fe453): the best is M 2,247 at 27,400. It is the pool-CPI
  drop-glue pair (`drop_in_place<Rc<RefCell<&mut u64>>>.exit.i.i + bb1.i.i4.i.i` before `bb1.i.i.i.i270`, +8 B) plus the
  sweep `Rent::get` Err block `bb84.i138` before `bb37.i129` (-8 B). Each move alone loses 2 to 3 M; together they gain
  +2 M, spread over chunks 0x2400, 0x5400 and 0x6000. On ebe5387 the same pair gives 2,249 (0.67376).
  Drop-glue order is fixed by the types, so this pair has no source form.
- Greedy accumulation from that pair: 2,248 at 27,400 (13fe453). It flattens immediately.

### Instruction-order scan (`irinst.py`): one IR-only lead

The scan moves each pure instruction to its hoist and sink endpoints (1,033 per main), and each load to every legal
position in its block (1,830 on ebe5387). Exactly one class of moves gains:

- **TCF CPI program literal (`{let x=a.pump_amm.as_ref();AccountInfo{owner,key,lamports,data,rent_epoch,executable,
  is_writable,is_signer}}`): place the `rent_epoch` load (`%_60.i144`, x+32) after the first `lifetime.start` of the TCF
  accounts struct `_64` pieces, before the payer `to_account_info` Rc increment.** ebe5387: M 2,247 -> 2,251,
  **0.67316 -> 0.67436 at 27,400** (slots 3,125). Chunks 0x2400 and 0x3800 gain +2 each. 13fe453: +4 as well.
- The order of the load against the `lifetime.start` chain nodes is what matters, because SelectionDAG chains loads to
  the root:
  - [rent, bools, lifetime] (main) and [lifetime, rent, bools] are both main.
  - [bools, lifetime, rent] is +4.
  - [bools, rent, lifetime] collapses: 0.63252 at +16 B, with the TCF clone-run RA cascade in chunks 0x2800 to 0x3c00.
  - Any bools-after-lifetime form collapses the same way.
- The original (orig 0x2730 to 0x27d8) loads this literal's flags in the order 0x2a, 0x29, 0x28, then rent 0x20 and owner
  0x18, all after the payer's lamports `add`. Only the key is loaded early. The reversed load order suggests that the
  original's IR order is owner, rent_epoch, is_signer, is_writable, executable, which is AccountInfo declaration order, as
  in a derive(Clone) body.
- Source spellings tried (raw-IR capture + `rx.py`), all on ebe5387:

  | spelling | ratio | bytes |
  | --- | ---: | ---: |
  | tp09: tail `executable, is_writable, is_signer, rent_epoch` (= the [bools, rent, lifetime] IR) | 0.63252 | 27,416 |
  | tp08: tail `executable, is_writable, rent_epoch, is_signer` | 0.61635 | 27,416 |
  | d1: declaration order `key, lamports, data, owner, rent_epoch, is_signer, is_writable, executable` | 0.6493 | 27,416 |
  | d4: `key, lamports, data, rent_epoch, is_signer, is_writable, executable, owner` | 0.6483 | 27,424 |
  | e1: Rc clone between bools and rent (`owner, key, lamports, exec, writ, signer, data, rent`) | 0.65368 | 27,400 |
  | e2: `owner, key, exec, writ, signer, lamports, data, rent` | 0.58093 | 27,424 |

  On d1, sinking owner, rent and the flags after the lifetime in IR does not recover it (0.619 to 0.649). The TCF clone-run
  RA collapse decides that literal, and the load order does not. Main's literal form is the best of every spelling known.
- IR-only composite bound (rent-late + drop-glue pair + `bb84.i138` move): **0.67496, M 2,253 at 27,400** on ebe5387.

## Mechanism summary for other lanes

- IR block order outside validate is not a lever on current main. The leads that w14a71/w14a36 saw after RA (placement
  only) do not appear with real RA either. Main's block order is already the best per region, and the queue-order effect of
  w14a86/w14a82 is not reachable through block order (the token arm and clone runs are capped at main).
- The only order lever left outside validate is in-block load-versus-`lifetime.start` order in the TCF literal. Source
  cannot place a load after the accounts struct's StorageLive without reordering the CpiContext arguments.

## Tools (`tools/`, experiment-only; put next to w14a101's `rx.py` and `eseq.py`)

- `irscan.py <mn.ll> <out> [W] [maxlen]`: block-order scan outside validate (`WMIN`, `SEEDS`, `NP`, `TMPD` env).
- `armswap.py`: dominance-region (if/else arm) swap scan.
- `irpairs.py`, `irgreedy2.py`: pairwise and greedy accumulation of near-neutral moves.
- `irinst.py`: instruction hoist/sink scan (`ALLPOS=1` gives every position of loads, `NONLOAD=1` gives non-loads).
- `px2.py`: llc + ratio + M + per-0x400 orig-chunk M. `insmv.py` / `applymv.py`: apply single instruction or block moves.
- `bmap.py <x.s>`: block -> offset map of our build.
