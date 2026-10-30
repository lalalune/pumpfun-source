#!/usr/bin/env python3
"""bbmap.py <cand.so|orig> [sym]: basic-block map with call names and error-line immediates."""
import sys,re,json,struct,os
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-buyexactquote-v3/reconstruction/harness')
from win import Cand, demangle, objdump_text, BASE
from score import original_windows
sc=json.load(open(os.path.expanduser('~/.cache/pumpfun-reconstruction/baseline-main-d2cb88d/score.json')))['windows']
def short(n):
    d=demangle(n); d=re.sub(r'<.*>','<..>',d); return d.split('::')[-1] if not d.endswith('}}') else 'closure'
ST=0x1489f8
if sys.argv[1]=='orig':
    w=next(x for x in original_windows() if x['start']==ST); s,n=ST,w['bytes']; path=BASE/'original.so'
    names={int(k):(short(v['symbols'][0]) if v['symbols'] else '?') for k,v in sc.items()}
else:
    c=Cand(sys.argv[1]); sym=sys.argv[2] if len(sys.argv)>2 else r'trade::buy_exact_quote$'
    s,n,nm=next((s,n,nm) for s,n,nm in c.funcs if re.search(sym,demangle(nm))); path=c.path
    names={x[0]:short(x[2]) for x in c.funcs}
t={k:re.sub(r"\s*<[^>]*>","",v) for k,v in objdump_text(path,s,s+n).items()}; addrs=sorted(t)
def tgt(a,ins):
    m=re.search(r'([+-]0x[0-9a-f]+|[+-]\d+)$',ins)
    return a+8+int(m.group(1),16 if 'x' in m.group(1) else 10)*8
leaders={s}
for i,a in enumerate(addrs):
    ins=t[a]
    if ins.startswith('j'):
        leaders.add(tgt(a,ins))
        if i+1<len(addrs): leaders.add(addrs[i+1])
    if ins.startswith('exit') and i+1<len(addrs): leaders.add(addrs[i+1])
bid={a:k for k,a in enumerate(sorted(leaders))}
cur=None; out=[]
for i,a in enumerate(addrs):
    if a in bid: cur={'id':bid[a],'a':a,'n':0,'tags':[]}; out.append(cur)
    ins=t[a]; cur['n']+=1
    if ins.startswith('call'):
        m=re.search(r'call ([+-]?0x[0-9a-f]+|-?\d+)',ins); imm=int(m.group(1),16 if 'x' in m.group(1) else 10)
        cur['tags'].append(names.get(a+8+imm*8,'?') if imm!=-1 else 'sys')
    m=re.match(r'stw \[r10 - 0x[0-9a-f]+\], (0x3[0-9a-f]{2})$',ins)
    if m: cur['tags'].append('L%d'%int(m.group(1),16))
    if ins.startswith('j'):
        T=tgt(a,ins); cur['tags'].append(('%s->B%d'%(ins.split()[0],bid.get(T,-1))))
    if ins=='exit': cur['tags'].append('EXIT')
rel=lambda a:a-s
for b in out: print(f"B{b['id']:3d} {rel(b['a']):5x} n={b['n']:3d} "+' '.join(b['tags']))
