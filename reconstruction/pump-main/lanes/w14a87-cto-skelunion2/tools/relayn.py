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
            else:
                pat=re.sub(r'\d+$',r'\\d+',re.escape(x).replace('\\.','.'))
                c=[k for k in m if re.fullmatch(pat.replace('.',r'\.'),k) and k not in spec.split(',')]
                num=lambda k:int(re.search(r'(\d+)$',k).group(1))
                if c: c.sort(key=lambda k:abs(num(k)-num(x)))
                if c and (len(c)==1 or abs(num(c[0])-num(x))<abs(num(c[1])-num(x))) and abs(num(c[0])-num(x))<=20: g.append(m[c[0]])
                else: miss.append(x)
        out.append(','.join(g))
    t=R.relayout(i,';'.join(out)); open(o,'w').write(t)
    s=sc.score(o); s.pop('ch'); s['miss']=miss; return s
if __name__=='__main__':
    print(json.dumps(run(*sys.argv[1:4])))

# ---- polarity-aware variant: allow condition reversal (what a source polarity flip would give)
INV={'jeq':'jne','jne':'jeq','jgt':'jle','jle':'jgt','jge':'jlt','jlt':'jge','jsgt':'jsle','jsle':'jsgt','jsge':'jslt','jslt':'jsge'}
def emit_rev(pre,eb,post):
    body=[]; flips=0
    for k,(nm,b,ft) in enumerate(eb):
        b=list(b); nxt=eb[k+1][0] if k+1<len(eb) else None
        ii=R.insns(b)
        if ft is not None and ft!=nxt:
            last=b[ii[-1]].strip() if ii else ''
            op=last.split()[0] if last else ''
            if op in INV and nxt and last.endswith(', '+R.lab(nxt)):
                b[ii[-1]]='\t'+INV[op]+last[len(op):-len(R.lab(nxt))]+R.lab(ft); flips+=1
            else: b.append('\tja %s'%R.lab(ft))
        elif ft is None and ii:
            lastl=b[ii[-1]].strip()
            if nxt and lastl=='ja '+R.lab(nxt): del b[ii[-1]]
        body+=b
    emit_rev.flips=flips
    return '\n'.join(pre+body+post)
def run_rev(i,o,spec):
    old=R.emit; R.emit=emit_rev
    try: s=run(i,o,spec)
    finally: R.emit=old
    s['flips']=emit_rev.flips; return s
