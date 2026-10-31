# w14a39-cto-and1pscan: and-1 outline basin re-port, clone scans, Rc-order screen (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a10-cto-and1outline (#3224) and w14a07-cto-cold306 (#3223).
Ledger keys: `0x22a10-w14-{faf9962,28ab23a,6e011ea}-and1pscan-*-v1`.
All numbers come from the raw-IR capture + `opt -O3` + extracted `llc` oracle (w14a30 `capvar.sh`/`rx.py`, `eq_main`
true on every main used). `M` is the scorer's matched-token count. At the pinned size a candidate beats main only
with a higher M.

## Landed

- **#3340** (main 28ab23a -> 6e011ea): in the `transfer_creator_fees_to_pump_v2` CPI, the `pump_creator_vault_ata`
  AccountInfo literal clones `data` before `lamports` (`K,D,O,L,R,S,W,E`). admin_cto 0.65488 -> **0.65548** (+2 M),
  3,280 slots, 27,400 B, 0 losses, differential 363/0, unstripped sha256 `294794674d664b84…`.
  It came out of the Rc-order screen run in the and-1 basin (below). The same edit was +2 M on faf9962 too.

## 1. The and-1 basin on faf9962 (main 0.65129, M 2,174)

| form (all + tu8) | bytes | ratio | M |
| --- | ---: | ---: | ---: |
| main | 27,400 | 0.65129 | 2,174 |
| **p3u** (`hb` after quote_locked, validate `hopt:u8`) | 27,336 | 0.64907 | **2,164** |
| p3n (same, `hopt:bool`) | 27,328 | 0.64887 | 2,163 |
| p2 / p2u / p1u / e3 / p0u | 27,320-27,328 | 0.6387 | 2,129 |

On faf9962 the basin was only 10 M short of main (w14a10 measured 13-21 short on older mains). The literals that
landed since #3272 do help it: per 0x200 chunk it is +14 M at orig 0x600-0xa00 and -9 at 0x3600-0x3e00. The
0x4000-0x4800 clone-run collapse that w14a10 recorded does not happen at p3u.

- **jM** (jump offsets masked too, `tools/jm.py`): basin 2,285 against main 2,201 (+84); with registers masked as well,
  2,594 against 2,508. The basin is structurally closer. It loses 121 M to jump offsets, where main loses 27, and
  mismatched jumps number 119 against 105. The large deltas (+1312, +16768, ...) are validate jumps into error tails
  that sit somewhere else: that is block placement, not size.
- **Pure fill bound** (`tools/fillg.py`, greedy junk 8 B slots with crossing jumps fixed): +64 B of fill on the CD
  basin gives at most **+4 M** (2,166 -> 2,170; best spots orig-side 0x140, 0x1a0, 0x498, 0x4c8, 0x59e0). On main a
  single slot gives at most +1. So the basin needs real matched code worth more than 5 M, not padding.
- **Entry copy of `new` as the repay** (w13a41 t8 pieces on p3u+tu8): args after CtoState + `validate(args.0)`
  0.53391 @ 27,424; + plain PDA 0.51265; V2 by-value keys 0.55176; plain PDA alone 0.55489; V1 0.56612. All are
  layout collapses (-270..-450 M).
- **Size knobs** (all 48 `sizeknobs-cto.json` knobs that apply to the basin): 17 are token-identical. Every
  size-changing knob loses: +8 B costs 7-15 M, +16 B costs 3 M (`wl_ts_clockvar`, `g_w_clock_local`), +32 B costs 100 M.
  None is a viable fill.
- **Clone coordinate descent in the basin** (`tools/cd3.py`: every single scalar-read relocation of all 18 inlined
  AccountInfo clones, 11 TCF + 7 sharing; `tools/pscan.py` MODE=place on 11 clones, 729 placements each; pp
  in-position orders; event_authority 720 scalar orders): the only move is **TCF `associated_token_program` owner
  before the Rc clones** (+2 M, source-confirmed as a `K,O,L,D,..` literal, `TLO_ata`). Every other clone is at its
  placement optimum. Rc swaps per literal: RC2 (`pump_creator_vault_ata` data-first) +2, the rest -1..-52.
  RC2+TLO_ata gives 2,168 in the basin.
- Basin ceiling on faf9962: 2,168 + fill bound 4 = 2,172, below main's 2,174. **Not landable.**

## 2. After #3315 (native rent scope + Result<()> join) the basin collapses

