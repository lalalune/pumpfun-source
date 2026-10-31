# w14a91-cto-curvestorereg: q7 landed at 27,400 B; who holds r6/r8 over the curve-store block in the original

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continue w14a84-cto-raprio (#3419, 5b') and w14a82-cto-walletweight (#3409, next idea 0). Land q7 (the event's
`is_holder_reward` re-reads `a.bonding_curve.is_holder_reward`, as the original does at 0x4fe0) by finding the source lever
for its missing register decision.

Bases: main ecea702 (#3430, 0.67076 / 3,123) for the first screens, then main 963d1ee (#3437, 0.67226 / 3,123).
Oracle: raw-IR capture + opt + llc (`capvar.sh` / `rx.py`, w14a82/w14a84 tools; `eq_main` true on the unedited capture on
both mains), plus a rebuilt private RAPRIO llc (`llc-patch/build.sh` from w14a84) for forces and colour maps.
Ledger: approach `curvestorereg`, keys `0x22a10-w14-{ecea702,963d1ee}-curvestorereg-*`.

## Result: landed (#3480, 13fe4536b), admin_cto 0.67226 / 3,123 -> 0.67256 / 3,123 at 27,400 B

measure.sh on 963d1ee: 1034/1034 normalized and raw, zero losses; differential 363 cases, 0 mismatches;
unstripped sha256 `cec841bd60cc0022...`.

Change (line count unchanged):
- **q7**: `is_holder_reward:a.bonding_curve.is_holder_reward` in `AdminCtoEvent` (orig `ldxb r5,[r3+165]` at 0x4fe0). -8 B on 963d1ee.
- **csw**: the curve stores `is_holder_reward` before `is_cashback_coin`, the original's store order (`stxb [r1+165]` at 0x4b68
  before `stxb [r1+163]` at 0x4b78). Ratio-neutral, now matches the original's order locally.
- **sm reverted**: the sharing CPI is `match sharing_update{Some(val)=>{..}None=>{}}` again (+8 B), which repays q7.

| 963d1ee | bytes | ratio | slots |
| --- | ---: | ---: | ---: |
| main | 27,400 | 0.67226 | 3,123 |
| q7 | 27,392 | 0.67116 | |
| q7 + match sharing (G1) / + rent_epoch re-read (G2) | 27,400 | 0.67256 | 3,123 |
| **q7 + csw + match sharing (G3, landed)** | 27,400 | **0.67256** | 3,123 |
| q7 + csw + rent_epoch re-read (G4, measured zero-loss) | 27,400 | 0.67256 | 3,123 |
| q7 + match fee + both #3437 -8 B genes reverted (G5/G6) | 27,400 | 0.67226 | |

On 963d1ee q7 no longer needs the w14a84 force: #3437's `nf` local already spills old_fee at its definition (as the original
does at 0x4b50) and the curve-block piece of the accounts pointer `%0` already sits in r6. The best single RA force on q7 at
27,400 is now a sharing clone-run `rent_epoch` piece (`%2254 -> r4`, also 0.67256), not a curve-block value.

## 1. What holds r6 / r8 over the curve-store block in the original (orig 0x4a80-0x5030)

| reg | original | ours (q7 on ecea702) |
| --- | --- | --- |
| r6 | the `sharing_update` tag (`Option<Option<Pubkey>>` 2/0/1 phi): `mov r1,r6; and 255; jne 2` at the sharing match 0x3d00, the None arm jumps to 0x4aa8 with r6 = tag; Some arm reloads `ldxdw r6,[r10-2296]` at 0x4a90; live to the event `and64 r6,255; jne r6,2` at 0x4f18. On the pool path r6 is reused for the accounts pointer (0x4c50) and the tag is reloaded at 0x4d48 | old_fee (`%288`, from bb38 to the event store) |
| r8 | **nothing over the curve block**; pool_updated from 0x4c40 (`mov r8,0`, msg arm) / 0x4e30 (`mov r8,1`, after the pool CPI) to the event store 0x5028 | the accounts pointer piece, loaded once at 0x4a70 and kept |
| r3 | accounts pointer, reloaded for the block (`ldxdw r3,[r10-2264]` at 0x4ab8) | cashback |
| r9 | swept, live to the event (`stxdw [r10-536],r9` at 0x5030) | pool_updated / the pool-CPI holder arg (re-read `ldxb r9,[curve+165]`) |
| spill | old_fee (`stxdw [r10-2272]` at 0x4b50, reload at 0x5018), holder bool `[r10-2384]` (curve store and pool-CPI arg r4) | tag, swept |

