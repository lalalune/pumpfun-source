# w14a13-cto-sharingslots: sharing-region spill colours and a partial sibling-idiom port (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a05-cto-sibclone (#3217). Ledger approach `sharing-slots`, keys `0x22a10-w14-cef0574-sharingslots-*`
and `0x22a10-w14-b174038-sharingslots-m2-measure-v1`.

## Result

| build | bytes | ratio | slots | norm/raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main cef0574 | 27,400 | 0.63421 | 3,179 | 1034/1034 | |
| this change on cef0574 | 27,400 | **0.63451** | 3,179 | 1034/1034 | none |
| main b174038 (#3250) | 27,400 | 0.63571 | 3,173 | 1034/1034 | |
| this change merged on b174038 | 27,400 | **0.63661** | 3,173 | 1034/1034 | none |

Runtime differential: 363 cases, 0 mismatches. Unstripped sha256 prefix `bb53168d6ce7111e`.

The change has three semantics-preserving edits:
1. Sharing CPI `program:` is `a.pump_fees.to_account_info()` (the sibling idiom) instead of the literal `AccountInfo{..}`
   (subset `u_pr`: -16 B, 0.6335 alone).
2. Event `is_holder_reward: holder` instead of reading `a.bonding_curve.is_holder_reward` back (+8 B).
3. Curve update `curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);` instead of `if let Some(f)=fee{..}` (+8 B).

## Sharing CPI subset screen (raw-IR capture + opt/llc oracle, cef0574)

All 31 non-empty subsets of the 5 literal accounts (pa=pool_authority, gl=global, mi=mint, ea=event_authority,
pr=program) turned into plain `.to_account_info()`. Selected rows (fm masks frame offsets and jumps; rm also masks registers):

| subset | bytes | ratio | fm | rm |
| --- | ---: | ---: | ---: | ---: |
| main | 27,400 | 0.63421 | 0.72289 | 0.84661 |
| pr | 27,384 | 0.6335 | 0.7228 | 0.84837 |
| pa | 27,400 | 0.63241 | 0.72798 | 0.84721 |
| pa,gl | 27,400 | 0.63152 | 0.72768 | 0.84781 |
| pa,gl,ea | 27,376 | 0.6279 | **0.7337** | 0.84789 |
| pa,ea,pr | 27,352 | 0.62339 | 0.72984 | **0.86687** |
| all 7 (w14a05 s1) | 27,368 | 0.61841 | 0.72122 | 0.85971 |

`pool_authority`, `global` and `event_authority` as `to_account_info()` give the highest frame-masked structure (+0.011 fm).
They lose positional tokens only in orig 0x3800-0x4800, through the spill colours below. Composite screen: 5 subset bases
x 16 tail knobs (`tools/knobs13.py`, the w13a34 knobs adapted to cef0574) plus 12 knob pairs. Only `pr + ev_hr_local + cu_fee_unwrapcur` beat main.

## Colour map of the sharing region (`tools/sscmap.py`, debug llc `-debug-only=stack-slot-coloring`)

Spill FI k sits at `r10-(0x8d0+8*(k-177))`. Colours are assigned in weight order, so the region's clone temporaries
(2-site, weight 0.0053) take the first colours that no crossing interval holds. Main and s1 have the same map: the first
clone temporary sits at colour 197 (0x970). In the original the run starts at 195 (0x960).

- Crossing the region: the original has 8 spilled intervals (acct ptr 0x8d8, sret 0x8f0, ctx 0x938, fee tag 0x8e8, fee value 0x930,
  sharing tag 0x8f8, cashback 0x950, holder 0x958). Ours has 10: holder arg/cashback phi SS#183 (col 178, w 2.46, which pushes the accounts
  pointer to col 179), acct ptr SS#180, sharing tag SS#186 (col 180), sret, holder pieces SS#184 (col 182) and SS#185, fee tag SS#181,
  fee value SS#182, ctx SS#179 and **swept SS#189 (col 196)**.
- The two extra ones are **swept**, which the original keeps in r9 across the region (w14a06's coalescing problem), and
  **one extra holder/cashback piece**. The original materializes holder (0x958, `and 1` at the curve store) and cashback (0x950)
  as two bools. Ours recomputes holder as `[0x8f8]&[0x908]&1` at the curve store, and the cashback phi is coalesced with the holder
  argument's entry spill.
- The original also reuses two dead payload-piece slots (0x948, 0x900: the sharing `val` pubkey pieces copied at 0x3d48/0x3d58)
  as region temporaries. Ours copies `val` from aligned allocas, so it has no such slots.
- A what-if that shifts s1's region temporaries by -0x18 gives only 0.63429 at 27,368 B, so the colour shift is not
  worth chasing on its own. It follows the swept, holder and cashback RA state, not the sharing source.

## Next ideas

- pa/gl/ea `to_account_info()` (+0.011 fm) on top of a state where swept sits in a register: retest after any swept-coalescing landing.
- Materialize holder/cashback as two bools before the sharing CPI (one fewer crossing interval, and the accounts pointer back
  on colour 178). This is the holder lanes' territory (w14a10, w14a09).

## Landed

#3257 was merged by land.py as `1b0ae7021`: admin_cto went from 0.63571 to 0.63661 at 27,400 B with zero losses.

## After landing (branch `swarm/w14a13-cto-sharingslots-2`, notes only)

Every screen below used the raw-IR oracle on the main named in the heading. Knob strings for 1b0ae70 are in `tools/knobs_new.json`.

**On 1b0ae70 (0.63661).**
- The remaining literals {pa, gl, mi, ea} and the sweep TCF `pump_amm` literal clones (t1 = CpiContext program argument,
  t2 = accounts program field) were screened as singletons and pairs (21 trials). None beat main. The best were pa,gl at 0.63571
  (fm 0.72888) and gl at 0.63511.
- 16 tail knobs were screened on main and on pa,ea. Only `ev_nf_inline` / `nf_clean` (event `new_creator_fee_bps` read back from
  the curve, -24 B) scored higher: 0.63689 at 27,376 B.
- That gain is a size artifact. `ratio = 2M/(|a|+|b|)`, so dropping 3 tokens alone adds about +0.0005, and per-bin matches
  barely move (+1/-1). None of the 30+ fill combinations that bring it back to 27,400 B beat main (best 0.63391). These include the w11 catalog,
  the w13a34 knobs, Clock locals and `pargs` forms.
- Rule of thumb: when comparing an off-size oracle result with main, subtract about 0.00019 per 8 B removed.

**On d2d1875 (0.6417, after #3267 / #3272 / #3281).** pa, gl, pa+gl, t2, pa+t2 and gl+t2 are all below main
(0.62612-0.63871). Main's fm is now 0.73367, so the subsets' earlier fm advantage is gone.

## Status

The angle is exhausted at source level. The sharing-region colour offset is set by the RA state that crosses the
region (swept spilled instead of in r9, plus one extra holder/cashback piece). No sharing-CPI spelling changes that state.
