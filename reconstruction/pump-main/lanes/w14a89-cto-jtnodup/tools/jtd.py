#!/usr/bin/env python3
"""jtd.py in.ll [blocks-regex]: opt -O3 -print-before/after=jump-threading on execute; per JT dump print headers+terminators of
blocks matching regex, plus all .thread blocks; and cost per block (LLVM getJumpThreadDuplicationCost approx: lifetime/dbg free,
intrinsic call 2, other call 4, other non-free inst 1)."""
import sys,re,subprocess,glob,os
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
f=sys.argv[1]; pat=sys.argv[2] if len(sys.argv)>2 else r'^(bb75|bb19|bb21|bb76|bb77|bb22|bb25)\b'
r=subprocess.run([OPT,'-O3',f,'-S','-o','/dev/null','-print-before=jump-threading','-print-after=jump-threading','-filter-print-funcs=_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'],capture_output=True,text=True)
dumps=r.stderr.split('*** IR Dump')[1:]
FREE=('llvm.lifetime','llvm.dbg','llvm.assume','llvm.experimental.noalias.scope.decl')
def cost(body):
    c=0
    for l in body:
        l=l.strip()
        if not l or l.startswith(';') or ' = phi ' in l: continue
        if any(x in l for x in FREE): continue
        if l.startswith('br ') or l.startswith('switch') or l.startswith('ret') or l.startswith('unreachable'): continue
        if re.search(r' = (bitcast|freeze) ',l): continue
        c+=1
        if re.search(r'call .*@llvm\.',l): c+=1
        elif re.search(r'\bcall ',l): c+=3
    return c
for n,d in enumerate(dumps):
    print('#####',d.split('\n')[0][:60])
    for b in re.split(r'\n\n',d):
        L=b.strip('\n').split('\n'); m=re.match(r'([\w.$"]+):\s*(?:; preds = (.*))?',L[0])
        if not m: continue
        nm=m.group(1)
        if re.search(pat,nm) or 'thread' in nm and nm.startswith('bb'):
            print(f'  {nm} cost={cost(L[1:])} preds={m.group(2)} :: {L[-1].strip()[:90]}')
