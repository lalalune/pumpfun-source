# Lane w10r1-admincto-region1of6 (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute`. Angle: region split, region 1 of 6 = original window bytes
`0x0000..0x11d6` (the entry: holder PDA, `shared`, `global_quote`, the `CtoState` snapshot, and
`validate`'s 289/298/306/296 checks up to the start of the holder-arm fee checks and the 307/312 memcmps).
Base: origin/main 917ee615f (1032/347). Builds and IR in `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region1of6/`.

## Region metric (`tools/region.py`)

The original window is split into 6 equal byte ranges. `R1local` aligns the original's region-1
instructions (difflib) against the candidate's first `1.3 x` region bytes: `strict` = scorer-like tokens
(call and lddw immediates masked), `loose` = also registers and stack offsets masked. `errorder` lists the
`line!()` immediates of the error sites in layout order (`tools/errorder.py`).

## Result so far (committed: t06)

| metric | main 917ee61 | this branch (t06) | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,432** | 27,400 |
| size distance | 56 | **32** | 0 |
| win ratio | 0.37637 | 0.35778 | 1 |
| calls | 154+3 | 154+3 | 154+3 |
| R1local strict / loose | 230 / 304 | **237 / 370** | 548 |
| official normalized / raw | 1032 / 347 | 1032 / 347 | |
| gains / losses | | 0 / 0 | |
| unstripped sha256 | 3ca6911a... | 5673f98f... | |

Source changes (all in `execute`'s entry and `validate`'s call):

1. `holder.unwrap_or(false)` and `cashback=!holder&st.cashback`: the original uses the `holder` argument
   only as `x & 1` (orig `0x610 and64 r8,1`), which is what `unwrap_or(false)` lowers to.
2. `CtoState` literal evaluates `mayhem, holder_reward, cashback`, then `quote_locked: global_quote(..)`,
   then `creator`, `max_fee`, ...: the original loads the curve bools (`0xa3,0xa5,0xa2`) before the
   `quote_mint` copy and the `global_quote` memcmps, and copies `creator` after them. Ours now does the same.
3. `validate(.., sharing, holder_key)`: the original copies the sharing key before `holder_key` at entry.

## IR findings for region 1 (llc oracle on captured IR, experiment only)

- The hr==0 block tests `holder`; the original falls through to the non-holder (306) side. Swapping that
  `br` (IR e1) reproduces the original's `jeq holder,0,+1; ja` shape.
- The 306 test in the original is `and 1; jeq ..,0,+1; ja` (trunc of a tag without range metadata,
  "is None" branch first). IR e3 (`xor (trunc tag)` with the error successor first) reproduces it and puts
  the 306 error body between the 289 body and the 289 tail exactly like the original.
- Moving the 296 error blocks after the 306 error blocks in the IR (e7) gives error order
  289 298 330 306 296 326 312 307 (original: 289 298 306 296 326 312 307 330) and R1local 270/407.
- Variants that make 307/312 cold (296 `==false` forms v10/v14, 289 `holder==false` v15, #2370's 296 in the
  holder arm t08) outline `to_string` at 307/312 like the original (26,8xx B).

See SUMMARY.json for the attempt list.

## Round 2: equal-size frontier

#2524 (27400 B, 3297 slots), #2509 and #2528 reach the original size, which makes every normalized window raw (1032).
On #2524 this lane's genes move the size off 27400: c1/c2 (unwrap+lit) 27368, c3 27568, c4 27304, c5 27144, c6 27440,
c7 27344, c8 27488. Recommendation for the stitcher: start from #2524. Use the region-1 genes only together with a knob
that restores 27400, then rank by slots_diff. IR hill-climb on v10 (`irclimb-v10a-best.json`) reached the original's
error prefix 289 298 306 296 once, by block order alone.
