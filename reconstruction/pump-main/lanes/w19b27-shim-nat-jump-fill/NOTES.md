# w19b27-shim-nat-jump-fill

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B.

- #4186: volatile `holder_key` reads before the mayhem test, M 3,065 to 3,080.
- The 330 test: the original tests the raw cashback byte with `jeq r1,0` (own `icmp eq`, one use). Ours shared one multi-use `icmp ne` with the Plan phi, so the block got `jne +1; ja far`. `if !holder&&pt8(330,st.cashback as u8)!=0` keeps the holder threading and gives that compare its own use: main fad4cb028 M 3,104 to M 3,171 at 27,400 B with the line 289 read removed (sha f3a2bd1903cea320, losses [], raw_losses []).
