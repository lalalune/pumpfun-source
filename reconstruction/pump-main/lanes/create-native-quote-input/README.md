# create-v2: caller-owned native quote key closes the four-slot gap

**`create_v2::execute` at original `0x1e7c0` is now a normalized match.**
The target retains its original 15,576-byte size and 125 internal calls. It is not
raw-equal. Whole-program score rises from **1,032 normalized / 347 raw** to
**1,033 normalized / 347 raw**, with no normalized or raw membership losses.

Base: `f9ef509aa4067e2e1aaede3c2b98cca20a606c99`, freshly built with the maintained
identity recipe (v1.44 macOS compiler and Linux target libraries). `RESULTS.json`
pins source, linker and ELF hashes, the full score delta and target diagnostics.
A second build in a new build directory reproduced both ELF hashes exactly.

## Source change and mechanism

The private quote validator now takes `sol: &Pubkey`. Its only caller supplies
`&Pubkey::default()`, and both native-quote return paths copy `*sol` instead of
constructing their own zero key. The default key comparison remains unchanged.
This preserves the returned values and validation ordering; source line numbers,
compiler settings and linker inputs stay unchanged.

Previously the only differences were the destination registers of two zero moves
at offsets `0x490`/`0x498` and `0x2310`/`0x2318`: candidate r7/r2 versus original
r2/r7. All four slots now match. This follows the SROA lead in
[#2375](https://github.com/lalalune/pumpfun-source/pull/2375): copying a caller-owned
key gives optimization a different intermediate form than constructing a zero
key inside both callee branches. The final match is measured; the detailed
intermediate-pass explanation is an inference from that prior diagnostic work,
not a new IR proof in this packet.

Four preceding alignment-wrapper trials produced exactly the old four-slot
residual. They and the successful caller-owned-key trial are in `ATTEMPTS.jsonl`.
No original instructions, output patches, IR mutations or scorer changes are used.

## Verification

- Full 1,035-window censuses retained in `baseline-score.json.gz` and
  `candidate-score.json.gz`; complete source fingerprints accompany them.
- Call-target audit: 1,033 normalized and 1,033 bisimilar matched windows; no
  reported hidden callee mismatch. This remains a diagnostic, not whole-program proof.
- Existing creation differential: **110/110** cases agree on before/after account
  snapshots, errors, events, inner calls and return data.
- Extended captured create-v2 fixtures: **303/303** cases agree on errors, watched
  before/after account snapshots, events and returned account objects. These include
  absent/explicit native quote, zero quote key, token quotes, nested quote paths,
  Mayhem and validation failures. They are synthetic signed offline transactions;
  passing them does not establish every possible runtime behavior.

Build main and this source with `reconstruction/harness/fastbuild.py` using the
pinned identity setup, then use the unchanged scorer:

```sh
python3 reconstruction/harness/score.py /path/to/candidate/unstripped.so \
  --baseline /path/to/fresh-main-score.json --json /tmp/create-match-score.json
```

Runtime replay requires the repository's solders/LiteSVM environment (solders 0.27.1):

```sh
python3 scripts/pump_create_v2_differential.py \
  --candidate /path/to/candidate/candidate.so --output /tmp/create-standard.json.gz
python3 reconstruction/pump-main/lanes/create-native-quote-input/replay.py \
  --candidate /path/to/candidate/candidate.so --output /tmp/create-extended.json.gz
```

The replay adapter runs the compiled candidate against the captured original; it
reuses the fixtures from `tests/test_create_v2_captured.py`, not the host Rust model.
The original and dependency hashes are checked before running, and all inputs are
rehash-checked before publishing the report. No chain or external service is used.

## Coordination and credit

The open-PR file scan found no other open PR changing `programs/pump/src/create_v2.rs`
at publication preparation. Related work:

- [#2293](https://github.com/lalalune/pumpfun-source/pull/2293) and
  [#2386](https://github.com/lalalune/pumpfun-source/pull/2386): prior source work
  leading to the four-slot residual; this change starts from accepted main.
- [#2375](https://github.com/lalalune/pumpfun-source/pull/2375): SROA/zero-store
  investigation directly informing this source hypothesis.
- [#2497](https://github.com/lalalune/pumpfun-source/pull/2497): our earlier
  checkpoint and negative experiments. Its pinned 1,032/347 measurement remains
  historical; this new source gain is measured separately. No shared files.

No full unmerged branch integration or conflict is inferred from related scope.
Prepared as Oz-0s using Codex desktop, OpenAI / GPT-6 Astra (operator-reported).
