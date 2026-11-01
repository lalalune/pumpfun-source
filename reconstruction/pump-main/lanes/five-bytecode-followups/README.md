# Five-area bytecode investigation and current-main checkpoint (2026-10-30)

This packet records **1,032/1,035 normalized and 347 raw windows** for upstream
`9b216213`, adds a compiled-candidate replay of the existing 120 swap fixtures,
and publishes 52 source trials with exact patches and measurements. **It changes
no program source and claims no newly discovered match.** Three windows remain
unmatched; the investigation did not finish their reconstruction.

## Measured state

The historical comparison base is `5265cb3c2a4cb7bca51cb535ad2faa651c8121c3`
(1,032 normalized / 337 raw). Its fresh rebuild reproduced the earlier isolated
`4ba3b6f8` build's source fingerprint and ELF hashes. The current source revision
is pinned in `MEASUREMENTS.json` as `candidate_commit` (`9b216213`).

| Original target | Original bytes | Current-main bytes | Diagnostic ratio | Remaining |
| --- | ---: | ---: | ---: | --- |
| create-v2 `0x1e7c0` | 15,576 | 15,576 | 0.99892 | Four normalized slots |
| Admin CTO `0x22a10` | 27,400 | 27,344 | 0.37637 | Unmatched |
| swap hop `0x5b3b0` | 18,584 | 18,584 | 0.85352 | 1,023 positional slots differ |

Current main preserves every historical normalized/raw membership and adds ten
raw memberships already landed through #2403.
Those are upstream gains, not gains from this PR. The call-target audit retains
all 1,032 normalized windows on both builds and reports no hidden mismatch;
its unmatched-target pairings remain assumptions. Neither the scorer's masked
matches nor this audit proves whole-program identity.

## Five work areas and outcomes

1. **Create-v2:** four slots remain. Tested native-result adapters, inline
   result projections, byte/scalar split return layouts, all 23 alternative
   `QuoteSource` variant orders, and explicit `repr(u8)`/`repr(C)`. None improved
   the strongest baseline. Source remains unchanged.
2. **Admin CTO:** independently reproduced #2416's candidate, then tested cold
   error adapters, Result joins and branch likelihood hints. They either retained
   its result or regressed matches. No new mutation was accepted.
3. **Swap hop:** independently reproduced #2403. Result closures around buy work
   changed inlining and lost two matched windows; the first variant also failed
   the borrow checker. None is retained. The exact rejected patches are saved.
4. **Integration:** tested #2403 + the then-proposed #2416 source: 1,032/347,
   no losses, passing 363 Admin CTO and 120 swap comparisons. A clean build
   reproduced its ELF hashes. During publication review, #2403 and #2412 landed,
   while #2416 was merged **notes-only**. Maintainers rejected #2416's source
   because its improved ratio moved the function farther from the original size.
   We therefore removed that proposed production diff and rebuilt accepted main.
5. **Checkpoint:** this packet binds the accepted-main source, tool identities,
   complete 1,035-window census, call-target diagnostics and runtime reports.
   The overview now points to this measurement; older frozen packets stay historical.

There are 52 recorded source trials: three independent/combined candidate controls
and 49 follow-up attempts. `experiments.json.gz` contains exact source patches,
source hashes, build results and available target metrics. Patches are relative
to historical base `5265cb3c`, not the later accepted source. `ATTEMPTS.jsonl`
contains this lane's ledger entries. Exploratory batch drivers stay local.
No IR mutation, ELF patching, original-byte injection or scorer change is retained.

## Build and verify

Python 3.11 or later must be available as `python3` on PATH, including for the
compiler wrappers. Use the pinned platform-tools v1.44 identity setup: macOS
compiler, Linux identity target libraries in `toolchains/hybrid144`, and locked
offline registry. See `reconstruction/toolchain/` and
`reconstruction/harness/SOURCE_INPUTS.md` for provisioning. `MEASUREMENTS.json`
pins compiler/tool hashes, source aggregates, linker identity and both ELF hashes.
The small build adapter exposes local cache/SDK/registry locations and an explicit
input checkout. Scorer and source hashes are historical pins: later `main` may
change either even when its output ELF is unchanged. Keep this packet in the
current checkout and create separate input worktrees at its recorded revisions:

