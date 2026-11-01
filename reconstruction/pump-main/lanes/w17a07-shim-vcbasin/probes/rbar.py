# raw IR: compiler memory barrier (black_box(()) = asm sideeffect "" "~{memory}") at the start of execute::sweep
import re
def f(t):
    i=t.index('define internal void @_ZN14pump_recovered9admin_cto7execute5sweep17h')
    j=t.index('\nstart:\n',i)+len('\nstart:\n')
    k=t.index('\n',t.index('alloca',j)) # after first alloca line; insert after all allocas
    # find end of the alloca run
    lines=t[j:].split('\n'); n=0
    while lines[n].lstrip().startswith('%') and ' = alloca ' in lines[n]: n+=1
    pos=j+sum(len(x)+1 for x in lines[:n])
    return t[:pos]+'  call void asm sideeffect "", "~{memory}"()\n'+t[pos:]
EDITS=[f]
