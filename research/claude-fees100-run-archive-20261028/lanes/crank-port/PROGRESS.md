# crank-port PROGRESS (window 147944 crank_donation_fee_pda) — resume point
Lane dir: RR/lanes/crank-port. src/ = pristine w584 clone (native rebuild == w584 sha 45d10d76, out/base-symbols.so).
v/<name>/ = variant trees (APFS clones of src); slots/t1..t4 = target dirs (one build per slot at a time).
tools/run.sh NAME SLOT = nbuild + cs.py score + measure vs out/base; appends to out/scores.log.
tools/cs.py CAND.so [--diff] [--raw] = fast crank scorer (cached original listing an/orig-147944.json).
Findings log: RR/shared/findings/crank-port.md.

## Log
- 20:58 lane set up, baseline verified (1862i/15224B mask 0.6348 raw 0.2760 depth 2512).
- 21:05 p0 = PR #304 crank line + PR304 Event::data + in-crate `CrankInfoExt` trait (unsafe lifetime-extended as_ref +
  reload_from_info via set_inner), no anchor patch: 1947i/15952B mask 0.9494 raw 0.5876 depth 2464 (= PR304 numbers).
- 21:08 v08b = crank-b v08 reconstructed on w584 (helper `donation::sync_native_excess` at donation.rs:12, direct receiver
  `DonatePubkeyConfigIdWithPayerV1{..}.invoke_signed(..)` temp, direct mint condition, anchor-form Event::data):
  1950i/15976B mask 0.9641/74 raw 0.9533/110 depth 2168, measure 580 lost [] (== crank-b v08). v08 (with `let mint` +
  `let relay_accounts`) was mask 0.9421 depth 2392: event (192B) can't share the receiver slot when relay_accounts is a named local.
- 21:20 KEY (llc loop, tools/llcx.py + irx.py, exact reproduction of rustc crank): v08b's IR + ONE extra load = EXACT original
  crank (x6/x7: re-load the rent key `load ptr, ptr %_17` at the start of the infos rent clone instead of reusing the meta's
  rent key load). I.e. in the original the rent AccountInfo memory is NOT noalias-protected (rent ptr not a fn param);
  donation key IS CSE'd (noalias param). Next: source forms where rent's &AccountInfo is a local loaded early (before Rent::get).
- 21:22 v09a (`rent:&UncheckedAccount` + `let rent:&AccountInfo<'info>=rent;`) and v09b (`rent:&UncheckedAccount`, call site
  `&ctx.accounts.rent`, `rent.key()`/`rent.to_account_info()`): measure 581, gained [147944], lost [] — whole symbols ELF
  sha e77815918e6e022d... == crank-brute-g01 == crank-transfer-g01 (independent convergence).
- 21:24 DIRECTIVES 21:08: Crank already CLOSED by crank-brute-g01. Stopped experiments per directive; no duplicate harvest.
  LANE DONE (status no_gain / already closed).
