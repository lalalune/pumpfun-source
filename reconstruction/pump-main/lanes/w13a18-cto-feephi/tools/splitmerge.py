#!/usr/bin/env python3
"""splitmerge.py <in.ll> <out.ll> <block> <pred:suffix>...: duplicate <block> for each listed pred (phis reduced to that pred's incoming; defs renamed with suffix)."""
import sys,re
src,dst,B=sys.argv[1:4]; specs=[a.split(':') for a in sys.argv[4:]]
t=open(src).read()
s=t.index('admin_cto7execute'); s=t.rfind('\ndefine',0,s); e=t.index('\n}\n',s)
body=t[s:e]
m=re.search(r'\n'+re.escape(B)+r':[^\n]*\n(.*?)\n\n',body,re.S)
blk=m.group(1).split('\n')
defs=[re.match(r'\s*(%[\w.\-$]+) = ',l).group(1) for l in blk if re.match(r'\s*%[\w.\-$]+ = ',l)]
new=[]
for pred,suf in specs:
    out=[B+suf+':']
    for l in blk:
        if ' = phi ' in l:
            name,rest=l.split(' = phi ',1); ty=rest.split(' [',1)[0]
            inc=re.findall(r'\[ ([^,]+), %([\w.\-$"]+) \]',rest)
            v=[a for a,b in inc if b==pred][0]
            l=f'{name} = select i1 true, {ty} {v}, {ty} {v}'
        for d in sorted(defs,key=len,reverse=True):
            l=re.sub(re.escape(d)+r'(?![\w.\-$])',d+suf,l)
        out.append(l)
    new.append('\n'.join(out))
    # retarget pred's edge
    pm=re.search(r'\n'+re.escape(pred)+r':[^\n]*\n(.*?)\n\n',body,re.S)
    pb=pm.group(1); lines=pb.split('\n'); lines[-1]=re.sub(r'label %'+re.escape(B)+r'(?![\w.\-$])','label %'+B+suf,lines[-1])
    body=body[:pm.start(1)]+'\n'.join(lines)+body[pm.end(1):]
    # remove pred from phis in B
    m=re.search(r'\n'+re.escape(B)+r':[^\n]*\n(.*?)\n\n',body,re.S); bl=m.group(1).split('\n')
    bl=[re.sub(r', \[ [^\]]*?, %'+re.escape(pred)+r' \]','',re.sub(r'\[ [^\]]*?, %'+re.escape(pred)+r' \], ','',l)) if ' = phi ' in l else l for l in bl]
    body=body[:m.start(1)]+'\n'.join(bl)+body[m.end(1):]
# successors that got new preds: phis there need entries; append new blocks at end
term=blk[-1]
succ=re.findall(r'label %([\w.\-$"]+)',term)
for S in succ:
    m=re.search(r'\n'+re.escape(S)+r':[^\n]*\n(.*?)\n\n',body,re.S)
    if m and ' = phi ' in m.group(1): raise SystemExit('successor has phis: '+S)
body=body+'\n\n'+'\n\n'.join(new)
open(dst,'w').write(t[:s]+body+t[e:])
