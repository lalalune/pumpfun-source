#!/usr/bin/env python3
"""bsweep.py <basefile.ll> <fnregex> <out.jsonl> [maxn] : for each `br i1 %c` in the matching pre-opt function, try
llvm.expect.i1(c,true/false) and score with fx (experiment only)."""
import sys,os,re,json
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces'
os.environ['LANE_OUT']=OUT
sys.path.insert(0,OUT+'/irbeam/tools'); import fx
base,fnre,outp=sys.argv[1],sys.argv[2],sys.argv[3]; maxn=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
t=open(base).read()
m=re.search(r'^define [^\n]*@'+fnre+r'[^\n]*\{\n',t,re.M); s=m.start(); e=t.index('\n}\n',s)
body=t[s:e]
brs=[(mm.start()+s,mm.group(0),mm.group(1)) for mm in re.finditer(r'  br i1 (%[\w.]+), label %[\w.$"]+, label %[\w.$"]+\n',body)]
print(len(brs),'branches',flush=True)
done=set()
if os.path.exists(outp):
    for l in open(outp):
        try: done.add(json.loads(l)['name'])
        except: pass
f=open(outp,'a')
for k,(pos,line,c) in enumerate(brs[:maxn]):
    for v in ('true','false'):
        name=f'bw{k}{v[0]}'
        if name in done: continue
        new=line.replace(f'  br i1 {c},',f'  %bwx{k} = call i1 @llvm.expect.i1(i1 {c}, i1 {v})\n  br i1 %bwx{k},',1)
        tt=t[:pos]+new+t[pos+len(line):]
        r=fx.run(tt,name); r['br']=line.strip()[:120]; r['k']=k; r['v']=v
        f.write(json.dumps(r)+'\n'); f.flush()
        import shutil; shutil.rmtree(os.path.join(OUT,'irbeam','fx',name),ignore_errors=True)
