"""Interrupt real macOS bootstrap immediately after its canonical-path rename.

Both publication adapters perform the real rename and then signal the watchdog;
no compiler result or filesystem result is fabricated. The official pinned
v1.44 macOS compiler performs actual sysroot queries; this is not an SBF
reconstruction claim.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

repo = Path(sys.argv[1]).resolve(); sdk = Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory(prefix='mac-bootstrap-publication-') as folder:
    root = Path(folder).resolve()
    cache = root / 'cache'; hybrid = cache / 'toolchains/hybrid144'
    ready = root / 'rename-complete'
    wrappers = root / 'bin'; wrappers.mkdir()
    mv = wrappers / 'mv'
    mv.write_text('#!' + sys.executable + '\nimport os,subprocess,sys,time\nfrom pathlib import Path\n'
                  'args=sys.argv[1:]\n'
                  'if args[0] == os.environ["PROBE_CANONICAL"]:\n'
                  ' subprocess.run(["/bin/mv",*args],check=True)\n'
                  ' Path(os.environ["PROBE_READY"]).touch()\n'
                  ' time.sleep(30)\n'
                  'else: os.execv("/bin/mv",["mv",*args])\n')
    mv.chmod(0o755)
    code = r'''
import sys,os,time
from pathlib import Path
repo,sdk,cache,ready=sys.argv[1:]
sys.path.insert(0,str(Path(repo)/'reconstruction/toolchain'))
import bootstrap
bootstrap.SDK=Path(sdk);bootstrap.HOME_CACHE=Path(cache)
bootstrap.HYBRID=Path(cache)/'toolchains/hybrid144'
real=bootstrap.rename_toolchain
def observed(source,destination,**kwargs):
 result=real(source,destination,**kwargs)
 if Path(destination)==bootstrap.HYBRID and os.environ.get('PROBE_ARMED'):
  Path(ready).touch();time.sleep(30)
 return result
bootstrap.rename_toolchain=observed
sys.argv=['bootstrap.py','--sdk-check','full']
raise SystemExit(bootstrap.main())
'''
    env = dict(os.environ)
    command = [sys.executable, '-u', '-c', code, str(repo), str(sdk), str(cache), str(ready)]
    initial = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
    if initial.returncode: raise RuntimeError(initial.stdout + initial.stderr)
    marker = hybrid / 'retained-existing-file'; marker.write_bytes(b'previous installation')
    # An unused extra dylib makes this existing, still runnable compiler tree
    # fail hybrid_ok's exact library-set check and request a rebuild.
    (hybrid / 'rust/lib/libobsolete.dylib').write_bytes(b'old cache member')
    old_sysroot = subprocess.check_output([str(hybrid / 'rust/bin/rustc'), '--print', 'sysroot'],
                                         env=env, text=True).strip()
    env.update(PROBE_ARMED='1', PROBE_CANONICAL=str(hybrid), PROBE_READY=str(ready),
               PATH=str(wrappers) + os.pathsep + env.get('PATH', ''))
    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        deadline = time.monotonic() + 30
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.005)
        if not ready.exists():
            raise RuntimeError('publication seam not reached: ' + str(process.poll()))
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate(timeout=5)
        retained = [str(p.relative_to(root)) for p in cache.rglob('retained-existing-file')]
        current = None
        if (hybrid / 'rust/bin/rustc').exists():
            current = subprocess.check_output([str(hybrid / 'rust/bin/rustc'), '--print', 'sysroot'],
                                              env=env, text=True).strip()
        print(json.dumps({'old_compiler_was_runnable': old_sysroot == str(hybrid / 'rust'),
                          'canonical_exists_after_interrupt': hybrid.exists(),
                          'canonical_compiler_runnable_after_interrupt': current == str(hybrid / 'rust'),
                          'previous_files_retained_at': retained, 'bootstrap_returncode': process.returncode,
                          'stdout': stdout, 'stderr': stderr}, indent=2))
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL); process.communicate(timeout=5)
