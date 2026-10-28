# recovered from the transcript of lane crank-b (PROGRESS.md); entries in order

# crank-b PROGRESS (continuation notes)
Lane dir: lanes/crank-b. src/ = untouched frontier clone; v/<name>/ = variant trees; t1..t3 = target dirs;
out/ = build outputs + scores.log; tools/cx.py (scorer), tools/mkvar.py NAME SPEC.py (variant from w582 with
lib.rs:248 body + optional donation.rs 12..51 helper), tools/run.sh NAME SLOT (build+score).
an/orig-147944.txt = original disassembly with names.

## Status
- Baseline verified: lane rebuild == native w582 (sha e6849af5...).

# crank-b PROGRESS (continuation notes)
Lane dir: lanes/crank-b. v/<name>/ = variant trees (mkvar now bases on w583); dt1..3 = dbuild empty targets;
out/ = builds + scores.log; tools: cx.py (scorer; --diff N [--raw]), mkvar.py NAME SPEC.py, run.sh NAME SLOT (dbuild),
feat.py (structural features), lst.py (listing), blk.py (--frames slot map), sret.py, irfn.py. specs/*.py = variant specs.
an/orig-147944.txt = original disassembly with names.

## Status (13:00)
- Best: v07 (specs/v07.py): 15952B/1947i masked 0.8935 raw 0.8478; see findings/crank-b.md for the source + remaining diffs.
- Next: v08 = v07 + anchor/#[event]-style Event::data (serialize+unwrap) to fix the emit_cpi collect region.