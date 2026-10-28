#!/usr/bin/env python3
"""Build many source variants concurrently (through the native slot lock), score them, write a leaderboard.

usage: python3 -I farm.py --base SRC_DIR --out FARM_DIR [--addr 147944[,..]] [--symbol ADDR=SUBSTR]
                          [--baseline BASE_SYMBOLS.so] [--parallel N] [--builder dbuild|nbuild]
                          [--include-base] [--keep-targets] [--rescore] [--extra 'RUSTC ARGS']
                          [--variants-dir DIR] [VARIANT ...]
  VARIANT is [NAME=]PATH where PATH is one of
    *.patch / *.diff  unified diff (git or `diff -ru` style, absolute paths ok: strip level auto-detected),
                      applied to an APFS clone of --base;
    *.py              mutator: `python3 -I PATH CLONE_DIR` edits the clone in place;
    a directory       full tree (has Cargo.toml + programs/) -> used as the source (cloned), otherwise an overlay
                      (files at tree-relative paths copied over a clone of --base).
  --variants-dir DIR adds every *.patch/*.diff/*.py file and subdirectory of DIR.

For each variant: FARM/<name>/src (clone + edit) -> build -> FARM/<name>/out-{symbols.so,build.log,result.json}
-> score every --addr window exactly like fndiff/fastdiff (ratio, differing span, identical) + whole-program
normalized/raw counts and lost/gained normalized windows vs --baseline (default: native baseline of CURRENT).
FARM/leaderboard.tsv is rewritten after every finished variant (sorted: any loss last, then identical first, then
ratio desc, span asc); FARM/results.jsonl keeps every row. Re-running the same command skips variants whose
src is unchanged and whose result exists (use --rescore to only rescore existing outputs).

Builder dbuild (default): direct rustc replay when tools/direct has a validated template for the variant's depkey,
so no per-variant target clone is needed; variants with a new depkey get one cargo build first (template capture),
the rest then go direct. Builder nbuild: per-variant APFS clone of --warm-target (default shared/target-native-warm)
and nbuild.sh. Targets are deleted after scoring unless --keep-targets.
--parallel N (default 3) = concurrent builds this farm submits; every compile still waits for one of the shared
native slots (sbf_lock.py, NSLOTS=6 machine-wide), so do not raise it much: other lanes share the slots.
"""
import argparse, concurrent.futures as cf, hashlib, importlib.util, json, os, shutil, subprocess, sys, threading, time
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]


def module(n, p):
    if n in sys.modules: return sys.modules[n]
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m


fd = module('fees_fastdiff', HERE / 'fastdiff.py')
db = module('fees_dbuild', HERE / 'dbuild.py')
LOCK = threading.Lock()


def clone(src, dst):
    subprocess.run(['cp', '-c', '-R', str(src), str(dst)], check=True)


def tree_digest(root):
    return db.tree_hash(root, lambda r: False)


def sanitize_patch(text, src):
    """Rewrite every ---/+++ header to a path RELATIVE to src (never absolute, never '..', never resolving outside
    src). The strip level is the smallest one for which every file header names a file inside src (git a/ b/ and
    `diff -ru /abs/base /abs/variant` patches both work). Returns the rewritten patch text or None."""
    # drop non-hunk lines that some patch implementations use to pick file names (Index:, diff ..., Only in ...)
    lines = [l for l in text.splitlines(keepends=True) if not l.startswith(('Index:', 'diff ', 'Only in '))]
    hdr = lambda l: l[4:].rstrip('\n').split('\t')[0].strip()
    pairs = [(i, hdr(lines[i]), hdr(lines[i + 1])) for i in range(len(lines) - 1)
             if lines[i].startswith('--- ') and lines[i + 1].startswith('+++ ')]
    if not pairs:
        return None
    root = src.resolve()
    def inside(rel):
        if not rel or '..' in rel.split('/'):
            return False
        p = (root / rel).resolve()
        return p == root or root in p.parents
    for k in range(0, 40):
        rels = []
        for i, a, b in pairs:
            rel = None
            for cand in (a, b):
                if cand == '/dev/null':
                    continue
                parts = [x for x in cand.split('/') if x and x != '.']
                if len(parts) <= k:
                    continue
                r = '/'.join(parts[k:])
                if inside(r) and ((root / r).is_file() or (a == '/dev/null' and (root / r).parent.is_dir())):
                    rel = r; break
            if rel is None:
                break
            rels.append((i, rel, a == '/dev/null', b == '/dev/null'))
        else:
            for i, rel, new, gone in rels:
                lines[i] = f'--- {"/dev/null" if new else rel}\n'
                lines[i + 1] = f'+++ {"/dev/null" if gone else rel}\n'
            return ''.join(lines)
    return None


