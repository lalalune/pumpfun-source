# speed-fix lane findings (tool repair + proofs; produced bytes must not change)

## 20:58 recovered tools are complete (the "4 failed edits" were duplicate transcript records)
- replay_tools.py replays every tool_use record; each Edit also appears once more as an `api-request-blob` record, whose
  old_string no longer matches -> logged E-MISS although the edit had applied. The recovered dbuild.py/farm.py contain
  the rustc-JSON rendering, the store chmod and the patch sanitizer. Two duplicate records applied a second time
  (farm.py doubled `a.base_digest = ...` line; SPEED.md doubled sentence) -> harmless, fixed in the staged copies.

## 21:10 fastwin + fastdiff verified against the in-use fndiff.py / measure.py
- fastwin --selftest: 61 images (57 unique) fast_windows == fresh reference window_map instance; 0.055 s vs 0.78 s.
- fastdiff vs shared fndiff.py + measure.py: 427 (image, window) pairs over 7 windows, 0 mismatches (ratio, span,
  identical, insn counts, candidate symbol/address, exit code, every masked diff line; normalized/raw/lost/gained).
- Defaults changed: fastdiff/farm score only 147944 by default; default baseline = newest native/wNNN-symbols.so
  (frontier/CURRENT still says w583, so a w584 variant that lost 163920 would not have shown a loss).
