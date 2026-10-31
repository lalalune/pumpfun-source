# coin_present raw (data_is_empty of coin ATA) through an i8 slot: stored after the call, reloaded at each use
def f(t):
    t=t.replace("start:\n","start:\n  %cpsl = alloca i8, align 1\n",1)
    L=t.split('\n'); out=[]; k=0
    for l in L:
        if l.startswith('  %_27.i = call '):
            out.append(l); out.append('  %cpz = zext i1 %_27.i to i8'); out.append('  store i8 %cpz, ptr %cpsl, align 1'); continue
        if '%_27.i' in l and not l.startswith('  %_27.i ='):
            k+=1; out.append('  %%cpl%d = load i8, ptr %%cpsl, align 1'%k); out.append('  %%cpb%d = trunc i8 %%cpl%d to i1'%(k,k))
            l=l.replace('%_27.i,','%%cpb%d,'%k).replace('%_27.i\n','%%cpb%d\n'%k)
            if l.endswith('%_27.i'): l=l[:-len('%_27.i')]+'%%cpb%d'%k
        out.append(l)
    return '\n'.join(out)
EDITS=[f]
