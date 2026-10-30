import os,re
REG=os.environ.get('CLOB','r6')
def edit(f):
    L=f.split('\n')
    s=[i for i,l in enumerate(L) if 'ptr %ctx, i64 35' in l][1]
    e=[i for i,l in enumerate(L) if 'collect_transfer_native' in l][0]
    # back up s to its block label
    while not re.match(r'^\S.*:',L[s]): s-=1
    out=[];i=0
    regs=REG.split('+')
    clob=','.join('~{%s}'%r for r in regs)
    while i<len(L):
        out.append(L[i])
        if s<=i<=e and re.match(r'^[\w.$-]+:',L[i]):
            j=i+1
            while j<len(L) and re.match(r'\s+%\S+ = phi ',L[j]): out.append(L[j]); j+=1
            out.append('  call void asm sideeffect "", "%s"()'%clob)
            i=j; continue
        i+=1
    return '\n'.join(out)
