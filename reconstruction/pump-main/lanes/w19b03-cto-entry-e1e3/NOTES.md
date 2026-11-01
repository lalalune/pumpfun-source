# w19b03-cto-entry-e1e3: entry regions E1-E3 of admin_cto (0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B.

## Landed cell: mayhem field last (E2/E3)

`CtoState` declares its flags in the original's layout order (mayhem, holder_reward, cashback, quote_locked, holder_enabled,
fee_configurable), the max_fee passthrough is gone, and `st.mayhem` is read and stored right before the `new` tag load. The sk
copy then uses the original's r2/r3 scratch, and the flag stores land at the original's -0xb..-0x10 offsets.

## PDA-first re-priced on the outline base

| variant (source capture, main 864c2b5, M 2,334) | M | E1 exact/full mask | T1 | C1 |
|---|---:|---|---:|---:|
| PDA first, `cr` kept, curve load through a passthrough (d2 = IR i1) | 1,991 | +22/+31 | -242 | -82 |
| PDA first + in-place compare + sunk creator + flags early + hl + entry `new` pieces + creator GEP + hk by value (c3) | 1,886 | +15/+35 | -229 | -56 |

All3 reaches 2,972 (+66) on c3, so the structure is closer, but T1/C1 lose to two RA effects: `%0`'s region split takes r9/r6
instead of r8 once the sharing_config vreg (hint r1, bit 30) evicts `%0` early, and one extra spill interval rotates the T1/C1
spill colours by 8 B (155 tokens). See SUMMARY.json for the table.