def apply_patch(src, patch, log):
    text = sanitize_patch(Path(patch).read_text(errors='replace'), src)
    if text is None:
        log.write('patch: could not map every file header to a file inside the clone; nothing applied\n')
        return False
    safe = src.parent / 'variant.sanitized.patch'
    safe.write_text(text)
    for args in (['--dry-run'], []):
        r = subprocess.run(['patch', '-p0', '--batch', '--forward', '-d', str(src), '-i', str(safe)] + args,
                           capture_output=True, text=True)
        log.write(f'patch -p0 {" ".join(args)} (sanitized, relative to the clone): rc={r.returncode}\n{r.stdout}{r.stderr}')
        if r.returncode != 0:
            return False
    return True


def prepare(base, spec, vdir):
    """Create vdir/src for one variant. Returns (ok, note)."""
    src = vdir / 'src'
    if src.exists():
        shutil.rmtree(src)
    p = Path(spec)
    with open(vdir / 'prepare.log', 'w') as log:
        if p.is_dir() and (p / 'Cargo.toml').exists() and (p / 'programs').is_dir():
            clone(p, src); return True, 'full tree'
        clone(base, src)
        if p.is_dir():
            n = 0
            for f in sorted(x for x in p.rglob('*') if x.is_file()):
                rel = f.relative_to(p); dst = src / rel
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(f, dst); n += 1
                log.write(f'overlay {rel}\n')
            return True, f'overlay {n} files'
        if p.suffix in ('.patch', '.diff'):
            ok = apply_patch(src, p, log); return ok, 'patch' if ok else 'patch FAILED (see prepare.log)'
        if p.suffix == '.py':
            r = subprocess.run([sys.executable, '-I', str(p), str(src)], capture_output=True, text=True)
            log.write(r.stdout + r.stderr)
            return r.returncode == 0, 'mutator' if r.returncode == 0 else f'mutator rc={r.returncode}'
    return False, f'unsupported variant {spec}'


def build(a, name, vdir):
    src, tgt, out = vdir / 'src', vdir / 'target', vdir / 'out'
    extra = a.extra.split() if a.extra else []
    if tgt.exists():
        shutil.rmtree(tgt)
    if a.builder == 'nbuild':
        clone(Path(a.warm_target), tgt)
        cmd = [str(HERE / 'nbuild.sh'), str(src), str(tgt), str(out)] + extra
    else:
        tgt.mkdir()
        cmd = [sys.executable, '-I', str(HERE / 'dbuild.py'), str(src), str(tgt), str(out)] + extra
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    res = {}
    try:
        res = json.loads(Path(f'{out}-result.json').read_text())
    except (OSError, ValueError):
        res = dict(exit_code=r.returncode, symbols_sha256='none')
    res['wall_seconds'] = round(time.time() - t0, 1)
    if not a.keep_targets and tgt.exists():
        shutil.rmtree(tgt, ignore_errors=True)
    return res


def score(a, so_path):
    img = Path(so_path).read_bytes()
    names = (fd.dis.names_for(img), fd.dis.names_for(fd.ORIG, img))
    rows = [fd.score(img, addr, a.syms.get(addr), False, 0, names) for addr in a.addrs]
    ms = fd.measure(img, a.base_img)
    return rows, ms, hashlib.sha256(img).hexdigest()


