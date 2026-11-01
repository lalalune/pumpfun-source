# w18a03-shim-rescreen-ann

Target `0x22a10` `admin_cto::execute`, `programs/pump/src/creator/admin_cto.rs`, pinned at 27,400 B. Tools, screens and the full notes are on `origin/swarm/w18a03-shim-rescreen-ann`. Ledger approach `shim-rescreen-ann`.

## Event error tails: a byte read where the original copies the error payload

Measured on main `34c871838`: 0.70291 -> 0.70320, differing slots 3186 -> 3177, 27,400 B, calls 154 / 3, windows 1034 / 1034, losses and raw losses empty.

The original ends both event error paths (`Clock::get()?` and the self CPI's `?`) with `mov r9,r1; ja`, at 0x54e0 and 0x55a8. Main has no token there, so three jumps across them are one or two slots short (0x53d8, 0x5470, 0x54e8). A drop guard, forgotten on the Ok path, puts one byte read on the shared Err path. Tail duplication copies it into both tails, so it costs 16 B, repaid by the two reads at the sweep gate (line 647). The jumps at 0x22f8 and 0x3c10 move the other way.

The read is not the original's `mov`. The payload itself is r9 in the original and r8 in main at 22 tokens, and the two tails hold it in r1 first. Those tokens stay open.
