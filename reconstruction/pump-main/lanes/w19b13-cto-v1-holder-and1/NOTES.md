# w19b13-cto-v1-holder-and1: the original's holder test in V1 and the 307 key from the t stack slot

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main 882755412: 0.70261, M 2,346, 3,186 slots. This change: 0.7038, M 2,350, 3,166 slots, 1034 / 1034, zero losses.

- Validate's `holder` is `hopt.unwrap_or(false)`, computed after the mayhem test, so V1 tests `and64 rX,1` once at the original's place. The 289 and shared-arm tests carry `expect_p(..,0.625)`: BranchProbabilityInfo gives no zero heuristic on a single-bit `and`, so without the weight every later block frequency drops by 0.85, low spill intervals change rank, and T1/C1/W2 slots shift (M 2,287 instead of 2,338).
- The curve store keeps its own `and-1` through `pt8`: merged with validate's it costs 35 M. Execute's early `hopt==Some(true)` stays for the cashback: removing it gives the best skeleton (all-masked +20), but the sret pointer then stays in a register and exact M falls by 322.
- The 306 test is a single-bit tag test, as at the original's 0x738. A byte read on the 306 error path stands in for the original's dead reload at 0x710 (E289's first `jeq` then has the original's displacement).
- The 307 key's words 1..3 come from the `t` stack slot, as at the original's 0x13f0-0x1410 (V4 +3). Word 0 still comes from `new+1`. A whole copy from `t` ends the `new+1` interval early (M -87), and `ptp` or a volatile copy of `t` captures `t`, which blocks the creator forwarding (M -488).

Oracle: post-opt llc edits and slim pre-opt `fx`; the source forms reproduce the IR signatures. Ledger approach `v1-holder-and1`.
