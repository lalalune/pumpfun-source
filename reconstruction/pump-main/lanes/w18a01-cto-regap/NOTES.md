# w18a01-cto-regap: fee store test form (admin_cto 0x22a10)

Base main e60774c17: 0.70021, M 2,338. This change: 0.70051, M 2,339, 27,400 B, 1034 / 1034, zero losses.

The fee store at line 757 now tests the raw tag with `jne r1,0,+1` as the original does at 0x4b88 (was `jeq r1,1,+1`). `if let Some(f)` gives
`icmp eq tag,1`, and a plain `tag!=0` is canonicalised to `icmp eq tag,0` with the arms swapped, so the compare goes through a passthrough.

Oracle, tools and the priced lever table are on `origin/swarm/w18a01-cto-regap`. Ledger approach `regap`.