So the w14a84 "r8 occupant" does not exist: the original's r8 is free over the block, and the accounts piece is not in r8
because the original reloads it per block into a scratch register. The original's r6 occupant is the tag. This agrees with
w14a12-cto-tagreg (#3251), which priced the tag-in-r6 residual at +0.0027 at most.

Why ours spills the tag (debug greedy on q7+fm, ecea702): `%59` (tag phi, MOV 2 / MOV 0, weight 1.33e-06) takes r6 at step
318 and is evicted at step 330 by `%60` (the sweep-gate flag, MOV 0 / MOV 1, weight 4.6e-06). old_fee `%288` (1.37e-06)
takes the free r6 at step 469. When `%59` is region-split at step 1213, its tail piece `%1716` (8.99e-07) is lighter than
`%288` and spills.

## 2. Screens (rx oracle; bytes, ratio)

ecea702 (main 0.67076):

| key | form (on q7 unless noted) | bytes | ratio |
| --- | --- | ---: | ---: |
| q7 | event re-reads curve `is_holder_reward` | 27,384 | 0.66946 |
| po | `pool_updated = owner==AMM && !data_is_empty()` (the original's order: memcmp at 0x4be8, data_is_empty at 0x4c10) | 27,424 | 0.63333 |
| ph | pool-CPI holder arg `holder.unwrap_or(false)` (the original passes the spilled holder bool) | 27,416 | 0.63133 |
| poph | po + ph | 27,416 | 0.63193 |
| csw | holder store before cashback | 27,384 | 0.66946 (local shape = orig) |
| fm / fm2 / fm4 | `match fee{Some(f)=>..,None=>{}}` (and None-first, `=>()` spellings) | 27,376 | 0.67016 |
| fm3 / fm5 / fm6 / fm7 | `if fee.is_some()`, `if let..else{}`, `if fee.is_none(){}else{..}`, `_=>{}` | 27,384 | = q7 |
| pupre / popre | pool_updated computed before the curve block | 27,472 / 27,496 | 0.63067 / 0.60467 |
| q7+fm + 10 size knobs | w14a82 kn2 catalog (interrupted when main moved) | | best = fm |

963d1ee (main 0.67226): q7 0.67116 @27,392, q7+fm 0.67096 @27,384, fm alone 0.67056 @27,392, q7 + each of 41 kn2 knobs
(best 0.67116 at 27,392; nothing lands at 27,400 above main), po 0.63263, ph 0.63063, composites F1-F8 (q7 + csw + po, + ph,
+ tuple holder `hb` for store and pool arg, - nf) 0.570-0.634, q7 - nf 0.67026 @27,368.

- The fee test: the original is `jne tag,0,+1; ja +3` (Some branch taken, layout successor after the `ja`), q7 is
  `jeq tag,1,+1; ja +3` and fm is `jeq tag,0,+3` without the `ja`. InstCombine canonicalizes every `is_some` / `is_none` /
  `if let` spelling to the same compare; only `match` changes it, and to fm's shape, not the original's.
- po matches the original's pool test shape locally, but its -0.04 is not placement: the MBB order after `block-placement`
  is identical to q7's (349 blocks, `-stop-after=block-placement` diff), and branch weights on both pool branches change
  nothing. It is a colouring cascade over the tail and the wallet region.

## 3. RA probes (private llc, q7+fm on ecea702)

| probe | ratio | bytes |
| --- | ---: | ---: |
| q7 + `%1681` (curve-block `%0` piece) -> r6 (w14a84 5b' lead, re-found on ecea702) | 0.67376 | 27,400 |
| q7 + `%1683` (event `%0` piece) -> r6 | 0.67516 | 27,384 |
| fm + `%1683` -> r6 | 0.67586 | 27,376 |
| any tag `%59` piece -> r6 (17 forces) | <= 0.67046 | |
| `%60` (sweep gate) -> r7 / r8 / r9 / bottom priority | 0.49-0.61 | |
| `%288` (old_fee) spill / r7 / r8 / r9 | 0.595 / 0.609 / 0.665 / = fm | |
| IR: old_fee loaded at the event (semantics-breaking price) | 0.59236 | 27,392 |

Putting the tag in r6 as the original does is not reachable by a local decision: every force that moves it cascades.

## 4. After landing (#3480, main 13fe453: 0.67256 / 3,123)

`eq_main` holds on the unedited capture of 13fe453. Keys `0x22a10-w14-13fe453-curvestorereg-*`.

| key | form | bytes | ratio | best RA force (private llc) |
| --- | --- | ---: | ---: | --- |
| m_fm | `match fee{Some(f)=>..,None=>{}}` | 27,392 | 0.67086 | `%1684 -> r6` (event `%0` piece): 0.67356 @27,392 |
| **H1** | m_fm + pool_authority `rent_epoch` re-read (+8 B) | 27,400 | 0.67226 | **`%1685 -> r6`: 0.67496 @27,400 (+0.0024 over main)**; 3 forces 0.67825 |
| H2 | None-first fee match + rent re-read | 27,400 | 0.67226 | |
| J1 / J2 | pool CPI args inline (no `pargs` tuple), on H1 / on main | 27,432 | 0.630 | |

The lead in H1 is a register swap at the event. Ours: pool_updated (`%1650`, `mov 0` / `mov 1`) takes r6 by evicting
old_fee, and the accounts pointer piece `%1685` keeps `%0`'s r8. The original has pool_updated in r8 and reloads the accounts
pointer into r6 (0x4f38) after the tag test frees r6.
- Forcing pool_updated directly loses: r8 0.587, r7 0.582, r9 0.669, top priority 0.604, bottom priority 0.667.
- Only the `%0` piece -> r6 force gains. With it pool_updated lands in r9, where the original keeps swept.
- The root cause is again the tag-in-r6 colouring (section 1, w14a12). In the original, pool_updated cannot take r6 or r7
  because the tag holds r6 until 0x4f28.

## 5. Next ideas

- H1 (match fee + `rent_epoch` re-read) is at 27,400 and is RA-recoverable to 0.67496 by one decision (`%0`'s event piece in r6
  instead of pool_updated). A source form that makes pool_updated lose r6, or that makes r6 busy from the pool join to the
  event, lands about +0.0024. The original does it by keeping the sharing tag in r6.
- The faithful tail forms (po, holder bool for the curve store and the pool arg, fee `jne 0` polarity) all match the original
  locally and lose through RA cascades. They are the original's code; they need the swept-r9 / tag-r6 colouring
  (w14a12, w14a69) to pay off, so try them again on any base that moves swept into r9.
- Tools (`$OUT/tools`, experiment only): `sbsr.py <fn.bin> lo hi` side-by-side orig/candidate with register-masked alignment;
  `fam.py <ra.log> <root>`; `pair.sh` (two capvars); `knf.sh` (knob screen on any base edit set); `rec.py` (ledger row
  from an rx result).
