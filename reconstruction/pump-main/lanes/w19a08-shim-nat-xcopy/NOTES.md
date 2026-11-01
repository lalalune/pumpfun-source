# w19a08-shim-nat-xcopy: cashback through the target tuple

Target `0x22a10` `admin_cto::execute`. Full notes and tools: `origin/swarm/w19a08-shim-nat-xcopy`.

- Cashback is the third value of the target tuple: `false` on the holder arm, the `st.cashback` byte computed at the end of the non-holder arm, before the shared test (orig 0xd78).
- The 330 test reads `!is_holder&&st.cashback`, not the plan's value. GVN therefore cannot fold the plan's phi to `false` past the test, and r5 flows through the fee checks into `[-0x958]` as in the original.
- A passthrough on the byte keeps the compare in its block (no instruction).
- The last repay read comes out: the source is exactly 27,400 B by itself.
