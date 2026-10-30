# Window B: current-main Sweep Fees requalification

Target: `0x72810`, `sweep::execute` (7,832 bytes, 37 internal calls and 2
syscalls). Final upstream base: `3227e700baecd7e692164577c755cb5b24995fc6`.

This packet requalifies the Sweep reconstruction from PR #1548 against current
main. It does not change `programs/pump/src/sweep_fees.rs`: every tested source
alternative was worse than the maintained implementation, so retaining the
best source is the only zero-regression result.

## Fresh baseline

The identity build used the v1.44 SDK and Linux v1.44 SBF target libraries.

| measurement | original | current candidate |
|---|---:|---:|
| ELF SHA-256 | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` | `f0b3f34a89434d220f27fd24fd7e3a0bc5116b5fd3002c0a724fa62ea953847e` (stripped) |
| ELF bytes | 10,485,715 | 1,935,192 (stripped) |
| target bytes | 7,832 | 7,880 |
| direct calls | 37 internal + 2 syscalls | 37 internal + 2 syscalls |
| target similarity | 1.0 | 0.88669 |

The unstripped candidate is 2,666,160 bytes with SHA-256
`df437ee762e05a1826a02c40814cac08346f86b385996b56d4dd49b72c6eff75`.
The staged source snapshot hash emitted by `fastbuild.py` is
`7299d54139852736d6c519cdbeff52296fd4307ad27cd9ddb5418d7f85465315`.

The full current-main inventory score is 1,027/1,035 normalized windows and
276 raw windows, covering 1,677,176 matched text bytes. The sensitive window
`0xa868` is normalized-equal but not raw-equal in the fresh main build itself;
therefore 276, rather than the historical 277, is the authoritative raw
baseline for this investigation.

Relevant identities:

- `programs/pump/src/sweep_fees.rs`:
  `4e2cf1e7e6c1c07c85b51e7c06c6425bece6d8278787c27cb66e7b0b2ba94`
- `reconstruction/base/functions.tsv`:
  `fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8`
- `reconstruction/harness/score.py`:
  `ee69ca960e02a5ca58b896e7e22609856f57c11608b8131979a2930513f1b91b`
- `reconstruction/harness/fastbuild.py`:
  `3a9e48712b5eb8ff1394dab7da1272e50a4760bd35c5cf5167f9f373af3d44c9`
- rustc `1.79.0-dev`, LLVM `18.1.7`:
  `1f26338cc2cabd0a6057dcbd0528bba262b23ca1296d357a55304ee31d1d9e5a`
- cargo `1.79.0 (804e32543 2025-01-29)`:
  `cd27e4113fc155b5e79fca97c1cc5447ef89d1c8ce3d0e1e5679d2dd7a9ab0ef`
- llvm-objdump `18.1.7-rust-dev`:
  `24f83fd4c314fdc358920bf9936261985b8c39266f1ba7d556716c9dec1d24f9`

## Reproduced compiler mechanism

The prior lane identified a coupled rent-helper and inlining effect. This was
reproduced before changing any source:

1. Final optimized MIR still calls `admit_quote_pair` and
   `ensure_rent_exempt`; neither helper is consumed by the MIR inliner.
2. An LLVM dump taken before the regular `InlinerPass` already contains both
   helper bodies in `sweep::execute`. They are consumed by the LLVM
   `AlwaysInliner`, as required by their `#[inline(always)]` attributes.
3. In the maintained `Rent::get().map(...)?` helper, the `From` error, native
   transfer result and `Ok(())` paths merge through one result phi and one
   `result == 2` test. That is the major improvement preserved by PR #1548.
4. Replacing the map with `Rent::get()?` restores the original pre-tag rent
   payload copy, but MemCpyOpt merges the value/residual stack move and removes
   the lifetime markers. The surviving uncoloured 24-byte slot shifts the
   frame and collapses similarity to 0.54971.

The diagnostic compiler capture produced the same stripped ELF hash as the
official identity build. Compiler dumps were used only for diagnosis; the
acceptance build and scores use the unchanged official recipe.

## Controlled source experiments

