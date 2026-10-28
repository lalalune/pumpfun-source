#!/usr/bin/env python3
"""layout-elf lane: re-run ONLY the final link of a saved lbuild.py build (container rust-lld, same args).

usage: python3 -I relink.py BUILD_PREFIX OUT_PREFIX [--obj ROOT.o] [--ld ORDERED_LD]

BUILD_PREFIX is an lbuild.py output prefix (has -effective-link-args.txt and -linkinputs/). The link
is replayed with the saved rustc temporaries (symbols.o, version script) and root objects, optionally
substituting the root crate object (--obj) and/or the layout recipe (--ld). The output path and map
are redirected; nothing else changes. Holds a container slot lock while linking.
Writes OUT_PREFIX-{symbols.so,candidate.so,link.log,args.txt,result.json}, OUT_PREFIX.map.
"""
from pathlib import Path
import fcntl, hashlib, json, shutil, subprocess, sys, time
R = Path('/Users/shawwalters/fees100-run')
CW = R / 'cwork'; CONTAINER = 'claude-fees100-build'; LOCKDIR = R / 'shared/tools/locks'
STRIP = '/Users/shawwalters/.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objcopy'
sha = lambda b: hashlib.sha256(b).hexdigest()

def acquire(slots=2):
    while True:
        for i in range(slots):
            f = open(LOCKDIR / f'container{i}.lock', 'w')
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); return i, f
            except BlockingIOError:
                f.close()
        time.sleep(3)

def main():
    argv = sys.argv[1:]
    opt = {}
    for k in ('--obj', '--ld'):
        if k in argv:
            i = argv.index(k); opt[k] = Path(argv[i + 1]).resolve(); del argv[i:i + 2]
    bp, out = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    args = Path(str(bp) + '-effective-link-args.txt').read_text().splitlines()
    li = Path(str(bp) + '-linkinputs')
    label = 'relink-' + out.name + '-' + sha(str(out).encode())[:8]
    d = CW / 'src' / label
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    cwd = '/work/src/' + label
    for f in li.iterdir(): shutil.copyfile(f, d / f.name)
    root = None
    new = []
    i = 0
    while i < len(args):
        x = args[i]
        if x.startswith('--version-script='):
            new.append('--version-script=' + cwd + '/version-script.list')
        elif x.endswith('/symbols.o') and x.startswith('/tmp/rustc'):
            new.append(cwd + '/symbols.o')
        elif x.endswith('.rcgu.o') and x.startswith('/work/targets/'):
            nm = x.rsplit('/', 1)[1]
            if '-cgu.' in nm and opt.get('--obj'):
                shutil.copyfile(opt['--obj'], d / ('T-' + nm)); new.append(cwd + '/T-' + nm); root = nm
            else:
                new.append(cwd + '/' + nm)
        elif x in ('--script', '-T'):
            ld = opt.get('--ld') or Path(str(bp) + '-ordered.ld')
            shutil.copyfile(ld, d / 'ordered.ld'); new += [x, cwd + '/ordered.ld']; i += 1
        elif x == '-o':
            new += ['-o', cwd + '/out.so']; i += 1
        elif x.startswith('-Map='):
            new.append('-Map=' + cwd + '/link.map')
        else:
            new.append(x)
        i += 1
    (Path(str(out) + '-args.txt')).write_text('\n'.join(new) + '\n')
    slot, fh = acquire()
    t = time.monotonic()
    with open(str(out) + '-link.log', 'wb') as log:
        r = subprocess.run(['podman', 'exec', '-w', cwd, CONTAINER,
                            '/work/sdk/rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld'] + new,
                           stdout=log, stderr=subprocess.STDOUT)
    fh.close()
    res = dict(exit_code=r.returncode, seconds=round(time.monotonic() - t, 1), substituted_root=root,
               ld=str(opt.get('--ld')) if opt.get('--ld') else 'saved', obj=str(opt.get('--obj')) if opt.get('--obj') else 'saved')
    if r.returncode == 0:
        sym = Path(str(out) + '-symbols.so'); cand = Path(str(out) + '-candidate.so')
        shutil.copyfile(d / 'out.so', sym)
        subprocess.run([STRIP, '--strip-all', str(sym), str(cand)], check=True)
        shutil.copyfile(d / 'link.map', str(out) + '.map')
        res.update(symbols_sha256=sha(sym.read_bytes()), candidate_sha256=sha(cand.read_bytes()))
    Path(str(out) + '-result.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res))
    return r.returncode

if __name__ == '__main__':
    sys.exit(main())
