#!/usr/bin/env python3
"""regmap.py <cand.dis|m.ll> [chunk=0x800]: whole-function structural alignment (wd.py struct norm); for every aligned pair
whose only difference is register names, count (orig reg -> cand reg) substitutions per orig chunk."""
import sys,re,difflib,subprocess,os,collections
T=os.path.dirname(os.path.abspath(__file__))
g={'__file__':T+'/wd.py'}; exec(open(T+'/wd.py').read().split("a=sys.argv[1:]")[0],g)
p=sys.argv[1]; ch=int(sys.argv[2],16) if len(sys.argv)>2 else 0x800
O=g['rd'](open(T+'/../or.dis'))
d=subprocess.run(['bash',T+'/dll.sh',p],capture_output=True,text=True).stdout.split('\n') if p.endswith('.ll') else open(p).read().split('\n')
C=g['rd'](d)
sm=difflib.SequenceMatcher(None,[g['struct'](x[1]) for x in O],[g['struct'](x[1]) for x in C],autojunk=False)
per=collections.defaultdict(collections.Counter); tot=collections.Counter()
for i,j,n in sm.get_matching_blocks():
    for k in range(n):
        o=O[i+k][1]; c=C[j+k][1]
        if g['fm'](o)==g['fm'](c): continue
        ro=re.findall(r'\br(\d)\b',o); rc=re.findall(r'\br(\d)\b',c)
        if len(ro)!=len(rc): continue
        for a,b in zip(ro,rc):
            if a!=b: per[O[i+k][0]//ch][(a,b)]+=1; tot[(a,b)]+=1
print('total', ', '.join('r%s->r%s:%d'%(a,b,n) for (a,b),n in tot.most_common(12)))
for k in sorted(per): print('%05x'%(k*ch), ', '.join('r%s->r%s:%d'%(a,b,n) for (a,b),n in per[k].most_common(6)))
