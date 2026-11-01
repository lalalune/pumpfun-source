# w19b25-cto-nat-plan-flags

Target 0x22a10, pinned 27,400 B. On 8774902: 0.92243 -> 0.96346 (M 3,080 -> 3,217), zero losses, 154/3 calls, differential 388/0. Validate V1-V5, J1, J2 are byte-exact.

- 330 tests `!is_holder&&st.cashback`, not `cashback`, so GVN keeps the cashback phi and JumpThreading threads the holder arm past the test (orig 0xb00-0xb38).
- cashback is per shared arm (`st.cashback&&!holder`), which keeps one compare above the shared split (orig 0xd78-0xdb8).
- Marked shim: `cm326`, an empty `#[cold]` marker after 326's error is built. It keeps to_string out of line at validate's inliner (block 0.0279 against the 0.02 cold threshold), so MemCpyOpt forwards `name` to -0x2b0 (orig 0xb48), and execute inlines to_string afterwards. Peel target: the natural source of that block's lower frequency.
- Two of three repay reads removed.

Full notes and tools: origin/swarm/w19b25-cto-nat-plan-flags.
