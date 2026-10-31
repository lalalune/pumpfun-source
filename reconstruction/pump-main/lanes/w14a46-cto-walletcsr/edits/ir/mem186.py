import re
def mem(t, v='%186'):
    t=t.replace("start:\n","start:\n  %ccsl = alloca ptr, align 8\n",1)
    L=t.split('\n'); out=[]; k=0
    for l in L:
        if l.lstrip().startswith(v+' ='):
            out.append(l); out.append('  store ptr %s, ptr %%ccsl, align 8'%v); continue
        if re.search(re.escape(v)+r'\b',l) and (' call ' in l or l.lstrip().startswith('call ')):
            k+=1; n='%mm'+str(k)
            out.append('  %s = load ptr, ptr %%ccsl, align 8'%n)
            l=re.sub(re.escape(v)+r'\b',n,l)
        out.append(l)
    return '\n'.join(out)