| main | main M | best basin form | M | Δ |
| --- | ---: | --- | ---: | ---: |
| faf9962 | 2,174 | p3u+tu8 | 2,164 @ 27,336 | -10 |
| 28ab23a (#3315, #3334) | 2,186 | p3u+tu8 | 2,094 @ 27,288 | -92 |
| 6e011ea (#3340) | 2,188 | p3u / q2u / q4u + tu8 | 2,096 @ 27,288 | -92 |

All 13 `hb` positions (entry, after mint, after shared, after the PDA, before quote_locked, after quote_locked, at the
state block start, just before `hopt`) fall into two families: 2,096 (after quote_locked) and 2,057 (before it). The
loss sits at orig 0x4800 (-39) and 0x5800-0x5c00 (-45). 0x3c00-0x4800 is displaced by +352 B, which means a block
moved, and 0x5800 is the native arm that #3315 rewrote. **The and-1 outline is incompatible with #3315's native join**,
and #3315 is worth +11 M on main by itself.

## 3. Main-level screens on 6e011ea (M 2,188), none beats main

- Rc swap per literal (RC0..RC9 except RC2): 2,135-2,188 (RC9, the sharing program literal, is equal).
- to_account_info -> literal for every TCF field (payer, quote_mint, token_program, system_program,
  associated_token_program, coin_creator, coin_creator_vault_authority, pump_creator_vault, event_authority) and for
  sharing_config, in orders `KDLORSWE`, `KOLDRSWE` and `KODLRSWE`: best -1 (cva and TCF event_authority data-first). The
  `KLDORSWE` literal is token-equal to to_account_info. coin_creator and pump_creator_vault are `AccountInfo` fields
  whose to_account_info is an outlined call, so a literal there adds 8-56 B and loses 140-240 M.
- `cd3.py` over all 18 clones on main: no single scalar-read relocation gains.
- The 338 `CreatorFeeBpsOutOfRange` test (w14a10's OK-likely llc weight lead) in six spellings: `!(1..=max).contains(&f)`,
  `f.wrapping_sub(1)>=max`, `checked_sub(1).map_or`, `!(f>0&&f<=max)`, `f>max||f<1`, `(f==0)|(f>max)`. All fold
  to the same compare: M unchanged.

### Which #3315 hunk breaks the basin (main 0fbf8da, M 2,189)

p3u+tu8 with one #3315 hunk reverted at a time:

| revert | bytes | M |
| --- | ---: | ---: |
| none | 27,288 | 2,096 |
| W (wallet `is_writable==false`) | 27,280 | 2,096 |
| N (rent scope) | 27,336 | 2,163 |
| **J** (`(if amount>0{..}else{Ok(())}).map(\|()\|amount)` -> per-arm `.map`) | 27,336 | **2,168** |
| T (token arm `return Ok(amount)`) | 27,312 | 1,839 |
| E (event `nf` local) | 27,312 | 2,105 |
| all five | 27,344 | 2,162 |
| main with all five reverted | 27,408 | 2,165 |

The Result<()> join (J) is the incompatible piece. Basin+RVJ is 2,168 at -64 B (jM 2,292 against main's 2,223). cd3
finds no clone move there, and the holder-first curve store order (`sw`) is token-neutral. Its ceiling (+4 fill bound)
is about 2,172, 17 M below main.

### Other main-level checks on 0fbf8da

- Field reload through the account struct (`a.X.field` instead of `x.field`, the #3344 family) for every field of 8
  literals: 63 variants. Lamports/key/owner reloads are token-equal (GVN folds them); every other reload loses.
- tu8 alone on main: 2,164 @ 27,416; p3u alone: 2,136; p3n alone: 2,135.
- `sw` (curve `is_holder_reward` store before `is_cashback_coin`) on main: 2,177 @ 27,408.
- Basin-hopping cd3 from the near-main variants (RC9 = main, cva/TCF event_authority data-first at -1, RC3/7/8 at -2):
  no move from any base.

## Next ideas

- The and-1 outline would need a native-arm join spelling that keeps #3315's gain without its block move at orig
  0x3c00-0x4800. One that both keeps the basin and matches main's native-arm M has not been found. Each such spelling
  costs one 20 s capture: `e/genes.py` has `RVJ` as the starting point.
- The basin's real deficit is jump-offset and block placement (jM +69..+84 over main, M -10..-21). A jump-target
  placement oracle, which moves whole error blocks of validate to the original's tail positions, would show whether
  any placement reaches main's M before more source spellings are tried.

## Tools (`$OUT/tools`, experiment only)

`capvar.sh` (accepts callable edits), `rx.py` (prints M), `renum.py` (renames numbered IR values so lines can be
moved), `findclones.py`, `cd3.py` (greedy single-read coordinate descent over all clones), `pscan.py`/`eperm.py`
(thread-safe M), `fillg.py` (greedy pure-fill bound), `jm.py` (M / jM / jrM), `jd.py` (mismatched-jump histogram),
`preg2.py` (per-chunk M diff), `batch.sh` (2-stream capture queue). Under zsh, pass a name list as `${=L}`.
The gene library is `e/genes.py`: p3u/p3n/p2/e3/q*, tu8, AC/AV/V1/V2/HK0, RC0-RC11, TL/TLO, TX/SX, F_*, K_*.
