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
import argparse, json, shutil, subprocess, sys, re
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
    d = subprocess.run(['diff', '-ruN', 'a/pump', 'b/pump'], cwd=tmp, capture_output=True, text=True)
    out.write_text(d.stdout)
    return d.stdout


def preflight(name, base, parts, overrides):
    """Validate the complete composition before touching its output or snapshots."""
    def label(value):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value) or value in ('.', '..'):
            raise ValueError(f'invalid composition name or label: {value!r}')
        return value

    def selections(values, kind):
        result = {}
        for value in values:
            if '=' not in value:
                raise ValueError(f'{kind} must be LABEL=PATH')
            key, path = value.split('=', 1)
            label(key)
            if key in result or not path:
                raise ValueError(f'duplicate label or empty path in {kind}: {key}')
            result[key] = Path(path).resolve()
        return result

    label(name)
    selected = selections(parts, '--part')
    bases = selections(overrides, '--base-of')
    unknown = bases.keys() - selected.keys()
    if unknown:
        raise ValueError('base overrides have no matching part: ' + ', '.join(sorted(unknown)))
    output_path = SC / 'integ' / name
    if output_path.exists() or output_path.is_symlink():
        raise ValueError('output already exists; choose a new --name to preserve the earlier result')
    out = output_path.resolve()
    base = base.resolve()
    for source in {base, *selected.values(), *bases.values()}:
        if source == out or source in out.parents or out in source.parents:
            raise ValueError(f'source overlaps composition output: {source}')
        if not source.is_dir() or not (source / 'src').is_dir():
            raise ValueError(f'source is not a crate directory with src/: {source}')
        for required in ('Cargo.toml', 'Cargo.lock'):
            if not (source / required).is_file():
                raise ValueError(f'source is missing {required}: {source}')
    return out, base, [(key, path, bases.get(key, base)) for key, path in selected.items()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--base-src', type=Path, required=True)
    ap.add_argument('--part', action='append', default=[])
    ap.add_argument('--base-of', action='append', default=[])
    ap.add_argument('--no-build', action='store_true')
    a = ap.parse_args()
    try:
        out, base, parts = preflight(a.name, a.base_src, a.part, a.base_of)
    except (ValueError, OSError) as error:
        ap.error(str(error))
    (out / 'parts').mkdir(parents=True); (out / 'rejects').mkdir()
    src = out / 'src'
    shutil.copytree(base, src, ignore=shutil.ignore_patterns('target'))
    report = {'name': a.name, 'base': str(a.base_src), 'parts': []}
    for label, path, derived_from in parts:
        pf = out / 'parts' / f'{label}.patch'
        text = make_patch(derived_from, Path(path), pf, SC / 'integ' / '.tmp' / a.name / label)
        if not text.strip():
            report['parts'].append({'label': label, 'status': 'empty'}); continue
        dry = subprocess.run(['patch', '-p2', '--forward', '--dry-run', '-E', '-d', str(src), '-i', str(pf)], capture_output=True, text=True)
        if dry.returncode == 0:
            subprocess.run(['patch', '-s', '-p2', '--forward', '-E', '-d', str(src), '-i', str(pf)], check=True)
            for o in src.rglob('*.orig'):
                o.unlink()
            report['parts'].append({'label': label, 'status': 'applied', 'files': sorted({l[11:].split('\t')[0] for l in text.splitlines() if l.startswith('+++ b/')})})
        else:
            (out / 'rejects' / f'{label}.txt').write_text(dry.stdout + dry.stderr)
            report['parts'].append({'label': label, 'status': 'conflict', 'detail': (dry.stdout + dry.stderr)[-1500:]})
    if not a.no_build:
        res = fastbuild.build(src, out / 'work', out / 'build', quiet=True)
        report['build'] = res
        if res['ok']:
            s = subprocess.run([sys.executable, str(H / 'score.py'), str(out / 'build/unstripped.so'), '--json', str(out / 'score.json'), '--quiet'],
                               capture_output=True, text=True)
            report['score'] = json.loads(s.stdout)
    (out / 'report.json').write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != 'parts'} | {'parts': [{k: p[k] for k in ('label', 'status')} for p in report['parts']]}, indent=1))


if __name__ == '__main__':
    main()
