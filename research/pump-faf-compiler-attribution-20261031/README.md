# Frozen FAF compiler attribution evidence

This packet preserves one failed native diagnostic run and replays a narrower
code-identity result from its actual compiler output. It joins optimized LLVM
allocations to selected machine frame indices, virtual registers and final spill
slots for Pump `admin_cto::execute`. It changes no program source and supplies no
byte-match gain.

The source is frozen at `faf99624250b4e60107790f7edabf6609f709885`, not current
main. The selected 141-file source SHA256 is
`29a8df2d7e12b379a9dc515d5a84eaaf051729da62350a54996a0077015f0c8a`.
The retained CORE vector has 236 files and maintained workspace staging has 142.
The target symbol is
`_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E`,
VA `0x22a10`, 27,400 bytes.

## Native result and separate offline admission

The faithful control is [run 41146593117](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41146593117),
artifact 13020993188, operational commit
`50ebec8188201e8e8bf8f484f2b6b44e3387e121`. The single diagnostic capture is
[run 41148994357](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41148994357),
artifact 13022431433, operational commit
`39da3bb8c71dd83685c2c8584669ef0e67f8e6bf`.

**The diagnostic run failed.** Its original `FAILURE.json`,
`DIAGNOSTIC-COMPARISON.json`, `capture-result.json`, logs and metadata are retained
unchanged. The original gate required full stripped and unstripped ELF equality,
full score-summary equality and parsed complete stages. It correctly refused
qualified attribution under those requirements.

| Retained observation | Actual result |
| --- | --- |
| Complete stripped ELF | Equal to the faithful control: `d5cee214ba29be1a1ccbb96d036f3dd7dfbd683d61046d76b66103507d3ef750` |
| Complete unstripped ELF | Different: control `8febf467fc61fbf17ff11045ed9d7b0d3aba0eeedbcadf5060abb2552212b02a`; diagnostic `c213afb2eb6b6f2bb784051615a2011ec3f3d7ce7bc15d525f95d07d23e2885c` |
| Section payload differences | Only `.symtab` and `.strtab`; all other section payloads equal |
| Decoded symbol differences | Exactly 696 names; symbol info, visibility, section, value and size agree row by row |
| Saved official score | All 1,035 rows equal; 1,034 raw and normalized matches; summary differs only in the unstripped `candidate_sha256` |
| Original parser | Reports zero machine dumps: it requires bare `***` at line start, but the actual LLVM headings start `# ***` |
| Offline extraction | Five complete machine functions and the optimized target definition recovered as exact byte slices of the preserved log/module |

The parser explanation concerns this retained helper. Existing upstream capture
code already supports comment-prefixed headings; this packet claims no new
shared-tooling parser defect. The offline code-identity admission is a separate,
explicitly narrower result. It does not rewrite the native failure into success
or establish full unstripped equality.

## Actual compiler-stage joins

The fixed diagnostic arguments and full environment subset are preserved with
the four operational inputs. Capture used the maintained identity recipe and
one `cargo rustc --lib -- --emit=link,llvm-ir` boundary with target-filtered LLVM
printing. Source/CORE/staging seals, complete SDK checks, locked fetch, empty
native target/cache, local-crate fingerprints, linker receipt/map, and
before/after source/registry/tool checks remain in the original artifacts.

| Actual stage | Selected observed relation | Attribution limit |
| --- | --- | --- |
| Optimized LLVM target | `%e` is 200 bytes/alignment 8, with explicit lifetime start/end. Both prior 424-byte CPI-context lifetimes end before its start. `%authority_info` is 48 bytes; the authority bump has one load and one seed-byte-store use. | Original LLVM lifetimes are not available. Missing lifetime intrinsics on a candidate object do not establish a source defect. |
| After `finalize-isel` | Event uses FI120 and explicit lifetime pseudos. | This is the first retained machine snapshot. |
| Before `greedy` | The same event address v1393 now uses colored FI21. The authority clone address v1398 and bump v1399 span a region containing byte-pointer/length values v1409/v1410 and Instruction address v1418. | Coloring is visible by this boundary; the five snapshots do not identify which intervening pass performed it. Def/use overlap is not a printed LiveIntervals, spill-weight or eviction trace. |
| After `greedy` | The bump has split load/reload values v2239/v2240 and spill slot FI346. | The observed spill is established by this boundary; its cause or optimality is not proved. |
| After `virtregrewriter` | The clone address uses r6; the bump spills/reloads through FI346. | This explains the candidate allocation. Prior raw-byte work already identified the opposite original clone/bump allocation. |
| After `block-placement` | Event/shared slot FI21 is at SP-720; old FI346 is dead and the bump uses colored FI178 at SP-2264. | Physical placement is tied to the equal stripped code; it is not an original-source-local identity. |

