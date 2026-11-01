# w19a10-shim-clcarry: one trap weight on the first clone of the sharing CPI

Target `0x22a10` `admin_cto::execute`, 27,400 B. Tools and the cl and nocr2 tables are on `origin/swarm/w19a10-shim-clcarry`.

C1's register order hangs on one eviction: when the mint data pointer `%348` is dequeued, the lightest occupant decides who spills. By size the first clone's lamports pointer is 4.5% lighter than its data pointer, so r1 is evicted and the mint clone pointer takes r3. A 1:9 weight on the first clone's lamports trap (`aicl::<9>(a.pump_fees.as_ref())`) makes the data pointer lightest, as in the original. The three other trap weights are then not needed and are removed.
