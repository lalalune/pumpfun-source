#!/usr/bin/env python3
"""relayn.py <in.s> <out.s> <spec>: relay.py with IR block names (short: 'bb10.i', 'exit30.i' = to_string...exit30.i).
Missing names are reported and dropped. Prints sc.py score."""
import sys,os,re,json,importlib.util
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sp=importlib.util.spec_from_file_location('relay',T+'/relay.py'); R=importlib.util.module_from_spec(sp); sys.argv0=sys.argv; sp.loader.exec_module(R)
import sc
B=open(os.path.dirname(T)+'/tmp/Bspec.txt').read().strip()
B0='bb10.i,bb14.i,bb23.i,bb27.i,exit30.i,bb22.i,exit58.i,bb44.i,bb48.i,exit37.i,exit23.i,exit282,bb39.i'
def irmap(path):
    pre,bl,post=R.parse(path); m={}
    for n,b in bl:
        g=re.search(r'#\s*(%\S+)',b[0]) if n.startswith('LBB0') else re.search(r':\s*#\s*(%\S+)',b[0])
        if not g: continue
        s=g.group(1).strip('%"')
        if 'to_string' in s: s=s.split('E.')[-1]
        m.setdefault(s,n)
    return m
def run(i,o,spec):
    if spec=='B': spec=B
    m=irmap(i); out=[]; miss=[]
    for grp in spec.split(';'):
        g=[]
        for x in grp.split(','):
            if x=='*': g.append(x)
            elif x in m: g.append(m[x])
            else: miss.append(x)
        out.append(','.join(g))
    t=R.relayout(i,';'.join(out)); open(o,'w').write(t)
    s=sc.score(o); s.pop('ch'); s['miss']=miss; return s
if __name__=='__main__':
    print(json.dumps(run(*sys.argv[1:4])))
