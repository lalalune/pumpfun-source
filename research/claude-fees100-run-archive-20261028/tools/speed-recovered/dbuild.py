#!/usr/bin/env python3
"""Direct-rustc native build with the same contract as nbuild.sh (self-validating; falls back to cargo).

usage: python3 -I dbuild.py SRC_DIR TARGET_DIR OUT_PREFIX [extra rustc args...]
  writes OUT_PREFIX-symbols.so, OUT_PREFIX-build.log, OUT_PREFIX-result.json   (exit code = the compiler's)

How it works
  * depkey = sha256 of every input that can change the pump_fees rustc command or its dependencies: Cargo.toml,
    Cargo.lock, programs/pump-fees/ except src/, pump-fees-math/, .cargo/, every `path = ...` dependency/patch
    named in the manifests (e.g. the vendored anchor-attribute-program or a patched anchor-lang), ~/.cargo/config,
    and the toolchain identity. (Files the pump_fees compile reads itself are re-read by every replay.)
  * First build of a depkey ("cargo" mode): runs exactly nbuild.sh's cargo command (with -vv so cargo prints the
    rustc environment) in TARGET_DIR (an empty TARGET_DIR is first filled with clones of shared/target-native-warm),
    then freezes the dependency artifacts (APFS clones) in tools/direct/<depkey>/{sbpf-deps,host-deps} and records
    the rustc argv/env with SRC/TARGET placeholders. It replays that template once into a scratch dir and enables
    it only if the replay's .so is byte-identical to cargo's (template.json: validated + both sha256s).
  * Later builds of the same depkey ("direct" mode): run the recorded rustc command (rebound to this SRC_DIR; output
    to TARGET_DIR/sbpf-solana-solana/release/deps) against the frozen dependencies. No cargo, no fingerprinting,
    and TARGET_DIR need not be a warm target (an empty dir is fine) -> no per-variant target clone.
  * Extra rustc args are inserted where cargo puts `cargo rustc -- ARGS` (right after the remap args).
  Env: DBUILD_FORCE_CARGO=1 always uses cargo (like nbuild.sh); NSLOTS (default 6) / JOBS as nbuild.sh.
  Every compile holds one native slot through sbf_lock.py (same lock names as nbuild.sh).
"""
import hashlib, json, os, re, shlex, shutil, subprocess, sys, tempfile, time
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
STORE = HERE / 'direct'
T = Path.home() / '.cache/solana/v1.44/platform-tools'
SO = 'pump_fees_candidate.so'


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root, skip):
    """sha256 over (relative path, content sha) of every regular file under root; skip(rel_path) prunes."""
    h = hashlib.sha256()
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in ('target', '.git') and not skip(Path(dirpath, d).relative_to(root)))
        for fn in sorted(filenames):
            p = Path(dirpath, fn); rel = p.relative_to(root)
            if skip(rel) or not p.is_file():
                continue
            h.update(str(rel).encode() + b'\0' + sha_file(p).encode() + b'\n')
    return h.hexdigest()


def path_deps(src):
    """Resolved `path = "..."` dependencies/patches named in the tree's manifests."""
    out = set()
    tomls = [src / 'Cargo.toml'] + sorted((src / 'programs').glob('*/Cargo.toml')) + sorted(src.glob('pump-fees-math/Cargo.toml'))
    for toml in tomls:
        if toml.exists():
            for mm in re.finditer(r'path\s*=\s*"([^"]+)"', toml.read_text()):
                out.add((toml.parent / mm.group(1)).resolve())
    return sorted(out)


def depkey(src):
    """Hash of everything that can change the pump_fees rustc command line or the dependency artifacts."""
    src = Path(src).resolve()
    h = hashlib.sha256()
    h.update(b'dbuild-depkey-v2\n')
    for f in ('Cargo.toml', 'Cargo.lock'):
        h.update(f.encode() + b'=' + (sha_file(src / f) if (src / f).exists() else 'missing').encode() + b'\n')
    trees = [(src / 'programs/pump-fees', lambda r: r.parts[:1] == ('src',)),
             (src / 'pump-fees-math', lambda r: False), (src / '.cargo', lambda r: False)]
    covered = [src / 'programs/pump-fees', src / 'pump-fees-math']
    for dep in path_deps(src):
        if dep.is_dir() and not any(dep == c or c in dep.parents for c in covered):
            trees.append((dep, lambda r: False))
    for root, skip in trees:
        tag = str(root).replace(str(src), '{SRC}')
        h.update(tag.encode() + b'=' + (tree_hash(root, skip) if root.is_dir() else 'missing').encode() + b'\n')
    for cfg in (Path.home() / '.cargo/config.toml', Path.home() / '.cargo/config'):
        if cfg.exists():
            h.update(str(cfg).encode() + sha_file(cfg).encode())
    rustc = (T / 'rust/bin/rustc').resolve()
    st = rustc.stat()
    h.update(f'{rustc}:{st.st_size}:{int(st.st_mtime)}'.encode())
    return h.hexdigest()[:20]


