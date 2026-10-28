# speed-fix lane PROGRESS (resume from here)

Task: repair + PROVE the previous round's fast tools (R/shared/tools/speed-recovered: fastwin, fastdiff, dbuild, farm,
SPEED.md), fix paths to R=/Users/shawwalters/fees100-run, install verified tools into R/shared/tools, update SPEED.md,
append "[speed-fix] VERIFIED ..." to DIRECTIVES.md. Do NOT change fndiff/measure/dis interfaces (lanes use them).

Lane layout: R/lanes/speed-fix/{work (transcript analysis), stage/tools (staged tools), src (w584 clone), target, out, proof}

## Findings so far
- 20:58 The "4 failed edits" are NOT lost: replay_tools.py logged E-MISS for duplicate `api-request-blob` records of
  edits that had already applied. speed-recovered/* == my own replay of the round-2 speed transcript
  (agent-ae9c49a01a7037e9a). render() JSON diagnostics, os.chmod(store,0o755), sanitize_patch + Index:/diff/Only-in
  drop are all present. Two duplicate records were applied TWICE (old_string survived): farm.py
  `a.base_digest = tree_digest(a.base)` doubled; SPEED.md sentence doubled.
- Bash-made changes missing from the replay: fastwin chmod 0o644 of cache files; default windows (now only 147944);
  final SPEED.md paragraphs. fndiff/measure/dis in R/shared/tools are this round's own versions (measure.py has its
  own pickle cache tools/cache/<sha>.windows.pickle) -> leave them untouched.
- Path bugs: HERE.parents[1] used as R (wrong when run from speed-recovered/ or a stage dir); dbuild's lock_prefix
  uses HERE/sbf_lock.py -> a staged copy would NOT share the machine-wide slot lock. Fix: absolute R + shared lock.

## Plan / status
- [x] stage + fix tools (stage/tools)  - [x] fastwin selftest + fastdiff==fndiff/measure  - [ ] dbuild==nbuild (w584 + edited)
- [ ] farm never writes outside --out (absolute diff -ru patch)  - [ ] install + SPEED.md + DIRECTIVES line

## 21:10 fastwin/fastdiff PROVEN (staged copies in stage/tools)
- fastwin --selftest on 61 images (57 unique: original, w583/w584 native, w583 container+pr301 symbols/candidate,
  integration create-donation, 1 lane nbuild, 50 Codex outputs): fast_windows == FRESH reference instance, and the
  served (cached) table == reference. fast 0.055 s/image vs reference 0.78 s/image (load ~22).
- eqcheck (work/eqcheck.py TOOLS OUT IMAGES): fastdiff vs SHARED fndiff.py/measure.py: 427 (image,window) pairs, 7
  windows; 235 compared (192 = symbol missing in both, same error), 0 mismatches in ratio/span/identical/insn counts/
  candidate name+addr/exit code/every diff line; measure normalized/raw/gained/lost equal on all 61 images. Run with
  a cold FASTWIN_CACHE + FASTWIN_NO_REFCACHE=1 (proof dirs proof/eq3, proof/eq4-coldfast).
  eqcheck gotcha: split fndiff stdout on '\n' only (lddw previews contain \x0c etc.).
