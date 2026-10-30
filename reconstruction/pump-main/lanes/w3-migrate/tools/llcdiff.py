#!/usr/bin/env python3
"""llcdiff.py module.ll [extra llc args]: llc-compile, extract create_token_account_v2, compare to original."""
import subprocess, sys, difflib, os, tempfile
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent
B = Path.home() / '.cache/solana/v1.44/platform-tools/llvm/bin'
mod = sys.argv[1]; extra = sys.argv[2:]
fd, obj = tempfile.mkstemp(suffix='.o', dir=OUT / 'llc'); os.close(fd)
r = subprocess.run([str(B / 'llc'), '-O3', '-filetype=obj', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', mod, '-o', obj] + extra, capture_output=True, text=True)
if r.returncode: print('LLC FAIL', r.stderr[-2000:]); sys.exit(1)
a = subprocess.run([str(OUT / 'tools/disobj.sh'), obj], capture_output=True, text=True).stdout.splitlines()
os.unlink(obj)
o = (OUT / 'llc/orig.n').read_text().splitlines()
sm = difflib.SequenceMatcher(None, o, a, autojunk=False)
nd = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal')
print(f'insns={len(a)} orig={len(o)} ratio={sm.ratio():.4f} diffslots={nd}')
if os.environ.get('SHOW'):
    Path(os.environ['SHOW']).write_text('\n'.join(a) + '\n')
