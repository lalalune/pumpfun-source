# w19b18-cto-skelunion19: natural union on main

Target `0x22a10` `admin_cto::execute`, 27,400 B. Replaces main's steering shims with the natural source. Source = w19a03 natstitch `n2` (no shims, itself built on
w19b08 cleanroom, w19a02 and w19b06's `Plan` return) + w19a08 `n1` (the Some(None) uninit copy) + w19a07 `n0`, `two`, `ds` (native tail, two-test form, dest scope) + one repay read at the holder_enabled test.
Tools, tables and the valley table: origin/swarm/w19b18-cto-skelunion19.
