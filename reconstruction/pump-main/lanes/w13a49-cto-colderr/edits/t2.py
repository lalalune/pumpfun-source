# single sweep return join: move the Ok/Err cleanup lifetime.ends (bb51.i, bb55.i, bb59.i85) into sweep.exit
import re
SX='_ZN14pump_recovered9admin_cto7execute5sweep17h9943ff4781c7e018E.exit'
def blk(f,lab):
    i=f.index('\n'+lab+':')+1; j=f.index('\n\n',i); return i,j
def edit(f):
    lts=[]
    for lab in ('bb51.i','bb55.i','bb59.i85'):
        i,j=blk(f,lab); b=f[i:j]; ls=b.split('\n')
        keep=[]
        for l in ls:
            if 'llvm.lifetime.end' in l:
                k=re.sub(r', !noalias !\d+','',l.strip())
                if k not in lts: lts.append(k)
            else: keep.append(l)
        f=f[:i]+'\n'.join(keep)+f[j:]
    i,j=blk(f,SX); b=f[i:j].split('\n')
    # insert after phis
    k=max(n for n,l in enumerate(b) if ' = phi ' in l)+1
    b[k:k]=['  '+x for x in lts]
    return f[:i]+'\n'.join(b)+f[j:]
