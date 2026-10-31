# w14a55-cto-ifletrepay: s_iflet paid back inside the sharing CPI

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 63308119b (0.65698, 3,193 slots, M 2,193). Ledger approach `ifletrepay`, keys `0x22a10-w14-6330811-ifletrepay-*-v1`.
Continues w14a34-cto-curvetail (#3338) next idea 1.

## Result (landable: same ratio, 11 fewer slots)

| | main 6330811 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65698 | 0.65698 (M 2,193 = 2,193) |
| slots_diff | 3,193 | **3,182** |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `1aa5bedc0fe94b7e81a6af40d9b1020eaa0af62853333644629d8ffc8592148b` |

land.py ranks admin_cto by (size, -ratio, slots), so an equal ratio with fewer slots counts as closer.

## Change

1. s_iflet: `match sharing_update{Some(val)=>{..}None=>{}}` becomes `if let Some(val)=sharing_update{..}`. This gives the
   original's single `jne r7,2` CPI-return branch after `admin_cto_sharing_config` (main had `jeq r7,2,+1; ja`), -8 B.
2. Paid back with +8 B inside the sharing CPI clone run (where ours is 9 instructions shorter than the original):
   the pool_authority literal reads `rent_epoch:a.pool_authority.rent_epoch` through the account path instead of `x`.
   The read comes after the two Rc stores, so the AccountInfo pointer is re-loaded (the original reloads per clone).

## Screens (all on 6330811, s_iflet base 0.65678 @27,392, M 2,192)

| family | count | best +8 B partner (27,400) | result |
| --- | ---: | --- | --- |
| pscan `place` (729 each) on 7 sharing clones (ctx program, pool_authority, authority, global, mint, sharing_config, program literal) | 5,103 | authority 120002 0.65339; global 221011 0.65099; sharing_config 222021 0.64769 | far below main |
| pscan `pp` at current and top-6 +8 B placements | ~1,000 | 0.65339 | below |
| re-read singles (field read via the account path after the Rc stores) | 56 | pool_authority rent 2,193 / 3,182 slots; program-literal data 2,193 / 3,191 | **tie M, fewer slots** |
| re-read pairs | 1,540 | 46 variants at M 2,193; best slots 3,182 (all contain pool_authority rent) | no M gain |

- Re-reads placed before the Rc stores are CSEd (no change). Only reads after a store give +8 B.
- The s_iflet loss on 6330811 is pure jump distance (segdiff: -1 in segs 55/135/145/156, +1 in 11/12/67; seg 72 is unchanged).
  The re-read partner restores the per-segment match counts exactly (segdiff delta 0 in every segment).
- Source forms reproduce the IR oracle byte for byte (`sx_rent` = IR `%x:rent`, `sx_pdata` = IR `%x21:data`).

## Tools (`tools/`, experiment only)

- `reread.py <mn.ll> <out.jsonl> X... [--pairs]` (JOBS=file for listed combos): post-opt re-read oracle for x-bound
  AccountInfo literals. `rrdump.py` writes one variant's m.ll / fn.bin. Needs w14a34's `rx.py` next to it.
- `mcount.py` (M per fn.bin), `drift.py` (orig->cand offset drift), `fl.py` (raw listing of fn.bin), `psum.py` (pscan summary).

---

# Part 2 (branch -2): after #3369 landed (main c3e5b51, then 2e1379d)

Ledger keys `0x22a10-w14-{c3e5b51,2e1379d}-ifletrepay-*-v1`.

## Result: one zero-loss +1 M lead on c3e5b51, overtaken by #3372; nothing beats 2e1379d (0.65728, M 2,194)

| variant | base | bytes | M | ratio |
| --- | --- | ---: | ---: | ---: |
| main | c3e5b51 | 27,400 | 2,193 | 0.65698 |
| **sas_powner**: su_tafter + s_amm_present + sharing arm back to `match` + program literal `owner:a.pump_fees.owner` | c3e5b51 | 27,400 | **2,194** | **0.65728** (3,222 slots; measure.sh 0 losses; differential 363/0; sha `ce26de7c..`) |
| sas_adata_pdata (same + authority and program `data` via the account path) | c3e5b51 | 27,400 | 2,194 | 0.65728 |
| main (#3372: wallet `!is_writable` -8 B + program data re-read +8 B, w14a43) | 2e1379d | 27,400 | 2,194 | 0.65728 (3,192 slots) |
| merge of sas_powner into 2e1379d (both program re-reads) | 2e1379d | 27,400 | 2,194 | 0.65728 (3,215 slots: worse) |

The two routes to 2,194 do not stack: #3372's -8 B wallet knob uses the size budget the su_tafter bundle needed.

## su_tafter is still the largest local lead (w14a38): +4 M at -40 B on 2e1379d

| on 2e1379d | bytes | M |
| --- | ---: | ---: |
| su_tafter (`}else{let r=(false,Some(args.0),true);target=st.creator;r}`) | 27,360 | **2,198** |
| + s_amm_present (+16) | 27,376 | 2,197 |
| + wl_writ_eq (undo #3372's `!`, +8) | 27,384 | 2,196 |
| + sharing `match` (+8) | 27,368 | 2,194 |
| + k3 / n_ensiflet / s_rent_get | 27,368 / 27,360 / 27,360 | 2,188 / 2,182 / 2,198 (same) |
| + two-stage `sharing_update` copies (6 spellings: `let su=Some(..)`, `let r2=r`, holder-arm tuple let, `let v=args.0`, `let c=st.creator`, `(r.0,r.1,r.2)`) | 27,360 | 2,198 (byte-identical) |

- **Pure-size bound** (`tools/junkgreedy.py`, greedy 8 B junk insertions with every crossing jump fixed): su_tafter + 40 B of
  junk reaches **M 2,200 at 27,400 (0.65927)**. The first two junk slots gain +1 each (entry 0x190 and 0x140); the
  rest are free anywhere near the entry. So su_tafter lands as soon as ~40 B of faithful code costs at most 5 M.
- 75 w14a31 knob edits that still apply, stacked on su_tafter + s_amm_present: 62 are byte-identical; the size-adding ones
  are wl_writ_eq (+8, -1 M), wl_ixlit (+32, -15), wl_native_deref (+80, -13), ev_bc_deref, s_native_deref, tp_pargs_hold,
  wl_infos_ref (all large losses). v7c and its combinations collapse (M ~2,008).
- Re-read / RM beams (`tools/beam.py`, K 16-18, W 10-14, 3-5 rounds) toward 27,400 from each su base: best 2,191
  (su), 2,194 (su+am+sm, su+am+wl), 2,193 (su+am). Every sharing-arm re-read costs 1-3 M on the su bases, against 0
  on main. su + 40 B therefore stays at or below main with today's knobs.

## The re-read knob (+8 B per field read through the account path after the Rc stores)

- `tools/reload2.py`: ADD (`a.<acct>.<field>` inside an `x`-bound literal = re-load the AccountInfo pointer before that
  field) and RM (path read -> `x` read) over all 9 x-bound literals (5 sharing, 4 TCF). Reads before the Rc stores are
  CSEd away (no change).
- On main it is the cheapest +8 B partner known: 0 M when it repays s_iflet (#3369), 0 to -1 M elsewhere in the
  sharing arm. #3372 used the same form (program `data`) to repay its wallet knob.
- On 2e1379d the remaining +8 B ADDs cost 5-6 M (x21:24 -5, x21:0 -6) and the -8 B RMs cost 2-6 M. Single re-read
  levers are used up on main.

## Other screens

- Line-660 `require!(token_raw_amount(..)?==0)` (ours `jeq r7,2,+1; ja +28` where the original has one `jne r7,2,+1990`):
  match / let / map / `!=` / `0==` spellings are byte-identical (the `?` lowering is MIR-normalized); require_eq! 0.4777.
- validate: fee `if let` 0.63082 @27,408, new let-else 0.65249, new `match` and fee None-first byte-identical.
- shift.py on c3e5b51: removing the spill store at main 0x16e8 alone is +5 M (gains orig 0x810/0x8f0 validate jumps
  and 0x1818-0x18c8). That is the su_tafter region, which explains part of su_tafter's +4.

## Next ideas

1. su_tafter (+4 M at -40 B) is the lead to land. It needs ~40 B of faithful code that costs <= 5 M. The junk bound
   says code added near the entry (0x0-0x200) or anywhere before 0x1600 costs nothing in jump distance. Look for
   faithful entry-region forms (CtoState copy, holder bool spill, `shared` chain) that add instructions.
2. Re-screen the re-read ADD lattice whenever a landing changes the sharing arm. It is a zero-cost +8 B partner more
   often than any other knob.

## Part 3: main 304b03a (0.65788, M 2,196; #3361 landed su_tafter + amm_present + pump_fees owner re-read)

- w14a53 (#3361) landed the su_tafter + s_amm_present + program-owner re-read bundle (this lane's c3e5b51 lead) on 0d945ea.
- On 304b03a, dropping #3369's pool_authority rent re-read is a **free -8 B** (M 2,196 @27,392, source-confirmed `x_rmx`).
  The junk bound for one +8 B on that base is +1 (at 0x180/0x190, the `shared` chain, or 0x1f70-0x1fa0, the TCF arm head
  after the two coin_creator_vault_ata `data_is_empty` calls). So a zero-cost faithful +8 B there would land +1 M.
- Screened partners, none free: the re-read lattice (best = putting the rent re-read back = main; x18:16 -1),
  `shared` spellings (`data_len()!=0` 1,972, `*owner==FEES` no size change, `*key==` 2,188 @27,312, operand swap 2,190,
  `&&` reorder 1,965), TCF else-if gate (`data_len()!=0` 1,917, `amm_present` 1,689).
