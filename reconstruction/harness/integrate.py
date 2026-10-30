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
import argparse, ast, json, shutil, subprocess, sys, re
from pathlib import Path

H = Path(__file__).resolve().parent
SC = H.parent
sys.path.insert(0, str(H))
from treediff import reject_source_link


def build_source(*args, **kwargs):
    # File-only composition does not need the builder's POSIX locking support.
    import fastbuild
    return fastbuild.build(*args, **kwargs)


def crate_ignore(root: Path, *patterns):
    """Skip the crate-root build directory, as fastbuild staging does, plus `patterns` anywhere.

    Nested target directories and a regular file named target are source inputs.
    """
    root = Path(root)
    by_name = shutil.ignore_patterns(*patterns)

    def ignore(directory, names):
        ignored = set(by_name(directory, names))
        if Path(directory) == root and 'target' in names and (root / 'target').is_dir():
            ignored.add('target')
        return ignored
    return ignore


def make_patch(base: Path, part: Path, out: Path, tmp: Path):
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / 'a').mkdir(parents=True); (tmp / 'b').mkdir(parents=True)
    patterns = ('*.orig', '*.rej', '.DS_Store')
    shutil.copytree(base, tmp / 'a/pump', ignore=crate_ignore(base, *patterns))
    shutil.copytree(part, tmp / 'b/pump', ignore=crate_ignore(part, *patterns))
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


def reject_source_tree_links(root: Path):
    """Reject links before copytree can follow them into a composition."""
    reject_source_link(root)
    if not root.is_dir():
        return  # Preserve the existing missing/not-a-crate diagnostics.
    # Check entries as rglob yields them. Building an eager list first could
    # already traverse a Windows directory junction before it is inspected.
    for path in root.rglob('*'):
        reject_source_link(path)


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
            result[key] = Path(path)
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
    for source in {Path(base), *selected.values(), *bases.values()}:
        reject_source_tree_links(source)
    out = output_path.resolve()
    base = Path(base).resolve()
    selected = {key: path.resolve() for key, path in selected.items()}
    bases = {key: path.resolve() for key, path in bases.items()}
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
    baseline = SC / 'pump-main/baseline/score.json'
    if not a.no_build and not baseline.is_file():
        raise FileNotFoundError(f'Required scoring baseline is missing: {baseline}')
    try:
        out, base, parts = preflight(a.name, a.base_src, a.part, a.base_of)
    except (ValueError, OSError) as error:
        ap.error(str(error))
    (out / 'parts').mkdir(parents=True); (out / 'rejects').mkdir()
    src = out / 'src'
    shutil.copytree(base, src, ignore=crate_ignore(base))
    report = {'name': a.name, 'base': str(a.base_src), 'parts': []}
    exit_code = 0
    # GNU patch on Windows otherwise strips CR bytes from patch/source input.
    patch_command = ['patch'] + (['--binary'] if sys.platform == 'win32' else [])
    for label, path, derived_from in parts:
        pf = out / 'parts' / f'{label}.patch'
        text = make_patch(derived_from, Path(path), pf, SC / 'integ' / '.tmp' / a.name / label)
        if not text.strip():
            report['parts'].append({'label': label, 'status': 'empty'}); continue
        dry = subprocess.run(patch_command + ['-p2', '--forward', '--dry-run', '-E', '-d', str(src), '-i', str(pf)], capture_output=True, text=True)
        if dry.returncode == 0:
            subprocess.run(patch_command + ['-s', '-p2', '--forward', '-E', '-d', str(src), '-i', str(pf)], check=True)
            for o in src.rglob('*.orig'):
                o.unlink()
            report['parts'].append({'label': label, 'status': 'applied', 'files': patched_files(text)})
        else:
            (out / 'rejects' / f'{label}.txt').write_text(dry.stdout + dry.stderr)
            report['parts'].append({'label': label, 'status': 'conflict', 'detail': (dry.stdout + dry.stderr)[-1500:]})
    if not a.no_build:
        res = build_source(src, out / 'work', out / 'build', quiet=True)
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
