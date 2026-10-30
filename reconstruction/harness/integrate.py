#!/usr/bin/env python3
"""Compose several delivered crate snapshots onto a base crate, build and score.

  integrate.py --name NAME --base-src <crate> --part <label>=<crate snapshot dir> [--part ...]
               [--base-of <label>=<crate it was derived from>] [--no-build]

Each part is turned into a patch against the crate it was derived from (default: --base-src),
then applied in order with `patch -p2 --forward`. Rejects are reported and the part is skipped
(the composition continues). The composed crate is built with fastbuild.py and scored.
Output: SC/integ/<NAME>/{src, parts/<label>.patch, rejects/, report.json}
Names must be fresh; an earlier result is never overwritten.
"""
import argparse, ast, json, shutil, subprocess, sys
from pathlib import Path

H = Path(__file__).resolve().parent
SC = H.parent
sys.path.insert(0, str(H))
import fastbuild  # noqa


def make_patch(base: Path, part: Path, out: Path, tmp: Path):
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / 'a').mkdir(parents=True); (tmp / 'b').mkdir(parents=True)
    ign = shutil.ignore_patterns('target', '*.orig', '*.rej', '.DS_Store')
    shutil.copytree(base, tmp / 'a/pump', ignore=ign)
    shutil.copytree(part, tmp / 'b/pump', ignore=ign)
    d = subprocess.run(['diff', '-ruN', 'a/pump', 'b/pump'], cwd=tmp, capture_output=True)
    if d.returncode not in (0, 1):
        raise subprocess.CalledProcessError(d.returncode, d.args, output=d.stdout, stderr=d.stderr)
    out.write_bytes(d.stdout)
    # Decode only for report metadata; patch must receive the original diff bytes.
    return d.stdout.decode('utf-8', errors='surrogateescape')


def patched_files(text: str):
    files = set()
    in_headers = False
    for line in text.split('\n'):
        if line.startswith('diff '):
            in_headers = True
        elif line.startswith('@@'):
            in_headers = False
        if not in_headers or not line.startswith('+++ '):
            continue
        name = line[4:].split('\t', 1)[0]
        if name.startswith('"') and name.endswith('"'):
            # GNU diff C-quotes paths, including octal UTF-8 bytes. Decode a
            # bytes literal so those escapes round-trip to the original path.
            literal = name.encode('utf-8', errors='surrogateescape').decode('ascii', errors='backslashreplace')
            name = ast.literal_eval('b' + literal).decode('utf-8', errors='surrogateescape')
        if name.startswith('b/pump/'):
            files.add(name[len('b/pump/'):])
    return sorted(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--base-src', type=Path, required=True)
    ap.add_argument('--part', action='append', default=[])
    ap.add_argument('--base-of', action='append', default=[])
    ap.add_argument('--no-build', action='store_true')
    a = ap.parse_args()
    baseline = SC / 'pump-main/baseline/score.json'
    if not a.no_build and not baseline.is_file():
        raise FileNotFoundError(f'Required scoring baseline is missing: {baseline}')
    out = SC / 'integ' / a.name
    if out.exists() or out.is_symlink():
        ap.error('output already exists; choose a new --name to preserve the earlier result')
    (out / 'parts').mkdir(parents=True); (out / 'rejects').mkdir()
    src = out / 'src'
    shutil.copytree(a.base_src, src, ignore=shutil.ignore_patterns('target'))
    base_of = dict(x.split('=', 1) for x in a.base_of)
    report = {'name': a.name, 'base': str(a.base_src), 'parts': []}
    exit_code = 0
    for spec in a.part:
        label, path = spec.split('=', 1)
        derived_from = Path(base_of.get(label, a.base_src))
        pf = out / 'parts' / f'{label}.patch'
        text = make_patch(derived_from, Path(path), pf, SC / 'integ' / '.tmp' / a.name / label)
        if not text.strip():
            report['parts'].append({'label': label, 'status': 'empty'}); continue
        dry = subprocess.run(['patch', '-p2', '--forward', '--dry-run', '-E', '-d', str(src), '-i', str(pf)], capture_output=True, text=True)
        if dry.returncode == 0:
            subprocess.run(['patch', '-s', '-p2', '--forward', '-E', '-d', str(src), '-i', str(pf)], check=True)
            for o in src.rglob('*.orig'):
                o.unlink()
            report['parts'].append({'label': label, 'status': 'applied', 'files': patched_files(text)})
        else:
            (out / 'rejects' / f'{label}.txt').write_text(dry.stdout + dry.stderr)
            report['parts'].append({'label': label, 'status': 'conflict', 'detail': (dry.stdout + dry.stderr)[-1500:]})
    if not a.no_build:
        res = fastbuild.build(src, out / 'work', out / 'build', quiet=True)
        report['build'] = res
        if res['ok']:
            s = subprocess.run([sys.executable, str(H / 'score.py'), str(out / 'build/unstripped.so'),
                               '--baseline', str(baseline),
                               '--json', str(out / 'score.json'), '--quiet'],
                               capture_output=True, text=True)
            if s.returncode:
                report['score_error'] = {'returncode': s.returncode, 'stdout': s.stdout, 'stderr': s.stderr}
                exit_code = 1
            else:
                try:
                    report['score'] = json.loads(s.stdout)
                except json.JSONDecodeError:
                    report['score_error'] = {'returncode': s.returncode, 'stdout': s.stdout,
                                             'stderr': s.stderr, 'error': 'scorer returned invalid JSON'}
                    exit_code = 1
        else:
            exit_code = 1
    (out / 'report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != 'parts'} | {'parts': [{k: p[k] for k in ('label', 'status')} for p in report['parts']]}, indent=1))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
