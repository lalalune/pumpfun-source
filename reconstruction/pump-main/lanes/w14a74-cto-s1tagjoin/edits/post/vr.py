import re
def vr(t, which=None, arm_start='bb36:', arm_end_pat='admin_cto_sharing_config17'):
    L=t.split('\n')
    gep={}
    for l in L:
        m=re.match(r'  (%\S+) = getelementptr inbounds i8, ptr %_217, i64 (\d+)$',l)
        if m: gep[m.group(1)]=int(m.group(2))
    d=next(i for i,l in enumerate(L) if l.startswith('  %_217 = load ptr'))
    L.insert(d+1,'  store ptr %_217, ptr %acctslot, align 8')
    f=next(i for i,l in enumerate(L) if l.startswith('define ') and 'admin_cto7execute' in l)
    L.insert(f+2,'  %acctslot = alloca ptr, align 8')
    s=next(i for i,l in enumerate(L) if l.startswith(arm_start))
    e=next(i for i,l in enumerate(L) if arm_end_pat in l and ' call ' in l and i>s)
    out=[];n=0
    for i,l in enumerate(L):
        if s<i<e:
            m=re.match(r'  (%\S+) = load ptr, ptr (%[\w.]+), (.*)$',l)
            if m and (m.group(2) in gep or m.group(2)=='%_217'):
                n+=1
                if which is None or n in which:
                    off=gep.get(m.group(2),0)
                    out.append('  %%vr%d = load volatile ptr, ptr %%acctslot, align 8'%n)
                    if off:
                        out.append('  %%vrg%d = getelementptr inbounds i8, ptr %%vr%d, i64 %d'%(n,n,off)); base='%%vrg%d'%n
                    else: base='%%vr%d'%n
                    out.append('  %s = load ptr, ptr %s, %s'%(m.group(1),base,m.group(3))); continue
        out.append(l)
    return '\n'.join(out)
