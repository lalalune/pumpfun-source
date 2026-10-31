#!/usr/bin/env python3
"""jtc.py raw.ll : run opt -O3 -print-after=jump-threading on execute; for each JT dump list join blocks with >=2 '.i' preds
(validate exits) and their approximate getJumpThreadDuplicationCost (intrinsic=2, other inst=1, phi/dbg free)."""
import sys,re,subprocess,glob,os
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
f=sys.argv[1]; pat=sys.argv[2] if len(sys.argv)>2 else r'\.i\b'
r=subprocess.run([OPT,'-O3',f,'-S','-o','/dev/null','-print-after=jump-threading','-filter-print-funcs=_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'],capture_output=True,text=True)
dumps=r.stderr.split('*** IR Dump')[1:]
def cost(body):
    c=0
    for l in body:
        l=l.strip()
        if not l or l.startswith(';') or ' = phi ' in l or l.startswith('br ') or l.startswith('switch'): continue
        if 'llvm.dbg' in l: continue
        c+=1
        if re.search(r'call .*@llvm\.',l): c+=1
        elif re.search(r'\bcall ',l): c+=4
    return c
for n,d in enumerate(dumps):
    blocks=re.split(r'\n\n',d)
    for b in blocks:
        L=b.strip('\n').split('\n'); m=re.match(r'([\w.$"]+):\s*; preds = (.*)',L[0])
        if not m: continue
        preds=[p.strip().lstrip('%') for p in m.group(2).split(',')]
        if len(preds)>=2 and re.search(pat,L[-1]) and L[-1].strip().startswith("br i1"):
            print(f'JT{n+1} {m.group(1)} cost={cost(L[1:])} preds={preds} term={L[-1].strip()[:80]}')
