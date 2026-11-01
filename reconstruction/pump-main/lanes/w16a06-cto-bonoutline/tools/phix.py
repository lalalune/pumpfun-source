#!/usr/bin/env python3
"""phix.py <name> [cpi=1]: w15a29 fee-tag phi cell on rx/<name>/m.ll (post-opt IR): drop holder_key volatile loads, phi of
constants at bb75 ([1,OK],[0,None..]) feeds the line-757 test (icmp eq i64 %1,1) and, with cpi=1, the admin_cto_pool tag. Real llc."""
import sys,os,re,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, eseq, subprocess
n=sys.argv[1]; cpi=(sys.argv[2] if len(sys.argv)>2 else '1')=='1'
t=open(f'{O}/rx/{n}/m.ll').read()
t,k=re.subn(r'\n  %\d+ = load volatile i8, ptr %holder_key, align 1[^\n]*','',t)
m=re.search(r'\nbb75:\s+; preds = %([\w.]+), %([\w.]+), %([\w.]+)\n',t); ok,a,b=m.groups()
t=t[:m.end()]+f'  %feetag = phi i64 [ 1, %{ok} ], [ 0, %{a} ], [ 0, %{b} ]\n'+t[m.end():]
assert t.count('icmp eq i64 %1, 1')==1; t=t.replace('icmp eq i64 %1, 1','icmp eq i64 %feetag, 1')
if cpi:
    L=[l for l in t.split('\n') if 'admin_cto_pool' in l and 'call' in l and 'i64 noundef %1, i64 %2)' in l]; assert len(L)==1,len(L)
    t=t.replace(L[0],L[0].replace('i64 noundef %1, i64 %2)','i64 noundef %feetag, i64 %2)'))
d=f'{O}/rx/{n}_phi{"c" if cpi else ""}'; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
s=sc.score(d+'/m.s'); s.pop('ch',None); s['vol_removed']=k; s['eseq']=' '.join(map(str,eseq.seq(sc.fn(d+'/m.s'))[:10])); print(n,json.dumps(s))
