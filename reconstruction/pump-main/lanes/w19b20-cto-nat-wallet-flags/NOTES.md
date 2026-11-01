# w19b20-cto-nat-wallet-flags

Target `0x22a10` `admin_cto::execute`, 27,400 B. Every region except C1 is byte-exact after this change.

- Holder arm owns the 296 check: `if hr&&!holder{289} let (..)=if holder{ if !hr&&!enabled{296} ...`. rustc creates err 289 right after its test, so ISel inverts to `jne r8,0` and it falls through. Validate's relative frequency at 326 falls below 2%, so `to_string` stays out of line at validate's inliner, MemCpyOpt forwards `name` to -0x2b0, and execute inlines `to_string` later. The custom-MIR `e326` and the repay reads go.
- Cashback per arm and the `!is_holder&&st.cashback` test are from w19b25's #4195; native arm from #4184/#4181.
- Sweep arms use early returns, so all returns share one lifetime join and only the final `Ok(amount)` takes the normal path, which threads past the tag test (0x60f0 -> 0x3c68).