```sh
git worktree add --detach /tmp/pump-five-current-inputs 9b216213cfe59a0c4a8e54657142b3c86706ded4
git worktree add --detach /tmp/pump-five-base-inputs 5265cb3c2a4cb7bca51cb535ad2faa651c8121c3
python3 reconstruction/pump-main/lanes/five-bytecode-followups/build.py \
  --repo /tmp/pump-five-current-inputs \
  --cache /path/to/reconstruction-cache --sdk /path/to/platform-tools-v1.44 \
  --registry /path/to/cargo-home --work /tmp/pump-five-build --out /tmp/pump-five-current
```

Build the historical base separately with the same command, replacing `--repo`
with `/tmp/pump-five-base-inputs` and using distinct work/output directories. Then:

```sh
python3 reconstruction/pump-main/lanes/five-bytecode-followups/verify.py \
  --repo /tmp/pump-five-current-inputs \
  --baseline /tmp/pump-five-main/unstripped.so \
  --candidate /tmp/pump-five-current/unstripped.so --report /tmp/pump-five-verify.json
```

Run the verifier's success and refusal controls against the same supplied builds:

```sh
python3 reconstruction/pump-main/lanes/five-bytecode-followups/test_verify.py \
  --repo /tmp/pump-five-current-inputs \
  --baseline /tmp/pump-five-main/unstripped.so \
  --candidate /tmp/pump-five-current/unstripped.so
```

These controls exercise normal, `-O`, and `-OO` modes, wrong ELF rejection,
changed census/source binding rejection, and preservation of an existing report.
They copy only this packet into temporary directories and do not modify the
input checkout or supplied builds.

The verifier requires the recorded program source in the selected input checkout, exact ELF hashes,
unchanged scorer inputs and all 1,035 census rows. It rejects any membership loss
or different gain set. It does not compile or replay transactions. Binaries and
caches are not bundled: this is a source-bound measurement packet, not the older
checkpoint's standalone artifact export.

## Runtime comparisons

Use the repository's LiteSVM/solders 0.27.1 environment:

```sh
python3 scripts/pump_admin_cto_differential.py \
  --candidate /tmp/pump-five-current/candidate.so --output /tmp/admin-five.json
python3 reconstruction/pump-main/lanes/five-bytecode-followups/replay_swap.py \
  --candidate /tmp/pump-five-current/candidate.so --output /tmp/swap-five.json
```

Accepted main passes **363/363** Admin CTO comparisons of errors, before/after
account snapshots, events, inner calls and return data, using captured dependency
programs and synthetic signed transactions. It passes **120/120** swap comparisons
of errors, curve bytes, curve quote change, user base change and buyback receipt.
The new wrapper runs both compiled binaries; it does not use the Rust host model
as a substitute for either binary.

Swap signature verification is disabled to supply the AMM PDA signer. Cases cover
one hop, excluding two-hop paths, post-completion fills and Token-2022 quotes.
They do not compare every account, log, CPI or compute-unit count. Passing them
is bounded behavioral evidence, not general runtime identity. Gzipped reports
retain every checked case and input hashes; published provenance paths use
`$REPO` and `$LOCAL` aliases rather than contributor machine paths.

## Coordination and credit

- Merged #2403 and
  #2412 supply the accepted
  swap/Admin CTO combination now measured on main. No duplicate source is proposed.
- #2416 merged as research
  only. Its rejected source is a recorded experiment, not the published source.
- Open #2387,
  #2368, and
  #2366 cover related swap
  mechanisms. This packet changes neither their shared production file nor their
  branches. No full-branch integration is claimed.
- #2370 supplies precursor
  Admin CTO research; #2293
  and #2375 informed the
  create-v2/SROA search. Shared research does not establish a conflict or dependency.
- Merged #2413 supplies the
  120 swap fixtures reused by the compiled-candidate wrapper.

Prepared as Oz-0s using Codex desktop, OpenAI / GPT-6 Astra (operator-reported).
