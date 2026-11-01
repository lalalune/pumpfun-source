#!/usr/bin/env python3
"""anngen_post.py <m.ll> <edits.jsonl>: annotation insertions on the POST-opt slim execute body (llc-only screen):
ap/ai = after the def, all uses rerouted; ax = only uses outside the def block rerouted. Experiment only."""
import sys,re,json,collections
sys.path.insert(0,__import__('os').path.dirname(__file__))
import anngen
VAL=anngen.VAL
def main(src,dst):
    L=open(src).read().split('\n')
    a=[i for i,l in enumerate(L) if l.startswith('define ')][0]; b=a
    while L[b]!='}': b+=1
    blkof={}; cur='start'; E=[]; tag=0
    for i in range(a+1,b):
        m=re.match(r'^("?[\w.$-]+"?):',L[i])
        if m: cur=m.group(1)
        blkof[i]=cur
    for i in range(a+1,b):
        l=L[i]; op,t=anngen.vtype(l)
        if op is None or (t not in anngen.ITY and t!='ptr'): continue
        v=re.match(r'^\s+'+VAL,l).group(1)
        pat=re.compile(re.escape(v)+r'(?![\w.$-])')
        ins=i
        if op=='phi':
            k=i
            while re.match(r'^\s+'+VAL+r' = phi',L[k+1]): k+=1
            ins=k
        uses=[j for j in range(a+1,b) if j!=i and pat.search(L[j])]
        if not uses: continue
        xuses=[j for j in uses if blkof.get(j)!=blkof.get(i) or re.match(r'^\s+'+VAL+r' = phi',L[j])]
        fam='ap' if t=='ptr' else 'ai'
        for kind,us in ((fam,uses),('ax',xuses)):
            if not us or (kind=='ax' and len(xuses)==len(uses)): continue
            tag+=1; nv=f'%anv{tag}'
            rep={j:[pat.sub(nv,L[j])] for j in us}
            c=anngen.pcall(nv,v,tag) if t=='ptr' else anngen.icall(nv,t,v,tag)
            if ins in rep: rep[ins]=rep[ins]+[c]
            else: rep[ins]=[L[ins],c]
            E.append({'id':f'q{kind}:{i}','kind':'q'+kind,'cls':op+':'+t,'fn':'post','rep':rep,'extra':[anngen.PDECL if t=='ptr' else anngen.idecl(t)],'src':l.strip()[:120],'nuses':len(us),'xuses':len(xuses)})
    with open(dst,'w') as f:
        for e in E: f.write(json.dumps(e)+'\n')
    print(len(E),collections.Counter((e['kind'],e['cls']) for e in E).most_common(20))
if __name__=='__main__': main(*sys.argv[1:])
