# q4d ported to main 6330811: empty asm in sweep.exit (blocks early taildup -> J2 gone),
# Rent temp lifetime.end moved from exit into the two joins, native-zero edge weight W (default 7:5)
import os,re
E='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
W=os.environ.get('W','7,5'); OK=os.environ.get('OKJ','bb48.i114'); ERR=os.environ.get('ERRJ','bb56.i')
def blk(t,n):
    i=t.index('\n'+n+':')+1; j=t.index('\n\n',i); return i,j
def f(t):
    i,j=blk(t,E); b=t[i:j]
    m=re.search(r'  call void @llvm.lifetime.end.p0\(i64 24, ptr nonnull %_11\d.sroa.5.i\)\n',b); LE=m.group(0)
    b=b.replace(LE,'  call void asm sideeffect "", ""()\n'); t=t[:i]+b+t[j:]
    if os.environ.get('NOLT')!='1':
        for X in [OK,ERR]:
            i,j=blk(t,X); bb=t[i:j]; k=bb.rindex('  br label'); t=t[:i]+bb[:k]+LE+bb[k:]+t[j:]
    else:
        i,j=blk(t,E); b=t[i:j]; b=b.replace('  call void asm sideeffect "", ""()\n','  call void asm sideeffect "", ""()\n'+LE); t=t[:i]+b+t[j:]
    if W!='0':
        y=re.search(r'  br i1 %_12\d.not.not.i, label %bb30.i, label %'+re.escape(OK)+'\n',t).group(0)
        t=t.replace(y,y[:-1]+', !prof !99999\n'); t+='\n!99999 = !{!"branch_weights", i32 %s, i32 %s}\n'%tuple(W.split(','))
    return t
EDITS=[f]
