"""amv.py: alloca move scan. env MV="name:anchor:before|after" moves alloca %name next to %anchor."""
import os,re
def edit(f):
    out=f
    for spec in os.environ['MV'].split(','):
        name,anchor,pos=spec.split(':')
        lines=out.split('\n')
        i=next(k for k,l in enumerate(lines) if l.strip().startswith(f'%{name} = alloca'))
        L=lines.pop(i)
        j=next(k for k,l in enumerate(lines) if l.strip().startswith(f'%{anchor} = alloca'))
        lines.insert(j if pos=='before' else j+1, L)
        out='\n'.join(lines)
    return out
