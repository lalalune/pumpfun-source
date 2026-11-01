#!/usr/bin/env python3
"""px.py <name> <spec> [--base m.ll] : post-opt (llc-only) branch weights. spec: block:a:b,... sets !prof branch_weights a:b on
the terminator br of IR block <block> in execute. Prints M, bytes, errseq."""
import sys,os,re,json,subprocess,difflib,shutil
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,errseq,dis,fx
OUT=os.path.dirname(T)
LLC=fx.LLC; LLCA=fx.LLCA
def edit(t,spec):
    L=t.split('\n')
    st=[i for i,l in enumerate(L) if l.startswith('define ') and re.search(oracle.KEEP,l)][0]
    en=st+[i for i,l in enumerate(L[st:]) if l=='}'][0]
    extra=[]; k=0
    for it in [x for x in spec.split(',') if x]:
        b,a,c=it.rsplit(':',2)
        bi=[i for i in range(st,en) if L[i].startswith(b+':') or L[i].startswith('"'+b+'":')]
        assert len(bi)==1,(b,bi)
        j=bi[0]+1
        while not (L[j].startswith('  br ') or L[j].startswith('  switch ')): j+=1
        if L[j].startswith('  switch '):
            # switch: weights list given as a:c... only 2-way supported: default, case
            pass
        L[j]=re.sub(r', !prof !\d+','',L[j])
        k+=1; L[j]=L[j]+', !prof !88880%d'%k
        extra.append('!88880%d = !{!"branch_weights", i32 %s, i32 %s}'%(k,a,c))
    return '\n'.join(L)+'\n'+'\n'.join(extra)+'\n'
def run(name,spec,base):
    d=OUT+'/px/'+name; os.makedirs(d,exist_ok=True)
    t=edit(open(base).read(),spec); open(d+'/m.ll','w').write(t)
    r=subprocess.run(['nice','-n','5',LLC,*LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return {'name':name,'err':r.stderr[-400:]}
    b=oracle.elf_fn(d+'/m.o',oracle.KEEP); M,ratio=fx.Mof(b)
    e=errseq.analyze(b); v=[x for x in e if x['frm']<0x2000]
    res={'name':name,'M':M,'ratio':round(ratio,5),'bytes':len(b),'spec':spec,
      'from':' '.join(str(x['line']) for x in sorted(v,key=lambda x:x['frm'])),
      'name_ord':' '.join(str(x['line']) for x in sorted(v,key=lambda x:(x['name'] if x['name'] is not None else 1e9)))}
    open(d+'/fn.bin','wb').write(b)
    if '--keep' not in sys.argv: shutil.rmtree(d)
    return res
if __name__=='__main__':
    a=sys.argv[1:]; base=OUT+'/fx/m0/m.ll'
    if '--base' in a: base=a[a.index('--base')+1]
    print(json.dumps(run(a[0],a[1],base)))