The long-lived `%hk`33-byte holder-PDA result is distinct from the short-lived
sweep `%_7.i`33-byte result. The latter and the32-byte quote-key temporary coalesce
at SP-720; `%hk` remains at SP-1657 and supplies seven forwarded target-key bytes.
These are actual compiler-to-frame joins. The scoped-hk source lead is already
in [#3140](https://github.com/lalalune/pumpfun-source/pull/3140), including the
losing scoped form, so this packet supplies no candidate from it.

The verifier checks 50 exact event/sweep compiler-line witnesses against bytes
it re-derives from the original full module and raw log. Exact worker join
reports and producers are also preserved. Their remaining analysis, including
prior context-header/seed proofs, is authenticated as retained evidence rather
than newly reexecuted by this verifier.

## Replay and retained bytes

From the repository root, run with Python's standard library only:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/pump-faf-compiler-attribution-20261031/verify.py
```

An explicit path to `verify.py` works from other directories; it finds its
sibling manifest and archive. `--artifact /path/to/evidence.tar.xz` selects an
explicit local copy. There is no implicit network, SDK, compiler, VM, scorer,
Git checkout or installation. The verifier writes its report to stdout.

The single `evidence.tar.xz` retains all **43 reference and 47 diagnostic member
bytes**, including the complete 41,907,501-byte LLVM module, both full ELF pairs,
source/workspace archives, full raw compiler output and every original receipt.
It also retains the exact faithful baseline OPS3 and diagnostic OPS4, derived
five-stage/target slices, worker joins and failed-run metadata/log. `manifest.json`
pins every member's exact size/hash and records the original transport ZIP
hashes. Repacking preserves each member's bytes; it does not preserve the outer
ZIP container bytes. All inputs needed for this replay are retained locally;
GitHub's 30-day artifact expiry does not make replay depend on those links.

The verifier checks the archive hash, exact member domain, regular-file types,
unique safe relative names and every member hash. It reads members in memory
and never extracts them into the filesystem. It rechecks archived source/staging
bytes, operational Git-blob/hash bindings, complete stripped equality, ELF
section/symbol differences, full saved-row equality, the mandatory original
failure, complete original log/module slices, and the selected witness lines.
The saved official census is compared rather than independently recomputed.
Root's retained `CODE-IR-ADMISSION.json` records the separate prior independent
full-census recomputation.

The manifest must contain all five stage records in the observed order. Each
record's timing, canonical LLVM pass ID and canonical filename must agree with
the corresponding actual log heading before its slice is joined. The verifier
also requires all 50 witness checks and rejects lines that are not positive
integers within their selected compiler output. Checks may share a file/line
when one frame row supports several object joins. These metadata checks preserve
the recorded pass IDs and all retained input bytes.

## Prior work and scope

Post-optimization IR capture and stripped equality already appear in
[w12a02-cto-iroracle](../../reconstruction/pump-main/lanes/w12a02-cto-iroracle/NOTES.md).
[#2919](https://github.com/lalalune/pumpfun-source/pull/2919) covers prior
verification; [#3253](https://github.com/lalalune/pumpfun-source/pull/3253) and
[#3266](https://github.com/lalalune/pumpfun-source/pull/3266) cover frame methods;
[#3288](https://github.com/lalalune/pumpfun-source/pull/3288) already describes the
clone/bump residual. [#3315](https://github.com/lalalune/pumpfun-source/pull/3315)
already changes frozen FAF's cached new-fee lifetime family on later main.
None is presented as newly discovered here.

The contribution is a durably retained, replayable native-output/provenance
packet with exact optimized-LLVM→FI→vreg→spill witnesses. It performs no IR edits,
IR recompilation, layout/flag search, binary transplantation, source change or
score-mask change. Separately reported 363 runtime cases are prior evidence;
this packet adds no runtime coverage. It establishes no original compiler
lifetime recovery, allocator optimality, source gain, later-main equivalence,
whole-original equality or security acceptance.

## Historical authority-clone addendum

The event-authority negative belongs to open
[#3330](https://github.com/lalalune/pumpfun-source/pull/3330), rather than being
established by merged #3318 alone. The
[retained notes at 7073cc4a, lines 122–134](https://github.com/lalalune/pumpfun-source/blob/7073cc4a3f18d0c77b1364a2212437a0f468e816/reconstruction/pump-main/lanes/w14a30-cto-shareauthport/NOTES.md#L122-L134)
record a lamports-first result of 0.65398 below its 0.65458 baseline at
`6db95a76419b6b355a3f173f1c65c724c25f3029`, one source revision after frozen FAF.
This is a historical documented result. It is not an independently rebound
failed ELF or a fresh test of later main. The sealed worker inputs inside the
archive are preserved unchanged; this addendum supplies the clarified citation.
