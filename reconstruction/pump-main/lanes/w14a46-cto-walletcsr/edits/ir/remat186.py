import re
def remat(t, v='%186', base='%_266', off=168, only_calls=True):
    L=t.split('\n'); out=[]; k=0
    for l in L:
        if re.search(re.escape(v)+r'\b',l) and not l.lstrip().startswith(v+' =') and (not only_calls or ' call ' in l or l.lstrip().startswith('call ')):
            k+=1; n='%rm'+str(k)
            out.append('  %s = getelementptr inbounds i8, ptr %s, i64 %d'%(n,base,off))
            l=re.sub(re.escape(v)+r'\b',n,l)
        out.append(l)
    return '\n'.join(out)