def run_one(a, name, spec):
    vdir = a.out / name
    vdir.mkdir(parents=True, exist_ok=True)
    row = dict(name=name, spec=str(spec))
    marker = vdir / 'done.json'
    if marker.exists():
        prev = json.loads(marker.read_text())
        same = (prev.get('spec') == str(spec) and prev.get('base_digest') == a.base_digest and (vdir / 'src').exists()
                and prev.get('src_digest') == tree_digest(vdir / 'src') and prev.get('spec_digest') == spec_digest(spec))
        if a.rescore or same:
            if (vdir / 'out-symbols.so').exists():
                rows, ms, sha = score(a, vdir / 'out-symbols.so')
                prev.update(windows=rows, measure=ms, sha256=sha, reused=True)
                return prev
            if a.rescore:
                return prev
    if a.rescore:
        return dict(row, status='missing')
    ok, note = prepare(a.base, spec, vdir)
    row.update(prepare=note, spec_digest=spec_digest(spec), base_digest=a.base_digest)
    if not ok:
        row['status'] = 'prepare-failed'
        marker.write_text(json.dumps(row) + '\n'); return row
    row['src_digest'] = tree_digest(vdir / 'src')
    res = build(a, name, vdir)
    row.update(build=res)
    if res.get('exit_code') != 0 or not (vdir / 'out-symbols.so').exists():
        row['status'] = 'build-failed'
        try:
            tail = [l for l in Path(f'{vdir}/out-build.log').read_text(errors='replace').splitlines() if 'error' in l][:8]
            row['errors'] = tail
        except OSError:
            pass
    else:
        rows, ms, sha = score(a, vdir / 'out-symbols.so')
        row.update(status='ok', windows=rows, measure=ms, sha256=sha)
    marker.write_text(json.dumps(row) + '\n')
    return row


def spec_digest(spec):
    p = Path(spec)
    if p.is_dir():
        return tree_digest(p)
    return db.sha_file(p) if p.exists() else 'missing'


def sort_key(r):
    if r.get('status') != 'ok':
        return (3, 0, 0, 0)
    w0 = r['windows'][0]
    lost = len(r['measure'].get('lost_normalized', []))
    return (1 if lost else 0, 0 if all(w.get('identical') for w in r['windows']) else 1,
            -(w0.get('ratio') or 0), w0.get('span') or 0)


