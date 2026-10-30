#!/usr/bin/env python3
"""features.py <trimmed module.ll> <outdir>: apply the ranked admin_cto frame features to any captured
candidate and print how much each is worth on it (llc oracle, experiment only; no source proposal).

Auto-detects by IR shape (names differ between builds):
  slice  the wallet emit_cpi! signer slice: an inlined (.i) [16 x i8] alloca that receives
         `store i64 2` at +8 right before solana_program::program::invoke_signed
  bufs   inlined [24 x i8] allocas with lifetime markers (candidates for the unmerged 24 B piece)
  val    the 33 B no-lifetime sharing-CPI `val` copy (if any)
Rows: base, F1 = slice moved before the first no-lifetime execute alloca (the greedy's choice), F1 + best single 24 B nolt, + val moved before the first
no-lifetime execute alloca. Each row is one llc run; the nolt row tries every buffer (parallel)."""
import json, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle, iredit  # noqa: E402


def detect(fn):
    lines = fn.split('\n')
    allocas = re.findall(r'^\s*%(\S+) = alloca \[(\d+) x i8\]', fn, re.M)
    lt = set(re.findall(r'llvm\.lifetime\.start\.p0\(i64 \d+, ptr (?:nonnull )?%(\S+)\)', fn))
    slice_ = None
    for k, l in enumerate(lines):
        if 'invoke_signed' in l and l.strip().startswith('call'):
            for j in range(k - 1, max(0, k - 8), -1):
                m = re.match(r'\s*store i64 2, ptr %(\S+), align 8', lines[j])
                if m:
                    g = m.group(1)
                    for i2 in range(j - 1, max(0, j - 4), -1):
                        mm = re.match(r'\s*%' + re.escape(g) + r' = getelementptr inbounds i8, ptr %(\S+), i64 8', lines[i2])
                        if mm and mm.group(1).endswith('.i') or (mm and '.i' in mm.group(1)):
                            slice_ = mm.group(1)
                            break
                if slice_:
                    break
        if slice_:
            break
    bufs = [a for a, s in allocas if s == '24' and a in lt and '.i' in a]
    nolt = [a for a, s in allocas if a not in lt]
    val = next((a for a, s in allocas if s == '33' and a in nolt), None)
    anchor = next((a for a in nolt), None)
    return slice_, bufs, val, anchor


def main():
    mod_path, out = sys.argv[1], Path(sys.argv[2])
    mod = Path(mod_path).read_text()
    iredit.ORIG = ctoracle.orig_tokens()
    _, fn, _ = iredit.split_fn(mod)
    slice_, bufs, val, anchor = detect(fn)
    print(json.dumps({'slice': slice_, 'bufs': len(bufs), 'val': val, 'anchor': anchor}))
    run = lambda spec: iredit.run_spec(mod, out / f'w{threading.get_ident()}', spec)
    rows = [('base', '', run(''))]
    if not slice_:
        print('no emit_cpi slice detected'); return
    f1 = f'mv:{slice_}:{anchor or "END"}'
    rows.append(('F1', f1, run(f1)))
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda b: (b, run(f'{f1},nolt:{b}')), bufs))
    ok = [(b, m) for b, m in res if 'ratio' in m and m['bytes'] == rows[0][2]['bytes']]
    if ok:
        b, m = max(ok, key=lambda x: x[1]['ratio'])
        spec2 = f'{f1},nolt:{b}'
        rows.append((f'F1+nolt:{b}', spec2, m))
        if val and anchor and val != anchor:
            spec3 = f'{spec2},mv:{val}:{anchor}'
            rows.append((f'+mv:{val}:{anchor}', spec3, run(spec3)))
    for name, spec, m in rows:
        print(f"{name:40s} ratio {m.get('ratio')}  bytes {m.get('bytes')}  slots {m.get('slots_diff')}  spec={spec}")


if __name__ == '__main__':
    main()
