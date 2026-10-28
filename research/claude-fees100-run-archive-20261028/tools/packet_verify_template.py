"""Verify this Fees research packet: integrity, candidate ELFs, window measurement and source delta.

Run from the repository root:  python3 -B research/<packet>/verify.py
Uses only the standard library plus the repository's Fees window normalizer
(research/fees-composed-frontier188/window_map.py). Executes no compiler or target program.
"""
from pathlib import Path
import difflib, gzip, hashlib, importlib.util, json, sys
if not __debug__:
    raise RuntimeError('verification requires assertions; do not run under python -O')
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()

def read(path):
    return gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()

def check_manifest():
    paths = list(HERE.rglob('*'))
    assert not any(p.is_symlink() for p in paths), 'packet contains a symlink'
    assert all(p.is_dir() or p.is_file() for p in paths), 'packet contains a special file'
    actual = {p.relative_to(HERE).as_posix(): sha(p.read_bytes()) for p in paths
              if p.is_file() and p.relative_to(HERE).as_posix() != 'manifest.json'}
    assert actual == json.loads((HERE / 'manifest.json').read_text()), 'manifest mismatch (extra, missing or changed file)'

def windows_module():
    spec = importlib.util.spec_from_file_location('fees_window_map', ROOT / 'research/fees-composed-frontier188/window_map.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def measure(w, original, image):
    o, c = w.windows(original), w.windows(image)
    sigs = {r['signature'] for r in c}; raws = {r['raw_sha256'] for r in c}
    norm = sorted(r['address'] for r in o if r['signature'] in sigs)
    raw = sorted(r['address'] for r in o if r['raw_sha256'] in raws)
    return dict(original_windows=len(o), candidate_windows=len(c), normalized=norm, raw=raw)

def verify():
    check_manifest()
    claims = json.loads((HERE / 'claims.json').read_text())
    original = (ROOT / 'evidence/original/pump_fees/deployed.so').read_bytes()
    assert sha(original) == claims['original_sha256']
    builds = {}
    for role in claims['builds']:
        folder = HERE / 'builds' / role
        result = json.loads((folder / 'result.json').read_text())
        sym, cand = read(folder / 'symbols.so.gz'), read(folder / 'candidate.so.gz')
        assert result['exit_code'] == 0
        assert sha(sym) == result['symbols_sha256'] and sha(cand) == result['candidate_sha256'], role
        builds[role] = (sym, cand)
    if 'repeat' in builds:
        assert builds['repeat'] == builds['linux'], 'repeat build differs'
    sym, cand = builds['linux']
    if claims.get('whole_elf_equal'):
        n = claims['meaningful_elf_bytes']
        assert len(cand) == n and cand == original[:n] and not any(original[n:]), 'whole-ELF claim does not hold'
    else:
        assert original[:len(cand)] != cand
    w = windows_module()
    now = measure(w, original, sym)
    psym = read(HERE / 'parent' / 'symbols.so.gz')
    parent = measure(w, original, psym)
    assert sha(psym) == claims['parent_symbols_sha256']
    assert len(now['normalized']) == claims['normalized'] and len(now['raw']) == claims['raw'], (len(now['normalized']), len(now['raw']))
    assert now['candidate_windows'] == claims['candidate_windows']
    gained = sorted(set(now['normalized']) - set(parent['normalized']))
    lost = sorted(set(parent['normalized']) - set(now['normalized']))
    lost_raw = sorted(set(parent['raw']) - set(now['raw']))
    assert gained == claims['gained_normalized'], gained
    assert lost == [] and lost_raw == claims.get('lost_raw', []), (lost, lost_raw)
    inputs = {p.relative_to(HERE / 'source').as_posix(): sha(p.read_bytes()) for p in (HERE / 'source').rglob('*') if p.is_file()}
    assert inputs == claims['source_inputs']
    patch = []
    for name in sorted(claims['changed_files']):
        old = (HERE / 'parent-changed' / name).read_text() if (HERE / 'parent-changed' / name).exists() else ''
        new = (HERE / 'source' / name).read_text() if (HERE / 'source' / name).exists() else ''
        assert sha(old.encode()) == claims['parent_inputs'].get(name, sha(b''))
        patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'parent/' + name, 'candidate/' + name))
    assert ''.join(patch) == (HERE / 'source.patch').read_text(), 'source.patch mismatch'
    runtime = json.loads((HERE / 'runtime' / 'summary.json').read_text())
    assert runtime['candidate_sha256'] == sha(cand) and runtime['mismatches'] == [] and runtime['cases'] == claims['runtime_cases']
    return dict(normalized=len(now['normalized']), raw=len(now['raw']), candidate_windows=now['candidate_windows'],
                gained=gained, runtime_cases=runtime['cases'], candidate_sha256=sha(cand), symbols_sha256=sha(sym),
                whole_elf_equal=bool(claims.get('whole_elf_equal')))

if __name__ == '__main__':
    print(json.dumps(verify(), indent=1))
