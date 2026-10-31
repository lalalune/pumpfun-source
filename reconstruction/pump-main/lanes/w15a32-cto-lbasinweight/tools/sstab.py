#!/usr/bin/env python3
"""sstab.py <name>: per spill interval table (experiment only): SS#, weight, def slot, assigned colour fi, final offset,
first def instruction (pre-SSC MIR), and the relabel-vote original offset for that candidate offset.
Needs an/<name>.pressc.mir, an/<name>.pei.mir, ssc_<name>.log (debug llc -debug-only=stack-slot-coloring), rx/<name>/fn.bin."""
import sys,os,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
OUT=os.path.dirname(T)
import relab as R
def ssc(f):
    iv={};asg={}
    pre=True
    for l in open(f):
        if l.startswith('Color spill slot'): pre=False
        m=re.match(r'SS#(\d+) (\S.*?) 0@\S+\s+weight:(\S+)',l)
        if m and pre:
            segs=re.findall(r'\[(\d+)([rBeD]?),(\d+)([rBeD]?)',m.group(2))
            iv[int(m.group(1))]=dict(w=float(m.group(3)),s=segs[0][0]+segs[0][1],e=segs[-1][2]+segs[-1][3],n=len(segs),segs=[(int(a),int(c)) for a,b,c,d in segs]); continue
        m=re.match(r'Assigning fi#(\d+) to fi#(\d+)',l)
        if m: asg[int(m.group(1))]=int(m.group(2))
    return iv,asg
def pei(f):
    t=open(f).read(); st=t[t.index('\nstack:'):]
    return {int(i):int(o) for i,ty,o in re.findall(r'- \{ id: (\d+), name: \'[^\']*\', type: ([\w-]+), offset: (-?\d+), size: 8',st) if ty=='spill-slot'}
def firstdef(f):
    t=open(f).read(); b=t[t.index('\nbody:'):]
    d={};blk=None;refs={}
    for l in b.split('\n'):
        m=re.match(r'\s+bb\.(\d+)',l)
        if m: blk=int(m.group(1))
        for s in re.findall(r'%stack\.(\d+), 0',l):
            s=int(s); refs.setdefault(s,[]).append((blk,l.strip()[:70]))
    return refs
def table(n):
    iv,asg=ssc(f'{OUT}/ssc_{n}.log'); off=pei(f'{OUT}/an/{n}.pei.mir'); refs=firstdef(f'{OUT}/an/{n}.pressc.mir')
    b=open(f'{OUT}/rx/{n}/fn.bin','rb').read(); V=R.votes(b,set(off.values()))
    rows=[]
    for ss,x in sorted(iv.items(),key=lambda kv:-kv[1]['w']):
        fi=asg.get(ss,ss); o=off.get(fi)
        v=V.get(o,{}); vb=max(v.items(),key=lambda kv:kv[1]) if v else (None,0)
        rf=refs.get(ss,[])
        rows.append(dict(ss=ss,w=x['w'],s=x['s'],e=x['e'],fi=fi,off=o,vote=vb[0],nv=vb[1],votes=v,nref=len(rf),first=rf[0][1] if rf else ''))
    return rows
if __name__=='__main__':
    n=sys.argv[1]; k=int(sys.argv[2]) if len(sys.argv)>2 else 30
    for i,r in enumerate(table(n)[:k]):
        print(f"{i:3d} SS#{r['ss']:<4d} w={r['w']:.6f} [{r['s']:>6s},{r['e']:>7s}) fi#{r['fi']} off={r['off']} vote={r['vote']}({r['nv']}) nref={r['nref']} {r['first']}")
