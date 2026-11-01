# Two admin packets admit a duplicated manifest path and a symlinked member

Packets:
- `research/pump-fees-admin-cto-sharing-direct-20261030`
- `research/pump-global-admin-sequences-20261030`

## Defect

Both verifiers hash the members their `MANIFEST.json` lists and compare the
listed set against the folder, but neither refuses two admissions the rest of
the packet family refuses:

1. **A duplicated MANIFEST.json path is accepted.** The entry list is checked
   per entry and compared as a set, so a manifest that names the same file
   twice verifies as if it named it once.
2. **A symlinked packet member is accepted.** Member reads follow the link,
   so a member whose bytes live outside the packet passes its recorded hash;
   the packet on disk is not the packet the record describes.
3. **Cached Python bytecode is not refused by the global-admin verifier.**
   It imports its `producer.py` after admission; `sys.dont_write_bytecode`
   stops cache writes, not reads, and its file-set comparison excludes
   `__pycache__`. A planted `.pyc` with a valid header for `producer.py`
   therefore executes in place of the admitted source. The admitted packets
   refuse `.pyc`/`.pyo` anywhere in the packet tree. This mode is pinned by
   the census's cached-producer test, not by the five-mode matrix below.

The census behaviour matrix (five modes — pristine, changed, extra, symlink,
duplicate — run with nonexistent images) was executed against all 60 research
packets that ship `MANIFEST.json` with a `verify.py`. These are the only two
whose duplicate and symlink modes reach the image stage instead of being
refused; the other 58 refuse every tamper mode.

Secondary, for the fees packet only: its file-set comparison ran in `main()`,
after `import producer`. The fix runs the whole admission inside
`verify_manifest()`, before the producer is imported — the ordering
#4007 established for the reconstruction packets.

## Inputs (full sha256)

Base `verify.py` at the tested base:
- fees-admin-cto-sharing-direct: `c8cb58b0e850fb556abc9e2fa51a9bc44682de15088ad434cea34cd8d95c0f24`
- global-admin-sequences: `a28f69a3ef6893b8eebb38d2abe2d1549ba413c42f532b13c09d641c70739610`

Fixed `verify.py`:
- fees-admin-cto-sharing-direct: `17ab9fdf94dd5503ec5a5b0e991b97de02546a2e7e2769f5d4bbdf388eeda309`
- global-admin-sequences: `0b16e112f607a668986e63f2642b533107c59a11f2bf11affedd2768f210d56a`

## Reproduce

Against a base checkout (expect the defect):

```
python3 research/admin-manifest-admission-20261101/reproduce.py \
  --checkout <base-checkout> --revision 8330455eb0897493714da67aa4de6f9743d82b84 \
  --expect base --output results-base.json
```

Against the fixed tree (expect every tamper mode refused):

```
python3 research/admin-manifest-admission-20261101/reproduce.py \
  --checkout <fixed-checkout> --revision <fixed-sha> \
  --expect fixed --output results-fixed.json
```

`results.json` in this packet holds both recorded runs. On base, both
packets report `duplicate=reached-image-stage` and
`symlink=reached-image-stage`; with the fix, all five modes behave
(pristine reaches the image stage, the four tamper modes are refused).

## Scope / non-scope

- In scope: the two packets above, their `MANIFEST.json` re-pins (the edited
  `verify.py` entries only), and census behaviour coverage for them in
  `tests/test_packet_manifest_census.py`.
- Both packets gain the family's symlink-or-cached-bytecode refusal ahead of
  the file-set comparison. The global-admin packet keeps its own rule of
  excluding `__pycache__` from its file set; the suffix scan refuses the
  cached bytecode itself before that comparison runs. The fees packet gains
  the refusal together with the file-set check, matching the decode packets'
  `verify_manifest()`.
- Not touched: the fee packets (pass108, #3983, #4007 own their admission),
  the decode packets (#3982 owns them), the five reconstruction packets
  (#3988, #4007 own them), and every other research packet — the matrix
  shows they already refuse both modes.
- No claim about symlink races after admission (a member swapped between
  the check and the read); the fixed packets make the same non-claim.
