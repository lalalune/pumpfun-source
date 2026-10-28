Research packet: the Round37 main-Pump genuine composite plus **synthetic Source-line positioning**. It adds only `research/claude-pump-integration-20261027/r37-layout-03/`; `programs/pump`, rounds and status files are untouched.

**744 → 875 normalized windows** (121 → 147 raw) against a control build of the unchanged Round37 primary with the same repository builder, with **no losses**. With the original Linux `sbpf` target libraries (#307) the same source reaches **880 / 1,035**. Whole-ELF identity remains false.

**What is synthetic, and what is not.**
- Nearly every original window that contains an `error!` / `require!` site embeds the site's `Source {file, line}` as code immediates, and the original's values are readable from its own instructions.
- The coordinate lanes (coordfiles and coordlib, recovered from their transcripts and re-applied by the integrator) place each site on its original line. They do this with blank or `// layout-pad…` comment lines and token-preserving line joins. **That padding is a layout device, not recovered source text**, and it is marked as such in the README and in every pad marker.
- The code changes underneath are genuine source-form changes: original item order in `lib.rs`, legacy buy/sell bodies inline in the `#[program]` handlers, per-site closures, the buy_v2 handler split, and so on. Of this packet's gains over the genuine composite (#384, `r37-genuine-03`), only the line positions are synthetic.
- `tools/pipeline_r37.sh` rebuilds this tree from the genuine base.

**Behaviour:** the 44-suite captured-loader corpus passes against this exact candidate (10,468 cases, 10,464 paired diagnostic logs, 0 mismatches; `full.json.gz`). The build log has no stack-offset warnings.

```sh
python research/claude-pump-integration-20261027/r37-layout-03/verify.py
```

`verify.py` is pure Python. It checks the manifest and build bindings, regenerates `source.patch`, recomputes all 1,035 windows for both ELFs and their gains, and validates the regression report.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
