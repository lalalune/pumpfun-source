#!/usr/bin/env python3
"""Experiment-only build that records LLVM inliner remarks for selected caller functions.

  capture_inline.py --src <crate> --work <dir> --out <dir> --caller REGEX [--callee REGEX]

Adds `-C remark=inline` (rustc diagnostic remarks) to the root crate only, in this experiment;
proposed source never carries these flags. Writes inline-remarks.json with one row per remark
whose caller matches --caller: callee, caller, inlined or not, cost, threshold, reason.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'harness'))
import fastbuild  # noqa: E402
from win import demangle  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--caller', required=True)
    ap.add_argument('--callee')
    ap.add_argument('--parse-only', action='store_true', help='re-parse an existing <out>/build.log')
    ap.add_argument('--lines', action='store_true', help='add -C debuginfo=line-tables-only so remarks carry call-site file:line (diagnostic; may perturb codegen)')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.parse_only:
        return parse(a, {'ok': True})
    extra = ['-C', 'remark=inline'] + (['-C', 'debuginfo=line-tables-only'] if a.lines else [])
    real = subprocess.run

    def run(cmd, *ra, **kw):
        if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
            cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
        return real(cmd, *ra, **kw)
    subprocess.run = run
    try:
        res = fastbuild.build(a.src, a.work, a.out, recipe='identity')
    finally:
        subprocess.run = real
    return parse(a, res)


def parse(a, res):
    log = (a.out / 'build.log').read_text(errors='replace')
    rows = []
    # rustc prints e.g. "note: inline (missed): '<callee>' not inlined into '<caller>' because too costly to inline (cost=X, threshold=Y)"
    for m in re.finditer(r"note: [^\n]*? inline \((\w+)\): (.*)", log):
        kind, text = m.group(1) or 'passed', m.group(2)
        q = re.findall(r"'([^']+)'", text)
        if len(q) < 2:
            continue
        callee, caller = q[0], q[1]
        if not re.search(a.caller, demangle(caller)):
            continue
        if a.callee and not re.search(a.callee, demangle(callee)):
            continue
        cost = re.search(r'cost=(-?\d+|always|never)', text); thr = re.search(r'threshold=(-?\d+)', text)
        loc = re.search(r'note: ([^\s]+?):(\d+):(\d+) inline', m.group(0))
        rows.append({'loc': (loc.group(1).split('/')[-1] + ':' + loc.group(2)) if loc else None, 'kind': kind, 'callee': demangle(callee), 'caller': demangle(caller),
                     'cost': cost.group(1) if cost else None, 'threshold': thr.group(1) if thr else None, 'text': text[:400]})
    (a.out / 'inline-remarks.json').write_text(json.dumps(rows, indent=1) + '\n')
    print(json.dumps({'ok': res.get('ok'), 'remarks': len(rows), 'unstripped_sha256': res.get('unstripped_sha256')}))


if __name__ == '__main__':
    main()
