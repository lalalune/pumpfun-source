# w19b18-cto-skelunion19: natural union on main

Target `0x22a10` `admin_cto::execute`, 27,400 B. Replaces main's steering shims with the natural source. Source = w19a03 natstitch `n2` (no shims, itself built on
w19b08 cleanroom, w19a02 and w19b06's `Plan` return) + w19a08 `n1` (the Some(None) uninit copy) + w19a07 `n0`, `two`, `ds` (native tail, two-test form, dest scope) + one repay read at the holder_enabled test.
Tools, tables and the valley table: origin/swarm/w19b18-cto-skelunion19.

#4174 landed xf2 (M 2,725). This step: Rc trap weights pool_authority lamports 1:5 and mint data 1:200 in the sharing CPI, `hkr` reference parameter for the repay read, read moved before the holder_reward test. A volatile read is a MIR Call and blocks MIR jump threading of `holder` when it sits between the two tests, so that is where a read goes.
