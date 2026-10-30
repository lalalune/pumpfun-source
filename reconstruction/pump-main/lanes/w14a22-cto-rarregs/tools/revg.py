#!/usr/bin/env python3
# revg.py <repo> <commit>... : emit reversal genes (new->old char hunks of admin_cto.rs) as JSON {name:[(new,old)]}
import sys,subprocess,difflib,json
R=sys.argv[1]; P='programs/pump/src/creator/admin_cto.rs'; out={}
def show(c): return subprocess.run(['git','-C',R,'show',f'{c}:{P}'],capture_output=True,text=True).stdout
cur=open(sys.argv[2]).read()
for c in sys.argv[3:]:
    a=show(c+'^').split('\n'); b=show(c).split('\n'); hunks=[]
    for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if t!='replace' or i2-i1!=j2-j1: 
            if t!='equal': hunks.append(('\n'.join(b[j1:j2]),'\n'.join(a[i1:i2]),'lines'))
            continue
        for k in range(i2-i1):
            x,y=a[i1+k],b[j1+k]
            ops=[o for o in difflib.SequenceMatcher(None,x,y,autojunk=False).get_opcodes() if o[0]!='equal']
            grp=[]
            for o in ops:
                if grp and o[1]-grp[-1][2]<40: grp[-1]=(grp[-1][0],grp[-1][1],o[2],grp[-1][3],o[4])
                else: grp.append(o)
            for _,p1,p2,q1,q2 in grp:
                for ctx in range(12,400,8):
                    nb=y[max(0,q1-ctx):q2+ctx]; ob=x[max(0,p1-ctx):p2+ctx]
                    if cur.count(nb)==1: hunks.append((nb,ob,'chars')); break
                else: hunks.append((y[q1:q2],x[p1:p2],'NOTFOUND'))
    out[c]=hunks
json.dump(out,open(O+'/revg.json','w') if False else sys.stdout,indent=0)
