# Lane w10r1-admincto-state (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: state and event shape
(CtoState / AdminCtoEvent construction, field read order, which account each field is read from, copies vs
references, curve-store and event order). Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-state/`.
Ledger approach `state-event-shape`, dedupe keys `0x22a10-main-e61baa9-*-v1`.

## Result (r1, on origin/main 73a4e8379, which includes #2524)

Curve-store/event-side state shape, three behaviour-preserving edits in one block (line count unchanged, no
`line!()` site moves):

1. `curve.can_edit_creator_fee=false` is stored first in the curve-store block (it was stored last);
2. `curve.creator_fee_bps=fee.unwrap_or(old_fee)` (unconditional store of the same value) instead of
   `if let Some(f)=fee{curve.creator_fee_bps=f;}`;
3. `pool_updated` tests `!a.pool.data_is_empty()` before `a.pool.owner==&AMM`.

| metric | main 73a4e8379 | this PR | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 | 27,400 |
| slots_diff | 3,297 | 3,297 | 0 |
| ratio | 0.36010 | **0.36129** | 1 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1033 / 1033 | 1033 / 1033 | |
| gains / losses | | 0 / 0 (raw 0 / 0) | |
| unstripped sha256 | 5de92be1... | 626c747c... | |

Individually on #2524's source: (1) +8 B / 0.36364, (2) +16 B / 0.35969, (3) -16 B / 0.35960; the three
together return to 27,400 B with a higher ratio and the same slots_diff (attempt d8152b0c).

## Findings

- **Size knobs.** Several unrelated state/event edits move admin_cto by fixed amounts. On main e61baa9 (27,344 B):
  `quote_locked` before `shared` +56 (27,400, same as #2509), event fields `new_creator/is_holder_reward/is_cashback_coin`
  from locals +56 (27,400, 3,365 slots, 0.325), A1 literal order +120, collect_old `!shared` -8.
  On #2524: can_edit first +8, old_fee before old_creator +8, collect_old `!shared` -8, pool_updated order -16,
  unconditional fee store +16, CtoState literal global-first +8, fee by reference +152 (ratio 0.382).
  Composing opposite knobs reaches 27,400 again; slots_diff then stays 3,297 unless the entry prefix changes
  (y1/y2: 3,338).
- **holder/cashback representation.** The original computes `holder` as `arg & 1` (an `unwrap_or(false)`/
  `matches!` form) and keeps `holder` and `cashback` in spill slots (`[r10-0x950]`, `[r10-0x958]`, cashback reloaded
  with `& 1`) that are reloaded at the curve store and copied through the sweep exit blocks. Ours
  (`holder==Some(true)`) lowers to `(x & -3) != 0`, an i1 compare that CodeGenPrepare sinks, so the holder test
  is recomputed from the `Option<bool>` argument at each use (curve store: `mov r2,r0; and 0xff; jne`).
  The `unwrap_or` form reproduces the original's `& 1` but costs globally (main: 27,608 B / 0.300;
  with `cashback` after `validate`: 27,288 B / 0.364; on #2524: 27,512 / 0.292).
- **Entry.** The original loads the curve bools (0xa3 cashback, 0xa5 holder_reward, 0xa2 mayhem) before the
  `global_quote` memcmps, copies `new` as SROA scalars (tag, bytes 1..8 as two overlapping u32, 3 x u64, byte 32)
  before the mayhem check, and copies both validate keys by value. The A1 literal order gives the bool order but
  not the rest (on main 27,464 B / 0.356; on #2524 27,304 / 0.347).
- **sweep out-parameter.** `sweep(&ctx,&holder_key,&mut swept)->Result<()>` (t01, 27,504 B / 0.33966) equals, byte
  for byte in llc (oracle w3), deleting the payload phi from `sweep.exit` into `bb38`: the ptrtoint COPY that kept
  `sweep.exit` above the early tail-duplication limit is gone, but the sweep tail is still laid out after the
  post-sweep code. Declaring bump/old/vaultseeds at the top of sweep (to raise the jump-threading duplication cost
  of the exit, keeping Ok paths merged as in the original) is much worse (0.219).
- **Event.** The event construction (Clock::get, key copies, curve reads of 0xa5/0xa3) already matches the original
  instruction for instruction except for registers and stack slots; the event literal evaluation order is free
  (byte-identical) and `emit_cpi!(e.clone())` first is worse.

## Attempts (all zero losses unless noted)

| trial | mechanism | bytes | ratio | slots |
| --- | --- | ---: | ---: | ---: |
| t01 | sweep out-param `&mut swept` | 27,504 | 0.33966 | |
| t02 | A1 literal order on main | 27,464 | 0.35577 | |
| t03/t04 | holder `unwrap_or(false)` / `matches!` (identical) | 27,608 | 0.29991 | |
| t05 | cashback after validate | 27,456 | 0.35433 | |
| t06 | collect_old `!shared` | 27,336 | 0.37612 | |
| t07 | sharing_update `shared.then(..)` | 27,520 | 0.34315 | |
| t08 | target override before sharing_update | 27,584 | 0.36513 | |
| t09 | event from locals | 27,400 | 0.32534 | 3,365 |
| t10 | event fee `unwrap_or(old_fee)` | 27,368 | 0.36930 | |
| t11 | quote_locked before shared (= #2509) | 27,400 | 0.35800 | 3,361 |
| t12 | CtoState by value | identical | | |
| t13 | `let new=new` + clone | 27,752 | 0.32887 | |
| t14 | CtoState block unscoped | 27,312 | 0.21725 | |
| b2524 | #2524 rebuilt (= main now) | 27,400 | 0.36010 | 3,297 |
| u02-u26 | on #2524: A1, collect_old, event locals, fee unwrap, ql, reset:shared, fee/new by ref, holder_key after shared, holder before block, timestamp let | see ledger | | |
| v30-v38 | on #2524: CtoState literal permutations (v33-v35 identical), #2370, out-param, new.take() | see ledger | | |
| v40 | sweep seeds at top | 27,488 | 0.21920 | |
| w01-w08 | holder unwrap + cashback after validate (+ A1 / ql / #2524 / with_signer) | 27,184-27,400 | <= 0.364 | |
| x01-x10 | on #2524: curve store / pool / event order singles | 27,384-27,816 | <= 0.364 | |
| y1/y2 | +8 knob + collect_old `!shared` | 27,400 | 0.36339 / 0.36159 | 3,338 |
| z1-z7, f1, f2 | y4 / #2524 plus further knob compositions | 27,392-27,416 | <= 0.36219 | 3,297-3,355 |
| **y4** | can_edit first + fee unwrap_or + pool empty-first | **27,400** | **0.36129** | **3,297** |

## Next ideas

- Search compositions of the measured size knobs at 27,400 for a lower slots_diff: the entry prefix (bytes 0-304
  match; the first difference is the arg spill offsets [-0x928]/[-0x918]/[-0x8f0]/[-0x938]) decides slots_diff.
- Combine the holder `& 1` form with a size knob set that restores 27,400.
