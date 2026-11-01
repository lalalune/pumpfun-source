#!/usr/bin/env python3
"""ann2pt.py <ann_edits.jsonl> <ids_file|-> <out.jsonl>: rewrite annotation edits as llvm.bpf.passthrough edits (same
positions, same rerouting) so a screen can split each cell into opt-level folds (pt reproduces it) and CGP/ISel folds
(pt is byte-identical where ann is not)."""
import sys,json,re
ef,idf,outf=sys.argv[1:4]
E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
ids=[x.strip() for x in open(idf)] if idf!='-' else list(E)
def mang(t): return 'p0' if t=='ptr' else t
out=open(outf,'w')
for i in ids:
    e=E.get(i)
    if not e or e['kind'] not in ('ap','ai','ax','au'): continue
    rep={}
    ok=True; ty=None
    for k,v in e['rep'].items():
        nv=[]
        for l in v:
            m=re.match(r'^(\s+%[\w.$-]+ = )call ptr @llvm\.ptr\.annotation\.p0\.p0\(ptr (\S+), ptr null, ptr null, i32 (\d+), ptr null\)$',l)
            if m: l=f'{m.group(1)}call ptr @llvm.bpf.passthrough.p0.p0(i32 {m.group(3)}, ptr {m.group(2)})'; ty='ptr'
            m=re.match(r'^(\s+%[\w.$-]+ = )call (i\d+) @llvm\.annotation\.i\d+\.p0\((i\d+) (\S+), ptr null, ptr null, i32 (\d+)\)$',l)
            if m: l=f'{m.group(1)}call {m.group(2)} @llvm.bpf.passthrough.{m.group(2)}.{m.group(2)}(i32 {m.group(5)}, {m.group(2)} {m.group(4)})'; ty=m.group(2)
            nv.append(l)
        rep[k]=nv
    if ty is None: continue
    out.write(json.dumps({'id':'pt~'+i,'kind':'pt~'+e['kind'],'cls':e['cls'],'fn':e['fn'],'rep':rep,'extra':[f'declare {ty} @llvm.bpf.passthrough.{mang(ty)}.{mang(ty)}(i32, {ty})'],'src':e['src']})+'\n')