def write_board(a, rows):
    rows = sorted(rows, key=sort_key)
    seen = {}
    hdr = ['rank', 'name', 'status', 'mode', 'build_s', 'sha12']
    for addr in a.addrs:
        hdr += [f'{addr}:ratio', f'{addr}:span', f'{addr}:ident', f'{addr}:cand_bytes']
    hdr += ['normalized', 'raw', 'lost', 'gained', 'dup_of', 'spec']
    lines = ['\t'.join(hdr)]
    for i, r in enumerate(rows, 1):
        b = r.get('build', {})
        line = [str(i), r['name'], r.get('status', '?'), b.get('mode', '-'), str(b.get('wall_seconds', '-')),
                (r.get('sha256') or '-')[:12]]
        if r.get('status') == 'ok':
            for w in r['windows']:
                line += [f"{w['ratio']:.4f}", str(w['span']), str(w['identical']), str(w['cand_bytes'])] if 'ratio' in w else ['ERR', '-', '-', '-']
            ms = r['measure']
            line += [str(ms['normalized']), str(ms['raw_local']), ','.join(map(str, ms.get('lost_normalized', []))) or '-',
                     ','.join(map(str, ms.get('gained_normalized', []))) or '-']
            dup = seen.get(r['sha256']); seen.setdefault(r['sha256'], r['name'])
            line += [dup or '-']
        else:
            line += ['-'] * (4 * len(a.addrs) + 5)
        line += [r.get('spec', '')]
        lines.append('\t'.join(line))
    tmp = a.out / '.leaderboard.tsv.tmp'
    tmp.write_text('\n'.join(lines) + '\n'); os.replace(tmp, a.out / 'leaderboard.tsv')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('variants', nargs='*')
    ap.add_argument('--base', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--addr', default='120816,147944,163920'); ap.add_argument('--symbol', action='append', default=[])
    ap.add_argument('--baseline'); ap.add_argument('--parallel', type=int, default=3)
    ap.add_argument('--builder', choices=['dbuild', 'nbuild'], default='dbuild')
    ap.add_argument('--warm-target', default=str(R / 'shared/target-native-warm'))
    ap.add_argument('--include-base', action='store_true'); ap.add_argument('--keep-targets', action='store_true')
    ap.add_argument('--rescore', action='store_true'); ap.add_argument('--extra', default='')
    ap.add_argument('--variants-dir', action='append', default=[])
    a = ap.parse_args()
    a.base = Path(a.base).resolve(); a.out = Path(a.out).resolve(); a.out.mkdir(parents=True, exist_ok=True)
    a.base_digest = tree_digest(a.base)
    a.base_digest = tree_digest(a.base)
    a.addrs = [int(x, 0) for x in a.addr.split(',') if x]
    a.syms = {int(s.split('=', 1)[0], 0): s.split('=', 1)[1] for s in a.symbol}
    bp = Path(a.baseline) if a.baseline else fd.default_baseline()
    a.base_img = bp.read_bytes() if bp else None
    specs = []
    if a.include_base:
        specs.append(('base', str(a.base)))
    for d in a.variants_dir:
        for p in sorted(Path(d).iterdir()):
            if p.is_dir() or p.suffix in ('.patch', '.diff', '.py'):
                specs.append((p.stem if p.is_file() else p.name, str(p.resolve())))
    for v in a.variants:
        name, _, path = v.rpartition('=') if '=' in v and not Path(v).exists() else ('', '', v)
        p = Path(path).resolve()
        specs.append((name or (p.stem if p.is_file() else p.name), str(p)))
    names = [n for n, _ in specs]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        sys.exit(f'duplicate variant names: {sorted(dupes)} (use NAME=PATH)')
    print(f'[farm] {len(specs)} variants -> {a.out} (builder {a.builder}, parallel {a.parallel})', flush=True)
    rows = []
    if a.builder == 'dbuild' and not a.rescore:
        # variants whose depkey has no validated template: build one of each key first (captures the template)
        first_by_key, pending = {}, []
        for n, s in specs:
            p = Path(s)
            k = db.depkey(p) if p.is_dir() and (p / 'Cargo.toml').exists() else db.depkey(a.base)
            t = db.STORE / k / 'template.json'
            ok = t.exists() and json.loads(t.read_text()).get('validated')
            if not ok and k not in first_by_key:
                first_by_key[k] = (n, s)
            else:
                pending.append((n, s))
        for k, (n, s) in first_by_key.items():
            print(f'[farm] depkey {k} has no validated direct template: building {n} with cargo first', flush=True)
            r = run_one(a, n, s); rows.append(r); report(r); write_board(a, rows); append_jsonl(a, r)
        specs = pending
    with cf.ThreadPoolExecutor(max_workers=max(1, a.parallel)) as ex:
        futs = {ex.submit(run_one, a, n, s): n for n, s in specs}
        for f in cf.as_completed(futs):
            try:
                r = f.result()
            except Exception as e:  # keep the farm going
                r = dict(name=futs[f], status=f'error: {e!r}')
            with LOCK:
                rows.append(r); report(r); write_board(a, rows); append_jsonl(a, r)
    print(f'[farm] leaderboard: {a.out / "leaderboard.tsv"}', flush=True)
    return 0


def append_jsonl(a, r):
    with open(a.out / 'results.jsonl', 'a') as f:
        f.write(json.dumps(r) + '\n')


def report(r):
    if r.get('status') == 'ok':
        ws = ' '.join(f"{w['addr']}:{w.get('ratio', 0):.4f}/{w.get('span', '-')}{'=' if w.get('identical') else ''}" for w in r['windows'])
        ms = r['measure']
        print(f"[farm] {r['name']}: {ws} norm {ms['normalized']} lost {ms.get('lost_normalized', [])} "
              f"({r.get('build', {}).get('mode', 'reused')} {r.get('build', {}).get('wall_seconds', '-')}s)", flush=True)
    else:
        print(f"[farm] {r['name']}: {r.get('status')} {r.get('prepare', '')} {r.get('errors', '')}", flush=True)


if __name__ == '__main__':
    sys.exit(main())
