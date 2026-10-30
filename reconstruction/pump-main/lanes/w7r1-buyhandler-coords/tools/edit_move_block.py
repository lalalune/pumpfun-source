import re,os
SPEC=os.environ['MV']  # "blk>after" ; multiple separated by ,
def edit(t):
    m=re.search(r'^define[^\n]*buy_v211buy_handler17h[^\n]*\n',t,re.M); s=m.start()
    e=t.index('\n}\n',s)+3
    body=t[s:e]
    head,rest=body.split('\n',1)
    # split into blocks
    parts=re.split(r'\n(?=[A-Za-z0-9_.]+:)',rest)
    def name(p): 
        mm=re.match(r'([A-Za-z0-9_.]+):',p); return mm.group(1) if mm else None
    for sp in SPEC.split(','):
        b,a=sp.split('>')
        i=[name(p) for p in parts].index(b); blk=parts.pop(i)
        if blk.endswith('\n}\n'): raise SystemExit('cannot move last')
        j=[name(p) for p in parts].index(a); parts.insert(j+1,blk)
    nb=head+'\n'+'\n'.join(parts)
    return t[:s]+nb+t[e:]
