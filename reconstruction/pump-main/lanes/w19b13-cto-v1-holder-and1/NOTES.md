# w19b13-cto-v1-holder-and1: 307 key from the t stack slot (V4)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main 9357bd934: 0.705, M 2,354, 3,179 slots. This change: 0.7059, M 2,357, 3,179 slots, 1034 / 1034, zero losses.

The 307 `with_pubkeys` key words 1..3 now come from the `t` stack slot, as at the original's 0x13f0-0x1410 (V4 +3). MemCpyOpt had forwarded the copy to `new+1`, so main read `[r9+0x18]`, `[r9+0x10]`, `[r9+0x8]`.
- Word 0 stays on `new+1`: a whole copy from `t` ends the `new+1` interval early and costs 87 M.
- `ptp(t)` or `read_volatile(t)` capture `t` (a volatile memcpy counts as a capture), which blocks the creator forwarding: -488 M.
- The word order matters. A 24 B copy from `t+8` then a word load from `new+1` gives the original's load/store sequence. Four word copies schedule the `new+1` load first (-3).

The same lane's holder and-1 form for V1 (PR #4149: `hopt.unwrap_or(false)` after the mayhem test, 12:20 weights on the 289 and shared tests) is on `origin/swarm/w19b13-cto-v1-holder-and1`.
