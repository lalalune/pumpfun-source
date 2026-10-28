- 20:52 ROUND 3 START (after a reboot wiped /private/tmp; the run root is now persistent at /Users/shawwalters/fees100-run).
  CreateDonation 163920 is CLOSED (RR/shared/harvest/create-g01, recovered from the lanes' transcripts; coordinator is
  qualifying it on Linux + PR). The ONLY open window is Crank 147944. Frontier for lanes: RR/shared/frontier/w584.
- 21:05 MAIN UPDATED: all open Fees PRs are merged, including our CreateDonation recovery (PR #385,
  research/claude-fees100-create-donation-20261027): main's Fees research is now 584/585; Sweep (#301/#308), ATA stable-Rust
  (#312) and the whole-ELF end-state proof (#317) are also on main. Crank 147944 is the ONLY remaining window. Your w584 tree
  equals what #385 published.
- 21:08 CRANK 147944 IS CLOSED by crank-brute-g01 (rent passed as &UncheckedAccount so the inlined helper's AccountInfo
  carries no noalias scope -> original register allocation around the SyncNative pack). ALL lanes: stop experiments now,
  write your final notes to findings/<lane>.md, and return your structured result with status no_gain and
  "already closed" in the summary (crank-brute: return closed). Coordinator is qualifying it on Linux (585/585 + whole-ELF).
