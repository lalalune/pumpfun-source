#!/usr/bin/env python3
"""wscan2.py <post.ll> <tag> lo hi: like wscan for branch indices [lo,hi), reports ratio, bytes, M (scorer-exact matched units), tail."""
import sys,os,re,subprocess,json,difflib
sys.path.insert(0,os.path.dirname(__file__))
import oracle
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src,tag,lo,hi=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
L=open(src).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
e=s+[i for i,l in enumerate(L[s:]) if l=='}'][0]
brs=[i for i in range(s,e) if re.match(r'\s+br i1 %[^,]+, label %[^,]+, label %[^,\s]+$',L[i])]
orig=oracle.mask(oracle.orig_window())
def M(n):
    c=oracle.mask(open(O+'/rx/%s/fn.bin'%n,'rb').read())
    return sum(s for a,b,s in difflib.SequenceMatcher(None,orig,c,autojunk=False).get_matching_blocks())
res=[]
for bi in range(lo,min(hi,len(brs))):
    i=brs[bi]
    for nm,x,y in [('a',20,12),('b',12,20),('c',1,1000),('d',1000,1)]:
        L2=L[:]; L2[i]=L[i]+', !prof !99999'
        p=O+'/ir/ws2_%s.ll'%tag; open(p,'w').write('\n'.join(L2)+'\n!99999 = !{!"branch_weights", i32 %d, i32 %d}\n'%(x,y))
        r=subprocess.run(['python3',O+'/tools/llcm.py','ws2_'+tag,p],capture_output=True,text=True)
        try: d=json.loads(r.stdout.strip().splitlines()[-1])
        except: continue
        t=subprocess.run(['python3',O+'/tools/lseq.py',O+'/rx/ws2_%s/m.o'%tag],capture_output=True,text=True).stdout.strip().splitlines()[-1][17:]
        res.append((M('ws2_'+tag),d['ratio'],d['bytes'],bi,nm,t))
        print(res[-1],flush=True)
json.dump(res,open(O+'/ws2_%s.json'%tag,'w'))