def base_env(tgt):
    e = dict(os.environ)
    e.update(CARGO_HOME=str(Path.home() / '.cargo'), RUSTC=str(T / 'rust/bin/rustc'), RUSTDOC=str(T / 'rust/bin/rustdoc'),
             CC=str(T / 'llvm/bin/clang'), AR=str(T / 'llvm/bin/llvm-ar'), CARGO_TARGET_DIR=str(tgt),
             CARGO_NET_OFFLINE='true', RUSTFLAGS='-Zremap-cwd-prefix=',
             PATH=f"{T / 'rust/bin'}:{T / 'llvm/bin'}:/usr/bin:/bin")
    return e


def lock_prefix():
    return [sys.executable, '-I', str(HERE / 'sbf_lock.py'), '--slots', os.environ.get('NSLOTS', '6'), '--name', 'native', '--']


def remaps(src):
    return [f'--remap-path-prefix={src}/programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/',
            f'--remap-path-prefix={src}/pump-fees-math/=pump-fees-math/',
            '--remap-path-prefix=programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/']


def cargo_build(src, tgt, out, extra):
    """Exactly nbuild.sh's cargo command (-vv instead of --verbose so the rustc env is printed)."""
    cmd = lock_prefix() + [str(T / 'rust/bin/cargo'), 'rustc', '-vv', '--manifest-path',
           str(src / 'programs/pump-fees/Cargo.toml'), '--release', '--target', 'sbpf-solana-solana', '--locked',
           '--offline', '--jobs', os.environ.get('JOBS', '2'), '--lib', '--'] + remaps(src) + list(extra)
    (tgt / 'sbpf-solana-solana/release').mkdir(parents=True, exist_ok=True)
    so = tgt / 'sbpf-solana-solana/release' / SO
    if so.exists(): so.unlink()
    with open(f'{out}-build.log', 'wb') as log:
        rc = subprocess.call(cmd, cwd=src, env=base_env(tgt), stdout=log, stderr=subprocess.STDOUT)
    return rc, (so if rc == 0 and so.exists() else None)


def parse_running(log_text):
    """(env, argv) of the pump_fees_candidate rustc invocation in a cargo -vv log."""
    for line in log_text.splitlines():
        line = line.strip()
        if line.startswith('Running `') and '--crate-name pump_fees_candidate' in line:
            toks = shlex.split(line[len('Running `'):].rstrip('`'))
            env = {}
            while toks and re.match(r'^[A-Z_][A-Z0-9_]*=', toks[0]):
                k, v = toks.pop(0).split('=', 1); env[k] = v
            return env, toks
    return None


def make_template(src, tgt, log_text, key):
    parsed = parse_running(log_text)
    if not parsed:
        return None, 'no pump_fees_candidate Running line'
    env, argv = parsed
    if 'OUT_DIR' in env:
        return None, 'build script present (OUT_DIR); direct mode unsupported'
    STORE.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=STORE, prefix=f'.{key}-'))
    sbpf, host = tgt / 'sbpf-solana-solana/release/deps', tgt / 'release/deps'
    for name, srcdir in (('sbpf-deps', sbpf), ('host-deps', host)):
        subprocess.run(['cp', '-c', '-R', str(srcdir), str(tmp / name)], check=True)  # APFS clone: no data copied
        for f in (tmp / name).iterdir():
            if f.name.startswith(('libpump_fees_candidate', 'pump_fees_candidate')):
                f.unlink()
    S, G = str(src), str(tgt)
    def bind(s):
        s = s.replace(str(sbpf), '{STORE}/sbpf-deps').replace(str(host), '{STORE}/host-deps')
        return s.replace(S, '{SRC}').replace(G, '{TGT}')
    targv = [bind(a) for a in argv]
    i = targv.index('--out-dir'); targv[i + 1] = '{OUTDIR}'
    rm = [j for j, a in enumerate(targv) if a.startswith('--remap-path-prefix=')]
    tpl = dict(key=key, created=time.strftime('%Y-%m-%d %H:%M:%S'), src_at_capture=S, tgt_at_capture=G,
               env={k: bind(v) for k, v in env.items()}, argv=targv, extra_at=(rm[-1] + 1) if rm else len(targv),
               validated=False)
    return (tmp, tpl), None