Every compiled trial was scored across all 1,035 original Pump windows. All
retained 1,027 normalized and 276 raw memberships, but none improved the
target. Calls below are `internal + syscall`.

| trial | bytes | similarity | calls | result |
|---|---:|---:|---:|---|
| maintained `s6` | 7,880 | **0.88669** | 37 + 2 | retained |
| historical pre-`s6` rent placement | 7,768 | 0.82199 | 37 + 2 | reproduces the helper gain |
| admit helper, explicit success-first match | 7,840 | 0.75143 | 37 + 2 | broadly changes the CFG |
| admit helper, `and_then` | 7,840 | 0.75143 | 37 + 2 | byte-identical to explicit match |
| admit helper, `if let Err` return | 7,992 | 0.73271 | 38 + 2 | restores the unwanted clone call |
| borrowed named rent result | 7,832 | 0.86966 | 38 + 2 | exact size, wrong call graph/layout |
| recipient `as_ref().clone()` | 7,880 | 0.88669 | 37 + 2 | whole-ELF byte-identical |
| explicit `AccountInfo` field clone | 7,480 | 0.73959 | 37 + 2 | incompatible with the current frame |
| borrow success / consume rent error | 7,864 | 0.87292 | 38 + 2 | extra call, no payload repair |
| `Ok(ref rent)` / `Err(error)` | 7,808 | 0.87520 | 37 + 2 | payload copy remains in the late error block |
| `Rent::get()?` reproduction | 7,856 | 0.54971 | 37 + 2 | original copy, uncoloured 24-byte slot |
| `Rent::get().map_err(Error::from)?` | 7,808 | 0.87728 | 37 + 2 | disproves residual-size repair |

These results rule out the natural Result ownership and error-conversion
spellings as ways to preserve both the original rent payload copy and the
current frame colouring. They also confirm that source-level match/closure
spellings do not merely reverse the remaining admit branch polarity.

## Offline runtime qualification

The captured-program model suite passed:

- 98 fixed cases;
- 80 deterministic seeded random cases;
- the checker negative control and outcome-coverage assertion.

The broader binary differential then ran 504 cases against the original and
rebuilt Pump ELFs with zero mismatches. It compared errors, before/after
accounts, return data, inner instructions and event payloads. The matrix covers
native SOL, SPL Token and Token-2022 quote paths; missing, malformed, wrong-owner
and wrong-key accounts; ATA derivations; signer/writable constraints; zero and
insufficient balances; rent boundaries; failed CPI paths; fee overflow; mayhem
recipient selection; and creator/protocol buckets.

This is 682 original-versus-reconstruction behavior cases. It is behavioral
evidence only, not a byte-identity claim.

## Reproduction

```bash
python3 reconstruction/toolchain/bootstrap.py --sdk-check full
python3 reconstruction/harness/fastbuild.py \
  --src programs/pump --work /tmp/pump-sweep-work --out /tmp/pump-sweep-out
python3 reconstruction/harness/score.py \
  /tmp/pump-sweep-out/unstripped.so --no-baseline --json /tmp/pump-sweep-score.json
python3 reconstruction/harness/target_metric.py \
  /tmp/pump-sweep-out/unstripped.so 0x72810 --sym 'sweep.*execute'
python3 -m unittest -v tests.test_sweep_fees_captured
```

`scripts/pump_fee_sweep_differential.py` additionally needs the immutable
imported runtime snapshot used by the repository's local validation setup.

## Remaining byte differences

The maintained residuals are:

1. opposite block placement/polarity at the two token-account admit result
   branches;
2. the rent error payload copy/lifetime conflict described above;
3. quote-token-program and quote-mint loads hoisted before the native/token
   Option join instead of after it;
4. a late event bucket store using a cached creator value instead of reloading
   the spill.

The most promising next action is a source shape that changes the lifetime of
the `Rent::get` residual without creating another live alloca. The attempted
borrow, match and pre-conversion forms show that merely changing ownership or
the residual error type is insufficient; the useful lever must survive
MemCpyOpt's stack-move folding while retaining the LLVM-only helper merge.
