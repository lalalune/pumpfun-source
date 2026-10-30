import re,os
TY=os.environ.get('TY','i64'); POL=os.environ.get('POL','none'); CMP=os.environ.get('CMP','ne')
def edit(f):
    L=f.split('\n')
    for i,l in enumerate(L):
        if l.startswith('  %5 = phi i1'):
            one,zero=('1','0')
            s=l.replace('%5 = phi i1','%%f64 = phi %s'%TY)
            # base: true=None
            if POL=='none': s=s.replace('[ false,','[ 0,').replace('[ true,','[ 1,')
            else: s=s.replace('[ false,','[ 1,').replace('[ true,','[ 0,')
            L[i]=s; j=i
    k=j
    while ' = phi ' in L[k+1]: k+=1
    # want: cond true -> skip(bb11) iff None
    # f==1 iff None (POL none). cond 'ne': f!=0 -> None -> skip. cond 'eq': f==0 -> Some -> bb8
    if POL=='none':
        skip_on_true = (CMP=='ne')
    else:
        skip_on_true = (CMP=='eq')
    L.insert(k+1,'  %%5 = icmp %s %s %%f64, 0'%(CMP,TY))
    for i,l in enumerate(L):
        if l.strip()=='br i1 %5, label %bb11, label %bb8' and not skip_on_true:
            L[i]='  br i1 %5, label %bb8, label %bb11'
    return '\n'.join(L)