def replay(tpl, store_dir, src, outdir, extra, logpath):
    S, O = str(src), str(outdir)
    sub = lambda s: s.replace('{STORE}', str(store_dir)).replace('{SRC}', S).replace('{TGT}', O).replace('{OUTDIR}', O)
    argv = [sub(a) for a in tpl['argv']]
    k = tpl['extra_at']
    argv = argv[:k] + list(extra) + argv[k:]
    env = base_env(outdir)
    env.update({kk: sub(v) for kk, v in tpl['env'].items()})
    Path(outdir).mkdir(parents=True, exist_ok=True)
    so = Path(outdir) / SO
    if so.exists(): so.unlink()
    with open(logpath, 'ab') as log:
        log.write(('[dbuild] direct rustc (cwd ' + S + '): ' + shlex.join(argv) + '\n').encode())
        log.flush()
        p = subprocess.Popen(lock_prefix() + argv, cwd=src, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout:  # render rustc's JSON diagnostics like cargo does (format flags do not affect codegen)
            log.write(render(line))
        rc = p.wait()
    return rc, (so if rc == 0 and so.exists() else None)


ANSI = re.compile(rb'\x1b\[[0-9;]*m')


def render(line):
    if line.startswith(b'{'):
        try:
            d = json.loads(line)
        except ValueError:
            return line
        if 'artifact' in d:
            return b''
        r = d.get('rendered') or (d.get('message') if isinstance(d.get('message'), str) else None)
        if r is not None:
            return ANSI.sub(b'', r.encode()) + (b'' if r.endswith('\n') else b'\n')
    return line


def capture(src, tgt, out, key, cargo_so):
    """Freeze deps + record template, then prove replay == cargo output before enabling direct mode."""
    made, why = make_template(src, tgt, Path(f'{out}-build.log').read_text(errors='replace'), key)
    if not made:
        return f'not captured: {why}'
    tmp, tpl = made
    want = sha_file(cargo_so)
    vdir = Path(tempfile.mkdtemp(dir=tmp, prefix='validate-'))
    rc, so = replay(tpl, tmp, src, vdir, [], str(tmp / 'validate.log'))
    got = sha_file(so) if so else 'none'
    tpl.update(validated=(rc == 0 and got == want), validation=dict(cargo_sha256=want, direct_sha256=got, src=str(src)))
    shutil.rmtree(vdir, ignore_errors=True)
    (tmp / 'template.json').write_text(json.dumps(tpl, indent=1) + '\n')
    os.chmod(tmp, 0o755)
    try:
        os.rename(tmp, STORE / key)
    except OSError:  # another builder captured the same key first; keep theirs
        shutil.rmtree(tmp, ignore_errors=True)
    return 'captured+validated' if tpl['validated'] else f'captured but NOT validated ({want[:12]} vs {got[:12]})'


def ensure_warm(tgt):
    if not (tgt / 'sbpf-solana-solana/release/deps').is_dir():  # empty target: start from the shared warm one
        for sub in (R / 'shared/target-native-warm').iterdir():
            if not (tgt / sub.name).exists():
                subprocess.run(['cp', '-c', '-R', str(sub), str(tgt / sub.name)], check=True)


def main():
    if len(sys.argv) < 4:
        print(__doc__); return 2
    src = Path(sys.argv[1]).resolve(); tgt = Path(sys.argv[2]); out = sys.argv[3]; extra = sys.argv[4:]
    tgt.mkdir(parents=True, exist_ok=True); tgt = tgt.resolve()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    key = depkey(src)
    tfile = STORE / key / 'template.json'
    tpl = None
    if not os.environ.get('DBUILD_FORCE_CARGO') and tfile.exists():
        t = json.loads(tfile.read_text())
        if t.get('validated'):
            tpl = t
    res = dict(src=str(src), depkey=key)
    if tpl:
        Path(f'{out}-build.log').write_bytes(b'')
        rc, so = replay(tpl, STORE / key, src, tgt / 'sbpf-solana-solana/release/deps', extra, f'{out}-build.log')
        res['mode'] = 'direct'
    else:
        ensure_warm(tgt)
        rc, so = cargo_build(src, tgt, out, extra)
        res['mode'] = 'cargo'
        if rc == 0 and so and not extra and not os.environ.get('DBUILD_FORCE_CARGO') and not tfile.exists():
            res['template'] = capture(src, tgt, out, key, so)
    if rc == 0 and so:
        shutil.copyfile(so, f'{out}-symbols.so')
        sha = sha_file(f'{out}-symbols.so')
    else:
        sha = 'none'
    res = dict(exit_code=rc, elapsed_seconds=round(time.time() - start), symbols_sha256=sha, **res)
    txt = json.dumps(res)
    Path(f'{out}-result.json').write_text(txt + '\n')
    print(txt)
    return rc


if __name__ == '__main__':
    sys.exit(main())
